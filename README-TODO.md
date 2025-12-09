# Selfmade Labs Platform - Improved Architecture

**A self-hosted lab and service orchestration platform with OAuth authentication, Docker-based isolation, shared user storage, and browser-based access.**

---

## 🎯 Vision & Key Improvements

After analyzing labs.selfmade.ninja's architecture, we've identified key improvements to implement:

### **Critical Architecture Insight: Shared Storage Across Labs**

The most important discovery: **ALL labs for a single user should share the same filesystem**. When a user downloads a file in their Ubuntu lab, they should see it in their Kali lab, n8n lab, etc.

**How This Works:**
- Each user gets a **persistent Docker volume** (e.g., `user_dharuna457_home`)
- This volume is mounted to `/home/student` in **ALL** their lab containers
- Files persist across lab stops/starts
- Files are accessible across different lab types

**Example:**
```bash
# User starts Ubuntu SSH Lab
Container: lab_dharuna457_ubuntu
Mount: user_dharuna457_home:/home/student

# User downloads project.zip in Ubuntu
/home/student/project.zip

# User stops Ubuntu, starts Kali
Container: lab_dharuna457_kali
Mount: user_dharuna457_home:/home/student  # SAME VOLUME

# User can access project.zip in Kali
ls /home/student/project.zip  # File is there!
```

### **Browser-Based Terminal Access (No VPN Needed)**

Instead of SSH over VPN like labs.selfmade.ninja, we'll use **browser-based terminals**:

**Technologies:**
- **ttyd** - Lightweight web terminal (recommended)
- **wetty** - Alternative web terminal
- **Apache Guacamole** - For full desktop environments

**Why This Is Better:**
- No VPN configuration needed
- Works on any device with a browser
- Easier to secure with HTTPS
- Better user experience (click and use)

### **Resource Management**

**CPU/RAM Limits Per User:**
```yaml
# Each lab container gets:
cpus: "2"           # 2 vCPUs max
memory: "4g"        # 4GB RAM max
```

**How 24 vCPUs Can Handle 50+ Users:**
- CPU overcommitment: Most users don't max out CPU constantly
- Not all users are active simultaneously
- Proper resource limits prevent any single user from hogging resources

---

## 📊 Revised Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              Physical Server (i9-14900K, 64GB RAM)              │
├─────────────────────────────────────────────────────────────────┤
│                         Docker Host                              │
│                                                                  │
│  ┌────────────────── User: dharuna457 ──────────────────────┐  │
│  │                                                            │  │
│  │  Docker Volume: user_dharuna457_home (Persistent)         │  │
│  │  ├── /home/student/projects/                              │  │
│  │  ├── /home/student/downloads/                             │  │
│  │  └── /home/student/.bashrc                                │  │
│  │                          ▲                                 │  │
│  │                          │                                 │  │
│  │     ┌────────────────────┼────────────────────┐           │  │
│  │     │                    │                    │           │  │
│  │  ┌──▼────────┐    ┌──────▼───┐    ┌─────────▼──┐        │  │
│  │  │  Ubuntu    │    │   Kali   │    │    n8n     │        │  │
│  │  │  SSH Lab   │    │  Linux   │    │    Lab     │        │  │
│  │  │            │    │          │    │            │        │  │
│  │  │ ttyd:8001  │    │ttyd:8002 │    │Port: 5678  │        │  │
│  │  │ (Terminal) │    │(Terminal)│    │  (Web UI)  │        │  │
│  │  └────────────┘    └──────────┘    └────────────┘        │  │
│  │                                                            │  │
│  │  ALL containers mount: user_dharuna457_home:/home/student │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────── User: john_doe ─────────────────────────┐  │
│  │  Docker Volume: user_john_doe_home                         │  │
│  │  └── Separate isolated storage                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────── Shared Database Containers ──────────────────┐  │
│  │  selfmade-mysql-shared      (Port 3306)                    │  │
│  │  selfmade-postgresql-shared (Port 5432)                    │  │
│  │  selfmade-mongodb-shared    (Port 27018)                   │  │
│  │  selfmade-redis-shared      (Port 6379)                    │  │
│  │  selfmade-rabbitmq-shared   (Port 5672)                    │  │
│  │                                                             │  │
│  │  Each user gets a separate DATABASE in shared container    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────── Reverse Proxy (Traefik) ───────────────────┐  │
│  │  Routes:                                                     │  │
│  │  - dharuna457-ubuntu.selfmade.local → ttyd:8001            │  │
│  │  - dharuna457-kali.selfmade.local   → ttyd:8002            │  │
│  │  - dharuna457-n8n.selfmade.local    → n8n:5678             │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### 1. **User Volume Management**

