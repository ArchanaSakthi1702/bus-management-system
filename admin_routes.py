from fastapi import Depends,status,HTTPException,APIRouter,UploadFile,File,Query
from sqlalchemy.ext.asyncio import AsyncSession
from auth import verify_password,create_access_token,create_refresh_token,hash_password
from sqlalchemy import select,or_
from database import get_db
from schemas import (
    AdminLoginRequest,AdminLoginResponse,AdminCreate,AdminResponse,
    StudentCreate,StudentResponse,StudentUpdate,AttendanceResponse,
    BusCreate,BusResponse,BusUpdate)
from models import Admin,Student,Attendance,Bus
from admin_dependancies import is_admin
import json
from datetime import datetime,date
from times import MORNING_START,MORNING_END,EVENING_END,EVENING_START
from bus_location import bus_locations
import pytz
from sqlalchemy.orm import selectinload



admin_router=APIRouter(prefix="/admin")

@admin_router.post("/login", response_model=AdminLoginResponse)
async def admin_login(login_data: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    # Fetch admin
    result = await db.execute(select(Admin).where(Admin.user_id == login_data.user_id))
    admin = result.scalars().first()

    if not admin or not verify_password(admin.password_hash, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate JWTs
    access_token = create_access_token({"sub": admin.user_id})
    refresh_token = create_refresh_token({"sub": admin.user_id})

    return AdminLoginResponse(access_token=access_token, refresh_token=refresh_token)



# --------------------------
# 1️⃣ Register individual student
# --------------------------
@admin_router.post("/create-student", response_model=StudentResponse,dependencies=[Depends(is_admin)])
async def create_student(student: StudentCreate, db: AsyncSession = Depends(get_db)):
    # Check if roll_no or rfid_id already exists
    existing_student = await db.execute(
        select(Student).where((Student.roll_no == student.roll_no) | (Student.rfid_id == student.rfid_id))
    )
    if existing_student.scalars().first():
        raise HTTPException(status_code=400, detail="Student with same roll_no or RFID already exists")

    new_student = Student(
        name=student.name,
        roll_no=student.roll_no,
        rfid_id=student.rfid_id,
        phone_number=student.phone_number
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student

# --------------------------
# 2️⃣ Register students via JSON file
# --------------------------
@admin_router.post("/upload-json",dependencies=[Depends(is_admin)])
async def upload_students(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    contents = await file.read()
    try:
        students_list = json.loads(contents)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    created_students = []

    for s in students_list:
        # Expecting each JSON object: {"name": "...", "roll_no": "...", "rfid_id": "..."}
        if "name" not in s or "roll_no" not in s or "rfid_id" not in s:
            continue  # skip invalid entries

        # Check duplicates
        existing_student = await db.execute(
            select(Student).where((Student.roll_no == s["roll_no"]) | (Student.rfid_id == s["rfid_id"]))
        )
        if existing_student.scalars().first():
            continue  # skip duplicates

        new_student = Student(
            name=s["name"],
            roll_no=s["roll_no"],
            rfid_id=s["rfid_id"],
            phone_number=s.get("phone_number",None)

        )
        db.add(new_student)
        await db.flush()  # flush to get IDs without commit
        created_students.append(new_student)

    await db.commit()

    return {"created": len(created_students), "students": [s.id for s in created_students]}

# --------------------------
# Mark attendance
@admin_router.post("/mark-attendance/{rfid_id}")
async def mark_attendance(
    rfid_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Fetch student by RFID
    result = await db.execute(select(Student).where(Student.rfid_id == rfid_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # IST Timezone
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    today = now.date()
    current_time = now.time()
    print("IST current time:", current_time)

    # Fetch or create attendance record
    result = await db.execute(
        select(Attendance).where(Attendance.student_id == student.id, Attendance.date == today)
    )
    attendance = result.scalars().first()

    if not attendance:
        attendance = Attendance(student_id=student.id, date=today)
        db.add(attendance)
        await db.flush()

    # Morning attendance
    if MORNING_START <= current_time <= MORNING_END:
        if attendance.morning_present:
            raise HTTPException(status_code=400, detail="Morning attendance already marked")

        attendance.morning_time = now
        attendance.morning_present = True
        await db.commit()
        await db.refresh(attendance)
        return {"message": "Morning attendance marked", "time": now}

    # Evening attendance
    elif EVENING_START <= current_time <= EVENING_END:
        if attendance.evening_present:
            raise HTTPException(status_code=400, detail="Evening attendance already marked")

        attendance.evening_time = now
        attendance.evening_present = True
        await db.commit()
        await db.refresh(attendance)
        return {"message": "Evening attendance marked", "time": now}

    else:
        raise HTTPException(status_code=400, detail="Attendance cannot be marked at this time")


# --------------------------
# 1️⃣ Admin CRUD
# --------------------------

@admin_router.post("/create-admin", response_model=AdminResponse, dependencies=[Depends(is_admin)])
async def create_admin(admin_data: AdminCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    existing = await db.execute(select(Admin).where(Admin.user_id == admin_data.user_id))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Admin already exists")

    admin = Admin(user_id=admin_data.user_id, password_hash=hash_password(admin_data.password))
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@admin_router.get("/list-admins", response_model=list[AdminResponse], dependencies=[Depends(is_admin)])
async def list_admins(db: AsyncSession = Depends(get_db), search: str | None = Query(None)):
    query = select(Admin)
    if search:
        query = select(Admin).where(Admin.user_id.ilike(f"%{search}%"))
    result = await db.execute(query)
    return result.scalars().all()


@admin_router.delete("/delete-admin/{user_id}", status_code=204, dependencies=[Depends(is_admin)])
async def delete_admin(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.user_id == user_id))
    admin = result.scalars().first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    await db.delete(admin)
    await db.commit()
    return


# --------------------------
# 2️⃣ Student CRUD + Search
# --------------------------

@admin_router.get("/list-students", response_model=list[StudentResponse], dependencies=[Depends(is_admin)])
async def list_students(
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(None),
):
    query = select(Student)
    if search:
        query = select(Student).where(
            or_(
                Student.name.ilike(f"%{search}%"),
                Student.roll_no.ilike(f"%{search}%"),
                Student.rfid_id.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@admin_router.get("/get-student/{student_id}", response_model=StudentResponse, dependencies=[Depends(is_admin)])
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@admin_router.patch("/update-student/{student_id}", response_model=StudentResponse, dependencies=[Depends(is_admin)])
async def update_student(student_id: int, student_data: StudentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Only update fields that are provided
    if student_data.name is not None:
        student.name = student_data.name

    if student_data.roll_no is not None:
        student.roll_no = student_data.roll_no

    if student_data.rfid_id is not None:
        student.rfid_id = student_data.rfid_id

    if student_data.phone_number is not None:
        student.phone_number = student_data.phone_number

    await db.commit()
    await db.refresh(student)
    return student



@admin_router.delete("/delete-student/{student_id}", status_code=204, dependencies=[Depends(is_admin)])
async def delete_student(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await db.delete(student)
    await db.commit()
    return {
        "message":"Student Deleted Successfully"
    }


# --------------------------
# 3️⃣ Attendance CRUD + Search
# --------------------------

@admin_router.get("/list-attendances", response_model=list[AttendanceResponse], dependencies=[Depends(is_admin)])
async def list_attendance(
    db: AsyncSession = Depends(get_db),
    student_name: str | None = Query(None),
    date_filter: date | None = Query(None),
):
    query = (
        select(Attendance)
        .join(Student)
        .options(selectinload(Attendance.student))
    )

    if student_name:
        query = query.where(Student.name.ilike(f"%{student_name}%"))
    
    if date_filter:
        query = query.where(Attendance.date == date_filter)

    result = await db.execute(query)
    attendances = result.scalars().all()

    # Return mapped list
    return [
        AttendanceResponse(
            id=a.id,
            student_id=a.student_id,
            student_name=a.student.name,
            date=a.date,
            morning_present=a.morning_present,
            morning_time=a.morning_time,
            evening_present=a.evening_present,
            evening_time=a.evening_time,
        )
        for a in attendances
    ]



@admin_router.get("/get-student-attendance/{attendance_id}", response_model=AttendanceResponse, dependencies=[Depends(is_admin)])
async def get_attendance(attendance_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Attendance)
        .where(Attendance.id == attendance_id)
        .options(selectinload(Attendance.student))
    )
    result = await db.execute(query)
    att = result.scalars().first()

    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    return AttendanceResponse(
        id=att.id,
        student_id=att.student_id,
        student_name=att.student.name,
        date=att.date,
        morning_present=att.morning_present,
        morning_time=att.morning_time,
        evening_present=att.evening_present,
        evening_time=att.evening_time,
    )


@admin_router.patch("/update-student-attendance/{attendance_id}", response_model=AttendanceResponse, dependencies=[Depends(is_admin)])
async def update_attendance(
    attendance_id: int, 
    db: AsyncSession = Depends(get_db),
    morning_present: bool | None = None, 
    evening_present: bool | None = None
):
    query = (
        select(Attendance)
        .where(Attendance.id == attendance_id)
        .options(selectinload(Attendance.student))
    )
    result = await db.execute(query)
    att = result.scalars().first()

    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    if morning_present is not None:
        att.morning_present = morning_present
        att.morning_time = now if morning_present else None

    if evening_present is not None:
        att.evening_present = evening_present
        att.evening_time = now if evening_present else None

    await db.commit()
    await db.refresh(att)

    return AttendanceResponse(
        id=att.id,
        student_id=att.student_id,
        student_name=att.student.name,
        date=att.date,
        morning_present=att.morning_present,
        morning_time=att.morning_time,
        evening_present=att.evening_present,
        evening_time=att.evening_time,
    )


@admin_router.delete("/delete-attendance/{attendance_id}", status_code=204, dependencies=[Depends(is_admin)])
async def delete_attendance(attendance_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    att = result.scalars().first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    await db.delete(att)
    await db.commit()
    return



@admin_router.post("/create-bus", response_model=BusResponse, dependencies=[Depends(is_admin)])
async def create_bus(bus: BusCreate, db: AsyncSession = Depends(get_db)):
    # Check if bus_id already exists
    result = await db.execute(select(Bus).where(Bus.bus_id == bus.bus_id))
    existing_bus = result.scalars().first()
    if existing_bus:
        raise HTTPException(status_code=400, detail="Bus with this bus_id already exists")

    new_bus = Bus(
        bus_id=bus.bus_id,
        name=bus.name,
        route=bus.route
    )
    db.add(new_bus)
    await db.commit()
    await db.refresh(new_bus)
    return new_bus



@admin_router.put("/update-bus/{bus_id}", response_model=BusResponse, dependencies=[Depends(is_admin)])
async def update_bus(bus_id: str, bus: BusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bus).where(Bus.bus_id == bus_id))
    existing_bus = result.scalars().first()

    if not existing_bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    if bus.name is not None:
        existing_bus.name = bus.name
    
    if bus.route is not None:
        existing_bus.route = bus.route

    await db.commit()
    await db.refresh(existing_bus)
    return existing_bus



@admin_router.delete("/delete-bus/{bus_id}", dependencies=[Depends(is_admin)])
async def delete_bus(bus_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bus).where(Bus.bus_id == bus_id))
    bus = result.scalars().first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    await db.delete(bus)
    await db.commit()
    return {"status": "success", "message": "Bus deleted successfully", "bus_id": bus_id}



@admin_router.get("/list-buses", response_model=list[BusResponse], dependencies=[Depends(is_admin)])
async def get_all_buses_admin(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bus))
    return result.scalars().all()



@admin_router.get("/get-bus/{bus_id}", response_model=BusResponse, dependencies=[Depends(is_admin)])
async def get_bus(bus_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bus).where(Bus.bus_id == bus_id))
    bus = result.scalars().first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    return bus



@admin_router.get("/get-bus-location/{bus_id}", dependencies=[Depends(is_admin)])
async def admin_get_bus_live_gps(bus_id: str):
    bus_data = bus_locations.get(bus_id)
    if not bus_data:
        raise HTTPException(status_code=404, detail="Bus not found or no GPS updates yet")
    return {"bus_id": bus_id, "location": bus_data}
