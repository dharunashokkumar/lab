# TODO.md - Service Architecture & Username System Improvements

## 🎯 Objective

1. **Keep shared service containers** (current architecture is correct for RAM efficiency)
2. **Remove "student" username** - use actual usernames derived from email
3. **Create TODO.md files** for AI context instead of code dumps

---

## ✅ Current Service Architecture is CORRECT

**Your current shared container approach is optimal for RAM efficiency:**

```
✅ KEEP THIS:
┌─────────────────────────────────────────┐
│  selfmade-mysql-shared (ONE container)  │
│  ├── user_abc_db (User A)               │
│  ├── user_def_db (User B)               │
│  └── user_xyz_db (User C)               │
│  RAM: ~500MB total                      │
└─────────────────────────────────────────┘

VS

❌ DON'T DO THIS (per-user containers):
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ User A MySQL │ │ User B MySQL │ │ User C MySQL │
│ RAM: 500MB   │ │ RAM: 500MB   │ │ RAM: 500MB   │
└──────────────┘ └──────────────┘ └──────────────┘
Total: 1.5GB for 3 users!
```

**Recommendation:** Keep `app/service_controller.py` as-is (shared containers).

---

## 🔧 CRITICAL CHANGES NEEDED

### 1. Remove "student" Username System

**Problem:**
```
Current: All labs use "student" username
/home/student/  ❌ Same for everyone

Needed: Each user has their own username
/home/dharuna457/  ✅ Unique per user
/home/john_doe/    ✅ Unique per user
```

**Files to modify:**
- `labs/ubuntu-ssh/Dockerfile`
- `labs/kali-linux/Dockerfile`
- `app/lab_controller.py`
- `app/volume_manager.py`

---

## 📋 TODO #1: Update Volume Manager for Username-Based Volumes

**File:** `app/volume_manager.py`

**Current behavior:**
```python
def get_user_volume_name(user_email: str) -> str:
    username = user_email.split('@')[0].replace('.', '_')
    return f"user_{username}_home"  # ✅ Already correct!
```

**Mount path (WRONG):**
```python
# Current: Always mounts to /home/student
"-v", f"{volume_name}:/home/student"  # ❌ 

# Should be: Mount to /home/{username}
"-v", f"{volume_name}:/home/{username}"  # ✅
```

**Action:** Add function to extract clean username
```python
def get_username_from_email(user_email: str) -> str:
    """
    Extract username from email for Linux username.
    dharuna457@gmail.com -> dharuna457
    john.doe@company.com -> john_doe
    """
    # TODO: Implement this
    # 1. Split email at '@'
    # 2. Replace dots with underscores
    # 3. Return sanitized username
```

---

## 📋 TODO #2: Update Lab Controller for Dynamic Usernames

**File:** `app/lab_controller.py`

**Current mount (WRONG):**
```python
"-v", f"{volume_name}:/home/student"  # ❌ Hardcoded "student"
```

**New mount (CORRECT):**
```python
username = get_username_from_email(user_email)
"-v", f"{volume_name}:/home/{username}"  # ✅ Dynamic username
```

**Additional changes needed:**
1. Pass username to container as environment variable
2. Container should create user dynamically (not hardcode "student")

**Action:**
```
TODO: Update start_lab() function
1. Import: from app.volume_manager import get_username_from_email
2. Extract: username = get_username_from_email(user_email)
3. Mount: "-v", f"{volume_name}:/home/{username}"
4. Pass env var: "-e", f"USERNAME={username}"
```

---

## 📋 TODO #3: Update Dockerfiles to Accept Dynamic Username

**Files:** 
- `labs/ubuntu-ssh/Dockerfile`
- `labs/kali-linux/Dockerfile`

**Current approach (WRONG):**
```dockerfile
# Hardcoded "student" user
RUN useradd -m -s /bin/bash student
USER student
WORKDIR /home/student
```

**New approach (CORRECT):**
```dockerfile
# Accept USERNAME as build arg OR runtime env var
# Create user dynamically on container start
# Use entrypoint script
```

**Action:**
```
TODO: Create entrypoint script approach
1. Create: labs/ubuntu-ssh/entrypoint.sh
2. Script should:
   - Check if USERNAME env var exists
   - Create user: useradd -m -s /bin/bash $USERNAME
   - Set password: echo "$USERNAME:password123" | chpasswd
   - Give sudo: echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
   - Switch to user: su - $USERNAME
   - Start ttyd as that user
3. Update Dockerfile to use ENTRYPOINT
```

---

## 📋 TODO #4: Alternative Approach - Build-Time Username (Simpler)

**Instead of runtime username, use generic approach:**

**Keep "student" but make volume work for any username:**

```
Option A (Current):
Mount: /home/student
Problem: All users share "student" name in terminal

Option B (Recommended):
Mount: /workspace
Benefit: Clear it's a shared workspace
User: student (generic)
Terminal shows: student@ubuntu:/workspace$ 
```

