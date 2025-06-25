# main.py

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Set

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr

# --- 1. Security & Configuration ---

# Secret key for encoding/decoding JWTs. In a real app, load this from an environment variable.
SECRET_KEY = "a_very_secret_key_that_should_be_changed"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- 2. Pydantic Models ---

class User(BaseModel):
    email: EmailStr
    full_name: str

class UserInDB(User):
    hashed_password: str

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3, examples=["Goa Trip 2025"])
    members: Set[str] = Field(..., min_length=1, examples=[["Alice", "Bob", "Charlie"]])

class GroupDB(GroupCreate):
    group_id: str
    creator_email: EmailStr
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None


# --- 3. Database Functions ---

DB_FILE = Path("app_database.json")

def load_db() -> Dict[str, Dict]:
    """Loads the database, initializing with 'users' and 'groups' keys if empty."""
    if not DB_FILE.exists():
        return {"users": {}, "groups": {}}
    with DB_FILE.open("r") as f:
        try:
            data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "groups" not in data: data["groups"] = {}
            return data
        except json.JSONDecodeError:
            return {"users": {}, "groups": {}}

def save_db(data: Dict[str, Dict]):
    """Saves the provided dictionary to the JSON database file."""
    with DB_FILE.open("w") as f:
        json.dump(data, f, indent=4)


# --- 4. Password & Authentication Utilities ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: dict, email: str) -> UserInDB | None:
    user_data = db["users"].get(email)
    if user_data:
        return UserInDB(**user_data)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    db = load_db()
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# --- 5. FastAPI Application and Endpoints ---

app = FastAPI()

# Mount the 'static' directory to serve our HTML, CSS, JS files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/register", response_model=User)
def register_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Register a new user."""
    db = load_db()
    if form_data.username in db["users"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(form_data.password)
    user_data = {"email": form_data.username, "full_name": form_data.username, "hashed_password": hashed_password}
    new_user = UserInDB(**user_data)
    
    db["users"][form_data.username] = jsonable_encoder(new_user)
    save_db(db)
    
    return User(**user_data)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return a JWT access token."""
    db = load_db()
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/groups", response_model=GroupDB, status_code=status.HTTP_201_CREATED)
def create_group(
    group_input: GroupCreate,
    current_user: User = Depends(get_current_user)
):
    """Creates a new trip group, associated with the logged-in user."""
    db = load_db()
    group_id = str(uuid.uuid4())
    
    new_group = GroupDB(
        group_id=group_id,
        creator_email=current_user.email,
        created_at=datetime.now(timezone.utc),
        **group_input.model_dump()
    )
    
    db["groups"][group_id] = jsonable_encoder(new_group)
    save_db(db)
    return new_group


@app.get("/groups", response_model=List[GroupDB])
def get_my_groups(current_user: User = Depends(get_current_user)):
    """Retrieves a list of all groups created by the current logged-in user."""
    db = load_db()
    user_groups = [
        GroupDB(**group_data) 
        for group_data in db["groups"].values() 
        if group_data["creator_email"] == current_user.email
    ]
    return user_groups

@app.get("/")
async def read_root():
    """Serves the main HTML file."""
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)