# Selfmade Labs Platform

**A production-ready, self-hosted lab and service orchestration platform with OAuth authentication, Docker-based isolation, persistent storage, and a modern UI.**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
   - [High-Level Architecture](#high-level-architecture)
   - [Shared Services Architecture](#shared-services-architecture)
   - [Volume Management & Data Persistence](#volume-management--data-persistence)
   - [Resource Efficiency](#resource-efficiency)
3. [Key Features](#key-features)
4. [Technology Stack](#technology-stack)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Setup Instructions](#setup-instructions)
8. [Running the Platform](#running-the-platform)
9. [OAuth Configuration](#oauth-configuration)
10. [Project Structure](#project-structure)
11. [Development Workflow](#development-workflow)
12. [Troubleshooting](#troubleshooting)
13. [Security Considerations](#security-considerations)

---

## Overview

Selfmade Labs is a **production-ready platform** for orchestrating isolated lab environments and database services. Users authenticate via **OAuth (Google/GitHub)**, launch containerized labs (Ubuntu, Kali Linux, n8n), start database services (MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ), and receive real-time notifications about their resources.

### Core Principles

- **OAuth-Only Authentication**: No username/password - Google and GitHub OAuth only
- **Email-Based Identity**: Users identified by email address across the platform
- **Docker Orchestration**: All labs and services run in isolated Docker containers
- **Persistent Storage**: User data persists across lab sessions via Docker volumes
- **Resource Efficiency**: Shared service containers reduce RAM usage by 50-90%
- **Auto-Stop Timers**: Labs auto-stop after 30 minutes to prevent resource leaks
- **Modern UI**: Clean, minimal interface with dark/light theme support
- **Real-Time Notifications**: Users notified of all resource lifecycle events
- **Admin Panel**: Full user management, audit logs, and platform statistics

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SELFMADE LABS PLATFORM                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Browser UI     │  (HTML/CSS/JS with OAuth)
│  ┌────────────┐  │
│  │ Dashboard  │  │  - Lab management
│  │ Services   │  │  - Service credentials
│  │ Profile    │  │  - User settings
│  │ Admin      │  │  - Admin panel (role-based)
│  └────────────┘  │
└────────┬─────────┘
         │ HTTPS/HTTP
         │ JWT Bearer Token
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend (Python)                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Authentication │  │ Lab Controller │  │Service Control.│            │
│  │ - OAuth 2.0    │  │ - Docker mgmt  │  │ - Shared DBs   │            │
│  │ - JWT tokens   │  │ - Port alloc   │  │ - Credentials  │            │
│  │ - User mgmt    │  │ - Auto-stop    │  │ - Isolation    │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │Volume Manager  │  │ Notifications  │  │  Audit Logs    │            │
│  │ - Docker vols  │  │ - Events       │  │ - Admin actions│            │
│  │ - Persistence  │  │ - Unread count │  │ - Compliance   │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
└───────┬──────────────────────────────────────────────┬──────────────────┘
        │                                              │
        ▼                                              ▼
┌──────────────────┐                      ┌──────────────────────────────┐
│   MongoDB        │                      │      Docker Engine           │
│                  │                      │                              │
│ - users          │                      │  ┌─────────────────────┐    │
│ - lab_instances  │                      │  │  Lab Containers     │    │
│ - service_inst.  │                      │  │  (Per-User Isolated)│    │
│ - notifications  │                      │  ├─────────────────────┤    │
│ - audit_logs     │                      │  │ lab_user1_ubuntu    │    │
│ - lab_catalog    │                      │  │ lab_user2_kali      │    │
│ - service_cat.   │                      │  │ lab_user3_n8n       │    │
│                  │                      │  └─────────────────────┘    │
└──────────────────┘                      │                              │
                                          │  ┌─────────────────────┐    │
                                          │  │ Service Containers  │    │
                                          │  │  (Shared by Users)  │    │
                                          │  ├─────────────────────┤    │
                                          │  │ selfmade-mysql-     │    │
                                          │  │ shared (500MB)      │    │
                                          │  │ ├─ user_abc_db      │    │
                                          │  │ ├─ user_def_db      │    │
                                          │  │ └─ user_xyz_db      │    │
                                          │  ├─────────────────────┤    │
                                          │  │ selfmade-postgresql-│    │
                                          │  │ shared (400MB)      │    │
                                          │  │ selfmade-mongodb-   │    │
                                          │  │ shared (600MB)      │    │
                                          │  │ selfmade-redis-     │    │
                                          │  │ shared (100MB)      │    │
                                          │  │ selfmade-rabbitmq-  │    │
                                          │  │ shared (500MB)      │    │
                                          │  └─────────────────────┘    │
                                          │                              │
                                          │  ┌─────────────────────┐    │
                                          │  │ Docker Volumes      │    │
                                          │  │ (Persistent Storage)│    │
                                          │  ├─────────────────────┤    │
                                          │  │ user_dharuna457_home│    │
                                          │  │ user_john_doe_home  │    │
                                          │  │ user_jane_smith_home│    │
                                          │  └─────────────────────┘    │
                                          └──────────────────────────────┘
```

---

### Shared Services Architecture

**This platform uses SHARED SERVICE CONTAINERS for optimal resource efficiency.**

#### Architecture Comparison

```
✅ CURRENT IMPLEMENTATION (Shared Containers):
┌─────────────────────────────────────────┐
│  selfmade-mysql-shared (ONE container)  │
│  ├── user_abc_db (User A)               │
│  ├── user_def_db (User B)               │
│  └── user_xyz_db (User C)               │
│  RAM: ~500MB total for ALL users        │
└─────────────────────────────────────────┘

VS

❌ ALTERNATIVE (Isolated Per-User) - NOT USED:
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ User A MySQL │ │ User B MySQL │ │ User C MySQL │
│ RAM: 500MB   │ │ RAM: 500MB   │ │ RAM: 500MB   │
└──────────────┘ └──────────────┘ └──────────────┘
Total: 1.5GB for 3 users! (3x more RAM)
```

#### Why Shared Containers?

1. **RAM Efficiency**: 50-90% reduction in memory usage
   - Shared MySQL: 500MB total (all users)
   - Isolated MySQL: 500MB per user (10 users = 5GB!)

2. **Cost Savings**: Fewer server resources needed
   - 10 users with shared services: ~2GB RAM
   - 10 users with isolated services: ~21GB RAM

3. **Faster Startup**: Shared containers are pre-warmed
   - Service start: <1 second (container already running)
   - Isolated start: 5-10 seconds (container creation)

4. **Easier Management**: Single container per service type
   - Updates: Update one container, affects all users
   - Monitoring: Monitor one container per service

#### Isolation Strategy

While containers are shared, **user data is completely isolated**:

| Isolation Layer | Implementation |
|----------------|----------------|
| **MySQL** | Separate database per user (`user_a1b2c3d4`) with unique credentials |
| **PostgreSQL** | Separate database per user with unique credentials |
| **MongoDB** | Separate database with scoped user roles |
| **Redis** | Separate DB number per user (0-15) |
| **RabbitMQ** | Separate virtual host per user (`/user_a1b2c3d4`) |

**Security**: Users CANNOT access other users' data. Each user gets:
- Unique database name (hashed from email)
- Unique credentials (randomly generated)
- Database-scoped permissions (no cross-user access)

---

### Volume Management & Data Persistence

#### Volume Architecture

Each user gets **ONE persistent Docker volume** shared across ALL their labs:

```
Volume Strategy:
┌─────────────────────────────────────────┐
│  user_dharuna457_home (Docker Volume)  │
│  - Mounted to /home/labuser in labs    │
│  - Persists across container restarts  │
│  - Shared by all user's labs           │
│  - Survives container deletion         │
└─────────────────────────────────────────┘
         │
         ├─> Ubuntu Lab: /home/labuser
         ├─> Kali Lab: /home/labuser
         └─> n8n Lab: /home/labuser

User A sees SAME files in all labs
User B has SEPARATE volume with THEIR files
```

#### Volume Lifecycle

```
User Registration:
└─> No volume created yet

First Lab Launch:
├─> volume_manager.create_user_volume_if_not_exists(user_email)
├─> Volume created: user_{sanitized_email}_home
├─> Example: user_dharuna457_home
└─> Mounted to /home/labuser in container

Subsequent Lab Launches:
├─> Same volume reused
├─> User sees their files from previous sessions
└─> Changes persist immediately

User Account Deletion:
├─> volume_manager.delete_user_volume(user_email)
├─> Docker volume permanently deleted
└─> ALL user data removed
```

#### Volume Naming Convention

```python
# Email to Volume Name Mapping
dharuna457@gmail.com    →  user_dharuna457_home
john.doe@company.com    →  user_john_doe_home
jane-smith@example.org  →  user_jane_smith_home

# Rules:
# 1. Extract username before @
# 2. Replace dots with underscores
# 3. Replace dashes with underscores
# 4. Prefix with "user_", suffix with "_home"
```

#### What Persists vs Ephemeral

| Location | Persistence | Use Case |
|----------|-------------|----------|
| `/home/labuser` | ✅ Persistent (Docker volume) | User files, projects, configs |
| `/tmp` | ❌ Ephemeral (lost on stop) | Temporary files |
| Container OS | ❌ Ephemeral | System changes (use Dockerfile) |
| Installed packages | ❌ Ephemeral | Rebuild container or use volume |

---

### Resource Efficiency

#### RAM Consumption Comparison

**Current Architecture (Shared Services):**
```
Services (shared containers):
- MySQL: 500MB
- PostgreSQL: 400MB
- MongoDB: 600MB
- Redis: 100MB
- RabbitMQ: 500MB
Total Services: ~2GB for ALL users

Labs (per-user containers):
- Per lab: 4GB RAM + 2 CPUs
- 10 users × 1 lab each: 40GB RAM
Total Platform: 2GB + 40GB = 42GB
```

**Alternative Architecture (Isolated Services) - NOT USED:**
```
Services (isolated per-user):
- MySQL × 10 users: 5GB
- PostgreSQL × 10 users: 4GB
- MongoDB × 10 users: 6GB
- Redis × 10 users: 1GB
- RabbitMQ × 10 users: 5GB
Total Services: 21GB for 10 users

Labs (per-user containers):
- 10 users × 1 lab each: 40GB RAM
Total Platform: 21GB + 40GB = 61GB (45% more RAM!)
```

**Savings**: Shared service containers save **~20GB RAM for 10 users**, or **~2GB per user**.

#### Resource Limits

**Per-Lab Container Limits:**
- CPU: 2 vCPUs maximum
- Memory: 4GB RAM maximum
- Auto-stop: 30 minutes of runtime

**Service Container Limits:**
- No limits (shared infrastructure)
- Monitored via Docker stats

---

## Key Features

### Authentication & Authorization

- **OAuth 2.0 Only**: Google and GitHub providers
- **First User Admin**: Automatic admin role for first login
- **JWT Sessions**: 24-hour token expiration
- **Email-Based Identity**: No usernames, email is primary key
- **Role-Based Access**: Admin vs User permissions

### Lab Environments

| Lab | Description | Image | Port |
|-----|-------------|-------|------|
| **Ubuntu SSH** | Ubuntu 22.04 with dev tools, ttyd terminal | `selfmade/ubuntu-ssh` | 7681 |
| **Kali Linux** | Pentesting environment with security tools | `selfmade/kali-linux` | 7681 |
| **n8n** | Workflow automation platform | `n8nio/n8n` | 5678 |

**Lab Features:**
- Web-based terminal (ttyd) - no SSH client needed
- Persistent storage via Docker volumes
- Pre-installed development tools
- User: `labuser` (sudo privileges)
- Auto-stop after 30 minutes
- Dynamic port allocation (8000-9000)

### Database Services

| Service | Version | Port | Container Name |
|---------|---------|------|----------------|
| **MySQL** | 8.0 | 3306 | `selfmade-mysql-shared` |
| **PostgreSQL** | 16 | 5432 | `selfmade-postgresql-shared` |
| **MongoDB** | 7.0 | 27018 | `selfmade-mongodb-shared` |
| **Redis** | 7 Alpine | 6379 | `selfmade-redis-shared` |
| **RabbitMQ** | 3 Management | 5672 | `selfmade-rabbitmq-shared` |

**Service Features:**
- Shared containers (one per service type)
- Isolated user databases
- Auto-generated credentials
- Connection string generation
- Copy-to-clipboard credentials

### Notifications

- **Event Types**: `lab_started`, `lab_stopped`, `service_started`, `service_stopped`
- **Unread Tracking**: Badge with unread count
- **Mark as Read**: Individual or bulk operations
- **Auto-Cleanup**: Old read notifications deleted after 30 days

### Admin Panel

- **User Management**: Create, update role, delete users
- **Audit Logs**: Complete action history with timestamps
- **Platform Statistics**: Total users, active labs, active services
- **Role Enforcement**: Admin-only access

### UI/UX

- **Modern Design**: Clean, minimal, professional
- **Theme System**: Auto (system), Light, Dark modes
- **Responsive**: Works on desktop and mobile
- **Sidebar Navigation**: Persistent across pages
- **Material Icons**: Google Material Design iconography

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Runtime |
| FastAPI | 0.115.5 | Web framework |
| Uvicorn | 0.32.1 | ASGI server |
| PyMongo | 4.10.1 | MongoDB driver |
| Authlib | 1.3.0 | OAuth 2.0 client |
| python-jose | 3.3.0 | JWT encoding/decoding |
| python-dotenv | 1.0.0 | Environment config |
| httpx | 0.27.0 | Async HTTP client |
| email-validator | 2.1.1 | Email validation |

### Frontend

| Technology | Purpose |
|------------|---------|
| HTML5 | Structure |
| CSS3 (Custom Properties) | Theming system |
| Vanilla JavaScript | Interactivity (no frameworks) |
| Material Icons Round | Iconography |
| Google Fonts | Typography (Google Sans, Roboto) |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| MongoDB 7.0 | NoSQL database |
| Docker Engine | Container runtime |
| Docker Volumes | Persistent storage |
| Git | Version control |

---

## Database Schema

### Collections Overview

| Collection | Documents | Purpose |
|------------|-----------|---------|
| `users` | User accounts | OAuth profiles, roles, preferences |
| `lab_instances` | Running labs | Lab state, ports, volumes |
| `service_instances` | Running services | Service credentials, ports |
| `notifications` | User notifications | Events, read status |
| `audit_logs` | Admin actions | Compliance, security |
| `lab_catalog` | Available labs | Lab definitions (seeded) |
| `service_catalog` | Available services | Service definitions (seeded) |

### `users` Collection

```javascript
{
  "_id": ObjectId("..."),
  "email": "dharuna457@gmail.com",           // Primary identifier
  "full_name": "Dharun A",
  "avatar_url": "https://...",
  "role": "user",                            // "user" or "admin"
  "oauth_provider": "google",                // "google" or "github"
  "oauth_id": "1234567890",                  // Provider user ID
  "theme_preference": "auto",                // "auto", "light", "dark"
  "notifications_enabled": true,
  "created_at": ISODate("2025-01-01T00:00:00Z"),
  "last_login": ISODate("2025-01-01T12:00:00Z")
}
```

### `lab_instances` Collection

```javascript
{
  "_id": ObjectId("..."),
  "user_email": "dharuna457@gmail.com",
  "lab": "ubuntu-ssh",                       // Lab ID from catalog
  "lab_name": "Ubuntu Essentials Lab",
  "container": "lab_dharuna457_ubuntu-ssh_1234",
  "volume": "user_dharuna457_home",          // Persistent volume
  "port": 8234,                              // External port
  "access_url": "http://localhost:8234",     // Direct access URL
  "access_type": "web_terminal",             // "web" or "web_terminal"
  "status": "running",                       // "running", "stopped", "auto-stopped"
  "started_at": ISODate("2025-01-01T12:00:00Z"),
  "stopped_at": ISODate("2025-01-01T12:30:00Z"),
  "resources": {
    "cpus": "2",
    "memory": "4g"
  }
}
```

### `service_instances` Collection

```javascript
{
  "_id": ObjectId("..."),
  "user_email": "dharuna457@gmail.com",
  "service": "mysql",                        // Service ID from catalog
  "service_name": "MySQL 8.0",
  "container": "selfmade-mysql-shared",      // Shared container
  "port": 3306,
  "credentials": {
    "host": "localhost",
    "port": 3306,
    "username": "user_a1b2c3d4",             // Hashed username
    "password": "random_generated_password",
    "database": "user_a1b2c3d4"
  },
  "connection_info": {
    "host": "localhost",
    "port": 3306,
    "connection_string": "mysql://user_a1b2c3d4:password@localhost:3306/user_a1b2c3d4"
  },
  "status": "running",
  "started_at": ISODate("2025-01-01T12:00:00Z")
}
```

### `notifications` Collection

```javascript
{
  "_id": ObjectId("..."),
  "user_email": "dharuna457@gmail.com",
  "type": "lab_started",                     // Event type
  "title": "Lab Started",
  "message": "Your Ubuntu Essentials Lab is running",
  "metadata": {
    "lab_id": "ubuntu-ssh",
    "port": 8234
  },
  "read": false,
  "created_at": ISODate("2025-01-01T12:00:00Z")
}
```

### `audit_logs` Collection

```javascript
{
  "_id": ObjectId("..."),
  "user_email": "admin@example.com",
  "action": "USER_CREATED",                  // Action type
  "target": "newuser@example.com",
  "details": {
    "role": "user"
  },
  "timestamp": ISODate("2025-01-01T12:00:00Z")
}
```

---

## API Endpoints

### Authentication (`/auth/*`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/auth/google` | Initiate Google OAuth flow | None |
| GET | `/auth/google/callback` | Handle Google OAuth callback | None |
| GET | `/auth/github` | Initiate GitHub OAuth flow | None |
| GET | `/auth/github/callback` | Handle GitHub OAuth callback | None |
| POST | `/auth/logout` | Logout user (client-side) | User |

### User Profile (`/me`, `/profile/*`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/me` | Get current user profile | User |
| PUT | `/profile` | Update profile (name, theme, notifications) | User |
| GET | `/profile/stats` | Get user statistics | User |

### Labs (`/labs/*`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/labs` | Get lab catalog | User |
| POST | `/labs/start` | Start a lab (JSON: `{"lab_id": "ubuntu-ssh"}`) | User |
| POST | `/labs/stop` | Stop a lab (JSON: `{"lab_id": "ubuntu-ssh"}`) | User |
| GET | `/labs/status` | Get running labs for user | User |

### Services (`/services/*`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/services/catalog` | Get service catalog | User |
| POST | `/services/start` | Start a service (JSON: `{"service_id": "mysql"}`) | User |
| POST | `/services/stop` | Stop a service (JSON: `{"service_id": "mysql"}`) | User |
| GET | `/services/status` | Get running services for user | User |
| GET | `/services/{service_id}/credentials` | Get service credentials | User |

### Notifications (`/notifications/*`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/notifications` | Get user notifications | User |
| GET | `/notifications/unread-count` | Get unread count | User |
| POST | `/notifications/{id}/read` | Mark notification as read | User |
| POST | `/notifications/read-all` | Mark all as read | User |
| DELETE | `/notifications/{id}` | Delete notification | User |

### Admin (`/admin/*`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/admin/users` | Create user (JSON: `{"email": "...", "full_name": "...", "role": "user"}`) | Admin |
| GET | `/admin/users` | Get all users | Admin |
| PUT | `/admin/users/{email}/role` | Update user role (JSON: `{"role": "admin"}`) | Admin |
| DELETE | `/admin/users/{email}` | Delete user | Admin |
| GET | `/admin/audit-logs` | Get audit logs | Admin |
| GET | `/admin/stats` | Get platform statistics | Admin |

---

## Setup Instructions

### Prerequisites

- **Python 3.12+**
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **MongoDB** (via Docker or local install)
- **Git**
- **Google Cloud Console** account (for OAuth)
- **GitHub** account (for OAuth)

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd lab
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start MongoDB

```bash
# Using Docker
docker run -d \
  --name selfmade-mongo \
  -p 27017:27017 \
  mongo:7.0

# Verify running
docker ps | grep mongo
```

### 5. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and fill in OAuth credentials:

```env
# OAuth Credentials (Get from Google Cloud Console & GitHub)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Application Security
SECRET_KEY=your-secret-key-256-bits-change-this-in-production

# Database
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=selfmade_labs

# OAuth Callback URLs
OAUTH_CALLBACK_BASE_URL=http://localhost:8000

# Application Settings
ENVIRONMENT=development
DEBUG=True
```

### 6. Build Lab Docker Images

```bash
# Windows
build-labs.bat

# Linux/Mac
chmod +x build-labs.sh
./build-labs.sh
```

**Or build manually:**

```bash
# Ubuntu SSH Lab
cd labs/ubuntu-ssh
docker build -t selfmade/ubuntu-ssh .

# Kali Linux Lab
cd ../kali-linux
docker build -t selfmade/kali-linux .

# Return to root
cd ../..
```

### 7. Verify Docker Images

```bash
docker images | grep selfmade

# Expected output:
# selfmade/ubuntu-ssh    latest    ...
# selfmade/kali-linux    latest    ...
```

---

## Running the Platform

### Start the Server

```bash
# Activate virtual environment (if not already)
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

**Expected output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Access the Platform

Open your browser and navigate to:

```
http://localhost:8000/ui/login.html
```

**First Login:**
1. Click "Sign in with Google" or "Sign in with GitHub"
2. Authorize the application
3. First user automatically becomes admin
4. Redirected to dashboard

---

## OAuth Configuration

### Google Cloud Console Setup

1. **Create Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project: "Selfmade Labs"

2. **Enable OAuth Consent Screen**
   - Navigation: APIs & Services → OAuth consent screen
   - User Type: External
   - App name: "Selfmade Labs"
   - User support email: your_email@gmail.com
   - Developer contact: your_email@gmail.com
   - Scopes: Add `email`, `profile`, `openid`

3. **Create OAuth Client ID**
   - Navigation: APIs & Services → Credentials
   - Create Credentials → OAuth Client ID
   - Application type: Web application
   - Name: "Selfmade Labs Web Client"
   - Authorized redirect URIs:
     ```
     http://localhost:8000/auth/google/callback
     ```
   - Click Create
   - Copy **Client ID** and **Client Secret** to `.env`

### GitHub OAuth App Setup

1. **Create OAuth App**
   - Go to GitHub Settings → Developer settings → OAuth Apps
   - Click "New OAuth App"

2. **Configure App**
   - Application name: "Selfmade Labs"
   - Homepage URL: `http://localhost:8000`
   - Application description: "Self-hosted lab platform"
   - Authorization callback URL:
     ```
     http://localhost:8000/auth/github/callback
     ```
   - Click "Register application"

3. **Generate Client Secret**
   - Click "Generate a new client secret"
   - Copy **Client ID** and **Client Secret** to `.env`

---

## Project Structure

```
lab/
├── app/                          # Python backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, all endpoints
│   ├── auth.py                   # OAuth & JWT authentication
│   ├── db.py                     # MongoDB collections & seeding
│   ├── lab_controller.py         # Lab orchestration
│   ├── service_controller.py     # Service orchestration (shared containers)
│   ├── volume_manager.py         # Docker volume management
│   ├── notifications.py          # Notification system
│   └── migrate_db.py             # Database migration script
│
├── static/                       # Frontend (HTML/CSS/JS)
│   ├── login.html                # OAuth login page
│   ├── dashboard.html            # Main dashboard
│   ├── services.html             # Service management
│   ├── profile.html              # User profile
│   ├── settings.html             # User settings
│   ├── admin.html                # Admin panel
│   ├── css/
│   │   └── theme.css             # Design system & theming
│   └── js/
│       ├── theme.js              # Theme management
│       └── api.js                # API client with JWT
│
├── labs/                         # Docker lab definitions
│   ├── ubuntu-ssh/
│   │   └── Dockerfile            # Ubuntu 22.04 + ttyd
│   └── kali-linux/
│       └── Dockerfile            # Kali Linux + pentesting tools
│
├── .env                          # Environment configuration (create from .env.example)
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── build-labs.bat                # Windows lab builder
├── build-labs.sh                 # Linux/Mac lab builder
├── QUICKSTART.md                 # Quick setup guide
├── TROUBLESHOOTING.md            # Common issues & solutions
├── TODO.md                       # Development roadmap
└── README.md                     # This file
```

---

## Development Workflow

### Running in Development Mode

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run with auto-reload
uvicorn app.main:app --reload --port 8000
```

### Making Code Changes

```bash
# Make changes to Python files
# Server auto-reloads on save (--reload flag)

# Make changes to static files (HTML/CSS/JS)
# Refresh browser to see changes
```

### Git Workflow

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add username extraction function to volume_manager"

# Push to remote
git push origin main
```

### Database Reset

```bash
# Connect to MongoDB container
docker exec -it selfmade-mongo mongosh

# Drop database
> use selfmade_labs
> db.dropDatabase()
> exit

# Restart server (will re-seed catalogs)
uvicorn app.main:app --reload
```

### View Logs

```bash
# MongoDB logs
docker logs selfmade-mongo

# Lab container logs
docker logs lab_dharuna457_ubuntu-ssh_1234

# Service container logs
docker logs selfmade-mysql-shared
```

### Testing API Endpoints

```bash
# Health check (no auth)
curl http://localhost:8000/

# Get lab catalog (requires auth)
curl -H "Authorization: Bearer <your_jwt_token>" \
     http://localhost:8000/labs

# Start lab (requires auth)
curl -X POST \
     -H "Authorization: Bearer <your_jwt_token>" \
     -H "Content-Type: application/json" \
     -d '{"lab_id": "ubuntu-ssh"}' \
     http://localhost:8000/labs/start
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pymongo'"

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux

# Install dependencies
pip install -r requirements.txt
```

---

### Issue: "Cannot connect to MongoDB"

**Cause**: MongoDB container not running

**Solution**:
```bash
# Check if container exists
docker ps -a | grep mongo

# Start container if stopped
docker start selfmade-mongo

# Create container if doesn't exist
docker run -d --name selfmade-mongo -p 27017:27017 mongo:7.0
```

---

### Issue: "OAuth error: redirect_uri_mismatch"

**Cause**: Callback URLs in Google/GitHub don't match `.env`

**Solution**:
1. Check `.env` for `OAUTH_CALLBACK_BASE_URL` (should be `http://localhost:8000`)
2. Verify Google Cloud Console callback URL:
   ```
   http://localhost:8000/auth/google/callback
   ```
3. Verify GitHub OAuth App callback URL:
   ```
   http://localhost:8000/auth/github/callback
   ```

---

### Issue: "Port 8000 already in use"

**Cause**: Another process is using port 8000

**Solution**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8080
```

---

### Issue: "docker: command not found"

**Cause**: Docker not installed or not in PATH

**Solution**:
- **Windows/Mac**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: Install Docker Engine
  ```bash
  # Ubuntu/Debian
  sudo apt update
  sudo apt install docker.io
  sudo systemctl start docker
  sudo usermod -aG docker $USER
  ```

---

### Issue: Lab won't start - "Failed to start container"

**Cause**: Docker image not built or doesn't exist

**Solution**:
```bash
# Check if images exist
docker images | grep selfmade

# If missing, build images
cd labs/ubuntu-ssh
docker build -t selfmade/ubuntu-ssh .

cd ../kali-linux
docker build -t selfmade/kali-linux .
```

---

### Issue: "Permission denied" when creating volumes

**Cause**: Docker daemon requires elevated permissions

**Solution**:
```bash
# Windows: Run Docker Desktop as Administrator
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

---

### Issue: Service credentials show "undefined"

**Cause**: Service not fully started or database creation failed

**Solution**:
1. Check service container logs:
   ```bash
   docker logs selfmade-mysql-shared
   ```
2. Verify container is running:
   ```bash
   docker ps | grep selfmade
   ```
3. Restart service from UI or stop/start manually

---

## Security Considerations

### Production Deployment Checklist

- [ ] Change `SECRET_KEY` to a strong random value (32+ characters)
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use HTTPS with valid SSL certificate
- [ ] Update OAuth callback URLs to production domain
- [ ] Enable MongoDB authentication
- [ ] Implement rate limiting on API endpoints
- [ ] Set up firewall rules to restrict access
- [ ] Regular backups of MongoDB database
- [ ] Regular backups of Docker volumes
- [ ] Monitor resource usage (CPU, RAM, disk)
- [ ] Implement log rotation
- [ ] Review and update service root passwords

### Current Security Features

1. **OAuth-Only Authentication**: No password storage or management
2. **JWT Tokens**: Secure session management with expiration
3. **Isolated Databases**: Users cannot access other users' data
4. **Resource Limits**: Labs capped at 2 CPUs and 4GB RAM
5. **Auto-Stop Timers**: Prevents resource exhaustion
6. **Audit Logs**: All admin actions logged
7. **Role-Based Access**: Admin vs User permissions

### Known Limitations

1. **Service Root Passwords**: Hardcoded in `service_controller.py` (should be environment variables)
2. **No Password Rotation**: Service passwords are static
3. **HTTP in Development**: Use HTTPS in production
4. **No Rate Limiting**: Implement in production
5. **Single Server**: No high availability or load balancing

---

## License

**Private - Not for public distribution**

---

## Support

For issues, questions, or feature requests:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [TODO.md](TODO.md) for planned features
- Contact the development team

---

**Last Updated**: December 2025

**Version**: 2.0 (Username System Update)
