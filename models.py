# models.py

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, UniqueConstraint,Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# -----------------------
# Admin Table
# -----------------------

class Admin(Base):
    __tablename__ = "admins"

    user_id = Column(String, primary_key=True, index=True)  # Now string ID
    password_hash = Column(String, nullable=False)

# Student Table
# -----------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_no = Column(String, nullable=False, unique=True)
    rfid_id = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=True)  # <-- New column

    # Relationship to attendance table
    attendances = relationship("Attendance", back_populates="student")


# -----------------------
# Attendance Table
# -----------------------
class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False, server_default=func.current_date())

    # Morning attendance
    morning_time = Column(DateTime, nullable=True)
    morning_present = Column(Boolean, nullable=False, default=False)

    # Evening attendance
    evening_time = Column(DateTime, nullable=True)
    evening_present = Column(Boolean, nullable=False, default=False)

    # Relationship back to student
    student = relationship("Student", back_populates="attendances")

    __table_args__ = (
        # Ensures only one attendance record per student per day
        UniqueConstraint('student_id', 'date', name='uix_student_date'),
    )



# -----------------------
# Bus Table
# -----------------------
class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(String, nullable=False, unique=True)   # GPS device ID
    name = Column(String, nullable=True)                  # Optional bus name
    route = Column(String, nullable=True)                 # Optional route description
