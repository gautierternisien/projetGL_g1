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

# --- MODÈLES DE DONNÉES (Pydantic) ---

class Option(BaseModel):
    label: str
    value: str
    score: int
    is_default: bool = False

class Question(BaseModel):
    id: int
    text: str
    options: List[Option]


class Mission(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: Optional[str] = None

class UserAnswer(BaseModel):
    question_id: int
    answer_value: str

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
    "consommation": [
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
    "recyclage": [
        {
            "id": 401,
            "text": 'Tri des déchets ?',
            "options": [
                { "label": 'Toujours', "value": 'always', "score": -50, "is_default": True },
                { "label": 'Parfois', "value": 'sometimes', "score": 0 },
                { "label": 'Jamais', "value": 'never', "score": 50 },
            ],
        },
        {
            "id": 402,
            "text": 'Compost ?',
            "options": [
                { "label": 'Oui', "value": 'yes', "score": -50 },
                { "label": 'Non', "value": 'no', "score": 0, "is_default": True },
            ],
        },
    ],
    "numerique": [
        {
            "id": 501,
            "text": 'Streaming vidéo par jour ?',
            "options": [
                { "label": '+2h', "value": 'high', "score": 300 },
                { "label": '-1h', "value": 'low', "score": 100, "is_default": True },
                { "label": 'Aucun', "value": 'none', "score": 0 },
            ],
        },
        {
            "id": 502,
            "text": 'Changement smartphone ?',
            "options": [
                { "label": '1 an', "value": '1year', "score": 500 },
                { "label": '2-3 ans', "value": '3years', "score": 200, "is_default": True },
                { "label": '+4 ans', "value": 'max', "score": 50 },
            ],
        },
        {
            "id": 503,
            "text": 'Nettoyage mails ?',
            "options": [
                { "label": 'Oui', "value": 'yes', "score": -10 },
                { "label": 'Non', "value": 'no', "score": 10, "is_default": True },
            ],
        },
        {
            "id": 504,
            "text": 'Appareils éteints la nuit ?',
            "options": [
                { "label": 'Oui', "value": 'off', "score": -20 },
                { "label": 'Non (veille)', "value": 'standby', "score": 20, "is_default": True },
            ],
        },
    ],
    "loisirs": [
        {
            "id": 601,
            "text": 'Type de vacances ?',
            "options": [
                { "label": 'Lointain', "value": 'far', "score": 2000 },
                { "label": 'Local', "value": 'local', "score": 500, "is_default": True },
                { "label": 'Chez soi', "value": 'home', "score": 100 },
            ],
        },
        {
            "id": 602,
            "text": 'Matériel neuf ?',
            "options": [
                { "label": 'Souvent', "value": 'new', "score": 300 },
                { "label": 'Occasion/Loc', "value": 'used', "score": 100, "is_default": True },
                { "label": 'Garde longtemps', "value": 'keep', "score": 50 },
            ],
        },
        {
            "id": 603,
            "text": 'Loisirs motorisés ?',
            "options": [
                { "label": 'Oui', "value": 'motor', "score": 500 },
                { "label": 'Parfois', "value": 'mixed', "score": 200 },
                { "label": 'Non', "value": 'soft', "score": 0, "is_default": True },
            ],
        },
    ],
    "quotidien": [
        {
            "id": 701,
            "text": 'Bains ou douches ?',
            "options": [
                { "label": 'Bains', "value": 'bath', "score": 300 },
                { "label": 'Douches longues', "value": 'long_shower', "score": 150 },
                { "label": 'Douches rapides', "value": 'quick_shower', "score": 50, "is_default": True },
            ],
        },
        {
            "id": 703,
            "text": 'Lumière ?',
            "options": [
                { "label": 'Toujours éteinte', "value": 'always', "score": 0, "is_default": True },
                { "label": 'Oubli parfois', "value": 'sometimes', "score": 20 },
                { "label": 'Rarement', "value": 'rarely', "score": 50 },
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
    "numerique": [
        { "id": 6, "title": 'Nettoyer boîte mail', "description": 'Supprimez les anciens emails volumineux', "status": 'new' },
        { "id": 7, "title": 'Éteindre la nuit', "description": 'Éteindre ou débrancher les appareils non utilisés la nuit', "status": 'en_cours' },
    ],
    "loisirs": [
        { "id": 8, "title": 'Activité locale', "description": 'Privilégier une sortie proche à faible empreinte', "status": 'new' },
        { "id": 9, "title": 'Week‑end sans avion', "description": 'Planifier un week‑end sans prendre l’avion', "status": 'termine' },
    ],
    "quotidien": [
        { "id": 10, "title": 'Éteindre veille', "description": 'Éteindre les appareils en veille chaque soir', "status": 'en_cours' },
        { "id": 11, "title": 'Utiliser une gourde', "description": 'Remplacer les bouteilles plastiques par une gourde', "status": 'new' },
    ],
    "recyclage": [
        { "id": 12, "title": 'Compostage', "description": 'Mettre en place un compost ou collecter les déchets organiques', "status": 'new' },
        { "id": 13, "title": 'Réemploi', "description": 'Donner ou réparer un objet au lieu de le jeter', "status": 'termine' },
    ],
    "consommation": [
        { "id": 14, "title": 'Acheter d’occasion', "description": 'Acheter un article d’occasion cette semaine', "status": 'en_cours' },
        { "id": 15, "title": 'Attendre avant achat', "description": 'Attendre 48h avant un achat non essentiel', "status": 'new' },
    ],
}


# --- STOCKAGE TEMPORAIRE DES RÉPONSES ---
# Nouvelle Structure :
# {
#    123: {
#        "transport": { 1: "car", 2: "low" },
#        "alimentation": { 101: "high" }
#    }
# }
user_answers_db: Dict[int, Dict[str, Dict[int, str]]] = {}

# {
#    123: {
#        1: "en_cours",
#        2: "termine"
#    }
# }
user_missions_db: Dict[int, Dict[int, str]] = {}

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
    
    # Migrate answers from old username key (if exists) to numeric user_id
    if old_username in user_answers_db:
        if user_id not in user_answers_db:
            user_answers_db[user_id] = {}
        # Merge old data into numeric key
        for category, answers in user_answers_db[old_username].items():
            if category not in user_answers_db[user_id]:
                user_answers_db[user_id][category] = {}
            user_answers_db[user_id][category].update(answers)
        # Remove old key
        del user_answers_db[old_username]
    
    # Migrate missions from old username key (if exists) to numeric user_id
    if old_username in user_missions_db:
        if user_id not in user_missions_db:
            user_missions_db[user_id] = {}
        user_missions_db[user_id].update(user_missions_db[old_username])
        del user_missions_db[old_username]

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
            "sender": {"id": r.sender.id, "username": r.sender.username},
            "receiver": {"id": r.receiver.id, "username": r.receiver.username},
            "status": r.status
        } for r in requests
    ]


@app.get("/friend-requests/incoming", response_model=List[schemas.FriendRequestSchema])
async def get_incoming_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_incoming_requests(db, current_user.id)
    return [
        {
            "id": r.id,
            "sender": {"id": r.sender.id, "username": r.sender.username},
            "receiver": {"id": r.receiver.id, "username": r.receiver.username},
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

@app.get("/questions/{category}", response_model=List[Question])
async def get_questions_by_category(category: str):
    """
    Récupère les questions d'une catégorie spécifique (ex: /questions/transport)
    """
    if category not in QUESTIONS_DB:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")

    return QUESTIONS_DB[category]

@app.get("/missions/{category}", response_model=List[Mission])
async def get_missions_by_category(category: str, user_id: Optional[int] = None):
    """
    Récupère les missions d'une catégorie spécifique (ex: /missions/transport).
    Si user_id est fourni, retourne les statuts personnalisés.
    Sinon, retourne les missions avec statut 'new' par défaut.
    """
    if category not in MISSIONS_DB:
        raise HTTPException(status_code=404, detail="Catégorie de missions non trouvée")

    raw_missions = MISSIONS_DB[category]

    personalized_missions = []
    user_statuses = {}
    if user_id and user_id in user_missions_db:
        user_statuses = user_missions_db[user_id]

    for m in raw_missions:
        # On crée une copie pour ne pas modifier la DB globale
        m_copy = m.copy()

        # Si on a un statut pour cet utilisateur, on l'utilise
        # Sinon, c'est 'new'
        if user_id:
            m_copy['status'] = user_statuses.get(m['id'], 'new')
        else:
            # Si pas d'user_id (ex: appel anonyme), on met 'new' par défaut pour ne pas montrer de fausses progressions
            m_copy['status'] = 'new'

        personalized_missions.append(m_copy)

    return personalized_missions


class MissionUpdate(BaseModel):
    status: str
    user_id: Optional[int] = None


@app.put("/missions/{mission_id}")
async def update_mission(mission_id: int, payload: MissionUpdate, db: Session = Depends(get_db)):
    """
    Met à jour le statut d'une mission identifiée par son `id`.
    Si user_id est fourni, met à jour le statut pour cet utilisateur uniquement.
    """
    # Vérifier si la mission existe
    mission_exists = False
    mission_title = "Mission"
    for cat, missions in MISSIONS_DB.items():
        for m in missions:
            if int(m.get('id')) == mission_id:
                mission_exists = True
                mission_title = m.get('title', 'Mission')
                break
        if mission_exists:
            break

    if not mission_exists:
        raise HTTPException(status_code=404, detail="Mission non trouvée")

    if payload.user_id:
        # Utiliser CRUD pour persister le statut
        crud.update_user_mission_status(db, payload.user_id, mission_id, payload.status)

        if payload.user_id not in user_missions_db:
             user_missions_db[payload.user_id] = {}
        user_missions_db[payload.user_id][mission_id] = payload.status

        # Persist to DB for leagues
        crud.update_mission_status(db, payload.user_id, mission_id, payload.status)

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
        # Fallback legacy : update global DB (déconseillé si multi-user)
        for cat, missions in MISSIONS_DB.items():
            for m in missions:
                if int(m.get('id')) == mission_id:
                    m['status'] = payload.status
                    return m

    raise HTTPException(status_code=404, detail="Mission non trouvée")

@app.post("/answers/{category}/{user_id}")
async def save_answer(category: str, user_id: int, answer: UserAnswer):
    """
    Sauvegarde une réponse pour une catégorie et un utilisateur donnés.
    Calcule la progression de CETTE catégorie.
    """
    # 1. Vérifier si la catégorie existe
    if category not in QUESTIONS_DB:
        raise HTTPException(status_code=404, detail="Catégorie inconnue")

    # 2. Initialiser la structure si elle n'existe pas
    if user_id not in user_answers_db:
        user_answers_db[user_id] = {}

    if category not in user_answers_db[user_id]:
        user_answers_db[user_id][category] = {}

    # 3. Sauvegarder la réponse
    user_answers_db[user_id][category][answer.question_id] = answer.answer_value

    # 4. Calcul de progression pour CETTE catégorie
    total_questions = len(QUESTIONS_DB[category])
    answered_count = len(user_answers_db[user_id][category])

    progress = 0
    if total_questions > 0:
        progress = round((answered_count / total_questions) * 100)

    return {
        "status": "saved",
        "category": category,
        "progress": progress,
        "current_answers": user_answers_db[user_id][category]
    }

@app.get("/answers/{category}/{user_id}")
async def get_user_category_progress(category: str, user_id: int):
    """
    Récupère les réponses d'un utilisateur pour une catégorie spécifique.
    """
    if user_id not in user_answers_db or category not in user_answers_db[user_id]:
        return {
            "progress": 0,
            "answers": {}
        }

    # Recalcul de la progression à la volée
    total_questions = len(QUESTIONS_DB.get(category, []))
    answers = user_answers_db[user_id][category]
    answered_count = len(answers)

    progress = 0
    if total_questions > 0:
        progress = round((answered_count / total_questions) * 100)

    return {
        "progress": progress,
        "answers": answers
    }

@app.delete("/answers/{category}/{user_id}")
async def reset_category_progress(category: str, user_id: int):
    """
    Supprime les réponses d'un utilisateur pour une catégorie spécifique.
    """
    # On vérifie si l'utilisateur et la catégorie existent dans la "DB"
    if user_id in user_answers_db and category in user_answers_db[user_id]:
        # On supprime uniquement la clé de cette catégorie
        del user_answers_db[user_id][category]

        return {
            "status": "reset",
            "category": category,
            "progress": 0
        }

    # Si rien n'a été trouvé à supprimer, on renvoie quand même un succès
    return {
        "status": "no_data_found",
        "category": category,
        "progress": 0
    }

# --- NOUVELLE ROUTE : CALCUL DE L'IDENTITÉ CARBONE ---

@app.get("/carbon-score/{user_id}")
async def get_carbon_score(user_id: int):
    """
    Calcule le score carbone total de l'utilisateur.
    Logique :
    1. Parcourt toutes les questions de toutes les catégories.
    2. Si l'utilisateur a répondu, on prend le score de sa réponse.
    3. Si l'utilisateur n'a PAS répondu, on prend le score de l'option "is_default=True".
    """

    global_score = 0
    category_scores = {}
    user_data = user_answers_db.get(user_id, {})

    # On parcourt chaque catégorie disponible dans la DB
    for category, questions in QUESTIONS_DB.items():
        cat_score = 0
        user_cat_answers = user_data.get(category, {})

        for question in questions:
            # Réponse de l'utilisateur pour cette question (ex: 'car') ou None
            user_val = user_cat_answers.get(question['id'])

            score_added = False

            # On cherche l'option correspondante
            for option in question['options']:
                # Cas 1 : L'utilisateur a choisi cette option
                if user_val == option['value']:
                    cat_score += option['score']
                    score_added = True
                    break

            # Cas 2 : L'utilisateur n'a pas répondu, on cherche la valeur par défaut
            if not score_added:
                for option in question['options']:
                    if option.get('is_default'):
                        cat_score += option['score']
                        break

        # On enregistre le score de la catégorie
        category_scores[category] = cat_score
        global_score += cat_score

    # Calcul de la moyenne française (juste pour info, en additionnant tous les defaults)
    # Dans un vrai cas, on pourrait stocker cette valeur en constante
    average_score = 0
    for cat, questions in QUESTIONS_DB.items():
        for q in questions:
            for opt in q['options']:
                if opt.get('is_default'):
                    average_score += opt['score']

    return {
        "user_id": user_id,
        "global_score": global_score,
        "average_national_score": average_score, # Score de comparaison
        "details_by_category": category_scores,
        "unit": "points_impact" # ou kgCO2e
    }

@app.get("/global-stats")
async def get_global_stats(db: Session = Depends(get_db)):
    """
    Calcule la moyenne des scores de tous les utilisateurs enregistrés.
    Prend en compte tous les utilisateurs en base de données.
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
        user_id = user.id # user_answers_db utilise numeric user_id comme clé
        user_data = user_answers_db.get(user_id, {})

        for category, questions in QUESTIONS_DB.items():
            cat_score = 0
            user_cat_answers = user_data.get(category, {})

            for question in questions:
                user_val = user_cat_answers.get(question['id'])
                score_added = False

                # Chercher si l'utilisateur a répondu
                if user_val:
                    for option in question['options']:
                        if user_val == option['value']:
                            cat_score += option['score']
                            score_added = True
                            break

                # Sinon valeur par défaut
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
