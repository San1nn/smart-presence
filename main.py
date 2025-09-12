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
from app.routes import attendance, face_recognition, auth, teacher, admin, student
from app.services.auth_service import try_get_current_user, get_current_user_from_cookie
from app.config import HAAR_CASCADE_PATH

# --- FIX: Create the FastAPI app instance first ---
app = FastAPI(title="Smart Presence")

# --- Now, configure the app and its components ---
templates = Jinja2Templates(directory="app/templates")
models.Base.metadata.create_all(bind=connection.engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Define the main router (for the /dashboard endpoint) ---
main_router = APIRouter()

@main_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: models.User = Depends(get_current_user_from_cookie)):
    if current_user.role == models.UserRole.admin:
        return RedirectResponse(url="/admin/dashboard")
    elif current_user.role == models.UserRole.teacher:
        return templates.TemplateResponse("teacher/dashboard.html", {"request": request, "user": current_user})
    elif current_user.role == models.UserRole.student:
        return RedirectResponse(url="/student/dashboard")
    else:
        raise HTTPException(status_code=403, detail="Unknown user role. Access denied.")

# --- Include all the imported routers into the main app ---
app.include_router(auth.router)
app.include_router(face_recognition.router)
app.include_router(attendance.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(main_router)

# --- Define the root endpoint and startup events last ---
@app.get("/", response_class=HTMLResponse)
def root(request: Request, user: Optional[models.User] = Depends(try_get_current_user)):
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