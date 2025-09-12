import sys
from sqlalchemy.orm import Session

# Add project root to the path to allow imports from 'app'
sys.path.append('.')

from app.database.connection import SessionLocal
from app.models.attendance import Teacher, Subject

def assign_subject_to_teacher():
    """
    Command-line script to assign an existing subject to an existing teacher.
    """
    db: Session = SessionLocal()
    print("--- Assign Subject to Teacher ---")

    try:
        # Get Teacher Email
        teacher_email = input("Enter the teacher's email address: ").strip().lower()
        if not teacher_email:
            print("\n❌ Error: Email cannot be empty.")
            return

        # Find the teacher in the database
        teacher = db.query(Teacher).filter(Teacher.email == teacher_email).first()
        if not teacher:
            print(f"\n❌ Error: No teacher found with the email '{teacher_email}'.")
            return
        
        print(f"✅ Found Teacher: {teacher.name} (ID: {teacher.userID})")

        # Get Subject Name
        subject_name = input("Enter the exact name of the subject to assign: ").strip()
        if not subject_name:
            print("\n❌ Error: Subject name cannot be empty.")
            return

        # Find the subject in the database
        subject = db.query(Subject).filter(Subject.subjectName == subject_name).first()
        if not subject:
            print(f"\n❌ Error: No subject found with the name '{subject_name}'.")
            print("Tip: You may need to create the subject first using 'add_subject.py'.")
            return
            
        print(f"✅ Found Subject: {subject.subjectName} (ID: {subject.subjectID})")

        # --- The Assignment Logic ---
        # This updates the teacherID on the subject, creating the link
        subject.teacherID = teacher.userID
        db.commit()

        print("\n" + "="*40)
        print("✅ SUCCESS!")
        print(f"Assigned '{subject.subjectName}' to Teacher '{teacher.name}'.")
        print("="*40)

    except Exception as e:
        db.rollback()
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    assign_subject_to_teacher()