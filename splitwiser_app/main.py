# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .routers import auth, groups, expenses # <--- Import the new router

# Create the FastAPI app instance
app = FastAPI(
    title="SplitWiser",
    description="API for managing trip expenses.",
    version="0.2.0"
)

# --- Include Routers ---
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(expenses.router) # <--- Add this line

# --- Mount Static Files and Serve Frontend ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    """Serves the main HTML file for the single-page application."""
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)