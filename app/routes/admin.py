from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_
from collections import defaultdict
import datetime

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie, get_password_hash
from ..models.attendance import User, Student, Teacher, AttendanceRecord, Subject, ClassSchedule, DayOfWeek


async def ensure_admin_user(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'admin':
        raise HTTPException(status_code=403, detail="Access denied. Administrator privileges required.")
    return current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(ensure_admin_user)]
)

templates = Jinja2Templates(directory="app/templates")

# Constants
TOTAL_PERIODS = 8
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIOD_TIMES = {
    1: (datetime.time(9, 0), datetime.time(10, 0)),
    2: (datetime.time(10, 0), datetime.time(11, 0)),
    3: (datetime.time(11, 0), datetime.time(12, 0)),
    4: (datetime.time(12, 0), datetime.time(13, 0)),
    5: (datetime.time(14, 0), datetime.time(15, 0)),
    6: (datetime.time(15, 0), datetime.time(16, 0)),
    7: (datetime.time(16, 0), datetime.time(17, 0)),
    8: (datetime.time(17, 0), datetime.time(18, 0)),
}

# Base and Dashboard Routes
@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def admin_root():
    return RedirectResponse(url="/admin/dashboard")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    user_counts = {
        'total': db.query(User).count(),
        'students': db.query(Student).count(),
        'teachers': db.query(Teacher).count(),
    }
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": current_user, "user_counts": user_counts})

# User Management
@router.get("/manage-users", response_class=HTMLResponse)
async def manage_users_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    all_users = db.query(User).filter(User.role != None, User.role != '').order_by(User.userID).all()
    return templates.TemplateResponse("admin/manage_users.html", {"request": request, "users": all_users, "user": current_user})

# Academics Management (Teachers & Subjects)
@router.get("/manage-academics", response_class=HTMLResponse)
async def get_academics_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    all_teachers = db.query(Teacher).order_by(Teacher.name).all()
    all_subjects = db.query(Subject).order_by(Subject.subjectName).all()
    return templates.TemplateResponse(
        "admin/manage_academics.html", 
        {
            "request": request, 
            "user": current_user, 
            "teachers": all_teachers,
            "subjects": all_subjects
        }
    )

@router.post("/add-teacher-and-subject")
async def handle_add_teacher_and_subject(
    db: Session = Depends(get_db),
    teacher_name: str = Form(...),
    teacher_email: str = Form(...),
    password: str = Form(...),
    subject_name: str = Form(...),
    subject_description: str = Form(None)
):
    if db.query(User).filter(User.email == teacher_email).first():
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
    if db.query(Subject).filter(Subject.subjectName == subject_name).first():
        raise HTTPException(status_code=400, detail="A subject with this name already exists.")
    
    new_teacher = Teacher(name=teacher_name, email=teacher_email, hashed_password=get_password_hash(password))
    db.add(new_teacher)
    db.flush()

    new_subject = Subject(
        subjectName=subject_name,
        description=subject_description,
        teacherID=new_teacher.userID
    )
    db.add(new_subject)
    db.commit()
    return RedirectResponse(url="/admin/manage-academics", status_code=303)

@router.post("/assign-teacher")
async def handle_assign_teacher(db: Session = Depends(get_db), subject_id: int = Form(...), teacher_id: int = Form(...)):
    subject = db.query(Subject).filter(Subject.subjectID == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    
    subject.teacherID = teacher_id
    db.commit()
    return RedirectResponse(url="/admin/manage-academics", status_code=303)

# Timetable Management
@router.get("/manage-timetable", response_class=HTMLResponse)
async def get_timetable_management_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    all_teachers = db.query(Teacher).order_by(Teacher.name).all()
    all_subjects = db.query(Subject).order_by(Subject.subjectName).all()
    schedules = db.query(ClassSchedule).all()
    timetable_data = defaultdict(dict)
    for s in schedules:
        timetable_data[s.day_of_week.value][s.period] = s

    return templates.TemplateResponse(
        "admin/manage_timetable.html",
        {
            "request": request, "user": current_user, "total_periods": TOTAL_PERIODS,
            "days_of_week": DAYS_OF_WEEK, "timetable_data": timetable_data,
            "all_teachers": all_teachers, "all_subjects": all_subjects
        }
    )

@router.post("/manage-timetable")
async def handle_create_schedule(db: Session = Depends(get_db), teacher_id: int = Form(...), subject_id: int = Form(...), day_of_week: str = Form(...), period: int = Form(...), location: str = Form(None)):
    subject = db.query(Subject).filter(Subject.subjectID == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    subject.teacherID = teacher_id

    existing_schedule = db.query(ClassSchedule).filter(and_(ClassSchedule.day_of_week == day_of_week, ClassSchedule.period == period)).first()
    start_time, end_time = PERIOD_TIMES.get(period, (None, None))
    if not start_time:
        raise HTTPException(status_code=400, detail="Invalid period number.")

    if existing_schedule:
        existing_schedule.subjectID = subject_id
        existing_schedule.location = location or "N/A"
    else:
        new_schedule = ClassSchedule(
            subjectID=subject_id, day_of_week=DayOfWeek(day_of_week), period=period,
            start_time=start_time, end_time=end_time, location=location or "N/A"
        )
        db.add(new_schedule)
    
    db.commit()
    return RedirectResponse(url="/admin/manage-timetable", status_code=303)