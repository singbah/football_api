from flask import jsonify, request, Blueprint, current_app
from app_dir.models import User
from app_dir import UPLOAD_FOLDER, allowed_file, json_err, json_ok
import datetime, os, json
from flask_jwt_extended import get_current_user, create_access_token, create_refresh_token, get_jwt_identity

auths_bp = Blueprint("auths", __name__, url_prefix=("/auths"))

@auths_bp.route("/register_user", methods=['POST'])
def register_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    phone = request.form.get("phone")

    if not all([username, email, password, phone]):
        return json_err({"error":"all fields required"})
    
    user_exist = User.get_user_by_email(email=email)
    user_exist1 = User.get_user_by_phone(phone=phone)

    if user_exist:
        return json_err({"error":"user exist with this email"})
    
    if user_exist1:
        return json_err({"error":"user exist with this phone"})

    new_user = User(
        username=username,
        email=email,
        phone=phone,
        role= role if role else "user" )

    new_user.set_password(password)
    new_user.save()
    return json_ok({"user":new_user.to_dict()})

@auths_bp.route("/user_login", methods=['POST'])
def user_login():
    try:
        email = request.json.get("email")
        password = request.json.get("password")
    except Exception as e:
        return json_err({"error":str(e)}, 400)
    
    if not all([email, password]):
        return json_err({"error":"all fields required"})
    
    user = User.get_user_by_email(email=email)

    if not user or not user.password_hash:
        return json_err({"error":'Wrong credentails'}, 404)
    
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return json_ok({
        "user":user.to_dict(),
        "access_token":access_token,
        "refresh_token":refresh_token
    }, 200)
    
