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
# --- SIMULATION DES MISSIONS ---
# Les conditions correspondent aux clés de UserPreference.data (déduites du questionnaire)
MISSIONS_DB = {
    "transport": [
        # Missions Ciblées
        {
            "id": 100,
            "title": 'Vélotaf',
            "description": 'Remplacez un trajet voiture par le vélo pour aller au travail ou faire une course.',
            "conditions": ["possession_voiture", "possession_velo"],
            "mission_type": "one_shot"
        },
        {
            "id": 101,
            "title": 'Pression des pneus',
            "description": 'Vérifiez la pression de vos pneus. Des pneus sous-gonflés augmentent la consommation de carburant de 5% !',
            "conditions": ["possession_voiture"],
            "mission_type": "one_shot"
        },
        {
            "id": 102,
            "title": 'Covoiturage malin',
            "description": 'Proposez ou cherchez un covoiturage pour votre prochain trajet moyen/longue distance.',
            "conditions": ["possession_voiture"],
            "mission_type": "one_shot"
        },
        {
            "id": 103,
            "title": 'Vacances sur rails',
            "description": 'Planifiez vos prochaines vacances en train plutôt qu\'en avion.',
            "conditions": ["prend_avion"],
            "mission_type": "one_shot"
        },
        {
            "id": 105,
            "title": 'Transport en commun',
            "description": 'Utilisez les transports en commun au moins 3 jours cette semaine.',
            "conditions": ["possession_voiture"],
            "mission_type": "long_term"
        },
        # Missions Génériques
        {
            "id": 104,
            "title": 'Journée sans voiture',
            "description": 'Utilisez les transports en commun, la marche ou le vélo pour tous vos déplacements aujourd\'hui.',
            "conditions": [],
            "mission_type": "one_shot"
        }
    ],
    "logement": [
        # Missions Ciblées
        {
            "id": 200,
            "title": 'Chasse aux fuites',
            "description": 'Vérifiez les joints des fenêtres et portes. Une mauvaise isolation, c\'est chauffer le jardin !',
            "conditions": ["passoire_thermique"],
            "mission_type": "one_shot"
        },
        {
            "id": 201,
            "title": 'Thermostat intelligent',
            "description": 'Installez un thermostat programmable pour ne pas chauffer quand vous n\'êtes pas là.',
            "conditions": ["est_proprietaire"],
            "mission_type": "one_shot"
        },
        {
            "id": 202,
            "title": 'Récupérateur d\'eau',
            "description": 'Installez un système simple pour récupérer l\'eau de pluie pour arroser vos plantes.',
            "conditions": ["vit_en_maison"],
            "mission_type": "one_shot"
        },
        # Missions Génériques
        {
            "id": 203,
            "title": 'Pull over chauffage',
            "description": 'Réduisez la température de 1°C pendant 1 semaine (ex: 19°C au lieu de 20°C). C\'est -7% sur la facture !',
            "conditions": [],
            "mission_type": "long_term"
        },
        {
            "id": 204,
            "title": 'Douche express',
            "description": 'Essayez de limiter votre douche à 5 minutes pendant une semaine (le temps d\'une chanson).',
            "conditions": [],
            "mission_type": "long_term"
        },
        {
            "id": 205,
            "title": 'Multiprise à interrupteur',
            "description": 'Éteignez complètement vos appareils en veille (TV, Ordi) la nuit.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 206,
            "title": 'Lavage efficace',
            "description": 'Laver le linge à 30°C pendant 5 lessives.',
            "conditions": [],
            "mission_type": "long_term"
        },
        {
            "id": 207,
            "title": 'Séchage à l\'air',
            "description": 'Sécher le linge à l\'air libre.',
            "conditions": [],
            "mission_type": "one_shot"
        }

    ],
    "alimentation": [
        # Missions Ciblées
        {
            "id": 300,
            "title": 'Journée Verte',
            "description": 'Remplacez la viande rouge par des légumineuses pour vos repas d\'aujourd\'hui.',
            "conditions": ["viande_rouge_importante"],
            "mission_type": "one_shot"
        },
        {
            "id": 301,
            "title": 'Acheter local',
            "description": 'Achetez vos fruits et légumes au marché ou chez un producteur local cette semaine.',
            "conditions": ["conso_pas_locaux"],
            "mission_type": "long_term"
        },
        {
            "id": 302,
            "title": 'Calendrier de saison',
            "description": 'Vérifiez si les produits de votre panier sont de saison. Pas de tomates en hiver !',
            "conditions": ["conso_pas_saison"],
            "mission_type": "one_shot"
        },
        {
            "id": 303,
            "title": 'Gourde attitude',
            "description": 'Adoptez une gourde et bannissez les bouteilles en plastique pendant une semaine.',
            "conditions": ["eau_bouteille"],
            "mission_type": "long_term"
        },
        {
            "id": 304,
            "title": 'Pause café zéro déchet',
            "description": 'Amenez votre propre tasse au travail pour éviter les gobelets jetables.',
            "conditions": ["boissons_chaudes", "dechets_importants"],
            "mission_type": "one_shot"
        },
        {
            "id": 305,
            "title": 'Semaine sans soda',
            "description": 'Remplacez les sodas par de l\'eau ou des tisanes maison.',
            "conditions": ["soda"],
            "mission_type": "long_term"
        },
        {
            "id": 309,
            "title": 'Semaine sans déchet alimentaire',
            "description": 'Éviter le gaspillage alimentaire pendant une semaine.',
            "conditions": ["dechets_importants"],
            "mission_type": "long_term"
        },
        # Missions Génériques
        {
            "id": 306,
            "title": 'Cuisine des restes',
            "description": 'Faites un repas "touski" (tout ce qu\'il reste) pour éviter le gaspillage.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 307,
            "title": 'Semaine végétarienne',
            "description": 'Faire 3 jours végétarien cette semaine.',
            "conditions": [],
            "mission_type": "long_term"
        },
        {
            "id": 308,
            "title": 'Aujourd\'hui en vrac',
            "description": 'Acheter 5 produits différents en vrac.',
            "conditions": [],
            "mission_type": "one_shot"
        }
    ],
    "divers": [
        # Missions Ciblées
        {
            "id": 400,
            "title": 'Règle des 48h',
            "description": 'Vous avez envie d\'acheter ce vêtement neuf ? Attendez 48h pour voir si l\'envie passe.',
            "conditions": ["shopping_important"],
            "mission_type": "one_shot"
        },
        {
            "id": 401,
            "title": 'Cendrier de poche',
            "description": 'Si vous fumez à l\'extérieur, ne jetez aucun mégot par terre cette semaine.',
            "conditions": ["fumeur"],
            "mission_type": "long_term"
        },
        {
            "id": 402,
            "title": 'Compostage',
            "description": 'Installez un bac à compost dans votre jardin pour vos épluchures.',
            "conditions": ["vit_en_maison", "dechets_importants"],
            "mission_type": "one_shot"
        },
        # Missions Génériques
        {
            "id": 403,
            "title": 'Seconde main',
            "description": 'Pour votre prochain achat (livre, vêtement, déco), regardez l\'achat d\'occasion.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 404,
            "title": 'Réparer avant de jeter',
            "description": 'Recousez un bouton ou collez cet objet cassé au lieu de le remplacer.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 405,
            "title": 'Ménage au naturel',
            "description": 'Fabriquez un produit ménager maison (vinaigre blanc + eau) pour remplacer un produit chimique.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 406,
            "title": 'Nettoyage numérique',
            "description": 'Supprimer 100 mails inutiles.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 407,
            "title": 'Désabonnement',
            "description": 'Se désabonner de 5 listes de distribution non lues.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 408,
            "title": 'Veille nocturne',
            "description": 'Éteindre votre box internet pendant la nuit.',
            "conditions": [],
            "mission_type": "one_shot"
        },
        {
            "id": 409,
            "title": 'Stop Sac Plastique',
            "description": 'Ne pas utiliser de sacs plastiques jetable pendant 1 semaine.',
            "conditions": [],
            "mission_type": "long_term"
        },
        {
            "id": 410,
            "title": 'Seconde vie',
            "description": 'Revendre ou donner 1 objet inutilisé.',
            "conditions": [],
            "mission_type": "one_shot"
        }

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

    # Initialiser les trophées
    init_trophies(db)


# Définition des trophées avec leurs paliers intermédiaires
TROPHIES_DATA = [
    {
        "name": "trop_connecte",
        "title": "Trop connecté",
        "description": "Collectez toutes les médailles de connexion",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "login_count",
        "requirement_value": 5,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 3, "label": "Argent", "icon": "🥈"},
            {"value": 4, "label": "Or", "icon": "🥇"}
        ]
    },
    {
        "name": "champion_missions",
        "title": "Champion des missions",
        "description": "Collectez toutes les médailles de missions",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "mission_count",
        "requirement_value": 8,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 4, "label": "Argent", "icon": "🥈"},
            {"value": 6, "label": "Or", "icon": "🥇"}
        ]
    }
]

