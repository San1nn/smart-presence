from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.database import connection
from app.models import attendance as models
from app.routes import attendance, face_recognition, auth, teacher, admin, student
from app.services.auth_service import try_get_current_user, get_current_user_from_cookie
from app.config import HAAR_CASCADE_PATH

# Initialize the FastAPI app
app = FastAPI(title="Smart Presence")

# Create all database tables based on the models
models.Base.metadata.create_all(bind=connection.engine)

# Mount the static files directory to serve images, css, etc.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# --- Include all the application routers ---
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(face_recognition.router)
app.include_router(attendance.router)


# --- Main application routes ---

@app.get("/", response_class=HTMLResponse)
def root(request: Request, user: Optional[models.User] = Depends(try_get_current_user)):
    """
    Handles the landing page. Redirects to the dashboard if a user is logged in.
    """
    if user:
        return RedirectResponse(url="/dashboard")
    else:
        return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: models.User = Depends(get_current_user_from_cookie)):
    """
    Redirects logged-in users to their respective dashboards based on their role.
    """
    if current_user.role == models.UserRole.admin:
        return RedirectResponse(url="/admin/dashboard")
    elif current_user.role == models.UserRole.teacher:
        return templates.TemplateResponse("teacher/dashboard.html", {"request": request, "user": current_user})
    elif current_user.role == models.UserRole.student:
        return RedirectResponse(url="/student/dashboard")
    else:
        raise HTTPException(status_code=403, detail="Unknown user role. Access denied.")

@app.on_event("startup")
async def startup_event():
    """
    Checks for the Haar Cascade file on application startup.
    """
    if not os.path.exists(HAAR_CASCADE_PATH):
        print("="*80)
        print(f"!! WARNING: Haar Cascade file not found !!")
        print(f"Please download 'haarcascade_frontalface_default.xml' and place it in: {HAAR_CASCADE_PATH.parent}")
        print("="*80)