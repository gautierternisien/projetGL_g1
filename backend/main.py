from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import timedelta, datetime

import crud, models, schemas, utils
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuration CORS pour autoriser le frontend (Vue.js) à parler au backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Port par défaut de Vite/Vue
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
        token_data = schemas.TokenData(email=user_id_str) # reuse email field for user_id/sub
    except utils.JWTError:
        raise credentials_exception

    # Try to get user by numeric ID first (new token format)
    try:
        user_id = int(token_data.email)
        user = crud.get_user(db, user_id)
    except (ValueError, TypeError):
        # Fall back to username lookup (old token format for backward compatibility)
        user = crud.get_user_by_username(db, username=token_data.email)

    if user is None:
        raise credentials_exception
    return user

# --- SIMULATION DE BASE DE DONNÉES ---
# Dans un vrai projet, utilisez SQLite ou PostgreSQL
QUESTIONS_DB = {
    "transport": [
        {
            "id": 1,
            "text": 'Quel est votre moyen de transport principal ?',
            "options": [
                { "label": 'Voiture personnelle (diesel)', "value": 'car', "score": 2000, "is_default": True },
                { "label": 'Voiture personnelle (électrique)', "value": 'electric car', "score": 950,},
                { "label": 'Transports en commun (Bus)', "value": 'bus', "score": 850 },
                { "label": 'Transports en commun (Rail)', "value": 'rail', "score": 40 },
                { "label": 'Vélo / Marche', "value": 'soft', "score": 0 },
            ],
        },
        {
            "id": 2,
            "text": 'Combien de km parcourez-vous par jour ?',
            "options": [
                { "label": 'Moins de 5 km', "value": 'low', "score": 100 },
                { "label": 'Entre 5 et 20 km', "value": 'medium', "score": 500, "is_default": True },
                { "label": 'Plus de 20 km', "value": 'high', "score": 1000 },
            ],
        },
        {
            "id": 3,
            "text": 'À quelle fréquence faites-vous du covoiturage ?',
            "options": [
                { "label": 'Régulièrement', "value": 'regular', "score": -200 }, # Bonus
                { "label": 'Rarement', "value": 'rare', "score": -50 },
                { "label": 'Jamais', "value": 'never', "score": 0, "is_default": True },
            ],
        },
        {
            "id": 4,
            "text": "Prenez-vous l'avion pour vos vacances ?",
            "options": [
                { "label": 'Plusieurs fois par an', "value": 'often', "score": 3000 },
                { "label": 'Une fois par an', "value": 'once', "score": 1000 },
                { "label": 'Rarement ou jamais', "value": 'never', "score": 0, "is_default": True },
            ],
        },
    ],
    "alimentation": [
        {
            "id": 101,
            "text": 'Combien de repas avec viande mangez-vous par semaine ?',
            "options": [
                { "label": 'Tous les jours', "value": 'high', "score": 2000 },
                { "label": '1 à 3 fois', "value": 'medium', "score": 1000, "is_default": True },
                { "label": 'Jamais (Végétarien)', "value": 'none', "score": 300 },
            ],
        },
        {
            "id": 102,
            "text": "Vous consommez de l'eau en ?",
            "options": [
                { "label": 'Bouteille', "value": 'plastic', "score": 200 },
                { "label": 'Robinet', "value": 'tap', "score": 10, "is_default": True },
            ],
        },
        {
            "id": 103,
            "text": 'Consommation de produits laitiers ?',
            "options": [
                { "label": 'Importante', "value": 'high', "score": 800 },
                { "label": 'Modérée', "value": 'medium', "score": 400, "is_default": True },
                { "label": 'Faible', "value": 'low', "score": 100 },
            ],
        },
        {
            "id": 104,
            "text": 'Jetez-vous de la nourriture ?',
            "options": [
                { "label": 'Souvent', "value": 'often', "score": 300 },
                { "label": 'Parfois', "value": 'sometimes', "score": 100, "is_default": True },
                { "label": 'Jamais', "value": 'never', "score": 0 },
            ],
        },
    ],
    "logement": [
        {
            "id": 201,
            "text": 'Système de chauffage principal ?',
            "options": [
                { "label": 'Fioul ou Gaz', "value": 'fossil', "score": 2500, "is_default": True },
                { "label": 'Électrique', "value": 'electric', "score": 800 },
                { "label": 'Pompe à chaleur / Bois', "value": 'renewable', "score": 200 },
            ],
        },
        {
            "id": 202,
            "text": 'Température l\'hiver ?',
            "options": [
                { "label": 'Plus de 21°C', "value": 'hot', "score": 500 },
                { "label": 'Entre 19°C et 21°C', "value": 'standard', "score": 200, "is_default": True },
                { "label": '19°C ou moins', "value": 'eco', "score": 0 },
            ],
        },
        {
            "id": 203,
            "text": 'Qualité de l\'isolation ?',
            "options": [
                { "label": 'Mauvaise', "value": 'bad', "score": 1000 },
                { "label": 'Moyenne', "value": 'average', "score": 500, "is_default": True },
                { "label": 'Bonne', "value": 'good', "score": 100 },
            ],
        },
        {
            "id": 204,
            "text": 'Surface par personne ?',
            "options": [
                { "label": 'Grande (+60m²)', "value": 'large', "score": 800 },
                { "label": 'Moyenne (30-60m²)', "value": 'medium', "score": 400, "is_default": True },
                { "label": 'Petite (-30m²)', "value": 'small', "score": 200 },
            ],
        },
        {
            "id": 205,
            "text": 'Quel type de jardin ?',
            "options": [
                { "label": "Pas d'éxtérieur ", "value": 'no', "score": 0, "is_default": True },
                { "label": "Grande pelouse avec beaucoup d'entretien et de dalles/béton", "value": "high", "score": 500},
                { "label": 'Jardin classique', "value": 'classic', "score": 50 },
                { "label": "Jardin positif pour le climat (Compostage, potager,récupération d'eau", "value": 'eco', "score": -200}
            ],
        }
    ],
    "divers": [
        {
            "id": 301,
            "text": 'Achat vêtements neufs ?',
            "options": [
                { "label": 'Chaque mois', "value": 'monthly', "score": 600 },
                { "label": 'Quelques fois par an', "value": 'yearly', "score": 200, "is_default": True },
                { "label": 'Seconde main', "value": 'rarely', "score": 50 },
            ],
        },
        {
            "id": 302,
            "text": 'Quand un appareil est en panne ?',
            "options": [
                { "label": 'Achat neuf', "value": 'replace', "score": 500 },
                { "label": 'Réparation', "value": 'repair', "score": 100, "is_default": True },
                { "label": 'Occasion', "value": 'secondhand', "score": 50 },
            ],
        },
    ],
}

