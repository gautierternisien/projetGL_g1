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

@app.get("/missions/{category}", response_model=List[Mission])
async def get_missions_by_category(category: str):
    """
    Récupère les missions d'une catégorie spécifique (ex: /missions/transport)
    """
    if category not in MISSIONS_DB:
        raise HTTPException(status_code=404, detail="Catégorie de missions non trouvée")

    return MISSIONS_DB[category]


class MissionUpdate(BaseModel):
    status: str


@app.put("/missions/{mission_id}")
async def update_mission(mission_id: int, payload: MissionUpdate):
    """
    Met à jour le statut d'une mission identifiée par son `id`.
    """
    for cat, missions in MISSIONS_DB.items():
        for m in missions:
            if int(m.get('id')) == mission_id:
                m['status'] = payload.status
                return m

    raise HTTPException(status_code=404, detail="Mission non trouvée")

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

# --- NOUVELLE ROUTE : CALCUL DE L'IDENTITÉ CARBONE ---

@app.get("/carbon-score/{user_id}")
async def get_carbon_score(user_id: str):
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