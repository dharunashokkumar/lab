import subprocess
import random
import threading
from datetime import datetime
from app.db import instances

LAB_TIME_LIMIT = 30 * 60  # 30 minutes


def auto_stop(container_name, instance_id):
    subprocess.run(["docker", "stop", container_name])
    subprocess.run(["docker", "rm", container_name])

    instances.update_one(
        {"_id": instance_id},
        {"$set": {
            "status": "auto-stopped",
            "stopped_at": datetime.utcnow()
        }}
    )


def start_ubuntu_lab(username: str):
    existing = instances.find_one({
        "user_id": username,
        "status": "running"
    })

    if existing:
        return {
            "error": "Lab already running",
            "port": existing["port"]
        }

    port = random.randint(2200, 2300)
    container = f"lab_{username}"

    subprocess.run([
        "docker", "run", "-d",
        "-p", f"{port}:22",
        "--name", container,
        "ubuntu-ssh-lab"
    ])

    result = instances.insert_one({
        "user_id": username,
        "lab": "ubuntu-ssh",
        "container": container,
        "port": port,
        "status": "running",
        "started_at": datetime.utcnow()
    })


def stop_lab(username: str):
    instance = instances.find_one({
        "user_id": username,
        "status": "running"
    })
    ...

def get_lab_status(username: str):
    instance = instances.find_one(
        {"user_id": username},
        sort=[("started_at", -1)]
    )
    ...