```python
# app/volume_manager.py

import subprocess

def get_user_volume_name(user_email: str) -> str:
    """Generate consistent volume name for user"""
    # dharuna457@gmail.com -> user_dharuna457_home
    username = user_email.split('@')[0].replace('.', '_')
    return f"user_{username}_home"

def create_user_volume_if_not_exists(user_email: str):
    """Create persistent volume for user if it doesn't exist"""
    volume_name = get_user_volume_name(user_email)
    
    # Check if volume exists
    check_cmd = f"docker volume ls -q -f name={volume_name}"
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if not result.stdout.strip():
        # Create volume
        create_cmd = f"docker volume create {volume_name}"
        subprocess.run(create_cmd, shell=True, check=True)
        print(f"Created volume: {volume_name}")
    
    return volume_name

def delete_user_volume(user_email: str):
    """Delete user's persistent volume (admin action)"""
    volume_name = get_user_volume_name(user_email)
    delete_cmd = f"docker volume rm {volume_name}"
    subprocess.run(delete_cmd, shell=True)
```

### 2. **Lab Controller with Shared Storage**

```python
# app/lab_controller.py (IMPROVED)

def start_lab(user_email: str, lab_id: str):
    # Get or create user's persistent volume
    volume_name = create_user_volume_if_not_exists(user_email)
    
    # Generate unique container name
    container_name = f"lab_{user_email.split('@')[0]}_{lab_id}_{random.randint(1000,9999)}"
    
    # Get lab configuration
    lab_config = lab_catalog.find_one({"id": lab_id})
    
    # Allocate port for ttyd
    port = random.randint(8000, 9000)
    
    # Build Docker command with SHARED VOLUME
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        
        # CRITICAL: Mount user's persistent volume
        "-v", f"{volume_name}:/home/student",
        
        # Resource limits
        "--cpus", "2",
        "--memory", "4g",
        
        # Port mapping (ttyd web terminal)
        "-p", f"{port}:7681",
        
        # Lab image
        lab_config["image"]
    ]
    
    subprocess.run(cmd, check=True)
    
    # Record in database
    instances.insert_one({
        "user_email": user_email,
        "lab_id": lab_id,
        "container": container_name,
        "volume": volume_name,  # Track which volume is used
        "port": port,
        "access_url": f"http://localhost:{port}",
        "status": "running",
        "started_at": datetime.utcnow()
    })
    
    return {
        "status": "started",
        "access_url": f"http://localhost:{port}",
        "volume": volume_name
    }
```

### 3. **Lab Docker Images with ttyd**

```dockerfile
# labs/ubuntu-ssh/Dockerfile (IMPROVED)

FROM ubuntu:22.04

# Install essential tools
RUN apt update && apt install -y \
    sudo \
    curl \
    wget \
    git \
    vim \
    nano \
    build-essential \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd (web terminal)
RUN curl -L https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 \
    -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# Create student user
RUN useradd -m -s /bin/bash student && \
    echo "student:student123" | chpasswd && \
    echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /home/student
USER student

# Expose ttyd port
EXPOSE 7681

# Start ttyd with bash
CMD ["ttyd", "-p", "7681", "-W", "bash"]
```

### 4. **Frontend Access**

```javascript
// static/js/lab-access.js

function openLabTerminal(labId, port) {
    // Open lab terminal in new window
    const terminalUrl = `http://localhost:${port}`;
    window.open(terminalUrl, `lab_${labId}`, 'width=1200,height=800');
}

