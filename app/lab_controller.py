import subprocess
import random
import threading
from datetime import datetime
from app.db import instances, lab_catalog, services

LAB_TIME_LIMIT = 30 * 60  # 30 minutes

def auto_stop_timer(container_name, instance_id):
    import time
    time.sleep(LAB_TIME_LIMIT)
    # Re-check status before stopping
    current = instances.find_one({"_id": instance_id})
    if current and current["status"] == "running":
        print(f"Auto-stopping {container_name}")
        subprocess.run(["docker", "stop", container_name])
        subprocess.run(["docker", "rm", container_name])
        instances.update_one(
            {"_id": instance_id},
            {"$set": {"status": "auto-stopped", "stopped_at": datetime.utcnow()}}
        )

def start_lab(username: str, lab_id: str):
    # Check if user already has ANY lab running (for now limit 1)
    existing = instances.find_one({
        "user_id": username,
        "status": "running"
    })

    if existing:
        return {
            "error": "You already have a lab running. Stop it first.",
            "running_lab": existing["lab"]
        }

    # Get Lab Config
    lab_config = lab_catalog.find_one({"id": lab_id})
    if not lab_config:
        return {"error": "Invalid Lab ID"}

    port = random.randint(2200, 2300) # Simple port pool
    container = f"lab_{username}_{lab_id}_{random.randint(100,999)}"

    # Determine Docker Command based on type
    # (Simplified for prototype: mostly assuming SSH or Web mapped to port)
    
    cmd = [
        "docker", "run", "-d",
        "--name", container
    ]
    
    # Port Mapping Logic (Prototype)
    if lab_id == "n8n":
        cmd.extend(["-p", f"{port}:5678"]) # n8n default
        access_type = "web"
    else:
        cmd.extend(["-p", f"{port}:22"]) # Default SSH
        access_type = "ssh"

    cmd.append(lab_config["image"])

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return {"error": "Failed to start container", "details": str(e)}

    # Start Auto-stop Timer
    # In prod, use Celery/RQ. Here using thread for simplicity.
    
    # Insert record
    res = instances.insert_one({
        "user_id": username,
        "lab": lab_id,
        "lab_name": lab_config["name"],
        "container": container,
        "port": port,
        "access_type": access_type,
        "status": "running",
        "started_at": datetime.utcnow()
    })
    
    threading.Thread(target=auto_stop_timer, args=(container, res.inserted_id), daemon=True).start()

    return {
        "status": "started",
        "lab": lab_config["name"],
        "port": port,
        "access_type": access_type
    }


def stop_lab(username: str, lab_id: str = None):
    # Stop specific or all running labs for user
    query = {"user_id": username, "status": "running"}
    if lab_id:
        query["lab"] = lab_id
        
    running_labs = list(instances.find(query))
    
    stopped = []
    for instance in running_labs:
        container = instance["container"]
        try:
            subprocess.run(["docker", "stop", container], check=False)
            subprocess.run(["docker", "rm", container], check=False)
        except Exception:
            pass
            
        instances.update_one(
            {"_id": instance["_id"]},
            {"$set": {
                "status": "stopped",
                "stopped_at": datetime.utcnow()
            }}
        )
        stopped.append(instance["lab"])

    return {"message": "Labs stopped", "stopped": stopped}


def get_lab_status(username: str):
    # Get all running labs
    cursor = instances.find(
        {"user_id": username, "status": "running"},
        {"_id": 0}
    )
    return list(cursor)

def list_catalog():
    return list(lab_catalog.find({}, {"_id": 0}))

def list_services():
    return list(services.find({}, {"_id": 0}))
