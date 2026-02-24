from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict
from pathlib import Path
from datetime import timedelta, datetime
import json
import re
from jose import JWTError, jwt

import crud, models, schemas, utils
from database import SessionLocal

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- CONSTANTS AND DATA ---
NGC_DEFAULT_SCORE = 8559

MISSIONS_DB = {
    "transport": [
        {"id": 100, "title": 'Vélotaf', "description": 'Remplacez un trajet voiture par le vélo pour aller au travail ou faire une course.', "conditions": ["possession_voiture", "possession_velo"], "mission_type": "one_shot", "duplicable": True},
        {"id": 101, "title": 'Pression des pneus', "description": 'Vérifiez la pression de vos pneus. Des pneus sous-gonflés augmentent la consommation de carburant de 5% !', "conditions": ["possession_voiture"], "mission_type": "one_shot"},
        {"id": 102, "title": 'Covoiturage malin', "description": 'Proposez ou cherchez un covoiturage pour votre prochain trajet moyen/longue distance.', "conditions": ["possession_voiture"], "mission_type": "one_shot", "duplicable": True},
        {"id": 103, "title": 'Vacances sur rails', "description": 'Planifiez vos prochaines vacances en train plutôt qu\'en avion.', "conditions": ["prend_avion"], "mission_type": "one_shot"},
        {"id": 105, "title": 'Transport en commun', "description": 'Utilisez les transports en commun au moins 3 jours cette semaine.', "conditions": ["possession_voiture"], "mission_type": "long_term", "duplicable": True},
        {"id": 104, "title": 'Journée sans voiture', "description": 'Utilisez les transports en commun, la marche ou le vélo pour tous vos déplacements aujourd\'hui.', "conditions": [], "mission_type": "one_shot", "duplicable": True}
    ],
    "logement": [
        {"id": 200, "title": 'Chasse aux fuites', "description": 'Vérifiez les joints des fenêtres et portes. Une mauvaise isolation, c\'est chauffer le jardin !', "conditions": ["passoire_thermique"], "mission_type": "one_shot"},
        {"id": 201, "title": 'Thermostat intelligent', "description": 'Installez un thermostat programmable pour ne pas chauffer quand vous n\'êtes pas là.', "conditions": ["est_proprietaire"], "mission_type": "one_shot"},
        {"id": 202, "title": 'Récupérateur d\'eau', "description": 'Installez un système simple pour récupérer l\'eau de pluie pour arroser vos plantes.', "conditions": ["vit_en_maison"], "mission_type": "one_shot"},
        {"id": 203, "title": 'Pull over chauffage', "description": 'Réduisez la température de 1°C pendant 1 semaine (ex: 19°C au lieu de 20°C). C\'est -7% sur la facture !', "conditions": [], "mission_type": "long_term", "duplicable": True},
        {"id": 204, "title": 'Douche express', "description": 'Essayez de limiter votre douche à 5 minutes pendant une semaine (le temps d\'une chanson).', "conditions": [], "mission_type": "long_term", "duplicable": True},
        {"id": 205, "title": 'Multiprise à interrupteur', "description": 'Éteignez complètement vos appareils en veille (TV, Ordi) la nuit.', "conditions": [], "mission_type": "one_shot"},
        {"id": 206, "title": 'Lavage efficace', "description": 'Laver le linge à 30°C pendant 5 lessives.', "conditions": [], "mission_type": "long_term", "duplicable": True},
        {"id": 207, "title": 'Séchage à l\'air', "description": 'Sécher le linge à l\'air libre.', "conditions": [], "mission_type": "one_shot"}
    ],
    "alimentation": [
        {"id": 300, "title": 'Journée Verte', "description": 'Remplacez la viande rouge par des légumineuses pour vos repas d\'aujourd\'hui.', "conditions": ["viande_rouge_importante"], "mission_type": "one_shot", "duplicable": True},
        {"id": 301, "title": 'Acheter local', "description": 'Achetez vos fruits et légumes au marché ou chez un producteur local cette semaine.', "conditions": ["conso_pas_locaux"], "mission_type": "long_term", "duplicable": True},
        {"id": 302, "title": 'Calendrier de saison', "description": 'Vérifiez si les produits de votre panier sont de saison. Pas de tomates en hiver !', "conditions": ["conso_pas_saison"], "mission_type": "one_shot"},
        {"id": 303, "title": 'Gourde attitude', "description": 'Adoptez une gourde et bannissez les bouteilles en plastique pendant une semaine.', "conditions": ["eau_bouteille"], "mission_type": "long_term", "duplicable": True},
        {"id": 304, "title": 'Pause café zéro déchet', "description": 'Amenez votre propre tasse au travail pour éviter les gobelets jetables.', "conditions": ["boissons_chaudes", "dechets_importants"], "mission_type": "one_shot"},
        {"id": 305, "title": 'Semaine sans soda', "description": 'Remplacez les sodas par de l\'eau ou des tisanes maison.', "conditions": ["soda"], "mission_type": "long_term", "duplicable": True},
        {"id": 309, "title": 'Semaine sans déchet alimentaire', "description": 'Éviter le gaspillage alimentaire pendant une semaine.', "conditions": ["dechets_importants"], "mission_type": "long_term", "duplicable": True},
        {"id": 306, "title": 'Cuisine des restes', "description": 'Faites un repas "touski" (tout ce qu\'il reste) pour éviter le gaspillage.', "conditions": [], "mission_type": "one_shot", "duplicable": True},
        {"id": 307, "title": 'Semaine végétarienne', "description": 'Faire 3 jours végétarien cette semaine.', "conditions": [], "mission_type": "long_term", "duplicable": True},
        {"id": 308, "title": 'Aujourd\'hui en vrac', "description": 'Acheter 5 produits différents en vrac.', "conditions": [], "mission_type": "one_shot"}
    ],
    "divers": [
        {"id": 400, "title": 'Règle des 48h', "description": 'Vous avez envie d\'acheter ce vêtement neuf ? Attendez 48h pour voir si l\'envie passe.', "conditions": ["shopping_important"], "mission_type": "one_shot"},
        {"id": 401, "title": 'Cendrier de poche', "description": 'Si vous fumez à l\'extérieur, ne jetez aucun mégot par terre cette semaine.', "conditions": ["fumeur"], "mission_type": "long_term", "duplicable": True},
        {"id": 402, "title": 'Compostage', "description": 'Installez un bac à compost dans votre jardin pour vos épluchures.', "conditions": ["vit_en_maison", "dechets_importants"], "mission_type": "one_shot"},
        {"id": 403, "title": 'Seconde main', "description": 'Pour votre prochain achat (livre, vêtement, déco), regardez l\'achat d\'occasion.', "conditions": [], "mission_type": "one_shot", "duplicable": True},
        {"id": 404, "title": 'Réparer avant de jeter', "description": 'Recousez un bouton ou collez cet objet cassé au lieu de le remplacer.', "conditions": [], "mission_type": "one_shot", "duplicable": True},
        {"id": 405, "title": 'Ménage au naturel', "description": 'Fabriquez un produit ménager maison (vinaigre blanc + eau) pour remplacer un produit chimique.', "conditions": [], "mission_type": "one_shot"},
        {"id": 406, "title": 'Nettoyage numérique', "description": 'Supprimer 100 mails inutiles.', "conditions": [], "mission_type": "one_shot", "duplicable": True},
        {"id": 407, "title": 'Désabonnement', "description": 'Se désabonner de 5 listes de distribution non lues.', "conditions": [], "mission_type": "one_shot"},
        {"id": 408, "title": 'Veille nocturne', "description": 'Éteindre votre box internet pendant la nuit.', "conditions": [], "mission_type": "one_shot"},
        {"id": 409, "title": 'Stop Sac Plastique', "description": 'Ne pas utiliser de sacs plastiques jetable pendant 1 semaine.', "conditions": [], "mission_type": "long_term", "duplicable": True},
        {"id": 410, "title": 'Seconde vie', "description": 'Revendre ou donner 1 objet inutilisé.', "conditions": [], "mission_type": "one_shot", "duplicable": True}
    ],
}

