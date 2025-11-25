from fastapi import APIRouter,status,HTTPException,Depends
from fastapi.security import HTTPAuthorizationCredentials
from auth import decode_token,create_access_token,security

refresh_router=APIRouter(prefix="/refresh")
@refresh_router.post("/get-new-access-token")
async def refresh_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    refresh_token = credentials.credentials
    payload = decode_token(refresh_token)

    # Invalid token (tampered/wrong signature)
    if payload is None or payload.get("error") == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token is invalid!",
                "is_expired": False
            }
        )

    # Expired refresh token
    if payload.get("error") == "expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token expired. Please login again.",
                "is_expired": True
            }
        )

    # Ensure token type is refresh
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid token type",
                "is_expired": False
            }
        )

    # Remove old type and exp
    user_data = {k: v for k, v in payload.items() if k not in ["type", "exp"]}

    # Create a new access token
    new_access_token = create_access_token(
        user_data
    )

    return {
        "message": "New access token created successfully!",
        "access_token": new_access_token,
        "token_type": "bearer"
    }