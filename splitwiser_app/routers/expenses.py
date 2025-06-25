# routers/expenses.py

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(
    prefix="/groups/{group_id}/expenses", # This nests the URL
    tags=["Expenses"],
    responses={404: {"description": "Group not found"}},
)

@router.post("/", response_model=schemas.ExpenseDB, status_code=status.HTTP_201_CREATED)
def add_expense_to_group(
    group_id: str,
    expense_input: schemas.ExpenseCreate,
    current_user: schemas.User = Depends(security.get_current_user)
):
    """
    Adds a new expense to a specific group.

    - The logged-in user must be a member of the group.
    - The payer and all participants must be members of the group.
    """
    db = database.load_db()

    # 1. Check if the group exists
    group = db["groups"].get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group_members = set(group["members"])

    # 2. Authorization: Check if the current user is a member of the group
    if current_user.full_name not in group_members and current_user.email not in group_members:
        # A more robust check could use user IDs, but for now we use name/email
        # Assuming for now that the username added to a group is their full name or email
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group and cannot add expenses."
        )

    # 3. Validation: Check if payer and participants are valid group members
    if expense_input.payer not in group_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payer '{expense_input.payer}' is not a member of this group."
        )
    
    for participant in expense_input.participants:
        if participant not in group_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Participant '{participant}' is not a member of this group."
            )
            
    # 4. Create and save the new expense
    new_expense = schemas.ExpenseDB(
        expense_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        **expense_input.model_dump()
    )

    # Ensure the 'expenses' list exists in the group
    if "expenses" not in db["groups"][group_id]:
        db["groups"][group_id]["expenses"] = []

    db["groups"][group_id]["expenses"].append(jsonable_encoder(new_expense))
    database.save_db(db)

    return new_expense