TROPHIES_DATA = [
    {
        "name": "trop_connecte",
        "title": "Trop connecté",
        "description": "Bravo 🎉 vous vous êtes connecté(e) 8 fois",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "login_count",
        "requirement_value": 8,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 4, "label": "Argent", "icon": "🥈"},
            {"value": 6, "label": "Or", "icon": "🥇"}
        ]
    },
    {
        "name": "champion_missions",
        "title": "Champion des missions",
        "description": "Bravo 🎉 vous avez terminé 8 missions",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "mission_count",
        "requirement_value": 8,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 4, "label": "Argent", "icon": "🥈"},
            {"value": 6, "label": "Or", "icon": "🥇"}
        ]
    },
    {
        "name": "createur_ligues",
        "title": "Créa-Ligueur",
        "description": "Bravo 🎉 vous avez créé 8 ligues",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "league_created_count",
        "requirement_value": 8,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 4, "label": "Argent", "icon": "🥈"},
            {"value": 6, "label": "Or", "icon": "🥇"}
        ]
    },
    {
        "name": "membre_actif",
        "title": "Le Panini des Ligues",
        "description": "Bravo 🎉 vous avez rejoint 8 ligues",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "league_joined_count",
        "requirement_value": 8,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 4, "label": "Argent", "icon": "🥈"},
            {"value": 6, "label": "Or", "icon": "🥇"}
        ]
    },
    {
        "name": "finisher",
        "title": "Clap de fin des Ligues",
        "description": "Bravo 🎉 vous avez terminé 8 ligues",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "league_completed_count",
        "requirement_value": 8,
        "milestones": [
            {"value": 2, "label": "Bronze", "icon": "🥉"},
            {"value": 4, "label": "Argent", "icon": "🥈"},
            {"value": 6, "label": "Or", "icon": "🥇"}
        ]
    },
    {
        "name": "quiz_master",
        "title": "Maître des Quiz",
        "description": "Bravo 🎉 vous avez terminé tous les questionnaires",
        "icon": "🏆",
        "tier": "progressive",
        "requirement_type": "questionnaire_completed_count",
        "requirement_value": 4,
        "milestones": [
            {"value": 1, "label": "Bronze", "icon": "🥉"},
            {"value": 2, "label": "Argent", "icon": "🥈"},
            {"value": 3, "label": "Or", "icon": "🥇"}
        ]
    }
]

