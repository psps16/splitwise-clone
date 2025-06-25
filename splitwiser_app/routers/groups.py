# routers/groups.py
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
    responses={404: {"description": "Not found"}},
)

# --- Group Endpoints (Unchanged create_group, get_my_groups) ---

@router.post("", response_model=schemas.GroupDB, status_code=status.HTTP_201_CREATED, summary="Create a new group")
def create_group(
    group_input: schemas.GroupCreate,
    current_user: schemas.User = Depends(security.get_current_user)
):
    """Creates a new trip group, associated with the logged-in user."""
    db = database.load_db()
    group_id = str(uuid.uuid4())
    
    # Add creator to members if not already present
    if current_user.full_name not in group_input.members:
        group_input.members.add(current_user.full_name)
    
    new_group = schemas.GroupDB(
        group_id=group_id,
        creator_email=current_user.email,
        created_at=datetime.now(timezone.utc),
        **group_input.model_dump()
    )
    
    db["groups"][group_id] = jsonable_encoder(new_group)
    database.save_db(db)
    return new_group


@router.get("", response_model=List[schemas.GroupDB], summary="Get my groups")
def get_my_groups(current_user: schemas.User = Depends(security.get_current_user)):
    """Retrieves a list of all groups created by the current logged-in user."""
    db = database.load_db()
    user_groups = [
        schemas.GroupDB(**group_data) 
        for group_data in db["groups"].values() 
        if group_data["creator_email"] == current_user.email
    ]
    return user_groups


# --- NEW: Endpoint to get a single group's details ---

@router.get("/{group_id}", response_model=schemas.GroupDB, summary="Get group by ID")
def get_group_details(group_id: str, current_user: schemas.User = Depends(security.get_current_user)):
    """Retrieves the details for a single group."""
    db = database.load_db()
    group = db["groups"].get(group_id)
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if group["creator_email"] != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access this group")
        
    return group


# --- NEW: Expense Endpoints ---

@router.post("/{group_id}/expenses", response_model=schemas.ExpenseDB, status_code=status.HTTP_201_CREATED, summary="Add an expense to a group")
def add_expense_to_group(
    group_id: str,
    expense_input: schemas.ExpenseCreate,
    current_user: schemas.User = Depends(security.get_current_user)
):
    """Adds a new expense record to a specific group."""
    db = database.load_db()
    group = db["groups"].get(group_id)

    # Authorization checks
    if not group or group["creator_email"] != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to add expenses to this group")

    # Validation: Payer and participants must be members of the group
    group_members = set(group["members"])
    if expense_input.payer not in group_members:
        raise HTTPException(status_code=400, detail=f"Payer '{expense_input.payer}' is not a member of this group.")
    for participant in expense_input.participants:
        if participant not in group_members:
            raise HTTPException(status_code=400, detail=f"Participant '{participant}' is not a member of this group.")

    expense_id = str(uuid.uuid4())
    new_expense = schemas.ExpenseDB(
        expense_id=expense_id,
        group_id=group_id,
        created_at=datetime.now(timezone.utc),
        **expense_input.model_dump()
    )
    
    db["expenses"][expense_id] = jsonable_encoder(new_expense)
    database.save_db(db)
    return new_expense


@router.get("/{group_id}/expenses", response_model=List[schemas.ExpenseDB], summary="List expenses in a group")
def get_expenses_for_group(
    group_id: str,
    current_user: schemas.User = Depends(security.get_current_user)
):
    """Retrieves all expenses associated with a specific group."""
    db = database.load_db()
    group = db["groups"].get(group_id)

    if not group or group["creator_email"] != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view expenses for this group")

    group_expenses = [
        schemas.ExpenseDB(**expense_data)
        for expense_data in db["expenses"].values()
        if expense_data["group_id"] == group_id
    ]
    
    # Sort expenses by creation time, newest first
    group_expenses.sort(key=lambda x: x.created_at, reverse=True)
    
    return group_expenses