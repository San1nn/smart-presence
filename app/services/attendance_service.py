import cv2
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date
from fastapi import HTTPException
import numpy as np

from .. import config
from ..models.attendance import Student, AttendanceRecord, Subject # Import Subject model

def load_recognizer():
    """Loads the trained LBPH recognizer model from file."""
    if not os.path.exists(config.TRAINED_MODEL_PATH):
        raise HTTPException(status_code=500, detail="Model not found. Please train the model first via the /face-recognition/train endpoint.")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(config.TRAINED_MODEL_PATH))
    return recognizer

def mark_attendance(db: Session, subject: str, image: np.ndarray):
    """
    Recognizes faces in a given image and marks attendance in the database.
    """
    # --- FIX: Look up subject ID from subject name ---
    subject_obj = db.query(Subject).filter(Subject.subjectName == subject).first()
    if not subject_obj:
        raise HTTPException(status_code=404, detail=f"Subject '{subject}' not found.")
    subject_id = subject_obj.subjectID

    recognizer = load_recognizer()
    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        raise HTTPException(status_code=400, detail="No faces detected in the uploaded image.")

    recognized_students = []
    today = date.today()

    for (x, y, w, h) in faces:
        # Predict the face
        roll_number_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])

        # Check if the recognition is confident enough
        if confidence < config.RECOGNITION_CONFIDENCE_THRESHOLD:
            # --- FIX: Query by `rollNumber` instead of non-existent `enrollment_id` ---
            student = db.query(Student).filter(Student.rollNumber == str(roll_number_pred)).first()
            if student:
                # Check if attendance was already marked for this student, subject, and day
                # --- FIX: Use correct column names `studentID` and `subjectID` ---
                existing_record = db.query(AttendanceRecord).filter(
                    and_(
                        AttendanceRecord.studentID == student.studentID,
                        AttendanceRecord.subjectID == subject_id,
                        func.date(AttendanceRecord.timestamp) == today
                    )
                ).first()

                if not existing_record:
                    # --- FIX: Use correct column names `studentID` and `subjectID` ---
                    attendance_record = AttendanceRecord(studentID=student.studentID, subjectID=subject_id)
                    db.add(attendance_record)
                    # --- FIX: Use `rollNumber` in response ---
                    recognized_students.append({"rollNumber": student.rollNumber, "name": student.name, "status": "Attendance Marked"})
                else:
                    recognized_students.append({"rollNumber": student.rollNumber, "name": student.name, "status": "Already Marked Today"})
    
    if not recognized_students:
        raise HTTPException(status_code=404, detail="No known students were recognized in the image.")
        
    db.commit()
    return recognized_students

def get_attendance_summary(db: Session, subject: str):
    """
    Calculates and returns the attendance summary for a given subject.
    """
    # --- FIX: Look up subject ID from subject name ---
    subject_obj = db.query(Subject).filter(Subject.subjectName == subject).first()
    if not subject_obj:
        return [] # Return empty if subject doesn't exist, or raise error
    subject_id = subject_obj.subjectID

    students = db.query(Student).all()
    if not students:
        return []

    # Get the total number of unique class days for the subject
    total_days_query = db.query(func.count(func.distinct(func.date(AttendanceRecord.timestamp)))).filter(AttendanceRecord.subjectID == subject_id)
    total_class_days = total_days_query.scalar() or 0

    if total_class_days == 0:
        # --- FIX: Use `rollNumber` in response ---
        return [{"rollNumber": s.rollNumber, "name": s.name, "attendance_percentage": "0%"} for s in students]

    # Get the number of days each student was present
    # --- FIX: Use correct column names `studentID` and `subjectID` ---
    attendance_counts = db.query(
        AttendanceRecord.studentID,
        func.count(AttendanceRecord.recordID).label("days_present")
    ).filter(AttendanceRecord.subjectID == subject_id).group_by(AttendanceRecord.studentID).all()
    
    present_map = {student_id: count for student_id, count in attendance_counts}
    
    # Calculate percentage for each student
    summary = []
    for student in students:
        # --- FIX: Use `student.studentID` for lookup ---
        days_present = present_map.get(student.studentID, 0)
        percentage = round((days_present / total_class_days) * 100) if total_class_days > 0 else 0
        summary.append({
            # --- FIX: Use `rollNumber` in response ---
            "rollNumber": student.rollNumber,
            "name": student.name,
            "days_present": days_present,
            "total_class_days": total_class_days,
            "attendance_percentage": f"{percentage}%"
        })

    return summary