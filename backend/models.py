from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
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

    answers = relationship("UserAnswer", back_populates="user")
    mission_statuses = relationship("UserMissionStatus", back_populates="user")

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

    category = relationship("Category", back_populates="missions")
    user_statuses = relationship("UserMissionStatus", back_populates="mission")

class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_value = Column(String)

    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")

class UserMissionStatus(Base):
    __tablename__ = "user_mission_statuses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mission_id = Column(Integer, ForeignKey("missions.id"))
    status = Column(String, default="new")

    user = relationship("User", back_populates="mission_statuses")
    mission = relationship("Mission", back_populates="user_statuses")
