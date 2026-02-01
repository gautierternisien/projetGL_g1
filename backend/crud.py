from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas
from datetime import datetime

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

    if status == 'termine':
        db_status.completed_at = datetime.now().isoformat()

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
        if existing.status == "accepted":
            raise ValueError("Already friends")
        # If rejected before, create new one
        if existing.status == "rejected":
            db.delete(existing)
            db.commit()

    # Check if reverse request exists
    reverse = db.query(models.FriendRequest).filter(
        models.FriendRequest.sender_id == receiver_id,
        models.FriendRequest.receiver_id == sender_id
    ).first()

    if reverse:
        if reverse.status == "accepted":
            raise ValueError("Already friends")
        if reverse.status == "pending":
            # Mutual request: Accept the existing request
            reverse.status = "accepted"
            db.commit()
            db.refresh(reverse)
            return reverse

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

def get_user_mission_status(db: Session, user_id: int, mission_id: int):
    return db.query(models.UserMissionStatus).filter(
        models.UserMissionStatus.user_id == user_id,
        models.UserMissionStatus.mission_id == mission_id
    ).first()

def update_user_mission_status(db: Session, user_id: int, mission_id: int, status: str):
    db_status = get_user_mission_status(db, user_id, mission_id)
    if db_status:
        db_status.status = status
        db.commit()
        db.refresh(db_status)
        return db_status
    else:
        db_status = models.UserMissionStatus(user_id=user_id, mission_id=mission_id, status=status)
        db.add(db_status)
        db.commit()
        db.refresh(db_status)
        return db_status

def get_all_user_mission_statuses(db: Session, user_id: int):
    results = db.query(models.UserMissionStatus).filter(models.UserMissionStatus.user_id == user_id).all()
    # Convert list of objects to dict {mission_id: status} for easier lookup
    return {status.mission_id: status.status for status in results}

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

# --- LEAGUES ---
def create_league(db: Session, league: schemas.LeagueCreate, creator_id: int):
    now_iso = datetime.now().isoformat()
    db_league = models.League(
        name=league.name,
        start_date=league.start_date,
        end_date=league.end_date,
        created_at=now_iso,
        is_archived=False
    )
    db.add(db_league)
    db.commit()
    db.refresh(db_league)

    # Add creator as member
    member = models.LeagueMember(
        league_id=db_league.id,
        user_id=creator_id,
        joined_at=now_iso
    )
    db.add(member)
    db.commit()
    db.refresh(db_league)

    db_league.members_count = 1
    return db_league


def _archive_expired_leagues(db: Session):
    today = datetime.now().strftime("%Y-%m-%d")
    # Find active leagues that have ended (end_date < today)
    expired_leagues = db.query(models.League).filter(
        models.League.is_archived == False,
        models.League.end_date < today
    ).all()

    if expired_leagues:
        for l in expired_leagues:
            l.is_archived = True
        db.commit()


def get_active_leagues_for_user(db: Session, user_id: int):
    _archive_expired_leagues(db)
    # Find leagues where user is member and not archived
    leagues = db.query(models.League).join(models.LeagueMember).filter(
        models.LeagueMember.user_id == user_id,
        models.League.is_archived == False
    ).all()
    # Compute user count
    for l in leagues:
        l.members_count = db.query(models.LeagueMember).filter(models.LeagueMember.league_id == l.id).count()
    return leagues

def get_archived_leagues_for_user(db: Session, user_id: int):
    _archive_expired_leagues(db)
    leagues = db.query(models.League).join(models.LeagueMember).filter(
        models.LeagueMember.user_id == user_id,
        models.League.is_archived == True
    ).all()
    for l in leagues:
        l.members_count = db.query(models.LeagueMember).filter(models.LeagueMember.league_id == l.id).count()
    return leagues

def get_league(db: Session, league_id: int):
    return db.query(models.League).filter(models.League.id == league_id).first()

def get_league_members_with_stats(db: Session, league_id: int):
    # Get members
    members = db.query(models.LeagueMember).filter(models.LeagueMember.league_id == league_id).all()
    result = []

    league = get_league(db, league_id)

    # For now, simplistic mission counting
    for m in members:
        user = get_user(db, m.user_id)
        # Count completed missions
        query = db.query(models.UserMissionStatus).filter(
             models.UserMissionStatus.user_id == m.user_id,
             models.UserMissionStatus.status == "termine"
        )

        # Filter by league dates
        if league and league.start_date:
             query = query.filter(models.UserMissionStatus.completed_at >= league.start_date)
        if league and league.end_date:
             # Assuming end_date (YYYY-MM-DD) includes the full day, we can compare string directly
             # if completed_at is ISO including time, "2023-01-05" < "2023-01-05T10:00:00".
             # So strictly speaking, <= end_date usually excludes the day's events if they have time.
             # We should probably filter < (end_date + 1 day).
             # But for simplicity let's rely on simple string compare but adding time suffix for safe measure
             # or simply trusting standard string compare logic for now.
             # A robust way: completed_at <= end_date + "T23:59:59"
             query = query.filter(models.UserMissionStatus.completed_at <= league.end_date + "T23:59:59")

        completed_count = query.count()

        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "username": user.username,
            "joined_at": m.joined_at,
            "missions_completed": completed_count
        })
    return result

def invite_user_to_league(db: Session, league_id: int, inviter_id: int, invitee_id: int):
    # Check if already member
    exists = db.query(models.LeagueMember).filter(
        models.LeagueMember.league_id == league_id,
        models.LeagueMember.user_id == invitee_id
    ).first()
    if exists:
        return None # Already member

    # Check if invite exists
    invite = db.query(models.LeagueInvite).filter(
        models.LeagueInvite.league_id == league_id,
        models.LeagueInvite.invitee_id == invitee_id,
        models.LeagueInvite.status == "pending"
    ).first()

    if invite:
        return invite

    new_invite = models.LeagueInvite(
        league_id=league_id,
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        status="pending"
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return new_invite

def get_pending_league_invites(db: Session, user_id: int):
    return db.query(models.LeagueInvite).filter(
        models.LeagueInvite.invitee_id == user_id,
        models.LeagueInvite.status == "pending"
    ).all()

def get_league_invites(db: Session, league_id: int):
    return db.query(models.LeagueInvite).filter(
        models.LeagueInvite.league_id == league_id,
        models.LeagueInvite.status == "pending"
    ).all()

def respond_league_invite(db: Session, invite_id: int, accept: bool):
    invite = db.query(models.LeagueInvite).filter(models.LeagueInvite.id == invite_id).first()
    if not invite:
        return None

    if accept:
        invite.status = "accepted"
        # Add to members
        new_member = models.LeagueMember(
            league_id=invite.league_id,
            user_id=invite.invitee_id,
            joined_at=datetime.now().isoformat()
        )
        db.add(new_member)
    else:
        invite.status = "rejected"

    db.commit()
    return invite