def init_trophies(db: Session):
    """Initialize trophy definitions"""
    for trophy_data in TROPHIES_DATA:
        # Les descriptions sont maintenant générées côté frontend
        crud.create_trophy(db, trophy_data)

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

    # Enregistrer la connexion
    crud.record_user_login(db, user.id)

    # Mettre à jour les progrès des trophées
    crud.update_trophy_progress(db, user.id)

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
    Filtre les missions en fonction des préférences de l'utilisateur s'il est connecté.
    """
    # 1. On récupère toutes les missions de la BDD pour cette catégorie
    all_missions_db = db.query(models.Mission).filter(models.Mission.category_name == category).all()

    # 2. S'il n'y en a pas en BDD, on utilise le fallback statique (MISSIONS_DB)
    if not all_missions_db and category in MISSIONS_DB:
        all_missions_db = [models.Mission(**m) for m in MISSIONS_DB[category]]

    if not all_missions_db:
        raise HTTPException(status_code=404, detail="Catégorie de missions non trouvée")

    # 3. Filtrage basé sur les préférences de l'utilisateur
    filtered_missions = []

    if user_id:
        # On récupère les préférences de l'utilisateur
        user_prefs = crud.get_user_preferences(db, user_id)
        pref_data = user_prefs.data if user_prefs and user_prefs.data else {}

        for mission in all_missions_db:
            # On vérifie les conditions
            conditions = mission.conditions or []

            # Si aucune condition, la mission est pour tout le monde
            is_eligible = True

            # Si des conditions existent, l'utilisateur doit remplir TOUTES les conditions
            # ex: conditions = ["voiture"], pref_data doit contenir {"voiture": True}
            for cond in conditions:
                if not pref_data.get(cond, False): # Si la clé n'existe pas ou est False
                    is_eligible = False
                    break

            if is_eligible:
                filtered_missions.append(mission)
    else:
        # Si pas connecté, on montre tout
        filtered_missions = all_missions_db

    # 4. Formatage et ajout des statuts
    result = []
    for m in filtered_missions:
        m_data = schemas.Mission.model_validate(m)

        if user_id:
            # On récupère le statut spécifique de cet utilisateur
            status_entry = crud.get_user_mission_status(db, user_id, m.id)
            m_data.status = status_entry.status if status_entry else "new"
        else:
            m_data.status = "new"

        result.append(m_data)

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

        # Mettre à jour les progrès des trophées à chaque changement de statut
        # (important si une mission passe de "termine" à "en_cours")
        crud.update_trophy_progress(db, payload.user_id)

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

    real_xp = user.xp
    real_level = 1 + (real_xp // 100)

    # Count obtained trophies
    user_trophies = crud.get_user_trophies(db, user_id=user_id)
    trophy_count = sum(1 for ut in user_trophies if ut.is_obtained)


    return schemas.FriendProfile(
        id=user.id,
        username=user.username,
        mission_count=mission_count,
        trophy_count=trophy_count,
        level=real_level,
        xp=real_xp,
        profile_image=user.profile_image
    )

# --- ROUTES TROPHÉES ---

def get_trophy_milestones(trophy):
    """Retourne les paliers intermédiaires pour un trophée depuis la BD"""
    return trophy.milestones or []

@app.get("/trophies", tags=["Trophies"], summary="Get all trophies with user progress")
async def get_all_trophies_with_progress(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trophies with progress for current user"""
    all_trophies = crud.get_all_trophies(db)
    user_trophies = crud.get_user_trophies(db, current_user.id)

    # Create a dict for quick lookup
    user_trophy_dict = {ut.trophy_id: ut for ut in user_trophies}

    result = []
    for trophy in all_trophies:
        user_trophy = user_trophy_dict.get(trophy.id)
        result.append({
            "id": trophy.id,
            "name": trophy.name,
            "title": trophy.title,
            "description": trophy.description,
            "icon": trophy.icon,
            "tier": trophy.tier,
            "requirement_type": trophy.requirement_type,
            "requirement_value": trophy.requirement_value,
            "progress": user_trophy.progress if user_trophy else 0,
            "is_obtained": user_trophy.is_obtained if user_trophy else False,
            "obtained_at": user_trophy.obtained_at if user_trophy else None,
            "milestones": get_trophy_milestones(trophy)
        })

    return result

