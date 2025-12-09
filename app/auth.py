from datetime import datetime, timedelta
from typing import Optional
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.db import users

# ⚠️ CHANGE THIS BEFORE PUBLIC USE
SECRET_KEY = "change-this-to-a-long-random-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user(username: str):
    return users.find_one({"username": username})


def create_admin_user(username: str, password: str):
    existing = get_user(username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    users.insert_one({
        "username": username,
        "password": hash_password(password),
        "role": "admin",
        "created_at": datetime.utcnow()
    })

    return {"message": "Admin user created", "username": username}


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

def create_user(username: str, password: str, role: str = "user"):
    existing = get_user(username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    users.insert_one({
        "username": username,
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.utcnow()
    })

    return {"message": "User created", "username": username, "role": role}


def list_users():
    # Don't return password hashes
    cursor = users.find({}, {"_id": 0, "username": 1, "role": 1, "created_at": 1})
    return list(cursor)
    
def get_current_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