// In dashboard.html
function renderRunningLab(lab) {
    return `
        <div class="card">
            <h3>${lab.lab_name}</h3>
            <p>Status: <span class="badge badge-success">Running</span></p>
            <p>Volume: ${lab.volume}</p>
            
            <div class="button-group">
                <button class="btn btn-primary" 
                        onclick="openLabTerminal('${lab.lab_id}', ${lab.port})">
                    <span class="material-icons-round">terminal</span>
                    Open Terminal
                </button>
                
                <button class="btn btn-secondary" 
                        onclick="stopLab('${lab.lab_id}')">
                    <span class="material-icons-round">stop</span>
                    Stop Lab
                </button>
            </div>
        </div>
    `;
}
```

---

## 🗂️ Database Schema Updates

### Updated `lab_instances` Collection

```javascript
{
  "_id": ObjectId("..."),
  "user_email": "dharuna457@gmail.com",
  "lab_id": "ubuntu-ssh",
  "lab_name": "Ubuntu SSH Lab",
  "container": "lab_dharuna457_ubuntu_1234",
  "volume": "user_dharuna457_home",        // NEW: Track volume
  "port": 8001,                             // ttyd web terminal port
  "access_url": "http://localhost:8001",    // NEW: Direct access URL
  "access_type": "web_terminal",            // NEW: Type of access
  "status": "running",
  "started_at": ISODate("2025-01-01T12:00:00Z"),
  
  // Resource limits
  "resources": {
    "cpus": "2",
    "memory": "4g"
  }
}
```

---

## 🚀 Key Features

### ✅ Implemented (Current)
- OAuth authentication (Google, GitHub)
- JWT session management
- MongoDB database
- Docker-based labs
- Shared database services (MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ)
- Admin panel
- Notifications system
- Auto-stop timers

### 🎯 To Implement (Priority)

#### **High Priority**
1. **Shared User Volumes**
   - Create persistent volume per user
   - Mount volume across all user's labs
   - Implement volume cleanup on user deletion

2. **Browser-Based Terminal Access**
   - Replace SSH with ttyd in lab images
   - Update frontend to open terminals in browser
   - Implement secure access controls

3. **Resource Limits**
   - Add CPU/memory limits to all containers
   - Implement resource monitoring
   - Show resource usage in admin panel

#### **Medium Priority**
4. **Reverse Proxy (Traefik)**
   - Route user labs through subdomains
   - Enable HTTPS with Let's Encrypt
   - Implement authentication middleware

5. **Enhanced Lab Images**
   - Kali Linux with penetration testing tools
   - n8n automation platform
   - Jupyter Notebooks environment
   - VS Code Server environment

6. **Volume Management UI**
   - Show user's disk usage
   - Browse files in volume
   - Download/upload files to volume

#### **Low Priority**
7. **Desktop Environments**
   - Apache Guacamole for GUI access
   - VNC-based desktops
   - Remote desktop protocols

8. **Collaboration Features**
   - Share labs with other users
   - Multi-user lab sessions
   - Real-time collaboration tools

---

## 🏗️ Revised Tech Stack

### Backend (No Changes)
- Python 3.12
- FastAPI
- MongoDB
- Docker Python SDK
- PyJWT for authentication

### Frontend (No Changes)
- Vanilla JavaScript
- HTML5/CSS3
- Material Icons
- Google Fonts

### New Infrastructure Components
- **ttyd**: Web-based terminal emulator
- **Traefik**: Reverse proxy and load balancer (planned)
- **Docker Volumes**: Persistent user storage
- **Apache Guacamole**: Desktop environment access (planned)

---

## 📝 Implementation Roadmap

### Phase 1: Shared Volumes (Week 1)
- [ ] Create volume management module
- [ ] Update lab_controller.py to use volumes
- [ ] Test volume persistence across lab restarts
- [ ] Update database schema

### Phase 2: Browser Terminals (Week 2)
- [ ] Build Ubuntu image with ttyd
- [ ] Build Kali image with ttyd
- [ ] Update frontend to open terminals
- [ ] Test terminal functionality

### Phase 3: Resource Management (Week 3)
- [ ] Add CPU/memory limits to containers
- [ ] Implement resource monitoring
- [ ] Create admin resource dashboard
- [ ] Add usage alerts

### Phase 4: Reverse Proxy (Week 4)
- [ ] Set up Traefik container
- [ ] Configure subdomain routing
- [ ] Implement HTTPS/SSL
- [ ] Test authentication flow

### Phase 5: Enhanced Labs (Week 5-6)
- [ ] Build Kali Linux image
- [ ] Build n8n image
- [ ] Build Jupyter image
- [ ] Build VS Code Server image

---

## 🔒 Security Considerations

### Current Security
- OAuth 2.0 authentication only (no passwords)
- JWT tokens with expiration
- User isolation via Docker containers
- Admin role enforcement

### Additional Security Needed
- **Volume Isolation**: Ensure users can't access other users' volumes
- **Network Isolation**: Docker networks per user
- **Rate Limiting**: Prevent abuse of lab creation
- **HTTPS Enforcement**: SSL/TLS for all traffic
- **Content Security Policy**: XSS protection
- **Container Security**: Run containers as non-root

---

## 💡 Lessons from labs.selfmade.ninja

### What They Do Well
1. **Shared Storage**: All labs share same user home directory
2. **VPN-Free Access**: No VPN needed (they use VPN but we'll use web terminals)
3. **Resource Management**: Handle 50+ users on 24 cores
4. **Persistent Data**: User files survive lab restarts

### What We'll Do Better
1. **Browser-Based**: No SSH needed, everything in browser
2. **Better UX**: Cleaner UI, easier lab access
3. **Resource Monitoring**: Show users their resource usage
4. **File Management**: Built-in file browser for volumes
5. **Collaboration**: Share labs and work together

### What We'll Avoid
1. **VPN Complexity**: We use browser terminals instead
2. **SSH Key Management**: OAuth + web terminals = simpler
3. **Complex Networking**: Docker volumes + Traefik = cleaner

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_volume_manager.py
def test_create_user_volume():
    volume = create_user_volume_if_not_exists("test@example.com")
    assert volume == "user_test_home"
    
def test_volume_persistence():
    # Start lab, create file
    start_lab("test@example.com", "ubuntu-ssh")
    # Stop lab
    stop_lab("test@example.com", "ubuntu-ssh")
    # Start different lab, check file exists
    start_lab("test@example.com", "kali-linux")
    # File should be accessible
```

