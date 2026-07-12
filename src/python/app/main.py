from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database.connection import init_db
from .api import auth, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Booting up SmilAi FastAPI Brain...")
    init_db()  # Safely initialize SQLite unified schema
    yield
    # Shutdown logic
    print("Shutting down SmilAi...")

app = FastAPI(
    title="SmilAi Core API",
    description="The Brain of Smiley - Powered by Razel Tech",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for local UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to React App's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "Smiley is online and ready to teach!"}
