from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_
from collections import defaultdict

from ..database.connection import get_db
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Teacher, Subject, Student, AttendanceRecord, ClassSchedule, DayOfWeek

# --- FIX: This block MUST come first, right after the imports ---
router = APIRouter(
    prefix="/teacher",
    tags=["Teacher Dashboard"]
)

templates = Jinja2Templates(directory="app/templates")
# --- END OF FIX ---


# --- Now, all the routes can be defined below this point ---

@router.get("/my-classes", response_class=HTMLResponse)
async def get_my_classes_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    teacher = db.query(Teacher).filter(Teacher.userID == current_user.userID).first()
    if not teacher: raise HTTPException(status_code=404, detail="Teacher record not found.")
    subjects = teacher.subjects_taught
    class_data = []
    for subject in subjects:
        student_count = db.query(func.count(distinct(AttendanceRecord.studentID))).filter(AttendanceRecord.subjectID == subject.subjectID).scalar() or 0
        class_data.append({"subject": subject, "student_count": student_count})
    return templates.TemplateResponse("teacher/my_classes.html", {"request": request, "user": current_user, "classes": class_data})

@router.get("/attendance-reports", response_class=HTMLResponse)
async def get_attendance_reports_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    teacher = db.query(Teacher).filter(Teacher.userID == current_user.userID).first()
    if not teacher: raise HTTPException(status_code=404, detail="Teacher record not found.")
    subjects_taught = teacher.subjects_taught
    return templates.TemplateResponse("teacher/attendance_reports.html", {"request": request, "user": current_user, "subjects": subjects_taught})

@router.get("/timetable", response_class=HTMLResponse)
async def get_timetable_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    schedules = db.query(ClassSchedule).join(Subject).filter(Subject.teacherID == current_user.userID).order_by(ClassSchedule.start_time).all()
    timetable_data = defaultdict(list)
    for schedule in schedules:
        timetable_data[schedule.day_of_week.value].append(schedule)
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return templates.TemplateResponse("teacher/timetable.html", {"request": request, "user": current_user, "timetable": timetable_data, "days_order": days_order})

