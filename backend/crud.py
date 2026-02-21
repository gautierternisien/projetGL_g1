from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas
from datetime import datetime
import unicodedata

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

NGC_DEFAULT_BREAKDOWN = {
    'transport': 2200,
    'logement': 1700,
    'alimentation': 2000,
    'divers': 1200,
    'services_societaux': 1459,
}

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
    return db.query(models.User).filter(models.User.username.ilike(pattern), models.User.is_deleted == False).limit(limit).all()

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

def delete_user(db: Session, user_id: int):
    import random
    import string
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        # Générer un code aléatoire de 5 caractères
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        # Modifier le username
        db_user.username = f"utilisateur_supprimé_{user_id}_{code}"
        # Supprimer les informations sensibles
        db_user.email = None
        db_user.hashed_password = None
        db_user.first_name = None
        db_user.last_name = None
        db_user.profile_image = None
        db_user.is_active = False
        db_user.is_deleted = True
        db.commit()
        db.refresh(db_user)
    return db_user

def get_questions_by_category(db: Session, category_name: str):
    return db.query(models.Question).filter(models.Question.category_name == category_name).all()

def get_user_ngc_answers(db: Session, user_id: int):
    return db.query(models.UserNgcAnswers).filter(models.UserNgcAnswers.user_id == user_id).first()

def update_user_ngc_answers(db: Session, user_id: int, data_json: str):
    record = get_user_ngc_answers(db, user_id)
    now = datetime.utcnow().isoformat()
    if not record:
        record = models.UserNgcAnswers(user_id=user_id, data=data_json, updated_at=now)
        db.add(record)
    else:
        record.data = data_json
        record.updated_at = now

    db.commit()
    db.refresh(record)
    return record

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

def get_completed_missions_count(db: Session, user_id: int):
    return db.query(models.UserMissionStatus).filter(
        models.UserMissionStatus.user_id == user_id,
        models.UserMissionStatus.status == "termine"
    ).count()

# update_mission_status merged into update_user_mission_status


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

    question = db.query(models.Question).filter(models.Question.id == answer.question_id).first()

    if question:
        category_name = question.category_name

        # Vérifie si on a déjà eu la récompense pour cette catégorie
        existing_reward = db.query(models.UserQuestionnaireReward).filter(
            models.UserQuestionnaireReward.user_id == user_id,
            models.UserQuestionnaireReward.category_name == category_name
        ).first()

        if not existing_reward:
            # Compte le nombre total de questions dans cette catégorie
            total_questions = db.query(models.Question).filter(models.Question.category_name == category_name).count()

            # Compte le nombre de réponses de l'utilisateur pour cette catégorie
            # (Attention : ceci suppose que UserAnswer contient une ligne par question répondue)
            answered_count = db.query(models.UserAnswer).join(models.Question).filter(
                models.UserAnswer.user_id == user_id,
                models.Question.category_name == category_name
            ).count()

            # Si tout est répondu
            if total_questions > 0 and answered_count >= total_questions:
                # Ajout XP
                add_user_xp(db, user_id, 50)
                # Marquer comme récompensé
                reward = models.UserQuestionnaireReward(user_id=user_id, category_name=category_name)
                db.add(reward)
                db.commit()

    return db_answer


def _normalize_ngc_category_key(raw_key: str) -> str:
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', str(raw_key).strip().lower())
        if unicodedata.category(c) != 'Mn'
    )
    normalized = normalized.strip()
    if normalized == 'services societaux':
        return 'services_societaux'
    return normalized


