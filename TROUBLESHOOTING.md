# Troubleshooting Guide

## Issue 1: Admin Role Not Showing After MongoDB Update

### Problem
You changed your role to "admin" in MongoDB Compass, but the dashboard still shows you as a regular user.

### Cause
The JWT token contains your role at the time of login. When you change the role in the database, your current JWT token still has the old role.

### Solution
**Logout and login again:**

1. Click the **Logout** button in the sidebar
2. Go back to login page: http://localhost:8000/ui/login.html
3. Sign in with Google or GitHub again
4. Your new admin role will now be reflected

### Alternative: Clear Browser Storage
```javascript
// Open browser console (F12) and run:
localStorage.clear();
location.href = '/ui/login.html';
```

---

## Issue 2: Labs/Services Not Stopping When Clicking Stop Button

### Debugging Steps

1. **Open Browser Console** (Press F12 → Console tab)

2. **Click the Stop button** and check for error messages

3. **Look for these log messages:**
   - `Stopping lab: <lab-id>` - Button clicked successfully
   - `Stop lab result: {...}` - API call succeeded
   - `Stop lab error: ...` - API call failed (this will show the error)

### Common Causes

**A. API Endpoint Error**
```
Error: 404 Not Found
Solution: Check if server is running on http://localhost:8000
```

**B. Authentication Error**
```
Error: 401 Unauthorized
Solution: Logout and login again (token may be expired)
```

**C. Lab Not Found**
```
Error: Lab instance not found
Solution: The lab may have already stopped. Refresh the page.
```

**D. Docker Error**
```
Error: Container not found
Solution: Check if Docker Desktop is running
```

### Manual Testing
Test the API directly in browser console:

```javascript
// Test stop lab
await api.stopLab('ubuntu-ssh');

// Test stop service
await api.stopService('mysql');

// Check if any errors are logged
```

---

## Issue 3: Google Profile Image Not Loading

### Debugging Steps

1. **Open Browser Console** (F12 → Console tab)

2. **Check for these messages:**
   - `User data: {...}` - Shows if avatar_url is present
   - `Loading avatar: https://...` - Avatar URL exists
   - `No avatar URL, showing initials` - No avatar URL
   - `Failed to load avatar image` - Image failed to load

3. **Inspect the user object:**
```javascript
// In console, run:
await api.getProfile();
// Look for "avatar_url" field
```

### Common Causes

**A. Avatar URL Not Saved During OAuth**

Check MongoDB Compass:
1. Open `selfmade_labs` database
2. Open `users` collection
3. Find your user document
4. Check if `avatar_url` field exists and has a URL

**If missing**, the issue is in OAuth callback. Check server logs.

**B. Avatar URL is Empty String**

MongoDB shows:
```json
{
  "avatar_url": ""
}
```

**Solution**: Logout, delete your user from MongoDB, and login again. Google will provide the avatar URL on fresh login.

**C. Avatar Image CORS Error**

Console shows:
```
Failed to load image: CORS policy
```

**Solution**: This is rare with Google images. Try logging out and in again.

**D. Avatar Image 403 Forbidden**

Console shows:
```
Failed to load avatar image
GET https://... 403 (Forbidden)
```

**Solution**: Google avatar URLs can expire. Logout and login again to get a fresh URL.

### Manual Fix in MongoDB

If you want to manually set an avatar URL:

1. Open MongoDB Compass
2. Navigate to: `selfmade_labs` → `users` collection
3. Find your user document
4. Click Edit
5. Add or update:
```json
{
  "avatar_url": "https://lh3.googleusercontent.com/a/YOUR_GOOGLE_PHOTO_ID"
}
```
6. Save
7. Refresh dashboard page

---

## Quick Diagnostic Commands

Open browser console (F12) and run these:

```javascript
// 1. Check if logged in
console.log('Token:', localStorage.getItem('selfmade_token'));

// 2. Get current user data
api.getProfile().then(user => console.log('User:', user));

// 3. Check admin status
api.getProfile().then(user => console.log('Role:', user.role));

// 4. Test stop lab (replace 'ubuntu-ssh' with your lab ID)
api.stopLab('ubuntu-ssh')
  .then(result => console.log('Success:', result))
  .catch(error => console.error('Error:', error));

// 5. Check server connectivity
fetch('/labs/status', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('selfmade_token')}`
  }
})
.then(r => r.json())
.then(data => console.log('Labs:', data))
.catch(err => console.error('API Error:', err));
```

---

## Server-Side Debugging

### Check FastAPI Logs

The server terminal shows all API requests:

```
INFO:     127.0.0.1:12345 - "POST /labs/stop HTTP/1.1" 200 OK
INFO:     127.0.0.1:12345 - "POST /labs/stop HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:12345 - "POST /labs/stop HTTP/1.1" 500 Internal Server Error
```

- **200 OK** = Success
- **404 Not Found** = Lab doesn't exist
- **500 Internal Server Error** = Server error (check error details above)

### Check MongoDB Data

```bash
# Connect to MongoDB
docker exec -it selfmade-mongo mongosh

# Switch to database
use selfmade_labs

# Check users
db.users.find().pretty()

# Check running labs
db.lab_instances.find({status: "running"}).pretty()

# Check running services
db.service_instances.find({status: "running"}).pretty()

# Exit
exit
```

---

## Complete Reset (Nuclear Option)

If nothing works, reset everything:

### 1. Stop Server
```bash
# Press Ctrl+C in server terminal
```

### 2. Clear Database
```bash
docker exec -it selfmade-mongo mongosh
use selfmade_labs
db.dropDatabase()
exit
```

### 3. Clear Browser Data
```bash
# In browser:
# 1. Press F12
# 2. Go to Application tab
# 3. Storage → Local Storage → Clear All
# 4. Close browser completely
```

### 4. Restart Everything
```bash
# Start server
./venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

# Open fresh browser window
# Go to http://localhost:8000/ui/login.html
# Login with Google/GitHub
# You'll be the first user = auto admin
```

---

## Still Having Issues?

### Enable Debug Mode

Edit `.env`:
```env
DEBUG=True
ENVIRONMENT=development
```

Restart server and check logs for detailed error messages.

### Common Environment Issues

1. **Python Virtual Environment Not Activated**
```bash
# Windows
venv\Scripts\activate

# Check if active (should show (venv))
```

2. **MongoDB Not Running**
```bash
docker ps | grep mongo
# Should show selfmade-mongo container

# If not running:
docker start selfmade-mongo
```

3. **Docker Not Running**
```bash
# Windows: Open Docker Desktop
# Check if Docker Desktop is running in system tray
```

4. **Port 8000 Already in Use**
```bash
# Windows - find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

---

## Contact Support

If issues persist after trying these solutions:

1. Export browser console logs (right-click → Save as)
2. Export server terminal logs
3. Export MongoDB user document
4. Create GitHub issue with all logs attached