**Or keep flexibility:**
```
Option C (Best):
Mount: /home/labuser
User: labuser (generic but not "student")
All users see "labuser@ubuntu:/home/labuser$"
But files are isolated by volume
```

**Action:**
```
TODO: Decide on approach
1. Dynamic username (complex, needs entrypoint.sh)
2. Generic "labuser" (simple, just rename)
3. Workspace mount (simplest, no home dir)

Recommendation: Go with Option 2 (labuser)
- Easy to implement
- Still isolated by volume
- Professional name
```

---

## 📋 TODO #5: Update Service Architecture Documentation

**Current issue:** README-TODO.md says services should be isolated per-user.

**Action:**
```
TODO: Update README-TODO.md
1. Remove section about "isolated service containers"
2. Add section explaining RAM efficiency of shared containers
3. Document why shared is better:
   - MySQL shared: 500MB RAM
   - MySQL per-user (50 users): 25GB RAM!
   - Shared is 50x more efficient
```

---

## 📋 TODO #6: Improve Service Security (Keep Shared Architecture)

**Current security issues in shared containers:**
1. Hardcoded root password
2. No password rotation
3. Users might guess pattern of database names

**Action:**
```
TODO: Security improvements (without changing architecture)
1. Generate random root password per shared container
2. Store root passwords in MongoDB (encrypted)
3. Add database name hashing (harder to guess)
4. Add connection limits per database
5. Add MySQL audit logging
```

---

## 🏗️ Implementation Priority

### Phase 1: Username System (High Priority)
- [ ] TODO #4: Decide on username approach (labuser vs dynamic)
- [ ] TODO #2: Update lab_controller.py mount paths
- [ ] TODO #3: Update Dockerfiles (rename student to labuser)
- [ ] Test with fresh user signup

### Phase 2: Documentation (Medium Priority)
- [ ] TODO #5: Update README-TODO.md
- [ ] Create ARCHITECTURE.md explaining shared vs isolated
- [ ] Document RAM consumption comparison

### Phase 3: Security (Medium Priority)
- [ ] TODO #6: Implement security improvements
- [ ] Add password rotation system
- [ ] Add audit logging

### Phase 4: Future (Low Priority)
- [ ] Add resource monitoring dashboard
- [ ] Add database backup system
- [ ] Add multi-region support

---

## 💡 Recommended Changes Summary

### ✅ Keep As-Is:
- Shared service containers (MySQL, PostgreSQL, etc.)
- Service controller architecture
- Resource limits on labs only

### 🔧 Change:
- Remove "student" username → Use "labuser" or email-based
- Update volume mount paths
- Update Dockerfiles

### 📝 Document:
- Why shared services are better
- RAM consumption comparison
- Security considerations

---

## 🎯 Quick Win: Simple Username Fix

**Easiest approach (implement this first):**

1. **Rename "student" to "labuser" globally:**
   ```
   Find: student
   Replace: labuser
   Files: labs/*/Dockerfile, app/lab_controller.py
   ```

2. **Update welcome messages:**
   ```bash
   # Change from:
   echo "Welcome, student!"
   
   # To:
   echo "Welcome, $USER! (${USER_EMAIL})"
   ```

3. **Test:**
   - Create new user
   - Launch Ubuntu lab
   - Terminal should show: labuser@ubuntu
   - Files still isolated by volume

**Time to implement:** 30 minutes  
**Complexity:** Low  
**Impact:** High (professional appearance)

---

## 📊 Resource Consumption Comparison

### Current Architecture (Shared Services):
```
Services (shared):
- MySQL: 500MB
- PostgreSQL: 400MB
- MongoDB: 600MB
- Redis: 100MB
- RabbitMQ: 500MB
Total: ~2GB for ALL users

Labs (per-user):
- Per lab: 4GB RAM + 2 CPUs
- 10 users: 40GB RAM
Total: 2GB + 40GB = 42GB
```

### If Services Were Isolated (DON'T DO THIS):
```
Services (isolated):
- MySQL × 10 users: 5GB
- PostgreSQL × 10 users: 4GB
- MongoDB × 10 users: 6GB
- Redis × 10 users: 1GB
- RabbitMQ × 10 users: 5GB
Total: 21GB for 10 users

Labs (per-user):
- 10 users: 40GB RAM
Total: 21GB + 40GB = 61GB (45% more RAM!)
```

**Conclusion:** Shared service containers save ~20GB RAM for 10 users.

---

## 🚀 Next Steps

1. **Review this TODO.md**
2. **Decide on username approach** (labuser recommended)
3. **Make small changes first** (rename student → labuser)
4. **Test thoroughly**
5. **Document changes**

---

## 📞 Questions to Answer Before Implementation

1. **Username approach:**
   - Keep generic "labuser"? (Easy)
   - Use email-based username? (Complex)
   - Use workspace mount? (Very easy)

2. **Service security:**
   - Add root password rotation?
   - Add per-database connection limits?
   - Add audit logging?

3. **Documentation:**
   - Update README-TODO.md?
   - Create separate ARCHITECTURE.md?
   - Add RAM consumption guide?

---

**END OF TODO.md**