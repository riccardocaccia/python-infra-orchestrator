# api/app.py
from fastapi import FastAPI
from api.api import router

app = FastAPI(title="Cloud Orchestrator API")

# include API router
app.include_router(router)