def _safe_int(value, fallback: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return fallback


def _normalize_ngc_progress_map(raw_progress):
    normalized_progress = {}
    for k, v in (raw_progress or {}).items():
        key = _normalize_ngc_category_key(k)
        if key not in ('transport', 'logement', 'alimentation', 'divers'):
            continue
        normalized_progress[key] = max(0, min(100, _safe_int(v, 0)))
    return normalized_progress


def _get_default_ngc_breakdown(rows_by_user, progress_by_user):
    candidates = []

    for user_id, row in rows_by_user.items():
        progress_row = progress_by_user.get(user_id)
        if not progress_row:
            continue

        if (
            _safe_int(getattr(progress_row, 'transport', 0), 0) != 0
            or _safe_int(getattr(progress_row, 'logement', 0), 0) != 0
            or _safe_int(getattr(progress_row, 'alimentation', 0), 0) != 0
            or _safe_int(getattr(progress_row, 'divers', 0), 0) != 0
        ):
            continue

        candidate = {
            'transport': _safe_int(getattr(row, 'transport', 0), NGC_DEFAULT_BREAKDOWN['transport']),
            'logement': _safe_int(getattr(row, 'logement', 0), NGC_DEFAULT_BREAKDOWN['logement']),
            'alimentation': _safe_int(getattr(row, 'alimentation', 0), NGC_DEFAULT_BREAKDOWN['alimentation']),
            'divers': _safe_int(getattr(row, 'divers', 0), NGC_DEFAULT_BREAKDOWN['divers']),
            'services_societaux': _safe_int(
                getattr(row, 'services_societaux', 0),
                NGC_DEFAULT_BREAKDOWN['services_societaux'],
            ),
        }

        if sum(candidate.values()) <= 0:
            continue

        candidates.append(candidate)

    if not candidates:
        return dict(NGC_DEFAULT_BREAKDOWN)

    averaged = {}
    for key in NGC_DEFAULT_BREAKDOWN:
        averaged[key] = round(sum(c[key] for c in candidates) / len(candidates))

    if sum(averaged.values()) <= 0:
        return dict(NGC_DEFAULT_BREAKDOWN)

    return averaged


def upsert_user_ngc_stats(db: Session, user_id: int, payload: schemas.NgcStatsPayload):
    details = payload.details_by_category or {}
    progress = _normalize_ngc_progress_map(payload.category_progress or {})

    normalized_details = {}
    for k, v in details.items():
        normalized_details[_normalize_ngc_category_key(k)] = _safe_int(v, 0)

    row = db.query(models.UserNgcStat).filter(models.UserNgcStat.user_id == user_id).first()
    if not row:
        row = models.UserNgcStat(user_id=user_id)
        db.add(row)

    row.global_score = _safe_int(payload.global_score, 8559)
    row.transport = normalized_details.get('transport', 0)
    row.logement = normalized_details.get('logement', 0)
    row.alimentation = normalized_details.get('alimentation', 0)
    row.divers = normalized_details.get('divers', 0)
    row.services_societaux = normalized_details.get('services_societaux', 0)
    row.updated_at = datetime.now()

    progress_row = db.query(models.UserNgcProgress).filter(models.UserNgcProgress.user_id == user_id).first()
    if not progress_row:
        progress_row = models.UserNgcProgress(user_id=user_id)
        db.add(progress_row)

    progress_row.transport = progress.get('transport', 0)
    progress_row.logement = progress.get('logement', 0)
    progress_row.alimentation = progress.get('alimentation', 0)
    progress_row.divers = progress.get('divers', 0)
    progress_row.updated_at = datetime.now()

    db.commit()
    db.refresh(row)
    return row


def get_ngc_stats_aggregate(db: Session):
    all_users = db.query(models.User.id).filter(models.User.is_deleted == False).all()
    if not all_users:
        return None

    rows = db.query(models.UserNgcStat).all()
    rows_by_user = {row.user_id: row for row in rows}
    progress_rows = db.query(models.UserNgcProgress).all()
    progress_by_user = {row.user_id: row for row in progress_rows}
    default_breakdown = _get_default_ngc_breakdown(rows_by_user, progress_by_user)

    total = len(all_users)

    sums = {
        'transport': 0,
        'logement': 0,
        'alimentation': 0,
        'divers': 0,
        'services_societaux': 0,
    }

    global_sum = 0
    for user in all_users:
        user_id = user.id
        row = rows_by_user.get(user_id)

        if row:
            global_score = _safe_int(row.global_score, 8559)
            global_sum += global_score

            progress_row = progress_by_user.get(user_id)
            for key in ('transport', 'logement', 'alimentation', 'divers'):
                category_progress = _safe_int(getattr(progress_row, key, 0), 0) if progress_row else 0
                if category_progress >= 100:
                    sums[key] += _safe_int(getattr(row, key, 0), default_breakdown[key])
                else:
                    sums[key] += default_breakdown[key]

            # Services sociétaux reste une composante "de base" du modèle.
            sums['services_societaux'] += default_breakdown['services_societaux']
            continue

        # User has no pushed NGC stats yet: fallback to neutral model baseline.
        global_sum += 8559
        sums['transport'] += default_breakdown['transport']
        sums['logement'] += default_breakdown['logement']
        sums['alimentation'] += default_breakdown['alimentation']
        sums['divers'] += default_breakdown['divers']
        sums['services_societaux'] += default_breakdown['services_societaux']

    return {
        'global_score': round(global_sum / total),
        'details_by_category': {
            'transport': round(sums['transport'] / total),
            'logement': round(sums['logement'] / total),
            'alimentation': round(sums['alimentation'] / total),
            'divers': round(sums['divers'] / total),
            'services societaux': round(sums['services_societaux'] / total),
        },
        'user_count': total,
    }

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

def get_user_mission_statuses_dict(db: Session, user_id: int):
    statuses = db.query(models.UserMissionStatus).filter(models.UserMissionStatus.user_id == user_id).all()
    return {s.mission_id: s.status for s in statuses}

def update_user_mission_status(db: Session, user_id: int, mission_id: int, status: str):
    db_status = get_user_mission_status(db, user_id, mission_id)

    was_completed = db_status and db_status.status == 'termine'

    if db_status:
        db_status.status = status
    else:
        db_status = models.UserMissionStatus(user_id=user_id, mission_id=mission_id, status=status)
        db.add(db_status)

    if status == 'termine':
        db_status.completed_at = datetime.now()
        if not was_completed:
            mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
            if mission:
                # 1. Points de mission
                points = 35 if mission.mission_type == 'long_term' else 10
                add_user_xp(db, user_id, points)


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
    now = datetime.now()
    db_league = models.League(
        name=league.name,
        start_date=league.start_date,
        end_date=league.end_date,
        created_at=now,
        is_archived=False
    )
    db.add(db_league)
    db.commit()
    db.refresh(db_league)

    # Add creator as member
    member = models.LeagueMember(
        league_id=db_league.id,
        user_id=creator_id,
        joined_at=now
    )
    db.add(member)
    db.commit()
    db.refresh(db_league)

    db_league.members_count = 1

    add_user_xp(db, creator_id, 5)
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
            "username": "utilisateur_supprimé" if user.is_deleted else user.username,
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
            joined_at=datetime.now()
        )
        db.add(new_member)
    else:
        invite.status = "rejected"

    db.commit()
    return invite

