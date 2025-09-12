from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student, Teacher

# --- Helper Dependency for Admin-Only Routes ---
# This function ensures that only users with the 'admin' role can access the routes in this file.
async def ensure_admin_user(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Access denied. Administrator privileges required.")
    return current_user

# --- Setup for the admin router ---
# The dependency is applied to the entire router, protecting all defined endpoints.
router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(ensure_admin_user)]
)

templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the main admin dashboard page."""
    user_counts = {
        'total': db.query(User).count(),
        'students': db.query(Student).count(),
        'teachers': db.query(Teacher).count(),
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": current_user, "user_counts": user_counts}
    )

# --- THIS IS THE ROUTE FOR THE "MANAGE USERS" PAGE ---
@router.get("/manage-users", response_class=HTMLResponse)
async def manage_users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Fetches all users from the database and serves the page
    for viewing and managing user accounts.
    """
    # Query the database for all users, ordering them by their user ID.
    # This query will only fetch users with a valid role to prevent crashes.
    all_users = db.query(User).filter(User.role != None, User.role != '').order_by(User.userID).all()
    
    # Render the HTML template, passing the list of users to it.
    return templates.TemplateResponse(
        "admin/manage_users.html",
        {
            "request": request,
            "users": all_users,
            "user": current_user
        }
    )
# --- END OF "MANAGE USERS" ROUTE ---


@router.get("/site-settings", response_class=HTMLResponse)
async def site_settings_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Page for managing site content like 'About Us', newsletters, etc."""
    return templates.TemplateResponse(
        "admin/site_settings.html",
        {"request": request, "user": current_user}
    )

@router.get("/calendar-events", response_class=HTMLResponse)
async def calendar_events_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Page for managing calendar events, notifications, and alerts."""
    return templates.TemplateResponse(
        "admin/calendar_events.html",
        {"request": request, "user": current_user}
    )
# ... (keep all existing imports: APIRouter, Depends, RedirectResponse, etc.)

# ... (keep the existing router setup and other routes like /dashboard) ...

