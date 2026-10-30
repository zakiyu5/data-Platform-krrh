from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from app.extensions import db
from app.models import Dataset, ColumnProfile, QualityIssue, DuplicateCandidate
from app.services.ingestion import save_upload, compute_hash, read_dataset
from app.services.schema_discovery import profile_dataframe, detect_context
from app.services.semantic_mapping import map_column
from app.services.duplicate_detection import detect_duplicates
from app.services.quality_engine import scan_quality
import pandas as pd
import os
import io

datasets_bp = Blueprint("datasets", __name__)

@datasets_bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("No file selected")
        return redirect(url_for("datasets.upload"))

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        flash(f"File type .{ext} is not allowed")
        return redirect(url_for("datasets.upload"))

    path, stored_name = save_upload(file, current_app.config["UPLOAD_FOLDER"])
    file_hash = compute_hash(path)

    try:
        df = read_dataset(path)
    except Exception as e:
        flash(f"Failed to read file: {e}")
        return redirect(url_for("datasets.upload"))

    if df.empty or len(df) == 0:
        flash("The uploaded file contains 0 rows of data. Please check the file.")
        return redirect(url_for("datasets.upload"))

    profiles = profile_dataframe(df)
    context, context_conf = detect_context(df, profiles)
    dupes = detect_duplicates(df)
    issues, quality_score = scan_quality(df, profiles)

    dataset = Dataset(
        filename=stored_name, stored_path=path, file_hash=file_hash,
        file_size=os.path.getsize(path), rows=len(df), columns=len(df.columns),
        detected_context=context, context_confidence=context_conf,
        exact_duplicates=dupes["exact_count"], event_duplicates=dupes["event_count"],
        repeated_patients=dupes["repeated_patients"], quality_score=quality_score,
    )
    db.session.add(dataset)
    db.session.flush()

    for p in profiles:
        concept, conf, reason = map_column(p["name"], p["inferred_type"])
        cp = ColumnProfile(
            dataset_id=dataset.id, name=p["name"], position=p["position"],
            dtype=p["dtype"], inferred_type=p["inferred_type"],
            non_null=p["non_null"], null_count=p["null_count"], null_pct=p["null_pct"],
            unique_count=p["unique_count"], suggested_concept=concept,
            confidence=conf, sample_values=p["sample_values"],
        )
        db.session.add(cp)

    for i in issues:
        db.session.add(QualityIssue(
            dataset_id=dataset.id, column_name=i["column_name"], issue_type=i["issue_type"],
            severity=i["severity"], description=i["description"],
            affected_rows=i["affected_rows"], recommended_action=i["recommended_action"],
        ))

    if dupes["exact_count"]:
        db.session.add(DuplicateCandidate(
            dataset_id=dataset.id, level=1, confidence=0.99,
            matching_fields="ALL_COLUMNS", row_count=dupes["exact_count"],
            sample=str(dupes["exact_sample"][:3]),
        ))
    if dupes["event_count"]:
        db.session.add(DuplicateCandidate(
            dataset_id=dataset.id, level=2, confidence=0.90,
            matching_fields=",".join([k for k in dupes["keys"].values() if k]),
            row_count=dupes["event_count"], sample=str(dupes["event_groups"][:3]),
        ))

    db.session.commit()
    return redirect(url_for("datasets.detail", dataset_id=dataset.id))

@datasets_bp.route("/")
def list_datasets():
    datasets = Dataset.query.order_by(Dataset.uploaded_at.desc()).all()
    return render_template("datasets.html", datasets=datasets)

