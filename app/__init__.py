import os
from flask import Flask
from config import Config
from app.extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.datasets import datasets_bp
    from app.routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(datasets_bp, url_prefix="/datasets")
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        from app import models  # noqa
        db.create_all()

    return app
