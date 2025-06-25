# schemas.py
from datetime import datetime
from typing import Set
from pydantic import BaseModel, EmailStr, Field

# --- User Schemas ---
class User(BaseModel):
    email: EmailStr
    full_name: str

class UserInDB(User):
    hashed_password: str

# --- Group Schemas ---
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3, examples=["Goa Trip 2025"])
    members: Set[str] = Field(..., min_length=1, examples=[["Alice", "Bob", "Charlie"]])

class GroupDB(GroupCreate):
    group_id: str
    creator_email: EmailStr
    created_at: datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None