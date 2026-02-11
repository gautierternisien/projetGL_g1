from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    profile_image = Column(String, nullable=True)

    answers = relationship("UserAnswer", back_populates="user")
    mission_statuses = relationship("UserMissionStatus", back_populates="user")
    ngc_stat = relationship("UserNgcStat", back_populates="user", uselist=False)
    ngc_progress = relationship("UserNgcProgress", back_populates="user", uselist=False)
    ngc_answers = relationship("UserNgcAnswers", back_populates="user", uselist=False)
    preferences = relationship("UserPreference", back_populates="user", uselist=False)

class Category(Base):
    __tablename__ = "categories"

    name = Column(String, primary_key=True, index=True)

    questions = relationship("Question", back_populates="category")
    missions = relationship("Mission", back_populates="category")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    category_name = Column(String, ForeignKey("categories.name"))

    category = relationship("Category", back_populates="questions")
    options = relationship("Option", back_populates="question")
    user_answers = relationship("UserAnswer", back_populates="question")

class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    label = Column(String)
    value = Column(String)
    score = Column(Integer)
    is_default = Column(Boolean, default=False)

    question = relationship("Question", back_populates="options")

class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    category_name = Column(String, ForeignKey("categories.name"))

    conditions = Column(JSON, nullable=True, default=list)

    category = relationship("Category", back_populates="missions")
    user_statuses = relationship("UserMissionStatus", back_populates="mission")

class UserPreference(Base):
    """
    Stocke le profil utilisateur déduit du questionnaire et validé par l'utilisateur.
    Utilise un champ JSON pour de la flexibilité (ex: {"has_car": true, "diet": "omnivore"})
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)

    # On stocke les préférences sous forme de dictionnaire JSON.
    # Si True, l'utilisateur est d'accord pour recevoir ces missions.
    # Ex: {"voiture": True, "velo": False, "viande": True}
    data = Column(JSON, default=dict)

    # Flag pour savoir si l'utilisateur a validé l'écran d'onboarding des missions
    has_completed_onboarding = Column(Boolean, default=False)

    user = relationship("User", back_populates="preferences")

class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_value = Column(String)

    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")


class UserNgcStat(Base):
    __tablename__ = "user_ngc_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)

    global_score = Column(Integer, nullable=False, default=8559)
    transport = Column(Integer, nullable=False, default=0)
    logement = Column(Integer, nullable=False, default=0)
    alimentation = Column(Integer, nullable=False, default=0)
    divers = Column(Integer, nullable=False, default=0)
    services_societaux = Column(Integer, nullable=False, default=0)
    updated_at = Column(String, nullable=True)

    user = relationship("User", back_populates="ngc_stat")


class UserNgcProgress(Base):
    __tablename__ = "user_ngc_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)

    transport = Column(Integer, nullable=False, default=0)
    logement = Column(Integer, nullable=False, default=0)
    alimentation = Column(Integer, nullable=False, default=0)
    divers = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="ngc_progress")


class UserNgcAnswers(Base):
    __tablename__ = "user_ngc_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    data = Column(String)  # Stored as JSON string
    updated_at = Column(String, nullable=True)

    user = relationship("User", back_populates="ngc_answers")


class UserMissionStatus(Base):
    __tablename__ = "user_mission_statuses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mission_id = Column(Integer, ForeignKey("missions.id"))
    status = Column(String, default="new")

    user = relationship("User", back_populates="mission_statuses")
    mission = relationship("Mission", back_populates="user_statuses")

    completed_at = Column(String, nullable=True) # ISO Date timestamp


class FriendLink(Base):
    __tablename__ = "friend_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='uq_friend_pair'),
    )

    user = relationship("User", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending, accepted, rejected

    __table_args__ = (
        UniqueConstraint('sender_id', 'receiver_id', name='uq_friend_request_pair'),
    )

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    start_date = Column(String) # ISO 8601 string
    end_date = Column(String)
    is_archived = Column(Boolean, default=False)
    created_at = Column(String) # ISO Date

    members = relationship("LeagueMember", back_populates="league")
    invites = relationship("LeagueInvite", back_populates="league")

class LeagueMember(Base):
    __tablename__ = "league_members"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(String) # ISO Date

    league = relationship("League", back_populates="members")
    user = relationship("User")

class LeagueInvite(Base):
    __tablename__ = "league_invites"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    inviter_id = Column(Integer, ForeignKey("users.id"))
    invitee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, accepted, rejected

    league = relationship("League", back_populates="invites")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])
