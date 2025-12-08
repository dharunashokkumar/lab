# Self-Made Labs Platform

Self-Made Labs is a backend-first lab orchestration platform that allows users to spin up isolated practice environments (labs) on demand using Docker.  
The platform is designed for learning, testing, and experimentation — not CTFs or challenge-based scoring.

This project is currently in **local beta (VM-based testing)** and is being prepared for **public beta**.

---

## 🎯 Project Goals

- Provide **on-demand Linux labs** (SSH-based)
- Ensure **isolation per user**
- Automatically **clean up resources**
- Be **simple, controllable, and extensible**
- Start small (classmates) → scale to public users

---

## 🧠 High-Level Architecture

[ User / Browser / CLI ]
|
| HTTP (REST API)
v
[ FastAPI Backend (Python) ]
|
| State & Metadata
v
[ MongoDB ]
|
| Container Control
v
[ Docker Engine ]
|
v
[ Lab Containers (Ubuntu, MySQL, etc.) ]
|
v
[ User connects via SSH ]


---

## 🧩 Core Components

### 1️⃣ Backend API (FastAPI)
- Language: **Python**
- Framework: **FastAPI**
- Responsibilities:
  - Start / Stop labs
  - Track lab state
  - Prevent duplicate labs
  - Enforce auto-timeouts
  - Act as a single control plane

---

### 2️⃣ Lab Engine (Docker-based)
- Each lab runs as **one Docker container per user**
- Containers are:
  - Non-privileged
  - Port-mapped dynamically
  - Destroyed after use

Example:

lab_dharun → ubuntu-ssh-lab → port 2283


---

### 3️⃣ Database (MongoDB)
MongoDB stores **state**, not heavy data.

Collections:
- `users` (future)
- `labs` (lab templates)
- `lab_instances` (running / stopped labs)

Example lab instance document:

```json
{
  "user_id": "dharun",
  "lab": "ubuntu-ssh",
  "container": "lab_dharun",
  "port": 2283,
  "status": "running",
  "started_at": "2025-01-01T10:30:00Z"
}

4️⃣ Auto Cleanup System

    Every lab has a time limit (default: 30 minutes)

    Implemented using Python threading.Timer

    Prevents:

        Resource abuse

        Forgotten running labs

        Server overload

Statuses:

    running

    stopped

    auto-stopped

5️⃣ Frontend (HTML/CSS Dashboard)

    Simple static dashboard

    Communicates with backend via Fetch API

    No framework (intentionally)

    Used for:

        Starting labs

        Stopping labs

        Viewing connection info

🔐 Security Model (Current)

✅ One container per user
✅ No shared containers
✅ No privileged Docker access
✅ Time-limited labs
✅ No direct host access from containers

Authentication & authorization are next planned features.
🧪 Current Features (Implemented)

    ✅ Ubuntu SSH Lab

    ✅ Dynamic port allocation

    ✅ Start / Stop lab via API

    ✅ Auto-stop after timeout

    ✅ MongoDB state persistence

    ✅ Simple dashboard

    ✅ Manual SSH access

🚧 Planned Features (Public Beta Roadmap)
Phase 1 – Admin & Auth (NEXT)

    Admin login

    User authentication (JWT)

    Role-based access (admin / user)

    Admin-only lab creation

Phase 2 – Multiple Labs

    MySQL lab

    Web server lab

    Docker practice lab

    Lab catalog UI

Phase 3 – Public Beta Hardening

    Rate limiting

    Firewall rules

    Server migration (bare metal / VPS)

    Logging & monitoring

🖥️ Development Environment

    Host: Ubuntu VM (VirtualBox)

    Python: 3.12 (venv)

    Docker: Engine

    MongoDB: Community Edition

    OS tested: Ubuntu 22.04 LTS

▶️ How to Run (Local Testing)
Backend

source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

Dashboard

xdg-open dashboard/index.html

Connect to Lab

ssh student@<server-ip> -p <port>

Password:

student123

🧠 Design Philosophy

    Backend-first

    Explicit over magic

    Docker before VMs

    Simple systems > complex frameworks

    Build small → scale later

📌 Status

✅ Core platform functional
✅ Architecture validated
🚧 Admin & auth in progress
🚀 Preparing for public beta


---

## ✅ Why this README is IMPORTANT

- Another AI can now:
  - Understand architecture
  - Suggest changes correctly
  - Not break core logic

- You can now:
  - Explain your system confidently
  - Share repo without confusion
  - Resume work months later

---

## 🚀 NEXT STEP (as you asked)

Now we move to **Admin Panel + Auth System**, in the **correct order**:

### ✅ Order we will follow (important)
1. **JWT Authentication**
2. **User roles (admin / user)**
3. **Admin-protected APIs**
4. **Admin dashboard**
5. **Public beta hardening**

If you agree, next reply with:

👉 **“Start Auth System”**

and I’ll build it with you step-by-step, clean and production-ready.