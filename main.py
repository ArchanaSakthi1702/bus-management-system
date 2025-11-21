# main.py

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from database import engine, Base
from models import Admin, Student, Attendance,Bus
from admin_routes import admin_router
from student_routes import student_router
from bus_location import bus_locations,gps_router
from notifications import evening_absent_routine,morning_absent_routine
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from times import (
    MORNING_NOTIFY_HOUR,
    MORNING_NOTIFY_MINUTE,
    EVENING_NOTIFY_MINUTE,
    EVENING_NOTIFY_HOUR
                   )



async def clear_bus_locations():
    bus_locations.clear()
    print(f"✅ Cleared all bus locations at {datetime.now()}")


# --------------------------
# Lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")

    # --------------------------
    # Start APScheduler
    scheduler = AsyncIOScheduler()

    scheduler.add_job(morning_absent_routine, "cron", hour=MORNING_NOTIFY_HOUR, minute=MORNING_NOTIFY_MINUTE)
    scheduler.add_job(evening_absent_routine, "cron", hour=EVENING_NOTIFY_HOUR, minute=EVENING_NOTIFY_MINUTE)
    scheduler.add_job(clear_bus_locations,"cron",hour=23,minute=59)

    scheduler.start()
    print("⏰ Scheduler started")

    yield  # App runs here

    # Shutdown logic
    scheduler.shutdown()
    await engine.dispose()
    print("🔒 Database connection closed")



# --------------------------
# FastAPI app with lifespan
app = FastAPI(
    title="Bus Attendance System",
    lifespan=lifespan
)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "*",  # Optional: allow all origins (for development)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(student_router)
app.include_router(gps_router)
# --------------------------
# Example route
@app.get("/")
async def root():
    return {"message": "Bus Attendance System running!"}