@app.get("/trophies/obtained", tags=["Trophies"], summary="Get obtained or partially obtained trophies for current user")
async def get_obtained_trophies(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trophies with progress (obtained or partially obtained) for current user"""
    all_trophies = crud.get_all_trophies(db)
    user_trophies_map = {ut.trophy_id: ut for ut in crud.get_user_trophies(db, current_user.id)}

    trophies_list = []
    summary = {"Bronze": 0, "Argent": 0, "Or": 0, "Trophée": 0}

    for trophy in all_trophies:
        user_trophy = user_trophies_map.get(trophy.id)

        # On ne s'intéresse qu'aux trophées où il y a une progression
        if not user_trophy or user_trophy.progress == 0:
            continue

        milestones = get_trophy_milestones(trophy)

        # Vérifier si le trophée final est obtenu
        is_final_trophy_obtained = user_trophy.progress >= trophy.requirement_value

        # Trouver la dernière médaille/trophée obtenu (la plus haute)
        last_milestone_obtained = None
        if is_final_trophy_obtained:
            # Le trophée final est obtenu
            last_milestone_obtained = {
                "label": "Trophée",
                "icon": trophy.icon,
                "value": trophy.requirement_value
            }
        else:
            # Chercher la médaille la plus haute obtenue
            for milestone in sorted(milestones, key=lambda m: m['value'], reverse=True):
                if user_trophy.progress >= milestone['value']:
                    last_milestone_obtained = milestone
                    break

        # Compter uniquement la médaille/trophée la plus haute obtenue
        if last_milestone_obtained:
            if last_milestone_obtained['label'] in summary:
                summary[last_milestone_obtained['label']] += 1

            # Gérer la sérialisation des dates (peut être datetime ou string selon le modèle)
            obtained_at_str = None
            if user_trophy.obtained_at:
                obtained_at_str = user_trophy.obtained_at if isinstance(user_trophy.obtained_at, str) else user_trophy.obtained_at.isoformat()

            last_milestone_date_str = None
            if user_trophy.last_milestone_date:
                last_milestone_date_str = user_trophy.last_milestone_date if isinstance(user_trophy.last_milestone_date, str) else user_trophy.last_milestone_date.isoformat()

            trophies_list.append({
                "id": trophy.id,
                "name": trophy.name,
                "title": trophy.title,
                "description": trophy.description,
                "icon": trophy.icon,
                "tier": last_milestone_obtained['label'],  # Tier actuel calculé (Bronze/Argent/Or/Trophée)
                "requirement_type": trophy.requirement_type,
                "requirement_value": trophy.requirement_value,
                "progress": user_trophy.progress,
                "is_obtained": is_final_trophy_obtained,
                "obtained_at": obtained_at_str,
                "last_milestone_date": last_milestone_date_str,
                "milestones": milestones
            })

    return {"trophies": trophies_list, "summary": summary}

@app.get("/trophies/in-progress", tags=["Trophies"], summary="Get in-progress trophies for current user")
async def get_in_progress_trophies(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get only in-progress trophies for current user"""
    all_trophies = crud.get_all_trophies(db)
    user_trophies = crud.get_user_trophies(db, current_user.id)

    user_trophy_dict = {ut.trophy_id: ut for ut in user_trophies}

    result = []
    for trophy in all_trophies:
        user_trophy = user_trophy_dict.get(trophy.id)
        if not user_trophy or not user_trophy.is_obtained:
            progress = user_trophy.progress if user_trophy else 0
            milestones = get_trophy_milestones(trophy)

            # Les descriptions sont maintenant générées côté frontend
            result.append({
                "id": trophy.id,
                "name": trophy.name,
                "title": trophy.title,
                "description": trophy.description,
                "icon": trophy.icon,
                "tier": trophy.tier,
                "requirement_type": trophy.requirement_type,
                "requirement_value": trophy.requirement_value,
                "progress": progress,
                "milestones": milestones
            })

    return result

# --- ROUTES PREFERENCES MISSIONS ---

@app.get("/users/me/preferences", response_model=schemas.UserPreferenceResponse, tags=["Users"], summary="Get user mission preferences")
def read_user_preferences(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Récupère les préférences de missions de l'utilisateur.
    """
    prefs = crud.get_user_preferences(db, current_user.id)
    # On mock l'ID si c'est un objet par défaut généré par le CRUD
    return schemas.UserPreferenceResponse(
        id=prefs.id or 0,
        user_id=current_user.id,
        data=prefs.data,
        has_completed_onboarding=prefs.has_completed_onboarding
    )

@app.put("/users/me/preferences", response_model=schemas.UserPreferenceResponse, tags=["Users"], summary="Update user mission preferences")
def update_user_preferences_route(payload: schemas.UserPreferenceCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Met à jour les préférences de missions de l'utilisateur (validées lors de l'onboarding).
    """
    prefs = crud.update_user_preferences(db, current_user.id, payload)
    return prefs

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
        try:
            stats["total_trophies"] = db.query(models.UserTrophy).filter(
                models.UserTrophy.is_obtained == True
            ).count()
        except Exception as e:
            print(f"Erreur stats trophées: {e}")

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
    crud.process_league_rewards(db)
    return crud.get_active_leagues_for_user(db, current_user.id)

@app.get("/leagues/archived", response_model=List[schemas.League], tags=["Leagues"])
def get_archived_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.process_league_rewards(db)
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
    crud.process_league_rewards(db)
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

@app.post("/ngc/category/{category}/complete", tags=["Statistics"], summary="Mark category as completed and award XP")
def complete_category_route(category: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Appelé par le frontend quand le questionnaire d'une catégorie est fini.
    Donne 50 XP si c'est la première fois.
    """
    crud.award_category_completion_xp(db, current_user.id, category)
    return {"status": "completed", "category": category}