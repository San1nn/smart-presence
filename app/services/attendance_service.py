import cv2
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date
from fastapi import HTTPException
import numpy as np

from .. import config
from ..models.attendance import Student, AttendanceRecord, Subject

def load_recognizer():
    """Loads the trained LBPH recognizer model with proper error handling."""
    # --- ADDED VALIDATION ---
    if not os.path.exists(config.TRAINED_MODEL_PATH):
        print("!!! ERROR: Trained model file not found at:", config.TRAINED_MODEL_PATH)
        raise HTTPException(
            status_code=500, 
            detail="Model not found. Please train the model via the Face Registration page first."
        )
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        recognizer.read(str(config.TRAINED_MODEL_PATH))
    except cv2.error as e:
        print(f"!!! ERROR: OpenCV could not read the model file. It might be corrupt. Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load the recognition model. It may be corrupt. Please retrain the model."
        )
    return recognizer

def mark_attendance(db: Session, subject: str, image: np.ndarray):
    """Recognizes faces in an image and marks attendance with improved error handling."""
    subject_obj = db.query(Subject).filter(Subject.subjectName == subject).first()
    if not subject_obj:
        raise HTTPException(status_code=404, detail=f"Subject '{subject}' not found.")
    subject_id = subject_obj.subjectID

    # --- ADDED VALIDATION ---
    if not os.path.exists(config.HAAR_CASCADE_PATH):
        print("!!! ERROR: Haar Cascade file not found at:", config.HAAR_CASCADE_PATH)
        raise HTTPException(status_code=500, detail="Face detector file is missing from the server.")

    recognizer = load_recognizer()
    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        raise HTTPException(status_code=400, detail="No faces were detected in the image.")

    recognized_students = []
    today = date.today()

    for (x, y, w, h) in faces:
        roll_number_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])

        if confidence < config.RECOGNITION_CONFIDENCE_THRESHOLD:
            student = db.query(Student).filter(Student.rollNumber == str(roll_number_pred)).first()
            if student:
                existing_record = db.query(AttendanceRecord).filter(
                    and_(
                        AttendanceRecord.studentID == student.studentID,
                        AttendanceRecord.subjectID == subject_id,
                        func.date(AttendanceRecord.timestamp) == today
                    )
                ).first()

                if not existing_record:
                    attendance_record = AttendanceRecord(studentID=student.studentID, subjectID=subject_id)
                    db.add(attendance_record)
                    recognized_students.append({"rollNumber": student.rollNumber, "name": student.name, "status": "Attendance Marked"})
                else:
                    recognized_students.append({"rollNumber": student.rollNumber, "name": student.name, "status": "Already Marked Today"})
    
    if not recognized_students:
        raise HTTPException(status_code=404, detail="No known students were recognized with sufficient confidence.")
        
    db.commit()
    return recognized_students