def get_category_by_name(db: Session, name: str):
    return db.query(models.Category).filter(models.Category.name == name).first()

def create_category(db: Session, name: str):
    cat = models.Category(name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

def create_question(db: Session, question_data: dict, category_name: str):
    # Check if exists by ID
    q = db.query(models.Question).filter(models.Question.id == question_data['id']).first()
    if not q:
        q = models.Question(
            id=question_data['id'],
            text=question_data['text'],
            category_name=category_name
        )
        db.add(q)
        db.commit()
        db.refresh(q)

        # Create options
        for opt in question_data.get('options', []):
            o = models.Option(
                question_id=q.id,
                label=opt['label'],
                value=opt['value'],
                score=opt.get('score', 0),
                is_default=opt.get('is_default', False)
            )
            db.add(o)
        db.commit()
    return q

def create_mission(db: Session, mission_data: dict, category_name: str):
    m = db.query(models.Mission).filter(models.Mission.id == mission_data['id']).first()

    m_type = mission_data.get('mission_type', 'one_shot')

    # Si la mission n'existe pas, on la crée
    if not m:
        m = models.Mission(
            id=mission_data['id'],
            title=mission_data['title'],
            description=mission_data.get('description', ""),
            category_name=category_name,
            # AJOUT ICI : On enregistre les conditions
            conditions=mission_data.get('conditions', []),
            mission_type=m_type
        )
        db.add(m)
    else:
        # AJOUT ICI : Si elle existe déjà, on met à jour ses infos (titre, desc, conditions)
        # Cela permet d'appliquer vos changements sans supprimer la BDD
        m.title = mission_data['title']
        m.description = mission_data.get('description', "")
        m.conditions = mission_data.get('conditions', [])
        m.category_name = category_name
        m.mission_type=m_type

    db.commit()
    db.refresh(m)
    return m


# --- TROPHY CRUD ---

def create_trophy(db: Session, trophy_data: dict):
    """Create a trophy if it doesn't exist"""
    t = db.query(models.Trophy).filter(models.Trophy.name == trophy_data['name']).first()
    if not t:
        t = models.Trophy(
            name=trophy_data['name'],
            title=trophy_data['title'],
            description=trophy_data['description'],
            icon=trophy_data['icon'],
            tier=trophy_data['tier'],
            requirement_type=trophy_data['requirement_type'],
            requirement_value=trophy_data['requirement_value'],
            milestones=trophy_data.get('milestones', [])
        )
        db.add(t)
        db.commit()
        db.refresh(t)
    return t


def get_all_trophies(db: Session):
    """Get all trophies"""
    return db.query(models.Trophy).all()


def get_user_trophies(db: Session, user_id: int):
    """Get all trophies for a user with progress"""
    return db.query(models.UserTrophy).filter(
        models.UserTrophy.user_id == user_id
    ).all()


def get_user_trophy(db: Session, user_id: int, trophy_id: int):
    """Get a specific user trophy"""
    return db.query(models.UserTrophy).filter(
        models.UserTrophy.user_id == user_id,
        models.UserTrophy.trophy_id == trophy_id
    ).first()


def upsert_user_trophy(db: Session, user_id: int, trophy_id: int, progress: int, is_obtained: bool = False, obtained_at: str = None, last_milestone_date: str = None):
    """Create or update a user trophy"""
    ut = get_user_trophy(db, user_id, trophy_id)
    if not ut:
        ut = models.UserTrophy(
            user_id=user_id,
            trophy_id=trophy_id,
            progress=progress,
            is_obtained=is_obtained,
            obtained_at=obtained_at,
            last_milestone_date=last_milestone_date
        )
        db.add(ut)
    else:
        ut.progress = progress
        ut.is_obtained = is_obtained
        if obtained_at and not ut.obtained_at:
            ut.obtained_at = obtained_at
        if last_milestone_date:
            ut.last_milestone_date = last_milestone_date
    db.commit()
    db.refresh(ut)
    return ut


def record_user_login(db: Session, user_id: int):
    """Record a user login"""
    from datetime import datetime
    login = models.UserLogin(
        user_id=user_id,
        login_at=datetime.utcnow()
    )
    db.add(login)
    db.commit()
    return login


def get_user_login_count(db: Session, user_id: int):
    """Get the total number of logins for a user"""
    return db.query(models.UserLogin).filter(models.UserLogin.user_id == user_id).count()


def update_trophy_progress(db: Session, user_id: int):
    """Update trophy progress for a user based on their activities"""
    from datetime import datetime

    # Get login count and mission count
    login_count = get_user_login_count(db, user_id)
    mission_count = get_completed_missions_count(db, user_id)

    # Get all trophies
    trophies = get_all_trophies(db)

    for trophy in trophies:
        # Determine the count based on trophy type
        if trophy.requirement_type == "login_count":
            count = login_count
        elif trophy.requirement_type == "mission_count":
            count = mission_count
        else:
            continue

        progress = min(count, trophy.requirement_value)
        is_obtained = count >= trophy.requirement_value
        obtained_at = None
        last_milestone_date = None

        # Check if already obtained
        existing_trophy = get_user_trophy(db, user_id, trophy.id)

        # Get milestones from database
        milestones = trophy.milestones or []

        # Preserve existing obtained_at if trophée is already obtained
        if existing_trophy and existing_trophy.obtained_at:
            obtained_at = existing_trophy.obtained_at

        # If trophée just became obtained
        if is_obtained and existing_trophy and not existing_trophy.is_obtained:
            obtained_at = datetime.utcnow()
        elif is_obtained and not existing_trophy:
            obtained_at = datetime.utcnow()

        # Update last_milestone_date when a milestone is reached
        # Chercher la médaille la plus haute obtenue (tri décroissant)
        if milestones:
            sorted_milestones = sorted(milestones, key=lambda m: m["value"], reverse=True)
            for milestone in sorted_milestones:
                if count >= milestone["value"]:
                    # Only update if not already set or if we're reaching a new milestone
                    if not existing_trophy or not existing_trophy.last_milestone_date or existing_trophy.progress < count:
                        last_milestone_date = datetime.utcnow()
                    else:
                        last_milestone_date = existing_trophy.last_milestone_date
                    break

        upsert_user_trophy(db, user_id, trophy.id, progress, is_obtained, obtained_at, last_milestone_date)


# --- USER PREFERENCES ---

def get_user_preferences(db: Session, user_id: int):
    pref = db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).first()
    if not pref:
        # Si pas de préférences, on renvoie un objet par défaut non sauvegardé
        # Le frontend saura qu'il faut afficher l'onboarding car has_completed_onboarding = False
        return models.UserPreference(user_id=user_id, data={}, has_completed_onboarding=False)
    return pref