# --- ADD THIS NEW POST ROUTE for deleting a user ---
@router.post("/manage-users/delete/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Handles the deletion of a user account.
    """
    # Prevent admin from deleting their own account
    if user_id == current_user.userID:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    user_to_delete = db.query(User).filter(User.userID == user_id).first()

    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")

    # --- Important Data Integrity Section ---
    # Before deleting a user, you must handle their related data.
    # If the user is a student, delete their attendance, submissions, etc.
    # If the user is a teacher, you need a plan for their subjects (e.g., set teacherID to NULL).
    # For now, we will add a simple cascade for attendance.
    if user_to_delete.role.value == 'student':
        db.query(AttendanceRecord).filter(AttendanceRecord.studentID == user_id).delete(synchronize_session=False)

    db.delete(user_to_delete)
    db.commit()

    # Redirect back to the manage users page
    return RedirectResponse(url="/admin/manage-users", status_code=303)
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie
# --- FIX: Add AttendanceRecord to the import list ---
from ..models.attendance import User, Student, Teacher, AttendanceRecord

# ... (keep the ensure_admin_user helper and router setup) ...
async def ensure_admin_user(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Access denied.")
    return current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(ensure_admin_user)]
)
templates = Jinja2Templates(directory="app/templates")

# ... (keep the /dashboard and /manage-users GET routes) ...


# --- This is the function where the error occurred ---
@router.post("/manage-users/delete/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Handles the deletion of a user account."""
    if user_id == current_user.userID:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    user_to_delete = db.query(User).filter(User.userID == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")

    # This line will now work because AttendanceRecord is imported
    if user_to_delete.role.value == 'student':
        db.query(AttendanceRecord).filter(AttendanceRecord.studentID == user_id).delete(synchronize_session=False)

    db.delete(user_to_delete)
    db.commit()

    return RedirectResponse(url="/admin/manage-users", status_code=303)

# ... (keep other admin routes) ...
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student, Teacher, AttendanceRecord

# Helper Dependency for Admin-Only Routes
async def ensure_admin_user(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Access denied.")
    return current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(ensure_admin_user)]
)
templates = Jinja2Templates(directory="app/templates")


# --- ADD THIS ENTIRE FUNCTION ---
@router.get("/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the main admin dashboard page."""
    # Fetch data for dashboard widgets
    user_counts = {
        'total': db.query(User).count(),
        'students': db.query(Student).count(),
        'teachers': db.query(Teacher).count(),
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": current_user, "user_counts": user_counts}
    )
# --- END OF FUNCTION TO ADD ---


# ... (rest of your admin routes like /manage-users, etc.)
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student, Teacher, AttendanceRecord

# ... (keep the helper function and router setup)

@router.get("/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    # ... (this function is correct)
    user_counts = {
        'total': db.query(User).count(),
        'students': db.query(Student).count(),
        'teachers': db.query(Teacher).count(),
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": current_user, "user_counts": user_counts}
    )

# --- ADD THIS ENTIRE FUNCTION ---
@router.get("/manage-users", response_class=HTMLResponse)
async def manage_users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Fetches all users from the database and serves the page
    for viewing and managing user accounts.
    """
    # This query will only fetch users with a valid role to prevent crashes
    all_users = db.query(User).filter(User.role != None, User.role != '').order_by(User.userID).all()
    
    return templates.TemplateResponse(
        "admin/manage_users.html",
        {
            "request": request,
            "users": all_users,
            "user": current_user
        }
    )
# --- END OF FUNCTION TO ADD ---


@router.post("/manage-users/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    # ... (this function is correct)
    if user_id == current_user.userID:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    user_to_delete = db.query(User).filter(User.userID == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")
    if user_to_delete.role.value == 'student':
        db.query(AttendanceRecord).filter(AttendanceRecord.studentID == user_id).delete(synchronize_session=False)
    db.delete(user_to_delete)
    db.commit()
    return RedirectResponse(url="/admin/manage-users", status_code=303)

# ... (rest of your admin routes)
# ... (keep all existing imports: APIRouter, Depends, Form, etc.) ...
# Add RedirectResponse and new models
from fastapi.responses import HTMLResponse, RedirectResponse
from ..models.attendance import User, Student, Teacher, Subject, ClassSchedule, DayOfWeek
import datetime

# ... (keep the existing router setup and other admin routes) ...

# --- ADD THESE TWO NEW ROUTES ---

@router.get("/manage-timetable", response_class=HTMLResponse)
async def get_timetable_management_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the page for creating new class schedules."""
    # Fetch all teachers and subjects to populate the form dropdowns
    all_teachers = db.query(Teacher).order_by(Teacher.name).all()
    all_subjects = db.query(Subject).order_by(Subject.subjectName).all()

    return templates.TemplateResponse(
        "admin/manage_timetable.html",
        {
            "request": request,
            "user": current_user,
            "teachers": all_teachers,
            "subjects": all_subjects
        }
    )

@router.post("/manage-timetable")
async def handle_create_schedule(
    db: Session = Depends(get_db),
    teacher_id: int = Form(...),
    subject_id: int = Form(...),
    day_of_week: DayOfWeek = Form(...),
    start_time: datetime.time = Form(...),
    end_time: datetime.time = Form(...),
    location: str = Form(None)
):
    """Processes the form to create a new schedule and assign the subject to the teacher."""
    
    # 1. Find the subject and assign the selected teacher to it
    subject = db.query(Subject).filter(Subject.subjectID == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    
    subject.teacherID = teacher_id

    # 2. Create the new ClassSchedule entry
    new_schedule = ClassSchedule(
        subjectID=subject_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        location=location or "N/A"
    )

    db.add(new_schedule)
    db.commit()

    # Redirect back to the same page to add another entry
    return RedirectResponse(url="/admin/manage-timetable", status_code=303)
# ... (keep all existing imports: APIRouter, Depends, Form, RedirectResponse, etc.) ...
from ..services import auth_service # We need this for hashing passwords

# ... (keep the existing router setup and other admin routes) ...

# --- NEW ROUTES FOR MANAGING TEACHERS ---

@router.get("/manage-teachers", response_class=HTMLResponse)
async def get_manage_teachers_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the page for viewing and adding teachers."""
    all_teachers = db.query(Teacher).order_by(Teacher.name).all()
    return templates.TemplateResponse(
        "admin/manage_teachers.html",
        {"request": request, "user": current_user, "teachers": all_teachers}
    )

@router.post("/manage-teachers/add")
async def handle_add_teacher(
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    """Processes the form to create a new teacher account."""
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    hashed_password = auth_service.get_password_hash(password)
    
    new_teacher = Teacher(
        name=name,
        email=email,
        hashed_password=hashed_password
    )
    db.add(new_teacher)
    db.commit()

    return RedirectResponse(url="/admin/manage-teachers", status_code=303)


# --- NEW ROUTES FOR MANAGING SUBJECTS ---

@router.get("/manage-subjects", response_class=HTMLResponse)
async def get_manage_subjects_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the page for viewing and adding subjects."""
    all_subjects = db.query(Subject).order_by(Subject.subjectName).all()
    return templates.TemplateResponse(
        "admin/manage_subjects.html",
        {"request": request, "user": current_user, "subjects": all_subjects}
    )

@router.post("/manage-subjects/add")
async def handle_add_subject(
    db: Session = Depends(get_db),
    subject_name: str = Form(...),
    description: str = Form(None)
):
    """Processes the form to create a new subject."""
    existing_subject = db.query(Subject).filter(Subject.subjectName == subject_name).first()
    if existing_subject:
        raise HTTPException(status_code=400, detail="A subject with this name already exists.")

    new_subject = Subject(
        subjectName=subject_name,
        description=description
    )
    db.add(new_subject)
    db.commit()
    
    return RedirectResponse(url="/admin/manage-subjects", status_code=303)
# ... (keep all existing imports: APIRouter, Depends, etc.) ...
from collections import defaultdict

# ... (keep the existing router setup and other admin routes) ...

# --- ADD THIS NEW ROUTE for the preview page ---
@router.get("/timetable-preview", response_class=HTMLResponse)
async def get_timetable_preview_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Fetches all class schedules for all teachers and displays them."""
    
    # Fetch all schedules and join with subject and teacher to get all necessary info
    all_schedules = db.query(ClassSchedule).join(Subject).order_by(ClassSchedule.start_time).all()

    # Group the schedules by day of the week for easy rendering
    timetable_data = defaultdict(list)
    for schedule in all_schedules:
        timetable_data[schedule.day_of_week.value].append(schedule)

    # Define the order of days for the template
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return templates.TemplateResponse(
        "admin/timetable_preview.html",
        {
            "request": request,
            "user": current_user,
            "timetable": timetable_data,
            "days_order": days_order
        }
    )