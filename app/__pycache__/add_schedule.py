import sys
import datetime

sys.path.append('.')

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.attendance import Teacher, Subject, ClassSchedule, DayOfWeek

def add_schedule_entry():
    db: Session = SessionLocal()
    print("--- Add New Class Schedule Entry ---")
    try:
        teacher_email = input("Enter teacher's email to find their subjects: ").strip().lower()
        teacher = db.query(Teacher).filter(Teacher.email == teacher_email).first()
        if not teacher:
            print(f"❌ Error: Teacher with email '{teacher_email}' not found.")
            return

        subject_name = input("Enter the exact name of the subject for this schedule: ").strip()
        subject = db.query(Subject).filter(Subject.teacherID == teacher.userID, Subject.subjectName == subject_name).first()
        if not subject:
            print(f"❌ Error: Subject '{subject_name}' not found for this teacher.")
            return

        day = input("Enter day of the week (e.g., Monday, Tuesday): ").strip().capitalize()
        if day not in [d.value for d in DayOfWeek]:
            print(f"❌ Error: Invalid day. Please use one of: {[d.value for d in DayOfWeek]}")
            return
        
        start_time_str = input("Enter start time (24-hour format, HH:MM): ").strip()
        end_time_str = input("Enter end time (24-hour format, HH:MM): ").strip()
        location = input("Enter location (e.g., Room 404): ").strip()

        start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time()

        new_schedule = ClassSchedule(
            subjectID=subject.subjectID,
            day_of_week=DayOfWeek(day),
            start_time=start_time,
            end_time=end_time,
            location=location
        )
        db.add(new_schedule)
        db.commit()

        print("\n✅ SUCCESS: New schedule entry added!")

    except ValueError:
        print("❌ Error: Invalid time format. Please use HH:MM.")
    finally:
        db.close()

if __name__ == "__main__":
    add_schedule_entry()