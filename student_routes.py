
from fastapi import APIRouter,HTTPException,Depends,Query
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session,get_db
from models import Student,Bus,Attendance
from student_dependancies import is_student
from auth import create_access_token
from schemas import StudentLogin
from bus_location import bus_locations


student_router=APIRouter(
    prefix="/student"
)

@student_router.post("/login")
async def student_login(data: StudentLogin):
    async with async_session() as db:
        result = await db.execute(
            select(Student).where(Student.rfid_id == data.rfid_id, Student.roll_no == data.roll_no)
        )
        student = result.scalars().first()
        if not student:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        # Create JWT token
        token = create_access_token({"student_id": student.id, "name": student.name})

        return {
            "status": "success",
            "student_id": student.id,
            "student_roll_no":student.roll_no,
            "name": student.name,
            "access_token": token,
            "token_type": "bearer"
        }
    

@student_router.get("/all-buses",dependencies=[Depends(is_student)])
async def get_all_buses(db: AsyncSession = Depends(get_db)):
    """
    Returns all buses with their ID, name, and route.
    Accessible only to students.
    """
    result = await db.execute(select(Bus))
    buses = result.scalars().all()
    return [{"bus_id": b.bus_id, "name": b.name, "route": b.route} for b in buses]




@student_router.get("/get-bus-location/{bus_id}",dependencies=[Depends(is_student)])
async def get_bus_live_gps(bus_id: str):
    bus_data = bus_locations.get(bus_id)
    if not bus_data:
        raise HTTPException(status_code=404, detail="Bus not found or no GPS updates yet")
    return {"bus_id": bus_id, "location": bus_data}

@student_router.get("/get=my-attendances")
async def get_my_attendances(
    current_student: Student = Depends(is_student),
    db: AsyncSession = Depends(get_db),
    date_filter: date | None = Query(None),
):
    query = (
        select(Attendance)
        .where(Attendance.student_id == current_student.id)
        .order_by(Attendance.date.desc())
    )

    if date_filter:
        query = query.where(Attendance.date == date_filter)

    result = await db.execute(query)
    return result.scalars().all()
