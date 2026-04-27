from fastapi import FastAPI
from src.api.routers import test, health, auth

app = FastAPI(title="Liora Velib APU", version="0.0.1")

# On allume les routers sur l'application
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(test.router)


@app.get("/")
def root():
    return {"message": "API en ligne 🚀"}