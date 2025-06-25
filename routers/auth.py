# routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(
    tags=["Authentication"] # This tag groups the endpoints in the docs
)

@router.post("/register", response_model=schemas.User)
def register_user(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database.load_db()
    if form_data.username in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = security.get_password_hash(form_data.password)
    user_data = {"email": form_data.username, "full_name": form_data.username, "hashed_password": hashed_password}
    new_user = schemas.UserInDB(**user_data)
    
    db["users"][form_data.username] = jsonable_encoder(new_user)
    database.save_db(db)
    
    return schemas.User(**user_data)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database.load_db()
    user = security.get_user(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}