# --- DEPENDENCIES ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=user_id_str)
    except JWTError:
        raise credentials_exception

    try:
        user_id = int(token_data.email)
        user = crud.get_user(db, user_id)
    except (ValueError, TypeError):
        user = crud.get_user_by_username(db, username=token_data.email)

    if user is None:
        raise credentials_exception
    return user

# --- INITIALIZATION FUNCTIONS ---
def init_db_from_static_data(db: Session):
    for category_name, missions in MISSIONS_DB.items():
        cat = crud.get_category_by_name(db, category_name)
        if not cat:
            cat = crud.create_category(db, category_name)
        for m_data in missions:
            crud.create_mission(db, m_data, category_name)
    init_trophies(db)

def init_trophies(db: Session):
    for trophy_data in TROPHIES_DATA:
        crud.create_trophy(db, trophy_data)

# --- HELPER FUNCTIONS ---
def get_trophy_milestones(trophy):
    return trophy.milestones or []

def extract_base_mission_title(title: str) -> str:
    """
    Extrait le titre de base d'une mission duplicable.
    Ex: "Vélotaf 1" -> "Vélotaf"
    Ex: "Journée sans voiture 3" -> "Journée sans voiture"
    """
    # Enlève " X" à la fin où X est un nombre
    match = re.match(r'^(.+)\s+\d+$', title)
    if match:
        return match.group(1)
    return title

# --- RULES ROUTE ---
RULES_PATH = Path(__file__).parent / "ngc" / "rules.json"

@router.get("/rules")
def get_rules():
    if not RULES_PATH.exists():
        raise HTTPException(status_code=404, detail=f"rules.json introuvable: {RULES_PATH}")
    try:
        with RULES_PATH.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/server-time", tags=["Utility"])
def get_server_time():
    """Return current server time in ISO format and as timestamp"""
    now = utils.get_current_time()
    # ISO 8601 week number (1-53)
    week_number = now.isocalendar()[1]
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": int(now.timestamp() * 1000),  # milliseconds
        "week_number": week_number  # ISO 8601 week number
    }

# --- AUTHENTICATION ROUTES ---
@router.post("/register", response_model=schemas.User, tags=["Authentication"], summary="Register a new user")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisée")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Pseudo déjà utilisé")
    return crud.create_user(db=db, user=user)

@router.post("/token", response_model=schemas.Token, tags=["Authentication"], summary="Login to get access token")
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

    crud.record_user_login(db, user.id)
    crud.update_trophy_progress(db, user.id)

    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- USERS ROUTES ---
@router.get("/users/me", response_model=schemas.User, tags=["Users"], summary="Get current user profile")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/users/me/email", response_model=schemas.User, tags=["Users"])
async def update_user_email(new_email: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, email=new_email)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Adresse mail déjà utilisée")
    return crud.update_user_email(db, current_user.id, new_email)

