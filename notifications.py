from datetime import datetime, date
from sqlalchemy import select
from database import async_session
from models import Student, Attendance
from twilio_helper import send_sms

# --------------------------
# Morning: auto-mark and notify
# --------------------------
async def morning_absent_routine():

    today = date.today()
    async with async_session() as db:
        # Get all students
        result = await db.execute(select(Student.id, Student.name, Student.phone_number))
        students = result.all()

        for student_id, name, phone in students:
            # Fetch or create attendance
            att_result = await db.execute(
                select(Attendance).where(
                    Attendance.student_id == student_id,
                    Attendance.date == today
                )
            )
            attendance = att_result.scalars().first()
            if not attendance:
                attendance = Attendance(student_id=student_id, date=today)
                db.add(attendance)
                await db.flush()  # Ensure it's added

            # Mark morning absent if not present
            if not attendance.morning_present:
                attendance.morning_present = False
                attendance.morning_time = None

                # Send SMS if phone exists
                if phone:
                    await send_sms(phone, f"{name}, you missed the morning attendance today.")

        await db.commit()
        print(f"✅ Morning auto-mark and notifications done for {len(students)} students.")


# --------------------------
# Evening: auto-mark and notify
# --------------------------
async def evening_absent_routine():
    
    today = date.today()
    async with async_session() as db:
        # Get all students
        result = await db.execute(select(Student.id, Student.name, Student.phone_number))
        students = result.all()

        for student_id, name, phone in students:
            # Fetch or create attendance
            att_result = await db.execute(
                select(Attendance).where(
                    Attendance.student_id == student_id,
                    Attendance.date == today
                )
            )
            attendance = att_result.scalars().first()
            if not attendance:
                attendance = Attendance(student_id=student_id, date=today)
                db.add(attendance)
                await db.flush()

            # Mark evening absent if not present
            if not attendance.evening_present:
                attendance.evening_present = False
                attendance.evening_time = None

                # Send SMS if phone exists
                if phone:
                    await send_sms(phone, f"{name}, you missed the evening attendance today.")

        await db.commit()
        print(f"✅ Evening auto-mark and notifications done for {len(students)} students.")
