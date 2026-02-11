from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict
from datetime import timedelta, datetime
from routes import router

import crud, models, schemas, utils
from database import SessionLocal, engine
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PGL API",
    description="API pour l'application ProjetGL : Calcul d'empreinte carbone, missions, et aspects sociaux.",
    version="1.0.0"
)

# On inclut le router qui sert le fichier rules.json
app.include_router(router)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validated user getter
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = utils.jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=user_id_str)
    except utils.JWTError:
        raise credentials_exception

    try:
        user_id = int(token_data.email)
        user = crud.get_user(db, user_id)
    except (ValueError, TypeError):
        user = crud.get_user_by_username(db, username=token_data.email)

    if user is None:
        raise credentials_exception
    return user

# --- CONSTANTES ---

# Score par défaut (moyenne française approx) utilisé comme fallback
NGC_DEFAULT_SCORE = 8559

# --- SIMULATION DES MISSIONS (On garde ça pour l'instant) ---
MISSIONS_DB = {
    "transport": [
        { "id": 1, "title": 'Prendre le vélo', "description": 'Remplacez un trajet voiture par vélo', "status": 'en_cours' },
        { "id": 2, "title": 'Privilégier les transports en commun', "description": 'Utilisez le bus ou le tram pour au moins un trajet cette semaine', "status": 'new' },
    ],
    "logement": [
        { "id": 101, "title": 'Isolation fenêtre', "description": 'Vérifier les joints des fenêtres', "status": 'new' },
        { "id": 3, "title": 'Baisser le chauffage', "description": 'Réduire la température de 1°C pendant une semaine', "status": 'en_cours' },
    ],
    "alimentation": [
        { "id": 4, "title": 'Recette végétarienne', "description": 'Essayez une recette végétarienne', "status": 'new' },
        { "id": 5, "title": 'Acheter local', "description": 'Acheter au moins un produit local et de saison', "status": 'termine' },
    ],
    "divers": [
        { "id": 14, "title": 'Acheter d’occasion', "description": 'Acheter un article d’occasion cette semaine', "status": 'en_cours' },
        { "id": 15, "title": 'Attendre avant achat', "description": 'Attendre 48h avant un achat non essentiel', "status": 'new' },
    ],
}

# --- DATA INITIALIZATION ---
def init_db_from_static_data(db: Session):
    """
    Initialise uniquement les missions et catégories si nécessaire.
    Les questions sont maintenant gérées par Publicodes (rules.json).
    """
    # On initialise les missions
    for category_name, missions in MISSIONS_DB.items():
        # On s'assure que la catégorie existe
        cat = crud.get_category_by_name(db, category_name)
        if not cat:
            cat = crud.create_category(db, category_name)

        for m_data in missions:
            crud.create_mission(db, m_data, category_name)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        init_db_from_static_data(db)
    finally:
        db.close()

# Feed des activités : { "username_receiver": [ { "sender_username": "...", "mission_id": 1, ... } ] }
user_feed_db: Dict[str, List[Dict]] = {}

# --- ROUTES API ---

@app.post("/register", response_model=schemas.User, tags=["Authentication"], summary="Register a new user")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisée")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Pseudo déjà utilisé")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token, tags=["Authentication"], summary="Login to get access token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        user = crud.get_user_by_email(db, email=form_data.username)

    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pseudo/Email ou Mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User, tags=["Users"], summary="Get current user profile")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ... (Gardez les routes PUT /users/me/... ici, inchangées) ...
@app.put("/users/me/email", response_model=schemas.User, tags=["Users"])
async def update_user_email(new_email: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, email=new_email)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Adresse mail déjà utilisée")
    return crud.update_user_email(db, current_user.id, new_email)