@router.get("/class/{subject_id}", response_class=HTMLResponse)
async def get_class_details_page(request: Request, subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    subject = db.query(Subject).filter(Subject.subjectID == subject_id).first()
    if not subject: raise HTTPException(status_code=404, detail="Class not found.")
    if subject.teacherID != current_user.userID: raise HTTPException(status_code=403, detail="Not authorized.")
    total_class_days = db.query(func.count(distinct(func.date(AttendanceRecord.timestamp)))).filter(AttendanceRecord.subjectID == subject_id).scalar() or 0
    enrolled_student_ids_query = db.query(distinct(AttendanceRecord.studentID)).filter(AttendanceRecord.subjectID == subject_id)
    enrolled_student_ids = [s_id for s_id, in enrolled_student_ids_query.all()]
    attendance_data = []
    if enrolled_student_ids:
        students = db.query(Student).filter(Student.studentID.in_(enrolled_student_ids)).all()
        for student in students:
            days_present = db.query(func.count(AttendanceRecord.recordID)).filter(
                and_(AttendanceRecord.subjectID == subject_id, AttendanceRecord.studentID == student.studentID)
            ).scalar() or 0
            percentage = round((days_present / total_class_days) * 100) if total_class_days > 0 else 0
            attendance_data.append({"student": student, "days_present": days_present, "total_class_days": total_class_days, "percentage": percentage})
    return templates.TemplateResponse("teacher/class_details.html", {"request": request, "user": current_user, "subject": subject, "attendance_data": attendance_data})

@router.get("/add-class", response_class=HTMLResponse)
async def get_add_class_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    return templates.TemplateResponse("teacher/add_class.html", {"request": request, "user": current_user})

@router.post("/add-class")
async def handle_add_class_form(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie), subject_name: str = Form(...), subject_description: str = Form(None)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    existing_subject = db.query(Subject).filter(and_(Subject.subjectName == subject_name, Subject.teacherID == current_user.userID)).first()
    if existing_subject: raise HTTPException(status_code=400, detail="You already have a class with this name.")
    new_subject = Subject(subjectName=subject_name, description=subject_description, teacherID=current_user.userID)
    db.add(new_subject)
    db.commit()
    return RedirectResponse(url="/teacher/my-classes", status_code=303)

@router.get("/edit-class/{subject_id}", response_class=HTMLResponse)
async def get_edit_class_page(request: Request, subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    subject = db.query(Subject).filter(Subject.subjectID == subject_id, Subject.teacherID == current_user.userID).first()
    if not subject: raise HTTPException(status_code=404, detail="Class not found or you are not authorized to edit it.")
    return templates.TemplateResponse("teacher/edit_class.html", {"request": request, "user": current_user, "subject": subject})

@router.post("/edit-class/{subject_id}")
async def handle_edit_class_form(subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie), subject_name: str = Form(...), subject_description: str = Form(None)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    subject_to_update = db.query(Subject).filter(Subject.subjectID == subject_id, Subject.teacherID == current_user.userID).first()
    if not subject_to_update: raise HTTPException(status_code=404, detail="Class not found or not authorized.")
    subject_to_update.subjectName = subject_name
    subject_to_update.description = subject_description
    db.commit()
    return RedirectResponse(url="/teacher/my-classes", status_code=303)

@router.post("/delete-class/{subject_id}")
async def handle_delete_class(subject_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != 'teacher': raise HTTPException(status_code=403, detail="Access denied.")
    subject_to_delete = db.query(Subject).filter(Subject.subjectID == subject_id, Subject.teacherID == current_user.userID).first()
    if not subject_to_delete: raise HTTPException(status_code=404, detail="Class not found or not authorized.")
    db.query(AttendanceRecord).filter(AttendanceRecord.subjectID == subject_id).delete(synchronize_session=False)
    db.delete(subject_to_delete)
    db.commit()
    return RedirectResponse(url="/teacher/my-classes", status_code=303)
# ... (keep all existing imports and routes) ...

# --- ADD THIS NEW ROUTE ---
@router.get("/realtime-attendance", response_class=HTMLResponse)
async def get_realtime_attendance_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the page for real-time, continuous attendance marking."""
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Access denied.")

    teacher = db.query(Teacher).filter(Teacher.userID == current_user.userID).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher record not found.")

    # Fetch subjects to populate the dropdown
    subjects = teacher.subjects_taught

    return templates.TemplateResponse(
        "teacher/realtime_attendance.html",
        {"request": request, "user": current_user, "subjects": subjects}
    )
# ... (keep all existing imports: APIRouter, Depends, Form, RedirectResponse, etc.) ...
from sqlalchemy import and_

# ... (keep the existing router setup) ...

# --- ADD THESE TWO NEW ROUTES ---

@router.get("/add-class", response_class=HTMLResponse)
async def get_add_class_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the HTML page with the form to add a new class."""
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Access denied.")
    
    return templates.TemplateResponse(
        "teacher/add_class.html",
        {"request": request, "user": current_user}
    )

@router.post("/add-class")
async def handle_add_class_form(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    subject_name: str = Form(...),
    subject_description: str = Form(None)
):
    """Processes the form data to create a new subject and assign it to the teacher."""
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Access denied.")

    # Check for duplicates for this specific teacher
    existing_subject = db.query(Subject).filter(
        and_(
            Subject.subjectName == subject_name,
            Subject.teacherID == current_user.userID
        )
    ).first()

    if existing_subject:
        # A more advanced implementation could show an error on the form
        raise HTTPException(status_code=400, detail="You already have a class with this exact name.")

    # Create the new subject and link it to the current teacher
    new_subject = Subject(
        subjectName=subject_name,
        description=subject_description,
        teacherID=current_user.userID
    )
    
    db.add(new_subject)
    db.commit()

    # Redirect back to the list of classes to see the new addition
    return RedirectResponse(url="/teacher/my-classes", status_code=303)

# ... (keep all your other existing teacher routes below) ...
# ... (keep all existing imports and routes) ...

# --- ADD THIS NEW ROUTE ---
@router.get("/bulk-attendance", response_class=HTMLResponse)
async def get_bulk_attendance_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Serves the page for marking attendance from a single class photo."""
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Access denied.")

    teacher = db.query(Teacher).filter(Teacher.userID == current_user.userID).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher record not found.")

    # Fetch subjects to populate the dropdown
    subjects = teacher.subjects_taught

    return templates.TemplateResponse(
        "teacher/bulk_attendance.html",
        {"request": request, "user": current_user, "subjects": subjects}
    )