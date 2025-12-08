
# Selfmade Labs Platform 🚀

Selfmade Labs is a **self-hosted lab orchestration platform** that allows authenticated users to spin up isolated, time-limited practice labs (starting with Ubuntu SSH) using Docker.

This project is built as a **real backend-first product**, not a demo or tutorial, and is currently in **private beta**.

---

## 🔑 Key Features

- ✅ JWT-based authentication
- ✅ Admin-controlled access
- ✅ Secure, per-user labs
- ✅ Docker-based isolation
- ✅ Auto lab cleanup (timeouts)
- ✅ Live dashboard (HTML + JS)
- ✅ GitHub-based dev workflow

---

## 🧠 High-Level Architecture

```

Browser (UI)
│
│  HTTP (JWT Auth)
▼
FastAPI Backend
│
├── MongoDB (users, lab state)
├── Docker Engine
│     └── Lab Containers (Ubuntu SSH)
│
└── Static UI (/ui)

```

---

## 🧩 Tech Stack

### Backend
- Python 3.12
- FastAPI
- MongoDB
- Docker
- JWT (python-jose)
- passlib (bcrypt)

### Frontend
- Plain HTML
- CSS (dark UI)
- Vanilla JavaScript
- Served via FastAPI static routing

### Dev & Infra
- Git + GitHub
- Ubuntu VM (server)
- Windows (development machine)

---

## 🔐 Authentication Model

- Admin and users authenticate via **JWT tokens**
- Tokens are stored in browser `localStorage`
- All lab APIs are **protected**
- Unauthorized requests return `401 / 403`

### Auth Endpoints
```

POST /auth/login
POST /auth/register-admin   (disabled later for public beta)

````

---

## 🧪 Lab System

### Current Lab
- Ubuntu 22.04 SSH lab
- One container per user
- Dynamic port allocation

### Lab Lifecycle
1. User clicks **Start Lab**
2. Docker container is created
3. SSH credentials are shown
4. Lab auto-expires after fixed time
5. Container is destroyed

### Example SSH Access
```bash
ssh student@127.0.0.1 -p 22XX
Password: student123
````

---

## 📊 Database Collections (MongoDB)

### users

```json
{
  "username": "admin",
  "password": "<bcrypt_hash>",
  "role": "admin",
  "created_at": "ISO_DATE"
}
```

### lab_instances

```json
{
  "user_id": "admin",
  "lab": "ubuntu-ssh",
  "container": "lab_admin",
  "port": 2283,
  "status": "running",
  "started_at": "ISO_DATE"
}
```

---

## 🖥️ Dashboard (UI)

The UI is served from FastAPI:

```
/ui/login.html
/ui/dashboard.html
```

### Dashboard Features

* Login / Logout
* Start / Stop lab
* Live lab status
* SSH command display
* Auto-refresh (every 5s)

---

## ▶️ How to Run (Local / VM)

### 1️⃣ Start Backend

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2️⃣ Open UI

```
http://127.0.0.1:8000/ui/login.html
```

---

## 🧑‍💻 Development Workflow

### Initial Push (Ubuntu VM)

```bash
git init
git add .
git commit -m "Initial Selfmade Labs platform"
git push origin main
```

### Daily Workflow

* ✅ Develop on Windows
* ✅ Push to GitHub
* ✅ Pull & run on Ubuntu VM

```bash
git pull
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🧠 Design Principles

* Backend-first architecture
* Explicit > magic
* Secure-by-default
* Docker over VMs
* Same-origin UI + API
* Simple UI, powerful backend

---

## 🚧 Current Status

✅ Core platform complete
✅ Auth system stable
✅ Dashboard stable
✅ Lab orchestration verified

---

## 🛣️ Roadmap

### Phase 1 (Next)

* Admin UI to create users
* Disable admin self-registration
* User role enforcement

### Phase 2

* Multiple lab types (MySQL, Web, Docker)
* Lab catalog UI

### Phase 3

* Public beta hardening
* Rate limits
* Firewall rules
* Monitoring & logs

---


