from app_dir.routes.auths import auths_bp
from app_dir.routes.user_bp import users_bp
from app_dir.routes.leagues_teams.teams_bp import teams_bp

all_bps = [auths_bp, users_bp, teams_bp]