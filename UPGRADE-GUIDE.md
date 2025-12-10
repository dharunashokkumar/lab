# Selfmade Labs v2.0 - Upgrade Guide

This guide explains the major improvements implemented in v2.0 based on the README-TODO.md architecture plan.

---

## 🎉 What's New in v2.0

### ✅ **Phase 1: Shared User Volumes** (IMPLEMENTED)
- **ONE persistent volume per user** shared across ALL their labs
- Files created in Ubuntu lab are accessible in Kali lab
- All user data survives lab restarts
- Automatic volume creation and management

### ✅ **Phase 2: Browser-Based Terminals** (IMPLEMENTED)
- **No SSH configuration needed** - everything runs in the browser
- Click "Open Terminal" button to launch web-based terminal
- Built with `ttyd` - lightweight, secure web terminal
- Works on any device with a modern browser

### ✅ **Phase 3: Resource Management** (IMPLEMENTED)
- **CPU Limits**: 2 vCPUs per lab container
- **Memory Limits**: 4GB RAM per lab container
- Prevents resource starvation
- Enables running 50+ users on 24-core server

---

## 🚀 Key Features

### 1. Shared Persistent Volumes

**How it works:**
```
User: dharuna457@gmail.com
Volume: user_dharuna457_home

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Ubuntu Lab     │     │   Kali Lab      │     │    n8n Lab      │
│                 │     │                 │     │                 │
│ /home/student ──┼─────┼─ /home/student ─┼─────┼─ /home/student  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                    user_dharuna457_home (Docker Volume)
                         Persistent Storage
```

**Benefits:**
- Download a file in Ubuntu, access it in Kali
- Share projects across different lab environments
- Data persists even when labs are stopped
- One unified workspace for all activities

### 2. Browser-Based Terminals (ttyd)

**Before (v1.0):**
```bash
# User had to configure SSH client
ssh student@localhost -p 2234
# Required VPN or port forwarding
# Complex for beginners
```

**After (v2.0):**
```
1. Click "Launch" on any lab
2. Click "Open Terminal" button
3. Browser window opens with full terminal
4. Start working immediately!
```

**Features:**
- Full terminal emulation in browser
- Copy/paste support
- Resizable window
- HTTPS-ready (when behind reverse proxy)

### 3. Resource Limits

**Configuration (automatic):**
```yaml
Each lab container gets:
  cpus: "2"           # 2 virtual CPUs
  memory: "4g"        # 4GB RAM maximum
```

**Why this matters:**
- Fair resource distribution
- No single user can crash the server
- Supports many concurrent users
- Predictable performance

---

## 📦 New Files & Components

### Backend Modules
- **`app/volume_manager.py`** - Volume creation, deletion, tracking
- **`app/lab_controller.py`** - Updated with volume mounting and resource limits
- **`app/auth.py`** - Enhanced user deletion with volume cleanup

### Docker Images
- **`labs/ubuntu-ssh/Dockerfile`** - Ubuntu 22.04 + ttyd + dev tools
- **`labs/kali-linux/Dockerfile`** - Kali Linux + ttyd + pentesting tools

### Build Scripts
- **`build-labs.bat`** - Windows build script
- **`build-labs.sh`** - Linux/Mac build script

### Frontend
- **`static/dashboard.html`** - Updated UI with "Open Terminal" buttons

---

## 🔄 Migration Steps

### Step 1: Backup Existing Data (if any)
```bash
# Backup MongoDB data
mongodump --uri="mongodb://localhost:27017/selfmade_labs" --out=backup/

# List existing lab containers
docker ps -a | grep lab_
```

### Step 2: Build New Docker Images
```bash
# Windows
build-labs.bat

# Linux/Mac
chmod +x build-labs.sh
./build-labs.sh
```

**Expected output:**
```
Building Ubuntu SSH Lab...
✓ Ubuntu SSH Lab built successfully

Building Kali Linux Lab...
✓ Kali Linux Lab built successfully

All lab images built successfully!
```

### Step 3: Update Database (Optional - Auto-migrates on startup)
If you have an existing database, the lab catalog will auto-update on first run.

To force a catalog update:
```python
# In MongoDB shell or Python
from app.db import lab_catalog

# Clear old catalog
lab_catalog.delete_many({})

# Restart the app - new catalog will seed automatically
```

