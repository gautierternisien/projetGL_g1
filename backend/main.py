from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

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
questions_db = [
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
]

# Stockage temporaire des réponses (dictionnaire en mémoire)
# Format: { "user_id": { question_id: "answer_value" } }
user_answers_db = {}

# --- ROUTES API ---

@app.get("/")
async def root():
    return {"message": "API Questionnaire En Ligne"}

@app.get("/questions/transport", response_model=List[Question])
async def get_transport_questions():
    """Renvoie la liste des questions pour le transport"""
    return questions_db

@app.post("/answers/{user_id}")
async def save_answer(user_id: str, answer: UserAnswer):
    """Sauvegarde une réponse pour un utilisateur spécifique"""
    if user_id not in user_answers_db:
        user_answers_db[user_id] = {}

    user_answers_db[user_id][answer.question_id] = answer.answer_value

    # Calcul simple de progression pour le retour
    answered_count = len(user_answers_db[user_id])
    total_questions = len(questions_db)
    progress = round((answered_count / total_questions) * 100)

    return {
        "status": "saved",
        "progress": progress,
        "current_answers": user_answers_db[user_id]
    }

@app.get("/answers/{user_id}")
async def get_user_progress(user_id: str):
    """Récupère les réponses existantes pour reprendre le questionnaire"""
    return user_answers_db.get(user_id, {})
