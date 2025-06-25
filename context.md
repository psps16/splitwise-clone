
---

### ```context.md```

# Project Context: SplitWiser - An AI-Enhanced Expense Splitter

## 1. Project Goal, Vision, and Strategy

### Vision
The primary goal is to build a full-stack web application inspired by Splitwise, designed to help users manage and split expenses within groups.

The key long-term differentiator is the **integration of AI agents** to provide smart automation features. This vision originated from an initial brainstorming session that explored ideas such as:
*   **NLP Expense Entry:** Allowing users to log expenses with natural language (e.g., "I paid ₹500 for dinner with Alice and Bob").
*   **Receipt Scanning:** Using OCR to automatically parse details from uploaded receipts.
*   **Settlement Optimization:** An intelligent agent to calculate the most efficient way for group members to settle their debts.
*   **Budgeting & Insights:** An agent to analyze spending habits and provide proactive financial advice.

### Development Strategy
Based on that initial discussion, a practical, phased development strategy was adopted:
1.  **Build a Solid MVP First (Phase 1 - Complete):** Create a robust, traditional expense-splitting application with all core features like user authentication, group management, and manual expense tracking. This ensures a stable and useful core product.
2.  **Layer on AI Features (Phase 2 - Next Steps):** After the MVP is complete, begin integrating the AI agent features one by one, starting with the settlement calculation logic.

## 2. Core Backend Logic: The Settlement Algorithm

The heart of the application is the logic that simplifies complex debts into a minimal number of transactions. This was designed during our initial conceptual phase and consists of two parts.

### Part A: Building the Debt Graph from Expenses
We convert a list of expenses into a structured **debt graph** (an adjacency list) that represents who owes whom.
*   **Structure:** A dictionary where `debt_graph[debtor][creditor] = amount_owed`.
*   **Process:** For each expense, the application calculates each participant's share. For every participant who didn't pay, it adds their share as a debt to the person who paid.

### Part B: The Cash Flow Minimization Algorithm
This algorithm takes the `debt_graph` and simplifies it.
1.  **Calculate Net Balances:** It first computes the final financial position for each person (net debtor or net creditor).
2.  **Greedy Settlement with Heaps:** It uses two priority queues (a "debtors" max-heap and a "creditors" max-heap) to match the person who owes the most with the person who is owed the most, creating minimal transactions until all balances are zero.

## 3. Current State & Core Features (MVP Complete)

We have successfully built the foundational MVP, which includes:
*   **Full User Authentication:** Secure registration and login (bcrypt + JWT).
*   **User-Specific Group & Expense Management:** Users can create groups, add members, and add expenses to those groups. All data is private to the creator.
*   **Data Persistence:** All data is stored in a single JSON file (`app_database.json`).
*   **Polished Web Frontend:** A responsive, interactive single-page application.
*   **Modular FastAPI Backend:** A well-structured backend serving the API and static files.

## 4. Technical Stack

*   **Backend:** Python 3, FastAPI
*   **Server:** Uvicorn
*   **Data Validation:** Pydantic
*   **Security:** `passlib[bcrypt]` for password hashing, `python-jose` for JWTs.
*   **Database:** A single JSON file (`app_database.json`).
*   **Frontend:** HTML5, CSS3, modern JavaScript (ES6+).

## 5. Project File Structure

```
.
├── splitwiser_app/
│   ├── routers/
│   │   ├── auth.py
│   │   └── groups.py
│   ├── database.py
│   ├── main.py
│   ├── schemas.py
│   └── security.py
└── static/
    ├── index.html
    ├── script.js
    └── style.css
```

---

## 6. Complete Source Code

### Backend: `splitwiser_app/main.py`
```python
# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .routers import auth, groups

app = FastAPI(
    title="SplitWiser",
    description="API for managing trip expenses.",
    version="0.2.0"
)

app.include_router(auth.router)
app.include_router(groups.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
```

### Backend: `splitwiser_app/schemas.py`
```python
# schemas.py
from datetime import datetime
from typing import Set, List
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    email: EmailStr
    full_name: str

class UserInDB(User):
    hashed_password: str

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3)
    members: Set[str] = Field(..., min_length=1)

class GroupDB(GroupCreate):
    group_id: str
    creator_email: EmailStr
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None

class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    payer: str
    participants: List[str] = Field(..., min_length=1)

class ExpenseDB(ExpenseCreate):
    expense_id: str
    group_id: str
    created_at: datetime
```

