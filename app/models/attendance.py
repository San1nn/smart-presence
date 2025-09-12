from sqlalchemy import (Column, Integer, String, DateTime, Time, Date, Text, Float, ForeignKey, 
                        Enum as SQLAlchemyEnum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.connection import Base # <-- 'Base' is imported here
import enum

# --- Enums should be defined first ---
class DayOfWeek(str, enum.Enum):
    Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"

class UserRole(str, enum.Enum):
    student, teacher, admin = "student", "teacher", "admin"


# --- Core User Models ---
class User(Base):
    __tablename__ = "user"
    userID = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    __mapper_args__ = {"polymorphic_identity": "user", "polymorphic_on": role}

class Student(User):
    __tablename__ = "student"
    studentID = Column(Integer, ForeignKey("user.userID"), primary_key=True)
    rollNumber = Column(String(30), unique=True, index=True, nullable=False)
    student_class = Column("class", String(30))
    attendances = relationship("AttendanceRecord", back_populates="student")
    __mapper_args__ = {"polymorphic_identity": UserRole.student}

class Teacher(User):
    __tablename__ = "teacher"
    teacherID = Column(Integer, ForeignKey("user.userID"), primary_key=True)
    subjects_taught = relationship("Subject", back_populates="teacher")
    __mapper_args__ = {"polymorphic_identity": UserRole.teacher}

class Admin(User):
    __tablename__ = "admin"
    adminID = Column(Integer, ForeignKey("user.userID"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": UserRole.admin}


# --- Academic and Attendance Models ---
class Subject(Base):
    __tablename__ = "subject"
    subjectID = Column(Integer, primary_key=True, index=True)
    subjectName = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    teacherID = Column(Integer, ForeignKey("user.userID"))
    teacher = relationship("Teacher", back_populates="subjects_taught")
    attendance_records = relationship("AttendanceRecord", back_populates="subject", cascade="all, delete-orphan")
    schedules = relationship("ClassSchedule", back_populates="subject", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    __tablename__ = "attendance_record"
    recordID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("student.studentID"), nullable=False)
    subjectID = Column(Integer, ForeignKey("subject.subjectID"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    isPresent = Column(String(255), default='True')
    student = relationship("Student", back_populates="attendances")
    subject = relationship("Subject", back_populates="attendance_records")

class ClassSchedule(Base):
    __tablename__ = "class_schedule"
    scheduleID = Column(Integer, primary_key=True, index=True)
    subjectID = Column(Integer, ForeignKey("subject.subjectID"), nullable=False)
    day_of_week = Column(SQLAlchemyEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String(100), default="N/A")
    subject = relationship("Subject", back_populates="schedules")


# --- NEW Student Portal Models ---
class Notification(Base):
    __tablename__ = "notification"
    notificationID = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Assignment(Base):
    __tablename__ = "assignment"
    assignmentID = Column(Integer, primary_key=True, index=True)
    subjectID = Column(Integer, ForeignKey("subject.subjectID"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True))
    subject = relationship("Subject", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submission"
    submissionID = Column(Integer, primary_key=True, index=True)
    assignmentID = Column(Integer, ForeignKey("assignment.assignmentID"), nullable=False)
    studentID = Column(Integer, ForeignKey("student.studentID"), nullable=False)
    file_path = Column(String(255))
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    grade = Column(String(20))
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student")

class LeaveApplication(Base):
    __tablename__ = "leave_application"
    leaveID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("student.studentID"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="Pending")
    student = relationship("Student")

class FeeRecord(Base):
    __tablename__ = "fee_record"
    feeID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("student.studentID"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    transaction_id = Column(String(255))
    description = Column(String(255))
    student = relationship("Student")