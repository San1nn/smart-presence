import dlib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import func, and_
import cv2
import shutil
import os

from .. import config
from ..models.attendance import Student, Subject, AttendanceRecord

# --- Load Dlib models once when the service starts ---
try:
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(config.SHAPE_PREDICTOR_PATH))
    face_reco_model = dlib.face_recognition_model_v1(str(config.FACE_REC_MODEL_PATH))
except Exception as e:
    print(f"!!! DLIB MODEL ERROR: {e}. Please ensure model files are in data/dlib_models/ !!!")
    detector = predictor = face_reco_model = None

# --- Load known face features from CSV ---
try:
    features_df = pd.read_csv(config.FACE_FEATURES_CSV_PATH)
    known_face_features = np.array(features_df.iloc[:, 1:])
    known_face_roll_numbers = list(features_df.iloc[:, 0])
except FileNotFoundError:
    print(f"!!! WARNING: {config.FACE_FEATURES_CSV_PATH} not found. Recognition will not work. !!!")
    known_face_features = []
    known_face_roll_numbers = []

def return_euclidean_distance(feature_1, feature_2):
    return np.linalg.norm(feature_1 - feature_2)

def register_face_dlib(roll_number: str, name: str, image: np.ndarray):
    if not detector:
        raise Exception("Dlib detector not loaded.")

    student_dir = config.DATA_DIR / "data_faces_from_camera" / f"{roll_number}_{name}"
    os.makedirs(student_dir, exist_ok=True)

    faces = detector(image, 1)

    if len(faces) == 0:
        return {"status": "error", "message": "No face detected. Please position yourself in the center."}
    
    if len(faces) > 1:
        return {"status": "error", "message": "Multiple faces detected. Only one person at a time."}

    face = faces[0]
    
    ss_cnt = 0
    for f in os.listdir(student_dir):
        if f.endswith(".jpg"):
            try:
                num = int(f.split('_')[-1].split('.')[0])
                if num > ss_cnt:
                    ss_cnt = num
            except:
                continue
    
    new_image_num = ss_cnt + 1
    
    cropped_face = image[face.top():face.bottom(), face.left():face.right()]
    
    save_path = student_dir / f"img_face_{new_image_num}.jpg"
    
    cv2.imwrite(str(save_path), cv2.cvtColor(cropped_face, cv2.COLOR_BGR2RGB))
    
    return {"status": "success", "message": f"Image {new_image_num} saved successfully!", "image_count": new_image_num}

def clear_all_registered_faces():
    faces_dir = config.DATA_DIR / "data_faces_from_camera"
    if os.path.exists(faces_dir):
        shutil.rmtree(faces_dir)
    
    if os.path.exists(config.FACE_FEATURES_CSV_PATH):
        os.remove(config.FACE_FEATURES_CSV_PATH)

    os.makedirs(faces_dir, exist_ok=True)
    return {"message": "All registered faces and features have been cleared."}

def extract_features_to_csv():
    if not all([detector, predictor, face_reco_model]):
        raise Exception("Dlib models not loaded.")

    path_faces_from_camera = config.DATA_DIR / "data_faces_from_camera"
    student_folders = [f for f in os.listdir(path_faces_from_camera) if os.path.isdir(os.path.join(path_faces_from_camera, f))]

    if not student_folders:
        return {"message": "No face images found to process."}

    features_list = []
    
    for folder in student_folders:
        roll_number = folder.split('_')[0]
        image_files = os.listdir(os.path.join(path_faces_from_camera, folder))

        descriptors = []
        for file in image_files:
            img_path = os.path.join(path_faces_from_camera, folder, file)
            img = cv2.imread(img_path)
            
            faces = detector(img, 1)
            if len(faces) == 1:
                shape = predictor(img, faces[0])
                descriptor = face_reco_model.compute_face_descriptor(img, shape)
                descriptors.append(np.array(descriptor))
        
        if descriptors:
            avg_descriptor = np.mean(descriptors, axis=0)
            row = [roll_number] + list(avg_descriptor)
            features_list.append(row)

    df = pd.DataFrame(features_list)
    df.to_csv(config.FACE_FEATURES_CSV_PATH, header=False, index=False)
    
    return {"message": f"Successfully extracted and saved features for {len(features_list)} students."}

def mark_attendance_dlib(db: Session, subject_name: str, image: np.ndarray):
    if not all([detector, predictor, face_reco_model]):
        raise Exception("Dlib models are not loaded. Cannot perform recognition.")

    subject_obj = db.query(Subject).filter(Subject.subjectName == subject_name).first()
    if not subject_obj:
        return {"error": f"Subject '{subject_name}' not found."}

    faces = detector(image, 1)
    if len(faces) == 0:
        return {"error": "No faces detected in the image."}

    recognized_students = []
    today = date.today()

    for face in faces:
        shape = predictor(image, face)
        face_descriptor = np.array(face_reco_model.compute_face_descriptor(image, shape))

        distances = []
        for known_feature in known_face_features:
            dist = return_euclidean_distance(face_descriptor, known_feature)
            distances.append(dist)
        
        if distances:
            min_dist_idx = np.argmin(distances)
            if distances[min_dist_idx] < 0.6:
                recognized_roll = known_face_roll_numbers[min_dist_idx]
                
                student = db.query(Student).filter(Student.rollNumber == str(recognized_roll)).first()
                if student:
                    existing_record = db.query(AttendanceRecord).filter(
                        and_(
                            AttendanceRecord.studentID == student.studentID,
                            AttendanceRecord.subjectID == subject_obj.subjectID,
                            func.date(AttendanceRecord.timestamp) == today
                        )
                    ).first()

                    if not existing_record:
                        new_record = AttendanceRecord(studentID=student.studentID, subjectID=subject_obj.subjectID)
                        db.add(new_record)
                        recognized_students.append({"name": student.name, "rollNumber": student.rollNumber, "status": "Attendance Marked"})
                    else:
                        recognized_students.append({"name": student.name, "rollNumber": student.rollNumber, "status": "Already Marked Today"})

    db.commit()
    return recognized_students