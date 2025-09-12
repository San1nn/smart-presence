import sys
from sqlalchemy.orm import Session

# Add the project's root directory to the Python path
# to allow importing from the 'app' package
sys.path.append('.')

from app.database.connection import SessionLocal
from app.models.attendance import Subject

def add_subject():
    """
    A command-line utility to add a new subject to the database.
    """
    print("--- Add New Subject/Class ---")
    
    # Establish a connection to the database
    db: Session = SessionLocal()
    
    try:
        # --- 1. Get Subject Details ---
        name = input("Enter the subject name (e.g., 'Computer Science 101'): ").strip()
        description = input("Enter a brief description for the subject: ").strip()

        if not name:
            print("\n❌ Error: Subject name cannot be empty.")
            return

        # --- 2. Check if a subject with that name already exists ---
        existing_subject = db.query(Subject).filter(Subject.subjectName == name).first()
        if existing_subject:
            print(f"\n❌ Error: A subject with the name '{name}' already exists in the database.")
            return

        # --- 3. Create and Save the New Subject ---
        print("\nCreating new subject record...")
        
        new_subject = Subject(
            subjectName=name,
            description=description
        )

        db.add(new_subject)
        db.commit()
        db.refresh(new_subject) # Refresh to get the auto-generated subjectID

        print("\n" + "="*40)
        print("✅ SUCCESS: Subject added to the database!")
        print(f"   Subject ID: {new_subject.subjectID}")
        print(f"   Name:       {new_subject.subjectName}")
        print(f"   Description:{new_subject.description}")
        print("="*40)
        print("\nNext, you can assign this subject to a teacher using the 'assign_subject.py' script.")

    except Exception as e:
        db.rollback() # Roll back any changes if an error occurs
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        db.close() # Always close the database session

if __name__ == "__main__":
    add_subject()