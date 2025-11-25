from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import HTTPAuthorizationCredentials
from database import get_db
from models import Admin

from auth import decode_token,security

# --------------------------
# Check if token is valid
# --------------------------
async def is_authorized(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)

    # Invalid token (tampered/modified/not correct signature)
    if payload is None or payload.get("error") == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message":"Token is invalid!",
                "is_expired":False
            }
        )

    # Expired token (valid but expired time)
    if payload.get("error") == "expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message":"Token expired. Please refresh token.",
                "is_expired":True
            }
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    return payload

# --------------------------
# Check if the user is an admin
# --------------------------
async def is_admin(payload: dict = Depends(is_authorized), db: AsyncSession = Depends(get_db)):
    """
    Checks if the user in the JWT payload exists in the Admin table.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    result = await db.execute(select(Admin).where(Admin.user_id == user_id))
    admin = result.scalars().first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    return admin
