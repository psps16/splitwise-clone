# schemas.py
from datetime import datetime
from typing import Set, List # Add List
from pydantic import BaseModel, EmailStr, Field

# --- User Schemas (Unchanged) ---
class User(BaseModel):
    email: EmailStr
    full_name: str

class UserInDB(User):
    hashed_password: str

# --- Group Schemas (Unchanged) ---
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3, examples=["Goa Trip 2025"])
    members: Set[str] = Field(..., min_length=1, examples=[["Alice", "Bob", "Charlie"]])

class GroupDB(GroupCreate):
    group_id: str
    creator_email: EmailStr
    created_at: datetime

# --- Token Schemas (Unchanged) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None

# --- NEW: Expense Schemas ---
class ExpenseCreate(BaseModel):
    """Schema for creating an expense."""
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    payer: str
    participants: List[str] = Field(..., min_length=1)

class ExpenseDB(ExpenseCreate):
    """Schema for an expense stored in the database."""
    expense_id: str
    group_id: str
    created_at: datetime