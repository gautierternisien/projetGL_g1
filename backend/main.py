from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

app = FastAPI()

# Configuration CORS pour autoriser le frontend (Vue.js) à parler au backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Port par défaut de Vite/Vue
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODÈLES DE DONNÉES (Pydantic) ---

class Option(BaseModel):
    label: str
    value: str

class Question(BaseModel):
    id: int
    text: str
    options: List[Option]

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
                { "label": 'Voiture personnelle', "value": 'car' },
                { "label": 'Transports en commun', "value": 'public' },
                { "label": 'Vélo / Marche', "value": 'soft' },
            ],
        },
        {
            "id": 2,
            "text": 'Combien de km parcourez-vous par jour ?',
            "options": [
                { "label": 'Moins de 5 km', "value": 'low' },
                { "label": 'Entre 5 et 20 km', "value": 'medium' },
                { "label": 'Plus de 20 km', "value": 'high' },
            ],
        },
        {
            "id": 3,
            "text": 'Possédez-vous un véhicule électrique ?',
            "options": [
                { "label": 'Oui', "value": 'yes' },
                { "label": 'Non', "value": 'no' },
                { "label": 'Je ne possède pas de voiture', "value": 'none' },
            ],
        },
        {
            "id": 4,
            "text": 'À quelle fréquence faites-vous du covoiturage ?',
            "options": [
                { "label": 'Régulièrement', "value": 'regular' },
                { "label": 'Rarement', "value": 'rare' },
                { "label": 'Jamais', "value": 'never' },
            ],
        },
        {
            "id": 5,
            "text": "Prenez-vous l'avion pour vos vacances ?",
            "options": [
                { "label": 'Plusieurs fois par an', "value": 'often' },
                { "label": 'Une fois par an', "value": 'once' },
                { "label": 'Rarement ou jamais', "value": 'never' },
            ],
        },
    ],
    "alimentation": [
        {
            "id": 101,
            "text": 'Combien de repas avec viande mangez-vous par semaine ?',
            "options": [
                { "label": 'Tous les jours', "value": 'high' },
                { "label": '1 à 3 fois', "value": 'medium' },
                { "label": 'Jamais (Végétarien)', "value": 'none' },
            ],
        },
        {
            "id": 102,
            "text": 'Achetez-vous des produits locaux et de saison ?',
            "options": [
                { "label": 'Toujours', "value": 'always' },
                { "label": 'Parfois', "value": 'sometimes' },
                { "label": 'Rarement', "value": 'rarely' },
            ],
        },
        {
            "id": 103,
            "text": 'Quelle est votre consommation de produits laitiers (fromage, lait) ?',
            "options": [
                { "label": 'Importante (tous les jours)', "value": 'high' },
                { "label": 'Modérée', "value": 'medium' },
                { "label": 'Faible ou nulle', "value": 'low' },
            ],
        },
        {
            "id": 104,
            "text": 'Vous arrive-t-il de jeter de la nourriture ?',
            "options": [
                { "label": 'Souvent', "value": 'often' },
                { "label": 'Parfois', "value": 'sometimes' },
                { "label": 'Jamais (Zéro gaspillage)', "value": 'never' },
            ],
        },
    ],
    "logement": [
        {
            "id": 201,
            "text": 'Quel est votre système de chauffage principal ?',
            "options": [
                { "label": 'Fioul ou Gaz', "value": 'fossil' },
                { "label": 'Électrique', "value": 'electric' },
                { "label": 'Bois / Pompe à chaleur / Géothermie', "value": 'renewable' },
            ],
        },
        {
            "id": 202,
            "text": 'À quelle température chauffez-vous votre logement l\'hiver ?',
            "options": [
                { "label": 'Plus de 21°C', "value": 'hot' },
                { "label": 'Entre 19°C et 21°C', "value": 'standard' },
                { "label": '19°C ou moins', "value": 'eco' },
            ],
        },
        {
            "id": 203,
            "text": 'Quelle est la qualité de l\'isolation de votre logement ?',
            "options": [
                { "label": 'Mauvaise (passoire thermique)', "value": 'bad' },
                { "label": 'Moyenne', "value": 'average' },
                { "label": 'Bonne / Très bonne', "value": 'good' },
            ],
        },
        {
            "id": 204,
            "text": 'Quelle surface habitez-vous par personne ?',
            "options": [
                { "label": 'Grande (+60m²/pers)', "value": 'large' },
                { "label": 'Moyenne (30-60m²/pers)', "value": 'medium' },
                { "label": 'Petite (-30m²/pers)', "value": 'small' },
            ],
        },
    ],
    "consommation": [
        {
            "id": 301,
            "text": 'À quelle fréquence achetez-vous des vêtements neufs ?',
            "options": [
                { "label": 'Chaque mois', "value": 'monthly' },
                { "label": 'Quelques fois par an', "value": 'yearly' },
                { "label": 'Rarement / Seconde main', "value": 'rarely' },
            ],
        },
        {
            "id": 302,
            "text": 'Que faites-vous quand un appareil tombe en panne ?',
            "options": [
                { "label": 'J\'en achète un neuf immédiatement', "value": 'replace' },
                { "label": 'J\'essaie de le réparer ou le fais réparer', "value": 'repair' },
                { "label": 'Je l\'achète d\'occasion', "value": 'secondhand' },
            ],
        },
        {
            "id": 303,
            "text": 'Achetez-vous souvent des objets "gadgets" ou de la décoration ?',
            "options": [
                { "label": 'Régulièrement', "value": 'regular' },
                { "label": 'Pour les occasions', "value": 'occasional' },
                { "label": 'Presque jamais', "value": 'never' },
            ],
        },
    ],
    "recyclage": [
        {
            "id": 401,
            "text": 'Triez-vous vos déchets (verre, carton, plastique) ?',
            "options": [
                { "label": 'Toujours', "value": 'always' },
                { "label": 'Parfois', "value": 'sometimes' },
                { "label": 'Jamais', "value": 'never' },
            ],
        },
        {
            "id": 402,
            "text": 'Faites-vous du compost (déchets organiques) ?',
            "options": [
                { "label": 'Oui', "value": 'yes' },
                { "label": 'Non, mais j\'aimerais bien', "value": 'maybe' },
                { "label": 'Non', "value": 'no' },
            ],
        },
        {
            "id": 403,
            "text": 'Privilégiez-vous les produits en vrac (sans emballage) ?',
            "options": [
                { "label": 'Le plus souvent possible', "value": 'bulk' },
                { "label": 'De temps en temps', "value": 'sometimes' },
                { "label": 'Jamais', "value": 'packaged' },
            ],
        },
    ],
    "numerique": [
        {
            "id": 501,
            "text": 'Combien d\'heures de streaming vidéo (Netflix, YouTube...) regardez-vous par jour ?',
            "options": [
                { "label": 'Plus de 2h', "value": 'high' },
                { "label": 'Moins de 1h', "value": 'low' },
                { "label": 'Je ne regarde pas de streaming', "value": 'none' },
            ],
        },
        {
            "id": 502,
            "text": 'À quelle fréquence changez-vous de smartphone ?',
            "options": [
                { "label": 'Tous les ans', "value": '1year' },
                { "label": 'Tous les 2-3 ans', "value": '3years' },
                { "label": 'Quand il ne marche vraiment plus (+4 ans)', "value": 'max' },
            ],
        },
        {
            "id": 503,
            "text": 'Nettoyez-vous régulièrement votre boîte mail ?',
            "options": [
                { "label": 'Régulièrement', "value": 'yes' },
                { "label": 'Jamais', "value": 'no' },
            ],
        },
        {
            "id": 504,
            "text": 'Éteignez-vous vos appareils (Box, Ordi) la nuit ?',
            "options": [
                { "label": 'Oui, tout est éteint', "value": 'off' },
                { "label": 'Non, ils restent en veille', "value": 'standby' },
            ],
        },
    ],
    "loisirs": [
        {
            "id": 601,
            "text": 'Quel type de vacances privilégiez-vous ?',
            "options": [
                { "label": 'Voyage lointain (Avion/Croisière)', "value": 'far' },
                { "label": 'Tourisme local / France', "value": 'local' },
                { "label": 'Staycation (Rester chez soi)', "value": 'home' },
            ],
        },
        {
            "id": 602,
            "text": 'Achetez-vous du matériel neuf pour vos loisirs (sport, musique...) ?',
            "options": [
                { "label": 'Souvent (Derniers modèles)', "value": 'new' },
                { "label": 'Je loue ou achète d\'occasion', "value": 'used' },
                { "label": 'Je garde mon matériel très longtemps', "value": 'keep' },
            ],
        },
        {
            "id": 603,
            "text": 'Vos activités de loisirs nécessitent-elles des déplacements motorisés ?',
            "options": [
                { "label": 'Oui, souvent (ex: Sports mécaniques)', "value": 'motor' },
                { "label": 'Parfois', "value": 'mixed' },
                { "label": 'Non (ex: Rando, Lecture, Arts)', "value": 'soft' },
            ],
        },
    ],
    "quotidien": [
        {
            "id": 701,
            "text": 'Prenez-vous plutôt des bains ou des douches ?',
            "options": [
                { "label": 'Des bains', "value": 'bath' },
                { "label": 'Des douches longues (>10min)', "value": 'long_shower' },
                { "label": 'Des douches rapides', "value": 'quick_shower' },
            ],
        },
        {
            "id": 702,
            "text": 'Quelle eau buvez-vous principalement ?',
            "options": [
                { "label": 'Eau en bouteille plastique', "value": 'plastic' },
                { "label": 'Eau du robinet', "value": 'tap' },
            ],
        },
        {
            "id": 703,
            "text": 'Pensez-vous à éteindre la lumière en sortant d\'une pièce ?',
            "options": [
                { "label": 'Toujours', "value": 'always' },
                { "label": 'Parfois j\'oublie', "value": 'sometimes' },
                { "label": 'Rarement', "value": 'rarely' },
            ],
        },
    ],
}

# --- STOCKAGE TEMPORAIRE DES RÉPONSES ---
# Nouvelle Structure :
# {
#    "user_123": {
#        "transport": { 1: "car", 2: "low" },
#        "alimentation": { 101: "high" }
#    }
# }
user_answers_db: Dict[str, Dict[str, Dict[int, str]]] = {}

# --- ROUTES API ---

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

@app.post("/answers/{category}/{user_id}")
async def save_answer(category: str, user_id: str, answer: UserAnswer):
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
async def get_user_category_progress(category: str, user_id: str):
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
async def reset_category_progress(category: str, user_id: str):
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
