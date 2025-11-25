# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Student
from auth import decode_token,security
from fastapi.security import HTTPAuthorizationCredentials

# --------------------------
# Check if token is valid
# --------------------------
async def is_student_authorized(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_token(token)

    # Invalid token (tampered/wrong signature)
    if payload is None or payload.get("error") == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token is invalid!",
                "is_expired": False
            }
        )

    # Expired token
    if payload.get("error") == "expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token expired. Please refresh token.",
                "is_expired": True
            }
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid token type",
                "is_expired": False
            }
        )

    # Check student-specific requirement
    if "student_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Not authorized as a student",
                "is_expired": False
            }
        )

    return payload

# --------------------------
# Get student from DB
# --------------------------
async def is_student(payload: dict = Depends(is_student_authorized), db: AsyncSession = Depends(get_db)):
    """
    Checks if the student in the JWT payload exists in the Student table.
    Returns the Student object.
    """
    student_id = payload["student_id"]

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    return student
