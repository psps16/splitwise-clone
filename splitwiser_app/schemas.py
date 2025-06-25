# schemas.py

from datetime import datetime
from typing import List, Set # <-- Add List here
from pydantic import BaseModel, EmailStr, Field

# --- User Schemas (Unchanged) ---
class User(BaseModel):
    email: EmailStr
    full_name: str

class UserInDB(User):
    hashed_password: str

# --- NEW: Expense Schemas ---
class ExpenseBase(BaseModel):
    """Base model for an expense, containing common fields."""
    description: str = Field(..., min_length=1, max_length=100, examples=["Lunch at the beach"])
    amount: float = Field(..., gt=0, description="The total amount of the expense.")
    payer: str = Field(..., description="The name of the group member who paid.")
    participants: Set[str] = Field(..., min_length=1, description="Set of members participating in this expense.")

class ExpenseCreate(ExpenseBase):
    """The model for creating a new expense. No extra fields needed for now."""
    pass

class ExpenseDB(ExpenseBase):
    """The model representing an expense in the database."""
    expense_id: str
    created_at: datetime


# --- Group Schemas (GroupDB is updated) ---
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3, examples=["Goa Trip 2025"])
    members: Set[str] = Field(..., min_length=1, examples=[["Alice", "Bob", "Charlie"]])

class GroupDB(GroupCreate):
    group_id: str
    creator_email: EmailStr
    created_at: datetime
    # MODIFICATION: Add a list to hold expenses for this group.
    # It will default to an empty list when a new group is created.
    expenses: List[ExpenseDB] = [] # <--- THIS IS THE NEW LINE


# --- Token Schemas (Unchanged) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None