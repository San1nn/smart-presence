from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, 
                        Enum as SQLAlchemyEnum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.connection import Base
import enum

# --- FIX: ADD 'admin' to UserRole ENUM ---
class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class User(Base):
    __tablename__ = "user"

    userID = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": role,
    }

class Student(User):
    __tablename__ = "student"
    studentID = Column(Integer, ForeignKey("user.userID"), primary_key=True)
    rollNumber = Column(String(30), unique=True, index=True, nullable=False)
    student_class = Column("class", String(30))

    attendances = relationship("AttendanceRecord", back_populates="student")

    __mapper_args__ = {
        "polymorphic_identity": UserRole.student,
    }

class Teacher(User):
    __tablename__ = "teacher"
    teacherID = Column(Integer, ForeignKey("user.userID"), primary_key=True)

    subjects_taught = relationship("Subject", back_populates="teacher")
    
    __mapper_args__ = {
        "polymorphic_identity": UserRole.teacher,
    }

# --- NEW: ADD THE ADMIN MODEL ---
class Admin(User):
    __tablename__ = "admin"
    adminID = Column(Integer, ForeignKey("user.userID"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": UserRole.admin,
    }

class Subject(Base):
    __tablename__ = "subject"
    subjectID = Column(Integer, primary_key=True, index=True)
    subjectName = Column(String(30), nullable=False, index=True)
    description = Column(String(255))
    teacherID = Column(Integer, ForeignKey("user.userID"))

    teacher = relationship("Teacher", back_populates="subjects_taught")
    attendance_records = relationship("AttendanceRecord", back_populates="subject")

class AttendanceRecord(Base):
    __tablename__ = "attendance_record"
    recordID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("student.studentID"), nullable=False)
    subjectID = Column(Integer, ForeignKey("subject.subjectID"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    isPresent = Column(String(255), default=True)

    student = relationship("Student", back_populates="attendances")
    subject = relationship("Subject", back_populates="attendance_records")