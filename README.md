# Selfmade Labs Platform

**A self-hosted lab and service orchestration platform with OAuth authentication, Docker-based isolation, and a Google Drive-inspired UI.**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Features](#features)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Setup Instructions](#setup-instructions)
8. [Running the Platform](#running-the-platform)
9. [OAuth Configuration](#oauth-configuration)
10. [Project Structure](#project-structure)
11. [Development Workflow](#development-workflow)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Selfmade Labs is a production-ready platform for orchestrating isolated lab environments and database services. Users authenticate via OAuth (Google/GitHub), launch containerized labs (Ubuntu SSH, Kali Linux, n8n), start database services (MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ), and receive real-time notifications about their resources.

**Key Characteristics:**
- **OAuth-Only Authentication**: No username/password - Google and GitHub OAuth only
- **Email-Based Identity**: Users identified by email address across the platform
- **Docker Orchestration**: All labs and services run in isolated Docker containers
- **Auto-Stop Timers**: Labs auto-stop after 30 minutes, services after 60 minutes
- **Google Drive UI**: Minimal, clean interface with auto dark/light theme
- **Real-Time Notifications**: Users notified when labs/services start, stop, or expire
- **Admin Panel**: Full user management, audit logs, and platform statistics

---

## Architecture

### High-Level Overview

```
┌─────────────────┐
│   Browser       │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │ HTTPS/HTTP
         │ JWT Bearer Token
         ▼
┌─────────────────────────────────────┐
│       FastAPI Backend               │
│  ┌──────────────────────────────┐  │
│  │  Authentication (OAuth 2.0)  │  │
│  │  - Google OAuth              │  │
│  │  - GitHub OAuth              │  │
│  │  - JWT Token Generation      │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Lab Controller              │  │
│  │  - Docker container mgmt     │  │
│  │  - Port allocation           │  │
│  │  - Auto-stop timers          │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Service Controller          │  │
│  │  - Database services         │  │
│  │  - Credential generation     │  │
│  │  - Connection strings        │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Notification System         │  │
│  │  - Event-driven notifications│  │
│  │  - Unread count tracking     │  │
│  └──────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │
        ┌─────┴──────┐
        │            │
        ▼            ▼
┌──────────────┐  ┌──────────────────┐
│   MongoDB    │  │  Docker Engine   │
│              │  │                  │
│ - users      │  │ ┌──────────────┐ │
│ - labs       │  │ │ Lab Containers│ │
│ - services   │  │ │ - Ubuntu SSH │ │
│ - notifs     │  │ │ - Kali Linux │ │
│ - audit_logs │  │ │ - n8n        │ │
│ - catalogs   │  │ └──────────────┘ │
└──────────────┘  │ ┌──────────────┐ │
                  │ │Service Ctrs  │ │
                  │ │ - MySQL      │ │
                  │ │ - PostgreSQL │ │
                  │ │ - MongoDB    │ │
                  │ │ - Redis      │ │
                  │ │ - RabbitMQ   │ │
                  │ └──────────────┘ │
                  └──────────────────┘
```

### Component Breakdown

#### 1. Frontend (Static Files)
- **Location**: `static/` directory
- **Served By**: FastAPI static file mounting at `/ui`
- **Theme System**: CSS custom properties with auto/light/dark modes
- **API Communication**: Centralized `api.js` with JWT token management
- **Pages**:
  - `login.html` - OAuth authentication
  - `dashboard.html` - Labs, services, stats, notifications
  - `services.html` - Service management with credentials
  - `profile.html` - User profile and statistics
  - `settings.html` - Theme and notification preferences
  - `admin.html` - User management, audit logs, platform stats

#### 2. Backend (FastAPI)
- **Location**: `app/` directory
- **Framework**: FastAPI with async/await
- **Authentication**: Authlib for OAuth 2.0, JWT for session management
- **Modules**:
  - `main.py` - FastAPI app, 40+ API endpoints
  - `auth.py` - OAuth flows, JWT encoding/decoding, user management
  - `lab_controller.py` - Docker lab orchestration
  - `service_controller.py` - Database service management
  - `notifications.py` - Notification CRUD operations
  - `db.py` - MongoDB collections and seeding

#### 3. Database (MongoDB)
- **Collections**: 7 total
  - `users` - User accounts (email-based)
  - `lab_instances` - Running lab state
  - `service_instances` - Running service state
  - `notifications` - User notifications
  - `audit_logs` - Admin action logs
  - `lab_catalog` - Available labs
  - `service_catalog` - Available services

#### 4. Container Orchestration (Docker)
- **Lab Containers**: SSH-accessible, single user limit
- **Service Containers**: Multiple concurrent per user
- **Port Management**: Dynamic allocation (8000-9000 range)
- **Lifecycle**: Auto-stop timers prevent resource leaks

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.115.6 | Web framework |
| Uvicorn | 0.34.0 | ASGI server |
| PyMongo | 4.10.1 | MongoDB driver |
| Authlib | 1.3.0 | OAuth 2.0 client |
| PyJWT | 2.10.1 | JWT encoding/decoding |
| python-dotenv | 1.0.0 | Environment config |
| httpx | 0.27.0 | Async HTTP client (OAuth) |
| email-validator | 2.1.1 | Email validation |

### Frontend
| Technology | Purpose |
|------------|---------|
| HTML5 | Structure |
| CSS3 (Custom Properties) | Theming system |
| Vanilla JavaScript | Interactivity |
| Material Icons Round | Iconography |
| Google Fonts (Google Sans, Roboto) | Typography |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| MongoDB 7.0 | Database |
| Docker Engine | Container runtime |
| Git | Version control |

---

## Features

### Authentication
- **OAuth 2.0 Only**: Google and GitHub providers
- **First User Admin**: Automatic admin role assignment
- **JWT Sessions**: 24-hour token expiration
- **Email-Based**: Users identified by email (not username)

### Labs
- **3 Lab Types**: Ubuntu SSH, Kali Linux, n8n
- **One Lab Per User**: Only one active lab at a time
- **SSH Access**: Dynamic port allocation with credentials
- **Auto-Stop**: 30-minute automatic cleanup
- **Docker Images**: Pre-built or custom images

### Services
- **5 Database Types**: MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ
- **Multiple Concurrent**: Users can run multiple services
- **Auto-Generated Credentials**: Random passwords for MySQL/PostgreSQL
- **Connection Strings**: Ready-to-use connection info
- **Auto-Stop**: 60-minute automatic cleanup

### Notifications
- **Event-Driven**: Lab/service lifecycle notifications
- **Unread Tracking**: Badge with unread count
- **Mark as Read**: Individual or bulk operations
- **Real-Time Updates**: 5-second polling interval

### Admin Panel
- **User Management**: Create, update role, delete users
- **Audit Logs**: Track all admin actions with timestamps
- **Platform Stats**: Total users, active labs, active services
- **Role Enforcement**: Admin-only access to panel

### UI/UX
- **Google Drive Aesthetic**: Minimal, clean, professional
- **Theme System**: Auto (system), Light, Dark modes
- **CSS Custom Properties**: Consistent design tokens
- **Responsive**: Works on desktop and mobile
- **Sidebar Navigation**: Persistent across pages

---

## Database Schema

### `users` Collection
```javascript
{
  "_id": ObjectId("..."),
  "email": "user@example.com",              // Primary identifier
  "full_name": "John Doe",
  "avatar_url": "https://...",
  "role": "user",                           // "user" or "admin"
  "oauth_provider": "google",               // "google" or "github"
  "oauth_id": "1234567890",                 // OAuth provider user ID
  "theme_preference": "auto",               // "auto", "light", "dark"
  "notifications_enabled": true,
  "created_at": ISODate("2025-01-01T00:00:00Z"),
  "last_login": ISODate("2025-01-01T12:00:00Z")
}
```

### `lab_instances` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_email": "user@example.com",
  "lab": "ubuntu-ssh",                      // Lab ID from catalog
  "lab_name": "Ubuntu SSH Lab",
  "container": "lab_user_example_com",      // Docker container name
  "port": 2283,                             // SSH port
  "status": "running",
  "started_at": ISODate("2025-01-01T12:00:00Z")
}
```

### `service_instances` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_email": "user@example.com",
  "service": "mysql",                       // Service ID from catalog
  "service_name": "MySQL 8.0",
  "container": "service_mysql_abc123",
  "port": 8306,                             // External port
  "credentials": {
    "username": "root",
    "password": "RandomPass123!",
    "database": "testdb"
  },
  "connection_info": {
    "host": "localhost",
    "port": 8306,
    "connection_string": "mysql://root:RandomPass123!@localhost:8306/testdb"
  },
  "status": "running",
  "started_at": ISODate("2025-01-01T12:00:00Z")
}
```

### `notifications` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_email": "user@example.com",
  "type": "lab_started",                    // Event type
  "title": "Lab Started",
  "message": "Your Ubuntu SSH Lab is ready",
  "metadata": {                             // Optional context
    "lab_id": "ubuntu-ssh",
    "port": 2283
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
  "action": "USER_CREATED",                 // Action type
  "details": {                              // Action-specific data
    "target_email": "newuser@example.com",
    "role": "user"
  },
  "timestamp": ISODate("2025-01-01T12:00:00Z")
}
```

### `lab_catalog` Collection
```javascript
{
  "_id": ObjectId("..."),
  "id": "ubuntu-ssh",
  "name": "Ubuntu SSH Lab",
  "description": "Ubuntu 22.04 with SSH access",
  "image": "selfmade/ubuntu-ssh",           // Docker image
  "port": 22                                // Internal port to map
}
```

### `service_catalog` Collection
```javascript
{
  "_id": ObjectId("..."),
  "id": "mysql",
  "name": "MySQL 8.0",
  "description": "MySQL relational database",
  "image": "mysql:8",
  "port": 3306,
  "env_template": {                         // Environment variables
    "MYSQL_ROOT_PASSWORD": "{{password}}",
    "MYSQL_DATABASE": "testdb"
  }
}
```

---

## API Endpoints

### Authentication (`/auth/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Initiate Google OAuth flow |
| GET | `/auth/google/callback` | Handle Google OAuth callback |
| GET | `/auth/github` | Initiate GitHub OAuth flow |
| GET | `/auth/github/callback` | Handle GitHub OAuth callback |
| POST | `/auth/logout` | Logout user (optional cleanup) |

### User Profile (`/me`, `/profile/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me` | Get current user profile |
| PUT | `/profile` | Update profile (full_name, theme, notifications) |
| GET | `/profile/stats` | Get user statistics |

### Labs (`/labs/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/labs` | Get lab catalog |
| POST | `/labs/start` | Start a lab |
| POST | `/labs/stop` | Stop a lab |
| GET | `/labs/status` | Get running labs for user |

### Services (`/services/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/services/catalog` | Get service catalog |
| POST | `/services/start` | Start a service |
| POST | `/services/stop` | Stop a service |
| GET | `/services/status` | Get running services for user |
| GET | `/services/{service_id}/credentials` | Get service credentials |

### Notifications (`/notifications/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | Get user notifications |
| GET | `/notifications/unread-count` | Get unread count |
| POST | `/notifications/{id}/read` | Mark notification as read |
| POST | `/notifications/read-all` | Mark all as read |
| DELETE | `/notifications/{id}` | Delete notification |

### Admin (`/admin/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/users` | Create user |
| GET | `/admin/users` | Get all users |
| PUT | `/admin/users/{email}/role` | Update user role |
| DELETE | `/admin/users/{email}` | Delete user |
| GET | `/admin/audit-logs` | Get audit logs |
| GET | `/admin/stats` | Get platform statistics |

---

## Setup Instructions

### Prerequisites
- **Python 3.12+**
- **Docker Desktop** (Windows) or Docker Engine (Linux)
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
docker run -d \
  --name selfmade-mongo \
  -p 27017:27017 \
  mongo:7.0
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and fill in OAuth credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# OAuth Credentials (Get these from Google Cloud Console & GitHub)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Application Security
SECRET_KEY=XsjnXM0yCZm4gQjUwrWrjavwQgkypBzJPDd4lLJVM-0

# Database
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=selfmade_labs

# OAuth Callback URLs
OAUTH_CALLBACK_BASE_URL=http://localhost:8000

# Application Settings
ENVIRONMENT=development
DEBUG=True
```

### 6. Run Database Migration (Optional)
If migrating from old username-based system:
```bash
python -m app.migrate_db
```

### 7. Build Lab Docker Images
```bash
# Ubuntu SSH Lab
cd labs/ubuntu-ssh
docker build -t selfmade/ubuntu-ssh .
cd ../..
```

---

## Running the Platform

### Start the Server
```bash
# Activate virtual environment (if not already)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### Access the Platform
Open browser and navigate to:
```
http://localhost:8000/ui/login.html
```

### Server Output
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## OAuth Configuration

### Google Cloud Console Setup

1. **Create Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project: "Selfmade Labs"

2. **Enable OAuth Consent Screen**
   - OAuth consent screen → External
   - App name: "Selfmade Labs"
   - Add scopes: `email`, `profile`, `openid`

3. **Create OAuth Client ID**
   - Credentials → Create Credentials → OAuth Client ID
   - Application type: Web application
   - Authorized redirect URIs:
     ```
     http://localhost:8000/auth/google/callback
     ```
   - Copy Client ID and Client Secret to `.env`

### GitHub OAuth App Setup

1. **Create OAuth App**
   - Go to GitHub Settings → Developer settings → OAuth Apps
   - New OAuth App

2. **Configure App**
   - Application name: "Selfmade Labs"
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL:
     ```
     http://localhost:8000/auth/github/callback
     ```
   - Generate new client secret
   - Copy Client ID and Client Secret to `.env`

---

## Project Structure

```
lab/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, all endpoints
│   ├── auth.py              # OAuth & JWT authentication
│   ├── db.py                # MongoDB collections & seeding
│   ├── lab_controller.py   # Lab orchestration
│   ├── service_controller.py  # Service orchestration
│   ├── notifications.py     # Notification system
│   └── migrate_db.py        # Database migration script
├── static/
│   ├── login.html           # OAuth login page
│   ├── dashboard.html       # Main dashboard
│   ├── services.html        # Service management
│   ├── profile.html         # User profile
│   ├── settings.html        # User settings
│   ├── admin.html           # Admin panel
│   ├── css/
│   │   └── theme.css        # Design system & theming
│   └── js/
│       ├── theme.js         # Theme management
│       └── api.js           # API client with JWT
├── labs/
│   └── ubuntu-ssh/
│       ├── Dockerfile
│       └── setup.sh
├── .env                     # Environment configuration
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## Development Workflow

### Git Workflow
```bash
# Make changes
git add .
git commit -m "feat: add feature X"
git push origin main
```

### Database Reset
```bash
# Drop database
docker exec -it selfmade-mongo mongosh
> use selfmade_labs
> db.dropDatabase()
> exit

# Restart server (will re-seed)
uvicorn app.main:app --reload
```

### View Logs
```bash
# MongoDB logs
docker logs selfmade-mongo

# Server logs (in terminal)
```

### Testing API
```bash
# Get lab catalog (requires auth)
curl -H "Authorization: Bearer <token>" http://localhost:8000/labs

# Health check
curl http://localhost:8000/
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pymongo'"
**Solution**: Activate virtual environment
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux
```

### Issue: "Cannot connect to MongoDB"
**Solution**: Ensure MongoDB container is running
```bash
docker ps | grep mongo
docker start selfmade-mongo
```

### Issue: "OAuth error: redirect_uri_mismatch"
**Solution**: Check callback URLs in Google/GitHub match `.env`
```
Google: http://localhost:8000/auth/google/callback
GitHub: http://localhost:8000/auth/github/callback
```

### Issue: "Port 8000 already in use"
**Solution**: Kill existing process or use different port
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

### Issue: "UnicodeEncodeError" in migration script
**Solution**: Already fixed - uses `[OK]` instead of Unicode symbols

### Issue: "docker: command not found"
**Solution**: Install Docker Desktop (Windows) or Docker Engine (Linux)

### Issue: Lab won't start
**Solution**: Check Docker image exists
```bash
docker images | grep selfmade
# If missing, rebuild image
cd labs/ubuntu-ssh
docker build -t selfmade/ubuntu-ssh .
```

---

## License

Private - Not for public distribution

---

## Support

For issues or questions, contact the development team or open an issue in the repository.

---

**Last Updated**: December 2025