def update_user_preferences(db: Session, user_id: int, pref_data: schemas.UserPreferenceCreate):
    pref = db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).first()

    if not pref:
        pref = models.UserPreference(
            user_id=user_id,
            data=pref_data.data,
            has_completed_onboarding=pref_data.has_completed_onboarding
        )
        db.add(pref)
    else:
        pref.data = pref_data.data
        pref.has_completed_onboarding = pref_data.has_completed_onboarding

    db.commit()
    db.refresh(pref)
    return pref


def add_user_xp(db: Session, user_id: int, amount: int):
    user = get_user(db, user_id)
    if user:
        user.xp += amount
        db.commit()
        db.refresh(user)
    return user

def award_category_completion_xp(db: Session, user_id: int, category_name: str):
    """
    Attribue 50 XP pour la complétion d'une catégorie si pas déjà reçu.
    """
    # Vérifier si déjà récompensé
    existing_reward = db.query(models.UserQuestionnaireReward).filter(
        models.UserQuestionnaireReward.user_id == user_id,
        models.UserQuestionnaireReward.category_name == category_name
    ).first()

    if existing_reward:
        return None # Déjà gagné

    # Donner 50 XP
    add_user_xp(db, user_id, 50)

    # Marquer comme récompensé
    reward = models.UserQuestionnaireReward(user_id=user_id, category_name=category_name)
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward

