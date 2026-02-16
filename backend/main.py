from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import SessionLocal, engine
from routes import router, init_db_from_static_data

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PGL API",
    description="API pour l'application ProjetGL : Calcul d'empreinte carbone, missions, et aspects sociaux.",
    version="1.0.0"
)

# Include all routes from routes.py
app.include_router(router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        init_db_from_static_data(db)
    finally:
        db.close()