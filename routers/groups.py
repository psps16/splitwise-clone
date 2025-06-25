# routers/groups.py
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(
    prefix="/groups", # All routes in this file will start with /groups
    tags=["Groups"],
    responses={404: {"description": "Not found"}},
)

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

@router.get("/", response_model=List[schemas.GroupDB])
def get_my_groups(current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    user_groups = [
        schemas.GroupDB(**group_data) 
        for group_data in db["groups"].values() 
        if group_data["creator_email"] == current_user.email
    ]
    return user_groups