from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Admin
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from auth import decode_token

# --------------------------
# OAuth2 scheme for Authorization header: "Bearer <token>"
# --------------------------
security = HTTPBearer()

# --------------------------
# Check if token is valid
# --------------------------
async def is_authorized(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies if the access token is valid.
    Returns the payload if valid, otherwise raises HTTPException.
    """
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
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
