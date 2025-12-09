"""
Selfmade Labs - Main API Application
Complete platform with OAuth, Labs, Services, Notifications
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import httpx

from app.lab_controller import start_lab, stop_lab, get_lab_status, list_catalog
from app.service_controller import (
    start_service, stop_service, get_service_status,
    get_service_credentials, list_service_catalog
)
from app.notifications import (
    create_notification, get_user_notifications,
    get_unread_count, mark_as_read, mark_all_as_read,
    delete_notification
)
from app.auth import (
    oauth, create_access_token, get_current_user, get_current_admin,
    get_or_create_user, extract_google_user_info, extract_github_user_info,
    update_user_profile, create_user_as_admin, list_all_users,
    update_user_role, delete_user, OAUTH_CALLBACK_BASE_URL, SECRET_KEY
)
from app.db import audit_logs, lab_instances, service_instances

app = FastAPI(
    title="Selfmade Labs API",
    description="Self-hosted lab orchestration platform",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=3600  # 1 hour session lifetime
)

# ==================== Pydantic Models ====================

class LabRequest(BaseModel):
    lab_id: str

class ServiceRequest(BaseModel):
    service_id: str

class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "user"

class UserRoleUpdate(BaseModel):
    role: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None

# ==================== Root ====================

@app.get("/")
def home():
    return {
        "status": "Selfmade Labs running",
        "version": "2.0.0",
        "features": ["OAuth", "Labs", "Services", "Notifications"]
    }

# ==================== OAuth Routes ====================

@app.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth flow"""
    redirect_uri = f"{OAUTH_CALLBACK_BASE_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # Extract user data
        user_data = extract_google_user_info(user_info)

        # Create or update user
        user = get_or_create_user(
            email=user_data["email"],
            full_name=user_data["full_name"],
            avatar_url=user_data["avatar_url"],
            provider="google",
            oauth_id=user_data["oauth_id"]
        )

        # Create JWT token
        access_token = create_access_token({
            "email": user["email"],
            "role": user["role"],
            "provider": "google"
        })

        # Redirect to dashboard with token
        return RedirectResponse(
            url=f"/ui/dashboard.html?token={access_token}",
            status_code=302
        )

    except Exception as e:
        print(f"Google OAuth error: {e}")
        return RedirectResponse(url="/ui/login.html?error=oauth_failed", status_code=302)

@app.get("/auth/github")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow"""
    redirect_uri = f"{OAUTH_CALLBACK_BASE_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)

@app.get("/auth/github/callback")
async def github_callback(request: Request):
    """Handle GitHub OAuth callback"""
    try:
        token = await oauth.github.authorize_access_token(request)

        # Get user info from GitHub API
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token['access_token']}"}

            # Get user profile
            user_resp = await client.get("https://api.github.com/user", headers=headers)
            user_info = user_resp.json()

            # Get primary email
            email_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            emails = email_resp.json()
            primary_email = next((e["email"] for e in emails if e["primary"]), emails[0]["email"] if emails else None)

            if not primary_email:
                raise HTTPException(status_code=400, detail="No email found in GitHub account")

        # Extract user data
        user_data = extract_github_user_info(user_info, primary_email)

        # Create or update user
        user = get_or_create_user(
            email=user_data["email"],
            full_name=user_data["full_name"],
            avatar_url=user_data["avatar_url"],
            provider="github",
            oauth_id=user_data["oauth_id"]
        )

        # Create JWT token
        access_token = create_access_token({
            "email": user["email"],
            "role": user["role"],
            "provider": "github"
        })

        # Redirect to dashboard with token
        return RedirectResponse(
            url=f"/ui/dashboard.html?token={access_token}",
            status_code=302
        )

    except Exception as e:
        print(f"GitHub OAuth error: {e}")
        return RedirectResponse(url="/ui/login.html?error=oauth_failed", status_code=302)

@app.post("/auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Logout (client-side token removal)"""
    return {"message": "Logged out successfully"}

# ==================== User Profile ====================

@app.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "avatar_url": current_user.get("avatar_url", ""),
        "role": current_user["role"],
        "oauth_provider": current_user.get("oauth_provider", ""),
        "theme_preference": current_user.get("theme_preference", "auto"),
        "notifications_enabled": current_user.get("notifications_enabled", True),
        "created_at": current_user.get("created_at"),
        "last_login": current_user.get("last_login")
    }

@app.put("/profile")
def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    update_user_profile(
        current_user["email"],
        full_name=data.full_name,
        theme=data.theme,
        notifications=data.notifications_enabled
    )
    return {"message": "Profile updated"}

