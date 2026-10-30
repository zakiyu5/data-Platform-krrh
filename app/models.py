from datetime import datetime
from app.extensions import db

class Dataset(db.Model):
    __tablename__ = "datasets"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    file_hash = db.Column(db.String(64), index=True)
    file_size = db.Column(db.Integer)
    rows = db.Column(db.Integer, default=0)
    columns = db.Column(db.Integer, default=0)
    detected_context = db.Column(db.String(120))
    context_confidence = db.Column(db.Float, default=0.0)
    exact_duplicates = db.Column(db.Integer, default=0)
    event_duplicates = db.Column(db.Integer, default=0)
    repeated_patients = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0.0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_cleaned = db.Column(db.Boolean, default=False)

    columns_rel = db.relationship("ColumnProfile", backref="dataset", cascade="all, delete-orphan")
    issues_rel = db.relationship("QualityIssue", backref="dataset", cascade="all, delete-orphan")
    dupes_rel = db.relationship("DuplicateCandidate", backref="dataset", cascade="all, delete-orphan")

class ColumnProfile(db.Model):
    __tablename__ = "column_profiles"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), index=True)
    name = db.Column(db.String(255))
    position = db.Column(db.Integer)
    dtype = db.Column(db.String(50))
    inferred_type = db.Column(db.String(50))
    non_null = db.Column(db.Integer)
    null_count = db.Column(db.Integer)
    null_pct = db.Column(db.Float)
    unique_count = db.Column(db.Integer)
    suggested_concept = db.Column(db.String(80))
    confidence = db.Column(db.Float)
    sample_values = db.Column(db.Text)

class QualityIssue(db.Model):
    __tablename__ = "quality_issues"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), index=True)
    column_name = db.Column(db.String(255))
    issue_type = db.Column(db.String(80))
    severity = db.Column(db.String(20))
    description = db.Column(db.Text)
    affected_rows = db.Column(db.Integer)
    recommended_action = db.Column(db.String(255))

class DuplicateCandidate(db.Model):
    __tablename__ = "duplicate_candidates"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), index=True)
    level = db.Column(db.Integer)
    confidence = db.Column(db.Float)
    matching_fields = db.Column(db.Text)
    row_count = db.Column(db.Integer)
    sample = db.Column(db.Text)
