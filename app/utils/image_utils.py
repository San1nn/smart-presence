import numpy as np
import cv2
from fastapi import UploadFile

async def to_cv2_image(file: UploadFile) -> np.ndarray:
    """
    Converts a FastAPI UploadFile object to a CV2 image (numpy array).
    """
    # Read the file content into a byte stream
    contents = await file.read()
    
    # Convert byte stream to a numpy array
    nparr = np.frombuffer(contents, np.uint8)
    
    # Decode the numpy array into a CV2 image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    return img