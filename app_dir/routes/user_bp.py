from flask import jsonify, request, Blueprint, current_app
from app_dir.models import User
from app_dir import UPLOAD_FOLDER, allowed_file, json_err, json_ok
import datetime, os, json
from flask_jwt_extended import get_current_user, create_access_token, create_refresh_token, get_jwt_identity, jwt_required

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/get_user", methods=['GET'])
@jwt_required()
def get_user():
    try:
        current_user = int(get_jwt_identity())
    except Exception as e:
        return json_err({"error":str(e)})

    user= User.get_user(current_user)

    if not user:
        return json_err({"error":"User not found"}, 404)
    
    return json_ok({"user":user.to_dict()})