### Integration Tests
- Test lab startup with volume mounting
- Test file creation and persistence
- Test multi-lab volume sharing
- Test resource limit enforcement

### Load Tests
- Simulate 50 concurrent users
- Monitor CPU/memory usage
- Test auto-stop timers
- Verify no resource leaks

---

## 📚 API Endpoints (Updated)

### Labs

#### Start Lab
```http
POST /labs/start
Content-Type: application/json
Authorization: Bearer {token}

{
  "lab_id": "ubuntu-ssh"
}

Response:
{
  "status": "started",
  "lab_name": "Ubuntu SSH Lab",
  "container": "lab_dharuna457_ubuntu_1234",
  "volume": "user_dharuna457_home",
  "access_url": "http://localhost:8001",
  "port": 8001
}
```

#### Get Lab Status
```http
GET /labs/status
Authorization: Bearer {token}

Response:
[
  {
    "lab_id": "ubuntu-ssh",
    "lab_name": "Ubuntu SSH Lab",
    "container": "lab_dharuna457_ubuntu_1234",
    "volume": "user_dharuna457_home",
    "access_url": "http://localhost:8001",
    "status": "running",
    "started_at": "2025-01-01T12:00:00Z",
    "resources": {
      "cpus": "2",
      "memory": "4g"
    }
  }
]
```

---

## 🎓 For Future AI Assistants

When implementing this platform, remember:

1. **Shared Volumes Are Critical**: Every user must have ONE persistent volume shared across ALL their labs. This is not optional.

2. **Browser > SSH**: Use ttyd or similar for web terminals. Don't make users configure SSH.

3. **Resource Limits Always**: Every container MUST have CPU and memory limits. No exceptions.

4. **User Isolation**: While volumes are shared per-user, they must be isolated between users.

5. **Start Simple**: Get basic ttyd terminal working before adding Guacamole desktops.

6. **Test Persistence**: Always test that files created in Lab A are accessible in Lab B for the same user.

7. **Monitor Resources**: Track CPU/memory usage per user and show in admin panel.

8. **Clean Up Properly**: When deleting users, remember to delete their Docker volumes too.

---

## 🛠️ Quick Start for Development

```bash
# 1. Clone repository
git clone <repo-url>
cd lab

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start MongoDB
docker run -d --name selfmade-mongo -p 27017:27017 mongo:7.0

# 5. Configure OAuth (edit .env)
cp .env.example .env
# Add your Google and GitHub OAuth credentials

# 6. Build lab images
cd labs/ubuntu-ssh
docker build -t selfmade/ubuntu-ssh .
cd ../..

# 7. Start server
uvicorn app.main:app --reload --port 8000

# 8. Access platform
# Open browser: http://localhost:8000/ui/login.html
```

---

## 📞 Support & Contact

For questions or issues:
- Check TROUBLESHOOTING.md first
- Review this README thoroughly
- Test with single user before scaling
- Monitor Docker logs for errors

---

**Version**: 2.0.0 (Improved Architecture)  
**Last Updated**: December 2025  
**Status**: In Development (Phase 1: Shared Volumes)