from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.lab_controller import start_ubuntu_lab, stop_lab, get_lab_status
from app.auth import (
    create_admin_user,
    create_user,
    list_users,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_admin,
)

app = FastAPI(title="Selfmade Labs API")


# ---------- CORS ----------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic Models ----------

class UserCreds(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"  # user | admin


# ---------- ROOT ----------

@app.get("/")
def home():
    return {"status": "Selfmade Labs running"}


# ---------- AUTH ROUTES ----------

@app.post("/auth/register-admin")
def register_admin(payload: UserCreds):
    # Disable this after first admin in production
    return create_admin_user(payload.username, payload.password)


@app.post("/auth/login")
def login(payload: UserCreds):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({
        "sub": user["username"],
        "role": user.get("role", "user")
    })
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user.get("role", "user")
    }


# ---------- LAB ROUTES (AUTH REQUIRED) ----------

@app.post("/start-lab")
def api_start_lab(current_user: dict = Depends(get_current_user)):
    return start_ubuntu_lab(current_user["username"])


@app.post("/stop-lab")
def api_stop_lab(current_user: dict = Depends(get_current_user)):
    return stop_lab(current_user["username"])


@app.get("/lab-status")
def api_lab_status(current_user: dict = Depends(get_current_user)):
    return get_lab_status(current_user["username"])


# ---------- ADMIN ROUTES (ADMIN ONLY) ----------

@app.post("/admin/create-user")
def admin_create_user(
    payload: UserCreate,
    admin: dict = Depends(get_current_admin)
):
    return create_user(payload.username, payload.password, payload.role)


@app.get("/admin/users")
def admin_list_users(admin: dict = Depends(get_current_admin)):
    return list_users()


# ---------- STATIC UI (MUST BE LAST) ----------

app.mount("/ui", StaticFiles(directory="static", html=True), name="static")
