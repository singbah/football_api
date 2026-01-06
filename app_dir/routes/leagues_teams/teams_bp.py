from flask import jsonify, request, Blueprint, current_app
from app_dir.models import *
from app_dir import UPLOAD_FOLDER, allowed_file, json_err, json_ok, db
import datetime, os, json
from werkzeug.utils import secure_filename
from flask_jwt_extended import get_current_user, create_access_token, create_refresh_token, get_jwt_identity, jwt_required

teams_bp = Blueprint("teams", __name__, url_prefix="/teams")

# REGISTER A TEAM
@teams_bp.route("/register_team", methods=['POST'])
def register_team():
    try:
        name = request.form.get("name")
        county = request.form.get("county")
        logo = request.files.get("logo")
    except Exception as e:
        return json_err({"error":str(e)})

    if not name:
        return json_err({"error":"all fields required"})
    
    if logo and allowed_file(logo.filename):
        filename = secure_filename(logo.filename)
        time_stamp = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
        filename = f"{time_stamp}_{filename}"

        file_path = os.path.join(UPLOAD_FOLDER)
        os.makedirs(file_path, exist_ok=True)

        logo.save(os.path.join(file_path, filename))

        relative_path = f"uploads/{filename}"
    else: 
        relative_path = None

    new_team = Team(
        name=name,
        # county = county,
        logo=relative_path
    )

    new_team.save()
    team_data = {
        "county":new_team.county,
        "home_matches":[home_game.to_dict() for home_game in new_team.home_matches],
        "away_matches":[away_games.to_dict() for away_games in new_team.away_matches],
        "squad":[player.to_dict() for player in new_team.squad],
        "lineups":[player.to_dict() for player in new_team.lineups],
        "standings":[points for points in new_team.standings],
    }
    return json_ok({"team":new_team.to_dict(), "team_data":team_data})

# GET TEAMS DATA
@teams_bp.route("/get_all_teams", methods=['GET'])
def get_teams():
    teams = Team.query.all()
    return json_ok({"teams":[team.to_dict() for team in teams]})

# GET A TEAM DATA
@teams_bp.route("/get_team", methods=['POST'])
def get_team():
    team_id = request.json.get("team_id")

    team = Team.query.filter_by(id=team_id).first()
    matches = [*team.home_matches, *team.away_matches]
    team_squad = [player_id.to_dict() for player_id in team.squad]
    

    
    team_info = team.to_dict()
    all_matches = []


    for player in team_squad:
        player["player_data"] = Player.query.filter_by(id=player.get("id")).first().to_dict()

    team_info['squad'] = team_squad

    for game in matches:
        _game = game.to_dict()
        _game["competition_id"] = Competition.query.filter_by(id=_game.get("competition_id")).first().to_dict()

        _game["home_team_id"] = Team.query.filter_by(id=_game.get("home_team_id")).first().to_dict()

        _game["away_team_id"] = Team.query.filter_by(id=_game.get("away_team_id")).first().to_dict()

        all_matches.append(_game)
    
    return json_ok({"team":team_info, "team_data":all_matches})

# REGISTER A PLAYER
@teams_bp.route("/register_player", methods=['POST'])
def register_player():
    try:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        position = request.form.get("position")
        nationality = request.form.get("nationality")
        photo = request.files.get("photo")
    except Exception as e:
        return json_err({"error":str(e)}, 400)

    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        time_stamp = datetime.datetime.now().strftime("%d%m%Y%M%S")
        filename = f"{time_stamp}_{filename}"

        file_path = os.path.join(UPLOAD_FOLDER)
        os.makedirs(file_path, exist_ok=True)

        photo.save(os.path.join(file_path, filename))

        relative_path = f"/uploads/{filename}"
    else:
        relative_path = None

    new_player = Player(
        first_name=first_name,
        last_name=last_name,
        position=position,
        nationality=nationality,
        photo=relative_path
    )
    new_player.save()

    return json_ok({"player":new_player.to_dict()}, 200)

# ADD A PLAYER IN SQUARD
@teams_bp.route("/add_to_squard", methods=['POST'])
@jwt_required()
def add_to_squard():
    try:
        admin_id = int(get_jwt_identity())
        team_id = request.json.get("team_id")
        player_id = request.json.get("player_id")
        squad_number = request.json.get("squard_number")
        season = request.json.get("season")
    except Exception as e:
        return json_err({"error":str(e)})
    
    admin = User.get_user(id=admin_id)
    team = Team.get_team(id=team_id)

    if not admin:
        return json_err({"error":"Admin Not found"})
    
    if not team:
        return json_err({"error":"Team Not found"})
    
    team_squard = TeamSquad(
        team_id=team_id,
        player_id=player_id,
        squad_number=squad_number,
        season=season
    )
    team_squard.save()

    return json_ok({"team_squard":team_squard.to_dict()})

