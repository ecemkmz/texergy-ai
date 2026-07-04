from fastapi import FastAPI
from app.database import init_db
from app.routers import health, files

app = FastAPI()
init_db()

app.include_router(health.router)
app.include_router(files.router)