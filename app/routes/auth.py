from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ..database.connection import get_db
from ..services import auth_service
from ..models.attendance import User, Student, UserRole

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- HTML Page Serving Routes ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def registration_page(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})

# --- API Logic Routes ---
@router.post("/register")
async def register_user_submit(
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(...),
    rollNumber: Optional[str] = Form(None),
    studentClass: Optional[str] = Form(None)
):
    """Handles submission of the registration form."""
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        # In a real app, you'd return an error message to the template
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth_service.get_password_hash(password)
    
    if role == UserRole.student:
        if not rollNumber:
            raise HTTPException(status_code=400, detail="Roll number is required for students.")
        new_user = Student(
            name=name,
            email=email,
            hashed_password=hashed_password,
            rollNumber=rollNumber,
            student_class=studentClass
        )
    else: # Teacher
        new_user = User(
            name=name,
            email=email,
            hashed_password=hashed_password,
            role=role
        )
    
    db.add(new_user)
    db.commit()
    
    # Redirect to login page after successful registration
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login")
async def login_submit(
    db: Session = Depends(get_db),
    username: str = Form(...), # from <input name="username">
    password: str = Form(...)  # from <input name="password">
):
    """Handles submission of the login form and sets a session cookie."""
    user = db.query(User).filter(User.email == username).first()
    if not user or not auth_service.verify_password(password, user.hashed_password):
        # In a real app, you'd return an error message to the login page
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = auth_service.create_access_token(data={"sub": user.email})
    
    # Redirect to the main dashboard and set the token in a cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# NEW ROUTE: Logout
@router.get("/logout")
async def logout():
    """Logs the user out by deleting the session cookie."""
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response