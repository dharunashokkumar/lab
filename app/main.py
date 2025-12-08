from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from app.lab_controller import start_ubuntu_lab, stop_lab, get_lab_status
from app.auth import (
    create_admin_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_admin,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserCreds(BaseModel):
    username: str
    password: str


@app.get("/")
def home():
    return {"status": "Selfmade Labs running"}


# ---------- AUTH ----------

@app.post("/auth/register-admin")
def register_admin(payload: UserCreds):
    # In real deployment, you may disable this after first admin is created
    return create_admin_user(payload.username, payload.password)


@app.post("/auth/login")
def login(payload: UserCreds):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": user["username"], "role": user.get("role", "user")})
    return {"access_token": token, "token_type": "bearer"}


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


from fastapi.staticfiles import StaticFiles

app.mount("/ui", StaticFiles(directory="static", html=True), name="static")