### Backend: `splitwiser_app/database.py`
```python
# database.py
import json
from pathlib import Path
from typing import Dict

DB_FILE = Path("app_database.json")

def load_db() -> Dict[str, Dict]:
    if not DB_FILE.exists():
        return {"users": {}, "groups": {}, "expenses": {}}
    with DB_FILE.open("r") as f:
        try:
            data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "groups" not in data: data["groups"] = {}
            if "expenses" not in data: data["expenses"] = {}
            return data
        except json.JSONDecodeError:
            return {"users": {}, "groups": {}, "expenses": {}}

def save_db(data: Dict[str, Dict]):
    with DB_FILE.open("w") as f:
        json.dump(data, f, indent=4)
```

### Backend: `splitwiser_app/security.py`
```python
# security.py
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Dict

from . import schemas
from .database import load_db

SECRET_KEY = "a_very_secret_key_that_should_be_changed"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(db: Dict, email: str) -> schemas.UserInDB | None:
    user_data = db["users"].get(email)
    return schemas.UserInDB(**user_data) if user_data else None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> schemas.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    db = load_db()
    user = get_user(db, email=token_data.email)
    if user is None: raise credentials_exception
    return schemas.User(**user.model_dump())
```

### Backend: `splitwiser_app/routers/auth.py`
```python
# routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=schemas.User)
def register_user(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database.load_db()
    if form_data.username in db["users"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    
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
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password", {"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
```

### Backend: `splitwiser_app/routers/groups.py`
```python
# routers/groups.py
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder

from .. import schemas, security, database

router = APIRouter(prefix="/groups", tags=["Groups & Expenses"])

@router.post("", response_model=schemas.GroupDB, status_code=status.HTTP_201_CREATED)
def create_group(group_input: schemas.GroupCreate, current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    group_id = str(uuid.uuid4())
    if current_user.full_name not in group_input.members:
        group_input.members.add(current_user.full_name)
    new_group = schemas.GroupDB(group_id=group_id, creator_email=current_user.email, created_at=datetime.now(timezone.utc), **group_input.model_dump())
    db["groups"][group_id] = jsonable_encoder(new_group)
    database.save_db(db)
    return new_group

@router.get("", response_model=List[schemas.GroupDB])
def get_my_groups(current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    return [schemas.GroupDB(**g) for g in db["groups"].values() if g["creator_email"] == current_user.email]

@router.get("/{group_id}", response_model=schemas.GroupDB)
def get_group_details(group_id: str, current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    group = db["groups"].get(group_id)
    if not group: raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")
    if group["creator_email"] != current_user.email: raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized")
    return group

@router.post("/{group_id}/expenses", response_model=schemas.ExpenseDB, status_code=status.HTTP_201_CREATED)
def add_expense_to_group(group_id: str, expense_input: schemas.ExpenseCreate, current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    group = db["groups"].get(group_id)
    if not group or group["creator_email"] != current_user.email: raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized")
    group_members = set(group["members"])
    if expense_input.payer not in group_members: raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Payer '{expense_input.payer}' is not in the group.")
    for p in expense_input.participants:
        if p not in group_members: raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Participant '{p}' is not in the group.")
    
    expense_id = str(uuid.uuid4())
    new_expense = schemas.ExpenseDB(expense_id=expense_id, group_id=group_id, created_at=datetime.now(timezone.utc), **expense_input.model_dump())
    db["expenses"][expense_id] = jsonable_encoder(new_expense)
    database.save_db(db)
    return new_expense

@router.get("/{group_id}/expenses", response_model=List[schemas.ExpenseDB])
def get_expenses_for_group(group_id: str, current_user: schemas.User = Depends(security.get_current_user)):
    db = database.load_db()
    group = db["groups"].get(group_id)
    if not group or group["creator_email"] != current_user.email: raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized")
    
    group_expenses = [schemas.ExpenseDB(**e) for e in db["expenses"].values() if e["group_id"] == group_id]
    group_expenses.sort(key=lambda x: x.created_at, reverse=True)
    return group_expenses
```

