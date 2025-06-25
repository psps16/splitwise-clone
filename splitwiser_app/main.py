# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .routers import auth, groups

# Create the FastAPI app instance
app = FastAPI(
    title="SplitWiser",
    description="API for managing trip expenses.",
    version="0.2.0"
)

# --- Include Routers ---
# Include the authentication router (for /register, /token)
app.include_router(auth.router)
# Include the groups router (for /groups)
app.include_router(groups.router)

# --- Mount Static Files and Serve Frontend ---
# This must come after the API routers
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    """Serves the main HTML file for the single-page application."""
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)