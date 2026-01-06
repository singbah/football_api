from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app_dir import db

# =====================================================
# Base Model
# =====================================================
class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        db.session.commit()

    def restore(self):
        self.is_active = True
        self.is_deleted = False
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

    def to_dict(self, exclude=None):
        exclude = exclude or []
        data = {}
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[column.name] = value
        return data
    
    @classmethod
    def get_user_by_email(cls, email):
        user = cls.query.filter_by(email=email).first()
        return user
    
    @classmethod
    def get_user_by_phone(cls, phone):
        user = cls.query.filter_by(phone=phone).first()
        return user
    
    @classmethod
    def get_teams(cls):
        teams = [team for team in cls.query.all() if not team.is_deleted]
        return teams
    
    @classmethod
    def get_team(cls, id):
        team = cls.query.filter_by(id=id).first()
        return team if team else None


# =====================================================
# User
# =====================================================
class User(BaseModel):
    __tablename__ = "users"

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin")  # admin, editor

    news = db.relationship("News", back_populates="author")
    media = db.relationship("Media", back_populates="uploader")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def get_user(cls, id):
        return cls.query.filter_by(id=id).first()


# =====================================================
# Competition
# =====================================================
class Competition(BaseModel):
    __tablename__ = "competitions"

    name = db.Column(db.String(120), nullable=False)
    season = db.Column(db.String(20))
    types = db.Column(db.String(50))  # league, knockout

    matches = db.relationship("Match", back_populates="competition")
    standings = db.relationship("Standing", back_populates="competition")
    news = db.relationship("News", back_populates="competition")

# =====================================================
# County
# =====================================================
class County(BaseModel):
    __tablename__ = "counties"

    name = db.Column(db.String(50), unique=True, nullable=False)
    # flag = db.Column(db.String(50), default=None)
    teams = db.relationship("Team", back_populates="county")


# =====================================================
# Team
# =====================================================
class Team(BaseModel):
    __tablename__ = "teams"

    name = db.Column(db.String(120), nullable=False)
    logo = db.Column(db.String(255))
    county_id = db.Column(db.Integer, db.ForeignKey("counties.id"), default=None)

    county = db.relationship("County", back_populates="teams")
    home_matches = db.relationship(
        "Match",
        foreign_keys="Match.home_team_id",
        back_populates="home_team"
    )
    away_matches = db.relationship(
        "Match",
        foreign_keys="Match.away_team_id",
        back_populates="away_team"
    )
    
    squad = db.relationship("TeamSquad", back_populates="team")
    lineups = db.relationship("MatchLineup", back_populates="team")
    standings = db.relationship("Standing", back_populates="team")


# =====================================================
# Player
# =====================================================
class Player(BaseModel):
    __tablename__ = "players"

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    position = db.Column(db.String(20))  # GK, DF, MF, FW
    nationality = db.Column(db.String(50))
    photo = db.Column(db.String(255))

    squads = db.relationship("TeamSquad", back_populates="player")
    lineups = db.relationship("MatchLineup", back_populates="player")


# =====================================================
# Team Squad
# =====================================================
class TeamSquad(BaseModel):
    __tablename__ = "team_squads"

    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    squad_number = db.Column(db.Integer)
    season = db.Column(db.String(20))

    team = db.relationship("Team", back_populates="squad")
    player = db.relationship("Player", back_populates="squads")


# =====================================================
# Match
# =====================================================
class Match(BaseModel):
    __tablename__ = "matches"

    competition_id = db.Column(db.Integer, db.ForeignKey("competitions.id"))
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))

    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    added_time = db.Column(db.Integer, default=0)
    extra_time = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="scheduled")  # scheduled, live, FT
    match_date = db.Column(db.String(20), nullable=False)
    match_time = db.Column(db.String(20), nullable=False)

    competition = db.relationship("Competition", back_populates="matches")
    home_team = db.relationship(
        "Team",
        foreign_keys=[home_team_id],
        back_populates="home_matches"
    )
    away_team = db.relationship(
        "Team",
        foreign_keys=[away_team_id],
        back_populates="away_matches"
    )

    lineups = db.relationship("MatchLineup", back_populates="match")
    media = db.relationship("Media", back_populates="match")

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit(self)
        return self



# =====================================================
# Match Lineup
# =====================================================
class MatchLineup(BaseModel):
    __tablename__ = "match_lineups"

    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    is_starting = db.Column(db.Boolean, default=False)
    position = db.Column(db.String(20))

    match = db.relationship("Match", back_populates="lineups")
    team = db.relationship("Team", back_populates="lineups")
    player = db.relationship("Player", back_populates="lineups")


# =====================================================
# Standing
# =====================================================
class Standing(BaseModel):
    __tablename__ = "standings"

    competition_id = db.Column(db.Integer, db.ForeignKey("competitions.id"))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))

    played = db.Column(db.Integer, default=0)
    won = db.Column(db.Integer, default=0)
    drawn = db.Column(db.Integer, default=0)
    lost = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)

    competition = db.relationship("Competition", back_populates="standings")
    team = db.relationship("Team", back_populates="standings")


# =====================================================
# News
# =====================================================
class News(BaseModel):
    __tablename__ = "news"

    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    source = db.Column(db.String(120))
    competition_id = db.Column(db.Integer, db.ForeignKey("competitions.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    competition = db.relationship("Competition", back_populates="news")
    author = db.relationship("User", back_populates="news")


# =====================================================
# Media
# =====================================================
class Media(BaseModel):
    __tablename__ = "media"

    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20))  # image, video, pdf
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"))
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    match = db.relationship("Match", back_populates="media")
    uploader = db.relationship("User", back_populates="media")

class AdminLog(BaseModel):
    __tablename__ = "admin_logs"

    action = db.Column(db.String(200))
    action_id = db.Column(db.String(200))

class Stats(BaseModel):
    __tablename__ = "stats"

    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    possession = db.Column(db.Float, default=0.0)
    shots_on_target = db.Column(db.Integer, default=0)
    shots_off_target = db.Column(db.Integer, default=0)
    corners = db.Column(db.Integer, default=0)
    fouls = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    saves = db.Column(db.Integer, default=0)
    offsides = db.Column(db.Integer, default=0)

    match = db.relationship("Match")
    team = db.relationship("Team")

class Event(BaseModel):
    __tablename__ = "events"

    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"))
    event_type = db.Column(db.String(50))  # goal, assist, yellow_card, red_card, substitution
    event_time = db.Column(db.String(10))  # e.g., "45+2", "90"

    match = db.relationship("Match")
    team = db.relationship("Team")
    player = db.relationship("Player")


    