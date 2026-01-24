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

def get_users_by_ids(db: Session, ids):
    return db.query(models.User).filter(models.User.id.in_(ids)).all()

def search_users_by_prefix(db: Session, prefix: str, limit: int = 20):
    if not prefix:
        return []
    pattern = f"{prefix}%"
    return db.query(models.User).filter(models.User.username.ilike(pattern)).limit(limit).all()

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

def update_user_email(db: Session, user_id: int, new_email: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.email = new_email
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_username(db: Session, user_id: int, new_username: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.username = new_username
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_first_name(db: Session, user_id: int, new_first_name: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.first_name = new_first_name
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_last_name(db: Session, user_id: int, new_last_name: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.last_name = new_last_name
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_password(db: Session, user_id: int, new_password: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.hashed_password = get_password_hash(new_password)
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

def _normalize_pair(user_id: int, friend_id: int):
    # Store pairs in sorted order to keep uniqueness symmetric
    return (user_id, friend_id) if user_id < friend_id else (friend_id, user_id)

def add_friend(db: Session, user_id: int, friend_id: int):
    if user_id == friend_id:
        raise ValueError("Cannot add yourself as friend")
    pair = _normalize_pair(user_id, friend_id)
    existing = db.query(models.FriendLink).filter(
        models.FriendLink.user_id == pair[0],
        models.FriendLink.friend_id == pair[1]
    ).first()
    if existing:
        return existing

    link = models.FriendLink(user_id=pair[0], friend_id=pair[1])
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def remove_friend(db: Session, user_id: int, friend_id: int):
    pair = _normalize_pair(user_id, friend_id)
    link = db.query(models.FriendLink).filter(
        models.FriendLink.user_id == pair[0],
        models.FriendLink.friend_id == pair[1]
    ).first()
    if link:
        db.delete(link)
        db.commit()

def get_friend_ids(db: Session, user_id: int):
    links = db.query(models.FriendLink).filter(
        (models.FriendLink.user_id == user_id) | (models.FriendLink.friend_id == user_id)
    ).all()
    result = []
    for link in links:
        result.append(link.friend_id if link.user_id == user_id else link.user_id)
    return result

def send_friend_request(db: Session, sender_id: int, receiver_id: int):
    if sender_id == receiver_id:
        raise ValueError("Cannot send request to yourself")
    # Check if request already exists (pending or accepted)
    existing = db.query(models.FriendRequest).filter(
        models.FriendRequest.sender_id == sender_id,
        models.FriendRequest.receiver_id == receiver_id
    ).first()
    if existing:
        if existing.status == "pending":
            return existing
        # If rejected before, create new one
        if existing.status == "rejected":
            db.delete(existing)
            db.commit()

    # Check if reverse request exists (already friends)
    reverse = db.query(models.FriendRequest).filter(
        models.FriendRequest.sender_id == receiver_id,
        models.FriendRequest.receiver_id == sender_id,
        models.FriendRequest.status == "accepted"
    ).first()
    if reverse:
        raise ValueError("Already friends")

    req = models.FriendRequest(sender_id=sender_id, receiver_id=receiver_id, status="pending")
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def accept_friend_request(db: Session, request_id: int):
    req = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    if not req or req.status != "pending":
        raise ValueError("Request not found or not pending")
    
    req.status = "accepted"
    db.commit()
    db.refresh(req)
    return req

def reject_friend_request(db: Session, request_id: int):
    req = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    if not req:
        raise ValueError("Request not found")
    # Delete the request (for rejecting incoming requests)
    db.delete(req)
    db.commit()

def cancel_friend_request(db: Session, request_id: int):
    req = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    if not req:
        raise ValueError("Request not found")
    # Delete the request (for canceling sent pending requests)
    db.delete(req)
    db.commit()

def get_pending_requests_sent(db: Session, user_id: int):
    requests = db.query(models.FriendRequest).filter(
        models.FriendRequest.sender_id == user_id,
        models.FriendRequest.status == "pending"
    ).all()
    return requests

def get_incoming_requests(db: Session, user_id: int):
    requests = db.query(models.FriendRequest).filter(
        models.FriendRequest.receiver_id == user_id,
        models.FriendRequest.status == "pending"
    ).all()
    return requests

def get_accepted_friends(db: Session, user_id: int):
    # Get all accepted requests where user is sender or receiver
    requests = db.query(models.FriendRequest).filter(
        ((models.FriendRequest.sender_id == user_id) | (models.FriendRequest.receiver_id == user_id)),
        models.FriendRequest.status == "accepted"
    ).all()
    friend_ids = []
    for req in requests:
        if req.sender_id == user_id:
            friend_ids.append(req.receiver_id)
        else:
            friend_ids.append(req.sender_id)
    return friend_ids
