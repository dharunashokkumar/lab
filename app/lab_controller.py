import subprocess
import random
import threading
import logging
from datetime import datetime
from app.db import lab_instances as instances, lab_catalog, service_instances as services
from app.volume_manager import create_user_volume_if_not_exists, get_user_volume_name

logger = logging.getLogger(__name__)

LAB_TIME_LIMIT = 30 * 60  # 30 minutes

# Resource limits per lab container
RESOURCE_LIMITS = {
    "cpus": "2",      # 2 vCPUs max
    "memory": "4g"    # 4GB RAM max
}

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

def start_lab(user_email: str, lab_id: str):
    # Check if user already has THIS SPECIFIC lab running
    existing = instances.find_one({
        "user_email": user_email,
        "lab": lab_id,
        "status": "running"
    })

    if existing:
        return {
            "error": f"You already have {lab_id} lab running. Stop it first.",
            "running_lab": existing["lab"],
            "port": existing["port"],
            "access_url": existing.get("access_url")
        }

    # Get Lab Config
    lab_config = lab_catalog.find_one({"id": lab_id})
    if not lab_config:
        return {"error": "Invalid Lab ID"}

    # Create or get user's persistent volume
    try:
        volume_name = create_user_volume_if_not_exists(user_email)
    except RuntimeError as e:
        return {"error": f"Failed to create user volume: {str(e)}"}

    # Allocate port based on lab type
    port = random.randint(8000, 9000)  # Expanded port range for web terminals
    container = f"lab_{user_email.split('@')[0]}_{lab_id}_{random.randint(1000,9999)}"

    # Build Docker command with shared volume and resource limits
    cmd = [
        "docker", "run", "-d",
        "--name", container,

        # CRITICAL: Mount user's persistent volume
        "-v", f"{volume_name}:/home/student",

        # Resource limits (CPU and memory)
        "--cpus", RESOURCE_LIMITS["cpus"],
        "--memory", RESOURCE_LIMITS["memory"],
    ]

    # Port Mapping Logic (updated for web terminals)
    if lab_id == "n8n":
        cmd.extend(["-p", f"{port}:5678"])  # n8n web UI
        access_type = "web"
        internal_port = 5678
    elif lab_id in ["ubuntu-ssh", "kali-linux"]:
        cmd.extend(["-p", f"{port}:7681"])  # ttyd web terminal
        access_type = "web_terminal"
        internal_port = 7681
    else:
        # Default: assume web terminal on port 7681
        cmd.extend(["-p", f"{port}:7681"])
        access_type = "web_terminal"
        internal_port = 7681

    cmd.append(lab_config["image"])

    # Start container
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Started container {container} for {user_email}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start container {container}: {e.stderr}")
        return {"error": "Failed to start container", "details": e.stderr}

    # Build access URL
    access_url = f"http://localhost:{port}"

    # Insert record with volume and resource information
    res = instances.insert_one({
        "user_email": user_email,
        "lab": lab_id,
        "lab_name": lab_config["name"],
        "container": container,
        "volume": volume_name,           # NEW: Track volume
        "port": port,
        "access_url": access_url,        # NEW: Direct access URL
        "access_type": access_type,
        "status": "running",
        "started_at": datetime.utcnow(),

        # Resource limits tracking
        "resources": {
            "cpus": RESOURCE_LIMITS["cpus"],
            "memory": RESOURCE_LIMITS["memory"]
        }
    })

    # Start Auto-stop Timer
    threading.Thread(target=auto_stop_timer, args=(container, res.inserted_id), daemon=True).start()

    return {
        "status": "started",
        "lab_name": lab_config["name"],
        "container": container,
        "volume": volume_name,
        "port": port,
        "access_url": access_url,
        "access_type": access_type,
        "resources": RESOURCE_LIMITS
    }


def stop_lab(user_email: str, lab_id: str = None):
    # Stop specific or all running labs for user
    query = {"user_email": user_email, "status": "running"}
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


def get_lab_status(user_email: str):
    # Get all running labs
    cursor = instances.find(
        {"user_email": user_email, "status": "running"},
        {"_id": 0}
    )
    return list(cursor)

def list_catalog():
    return list(lab_catalog.find({}, {"_id": 0}))

def list_services():
    return list(services.find({}, {"_id": 0}))
