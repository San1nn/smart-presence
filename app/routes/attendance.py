from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import numpy as np

from ..database.connection import get_db
from ..services import attendance_service
from ..utils import image_utils

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

    - **subject**: The subject for which attendance is being taken (e.g., 'Math').
    - **image_file**: An image containing faces of students.
    """
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    try:
        cv2_image = await image_utils.to_cv2_image(image_file)
        # Pass the original numpy array to the service
        result = attendance_service.mark_attendance(db=db, subject=subject, image=cv2_image)
        return result
    except HTTPException as e:
        # Re-raise HTTPExceptions to return proper error responses
        raise e
    except Exception as e:
        # Catch any other unexpected errors during processing
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/summary/{subject}")
def get_attendance_summary_endpoint(subject: str, db: Session = Depends(get_db)):
    """
    Get a summary of attendance for a specific subject.
    Calculates the attendance percentage for each registered student.
    """
    summary = attendance_service.get_attendance_summary(db=db, subject=subject)
    if not summary:
        raise HTTPException(status_code=404, detail=f"No student or attendance data found for subject '{subject}'.")
    return summary
    # ... (keep all existing imports: APIRouter, Depends, Form, File, UploadFile, etc.)
from ..services import attendance_service
from ..utils import image_utils
import cv2 # Make sure cv2 is imported
from ..models.attendance import Student # Import Student model

# ... (keep the existing router setup) ...

# --- NEW, LIGHTWEIGHT ROUTE for Real-Time UI Feedback ---
@router.post("/recognize-frame")
async def recognize_faces_in_frame(
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db) # We need the DB to look up names
):
    """
    Detects and recognizes faces in a single frame for UI display.
    Returns a list of names and bounding box coordinates.
    This endpoint does NOT mark attendance.
    """
    try:
        # Load the pre-trained models
        recognizer = attendance_service.load_recognizer()
        detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
        
        # Process the incoming image
        cv2_image = await image_utils.to_cv2_image(image_file)
        gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        
        # Detect all faces in the frame
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        results = []
        for (x, y, w, h) in faces:
            # For each face, predict who it is
            roll_number_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            
            name = "Unknown" # Default name
            if confidence < config.RECOGNITION_CONFIDENCE_THRESHOLD:
                # If confidence is good, look up the student's name in the DB
                student = db.query(Student).filter(Student.rollNumber == str(roll_number_pred)).first()
                if student:
                    name = student.name
            
            results.append({
                "name": name,
                "box": [x, y, w, h] # Send coordinates back to the UI
            })
            
        return {"results": results}
    except Exception:
        # If model isn't trained or another error occurs, return empty
        return {"results": []}

# --- The /mark route remains unchanged for the actual database marking ---
@router.post("/mark")
async def mark_attendance_endpoint(
    subject: str = Form(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    cv2_image = await image_utils.to_cv2_image(image_file)
    return attendance_service.mark_attendance(db=db, subject=subject, image=cv2_image)
