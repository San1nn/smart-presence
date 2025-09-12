from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from ..database.connection import get_db
from ..services import face_rec_service # Use the OpenCV service
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"]
)

@router.get("/students-for-registration")
def get_students_for_registration(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'teacher': raise HTTPException(status_code=403, detail="Not authorized.")
    students = db.query(Student).order_by(Student.name).all()
    return [{"roll_number": s.rollNumber, "name": s.name} for s in students]

@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})

@router.post("/register-faces")
async def register_student_faces(
    roll_number: str = Form(...),
    name: str = Form(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    if current_user.role.value != 'teacher': raise HTTPException(status_code=403, detail="Not authorized.")
    face_rec_service.add_student_db(db=db, roll_number=roll_number, name=name)
    return await face_rec_service.save_face_images(roll_number=roll_number, name=name, images=images)

@router.post("/train")
def train_model_endpoint(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'teacher': raise HTTPException(status_code=403, detail="Not authorized.")
    return face_rec_service.train_model()# ... (imports) ...

# In the get_face_recognition_page function:
@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    # Change this to point to the correct, simpler template
    return templates.TemplateResponse("teacher/face_registration.html", {"request": request})

# ... (rest of the file remains the same)
# The @router.post("/register-faces") function is already correct for this form.
# ... (all imports) ...

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"]
)

# ... (keep the /students-for-registration route) ...

@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    # This route now serves our new webcam capture page
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})

# The POST route for /register-faces and /train require NO CHANGES.
# They are already set up perfectly for what the new frontend sends.
# ... (rest of the file) ...
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from ..database.connection import get_db
from ..services import face_rec_service
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"]
)

# --- ADD THIS ENTIRE FUNCTION ---
@router.get("/students-for-registration")
def get_students_for_registration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Gets a list of all registered students to populate the registration form's dropdown.
    """
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    students = db.query(Student).order_by(Student.name).all()
    
    # Return a list of dictionaries with the student's name and roll number
    return [{"roll_number": s.rollNumber, "name": s.name} for s in students]
# --- END OF FUNCTION TO ADD ---


@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})


# ... (rest of the file with /register-faces and /train routes) ...
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from ..database.connection import get_db
from ..services import face_rec_service # Make sure this is using the OpenCV service
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"]
)

@router.get("/students-for-registration")
def get_students_for_registration(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'teacher': raise HTTPException(status_code=403, detail="Not authorized.")
    students = db.query(Student).order_by(Student.name).all()
    return [{"roll_number": s.rollNumber, "name": s.name} for s in students]

@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})

# --- ADD THIS ENTIRE FUNCTION ---
@router.post("/register-faces")
async def register_student_faces(
    roll_number: str = Form(...),
    name: str = Form(...),
    images: List[UploadFile] = File(...), # Expects a list of files
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Receives student details and a list of face images,
    then saves them using the face recognition service.
    """
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized.")

    # First, validate that the student exists
    face_rec_service.add_student_db(db=db, roll_number=roll_number, name=name)
    
    # Then, save the images
    return await face_rec_service.save_face_images(
        roll_number=roll_number, 
        name=name, 
        images=images
    )
# --- END OF FUNCTION TO ADD ---


@router.post("/train")
def train_model_endpoint(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized.")
    return face_rec_service.train_model()
# ... (all imports) ...

@router.post("/register-faces")
async def register_student_faces(
    roll_number: str = Form(...),
    name: str = Form(...),
    images: List[UploadFile] = File(...), # This handles both webcam and file uploads
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Receives student details and a list of face images,
    then saves them using the face recognition service.
    """
    if current_user.role.value != 'teacher':
        raise HTTPException(status_code=403, detail="Not authorized.")

    face_rec_service.add_student_db(db=db, roll_number=roll_number, name=name)
    
    return await face_rec_service.save_face_images(
        roll_number=roll_number, 
        name=name, 
        images=images
    )
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from ..database.connection import get_db
from ..services import face_rec_service # Point back to the OpenCV service
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/face-recognition", tags=["Face Recognition"])

@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})

@router.get("/students-for-registration", response_class=HTMLResponse)
def get_students_for_registration(db: Session = Depends(get_db)):
    students = db.query(Student).order_by(Student.name).all()
    return [{"roll_number": s.rollNumber, "name": s.name} for s in students]

@router.post("/register-faces")
async def register_student_faces(
    roll_number: str = Form(...), name: str = Form(...),
    images: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    face_rec_service.add_student_db(db=db, roll_number=roll_number, name=name)
    return await face_rec_service.save_face_images(roll_number, name, images)

@router.post("/train")
def train_model_endpoint():
    return face_rec_service.train_model()
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from ..database.connection import get_db
from ..services import face_rec_service
from ..services.auth_service import get_current_user_from_cookie
from ..models.attendance import User, Student

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/face-recognition", tags=["Face Recognition"])


@router.get("/recognize", response_class=HTMLResponse)
async def get_face_recognition_page(request: Request):
    return templates.TemplateResponse("teacher/face_recognition.html", {"request": request})


# --- FIX: Change the function to be async ---
@router.get("/students-for-registration")
async def get_students_for_registration(db: Session = Depends(get_db)):
    """
    Gets a list of all registered students. FastAPI will automatically
    convert the returned list into a proper JSON response.
    """
    students = db.query(Student).order_by(Student.name).all()
    return [{"roll_number": s.rollNumber, "name": s.name} for s in students]
# --- END OF FIX ---


@router.post("/register-faces")
async def register_student_faces(
    roll_number: str = Form(...), name: str = Form(...),
    images: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    face_rec_service.add_student_db(db=db, roll_number=roll_number, name=name)
    return await face_rec_service.save_face_images(roll_number, name, images)


@router.post("/train")
def train_model_endpoint():
    return face_rec_service.train_model()