@app.put("/users/me/username", response_model=schemas.User, tags=["Users"])
async def update_user_username(new_username: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_username(db, username=new_username)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Pseudo déjà utilisé")

    # Migration des feeds (logique existante)
    old_username = current_user.username
    user_id = current_user.id
    if old_username in user_feed_db:
        user_feed_db[new_username] = user_feed_db.pop(old_username)
    for feed in user_feed_db.values():
        for act in feed:
            if act.get("sender_id") == user_id:
                act["sender_username"] = new_username

    return crud.update_user_username(db, current_user.id, new_username)

@app.put("/users/me/first_name", response_model=schemas.User, tags=["Users"])
async def update_user_first_name(new_first_name: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user_first_name(db, current_user.id, new_first_name)

@app.put("/users/me/last_name", response_model=schemas.User, tags=["Users"])
async def update_user_last_name(new_last_name: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user_last_name(db, current_user.id, new_last_name)

@app.put("/users/me/password", response_model=schemas.User, tags=["Users"])
async def update_user_password(current_password: str, new_password: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not crud.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    return crud.update_user_password(db, current_user.id, new_password)

# ... (Gardez les routes Friends inchangées ici) ...
@app.get("/users", response_model=List[schemas.UserPublic], tags=["Users"])
async def search_users(prefix: str = "", current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if len(prefix) < 3: return []
    users = crud.search_users_by_prefix(db, prefix)
    friend_ids = set(crud.get_accepted_friends(db, current_user.id))
    pending_requests = crud.get_pending_requests_sent(db, current_user.id)
    pending_receiver_ids = set(r.receiver_id for r in pending_requests)
    filtered = [u for u in users if u.id != current_user.id and u.id not in friend_ids and u.id not in pending_receiver_ids]
    return filtered

@app.get("/friends", response_model=List[schemas.UserPublic], tags=["Friends"])
async def list_friends(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    friend_ids = crud.get_accepted_friends(db, current_user.id)
    if not friend_ids: return []
    return crud.get_users_by_ids(db, friend_ids)

@app.get("/friends/activity", response_model=List[schemas.FriendActivity], tags=["Friends"])
async def get_friends_activity(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_feed = user_feed_db.get(current_user.username, [])
    response_activities = []
    for activity in reversed(my_feed):
        response_activities.append(schemas.FriendActivity(
            friend_id=activity["sender_id"],
            friend_username=activity["sender_username"],
            mission_title=activity["mission_title"],
            mission_id=activity["mission_id"],
            status=activity["status"],
            timestamp=activity["timestamp"].isoformat() if activity.get("timestamp") else None
        ))
    return response_activities

@app.post("/friend-requests/{friend_id}", tags=["Friends"])
async def send_friend_request(friend_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = crud.get_user(db, friend_id)
    if not target: raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    try:
        req = crud.send_friend_request(db, current_user.id, friend_id)
        return {"id": req.id, "status": "pending", "receiver": {"id": target.id, "username": target.username}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/friend-requests/pending", response_model=List[schemas.FriendRequestSchema], tags=["Friends"])
async def get_pending_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_pending_requests_sent(db, current_user.id)
    return [{"id": r.id, "sender": {"id": r.sender.id, "username": r.sender.username, "profile_image": r.sender.profile_image}, "receiver": {"id": r.receiver.id, "username": r.receiver.username, "profile_image": r.receiver.profile_image}, "status": r.status} for r in requests]

@app.get("/friend-requests/incoming", response_model=List[schemas.FriendRequestSchema], tags=["Friends"])
async def get_incoming_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_incoming_requests(db, current_user.id)
    return [{"id": r.id, "sender": {"id": r.sender.id, "username": r.sender.username, "profile_image": r.sender.profile_image}, "receiver": {"id": r.receiver.id, "username": r.receiver.username, "profile_image": r.receiver.profile_image}, "status": r.status} for r in requests]

@app.put("/friend-requests/{request_id}/accept", tags=["Friends"])
async def accept_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        req = crud.accept_friend_request(db, request_id)
        return {"accepted": True, "request_id": req.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/friend-requests/{request_id}/reject", tags=["Friends"])
async def reject_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        crud.reject_friend_request(db, request_id)
        return {"rejected": True, "request_id": request_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/friend-requests/{request_id}/cancel", tags=["Friends"])
async def cancel_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        crud.cancel_friend_request(db, request_id)
        return {"cancelled": True, "request_id": request_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/friends/{friend_id}", tags=["Friends"])
async def delete_friend(friend_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.query(models.FriendRequest).filter(
        ((models.FriendRequest.sender_id == current_user.id) & (models.FriendRequest.receiver_id == friend_id)) |
        ((models.FriendRequest.sender_id == friend_id) & (models.FriendRequest.receiver_id == current_user.id)),
        models.FriendRequest.status == "accepted"
    ).first()
    if req:
        crud.remove_friend(db, current_user.id, friend_id)
        db.delete(req)
        db.commit()
        # Nettoyage feed (code simplifié)
        friend_user = crud.get_user(db, friend_id)
        if friend_user:
            friend_username = friend_user.username
            if current_user.username in user_feed_db:
                user_feed_db[current_user.username] = [act for act in user_feed_db[current_user.username] if act["sender_username"] != friend_username]
            if friend_username in user_feed_db:
                user_feed_db[friend_username] = [act for act in user_feed_db[friend_username] if act["sender_username"] != current_user.username]
    return {"deleted": True}

@app.get("/", tags=["General"], summary="Root endpoint")
async def root():
    # On renvoie les clés de la DB Missions pour compatibilité, ou les catégories statiques
    return {
        "message": "API Questionnaire Multi-Catégories (Mode Publicodes)",
        "available_categories": list(MISSIONS_DB.keys())
    }

# NOTE : Les routes /questions/{category} et /answers/... ont été supprimées
# car le frontend utilise maintenant Publicodes et /ngc/stats/me.

@app.get("/missions/{category}", response_model=List[schemas.Mission], tags=["Missions"], summary="Get missions by category")
async def get_missions_by_category(category: str, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Récupère les missions d'une catégorie spécifique.
    """
    if user_id:
        return crud.get_missions_by_category(db, category, user_id)
    else:
        # anonymous view -> default status
        missions = db.query(models.Mission).filter(models.Mission.category_name == category).all()
        result = []
        for m in missions:
            m_data = schemas.Mission.model_validate(m)
            m_data.status = "new"
            result.append(m_data)

        # Fallback si la DB est vide mais que la variable statique existe
        if not result and category in MISSIONS_DB:
            for m in MISSIONS_DB[category]:
                m_obj = schemas.Mission(**m)
                m_obj.status = "new"
                result.append(m_obj)

        if not result:
            raise HTTPException(status_code=404, detail="Catégorie de missions non trouvée")

        return result

@app.put("/missions/{mission_id}", tags=["Missions"], summary="Update mission status")
async def update_mission(mission_id: int, payload: schemas.MissionUpdate, db: Session = Depends(get_db)):
    """
    Met à jour le statut d'une mission.
    """
    mission_db = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    mission_title = "Unknown Mission"

    if not mission_db:
        found = False
        for cat, missions in MISSIONS_DB.items():
            for m in missions:
                if int(m.get('id')) == mission_id:
                    mission_title = m.get('title', 'Mission')
                    found = True
                    break
            if found: break
        if not found:
            raise HTTPException(status_code=404, detail="Mission non trouvée")
    else:
        mission_title = mission_db.title

    if payload.user_id:
        crud.update_user_mission_status(db, payload.user_id, mission_id, payload.status)

        # Feed activity
        if payload.status == 'termine':
            user = crud.get_user(db, payload.user_id)
            if user:
                friend_ids = crud.get_accepted_friends(db, user.id)
                friends = crud.get_users_by_ids(db, friend_ids)
                new_activity = {
                    "sender_id": payload.user_id,
                    "sender_username": user.username,
                    "mission_id": mission_id,
                    "mission_title": mission_title,
                    "status": payload.status,
                    "timestamp": datetime.now()
                }
                for friend in friends:
                    if friend.username not in user_feed_db: user_feed_db[friend.username] = []
                    user_feed_db[friend.username].append(new_activity)

        return {"id": mission_id, "status": payload.status}
    else:
        raise HTTPException(status_code=400, detail="User ID is required for mission update")

@app.get("/users/{user_id}/profile", response_model=schemas.FriendProfile, tags=["Users"], summary="Get user public profile")
def read_user_profile(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    user = crud.get_user(db, user_id=user_id)
    if not user: raise HTTPException(status_code=404, detail="User not found")

    mission_count = crud.get_completed_missions_count(db, user_id=user_id)
    # Placeholder stats
    trophy_count = 0
    level = 5
    xp = 60

    return schemas.FriendProfile(
        id=user.id,
        username=user.username,
        mission_count=mission_count,
        trophy_count=trophy_count,
        level=level,
        xp=xp,
        profile_image=user.profile_image
    )

# --- ROUTES STATISTIQUES NGC (Publicodes) ---

@app.post("/ngc/stats/me", response_model=schemas.NgcStatsPayload)
def update_user_ngc_stats(
    payload: schemas.NgcStatsPayload,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = crud.upsert_user_ngc_stats(db, current_user.id, payload)

    # Return what we just saved, but reconstructed as NgcStatsPayload
    # (or simply return the input payload if everything went well)
    result = schemas.NgcStatsPayload(
        global_score=stats.global_score,
        details_by_category={
            'transport': stats.transport,
            'logement': stats.logement,
            'alimentation': stats.alimentation,
            'divers': stats.divers,
            'services societaux': stats.services_societaux
        },
        category_progress={} # Not persisting progress map in details response for now
    )
    return result


@app.get("/ngc/answers/me", response_model=schemas.UserNgcAnswersResponse)
def get_ngc_answers_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les réponses brutes (JSON) du questionnaire pour l'utilisateur connecté.
    """
    record = crud.get_user_ngc_answers(db, current_user.id)
    if not record:
        return schemas.UserNgcAnswersResponse(data={})

    try:
        data = json.loads(record.data) if record.data else {}
    except:
        data = {}

    return schemas.UserNgcAnswersResponse(data=data, updated_at=record.updated_at)


@app.post("/ngc/answers/me", response_model=schemas.UserNgcAnswersResponse)
def update_ngc_answers_me(
    payload: schemas.UserNgcAnswersCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enregistre les réponses brutes (JSON) du questionnaire.
    """
    data_str = json.dumps(payload.data)
    record = crud.update_user_ngc_answers(db, current_user.id, data_str)

    return schemas.UserNgcAnswersResponse(
        data=payload.data,
        updated_at=record.updated_at
    )

@app.get("/carbon-score/{user_id}", tags=["Statistics"], summary="Get user stored carbon score")
async def get_carbon_score(user_id: int, db: Session = Depends(get_db)):
    """
    Récupère le score carbone STOCKÉ en base (calculé par le front via Publicodes).
    Ne recalcule plus via l'ancienne QUESTIONS_DB.
    """
    ngc_stat = db.query(models.UserNgcStat).filter(models.UserNgcStat.user_id == user_id).first()

    if ngc_stat:
        return {
            "user_id": user_id,
            "global_score": ngc_stat.global_score,
            "average_national_score": NGC_DEFAULT_SCORE,
            "details_by_category": {
                "transport": ngc_stat.transport,
                "logement": ngc_stat.logement,
                "alimentation": ngc_stat.alimentation,
                "divers": ngc_stat.divers,
                "services_societaux": ngc_stat.services_societaux
            },
            "unit": "points_impact"
        }
    else:
        # Pas de données encore, on renvoie la moyenne par défaut
        return {
            "user_id": user_id,
            "global_score": NGC_DEFAULT_SCORE,
            "average_national_score": NGC_DEFAULT_SCORE,
            "details_by_category": {}, # Ou des valeurs par défaut
            "unit": "points_impact"
        }

@app.get("/global-stats", tags=["Statistics"], summary="Get global statistics")
async def get_global_stats(db: Session = Depends(get_db)):
    """
    Calcule les statistiques globales en utilisant les agrégats de UserNgcStat.
    """
    stats = {
        "global_score": NGC_DEFAULT_SCORE,
        "average_national_score": NGC_DEFAULT_SCORE,
        "details_by_category": {},
        "user_count": 0,
        "total_leagues": 0,
        "total_missions_completed": 0,
        "total_trophies": 0
    }

    try:
        # --- 1. EMPREINTE CARBONE & USER COUNT ---
        ngc_aggregate = crud.get_ngc_stats_aggregate(db)
        if ngc_aggregate and ngc_aggregate["user_count"] > 0:
            stats["global_score"] = ngc_aggregate["global_score"]
            stats["details_by_category"] = ngc_aggregate["details_by_category"]
            stats["user_count"] = ngc_aggregate["user_count"]

            if stats["global_score"] == 0:
                stats["global_score"] = NGC_DEFAULT_SCORE
        else:
            # Fallback si pas de stats NGC : on compte juste les inscrits
            count_users = db.query(models.User).count()
            stats["user_count"] = count_users

        # --- 2. LIGUES ---
        try:
            stats["total_leagues"] = db.query(models.League).count()
        except: pass

        # --- 3. MISSIONS ---
        try:
            stats["total_missions_completed"] = db.query(models.UserMissionStatus).filter(
                or_(
                    models.UserMissionStatus.status == 'termine',
                    models.UserMissionStatus.status == 'terminee',
                    models.UserMissionStatus.status == 'completed',
                    models.UserMissionStatus.status == 'done'
                )
            ).count()
        except Exception as e:
            print(f"Erreur stats missions: {e}")

        # --- 4. TROPHÉES ---
        if stats["total_missions_completed"] > 0:
            stats["total_trophies"] = int(stats["total_missions_completed"] // 3)

    except Exception as global_e:
        print(f"ERREUR CRITIQUE DANS GET_GLOBAL_STATS: {global_e}")

    return stats

# ... (Routes LEAGUES et PROFILE IMAGE inchangées) ...
@app.post("/leagues/", response_model=schemas.League, tags=["Leagues"])
async def create_league_route(league: schemas.LeagueCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try: return crud.create_league(db=db, league=league, creator_id=current_user.id)
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.get("/leagues/active", response_model=List[schemas.League], tags=["Leagues"])
def get_active_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_active_leagues_for_user(db, current_user.id)

@app.get("/leagues/archived", response_model=List[schemas.League], tags=["Leagues"])
def get_archived_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_archived_leagues_for_user(db, current_user.id)

@app.get("/leagues/invites", response_model=List[schemas.LeagueInvite], tags=["Leagues"])
def get_invites(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invites = crud.get_pending_league_invites(db, current_user.id)
    return [{"id": i.id, "league_id": i.league_id, "league_name": crud.get_league(db, i.league_id).name if crud.get_league(db, i.league_id) else "Unknown", "inviter_id": i.inviter_id, "inviter_name": crud.get_user(db, i.inviter_id).username, "invitee_id": i.invitee_id, "status": i.status} for i in invites]

@app.get("/leagues/{league_id}/invites", response_model=List[schemas.LeagueInvite], tags=["Leagues"])
def get_league_invites_route(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league: raise HTTPException(status_code=404, detail="League not found")
    if not any(m.user_id == current_user.id for m in league.members): raise HTTPException(status_code=403, detail="Not a member")
    invites = crud.get_league_invites(db, league_id)
    return [{"id": i.id, "league_id": i.league_id, "league_name": league.name, "inviter_id": i.inviter_id, "inviter_name": crud.get_user(db, i.inviter_id).username, "invitee_id": i.invitee_id, "status": i.status} for i in invites]

@app.get("/leagues/{league_id}", response_model=schemas.LeagueDetail, tags=["Leagues"])
def get_league_detail(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league: raise HTTPException(status_code=404, detail="League not found")
    if not any(m.user_id == current_user.id for m in league.members): raise HTTPException(status_code=403, detail="Not a member")
    members_stats = crud.get_league_members_with_stats(db, league_id)
    league_base = schemas.League.model_validate(league)
    league_data = league_base.model_dump()
    league_data['members_count'] = len(members_stats)
    return schemas.LeagueDetail(**league_data, members=[schemas.LeagueMember(**m) for m in members_stats])

@app.post("/leagues/{league_id}/invite/{user_id}", response_model=schemas.LeagueInvite, tags=["Leagues"])
def invite_user(league_id: int, user_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league: raise HTTPException(status_code=404, detail="League not found")
    if not any(m.user_id == current_user.id for m in league.members): raise HTTPException(status_code=403, detail="Not allowed")
    if user_id == current_user.id: raise HTTPException(status_code=400, detail="Cannot invite self")
    invite = crud.invite_user_to_league(db, league_id, current_user.id, user_id)
    if not invite: raise HTTPException(status_code=400, detail="Error inviting")
    return schemas.LeagueInvite(id=invite.id, league_id=invite.league_id, league_name=league.name, inviter_id=invite.inviter_id, inviter_name=current_user.username, invitee_id=invite.invitee_id, status=invite.status)

@app.put("/leagues/invites/{invite_id}/accept", response_model=schemas.LeagueInvite, tags=["Leagues"])
def accept_invite_route(invite_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = crud.respond_league_invite(db, invite_id, accept=True)
    if not invite: raise HTTPException(status_code=404, detail="Invite not found")
    return schemas.LeagueInvite(id=invite.id, league_id=invite.league_id, league_name=crud.get_league(db, invite.league_id).name, inviter_id=invite.inviter_id, inviter_name=crud.get_user(db, invite.inviter_id).username, invitee_id=invite.invitee_id, status=invite.status)

@app.put("/leagues/invites/{invite_id}/reject", response_model=schemas.LeagueInvite, tags=["Leagues"])
def reject_invite_route(invite_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = crud.respond_league_invite(db, invite_id, accept=False)
    if not invite: raise HTTPException(status_code=404, detail="Invite not found")
    return schemas.LeagueInvite(id=invite.id, league_id=invite.league_id, league_name=crud.get_league(db, invite.league_id).name, inviter_id=invite.inviter_id, inviter_name=crud.get_user(db, invite.inviter_id).username, invitee_id=invite.invitee_id, status=invite.status)

@app.delete("/leagues/{league_id}/leave", tags=["Leagues"])
def leave_league(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(models.LeagueMember).filter(models.LeagueMember.league_id == league_id, models.LeagueMember.user_id == current_user.id).first()
    if member:
        db.delete(member)
        db.commit()
    return {"status": "left"}

@app.put("/users/profile-image", response_model=schemas.User, tags=["Users"])
def update_profile_image(profile_image: str, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user(db, current_user.id)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.profile_image = profile_image
    db.commit()
    db.refresh(user)
    return user