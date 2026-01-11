from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_all_users(db: Session):
    return db.query(models.User).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_questions_by_category(db: Session, category_name: str):
    return db.query(models.Question).filter(models.Question.category_name == category_name).all()

def get_missions_by_category(db: Session, category_name: str, user_id: int):
    missions = db.query(models.Mission).filter(models.Mission.category_name == category_name).all()

    result = []
    for m in missions:
        status_entry = db.query(models.UserMissionStatus).filter(
            models.UserMissionStatus.mission_id == m.id,
            models.UserMissionStatus.user_id == user_id
        ).first()

        status = status_entry.status if status_entry else "new"

        # Create a schema object
        m_data = schemas.Mission.model_validate(m)
        m_data.status = status
        result.append(m_data)

    return result

def update_mission_status(db: Session, user_id: int, mission_id: int, status: str):
    db_status = db.query(models.UserMissionStatus).filter(
        models.UserMissionStatus.user_id == user_id,
        models.UserMissionStatus.mission_id == mission_id
    ).first()

    if db_status:
        db_status.status = status
    else:
        db_status = models.UserMissionStatus(user_id=user_id, mission_id=mission_id, status=status)
        db.add(db_status)

    db.commit()
    db.refresh(db_status)
    return db_status

def save_user_answer(db: Session, user_id: int, answer: schemas.UserAnswerBase):
    db_answer = db.query(models.UserAnswer).filter(
        models.UserAnswer.user_id == user_id,
        models.UserAnswer.question_id == answer.question_id
    ).first()

    if db_answer:
        db_answer.answer_value = answer.answer_value
    else:
        db_answer = models.UserAnswer(user_id=user_id, question_id=answer.question_id, answer_value=answer.answer_value)
        db.add(db_answer)

    db.commit()
    db.refresh(db_answer)
    return db_answer

def get_user_answers_by_category(db: Session, user_id: int, category_name: str):
    return db.query(models.UserAnswer).join(models.Question).filter(
        models.UserAnswer.user_id == user_id,
        models.Question.category_name == category_name
    ).all()

def reset_user_answers_by_category(db: Session, user_id: int, category_name: str):
    answers = get_user_answers_by_category(db, user_id, category_name)
    for ans in answers:
        db.delete(ans)
    db.commit()

def get_all_categories(db: Session):
    return db.query(models.Category).all()

def get_all_questions(db: Session):
    return db.query(models.Question).all()