### Step 4: Restart the Platform
```bash
# Stop the old version
Ctrl+C (if running)

# Start the new version
uvicorn app.main:app --reload --port 8000
```

### Step 5: Test New Features
1. Login to the platform
2. Launch Ubuntu Essentials Lab
3. Click "Open Terminal" - terminal should open in browser
4. Create a file: `echo "Hello from Ubuntu" > test.txt`
5. Stop Ubuntu lab
6. Launch Kali Linux Lab
7. Click "Open Terminal"
8. Check file exists: `cat test.txt` - should show "Hello from Ubuntu"

✅ **Success!** Your files persist across labs!

---

## 🔍 What Changed?

### Database Schema Updates

**lab_instances collection:**
```javascript
{
  // NEW FIELDS:
  "volume": "user_dharuna457_home",      // Tracks user volume
  "access_url": "http://localhost:8001",  // Direct browser access
  "resources": {
    "cpus": "2",
    "memory": "4g"
  },

  // UPDATED FIELDS:
  "access_type": "web_terminal",  // Was: "ssh"
  "port": 8001                    // Now maps to ttyd (7681 internal)
}
```

### API Response Changes

**POST /labs/start - Enhanced response:**
```json
{
  "status": "started",
  "lab_name": "Ubuntu Essentials Lab",
  "container": "lab_dharuna457_ubuntu-ssh_1234",
  "volume": "user_dharuna457_home",       // NEW
  "access_url": "http://localhost:8001",  // NEW
  "port": 8001,
  "access_type": "web_terminal",          // NEW
  "resources": {                          // NEW
    "cpus": "2",
    "memory": "4g"
  }
}
```

**GET /labs/status - Enhanced response:**
```json
[
  {
    "lab": "ubuntu-ssh",
    "lab_name": "Ubuntu Essentials Lab",
    "container": "lab_dharuna457_ubuntu-ssh_1234",
    "volume": "user_dharuna457_home",       // NEW
    "port": 8001,
    "access_url": "http://localhost:8001",  // NEW
    "access_type": "web_terminal",
    "status": "running",
    "resources": {                          // NEW
      "cpus": "2",
      "memory": "4g"
    }
  }
]
```

### Frontend Changes

**Dashboard UI:**
- "Open Terminal" button for web_terminal labs
- Volume name display
- Resource usage display (CPU/Memory limits)
- Access URL with copy button

**Before:**
```
ssh student@127.0.0.1 -p 2234
[Copy] [Stop]
```

**After:**
```
http://localhost:8001
[Copy] [Open Terminal] [Stop]
CPU: 2 cores • RAM: 4g
Volume: user_dharuna457_home
```

---

## 🎓 Usage Guide

### For Users

#### Launching a Lab
1. Go to Dashboard
2. Click "Launch" on any lab card
3. Wait for lab to start (~10 seconds)
4. Click "Open Terminal" button
5. New browser window opens with terminal

#### Using Persistent Storage
```bash
# All your files go in /home/student
cd /home/student

# Create directories
mkdir projects downloads tools

# Your work persists across:
# - Lab restarts
# - Different lab types (Ubuntu → Kali)
# - Server reboots (data stored in Docker volume)
```

#### File Organization Best Practices
```
/home/student/
├── projects/          # Your coding projects
├── downloads/         # Downloaded files
├── tools/             # Custom scripts/tools
└── .bashrc           # Your shell configuration
```

### For Admins

#### Viewing User Volumes
```bash
# List all user volumes
docker volume ls | grep user_

# Inspect specific user volume
docker volume inspect user_dharuna457_home

# Check volume size
docker system df -v | grep user_
```

#### Deleting User (with volume cleanup)
When you delete a user via Admin Panel:
1. All running labs are stopped
2. All lab containers are removed
3. **User's Docker volume is deleted** (⚠️ data loss!)
4. Database records are cleaned up

**⚠️ WARNING:** User deletion is permanent and deletes ALL user data!

#### Monitoring Resources
```bash
# Check running containers with resource limits
docker ps --format "table {{.Names}}\t{{.CPUs}}\t{{.MemUsage}}"

# Monitor real-time usage
docker stats

# Check total resource allocation
docker ps -q | xargs docker inspect --format='{{.Name}}: {{.HostConfig.NanoCpus}} CPUs, {{.HostConfig.Memory}} bytes'
```