@router.put("/users/me/username", response_model=schemas.User, tags=["Users"])
async def update_user_username(new_username: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_username(db, username=new_username)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Pseudo déjà utilisé")

    return crud.update_user_username(db, current_user.id, new_username)

@router.put("/users/me/first_name", response_model=schemas.User, tags=["Users"])
async def update_user_first_name(new_first_name: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user_first_name(db, current_user.id, new_first_name)

@router.put("/users/me/last_name", response_model=schemas.User, tags=["Users"])
async def update_user_last_name(new_last_name: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user_last_name(db, current_user.id, new_last_name)

@router.put("/users/me/password", response_model=schemas.User, tags=["Users"])
async def update_user_password(current_password: str, new_password: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not crud.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    return crud.update_user_password(db, current_user.id, new_password)

@router.delete("/users/me", tags=["Users"])
async def delete_user(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.delete_user(db, current_user.id)
    return {"message": "Utilisateur supprimé"}

@router.get("/users", response_model=List[schemas.UserPublic], tags=["Users"])
async def search_users(prefix: str = "", current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if len(prefix) < 3: return []
    users = crud.search_users_by_prefix(db, prefix)
    friend_ids = set(crud.get_accepted_friends(db, current_user.id))
    pending_requests = crud.get_pending_requests_sent(db, current_user.id)
    pending_receiver_ids = set(r.receiver_id for r in pending_requests)
    filtered = [u for u in users if u.id != current_user.id and u.id not in friend_ids and u.id not in pending_receiver_ids]
    return filtered

@router.put("/users/profile-image", response_model=schemas.User, tags=["Users"])
def update_profile_image(profile_image: str, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user(db, current_user.id)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.profile_image = profile_image
    db.commit()
    db.refresh(user)
    return user

# --- FRIENDS ROUTES ---
@router.get("/friends", response_model=List[schemas.UserPublic], tags=["Friends"])
async def list_friends(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    friend_ids = crud.get_accepted_friends(db, current_user.id)
    if not friend_ids: return []
    users = crud.get_users_by_ids(db, friend_ids)
    user_publics = [schemas.UserPublic(id=u.id, username="utilisateur_supprimé" if u.is_deleted else u.username, profile_image=u.profile_image, is_deleted=u.is_deleted) for u in users]
    # Filtrer les utilisateurs supprimés
    return [up for up in user_publics if not up.is_deleted]

@router.get("/friends/activity", response_model=List[schemas.FriendActivity], tags=["Friends"])
async def get_friends_activity(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Ensure ended leagues are processed so league-end events appear in feed.
    crud.process_league_rewards(db)
    activities = crud.get_user_activities(db, current_user.id)
    response_activities = []
    for activity in activities:
        sender = crud.get_user(db, activity.sender_id)
        sender_username = "utilisateur_supprimé" if sender and sender.is_deleted else (sender.username if sender else "Inconnu")
        profile_image = sender.profile_image if sender and not sender.is_deleted else None
        response_activities.append(schemas.FriendActivity(
            friend_id=activity.sender_id,
            friend_username=sender_username,
            profile_image=profile_image,
            activity_type=activity.activity_type,
            mission_title=activity.mission_title,
            mission_id=activity.mission_id,
            trophy_title=activity.trophy_title,
            trophy_id=activity.trophy_id,
            trophy_icon=activity.trophy_icon,
            status=activity.status,
            timestamp=activity.created_at.isoformat() if activity.created_at else None
        ))
    return response_activities

@router.post("/friend-requests/{friend_id}", tags=["Friends"])
async def send_friend_request(friend_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = crud.get_user(db, friend_id)
    if not target: raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    try:
        req = crud.send_friend_request(db, current_user.id, friend_id)
        return {"id": req.id, "status": "pending", "receiver": {"id": target.id, "username": target.username}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/friend-requests/pending", response_model=List[schemas.FriendRequestSchema], tags=["Friends"])
async def get_pending_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_pending_requests_sent(db, current_user.id)
    return [{"id": r.id, "sender": {"id": r.sender.id, "username": r.sender.username, "profile_image": r.sender.profile_image}, "receiver": {"id": r.receiver.id, "username": r.receiver.username, "profile_image": r.receiver.profile_image}, "status": r.status} for r in requests]

@router.get("/friend-requests/incoming", response_model=List[schemas.FriendRequestSchema], tags=["Friends"])
async def get_incoming_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = crud.get_incoming_requests(db, current_user.id)
    return [{"id": r.id, "sender": {"id": r.sender.id, "username": r.sender.username, "profile_image": r.sender.profile_image}, "receiver": {"id": r.receiver.id, "username": r.receiver.username, "profile_image": r.receiver.profile_image}, "status": r.status} for r in requests]

@router.put("/friend-requests/{request_id}/accept", tags=["Friends"])
async def accept_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        req = crud.accept_friend_request(db, request_id)
        return {"accepted": True, "request_id": req.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/friend-requests/{request_id}/reject", tags=["Friends"])
async def reject_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        crud.reject_friend_request(db, request_id)
        return {"rejected": True, "request_id": request_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/friend-requests/{request_id}/cancel", tags=["Friends"])
async def cancel_request(request_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        crud.cancel_friend_request(db, request_id)
        return {"cancelled": True, "request_id": request_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/friends/{friend_id}", tags=["Friends"])
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
        
        # Supprimer les activités de l'ami du feed de l'utilisateur
        friend_user = crud.get_user(db, friend_id)
        if friend_user:
            db.query(models.Activity).filter(
                models.Activity.user_id == current_user.id,
                models.Activity.sender_id == friend_id
            ).delete()
            db.query(models.Activity).filter(
                models.Activity.user_id == friend_id,
                models.Activity.sender_id == current_user.id
            ).delete()
            db.commit()
    return {"deleted": True}

# --- MISSIONS ROUTES ---
@router.get("/missions/{category}", response_model=List[schemas.Mission], tags=["Missions"], summary="Get missions by category")
async def get_missions_by_category(category: str, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    # Récupérer les missions partagées (user_id IS NULL) et les missions personnelles de l'utilisateur
    all_missions_db = db.query(models.Mission).filter(
        models.Mission.category_name == category,
        or_(models.Mission.user_id.is_(None), models.Mission.user_id == user_id) if user_id else models.Mission.user_id.is_(None)
    ).all()

    if not all_missions_db and category in MISSIONS_DB:
        all_missions_db = [models.Mission(**m) for m in MISSIONS_DB[category]]

    if not all_missions_db:
        raise HTTPException(status_code=404, detail="Catégorie de missions non trouvée")

    filtered_missions = []

    if user_id:
        user_prefs = crud.get_user_preferences(db, user_id)
        pref_data = user_prefs.data if user_prefs and user_prefs.data else {}

        for mission in all_missions_db:
            conditions = mission.conditions or []
            is_eligible = True

            for cond in conditions:
                if not pref_data.get(cond, False):
                    is_eligible = False
                    break

            if is_eligible:
                # Vérifier si cette mission a un statut pour l'utilisateur
                status_entry = crud.get_user_mission_status(db, user_id, mission.id)
                mission_status = status_entry.status if status_entry else "new"
                
                # Si la mission est duplicable, filtrer par statut
                if mission.duplicable:
                    base_id = mission.base_mission_id if mission.base_mission_id else mission.id
                    
                    if mission_status == "termine":
                        # Pour les missions terminées, trouver la dernière version terminée
                        highest_terminated = db.query(models.Mission).join(
                            models.UserMissionStatus,
                            models.UserMissionStatus.mission_id == models.Mission.id
                        ).filter(
                            or_(
                                models.Mission.id == base_id,
                                models.Mission.base_mission_id == base_id
                            ),
                            or_(
                                models.Mission.user_id.is_(None),
                                models.Mission.user_id == user_id
                            ),
                            models.UserMissionStatus.user_id == user_id,
                            models.UserMissionStatus.status == "termine"
                        ).order_by(models.Mission.duplicate_count.desc()).first()
                        
                        # Ne montrer que la dernière version terminée
                        if highest_terminated and highest_terminated.id != mission.id:
                            continue
                    else:
                        # Pour les missions non terminées, trouver la dernière version non terminée
                        all_versions = db.query(models.Mission).filter(
                            or_(
                                models.Mission.id == base_id,
                                models.Mission.base_mission_id == base_id
                            ),
                            or_(
                                models.Mission.user_id.is_(None),
                                models.Mission.user_id == user_id
                            )
                        ).all()
                        
                        # Filtrer pour ne garder que les versions non terminées
                        non_terminated_versions = []
                        for v in all_versions:
                            v_status = crud.get_user_mission_status(db, user_id, v.id)
                            v_status_str = v_status.status if v_status else "new"
                            if v_status_str != "termine":
                                non_terminated_versions.append(v)
                        
                        # Trouver la dernière version non terminée
                        if non_terminated_versions:
                            highest_non_terminated = max(non_terminated_versions, key=lambda x: x.duplicate_count)
                            if highest_non_terminated.id != mission.id:
                                continue
                
                filtered_missions.append(mission)
    else:
        filtered_missions = all_missions_db

    result = []
    for m in filtered_missions:
        m_data = schemas.Mission.model_validate(m)

        if user_id:
            status_entry = crud.get_user_mission_status(db, user_id, m.id)
            m_data.status = status_entry.status if status_entry else "new"
        else:
            m_data.status = "new"

        result.append(m_data)

    return result

@router.put("/missions/{mission_id}", tags=["Missions"], summary="Update mission status")
async def update_mission(mission_id: int, payload: schemas.MissionUpdate, db: Session = Depends(get_db)):
    mission_db = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    mission_title = "Unknown Mission"
    is_duplicable = False
    mission_category = None
    mission_data = None

    if not mission_db:
        found = False
        for cat, missions in MISSIONS_DB.items():
            for m in missions:
                if int(m.get('id')) == mission_id:
                    mission_title = m.get('title', 'Mission')
                    is_duplicable = m.get('duplicable', False)
                    mission_category = cat
                    mission_data = m
                    found = True
                    break
            if found: break
        if not found:
            raise HTTPException(status_code=404, detail="Mission non trouvée")
    else:
        mission_title = mission_db.title
        is_duplicable = mission_db.duplicable
        mission_category = mission_db.category_name

    if payload.user_id:
        crud.update_user_mission_status(db, payload.user_id, mission_id, payload.status)
        newly_obtained_trophies, lost_trophies = crud.update_trophy_progress(db, payload.user_id)
        
        # Ajouter les nouveaux trophées au feed
        if newly_obtained_trophies:
            user = crud.get_user(db, payload.user_id)
            if user:
                friend_ids = crud.get_accepted_friends(db, user.id)
                for trophy in newly_obtained_trophies:
                    for friend_id in friend_ids:
                        crud.create_activity(
                            db=db,
                            user_id=friend_id,
                            sender_id=payload.user_id,
                            activity_type="trophy",
                            trophy_id=trophy.id,
                            trophy_title=trophy.title,
                            trophy_icon=trophy.icon,
                            status="obtained"
                        )
        
        # Supprimer les trophées perdus du feed
        if lost_trophies:
            for trophy in lost_trophies:
                crud.delete_trophy_activities(db, payload.user_id, trophy.id)
        
        # Si la mission n'est plus "termine", supprimer l'activité du feed
        if payload.status != 'termine':
            crud.delete_mission_activities(db, payload.user_id, mission_id)

        # Si on remet une mission "en_cours", supprimer les versions ultérieures
        if payload.status == 'en_cours' and is_duplicable and mission_db:
            base_id = mission_db.base_mission_id if mission_db.base_mission_id else mission_id
            current_count = mission_db.duplicate_count
            
            # Trouver et supprimer toutes les versions avec duplicate_count > current
            newer_versions = db.query(models.Mission).filter(
                models.Mission.base_mission_id == base_id,
                models.Mission.duplicate_count > current_count,
                models.Mission.user_id == payload.user_id
            ).all()
            
            for newer in newer_versions:
                # Supprimer les statuts associés
                db.query(models.UserMissionStatus).filter(
                    models.UserMissionStatus.user_id == payload.user_id,
                    models.UserMissionStatus.mission_id == newer.id
                ).delete()
                # Supprimer la mission elle-même
                db.delete(newer)
            
            if newer_versions:
                db.commit()

        if payload.status == 'termine':
            user = crud.get_user(db, payload.user_id)
            if user:
                friend_ids = crud.get_accepted_friends(db, user.id)
                for friend_id in friend_ids:
                    crud.create_activity(
                        db=db,
                        user_id=friend_id,
                        sender_id=payload.user_id,
                        activity_type="mission",
                        mission_id=mission_id,
                        mission_title=mission_title,
                        status=payload.status
                    )
            
            # Logique pour les missions duplicables : garder l'historique
            if is_duplicable and mission_db:
                base_id = mission_db.base_mission_id if mission_db.base_mission_id else mission_id
                
                # Déterminer le prochain numéro (commence à 2)
                current_count = mission_db.duplicate_count
                next_count = current_count + 1
                
                # Le titre de base (sans numéro)
                base_title = extract_base_mission_title(mission_db.title) if current_count > 0 else mission_db.title
                new_title = f"{base_title} {next_count + 1}"
                
                # Vérifier si la prochaine version existe déjà
                existing_next = db.query(models.Mission).filter(
                    models.Mission.base_mission_id == base_id,
                    models.Mission.duplicate_count == next_count,
                    models.Mission.user_id == payload.user_id
                ).first()
                
                # Créer la mission suivante seulement si elle n'existe pas déjà
                if not existing_next:
                    new_mission = models.Mission(
                        title=new_title,
                        description=mission_db.description,
                        category_name=mission_db.category_name,
                        conditions=mission_db.conditions,
                        mission_type=mission_db.mission_type,
                        duplicable=True,
                        base_mission_id=base_id,
                        duplicate_count=next_count,
                        user_id=payload.user_id
                    )
                    db.add(new_mission)
                    db.commit()
                    db.refresh(new_mission)
                    
                    # Créer le statut "new" pour cette nouvelle mission
                    new_status = models.UserMissionStatus(
                        user_id=payload.user_id,
                        mission_id=new_mission.id,
                        status="new"
                    )
                    db.add(new_status)
                    db.commit()

        return {"id": mission_id, "status": payload.status}
    else:
        raise HTTPException(status_code=400, detail="User ID is required for mission update")

# --- TROPHIES ROUTES ---
@router.get("/trophies", tags=["Trophies"], summary="Get all trophies with user progress")
async def get_all_trophies_with_progress(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    all_trophies = crud.get_all_trophies(db)
    user_trophies = crud.get_user_trophies(db, current_user.id)

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

@router.get("/trophies/obtained", tags=["Trophies"], summary="Get obtained or partially obtained trophies for current user")
async def get_obtained_trophies(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    all_trophies = crud.get_all_trophies(db)
    user_trophies_map = {ut.trophy_id: ut for ut in crud.get_user_trophies(db, current_user.id)}

    trophies_list = []
    summary = {"Bronze": 0, "Argent": 0, "Or": 0, "Trophée": 0}

    for trophy in all_trophies:
        user_trophy = user_trophies_map.get(trophy.id)

        if not user_trophy or user_trophy.progress == 0:
            continue

        milestones = get_trophy_milestones(trophy)
        is_final_trophy_obtained = user_trophy.progress >= trophy.requirement_value

        last_milestone_obtained = None
        if is_final_trophy_obtained:
            last_milestone_obtained = {
                "label": "Trophée",
                "icon": trophy.icon,
                "value": trophy.requirement_value
            }
        else:
            for milestone in sorted(milestones, key=lambda m: m['value'], reverse=True):
                if user_trophy.progress >= milestone['value']:
                    last_milestone_obtained = milestone
                    break

        if last_milestone_obtained:
            if last_milestone_obtained['label'] in summary:
                summary[last_milestone_obtained['label']] += 1

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
                "tier": last_milestone_obtained['label'],
                "requirement_type": trophy.requirement_type,
                "requirement_value": trophy.requirement_value,
                "progress": user_trophy.progress,
                "is_obtained": is_final_trophy_obtained,
                "obtained_at": obtained_at_str,
                "last_milestone_date": last_milestone_date_str,
                "milestones": milestones
            })

    return {"trophies": trophies_list, "summary": summary}

@router.get("/trophies/in-progress", tags=["Trophies"], summary="Get in-progress trophies for current user")
async def get_in_progress_trophies(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    all_trophies = crud.get_all_trophies(db)
    user_trophies = crud.get_user_trophies(db, current_user.id)

    user_trophy_dict = {ut.trophy_id: ut for ut in user_trophies}

    result = []
    for trophy in all_trophies:
        user_trophy = user_trophy_dict.get(trophy.id)
        if not user_trophy or not user_trophy.is_obtained:
            progress = user_trophy.progress if user_trophy else 0
            milestones = get_trophy_milestones(trophy)

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

# --- USER PROFILE ROUTES ---
@router.get("/users/{user_id}/profile", response_model=schemas.FriendProfile, tags=["Users"], summary="Get user public profile")
def read_user_profile(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    user = crud.get_user(db, user_id=user_id)
    if not user: raise HTTPException(status_code=404, detail="User not found")

    mission_count = crud.get_completed_missions_count(db, user_id=user_id)
    real_xp = user.xp
    real_level = 1 + (real_xp // 100)

    user_trophies = crud.get_user_trophies(db, user_id=user_id)
    trophy_count = sum(1 for ut in user_trophies if ut.is_obtained)
    user_trophies_map = {ut.trophy_id: ut for ut in user_trophies}
    all_trophies = crud.get_all_trophies(db)

    medals_summary = {"trophee": 0, "or": 0, "argent": 0, "bronze": 0}
    for trophy in all_trophies:
        user_trophy = user_trophies_map.get(trophy.id)
        if not user_trophy or user_trophy.progress <= 0:
            continue

        if user_trophy.progress >= trophy.requirement_value:
            medals_summary["trophee"] += 1
            continue

        milestones = sorted(get_trophy_milestones(trophy), key=lambda m: m.get("value", 0), reverse=True)
        for milestone in milestones:
            try:
                milestone_value = int(milestone.get("value", 0))
            except Exception:
                milestone_value = 0

            if user_trophy.progress < milestone_value:
                continue

            label = str(milestone.get("label", "")).strip().lower()
            if label == "or":
                medals_summary["or"] += 1
            elif label == "argent":
                medals_summary["argent"] += 1
            elif label == "bronze":
                medals_summary["bronze"] += 1
            break

    missions_by_category = {"transport": 0, "logement": 0, "alimentation": 0, "divers": 0}
    mission_rows = db.query(
        models.Mission.category_name,
        func.count(models.UserMissionStatus.id)
    ).join(
        models.UserMissionStatus,
        models.UserMissionStatus.mission_id == models.Mission.id
    ).filter(
        models.UserMissionStatus.user_id == user_id,
        models.UserMissionStatus.status == "termine"
    ).group_by(models.Mission.category_name).all()

    for category_name, count in mission_rows:
        key = str(category_name or "").strip().lower()
        if key in missions_by_category:
            missions_by_category[key] = int(count or 0)

    return schemas.FriendProfile(
        id=user.id,
        username=user.username,
        mission_count=mission_count,
        trophy_count=trophy_count,
        level=real_level,
        xp=real_xp,
        profile_image=user.profile_image,
        medals_summary=medals_summary,
        missions_by_category=missions_by_category
    )

# --- PREFERENCES ROUTES ---
@router.get("/users/me/preferences", response_model=schemas.UserPreferenceResponse, tags=["Users"], summary="Get user mission preferences")
def read_user_preferences(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = crud.get_user_preferences(db, current_user.id)
    return schemas.UserPreferenceResponse(
        id=prefs.id or 0,
        user_id=current_user.id,
        data=prefs.data,
        has_completed_onboarding=prefs.has_completed_onboarding
    )

@router.put("/users/me/preferences", response_model=schemas.UserPreferenceResponse, tags=["Users"], summary="Update user mission preferences")
def update_user_preferences_route(payload: schemas.UserPreferenceCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = crud.update_user_preferences(db, current_user.id, payload)
    return prefs

# --- NGC STATS ROUTES ---
@router.post("/ngc/stats/me", response_model=schemas.NgcStatsPayload)
def update_user_ngc_stats(
    payload: schemas.NgcStatsPayload,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = crud.upsert_user_ngc_stats(db, current_user.id, payload)

    result = schemas.NgcStatsPayload(
        global_score=stats.global_score,
        details_by_category={
            'transport': stats.transport,
            'logement': stats.logement,
            'alimentation': stats.alimentation,
            'divers': stats.divers,
            'services societaux': stats.services_societaux
        },
        category_progress={}
    )
    return result

@router.get("/ngc/answers/me", response_model=schemas.UserNgcAnswersResponse)
def get_ngc_answers_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = crud.get_user_ngc_answers(db, current_user.id)
    if not record:
        return schemas.UserNgcAnswersResponse(data={})

    try:
        data = json.loads(record.data) if record.data else {}
    except:
        data = {}

    return schemas.UserNgcAnswersResponse(data=data, updated_at=record.updated_at)

@router.post("/ngc/answers/me", response_model=schemas.UserNgcAnswersResponse)
def update_ngc_answers_me(
    payload: schemas.UserNgcAnswersCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data_str = json.dumps(payload.data)
    record = crud.update_user_ngc_answers(db, current_user.id, data_str)

    return schemas.UserNgcAnswersResponse(
        data=payload.data,
        updated_at=record.updated_at
    )

# --- CARBON SCORE ROUTES ---
@router.get("/carbon-score/{user_id}", tags=["Statistics"], summary="Get user stored carbon score")
async def get_carbon_score(user_id: int, db: Session = Depends(get_db)):
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
        return {
            "user_id": user_id,
            "global_score": NGC_DEFAULT_SCORE,
            "average_national_score": NGC_DEFAULT_SCORE,
            "details_by_category": {},
            "unit": "points_impact"
        }

# --- GLOBAL STATS ROUTES ---
@router.get("/global-stats", tags=["Statistics"], summary="Get global statistics")
async def get_global_stats(db: Session = Depends(get_db)):
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
        ngc_aggregate = crud.get_ngc_stats_aggregate(db)
        if ngc_aggregate and ngc_aggregate["user_count"] > 0:
            stats["global_score"] = ngc_aggregate["global_score"]
            stats["details_by_category"] = ngc_aggregate["details_by_category"]
            stats["user_count"] = ngc_aggregate["user_count"]

            if stats["global_score"] == 0:
                stats["global_score"] = NGC_DEFAULT_SCORE
        else:
            count_users = db.query(models.User).filter(models.User.is_deleted == False).count()
            stats["user_count"] = count_users

        try:
            stats["total_leagues"] = db.query(models.League).count()
        except: pass

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

        try:
            stats["total_trophies"] = db.query(models.UserTrophy).filter(
                models.UserTrophy.is_obtained == True
            ).count()
        except Exception as e:
            print(f"Erreur stats trophées: {e}")

    except Exception as global_e:
        print(f"ERREUR CRITIQUE DANS GET_GLOBAL_STATS: {global_e}")

    return stats

# --- LEAGUES ROUTES ---
@router.post("/leagues/", response_model=schemas.League, tags=["Leagues"])
async def create_league_route(league: schemas.LeagueCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try: return crud.create_league(db=db, league=league, creator_id=current_user.id)
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.get("/leagues/active", response_model=List[schemas.League], tags=["Leagues"])
def get_active_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.process_league_rewards(db)
    return crud.get_active_leagues_for_user(db, current_user.id)

@router.get("/leagues/archived", response_model=List[schemas.League], tags=["Leagues"])
def get_archived_leagues(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.process_league_rewards(db)
    return crud.get_archived_leagues_for_user(db, current_user.id)

@router.get("/leagues/invites", response_model=List[schemas.LeagueInvite], tags=["Leagues"])
def get_invites(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invites = crud.get_pending_league_invites(db, current_user.id)
    return [{"id": i.id, "league_id": i.league_id, "league_name": crud.get_league(db, i.league_id).name if crud.get_league(db, i.league_id) else "Unknown", "inviter_id": i.inviter_id, "inviter_name": crud.get_user(db, i.inviter_id).username, "invitee_id": i.invitee_id, "status": i.status} for i in invites]

@router.get("/leagues/{league_id}/invites", response_model=List[schemas.LeagueInvite], tags=["Leagues"])
def get_league_invites_route(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league: raise HTTPException(status_code=404, detail="League not found")
    if not any(m.user_id == current_user.id for m in league.members): raise HTTPException(status_code=403, detail="Not a member")
    invites = crud.get_league_invites(db, league_id)
    return [{"id": i.id, "league_id": i.league_id, "league_name": league.name, "inviter_id": i.inviter_id, "inviter_name": crud.get_user(db, i.inviter_id).username, "invitee_id": i.invitee_id, "status": i.status} for i in invites]

@router.get("/leagues/{league_id}", response_model=schemas.LeagueDetail, tags=["Leagues"])
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

@router.post("/leagues/{league_id}/invite/{user_id}", response_model=schemas.LeagueInvite, tags=["Leagues"])
def invite_user(league_id: int, user_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id)
    if not league: raise HTTPException(status_code=404, detail="League not found")
    if not any(m.user_id == current_user.id for m in league.members): raise HTTPException(status_code=403, detail="Not allowed")
    if user_id == current_user.id: raise HTTPException(status_code=400, detail="Cannot invite self")
    invite = crud.invite_user_to_league(db, league_id, current_user.id, user_id)
    if not invite: raise HTTPException(status_code=400, detail="Error inviting")
    return schemas.LeagueInvite(id=invite.id, league_id=invite.league_id, league_name=league.name, inviter_id=invite.inviter_id, inviter_name=current_user.username, invitee_id=invite.invitee_id, status=invite.status)

@router.put("/leagues/invites/{invite_id}/accept", response_model=schemas.LeagueInvite, tags=["Leagues"])
def accept_invite_route(invite_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = crud.respond_league_invite(db, invite_id, accept=True)
    if not invite: raise HTTPException(status_code=404, detail="Invite not found")
    return schemas.LeagueInvite(id=invite.id, league_id=invite.league_id, league_name=crud.get_league(db, invite.league_id).name, inviter_id=invite.inviter_id, inviter_name=crud.get_user(db, invite.inviter_id).username, invitee_id=invite.invitee_id, status=invite.status)

@router.put("/leagues/invites/{invite_id}/reject", response_model=schemas.LeagueInvite, tags=["Leagues"])
def reject_invite_route(invite_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = crud.respond_league_invite(db, invite_id, accept=False)
    if not invite: raise HTTPException(status_code=404, detail="Invite not found")
    return schemas.LeagueInvite(id=invite.id, league_id=invite.league_id, league_name=crud.get_league(db, invite.league_id).name, inviter_id=invite.inviter_id, inviter_name=crud.get_user(db, invite.inviter_id).username, invitee_id=invite.invitee_id, status=invite.status)

@router.delete("/leagues/{league_id}/leave", tags=["Leagues"])
def leave_league(league_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(models.LeagueMember).filter(models.LeagueMember.league_id == league_id, models.LeagueMember.user_id == current_user.id).first()
    if member:
        db.delete(member)
        db.commit()
        # Update trophy progress after leaving a league
        crud.update_trophy_progress(db, current_user.id)
    return {"status": "left"}

# --- COMPLETION ROUTES ---
@router.post("/ngc/category/{category}/complete", tags=["Statistics"], summary="Mark category as completed and award XP")
def complete_category_route(category: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.award_category_completion_xp(db, current_user.id, category)
    return {"status": "completed", "category": category}

# --- GENERAL ROUTES ---
@router.get("/", tags=["General"], summary="Root endpoint")
async def root():
    return {
        "message": "API Questionnaire Multi-Catégories (Mode Publicodes)",
        "available_categories": list(MISSIONS_DB.keys())
    }
