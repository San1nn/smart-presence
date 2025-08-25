from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..database.connection import get_db
from ..services import face_rec_service
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"]
)

# --- Pydantic model for the new request body ---
class FaceRegistrationRequest(BaseModel):
    roll_number: str
    name: str
    images: List[str]  # This will be a list of base64 encoded image strings

# --- NEW ENDPOINT to fetch students for the dropdown ---
@router.get("/students-for-registration")
def get_students_for_registration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Gets a list of all registered students to populate the registration form's dropdown.
    """
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    students = db.query(Student).order_by(Student.name).all()
    if not students:
        return []
    
    return [{"roll_number": s.rollNumber, "name": s.name} for s in students]


@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    """
    Serves the HTML page for face recognition and attendance marking.
    This now serves the new webcam-enabled page.
    """
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})

# --- MODIFIED to handle webcam data instead of file uploads ---
@router.post("/register-faces")
async def register_student_faces(
    request_data: FaceRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Uploads face images for a PRE-REGISTERED student captured via webcam.
    """
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized to register faces.")

    if not request_data.images:
        raise HTTPException(status_code=400, detail="No image files provided.")

    # Validate that the student exists before saving images
    face_rec_service.add_student_db(db=db, roll_number=request_data.roll_number, name=request_data.name)
    
    # Call a new service function designed to handle base64 images
    return await face_rec_service.save_face_images_from_base64(
        roll_number=request_data.roll_number, 
        name=request_data.name, 
        base64_images=request_data.images
    )

@router.post("/train")
def train_model_endpoint(current_user: User = Depends(get_current_user_from_cookie)):
    """
    Triggers the face recognition model training process.
    """
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized to train the model.")
    return face_rec_service.train_model()

# The verify-face endpoint remains unchanged
@router.post("/verify-face")
async def verify_student_face(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Verifies a student's identity from a live image for attendance.
    """
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized to verify faces.")

    roll_number = await face_rec_service.recognize_face(image, db)

    if roll_number:
        attendance_status = face_rec_service.mark_attendance(db, roll_number)
        return {"message": f"Attendance marked for {roll_number}.", "status": attendance_status}
    else:
        raise HTTPException(status_code=404, detail="Student not recognized. Please try again.")