# --- SIMULATION FAUSSE DES MISSIONS ---
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
    for category_name, questions in QUESTIONS_DB.items():
        # Get or create category
        cat = crud.get_category_by_name(db, category_name)
        if not cat:
            cat = crud.create_category(db, category_name)

        # Questions
        for q_data in questions:
            crud.create_question(db, q_data, category_name)

    # Also init missions
    for category_name, missions in MISSIONS_DB.items():
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

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisée")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Pseudo déjà utilisé")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Try to find user by username
    user = crud.get_user_by_username(db, username=form_data.username)
    # If not found, try by email
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

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.put("/users/me/email", response_model=schemas.User)
async def update_user_email(new_email: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if email already exists (excluding current user)
    existing_user = crud.get_user_by_email(db, email=new_email)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Adresse mail déjà utilisée")
    return crud.update_user_email(db, current_user.id, new_email)

@app.put("/users/me/username", response_model=schemas.User)
async def update_user_username(new_username: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if username already exists (excluding current user)
    existing_user = crud.get_user_by_username(db, username=new_username)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Pseudo déjà utilisé")
    
    # Before updating, migrate data from old username to numeric user_id in in-memory stores
    old_username = current_user.username
    user_id = current_user.id
    
    # Migrate personal feed key and refresh sender_username in existing activities
    if old_username in user_feed_db:
        user_feed_db[new_username] = user_feed_db.pop(old_username)
    for feed in user_feed_db.values():
        for act in feed:
            if act.get("sender_id") == user_id:
                act["sender_username"] = new_username
    
    return crud.update_user_username(db, current_user.id, new_username)

@app.put("/users/me/first_name", response_model=schemas.User)
async def update_user_first_name(new_first_name: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user_first_name(db, current_user.id, new_first_name)

@app.put("/users/me/last_name", response_model=schemas.User)
async def update_user_last_name(new_last_name: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user_last_name(db, current_user.id, new_last_name)

@app.put("/users/me/password", response_model=schemas.User)
async def update_user_password(current_password: str, new_password: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not crud.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    return crud.update_user_password(db, current_user.id, new_password)

@app.get("/users", response_model=List[schemas.UserPublic])
async def search_users(prefix: str = "", current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if len(prefix) < 3:
        return []
    users = crud.search_users_by_prefix(db, prefix)
    # Get accepted friends and pending requests sent
    friend_ids = set(crud.get_accepted_friends(db, current_user.id))
    pending_requests = crud.get_pending_requests_sent(db, current_user.id)
    pending_receiver_ids = set(r.receiver_id for r in pending_requests)
    # Exclure soi-même, amis acceptés, et demandes en attente
    filtered = [u for u in users if u.id != current_user.id and u.id not in friend_ids and u.id not in pending_receiver_ids]
    return filtered


@app.get("/friends", response_model=List[schemas.UserPublic])
async def list_friends(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    friend_ids = crud.get_accepted_friends(db, current_user.id)
    if not friend_ids:
        return []
    friends = crud.get_users_by_ids(db, friend_ids)
    return friends

@app.get("/friends/activity", response_model=List[schemas.FriendActivity])
async def get_friends_activity(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Récupérer le feed personnel de l'utilisateur
    my_feed = user_feed_db.get(current_user.username, [])
    
    # Transformer pour le schema de réponse
    # On renvoie la liste inversée pour avoir le plus récent en premier
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


@app.post("/friend-requests/{friend_id}")
async def send_friend_request(friend_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = crud.get_user(db, friend_id)
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    try:
        req = crud.send_friend_request(db, current_user.id, friend_id)
        return {"id": req.id, "status": "pending", "receiver": {"id": target.id, "username": target.username}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/friend-requests/pending", response_model=List[schemas.FriendRequestSchema])
async def get_pending_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_pending_requests_sent(db, current_user.id)
    return [
        {
            "id": r.id,
            "sender": {"id": r.sender.id, "username": r.sender.username, "profile_image": r.sender.profile_image},
            "receiver": {"id": r.receiver.id, "username": r.receiver.username, "profile_image": r.receiver.profile_image},
            "status": r.status
        } for r in requests
    ]


@app.get("/friend-requests/incoming", response_model=List[schemas.FriendRequestSchema])
async def get_incoming_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_incoming_requests(db, current_user.id)
    return [
        {
            "id": r.id,
            "sender": {"id": r.sender.id, "username": r.sender.username, "profile_image": r.sender.profile_image},
            "receiver": {"id": r.receiver.id, "username": r.receiver.username, "profile_image": r.receiver.profile_image},
            "status": r.status
        } for r in requests
    ]


@app.put("/friend-requests/{request_id}/accept")
async def accept_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        req = crud.accept_friend_request(db, request_id)
        return {"accepted": True, "request_id": req.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/friend-requests/{request_id}/reject")
async def reject_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        crud.reject_friend_request(db, request_id)
        return {"rejected": True, "request_id": request_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/friend-requests/{request_id}/cancel")
async def cancel_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        crud.cancel_friend_request(db, request_id)
        return {"cancelled": True, "request_id": request_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/friends/{friend_id}")
async def delete_friend(friend_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Find the accepted request between them
    req = db.query(models.FriendRequest).filter(
        ((models.FriendRequest.sender_id == current_user.id) & (models.FriendRequest.receiver_id == friend_id)) |
        ((models.FriendRequest.sender_id == friend_id) & (models.FriendRequest.receiver_id == current_user.id)),
        models.FriendRequest.status == "accepted"
    ).first()
    if req:
        # Supprimer aussi le lien dans friend_links via crud.remove_friend
        crud.remove_friend(db, current_user.id, friend_id)
        
        db.delete(req)
        db.commit()

        # Nettoyage des feeds d'activités
        # 1. Retirer les activités de l'ami supprimé dans MON feed
        friend_user = crud.get_user(db, friend_id)
        if friend_user:
            friend_username = friend_user.username
            if current_user.username in user_feed_db:
                user_feed_db[current_user.username] = [
                    act for act in user_feed_db[current_user.username] 
                    if act["sender_username"] != friend_username
                ]
            
            # 2. Retirer MES activités dans le feed de l'ami supprimé
            if friend_username in user_feed_db:
                user_feed_db[friend_username] = [
                    act for act in user_feed_db[friend_username] 
                    if act["sender_username"] != current_user.username
                ]

    return {"deleted": True}

@app.get("/")
async def root():
    return {
        "message": "API Questionnaire Multi-Catégories",
        "available_categories": list(QUESTIONS_DB.keys())
    }

@app.get("/questions/{category}", response_model=List[schemas.Question])
async def get_questions_by_category(category: str, db: Session = Depends(get_db)):
    """
    Récupère les questions d'une catégorie spécifique (ex: /questions/transport)
    """
    # Use DB
    qs = crud.get_questions_by_category(db, category)
    if not qs:
         # Fallback to dictionary if not in DB yet (or empty)
         if category in QUESTIONS_DB:
             return QUESTIONS_DB[category]
         raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return qs # Pydantic will serialize SQL Alchemy objects

@app.get("/missions/{category}", response_model=List[schemas.Mission])
async def get_missions_by_category(category: str, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Récupère les missions d'une catégorie spécifique (ex: /missions/transport).
    Si user_id est fourni, retourne les statuts personnalisés.
    Sinon, retourne les missions avec statut 'new' par défaut.
    """
    # Check category existence
    if category not in QUESTIONS_DB and category not in MISSIONS_DB:
        # Note: MISSIONS_DB used as reference for category existence,
        # but better to check DB if possible.
        pass

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

        # Fallback if DB empty but static has it (should not happen due to init)
        if not result and category in MISSIONS_DB:
             for m in MISSIONS_DB[category]:
                  # Convert dict to schema
                  m_obj = schemas.Mission(**m)
                  m_obj.status = "new"
                  result.append(m_obj)

        if not result:
             raise HTTPException(status_code=404, detail="Catégorie de missions non trouvée")

        return result




@app.put("/missions/{mission_id}")
async def update_mission(mission_id: int, payload: schemas.MissionUpdate, db: Session = Depends(get_db)):
    """
    Met à jour le statut d'une mission identifiée par son `id`.
    Si user_id est fourni, met à jour le statut pour cet utilisateur uniquement.
    """
    # 1. Vérifier si la mission existe (via DB)
    mission_db = db.query(models.Mission).filter(models.Mission.id == mission_id).first()

    # Fallback sur MISSIONS_DB si pas trouvé en base (cas hybride)
    if not mission_db:
         # Try finding in static DB
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
        # Utiliser CRUD pour persister le statut
        # Note: update_user_mission_status handles created_at/completed_at logic
        crud.update_user_mission_status(db, payload.user_id, mission_id, payload.status)

        # Enregistrement dans le feed des amis si terminé
        if payload.status == 'termine':
            # 1. Recuperer l'ID de l'utilisateur qui a terminé la mission
            user = crud.get_user(db, payload.user_id)
            if user:
                # 2. Recuperer ses amis
                friend_ids = crud.get_accepted_friends(db, user.id)
                friends = crud.get_users_by_ids(db, friend_ids)
                
                # 3. Ajouter l'activité dans le feed de chaque ami
                new_activity = {
                    "sender_id": payload.user_id,
                    "sender_username": user.username,
                    "mission_id": mission_id,
                    "mission_title": mission_title,
                    "status": payload.status,
                    "timestamp": datetime.now()
                }
                
                for friend in friends:
                    if friend.username not in user_feed_db:
                        user_feed_db[friend.username] = []
                    user_feed_db[friend.username].append(new_activity)
            
        return {"id": mission_id, "status": payload.status}
    else:
        raise HTTPException(status_code=400, detail="User ID is required for mission update")


@app.post("/answers/{category}/{user_id}")
async def save_answer(category: str, user_id: int, answer: schemas.UserAnswerBase, db: Session = Depends(get_db)):
    """
    Sauvegarde une réponse pour une catégorie et un utilisateur donnés.
    Calcule la progression de CETTE catégorie.
    """
    # 1. Vérifier si la catégorie existe
    if category not in QUESTIONS_DB:
        raise HTTPException(status_code=404, detail="Catégorie inconnue")

    # 2. Sauvegarder en DB
    crud.save_user_answer(db, user_id, schemas.UserAnswerBase(
        question_id=answer.question_id,
        answer_value=answer.answer_value
    ))

    # 3. Calcul de progression pour CETTE catégorie
    answers_list = crud.get_user_answers_by_category(db, user_id, category)

    total_questions = len(QUESTIONS_DB[category])
    answered_count = len(answers_list)

    progress = 0
    if total_questions > 0:
        progress = round((answered_count / total_questions) * 100)

    current_answers_dict = {a.question_id: a.answer_value for a in answers_list}

    return {
        "status": "saved",
        "category": category,
        "progress": progress,
        "current_answers": current_answers_dict
    }

@app.get("/answers/{category}/{user_id}")
async def get_user_category_progress(category: str, user_id: int, db: Session = Depends(get_db)):
    """
    Récupère les réponses d'un utilisateur pour une catégorie spécifique.
    """
    answers_list = crud.get_user_answers_by_category(db, user_id, category)

    current_answers_dict = {a.question_id: a.answer_value for a in answers_list}
    answered_count = len(answers_list)
    total_questions = len(QUESTIONS_DB.get(category, []))

    progress = 0
    if total_questions > 0:
        progress = round((answered_count / total_questions) * 100)

    return {
        "progress": progress,
        "answers": current_answers_dict
    }

@app.delete("/answers/{category}/{user_id}")
async def reset_category_progress(category: str, user_id: int, db: Session = Depends(get_db)):
    """
    Supprime les réponses d'un utilisateur pour une catégorie spécifique.
    """
    crud.reset_user_answers_by_category(db, user_id, category)

    return {
        "status": "reset",
        "category": category,
        "progress": 0
    }

@app.get("/users/{user_id}/profile", response_model=schemas.FriendProfile)
def read_user_profile(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    mission_count = crud.get_completed_missions_count(db, user_id=user_id)

    # Placeholder values for now as requested
    trophy_count = 0
    level = 5  # Mock level
    xp = 60    # Mock XP percentage

    return schemas.FriendProfile(
        id=user.id,
        username=user.username,
        mission_count=mission_count,
        trophy_count=trophy_count,
        level=level,
        xp=xp
    )

# --- NOUVELLE ROUTE : CALCUL DE L'IDENTITÉ CARBONE ---

@app.get("/carbon-score/{user_id}")
async def get_carbon_score(user_id: int, db: Session = Depends(get_db)):
    """
    Calcule le score carbone total de l'utilisateur.
    """

    global_score = 0
    category_scores = {}

    # Récupérer TOUTES les réponses de l'utilisateur
    # Pour faire simple, on itère par catégorie

    for category, questions in QUESTIONS_DB.items():
        cat_score = 0

        # Récupérer réponses en DB
        answers_list = crud.get_user_answers_by_category(db, user_id, category)
        user_cat_answers = {a.question_id: a.answer_value for a in answers_list}

        for question in questions:
            user_val = user_cat_answers.get(question['id'])
            score_added = False

            # On cherche l'option correspondante
            for option in question['options']:
                if user_val == option['value']:
                    cat_score += option['score']
                    score_added = True
                    break

            # Cas 2 : L'utilisateur n'a pas répondu, valeur par défaut
            if not score_added:
                for option in question['options']:
                    if option.get('is_default'):
                        cat_score += option['score']
                        break

        category_scores[category] = cat_score
        global_score += cat_score

    # Calcul de la moyenne française
    average_score = 0
    for cat, questions in QUESTIONS_DB.items():
        for q in questions:
            for opt in q['options']:
                if opt.get('is_default'):
                    average_score += opt['score']

    return {
        "user_id": user_id,
        "global_score": global_score,
        "average_national_score": average_score,
        "details_by_category": category_scores,
        "unit": "points_impact"
    }

@app.get("/global-stats")
async def get_global_stats(db: Session = Depends(get_db)):
    """
    Calcule la moyenne des scores de tous les utilisateurs enregistrés.
    """
    # 1. Calcul du score national de référence (somme des defaults)
    sum_of_defaults = 0
    national_category_scores = {}

    for cat, questions in QUESTIONS_DB.items():
        cat_score = 0
        for q in questions:
            for opt in q['options']:
                if opt.get('is_default'):
                    cat_score += opt['score']
        national_category_scores[cat] = cat_score
        sum_of_defaults += cat_score

    average_national_score = sum_of_defaults

    # 2. Récupération de tous les utilisateurs
    all_users = crud.get_all_users(db)
    total_users = len(all_users)

    if total_users == 0:
        return {
            "global_score": sum_of_defaults,
            "average_national_score": average_national_score,
            "details_by_category": national_category_scores,
            "user_count": 0
        }

    # 3. Calcul de la moyenne réelle
    global_sum = 0
    category_sums = {cat: 0 for cat in QUESTIONS_DB}

    for user in all_users:
        # Pour chaque utilisateur, calculer son score
        for category, questions in QUESTIONS_DB.items():
            cat_score = 0

            # Optimisation: charger toutes les réponses utilisateur d'un coup serait mieux,
            # mais on va garder simple via crud par catégorie
            answers_list = crud.get_user_answers_by_category(db, user.id, category)
            user_cat_answers = {a.question_id: a.answer_value for a in answers_list}

            for question in questions:
                user_val = user_cat_answers.get(question['id'])
                score_added = False

                if user_val:
                    for option in question['options']:
                        if user_val == option['value']:
                            cat_score += option['score']
                            score_added = True
                            break

                if not score_added:
                    for option in question['options']:
                        if option.get('is_default'):
                            cat_score += option['score']
                            break

            category_sums[category] += cat_score
            global_sum += cat_score

    avg_global = round(global_sum / total_users)
    avg_categories = {cat: round(s / total_users) for cat, s in category_sums.items()}

    return {
        "global_score": avg_global,
        "average_national_score": average_national_score,
        "details_by_category": avg_categories,
        "user_count": total_users
    }

# --- LEAGUE ROUTES ---
@app.post("/leagues/", response_model=schemas.League)
async def create_league_route(league: schemas.LeagueCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return crud.create_league(db=db, league=league, creator_id=current_user.id)
    except Exception as e:
        print(f"Error creating league: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/leagues/active", response_model=List[schemas.League])
def get_active_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_active_leagues_for_user(db, current_user.id)

@app.get("/leagues/archived", response_model=List[schemas.League])
def get_archived_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_archived_leagues_for_user(db, current_user.id)

@app.get("/leagues/invites", response_model=List[schemas.LeagueInvite])
def get_invites(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invites = crud.get_pending_league_invites(db, current_user.id)
    result = []
    for inc in invites:
        league = crud.get_league(db, inc.league_id)
        inviter = crud.get_user(db, inc.inviter_id)
        result.append(schemas.LeagueInvite(
            id=inc.id,
            league_id=inc.league_id,
            league_name=league.name if league else "Unknown",
            inviter_id=inc.inviter_id,
            inviter_name=inviter.username if inviter else "Unknown",
            invitee_id=inc.invitee_id,
            status=inc.status
        ))
    return result

@app.get("/leagues/{league_id}/invites", response_model=List[schemas.LeagueInvite])
def get_league_invites_route(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    is_member = any(m.user_id == current_user.id for m in league.members)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this league")

    invites = crud.get_league_invites(db, league_id)
    result = []
    for inc in invites:
        inviter = crud.get_user(db, inc.inviter_id)
        result.append(schemas.LeagueInvite(
            id=inc.id,
            league_id=inc.league_id,
            league_name=league.name,
            inviter_id=inc.inviter_id,
            inviter_name=inviter.username if inviter else "Unknown",
            invitee_id=inc.invitee_id,
            status=inc.status
        ))
    return result

@app.get("/leagues/{league_id}", response_model=schemas.LeagueDetail)
def get_league_detail(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Check if user is member (security)
    is_member = any(m.user_id == current_user.id for m in league.members)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this league")

    members_stats = crud.get_league_members_with_stats(db, league_id)

    # Construct response
    # Step 1: Validate against base League schema to ignore members relationship issue
    league_base = schemas.League.model_validate(league)

    # Step 2: Create LeagueDetail with computed members
    members_schema = [schemas.LeagueMember(**m) for m in members_stats]

    league_data = schemas.LeagueDetail(
        **league_base.model_dump(),
        members=members_schema
    )

    # Re-calculate members count
    league_data.members_count = len(members_stats)

    return league_data

@app.post("/leagues/{league_id}/invite/{user_id}", response_model=schemas.LeagueInvite)
def invite_user(league_id: int, user_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    is_member = any(m.user_id == current_user.id for m in league.members)
    if not is_member:
        raise HTTPException(status_code=403, detail="You must be a member to invite others")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot invite yourself")

    invite = crud.invite_user_to_league(db, league_id, current_user.id, user_id)
    if not invite:
        raise HTTPException(status_code=400, detail="User already member or invited")

    inviter = crud.get_user(db, current_user.id)

    return schemas.LeagueInvite(
        id=invite.id,
        league_id=invite.league_id,
        league_name=league.name,
        inviter_id=invite.inviter_id,
        inviter_name=inviter.username,
        invitee_id=invite.invitee_id,
        status=invite.status
    )

@app.put("/leagues/invites/{invite_id}/accept", response_model=schemas.LeagueInvite)
def accept_invite_route(invite_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = crud.respond_league_invite(db, invite_id, accept=True)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    league = crud.get_league(db, invite.league_id)
    inviter = crud.get_user(db, invite.inviter_id)
    return schemas.LeagueInvite(
        id=invite.id,
        league_id=invite.league_id,
        league_name=league.name,
        inviter_id=invite.inviter_id,
        inviter_name=inviter.username,
        invitee_id=invite.invitee_id,
        status=invite.status
    )

@app.put("/leagues/invites/{invite_id}/reject", response_model=schemas.LeagueInvite)
def reject_invite_route(invite_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = crud.respond_league_invite(db, invite_id, accept=False)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    league = crud.get_league(db, invite.league_id)
    inviter = crud.get_user(db, invite.inviter_id)
    return schemas.LeagueInvite(
        id=invite.id,
        league_id=invite.league_id,
        league_name=league.name,
        inviter_id=invite.inviter_id,
        inviter_name=inviter.username,
        invitee_id=invite.invitee_id,
        status=invite.status
    )

@app.delete("/leagues/{league_id}/leave")
def leave_league(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(models.LeagueMember).filter(
        models.LeagueMember.league_id == league_id,
        models.LeagueMember.user_id == current_user.id
    ).first()
    if member:
        db.delete(member)
        db.commit()
    return {"status": "left"}

# --- PROFILE IMAGE ---
@app.put("/users/profile-image", response_model=schemas.User)
def update_profile_image(profile_image: str, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the user's profile image"""
    user = crud.get_user(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.profile_image = profile_image
    db.commit()
    db.refresh(user)
    return user