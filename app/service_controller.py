"""
Service Controller - Manages database/messaging services
MySQL, PostgreSQL, MongoDB, Redis, RabbitMQ
"""
import subprocess
import random
import string
import threading
from datetime import datetime
from app.db import service_instances, service_catalog
from app.notifications import create_notification

SERVICE_TIME_LIMIT = 60 * 60  # 60 minutes (longer than labs)

def generate_password(length=16):
    """Generate secure random password"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def auto_stop_service_timer(container_name, instance_id):
    """Auto-stop service after time limit"""
    import time
    time.sleep(SERVICE_TIME_LIMIT)

    # Re-check status before stopping
    current = service_instances.find_one({"_id": instance_id})
    if current and current["status"] == "running":
        print(f"Auto-stopping service: {container_name}")
        subprocess.run(["docker", "stop", container_name], check=False)
        subprocess.run(["docker", "rm", container_name], check=False)
        service_instances.update_one(
            {"_id": instance_id},
            {"$set": {"status": "auto-stopped", "stopped_at": datetime.utcnow()}}
        )

        # Notify user
        instance = service_instances.find_one({"_id": instance_id})
        if instance:
            create_notification(
                instance["user_email"],
                "service_stopped",
                "Service Auto-Stopped",
                f"Your {instance['service_name']} service was automatically stopped after 60 minutes",
                {"service_id": instance["service_id"]}
            )

def start_service(user_email: str, service_id: str):
    """Start a database/messaging service"""
    # Get service config
    service_config = service_catalog.find_one({"id": service_id})
    if not service_config:
        return {"error": "Invalid service ID"}

    # Generate credentials
    password = generate_password()

    # Random port assignment
    base_port = service_config["port"]
    port = random.randint(base_port, base_port + 100)

    # Container name
    container = f"service_{user_email.split('@')[0]}_{service_id}_{random.randint(100,999)}"

    # Build Docker command
    cmd = [
        "docker", "run", "-d",
        "--name", container,
        "-p", f"{port}:{service_config['port']}"
    ]

    # Add environment variables
    env_template = service_config.get("env_template", {})
    for key, value_template in env_template.items():
        value = value_template.replace("{password}", password)
        cmd.extend(["-e", f"{key}={value}"])

    # Add image
    cmd.append(service_config["image"])

    # Run container
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        return {"error": "Failed to start service", "details": str(e)}

    # Build connection string
    connection_info = build_connection_info(service_id, port, password)

    # Store instance in database
    instance_data = {
        "user_email": user_email,
        "service_id": service_id,
        "service_name": service_config["name"],
        "container": container,
        "port": port,
        "credentials": {
            "host": "localhost",
            "port": port,
            "username": connection_info.get("username", "root"),
            "password": password,
            "connection_string": connection_info.get("connection_string", "")
        },
        "status": "running",
        "started_at": datetime.utcnow()
    }

    # Handle RabbitMQ management port
    if service_id == "rabbitmq" and "management_port" in service_config:
        mgmt_port = random.randint(15672, 15700)
        # Restart container with management port
        subprocess.run(["docker", "stop", container], check=False)
        subprocess.run(["docker", "rm", container], check=False)

        cmd_with_mgmt = [
            "docker", "run", "-d",
            "--name", container,
            "-p", f"{port}:5672",
            "-p", f"{mgmt_port}:15672"
        ]
        cmd_with_mgmt.append(service_config["image"])
        subprocess.run(cmd_with_mgmt, check=True, capture_output=True)

        instance_data["management_port"] = mgmt_port
        instance_data["credentials"]["management_url"] = f"http://localhost:{mgmt_port}"

    res = service_instances.insert_one(instance_data)

    # Start auto-stop timer
    threading.Thread(
        target=auto_stop_service_timer,
        args=(container, res.inserted_id),
        daemon=True
    ).start()

    # Notify user
    create_notification(
        user_email,
        "service_started",
        "Service Started",
        f"Your {service_config['name']} service is now running",
        {"service_id": service_id, "port": port}
    )

    return {
        "status": "started",
        "service": service_config["name"],
        "credentials": instance_data["credentials"]
    }

def build_connection_info(service_id: str, port: int, password: str):
    """Build service-specific connection information"""
    if service_id == "mysql":
        return {
            "username": "root",
            "connection_string": f"mysql://root:{password}@localhost:{port}/mysql"
        }
    elif service_id == "postgresql":
        return {
            "username": "postgres",
            "connection_string": f"postgresql://postgres:{password}@localhost:{port}/postgres"
        }
    elif service_id == "mongodb":
        return {
            "username": "",
            "connection_string": f"mongodb://localhost:{port}/"
        }
    elif service_id == "redis":
        return {
            "username": "",
            "connection_string": f"redis://localhost:{port}"
        }
    elif service_id == "rabbitmq":
        return {
            "username": "guest",
            "connection_string": f"amqp://guest:guest@localhost:{port}/"
        }
    else:
        return {"username": "", "connection_string": ""}

def stop_service(user_email: str, service_id: str):
    """Stop a running service"""
    # Find running service
    query = {"user_email": user_email, "service_id": service_id, "status": "running"}
    service = service_instances.find_one(query)

    if not service:
        return {"error": "Service not found or not running"}

    container = service["container"]

    try:
        subprocess.run(["docker", "stop", container], check=False)
        subprocess.run(["docker", "rm", container], check=False)
    except Exception as e:
        print(f"Error stopping service: {e}")

    # Update status
    service_instances.update_one(
        {"_id": service["_id"]},
        {"$set": {
            "status": "stopped",
            "stopped_at": datetime.utcnow()
        }}
    )

    # Notify user
    create_notification(
        user_email,
        "service_stopped",
        "Service Stopped",
        f"Your {service['service_name']} service has been stopped",
        {"service_id": service_id}
    )

    return {"message": "Service stopped", "service": service["service_name"]}

def get_service_status(user_email: str):
    """Get all running services for user"""
    cursor = service_instances.find(
        {"user_email": user_email, "status": "running"},
        {"_id": 0}
    )
    return list(cursor)

def get_service_credentials(user_email: str, service_id: str):
    """Get credentials for a running service"""
    service = service_instances.find_one({
        "user_email": user_email,
        "service_id": service_id,
        "status": "running"
    })

    if not service:
        return {"error": "Service not found or not running"}

    return {
        "service": service["service_name"],
        "credentials": service["credentials"]
    }

def list_service_catalog():
    """List all available services"""
    return list(service_catalog.find({}, {"_id": 0}))

def stop_all_user_services(user_email: str):
    """Stop all running services for a user"""
    running_services = list(service_instances.find({
        "user_email": user_email,
        "status": "running"
    }))

    stopped = []
    for service in running_services:
        try:
            subprocess.run(["docker", "stop", service["container"]], check=False)
            subprocess.run(["docker", "rm", service["container"]], check=False)

            service_instances.update_one(
                {"_id": service["_id"]},
                {"$set": {
                    "status": "stopped",
                    "stopped_at": datetime.utcnow()
                }}
            )
            stopped.append(service["service_name"])
        except Exception as e:
            print(f"Error stopping service {service['container']}: {e}")

    return {"message": "Services stopped", "stopped": stopped}
