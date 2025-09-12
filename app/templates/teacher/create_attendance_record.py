import sys
from sqlalchemy.orm import Session

# Add project root to the path
sys.path.append('.')

from app.database.connection import SessionLocal
from app.models.attendance import Subject, Student, AttendanceRecord

def create_manual_attendance():
    """
    Command-line script to manually create a single attendance record
    for a student in a specific subject. This is a utility script
    to generate the data needed for the 'Class Details' page to work.
    """
    db: Session = SessionLocal()
    print("--- Create Manual Attendance Record ---")

    try:
        # 1. Get Student Roll Number
        student_roll = input("Enter the Roll Number of the student to mark present: ").strip()
        student = db.query(Student).filter(Student.rollNumber == student_roll).first()
        if not student:
            print(f"\n❌ Error: No student found with Roll Number '{student_roll}'.")
            return
        print(f"✅ Found Student: {student.name}")

        # 2. Get Subject Name
        subject_name = input(f"Enter the exact Subject Name to mark attendance for (e.g., 'Computer Science 101'): ").strip()
        subject = db.query(Subject).filter(Subject.subjectName == subject_name).first()
        if not subject:
            print(f"\n❌ Error: No subject found with the name '{subject_name}'.")
            return
        print(f"✅ Found Subject: {subject.subjectName}")

        # 3. Check for existing record to avoid duplicates for this utility
        existing_record = db.query(AttendanceRecord).filter(
            AttendanceRecord.studentID == student.studentID,
            AttendanceRecord.subjectID == subject.subjectID
        ).first()

        if existing_record:
            print(f"\nℹ️ Info: An attendance record already exists for {student.name} in {subject.name}.")
            return

        # 4. Create and save the new attendance record
        new_record = AttendanceRecord(
            studentID=student.studentID,
            subjectID=subject.subjectID,
            isPresent="True" # Mark as present
        )
        db.add(new_record)
        db.commit()

        print("\n" + "="*40)
        print("✅ SUCCESS!")
        print(f"Manually marked '{student.name}' as present in '{subject.subjectName}'.")
        print("You can now view this student on the 'Class Details' page.")
        print("="*40)

    except Exception as e:
        db.rollback()
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_manual_attendance()