# GET TEAM SQUARD AND TEAM INFORMATIONS
@teams_bp.route("/get_team_squard", methods=['POST'])
def get_team_squard():
    team_id = request.json.get("team_id")

    team = Team.get_team(team_id)
    if not team:
        return json_err({"error":"Team Not Found"}, 404)
    
    squard = [{"player_data":player.player.to_dict(),
               "player_number":player.squad_number,
               "season":player.season
               } for player in TeamSquad.query.filter_by(team_id=team.id).all()]
    
    matches = {"home":team.home_matches, 
               "away":team.away_matches,
               "linesup":team.lineups,
               "standings":team.standings
               }

    return json_ok({"players":squard, 
                    "team_data":team.to_dict(), 
                    "matches":matches})

# CREATE COMPETITIONS
@teams_bp.route("/create_competition", methods=['POST'])
@jwt_required()
def create_competition():
    try:
        admin_id = int(get_jwt_identity())
        name = request.json.get("name")
        season = request.json.get("season")
        types = request.json.get("types")
    except Exception as e:
        return json_err({"error":str(e)})
    
    admin = User.get_user(admin_id)
    if not admin:
        return json_err({"error":"Admin not found"}, 404)
    
    if not all([name, season, types]):
        print(name, season, types)
        return json_err({"error":"all fields required"}, 400)
    
    new_competition = Competition(
        name=name,
        season=season,
        types=types
    )

    new_competition.save()

    return json_ok({"competition":new_competition.to_dict()})
    
# CREATE MATCHES
@teams_bp.route("/create_match", methods=['POST'])
@jwt_required()
def create_match():
    try:
        admin_id = int(get_jwt_identity())
        Competition_id = request.json.get("competition_id")
        home_team_id = request.json.get("home_team_id")
        away_team_id = request.json.get("away_team_id")
        match_date = request.json.get("match_date")
        match_time = request.json.get("match_time")
        match_status = request.json.get("match_status")
    except Exception as e:
        return json_err({"error": str(e)})

    admin = User.get_user(admin_id)
    if not admin:
        return json_err({"error": "Admin not found"}, 404)

    new_match = Match(
        competition_id=Competition_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        match_date=match_date,
        match_time=match_time,
        status=match_status if match_status else "scheduled"
    )
    new_match.save()

    return json_ok({"new_match": new_match.to_dict()})

# GET MATCHES
@teams_bp.route("/get_matches", methods=['GET'])
def get_matches():
    matches = Match.query.all()
    
    all_matches = []
    for game in matches:
        team = Team.query.filter_by(id=game.home_team_id).first()
        opponent = Team.query.filter_by(id=game.away_team_id).first()
        match_info = game.to_dict()
        match_info["competition"] = game.competition.to_dict() if game.competition else None
        match_info["home_team"] = team.to_dict() if team else None
        match_info["away_team"] = opponent.to_dict() if opponent else None
        match_info['match_id'] = game.id
        match_info['status'] = game.status
        all_matches.append(match_info)

    return json_ok({"matches": all_matches})

# GET COMPETITIONS
@teams_bp.route("/get_competitions", methods=['GET'])
def get_competitions():
    competitions = Competition.query.all()
    competitions = [comp.to_dict() for comp in competitions]
    com_matches = {}
    for comp in competitions:
        matches = Match.query.filter_by(competition_id=comp['id']).all()
        com_matches[comp['id']] = [match.to_dict() for match in matches]

    return json_ok({"competitions": competitions, "com_matches": com_matches})

# UPDATE MATCH SCORE
@teams_bp.route("/update_match_score", methods=['POST'])
@jwt_required()
def update_match_score():
    try:
        admin_id = int(get_jwt_identity())
        match_id = request.json.get("match_id")
        home_score = request.json.get("home_score")
        away_score = request.json.get("away_score")
        match_status = request.json.get("match_status")
        extra_time = request.json.get("extra_time")
        added_time = request.json.get("added_time")
    except Exception as e:
        return json_err({"error": str(e)})

    admin = User.get_user(admin_id)
    if not admin:
        return json_err({"error": "Admin not found"}, 404)

    match = Match.query.filter_by(id=match_id).first()
    if not match:
        print(f"Match {match_id} not found")
        return json_err({"error": "Match not found"}, 404)

    match.home_score = home_score
    match.away_score = away_score
    match.added_time = int(added_time)
    match.extra_time = int(extra_time)
    match.status = match_status if match_status else match.status
    match.save()
    
    return json_ok({"updated_match": match.to_dict()})


@teams_bp.route("/create_county", methods=['POST'])
@jwt_required()
def create_county():
    admin_id = int(get_jwt_identity())
    name = request.json.get("name")

    admin = User.get_user(admin_id)
    if not admin:
        return json_err({"error":"Admin not found"}, 404)
    
    if not name:
        print(name)
        return json_err({"error":"name not found"})
    
    new_county = County(name=name)
    new_county.save()

    return json_ok({"county":new_county.to_dict()})


    
    