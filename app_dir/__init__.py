from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os, datetime

load_dotenv()

cors = CORS()
mail = Mail()
migrate = Migrate()
db = SQLAlchemy()
jwt = JWTManager()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_FILES_EXTENSIONS = {"jpeg", "jpg", "png", "pdf", "docx"}

def json_ok(payload=None, code=200):
    if payload is None:
        payload = {}
    payload["msg"] = "ok"
    payload["time_stamp"] = datetime.datetime.now()
    return jsonify(payload), code

def json_err(payload=None, code=400):
    if payload is None:
        payload = {}
    payload["msg"] = "something went wrong"
    payload['error'] = payload.get("error") or "error"
    payload["time_stamp"] = datetime.datetime.now()
    return jsonify(payload), code


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_FILES_EXTENSIONS

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///football.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
        JWT_ACCESS_TOKEN_EXPIRES=datetime.timedelta(days=7),
        JWT_REFRESH_TOKEN_EXPIRES=datetime.timedelta(days=30),

        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),

        UPLOAD_FOLDER=UPLOAD_FOLDER,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )

    from app_dir.routes import all_bps
    for bp in all_bps:
        app.register_blueprint(bp)

    cors.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    return app
