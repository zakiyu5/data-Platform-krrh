from flask import Blueprint, jsonify
from app.models import Dataset, ColumnProfile

api_bp = Blueprint("api", __name__)


@api_bp.route("/datasets")
def list_datasets():
    rows = Dataset.query.order_by(Dataset.uploaded_at.desc()).all()
    return jsonify([{
        "id": d.id,
        "filename": d.filename,
        "rows": d.rows,
        "columns": d.columns,
        "context": d.detected_context,
        "quality_score": d.quality_score,
        "uploaded_at": d.uploaded_at.isoformat(),
    } for d in rows])


@api_bp.route("/datasets/<int:dataset_id>")
def dataset_detail(dataset_id):
    d = Dataset.query.get_or_404(dataset_id)
    cols = ColumnProfile.query.filter_by(dataset_id=d.id).all()
    return jsonify({
        "id": d.id,
        "filename": d.filename,
        "rows": d.rows,
        "columns": d.columns,
        "context": d.detected_context,
        "context_confidence": d.context_confidence,
        "quality_score": d.quality_score,
        "exact_duplicates": d.exact_duplicates,
        "event_duplicates": d.event_duplicates,
        "repeated_patients": d.repeated_patients,
        "column_profiles": [{
            "name": c.name,
            "inferred_type": c.inferred_type,
            "suggested_concept": c.suggested_concept,
            "confidence": c.confidence,
            "null_pct": c.null_pct,
            "unique_count": c.unique_count,
        } for c in cols],
    })