### Frontend: `static/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SplitWiser</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <!-- Auth View: Login & Register -->
        <div id="auth-view">
            <h1 class="app-title">SplitWiser</h1>
            <div class="card">
                <div class="tabs">
                    <button class="tab-link active" data-tab="login">Login</button>
                    <button class="tab-link" data-tab="register">Register</button>
                </div>
                <div id="login" class="tab-content active">
                    <form id="login-form">
                        <div class="input-group"><i class="fas fa-envelope"></i><input type="email" id="login-email" placeholder="Email" required></div>
                        <div class="input-group"><i class="fas fa-lock"></i><input type="password" id="login-password" placeholder="Password" required></div>
                        <button type="submit" class="btn btn-primary">Login</button>
                    </form>
                </div>
                <div id="register" class="tab-content">
                    <form id="register-form">
                        <div class="input-group"><i class="fas fa-envelope"></i><input type="email" id="register-email" placeholder="Email" required></div>
                        <div class="input-group"><i class="fas fa-lock"></i><input type="password" id="register-password" placeholder="Password" required></div>
                        <button type="submit" class="btn btn-primary">Register</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- App View: Main Dashboard (List of Groups) -->
        <div id="app-view" class="hidden">
            <header class="app-header">
                <h1 class="app-title">SplitWiser</h1>
                <div class="user-info">
                    <span id="user-email"></span>
                    <button id="logout-button" class="btn-logout"><i class="fas fa-sign-out-alt"></i></button>
                </div>
            </header>
            <main>
                <div class="card">
                    <h2>Create a New Group</h2>
                    <form id="create-group-form">
                        <div class="input-group"><i class="fas fa-users"></i><input type="text" id="group-name" placeholder="Group Name (e.g., Goa Trip)" required></div>
                        <div class="member-input-section">
                            <label for="member-name-input">Add Members</label>
                            <div class="add-member-wrapper">
                                <div class="input-group"><i class="fas fa-user-plus"></i><input type="text" id="member-name-input" placeholder="Enter a member's name"></div>
                                <button type="button" id="add-member-button" class="btn btn-secondary">Add</button>
                            </div>
                        </div>
                        <div id="members-list-container"></div>
                        <button type="submit" id="create-group-button" class="btn btn-primary" disabled>Create Group</button>
                    </form>
                </div>
                <h2 class="section-title">My Groups</h2>
                <div id="groups-list"></div>
            </main>
        </div>

        <!-- Group Detail View -->
        <div id="group-detail-view" class="hidden">
            <header class="app-header">
                <button id="back-to-groups-button" class="btn-back"><i class="fas fa-arrow-left"></i> Back</button>
                <h2 id="group-detail-title" class="view-title">Group Details</h2>
            </header>
            <main>
                <div class="card">
                    <h3>Add New Expense</h3>
                    <form id="add-expense-form">
                        <div class="input-group"><i class="fas fa-comment-dots"></i><input type="text" id="expense-description" placeholder="Description (e.g., Dinner)" required></div>
                        <div class="input-group"><i class="fas fa-coins"></i><input type="number" id="expense-amount" placeholder="Amount" step="0.01" min="0.01" required></div>
                        <div class="input-group"><i class="fas fa-user-check"></i><select id="expense-payer" required></select></div>
                        <div class="participants-section">
                            <label>Split between:</label>
                            <div id="expense-participants-list" class="checkbox-grid"></div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Expense</button>
                    </form>
                </div>
                <h3>Expenses</h3>
                <div id="expenses-list"></div>
            </main>
        </div>
    </div>
    
    <div id="loader" class="hidden"><div class="spinner"></div></div>
    <div id="toast-notification" class="toast"></div>

    <script src="/static/script.js"></script>
