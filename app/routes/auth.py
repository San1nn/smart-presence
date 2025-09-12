from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import re

from ..database.connection import get_db
from ..services import auth_service
from ..models.attendance import User, Student, UserRole

# --- FIX: This block MUST come first, right after the imports ---
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)
# --- END OF FIX ---


# --- HTML Page Serving Routes ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.get("/register", response_class=HTMLResponse)
async def registration_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("registration.html", {"request": request, "error": error})


# --- API Logic Routes ---
@router.post("/register")
async def register_user_submit(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(...),
    rollNumber: Optional[str] = Form(None),
    studentClass: Optional[str] = Form(None)
):
    """Handles submission of the registration form with password and uniqueness validation."""
    
    # Password validation
    if len(password) < 8 or not re.search("[a-z]", password) or not re.search("[A-Z]", password) or not re.search("[0-9]", password) or not re.search("[!@#$%^&*]", password):
        error = "Password does not meet the complexity requirements."
        return templates.TemplateResponse("registration.html", {"request": request, "error": error}, status_code=400)

    # Check for duplicate email
    if db.query(User).filter(User.email == email).first():
        error = "An account with this email already exists."
        return templates.TemplateResponse("registration.html", {"request": request, "error": error}, status_code=400)

    # Check for duplicate roll number for students
    if role == UserRole.student:
        if not rollNumber:
            raise HTTPException(status_code=400, detail="Roll number is required for students.")
        if db.query(Student).filter(Student.rollNumber == rollNumber).first():
            error = f"A student with Roll Number '{rollNumber}' already exists."
            return templates.TemplateResponse("registration.html", {"request": request, "error": error}, status_code=400)

    hashed_password = auth_service.get_password_hash(password)
    
    if role == UserRole.student:
        new_user = Student(
            name=name, email=email, hashed_password=hashed_password,
            rollNumber=rollNumber, student_class=studentClass
        )
    else:
        new_user = User(name=name, email=email, hashed_password=hashed_password, role=role)
    
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login")
async def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    user = db.query(User).filter(User.email == username).first()
    if not user or not auth_service.verify_password(password, user.hashed_password):
        error = "Incorrect email or password. Please try again."
        return templates.TemplateResponse("login.html", {"request": request, "error": error}, status_code=401)

    access_token = auth_service.create_access_token(data={"sub": user.email})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response