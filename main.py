from fastapi import FastAPI, Request, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.database import connection
from app.database.connection import get_db
from app.models import attendance as models
from app.routes import attendance, face_recognition, auth
# --- FIX: Import the new cookie-based dependency ---
from app.services.auth_service import try_get_current_user, get_current_user_from_cookie
from app.config import HAAR_CASCADE_PATH

app = FastAPI(title="Smart Presence")
templates = Jinja2Templates(directory="app/templates")
models.Base.metadata.create_all(bind=connection.engine)

main_router = APIRouter()

# --- FIX: Implement Role-Based Dashboard Logic ---
@main_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: models.User = Depends(get_current_user_from_cookie)):
    """
    Serves the main dashboard page after a user logs in.
    It renders a different dashboard template based on the user's role.
    """
    if current_user.role == models.UserRole.admin:
        return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": current_user})
    elif current_user.role == models.UserRole.teacher:
        return templates.TemplateResponse("teacher/dashboard.html", {"request": request, "user": current_user})
    elif current_user.role == models.UserRole.student:
        return templates.TemplateResponse("student/dashboard.html", {"request": request, "user": current_user})
    else:
        raise HTTPException(status_code=403, detail="Unknown user role. Access denied.")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(face_recognition.router)
app.include_router(attendance.router)
app.include_router(main_router)


@app.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db), user: Optional[models.User] = Depends(try_get_current_user)):
    """
    Serves the main page.
    - If the user is logged in, it redirects to the '/dashboard' route.
    - If the user is not logged in, it shows the public 'landing.html' page.
    """
    if user:
        return RedirectResponse(url="/dashboard")
    else:
        return templates.TemplateResponse("landing.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    if not os.path.exists(HAAR_CASCADE_PATH):
        print("="*80)
        print(f"!! WARNING: Haar Cascade file not found !!")
        print(f"Please download 'haarcascade_frontalface_default.xml' and place it in: {HAAR_CASCADE_PATH.parent}")
        print("="*80)