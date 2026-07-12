from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
import os

from ..database.connection import get_db
from .schemas import UserCreate, UserLogin, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.environ.get("JWT_SECRET", "super-secret-local-key-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week for school labs

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Connection = Depends(get_db)):
    """Registers a new user (Student/Teacher/Admin) into the organization."""
    # Check if org exists first (to prevent foreign key failure in clean way)
    org = db.execute("SELECT id FROM organizations WHERE id = ?", (user.org_id,)).fetchone()
    if not org:
        raise HTTPException(status_code=400, detail="Organization not found")
        
    existing_user = db.execute("SELECT email FROM users WHERE email = ?", (user.email,)).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user.password)

    db.execute(
        "INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, user.name, user.email, hashed_pw, user.role, user.org_id)
    )
    db.commit()

    return UserResponse(
        id=user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        org_id=user.org_id
    )

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Connection = Depends(get_db)):
    """Authenticates a user and returns a JWT token."""
    user = db.execute("SELECT * FROM users WHERE email = ?", (credentials.email,)).fetchone()
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user["email"], "id": user["id"], "role": user["role"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "org_id": user["org_id"]
    }

@router.get("/users/{user_id}/profile")
def get_user_profile(user_id: str, db: Connection = Depends(get_db)):
    """Fetches public profile data for a user."""
    user = db.execute("SELECT id, name, email, role, org_id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return mock profile data since we don't have a profile table yet
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "org_id": user["org_id"],
        "phone": "+91 9876543210",
        "bio": "Enthusiastic learner focusing on Science and Math.",
        "grade": "10th",
        "board": "AP State Board"
    }
