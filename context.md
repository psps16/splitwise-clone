
---

### Project Context: AI-Enhanced Expense Splitter (SplitWiser)

#### 1. Project Goal & Vision

The primary goal is to build a full-stack web application inspired by Splitwise, designed to help users manage and split expenses within groups.

The key long-term differentiator is the **integration of AI agents** to provide smart automation features, such as receipt scanning, natural language expense entry, and intelligent settlement suggestions. The development is phased, focusing on building a solid, traditional expense-splitting application first, before adding the AI layer.

#### 2. Current Functionality & Features (What's Done)

We have successfully built the foundational, non-AI version of the application, which includes:

*   **Full User Authentication:**
    *   Users can register with an email and password.
    *   Passwords are never stored in plain text; they are securely hashed using **bcrypt**.
    *   A secure login system issues **JSON Web Tokens (JWTs)** to authenticated users for session management.

*   **User-Specific Group Management:**
    *   Logged-in users can create "trip groups" by providing a name and adding members.
    *   Members are added by name and do not need to be registered users on the platform.
    *   The application enforces privacy: **users can only view the groups they have created**.

*   **Data Persistence:**
    *   All user and group data is stored in a single JSON file (`app_database.json`), which acts as a simple, file-based NoSQL database.

*   **Polished Web Frontend:**
    *   A single-page application (SPA) built with vanilla HTML, CSS, and JavaScript.
    *   Features a modern UI with tabbed login/register forms.
    *   Provides clear user feedback through loaders and toast notifications.
    *   Includes a highly interactive form for creating groups where members can be added/removed as visual "pills" before submission.
    *   Dynamically fetches and displays the logged-in user's groups from the backend.

*   **Modular FastAPI Backend:**
    *   The backend is built with FastAPI and is structured into logical modules for scalability and maintainability.
    *   It serves the API endpoints for authentication and group management.
    *   It also serves the static frontend files (`index.html`, `style.css`, `script.js`).

#### 3. Current Technical Stack

*   **Backend:** Python 3, FastAPI
*   **Server:** Uvicorn
*   **Data Validation:** Pydantic
*   **Security:** `passlib[bcrypt]` for password hashing, `python-jose` for JWT creation and validation.
*   **Database:** A single JSON file (`app_database.json`).
*   **Frontend:** HTML5, CSS3, modern JavaScript (ES6+).

#### 4. Current Project Structure

The project has been refactored from a single file into a standard, modular structure:

```
splitwise/                  <-- Your project root directory
├── splitwiser_app/         <-- THE NEW MAIN APP PACKAGE
│   ├── __init__.py         <-- NEW (can be empty)
│   ├── routers/
│   │   ├── __init__.py     <-- NEW (can be empty)
│   │   ├── auth.py
│   │   └── groups.py
│   ├── database.py
│   ├── main.py
│   ├── schemas.py
│   └── security.py
└── static/                 <-- Stays at the root
    ├── index.html
    ├── script.js
    └── style.css
```

#### 5. Next Logical Steps & Future Vision

*   **Immediate Next Step:** Implement functionality to **add expenses to a specific group**. This will involve creating a new data model for expenses and new endpoints (e.g., `POST /groups/{group_id}/expenses`).
*   **Core Logic Integration:** Integrate the **debt settlement algorithm** (which we developed earlier using an adjacency list and heaps) into the API to calculate simplified "who owes whom" results for a given group.
*   **Long-Term Vision:** Once the core functionality is complete and robust, begin integrating the planned **AI agent features**, starting with a simple one like Natural Language Processing (NLP) for expense entry (e.g., parsing "I paid $50 for dinner with Alice and Bob").