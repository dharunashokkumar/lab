# Selfmade Labs v2.0 - Quick Start Guide

Get up and running with Selfmade Labs in 5 minutes!

---

## Prerequisites

- **Docker** installed and running
- **Python 3.12+** installed
- **MongoDB** running (or Docker container)
- **Google OAuth** credentials (or GitHub OAuth)

---

## 🚀 Quick Setup

### 1. Clone and Navigate
```bash
cd C:\Users\dharu\Desktop\lab
```

### 2. Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment file
copy .env.example .env     # Windows
# OR
cp .env.example .env       # Linux/Mac

# Edit .env and add your OAuth credentials
# GOOGLE_CLIENT_ID=your-google-client-id
# GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 4. Start MongoDB (if not running)
```bash
# Using Docker
docker run -d --name selfmade-mongo -p 27017:27017 mongo:7.0
```

### 5. Build Lab Docker Images
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
```

### 6. Start the Platform
```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Access the Platform
Open browser: **http://localhost:8000/ui/login.html**

---

## 🎯 First Steps

### 1. Login
- Click "Sign in with Google" or "Sign in with GitHub"
- **First user automatically becomes admin!**

### 2. Launch Your First Lab
1. Go to Dashboard
2. Click "Launch" on "Ubuntu Essentials Lab"
3. Wait ~10 seconds for lab to start
4. Click "Open Terminal" button
5. Browser window opens with terminal!

### 3. Test Persistent Storage
```bash
# In Ubuntu terminal
echo "Hello from Ubuntu!" > test.txt
ls -la

# Stop the lab (click Stop button)
# Launch Kali Linux Lab
# Open Terminal

# In Kali terminal
cat test.txt    # Should show "Hello from Ubuntu!"
```

**✅ Success!** Your files persist across different labs!

---

## 📋 Quick Reference

### Default Credentials
- **Terminal user:** student
- **Terminal password:** student123
- **User has sudo:** Yes (passwordless)

### Available Labs
1. **Ubuntu Essentials Lab**
   - Ubuntu 22.04
   - Python, Node.js, Git, Vim, Nano
   - Development tools

2. **Kali Linux Lab**
   - Kali Linux Rolling
   - Pentesting tools: nmap, metasploit, sqlmap
   - Network tools: wireshark, burpsuite

3. **n8n Automation Lab**
   - n8n workflow automation
   - Web-based UI
   - API integrations

### Resource Limits (per lab)
- **CPU:** 2 vCPUs max
- **Memory:** 4GB RAM max
- **Auto-stop:** 30 minutes of runtime

### Shared Services Available
- MySQL (port 3306)
- PostgreSQL (port 5432)
- MongoDB (port 27018)
- Redis (port 6379)
- RabbitMQ (port 5672)

---

## 🛠️ Common Tasks

### View Running Containers
```bash
docker ps
```

### View User Volumes
```bash
docker volume ls | grep user_
```

### Stop All Labs
```bash
# From dashboard, click "Stop" on each lab
# OR manually:
docker stop $(docker ps -q --filter "name=lab_")
```

### Check Application Logs
```bash
# Logs appear in terminal where uvicorn is running
# Look for errors or warnings
```

### Rebuild Lab Images
```bash
# After modifying Dockerfiles
build-labs.bat    # Windows
./build-labs.sh   # Linux/Mac
```

---

## 🎓 Usage Tips

### Best Practices
1. **Organize your files** in `/home/student/projects/`
2. **Use Git** to backup important work
3. **Stop labs** when not in use (saves resources)
4. **Don't store secrets** in lab files (use environment variables)

### Useful Commands
```bash
# Check disk usage
df -h

# Monitor resources
htop

# Find files
find /home/student -name "*.py"

# Install packages (Ubuntu)
sudo apt update && sudo apt install <package>

# Install packages (Kali)
sudo apt update && sudo apt install <package>
```

---

## 🔧 Admin Tasks

### Access Admin Panel
1. Login as admin user (first user)
2. Click "Admin Panel" in sidebar
3. Manage users, view logs, check stats

### Create New User
1. Go to Admin Panel
2. Click "Create User"
3. Enter email, name
4. Choose role (admin/user)
5. User can login via OAuth

### Delete User
**⚠️ WARNING:** This deletes ALL user data including their Docker volume!

1. Admin Panel → User list
2. Click "Delete" next to user
3. Confirm deletion
4. User + all data is removed

### View Platform Stats
- Admin Panel shows:
  - Total users
  - Active labs
  - Active services
  - System metrics

---

## 🐛 Quick Troubleshooting

### "Connection refused" when accessing localhost:8000
- Check uvicorn is running: `ps aux | grep uvicorn`
- Restart: `uvicorn app.main:app --reload --port 8000`

### "Cannot connect to MongoDB"
- Check MongoDB is running: `docker ps | grep mongo`
- Start MongoDB: `docker start selfmade-mongo`

### "Failed to start container"
- Check Docker is running: `docker ps`
- Check image exists: `docker images | grep selfmade`
- Rebuild images: `build-labs.bat` or `./build-labs.sh`

### Lab terminal shows blank screen
- Check container logs: `docker logs <container_name>`
- Try stopping and restarting the lab

### Cannot login with OAuth
- Verify OAuth credentials in `.env`
- Check redirect URL matches: `http://localhost:8000`
- Ensure MongoDB is accessible

---

## 📚 Learn More

- **UPGRADE-GUIDE.md** - Detailed explanation of v2.0 features
- **README-TODO.md** - Original architecture plan
- **README.md** - Full platform documentation

---

## 🎉 You're All Set!

You now have a fully functional Selfmade Labs platform with:
- ✅ Shared persistent storage across labs
- ✅ Browser-based terminals (no SSH needed)
- ✅ Resource management (CPU/RAM limits)
- ✅ Multiple lab environments
- ✅ Shared database services

**Happy hacking!** 🚀
