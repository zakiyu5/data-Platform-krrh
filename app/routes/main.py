from flask import Blueprint, render_template
from app.models import Dataset

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    recent = Dataset.query.order_by(Dataset.uploaded_at.desc()).limit(5).all()
    totals = {
        "datasets": Dataset.query.count(),
        "rows": sum(d.rows or 0 for d in Dataset.query.all()),
        "duplicates": sum(d.exact_duplicates or 0 for d in Dataset.query.all()),
    }
    return render_template("index.html", recent=recent, totals=totals)
