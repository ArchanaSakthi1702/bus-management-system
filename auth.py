from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta,timezone
import jwt
from typing import Optional
import os
import pytz
from fastapi.security import HTTPBearer
from dotenv import load_dotenv  # <-- import dotenv

# --------------------------
# Load environment variables from .env
# --------------------------
load_dotenv()  # <-- loads .env automatically


# Initialize Argon2 hasher
ph = PasswordHasher()

# --------------------------
# Hash password
# --------------------------
def hash_password(password: str) -> str:
    """
    Takes plain password and returns an Argon2 hashed password.
    """
    return ph.hash(password)

# --------------------------
# Verify password
# --------------------------
def verify_password(hashed_password: str, plain_password: str) -> bool:
    """
    Verify a plain password against the hashed password.
    Returns True if matches, False otherwise.
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except exceptions.VerifyMismatchError:
        return False


# --------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))       # 30 days
IST = pytz.timezone("Asia/Kolkata")

# --------------------------
# Create access token
# --------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(IST) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --------------------------
# Create refresh token
# --------------------------
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(IST) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
# --------------------------
# Decode token
# --------------------------
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        return {"error": "expired"}

    except jwt.InvalidTokenError:
        return {"error": "invalid"}


security=HTTPBearer()