@app.get("/profile/stats")
def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user usage statistics"""
    labs_started = lab_instances.count_documents({"user_email": current_user["email"]})
    services_started = service_instances.count_documents({"user_email": current_user["email"]})
    active_labs = lab_instances.count_documents({"user_email": current_user["email"], "status": "running"})
    active_services = service_instances.count_documents({"user_email": current_user["email"], "status": "running"})

    return {
        "labs_started_total": labs_started,
        "services_started_total": services_started,
        "active_labs": active_labs,
        "active_services": active_services
    }

# ==================== Lab Routes ====================

@app.get("/labs")
def api_list_labs(current_user: dict = Depends(get_current_user)):
    """List available labs"""
    return list_catalog()

@app.post("/labs/start")
def api_start_lab(payload: LabRequest, current_user: dict = Depends(get_current_user)):
    """Start a lab"""
    result = start_lab(current_user["email"], payload.lab_id)

    if "error" not in result:
        create_notification(
            current_user["email"],
            "lab_started",
            "Lab Started",
            f"Your {result.get('lab', 'lab')} is now running on port {result.get('port')}",
            {"lab_id": payload.lab_id, "port": result.get('port')}
        )

    return result

@app.post("/labs/stop")
def api_stop_lab(payload: LabRequest, current_user: dict = Depends(get_current_user)):
    """Stop a lab"""
    result = stop_lab(current_user["email"], payload.lab_id)

    if "message" in result:
        create_notification(
            current_user["email"],
            "lab_stopped",
            "Lab Stopped",
            f"Your lab has been stopped",
            {"lab_id": payload.lab_id}
        )

    return result

@app.get("/labs/status")
def api_lab_status(current_user: dict = Depends(get_current_user)):
    """Get user's running labs"""
    return get_lab_status(current_user["email"])

# ==================== Service Routes ====================

@app.get("/services/catalog")
def api_list_services(current_user: dict = Depends(get_current_user)):
    """List available services"""
    return list_service_catalog()

@app.post("/services/start")
def api_start_service(payload: ServiceRequest, current_user: dict = Depends(get_current_user)):
    """Start a service"""
    return start_service(current_user["email"], payload.service_id)

@app.post("/services/stop")
def api_stop_service(payload: ServiceRequest, current_user: dict = Depends(get_current_user)):
    """Stop a service"""
    return stop_service(current_user["email"], payload.service_id)

@app.get("/services/status")
def api_service_status(current_user: dict = Depends(get_current_user)):
    """Get user's running services"""
    return get_service_status(current_user["email"])

@app.get("/services/{service_id}/credentials")
def api_get_credentials(service_id: str, current_user: dict = Depends(get_current_user)):
    """Get service credentials"""
    return get_service_credentials(current_user["email"], service_id)

# ==================== Notification Routes ====================

@app.get("/notifications")
def api_notifications(unread_only: bool = False, current_user: dict = Depends(get_current_user)):
    """Get user notifications"""
    return get_user_notifications(current_user["email"], unread_only=unread_only)

@app.get("/notifications/unread-count")
def api_unread_count(current_user: dict = Depends(get_current_user)):
    """Get unread notification count"""
    count = get_unread_count(current_user["email"])
    return {"count": count}

@app.post("/notifications/{notification_id}/read")
def api_mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    success = mark_as_read(notification_id, current_user["email"])
    if success:
        return {"message": "Marked as read"}
    raise HTTPException(status_code=404, detail="Notification not found")

@app.post("/notifications/read-all")
def api_mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    count = mark_all_as_read(current_user["email"])
    return {"message": f"Marked {count} notifications as read"}

@app.delete("/notifications/{notification_id}")
def api_delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    success = delete_notification(notification_id, current_user["email"])
    if success:
        return {"message": "Notification deleted"}
    raise HTTPException(status_code=404, detail="Notification not found")

# ==================== Admin Routes ====================

@app.post("/admin/users")
def admin_create_user(payload: UserCreateRequest, admin: dict = Depends(get_current_admin)):
    """Admin creates a new user"""
    return create_user_as_admin(payload.email, payload.full_name, payload.role, admin)

@app.get("/admin/users")
def admin_list_users(admin: dict = Depends(get_current_admin)):
    """List all users"""
    return list_all_users()

@app.put("/admin/users/{email}/role")
def admin_update_role(email: str, payload: UserRoleUpdate, admin: dict = Depends(get_current_admin)):
    """Update user role"""
    return update_user_role(email, payload.role, admin)

@app.delete("/admin/users/{email}")
def admin_delete_user(email: str, admin: dict = Depends(get_current_admin)):
    """Delete a user"""
    return delete_user(email, admin)

@app.get("/admin/audit-logs")
def admin_get_logs(limit: int = 100, admin: dict = Depends(get_current_admin)):
    """Get audit logs"""
    logs = list(audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return logs

@app.get("/admin/stats")
def admin_stats(admin: dict = Depends(get_current_admin)):
    """Get platform statistics"""
    from app.db import users, lab_instances, service_instances

    total_users = users.count_documents({})
    total_admins = users.count_documents({"role": "admin"})
    active_labs = lab_instances.count_documents({"status": "running"})
    active_services = service_instances.count_documents({"status": "running"})
    total_labs_started = lab_instances.count_documents({})
    total_services_started = service_instances.count_documents({})

    return {
        "users": {
            "total": total_users,
            "admins": total_admins,
            "regular": total_users - total_admins
        },
        "labs": {
            "active": active_labs,
            "total_started": total_labs_started
        },
        "services": {
            "active": active_services,
            "total_started": total_services_started
        }
    }

# ==================== Static Files (MUST BE LAST) ====================

app.mount("/ui", StaticFiles(directory="static", html=True), name="static")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
