from pydantic import BaseModel, EmailStr
from typing import Optional

# ----------------- User Auth Schemas -----------------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str # 'student', 'teacher', or 'admin'
    org_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    org_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    org_id: str

# ----------------- Chat/RAG Schemas -----------------
class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    subject_id: str
    message: str
    use_voice: bool = False # If true, expect audio URL back or indicate voice mode
