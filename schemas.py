from pydantic import BaseModel
from typing import Optional
from datetime import datetime,date




class AdminLoginRequest(BaseModel):
    user_id: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"




# --------------------------
# Admin Schemas
# --------------------------

class AdminCreate(BaseModel):
    user_id: str
    password: str

class AdminResponse(BaseModel):
    user_id: str

    class Config:
        from_attributes = True


# --------------------------
# Student Schemas
# --------------------------


class StudentCreate(BaseModel):
    name: str
    roll_no: str
    rfid_id: str
    phone_number:Optional[str]=None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    roll_no: Optional[str] = None
    rfid_id: Optional[str] = None
    phone_number: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    name: str
    roll_no: str
    rfid_id: str
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


# --------------------------
# Attendance Schemas
# --------------------------

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    student_name:str
    date: date
    morning_present: bool
    morning_time: Optional[datetime] = None
    evening_present: bool
    evening_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceUpdateRequest(BaseModel):
    morning_present: Optional[bool] = None
    evening_present: Optional[bool] = None



# ---------------------------
# Student login model
# ---------------------------
class StudentLogin(BaseModel):
    rfid_id: str
    roll_no: str



# ---------------------------
# Request model from buses
# ---------------------------
class GPSUpdate(BaseModel):
    bus_id: str
    latitude: float
    longitude: float
    timestamp: Optional[datetime]=None



class BusCreate(BaseModel):
    bus_id: str
    name: str | None = None
    route: str | None = None

class BusUpdate(BaseModel):
    name: str | None = None
    route: str | None = None

class BusResponse(BaseModel):
    id: int
    bus_id: str
    name: str | None
    route: str | None

    class Config:
        from_attributes = True