def generate_dynamic_charts_and_insights(df_clean, profiles):
    charts = []
    insights = []
    
    good_cols = [p for p in profiles if p['inferred_type'] in ['categorical', 'date', 'numeric'] and p['unique_count'] > 1]
    
    for col in good_cols:
        if len(charts) >= 4: break
            
        col_name = col['name']
        
        # Date Charts
        if col['inferred_type'] == 'date':
            try:
                df_clean['parsed_date'] = pd.to_datetime(df_clean[col_name], errors='coerce')
                trend = df_clean.dropna(subset=['parsed_date']).groupby(df_clean['parsed_date'].dt.date).size().reset_index(name='count')
                trend = trend.sort_values('parsed_date').tail(30)
                if len(trend) > 1:
                    charts.append({
                        'type': 'line', 'title': f'Trend by {col_name}',
                        'labels': trend['parsed_date'].astype(str).tolist(),
                        'data': trend['count'].tolist(), 'color': '#0d6efd'
                    })
            except Exception: pass
            
        # Categorical Charts & Insights
        elif col['inferred_type'] in ['categorical', 'text']:
            if 2 <= col['unique_count'] <= 50:
                counts = df_clean[col_name].value_counts().head(10)
                total = len(df_clean)
                top_val = counts.index[0]
                top_count = counts.iloc[0]
                pct = round((top_count / total) * 100, 1)
                
                insights.append(f"🏆 The most common **{col_name}** is **{top_val}** ({top_count} records, {pct}% of total).")
                
                chart_type = 'pie' if col['unique_count'] <= 5 else 'bar'
                charts.append({
                    'type': chart_type, 'title': f'Distribution of {col_name}',
                    'labels': counts.index.astype(str).tolist(),
                    'data': counts.values.tolist(), 
                    'color': '#198754' if chart_type == 'bar' else ['#0d6efd', '#dc3545', '#ffc107', '#198754', '#6c757d']
                })
                
        # Numeric Charts & Insights
        elif col['inferred_type'] == 'numeric':
            try:
                numeric_data = pd.to_numeric(df_clean[col_name], errors='coerce').dropna()
                if len(numeric_data) > 0:
                    avg_val = round(numeric_data.mean(), 2)
                    insights.append(f"📊 The average **{col_name}** is **{avg_val}**.")
                    
                    if 2 <= col['unique_count'] <= 20:
                        counts = numeric_data.value_counts().sort_index().head(10)
                        charts.append({
                            'type': 'bar', 'title': f'Distribution of {col_name}',
                            'labels': counts.index.astype(str).tolist(),
                            'data': counts.values.tolist(), 'color': '#dc3545'
                        })
            except Exception: pass
                
    return charts, insights[:4] # Return max 4 insights to keep it clean

@datasets_bp.route("/<int:dataset_id>")
def detail(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    columns = ColumnProfile.query.filter_by(dataset_id=dataset.id).order_by(ColumnProfile.position).all()
    issues = QualityIssue.query.filter_by(dataset_id=dataset.id).all()
    dupes = DuplicateCandidate.query.filter_by(dataset_id=dataset.id).all()
    
    charts_data, insights_data = [], []
    try:
        df = read_dataset(dataset.stored_path)
        if not df.empty:
            df_clean = df.drop_duplicates()
            profiles_dict = [{'name': c.name, 'inferred_type': c.inferred_type, 'unique_count': c.unique_count} for c in columns]
            charts_data, insights_data = generate_dynamic_charts_and_insights(df_clean, profiles_dict)
    except Exception as e:
        print(f"Analytics error: {e}")

    return render_template("dataset_detail.html", dataset=dataset, columns=columns, 
                           issues=issues, dupes=dupes, charts=charts_data, insights=insights_data)

@datasets_bp.route("/<int:dataset_id>/clean")
def clean(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    dataset.is_cleaned = True
    db.session.commit()
    flash("Dataset approved for cleaning! You can now download the clean data.")
    return redirect(url_for("datasets.detail", dataset_id=dataset.id))

@datasets_bp.route("/<int:dataset_id>/export")
def export_clean(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    df = read_dataset(dataset.stored_path)
    df_clean = df.drop_duplicates()
    
    output = io.StringIO()
    df_clean.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"cleaned_{dataset.filename.replace('.xlsx', '.csv').replace('.xls', '.csv')}"
    )