---

## 🐛 Troubleshooting

### Lab Won't Start - "Failed to create user volume"

**Cause:** Docker daemon not running or permission issues

**Solution:**
```bash
# Check Docker is running
docker ps

# Check volume creation manually
docker volume create test_volume
docker volume rm test_volume
```

### Terminal Opens But Shows Blank Screen

**Cause:** ttyd port mapping issue

**Solution:**
1. Check container logs:
   ```bash
   docker logs lab_yourname_ubuntu-ssh_1234
   ```
2. Verify ttyd is running:
   ```bash
   docker exec lab_yourname_ubuntu-ssh_1234 ps aux | grep ttyd
   ```

### Files Not Persisting Across Labs

**Cause:** Volume not mounted correctly

**Solution:**
1. Check volume is mounted:
   ```bash
   docker inspect lab_yourname_ubuntu-ssh_1234 | grep -A 10 Mounts
   ```
2. Should show:
   ```json
   "Mounts": [
     {
       "Type": "volume",
       "Name": "user_yourname_home",
       "Source": "/var/lib/docker/volumes/user_yourname_home/_data",
       "Destination": "/home/student"
     }
   ]
   ```

### Cannot Access Lab - Port Already in Use

**Cause:** Port collision (rare with 8000-9000 range)

**Solution:**
```bash
# Stop the lab and restart
# New random port will be allocated
```

---

## 📊 Performance Notes

### Resource Planning

**Single User:**
- 1 lab = 2 vCPUs, 4GB RAM
- 2 labs = 4 vCPUs, 8GB RAM
- 3 labs = 6 vCPUs, 12GB RAM

**Server with 24 vCPUs, 64GB RAM:**
- **Conservative:** 10 concurrent labs (20 vCPUs, 40GB)
- **Moderate:** 15 concurrent labs (30 vCPUs, 60GB) - uses overcommit
- **Aggressive:** 20+ concurrent labs - relies on not all users maxing resources

**Reality:** Most users don't max out CPU constantly, so overcommit works well.

### Volume Storage

**Per User Estimate:**
- Fresh volume: ~100MB
- After development work: 500MB - 2GB
- Heavy usage: 5GB+

**100 Users:**
- Minimum: 10GB
- Average: 100GB
- Heavy: 500GB

**Recommendation:** Monitor with `docker system df -v`

---

## 🔐 Security Improvements

### Container Isolation
- Each user's containers are isolated
- Resource limits prevent DoS
- Volumes are user-specific (no cross-user access)

### Volume Security
- Volumes are named by user email (unique)
- Only user's containers can mount their volume
- Volume deletion requires admin action

### Network Security
- ttyd runs on localhost by default
- For production: Use reverse proxy (Traefik) with HTTPS
- Authentication handled by platform JWT

---

## 🚀 Next Steps (Future Phases)

### Phase 4: Reverse Proxy (Planned)
- Traefik for subdomain routing
- HTTPS with Let's Encrypt
- `dharuna457-ubuntu.selfmade.local`

### Phase 5: Enhanced Labs (Planned)
- Jupyter Notebooks environment
- VS Code Server in browser
- n8n automation platform
- Desktop environments (Apache Guacamole)

### Phase 6: Advanced Features (Planned)
- Volume file browser in UI
- Disk usage monitoring per user
- Lab templates and snapshots
- Collaboration features

---

## 📞 Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Review Docker container logs: `docker logs <container_name>`
3. Check application logs in terminal
4. Verify Docker daemon is running: `docker ps`

---

## 📝 Changelog

### v2.0.0 (December 2024)
- ✅ Shared persistent volumes per user
- ✅ Browser-based terminals (ttyd)
- ✅ Resource limits (CPU/memory)
- ✅ Volume cleanup on user deletion
- ✅ Enhanced API responses
- ✅ Improved Docker images (Ubuntu, Kali)
- ✅ Build automation scripts
- ✅ Updated UI with "Open Terminal" buttons

### v1.0.0 (Initial Release)
- OAuth authentication
- SSH-based lab access
- Basic lab management
- Service orchestration
- Admin panel

---

**Congratulations! You're now running Selfmade Labs v2.0 with all the latest improvements!** 🎉
