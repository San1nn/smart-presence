from pathlib import Path

# Define the base directory of the project (e.g., /smart_presence-main)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- FIX: Define the data directory INSIDE the project base directory ---
# This is a more robust and portable project structure.
# The app will now look for a folder named 'data' at the same level as your 'app' folder.
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Path to the Haar Cascade file for face detection
HAAR_CASCADE_PATH = DATA_DIR / "haarcascade_frontalface_default.xml"

# Directory to save training images of students
TRAINING_IMAGE_DIR = DATA_DIR / "TrainingImage"
TRAINING_IMAGE_DIR.mkdir(exist_ok=True)

# Directory and path for the trained model file
TRAINED_MODEL_DIR = DATA_DIR / "TrainingImageLabel"
TRAINED_MODEL_DIR.mkdir(exist_ok=True)
TRAINED_MODEL_PATH = TRAINED_MODEL_DIR / "Trainner.yml"

# New MySQL Database URL
DATABASE_URL = "mysql+pymysql://root:@localhost/smart_presence"


# Confidence threshold for face recognition.
RECOGNITION_CONFIDENCE_THRESHOLD = 70.0