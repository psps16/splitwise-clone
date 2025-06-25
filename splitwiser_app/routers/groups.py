# routers/groups.py

import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status # <-- Add HTTPException
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
    responses={404: {"description": "Not found"}},
)

# This endpoint is unchanged
@router.post("/", response_model=schemas.GroupDB, status_code=status.HTTP_201_CREATED)
def create_group(
    group_input: schemas.GroupCreate,
    current_user: schemas.User = Depends(security.get_current_user)
):
    db = database.load_db()
    group_id = str(uuid.uuid4())
    
    new_group = schemas.GroupDB(
        group_id=group_id,
        creator_email=current_user.email,
        created_at=datetime.now(timezone.utc),
        **group_input.model_dump()
    )
    
    db["groups"][group_id] = jsonable_encoder(new_group)
    database.save_db(db)
    return new_group

# This endpoint is also unchanged
@router.get("/", response_model=List[schemas.GroupDB])
def get_my_groups(current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    user_groups = [
        schemas.GroupDB(**group_data)
        for group_data in db["groups"].values()
        if group_data["creator_email"] == current_user.email
    ]
    return user_groups

# --- NEW ENDPOINT ---
@router.get("/{group_id}", response_model=schemas.GroupDB)
def get_group_details(
    group_id: str,
    current_user: schemas.User = Depends(security.get_current_user)
):
    """
    Retrieves the full details for a single group, including its expenses.
    The user must be the creator of the group to view it.
    """
    db = database.load_db()
    
    group = db["groups"].get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Authorization Check: For now, only the creator can view the full details.
    # We could change this to "any member" later.
    if group["creator_email"] != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this group."
        )

    return schemas.GroupDB(**group)