import cv2
import os
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import List
import base64

from .. import config
from ..models.attendance import Student

def add_student_db(db: Session, roll_number: str, name: str):
    """
    Checks if a student with the given roll number exists.
    This function is now simpler as registration is handled by the auth route.
    It's mainly for validating that the student exists before saving images.
    """
    db_student = db.query(Student).filter(Student.rollNumber == roll_number).first()
    if not db_student:
        raise HTTPException(
            status_code=404, 
            detail=f"Student with roll number {roll_number} not found. Please register the student first."
        )
    
    # --- FIX: Make the name comparison case-insensitive ---
    if db_student.name.lower() != name.lower():
         raise HTTPException(
            status_code=400, 
            detail=f"Name mismatch. Roll number {roll_number} is registered to '{db_student.name}', not '{name}'."
        )
    return db_student

async def save_face_images_from_base64(roll_number: str, name: str, base64_images: List[str]):
    student_dir = config.TRAINING_IMAGE_DIR / f"{roll_number}_{name}"
    os.makedirs(student_dir, exist_ok=True)

    detector = cv2.CascadeClassifier(str(config.HAAR_CASCADE_PATH))
    sample_num = 0

    for b64_string in base64_images:
        try:
            header, encoded = b64_string.split(",", 1)
            image_data = base64.b64decode(encoded)
        except (ValueError, TypeError):
            continue 
        
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = detector.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            continue

        for (x, y, w, h) in faces:
            sample_num += 1
            cv2.imwrite(
                str(student_dir / f"{name}_{roll_number}_{sample_num}.jpg"),
                gray[y:y+h, x:x+w],
            )
    
    if sample_num == 0:
        raise HTTPException(status_code=400, detail="No faces could be detected in the captured images.")
        
    return {"message": f"{sample_num} face samples saved for {name} ({roll_number}). Ready for training."}


def train_model():
    """Trains the LBPH face recognition model."""
    if not os.path.exists(config.HAAR_CASCADE_PATH):
        raise HTTPException(status_code=500, detail="Haar Cascade file not found.")
        
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    try:
        faces, ids = get_images_and_labels(config.TRAINING_IMAGE_DIR)
        
        if not faces:
             raise HTTPException(status_code=400, detail="No training data found. Please register faces for students first.")
        
        # --- FIX: Validate that there are at least two different people to train on ---
        unique_ids = set(ids)
        if len(unique_ids) < 2:
            raise HTTPException(
                status_code=400, 
                detail=f"Training requires face samples from at least two different students. Please register more students."
            )
        
        recognizer.train(faces, np.array(ids))
        recognizer.save(str(config.TRAINED_MODEL_PATH))

    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        # Catch any other unexpected errors during training
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during model training: {e}")

    return {"message": f"Model trained successfully for {len(unique_ids)} users."}


def get_images_and_labels(path):
    """Gets images and uses the roll_number from the directory name as the label."""
    # Get all subdirectories in the training path (e.g., '1_John', '2_Jane')
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    faces = []
    ids = []
    
    for image_path in image_paths:
        # Get all image files within the subdirectory
        files = [f for f in os.listdir(image_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        for file in files:
            full_path = os.path.join(image_path, file)
            pil_image = Image.open(full_path).convert("L") # Convert to grayscale
            image_np = np.array(pil_image, "uint8")
            
            # Extract roll number from directory name: "123_JohnDoe" -> "123"
            try:
                roll_number_str = os.path.basename(image_path).split("_")[0]
                ids.append(int(roll_number_str))
                faces.append(image_np)
            except (ValueError, IndexError):
                # This handles cases where a directory might be named incorrectly
                print(f"Warning: Could not parse ID from directory '{image_path}'. Skipping.")
                continue
    return faces, ids