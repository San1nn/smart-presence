import getpass
import sys

# We need to add the project root to the path to allow imports from 'app'
# This is a common pattern for standalone scripts in a project.
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine
from app.models.attendance import Teacher, User  # Import both for the check
from app.services.auth_service import get_password_hash

def add_teacher():
    """
    Command-line script to add a new teacher to the database.
    """
    print("--- Add New Teacher ---")
    
    # Establish a new database session
    db: Session = SessionLocal()
    
    try:
        # --- 1. Get User Input ---
        name = input("Enter teacher's full name: ").strip()
        email = input("Enter teacher's email address: ").strip().lower()
        
        if not name or not email:
            print("\n❌ Error: Name and email cannot be empty.")
            return

        # Use getpass for secure password entry
        password = getpass.getpass("Enter a password for the teacher: ")
        confirm_password = getpass.getpass("Confirm the password: ")

        if not password:
            print("\n❌ Error: Password cannot be empty.")
            return

        if password != confirm_password:
            print("\n❌ Error: Passwords do not match.")
            return

        # --- 2. Check if User Already Exists ---
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\n❌ Error: A user with the email '{email}' already exists.")
            return

        # --- 3. Hash the Password ---
        hashed_password = get_password_hash(password)
        print("\nPassword successfully hashed.")

        # --- 4. Create and Save the New Teacher ---
        print("Creating new teacher record...")
        
        # The 'role' is automatically set to 'teacher' because we are creating
        # a Teacher object, due to SQLAlchemy's polymorphic identity.
        new_teacher = Teacher(
            name=name,
            email=email,
            hashed_password=hashed_password
        )

        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher) # Get the new ID from the DB

        print("\n" + "="*40)
        print("✅ SUCCESS: Teacher added to the database!")
        print(f"   ID: {new_teacher.userID}")
        print(f"   Name: {new_teacher.name}")
        print(f"   Email: {new_teacher.email}")
        print("="*40)

    except Exception as e:
        db.rollback() # Important: Rollback any changes if an error occurs
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        db.close() # Always close the session

if __name__ == "__main__":
    add_teacher()