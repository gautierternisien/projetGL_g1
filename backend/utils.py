from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

SECRET_KEY = "Y5MssM1JhO9y3Pwx5MvbJi3azNJg3tJoxTuvkWjaHAE" # In production, use env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- TIME MANAGEMENT FOR TESTING ---
# Pour simuler une date/heure spécifique lors des tests, définir cette variable
# Exemple: SIMULATED_NOW = datetime(2026, 2, 25, 12, 0, 0) # testez plutot une date dans le futur 
SIMULATED_NOW: Optional[datetime] = None

def get_current_time() -> datetime:
    """
    Retourne l'heure actuelle (ou l'heure simulée si définie).
    Utiliser cette fonction partout au lieu de datetime.now() ou datetime.utcnow().
    
    Pour les tests:
    - utils.SIMULATED_NOW = datetime(2026, 2, 25, 12, 0, 0)
    - utils.SIMULATED_NOW = None  # pour revenir à l'heure réelle
    """
    if SIMULATED_NOW is not None:
        return SIMULATED_NOW
    return datetime.now()

def get_current_date_str() -> str:
    """Retourne la date actuelle au format YYYY-MM-DD"""
    return get_current_time().strftime("%Y-%m-%d")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = get_current_time() + expires_delta
    else:
        expire = get_current_time() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