</body>
</html>
```

### Frontend: `static/style.css`
```css
:root {
    --primary-color: #4a47a3;
    --secondary-color: #706fd3;
    --background-color: #f4f7f9;
    --card-background: #ffffff;
    --text-color: #333;
    --light-text-color: #888;
    --border-color: #e0e0e0;
    --success-color: #2ecc71;
    --error-color: #e74c3c;
    --shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
body { font-family: 'Poppins', sans-serif; background-color: var(--background-color); color: var(--text-color); margin: 0; padding: 20px; }
.container { max-width: 700px; margin: 0 auto; }
.card { background: var(--card-background); padding: 30px; border-radius: 12px; box-shadow: var(--shadow); margin-bottom: 25px; }
.app-title { text-align: center; color: var(--primary-color); font-weight: 700; margin-bottom: 20px; }
.hidden { display: none !important; }
.tabs { display: flex; border-bottom: 1px solid var(--border-color); margin-bottom: 20px; }
.tab-link { flex: 1; padding: 15px; text-align: center; background: none; border: none; cursor: pointer; font-size: 16px; font-weight: 600; color: var(--light-text-color); position: relative; transition: color 0.3s; }
.tab-link.active { color: var(--primary-color); }
.tab-link.active::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 100%; height: 3px; background-color: var(--primary-color); border-radius: 3px; }
.tab-content { display: none; }
.tab-content.active { display: block; }
form { display: flex; flex-direction: column; gap: 20px; }
.input-group { position: relative; }
.input-group i { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: var(--light-text-color); }
input[type="email"], input[type="password"], input[type="text"], input[type="number"], select { width: 100%; padding: 15px 15px 15px 45px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 16px; box-sizing: border-box; transition: border-color 0.3s, box-shadow 0.3s; -webkit-appearance: none; appearance: none; }
select { background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23888888%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 15px center; background-size: 12px; }
input:focus, select:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(74, 71, 163, 0.2); }
.btn { padding: 15px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: background-color 0.3s, transform 0.2s; }
.btn-primary { background-color: var(--primary-color); color: white; }
.btn-primary:hover { background-color: var(--secondary-color); }
.btn:active { transform: scale(0.98); }
button:disabled { background-color: #bdc3c7; cursor: not-allowed; }
button:disabled:hover { background-color: #bdc3c7; }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.user-info { display: flex; align-items: center; gap: 15px; font-weight: 600; }
.btn-logout { background: none; border: none; color: var(--error-color); font-size: 20px; cursor: pointer; transition: color 0.3s; }
.btn-logout:hover { color: #c0392b; }
h2 { color: #333; padding-bottom: 10px; margin-top: 0; margin-bottom: 20px; }
h3 { margin-top: 0; }
.section-title { font-size: 22px; margin-top: 40px; margin-bottom: 20px; border: none; text-align: left; }
#groups-list { display: grid; gap: 20px; }
.group-item { background: var(--card-background); padding: 20px; border-radius: 12px; box-shadow: var(--shadow); border-left: 5px solid var(--secondary-color); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
.group-item:hover { transform: translateY(-3px); box-shadow: 0 6px 25px rgba(0,0,0,0.1); }
.group-item h3 { margin: 0 0 15px 0; font-size: 18px; }
.group-item p { margin: 0; font-size: 14px; color: var(--light-text-color); display: flex; align-items: center; gap: 8px; }
.group-item p i { color: var(--secondary-color); }
#group-detail-view .app-header { margin-bottom: 10px; }
.view-title { color: var(--primary-color); font-weight: 600; margin: 0; font-size: 24px; text-align: right; flex-grow: 1; }
.btn-back { background: none; border: none; font-size: 16px; font-weight: 600; color: var(--primary-color); cursor: pointer; display: flex; align-items: center; gap: 8px; }
.participants-section label { display: block; font-weight: 600; margin-bottom: 10px; color: var(--text-color); }
.checkbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; }
.checkbox-item { display: flex; align-items: center; gap: 8px; background: #f9f9f9; padding: 10px; border-radius: 6px; }
.checkbox-item label { font-weight: 400; }
#expenses-list { display: flex; flex-direction: column; gap: 15px; }
.expense-item { background: #fdfdfd; border: 1px solid var(--border-color); padding: 20px; border-radius: 8px; }
.expense-item .description { font-size: 18px; font-weight: 600; margin: 0 0 15px 0; }
.expense-details { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.expense-details .payer { color: var(--light-text-color); }
.expense-details .amount { font-weight: 700; font-size: 20px; color: var(--primary-color); }
.expense-participants { font-size: 12px; color: #999; margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--border-color); }
.member-input-section label { display: block; font-weight: 600; margin-bottom: 10px; color: var(--text-color); }
.add-member-wrapper { display: flex; gap: 10px; align-items: center; }
.add-member-wrapper .input-group { flex-grow: 1; }
.btn-secondary { background-color: var(--secondary-color); color: white; flex-shrink: 0; }
.btn-secondary:hover { background-color: var(--primary-color); }
#members-list-container { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; padding: 10px; border: 1px dashed var(--border-color); border-radius: 8px; min-height: 40px; }
.member-pill { display: flex; align-items: center; background-color: #e9e8f8; color: var(--primary-color); padding: 8px 12px; border-radius: 20px; font-weight: 600; font-size: 14px; animation: fadeIn 0.3s ease; }
.remove-member-btn { background: none; border: none; color: var(--primary-color); margin-left: 8px; cursor: pointer; font-size: 16px; opacity: 0.7; transition: opacity 0.2s; }
.remove-member-btn:hover { opacity: 1; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.8); } to { opacity: 1; transform: scale(1); } }
#loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.7); display: flex; justify-content: center; align-items: center; z-index: 9999; }
.spinner { width: 50px; height: 50px; border: 5px solid var(--border-color); border-top-color: var(--primary-color); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); padding: 15px 25px; border-radius: 8px; color: white; font-weight: 600; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2); opacity: 0; visibility: hidden; transition: opacity 0.3s, bottom 0.3s, visibility 0.3s; z-index: 10000; }
.toast.show { opacity: 1; visibility: visible; bottom: 30px; }
.toast.success { background-color: var(--success-color); }
.toast.error { background-color: var(--error-color); }
@media (max-width: 768px) { body { padding: 10px; } .card { padding: 20px; } }
```

### Frontend: `static/script.js`
```javascript
document.addEventListener("DOMContentLoaded", () => {
    // --- Element Selectors ---
    const authView = document.getElementById("auth-view");
    const appView = document.getElementById("app-view");
    const groupDetailView = document.getElementById("group-detail-view");
    const loader = document.getElementById("loader");
    const toast = document.getElementById("toast-notification");
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const logoutButton = document.getElementById("logout-button");
    const userEmailSpan = document.getElementById("user-email");
    const groupsListDiv = document.getElementById("groups-list");
    const tabs = document.querySelectorAll(".tab-link");
    const tabContents = document.querySelectorAll(".tab-content");

    // --- State Management ---
    let currentGroupId = null;
    let currentGroupMembers = []; // Store members of the currently viewed group

    // --- Utility Functions ---
    const showLoader = () => loader.classList.remove("hidden");
    const hideLoader = () => loader.classList.add("hidden");
    const showToast = (message, type = 'success') => {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => { toast.className = 'toast'; }, 3000);
    };
    const getToken = () => localStorage.getItem("access_token");
    const showView = (viewId) => {
        document.querySelectorAll('#auth-view, #app-view, #group-detail-view').forEach(view => view.classList.add('hidden'));
        document.getElementById(viewId).classList.remove('hidden');
    };

    const updateUIForLoginState = () => {
        const token = getToken();
        if (token) {
            showView('app-view');
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                userEmailSpan.textContent = payload.sub;
                fetchGroups();
            } catch (e) {
                localStorage.removeItem("access_token");
                updateUIForLoginState();
            }
        } else {
            showView('auth-view');
        }
    };
    
    // --- API Call Functions ---
    const fetchGroups = async () => {
        const token = getToken();
        if (!token) return;
        showLoader();
        try {
            const response = await fetch("/groups", { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error("Could not fetch groups.");
            const groups = await response.json();
            groupsListDiv.innerHTML = "";
            if (groups.length === 0) {
                groupsListDiv.innerHTML = "<div class='card' style='text-align:center;'><p>You haven't created any groups yet.</p></div>";
            } else {
                groups.forEach(group => {
                    const groupEl = document.createElement("div");
                    groupEl.className = "group-item";
                    groupEl.dataset.groupId = group.group_id;
                    groupEl.innerHTML = `<h3>${group.name}</h3><p><i class="fas fa-users"></i><strong>Members:</strong> ${Array.from(group.members).join(", ")}</p>`;
                    groupsListDiv.appendChild(groupEl);
                });
            }
        } catch (error) { showToast(error.message, "error"); } finally { hideLoader(); }
    };

    const showGroupDetail = async (groupId) => {
        currentGroupId = groupId;
        showView('group-detail-view');
        showLoader();
        try {
            const token = getToken();
            const groupResponse = await fetch(`/groups/${groupId}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!groupResponse.ok) throw new Error("Could not load group details.");
            const group = await groupResponse.json();
            currentGroupMembers = group.members; // Store members
            document.getElementById('group-detail-title').textContent = group.name;
            populateExpenseForm(currentGroupMembers);
            
            const expensesResponse = await fetch(`/groups/${groupId}/expenses`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!expensesResponse.ok) throw new Error("Could not load expenses.");
            const expenses = await expensesResponse.json();
            renderExpenses(expenses);
        } catch (error) {
            showToast(error.message, "error");
            showView('app-view');
        } finally { hideLoader(); }
    };
    
    const populateExpenseForm = (members) => {
        const payerSelect = document.getElementById('expense-payer');
        const participantsList = document.getElementById('expense-participants-list');
        payerSelect.innerHTML = '<option value="" disabled selected>Who paid?</option>';
        participantsList.innerHTML = '';
        members.forEach(member => {
            const option = document.createElement('option');
            option.value = member;
            option.textContent = member;
            payerSelect.appendChild(option);
            const checkboxItem = document.createElement('div');
            checkboxItem.className = 'checkbox-item';
            checkboxItem.innerHTML = `<input type="checkbox" id="participant-${member.replace(/\s+/g, '-')}" name="participants" value="${member}" checked><label for="participant-${member.replace(/\s+/g, '-')}">${member}</label>`;
            participantsList.appendChild(checkboxItem);
        });
    };
    
    const renderExpenses = (expenses) => {
        const expensesListDiv = document.getElementById('expenses-list');
        expensesListDiv.innerHTML = '';
        if (expenses.length === 0) {
            expensesListDiv.innerHTML = "<p style='text-align:center;'>No expenses added yet.</p>";
            return;
        }
        expenses.forEach(expense => {
            const expenseEl = document.createElement('div');
            expenseEl.className = 'expense-item';
            expenseEl.innerHTML = `
                <p class="description">${expense.description}</p>
                <div class="expense-details">
                    <span class="payer">Paid by <strong>${expense.payer}</strong></span>
                    <span class="amount">₹${expense.amount.toFixed(2)}</span>
                </div>
                <div class="expense-participants">Split between: ${expense.participants.join(', ')}</div>`;
            expensesListDiv.appendChild(expenseEl);
        });
    };

    // --- Event Listeners ---
    tabs.forEach(tab => { tab.addEventListener("click", () => { tabs.forEach(t => t.classList.remove("active")); tabContents.forEach(c => c.classList.remove("active")); tab.classList.add("active"); document.getElementById(tab.dataset.tab).classList.add("active"); }); });
    const handleAuthFormSubmit = async (url, formData, successMessage, formToReset) => { showLoader(); try { const response = await fetch(url, { method: "POST", body: formData }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "An error occurred."); showToast(successMessage, "success"); if (formToReset) formToReset.reset(); return data; } catch (error) { showToast(error.message, "error"); } finally { hideLoader(); } };
    registerForm.addEventListener("submit", async (e) => { e.preventDefault(); const formData = new FormData(); formData.append('username', document.getElementById('register-email').value); formData.append('password', document.getElementById('register-password').value); await handleAuthFormSubmit("/register", formData, "Registration successful! Please log in.", registerForm); });
    loginForm.addEventListener("submit", async (e) => { e.preventDefault(); const formData = new FormData(); formData.append('username', document.getElementById('login-email').value); formData.append('password', document.getElementById('login-password').value); const data = await handleAuthFormSubmit("/token", formData, "Login successful!", loginForm); if (data && data.access_token) { localStorage.setItem("access_token", data.access_token); updateUIForLoginState(); } });
    logoutButton.addEventListener("click", () => { localStorage.removeItem("access_token"); showToast("Logged out successfully.", "success"); updateUIForLoginState(); });
    
    // Group Creation Logic
    const createGroupForm = document.getElementById("create-group-form"); const memberNameInput = document.getElementById("member-name-input"); const addMemberButton = document.getElementById("add-member-button"); const membersListContainer = document.getElementById("members-list-container"); const createGroupButton = document.getElementById("create-group-button"); let newGroupMembers = []; const renderNewGroupMembersList = () => { membersListContainer.innerHTML = ""; newGroupMembers.forEach(member => { const pill = document.createElement("div"); pill.className = "member-pill"; const safeMemberName = member.replace(/</g, "&lt;").replace(/>/g, "&gt;"); pill.innerHTML = `<span>${safeMemberName}</span><button type="button" class="remove-member-btn" data-member="${safeMemberName}">×</button>`; membersListContainer.appendChild(pill); }); validateCreateGroupButton(); }; const validateCreateGroupButton = () => { createGroupButton.disabled = newGroupMembers.length < 1; }; const addNewGroupMember = () => { const newMemberName = memberNameInput.value.trim(); if (!newMemberName) { showToast("Member name cannot be empty.", "error"); return; } if (newGroupMembers.map(m => m.toLowerCase()).includes(newMemberName.toLowerCase())) { showToast("This member has already been added.", "error"); return; } newGroupMembers.push(newMemberName); renderNewGroupMembersList(); memberNameInput.value = ""; memberNameInput.focus(); }; addMemberButton.addEventListener("click", addNewGroupMember); memberNameInput.addEventListener("keydown", (e) => { if (e.key === 'Enter') { e.preventDefault(); addNewGroupMember(); } }); membersListContainer.addEventListener("click", (e) => { if (e.target && e.target.classList.contains("remove-member-btn")) { const memberToRemove = e.target.dataset.member; newGroupMembers = newGroupMembers.filter(m => m !== memberToRemove); renderNewGroupMembersList(); } });
    createGroupForm.addEventListener("submit", async (e) => { e.preventDefault(); if (newGroupMembers.length < 1) { showToast("You must add at least one other member to the group.", "error"); return; } showLoader(); try { const token = getToken(); const groupName = document.getElementById("group-name").value; const response = await fetch("/groups", { method: "POST", headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ name: groupName, members: newGroupMembers }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Failed to create group."); showToast("Group created successfully!", "success"); document.getElementById("group-name").value = ""; newGroupMembers = []; renderNewGroupMembersList(); fetchGroups(); } catch (error) { showToast(error.message, "error"); } finally { hideLoader(); } });

    // Group Details Event Listeners
    groupsListDiv.addEventListener("click", (e) => { const groupItem = e.target.closest(".group-item"); if (groupItem) { showGroupDetail(groupItem.dataset.groupId); } });
    document.getElementById('back-to-groups-button').addEventListener('click', () => { currentGroupId = null; showView('app-view'); fetchGroups(); });
    document.getElementById('add-expense-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentGroupId) return;
        const description = document.getElementById('expense-description').value;
        const amount = parseFloat(document.getElementById('expense-amount').value);
        const payer = document.getElementById('expense-payer').value;
        const participants = Array.from(document.querySelectorAll('#expense-participants-list input:checked')).map(el => el.value);
        if (!description || !amount || !payer || participants.length === 0) { showToast("Please fill out all expense fields.", "error"); return; }
        showLoader();
        try {
            const token = getToken();
            const response = await fetch(`/groups/${currentGroupId}/expenses`, { method: "POST", headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ description, amount, payer, participants }) });
            if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.detail || "Failed to add expense."); }
            showToast("Expense added successfully!", "success");
            e.target.reset();
            populateExpenseForm(currentGroupMembers); // Re-populate form with full member list and default checks
            showGroupDetail(currentGroupId); // Refresh the view
        } catch (error) { showToast(error.message, "error"); } finally { hideLoader(); }
    });

    // --- Initial Load ---
    updateUIForLoginState();
});
```