def process_league_rewards(db: Session):
    """
    Vérifie toutes les ligues terminées qui n'ont pas encore distribué leurs récompenses.
    Calcule le classement et attribue l'XP.
    """
    today = datetime.now().strftime("%Y-%m-%d") # Format ISO YYYY-MM-DD

    # 1. Récupérer les ligues terminées (date de fin passée) et non traitées
    # On suppose que end_date est inclusif, donc terminé si today > end_date
    # Ou si on veut être précis à la seconde près, il faudrait des datetime complets.
    # Ici on fait simple : si on est le lendemain de la fin.

    # Note: Dans votre modèle, end_date est une string ISO.
    # Pour être sûr, on prend celles dont la date est < today (donc hier ou avant).
    leagues_to_process = db.query(models.League).filter(
        models.League.end_date < today,
        models.League.rewards_distributed == False
    ).all()

    for league in leagues_to_process:
        print(f"Distribution des récompenses pour la ligue {league.name} ({league.id})...")

        # 2. Récupérer les membres et leurs scores
        members_stats = get_league_members_with_stats(db, league.id)

        # 3. Trier par score décroissant (missions_completed)
        # En cas d'égalité, on peut départager par date de jointure ou laisser ex-aequo.
        # Ici : tri simple.
        sorted_members = sorted(members_stats, key=lambda x: x['missions_completed'], reverse=True)

        # 4. Attribuer les points selon le rang
        for index, member_data in enumerate(sorted_members):
            rank = index + 1
            user_id = member_data['user_id']
            xp_bonus = 0

            if rank == 1:
                xp_bonus = 75
            elif rank == 2:
                xp_bonus = 50
            elif rank == 3:
                xp_bonus = 30
            else:
                xp_bonus = 20 # Pour le reste

            # Donner l'XP
            if xp_bonus > 0:
                add_user_xp(db, user_id, xp_bonus)
                print(f"  - User {member_data['username']} (Rang {rank}) : +{xp_bonus} XP")

        # 5. Marquer la ligue comme traitée
        league.rewards_distributed = True
        db.commit()