# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Student
from auth import decode_token
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials

# --------------------------
# OAuth2 scheme for Authorization header: "Bearer <token>"
# --------------------------
security=HTTPBearer()

# --------------------------
# Check if token is valid
# --------------------------
async def is_student_authorized(credentials:HTTPAuthorizationCredentials=Depends(security)):
    """
    Verifies if the student access token is valid.
    Returns the payload if valid, otherwise raises HTTPException.
    """
    token=credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or "student_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
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
