"""
OAuth Authentication Module
Supports Google and GitHub OAuth 2.0
"""
from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

from app.db import users, audit_logs

# Load environment variables
load_dotenv()

# OAuth Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
OAUTH_CALLBACK_BASE_URL = os.getenv("OAUTH_CALLBACK_BASE_URL", "http://localhost:8000")

# Initialize OAuth
oauth = OAuth()

# Register Google OAuth
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

# Register GitHub OAuth
if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name='github',
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )

security = HTTPBearer()

# ==================== JWT Token Management ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

# ==================== User Management ====================

def get_user_by_email(email: str):
    """Get user by email"""
    return users.find_one({"email": email})

def get_or_create_user(email: str, full_name: str, avatar_url: str, provider: str, oauth_id: str, is_first_user: bool = False):
    """Get existing user or create new one from OAuth"""
    user = get_user_by_email(email)

    if user:
        # Update last login and OAuth info
        users.update_one(
            {"email": email},
            {"$set": {
                "last_login": datetime.utcnow(),
                "avatar_url": avatar_url,
                "full_name": full_name
            }}
        )
        return user

    # Determine role (first user is admin)
    total_users = users.count_documents({})
    role = "admin" if (total_users == 0 or is_first_user) else "user"

    # Create new user
    new_user = {
        "email": email,
        "full_name": full_name,
        "avatar_url": avatar_url,
        "oauth_provider": provider,
        "oauth_id": oauth_id,
        "role": role,
        "theme_preference": "auto",
        "notifications_enabled": True,
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow()
    }

    users.insert_one(new_user)

    # Log user creation
    audit_logs.insert_one({
        "user_email": "system",
        "action": "user_created",
        "target": email,
        "details": {"provider": provider, "role": role},
        "timestamp": datetime.utcnow()
    })

    return new_user

def update_user_profile(email: str, full_name: str = None, theme: str = None, notifications: bool = None):
    """Update user profile"""
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    if theme is not None:
        update_data["theme_preference"] = theme
    if notifications is not None:
        update_data["notifications_enabled"] = notifications

    if update_data:
        users.update_one({"email": email}, {"$set": update_data})
        return True
    return False

# ==================== OAuth Helpers ====================

def extract_google_user_info(user_info: dict):
    """Extract user info from Google OAuth response"""
    return {
        "email": user_info.get("email"),
        "full_name": user_info.get("name", user_info.get("email", "").split("@")[0]),
        "avatar_url": user_info.get("picture", ""),
        "oauth_id": user_info.get("sub", "")
    }

def extract_github_user_info(user_info: dict, email: str):
    """Extract user info from GitHub OAuth response"""
    return {
        "email": email,
        "full_name": user_info.get("name") or user_info.get("login", "User"),
        "avatar_url": user_info.get("avatar_url", ""),
        "oauth_id": str(user_info.get("id", ""))
    }

# ==================== FastAPI Dependencies ====================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials

    try:
        payload = verify_token(token)
        email = payload.get("email")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: email not found",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

def get_current_admin(user: dict = Depends(get_current_user)):
    """Verify user has admin role"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user

# ==================== Admin User Management ====================

def create_user_as_admin(email: str, full_name: str, role: str, admin_user: dict):
    """Admin creates a new user (OAuth placeholder)"""
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = {
        "email": email,
        "full_name": full_name,
        "avatar_url": f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=6366f1&color=fff",
        "oauth_provider": "admin_created",
        "oauth_id": "",
        "role": role,
        "theme_preference": "auto",
        "notifications_enabled": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }

    users.insert_one(new_user)

    # Log action
    audit_logs.insert_one({
        "user_email": admin_user["email"],
        "action": "user_created",
        "target": email,
        "details": {"role": role},
        "timestamp": datetime.utcnow()
    })

    return {"message": "User created", "email": email, "role": role}

def list_all_users():
    """List all users (admin only)"""
    cursor = users.find({}, {"_id": 0, "email": 1, "full_name": 1, "role": 1, "oauth_provider": 1, "created_at": 1, "last_login": 1})
    return list(cursor)

def update_user_role(email: str, new_role: str, admin_user: dict):
    """Update user role (admin only)"""
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting themselves
    if email == admin_user["email"]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    users.update_one({"email": email}, {"$set": {"role": new_role}})

    # Log action
    audit_logs.insert_one({
        "user_email": admin_user["email"],
        "action": "role_updated",
        "target": email,
        "details": {"new_role": new_role},
        "timestamp": datetime.utcnow()
    })

    return {"message": "Role updated", "email": email, "role": new_role}

def delete_user(email: str, admin_user: dict):
    """Delete user (admin only)"""
    # Prevent admin from deleting themselves
    if email == admin_user["email"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = users.delete_one({"email": email})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    # Log action
    audit_logs.insert_one({
        "user_email": admin_user["email"],
        "action": "user_deleted",
        "target": email,
        "details": {},
        "timestamp": datetime.utcnow()
    })

    return {"message": "User deleted", "email": email}
