from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# OpenCV paths
HAAR_CASCADE_PATH = DATA_DIR / "haarcascade_frontalface_default.xml"
TRAINING_IMAGE_DIR = DATA_DIR / "TrainingImage"
TRAINING_IMAGE_DIR.mkdir(exist_ok=True)
TRAINED_MODEL_DIR = DATA_DIR / "TrainingImageLabel"
TRAINED_MODEL_DIR.mkdir(exist_ok=True)
TRAINED_MODEL_PATH = TRAINED_MODEL_DIR / "Trainner.yml"

# Database URL
DATABASE_URL = "mysql+pymysql://root:root@localhost/smart_presence"

# Recognition confidence
RECOGNITION_CONFIDENCE_THRESHOLD = 70.0

# --- REMOVED DLIB PATHS ---