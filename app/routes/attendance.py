from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import numpy as np
import cv2

from ..database.connection import get_db
from ..services import attendance_service
from ..utils import image_utils
from ..models.attendance import Student
from .. import config

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)

@router.post("/mark")
async def mark_attendance_endpoint(
    subject: str = Form(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Mark attendance by recognizing faces in an uploaded image.
    - **subject**: The subject for which attendance is being taken.
    - **image_file**: An image containing faces of students.
    """
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    try:
        cv2_image = await image_utils.to_cv2_image(image_file)
        result = attendance_service.mark_attendance(db=db, subject=subject, image=cv2_image)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/summary/{subject}")
def get_attendance_summary_endpoint(subject: str, db: Session = Depends(get_db)):
    """
    Get a summary of attendance for a specific subject.
    """
    summary = attendance_service.get_attendance_summary(db=db, subject=subject)
    if not summary:
        raise HTTPException(status_code=404, detail=f"No student or attendance data found for subject '{subject}'.")
    return summary

@router.post("/recognize-frame")
async def recognize_faces_in_frame(
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Detects and recognizes faces in a single frame for UI display.
    This endpoint does NOT mark attendance.
    """
    try:
        recognizer = attendance_service.load_recognizer()
        detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
        
        cv2_image = await image_utils.to_cv2_image(image_file)
        gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        results = []
        for (x, y, w, h) in faces:
            roll_number_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            
            name = "Unknown"
            if confidence < config.RECOGNITION_CONFIDENCE_THRESHOLD:
                student = db.query(Student).filter(Student.rollNumber == str(roll_number_pred)).first()
                if student:
                    name = student.name
            
            results.append({
                "name": name,
                "box": [x, y, w, h]
            })
            
        return {"results": results}
    except Exception:
        return {"results": []}