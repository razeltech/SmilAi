import os
import sys

if sys.platform == "win32":
    # Resolve relative to main.py to support uvicorn workers and global python executors
    main_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(main_dir)))
    torch_lib = os.path.join(backend_dir, ".venv", "Lib", "site-packages", "torch", "lib")
    if os.path.exists(torch_lib):
        try:
            os.add_dll_directory(torch_lib)
        except Exception:
            pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.startup import boot_system
from .api import auth, chat, content, assessments, voice, system, learning
from .api.admin import users, subjects, enrollments, documents, assessments as admin_assessments, assignments
from .rag import coding_brain

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Booting up SmilAi FastAPI Brain...")
    boot_system()
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
app.include_router(content.router, prefix="/v1")
app.include_router(assessments.router, prefix="/v1")
app.include_router(coding_brain.router, prefix="/v1")
app.include_router(voice.router, prefix="/v1")
app.include_router(system.router, prefix="/v1")
app.include_router(learning.router, prefix="/v1")

# Admin Routers
app.include_router(users.router, prefix="/v1")
app.include_router(subjects.router, prefix="/v1")
app.include_router(enrollments.router, prefix="/v1")
app.include_router(documents.router, prefix="/v1")
app.include_router(admin_assessments.router, prefix="/v1")
app.include_router(assignments.router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "Smiley is online and ready to teach!"}
