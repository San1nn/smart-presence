from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student, Notification, Assignment, LeaveApplication, FeeRecord

# Helper Dependency for Student-Only Routes
async def ensure_student_user(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'student':
        raise HTTPException(status_code=403, detail="Access denied. This portal is for students only.")
    return current_user

# Setup for the student router
router = APIRouter(
    prefix="/student",
    tags=["Student Portal"],
    dependencies=[Depends(ensure_student_user)]
)

templates = Jinja2Templates(directory="app/templates")

# --- NEW STUDENT ROUTES ---

@router.get("/dashboard", response_class=HTMLResponse)
async def get_student_dashboard(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    # Re-route the main /dashboard for students to this dedicated one
    return templates.TemplateResponse("student/dashboard.html", {"request": request, "user": current_user})

@router.get("/my-attendance", response_class=HTMLResponse)
async def my_attendance_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    # Logic to fetch attendance data would go here
    return templates.TemplateResponse("student/my_attendance.html", {"request": request, "user": current_user})

@router.get("/assignments", response_class=HTMLResponse)
async def assignments_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    # Logic to fetch assignments would go here
    return templates.TemplateResponse("student/assignments.html", {"request": request, "user": current_user})

@router.get("/leave-application", response_class=HTMLResponse)
async def leave_application_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("student/leave_application.html", {"request": request, "user": current_user})

@router.get("/fees", response_class=HTMLResponse)
async def fees_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("student/fees.html", {"request": request, "user": current_user})

@router.get("/campus-services", response_class=HTMLResponse)
async def campus_services_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("student/campus_services.html", {"request": request, "user": current_user})

@router.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("student/feedback.html", {"request": request, "user": current_user})