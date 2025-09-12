import cv2
import os
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import List

from .. import config
from ..models.attendance import Student

def add_student_db(db: Session, roll_number: str, name: str):
    """Checks if a student exists before saving images."""
    db_student = db.query(Student).filter(Student.rollNumber == roll_number).first()
    if not db_student:
        raise HTTPException(status_code=404, detail=f"Student with roll number {roll_number} not found.")
    if db_student.name.lower() != name.lower():
         raise HTTPException(status_code=400, detail=f"Name mismatch for roll number {roll_number}.")
    return db_student

async def save_face_images(roll_number: str, name: str, images: List[UploadFile]):
    """Saves face images from uploaded files for a student."""
    student_dir = config.TRAINING_IMAGE_DIR / f"{roll_number}_{name}"
    os.makedirs(student_dir, exist_ok=True)

    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    sample_num = len(os.listdir(student_dir))

    for image_file in images:
        contents = await image_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = detector.detectMultiScale(gray, 1.3, 5)
        if not np.any(faces): continue

        for (x, y, w, h) in faces:
            sample_num += 1
            cv2.imwrite(str(student_dir / f"img_face_{sample_num}.jpg"), gray[y:y+h, x:x+w])
    
    if sample_num == len(os.listdir(student_dir)): # No new faces were added
        raise HTTPException(status_code=400, detail="No faces could be detected in the uploaded images.")
        
    return {"message": f"Successfully saved new face samples for {name}. Total samples: {sample_num}."}

def train_model():
    """Trains the OpenCV LBPH face recognition model."""
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    faces, ids = get_images_and_labels(config.TRAINING_IMAGE_DIR)
    if not faces or len(set(ids)) < 2:
         raise HTTPException(status_code=400, detail="Training requires face samples from at least two different students.")
    
    recognizer.train(faces, np.array(ids))
    recognizer.save(str(config.TRAINED_MODEL_PATH))

    return {"message": f"Model trained successfully for {len(set(ids))} users."}

def get_images_and_labels(path):
    """Gets images and roll_number from the directory name as the label."""
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    faces, ids = [], []
    
    for image_path in image_paths:
        try:
            roll_number = int(os.path.basename(image_path).split("_")[0])
        except (ValueError, IndexError):
            continue
        
        for file in os.listdir(image_path):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(image_path, file)
                pil_image = Image.open(full_path).convert("L")
                image_np = np.array(pil_image, "uint8")
                faces.append(image_np)
                ids.append(roll_number)
    return faces, ids
# ... (imports) ...

async def save_face_images(roll_number: str, name: str, images: List[UploadFile]):
    """Saves face images from uploaded files for a student."""
    student_dir = config.TRAINING_IMAGE_DIR / f"{roll_number}_{name}"
    os.makedirs(student_dir, exist_ok=True)
    
    # --- TEMPORARY DEBUGGING FOLDER ---
    debug_dir = config.DATA_DIR / "debug_uploads"
    os.makedirs(debug_dir, exist_ok=True)
    # --- END DEBUG ---

    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    sample_num = len(os.listdir(student_dir))
    faces_detected_count = 0

    for i, image_file in enumerate(images):
        contents = await image_file.read()
        
        # --- DEBUG: Save the original file ---
        with open(debug_dir / f"original_{roll_number}_{i}.jpg", "wb") as f:
            f.write(contents)
        # --- END DEBUG ---

        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        if not np.any(faces):
            print(f"DEBUG: No faces found in image {i} for roll number {roll_number}.") # Debug print
            continue

        faces_detected_count += len(faces)
        for (x, y, w, h) in faces:
            sample_num += 1
            cv2.imwrite(str(student_dir / f"img_face_{sample_num}.jpg"), gray[y:y+h, x:x+w])
    
    if faces_detected_count == 0:
        raise HTTPException(status_code=400, detail="No faces could be detected in any of the uploaded images. Please use clearer, well-lit photos.")
        
    return {"message": f"Successfully processed images. Found and saved {faces_detected_count} new face samples for {name}."}