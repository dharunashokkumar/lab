"""
Service Controller - Shared Container Architecture
Creates ONE shared container per service type, multiple user databases per container
"""
import subprocess
import secrets
import string
import hashlib
from datetime import datetime
from app.db import service_instances
from app.notifications import create_notification

# Shared container names (one per service type)
SHARED_CONTAINERS = {
    "mysql": "selfmade-mysql-shared",
    "postgresql": "selfmade-postgresql-shared",
    "mongodb": "selfmade-mongodb-shared",
    "redis": "selfmade-redis-shared",
    "rabbitmq": "selfmade-rabbitmq-shared"
}

# Service configurations
SERVICE_CONFIGS = {
    "mysql": {
        "image": "mysql:8",
        "port": 3306,
        "internal_port": 3306,
        "root_password": "selfmade_root_pass_2024"
    },
    "postgresql": {
        "image": "postgres:16",
        "port": 5432,
        "internal_port": 5432,
        "root_password": "selfmade_root_pass_2024"
    },
    "mongodb": {
        "image": "mongo:7.0",
        "port": 27018,  # Different from main MongoDB on 27017
        "internal_port": 27017,
        "root_password": "selfmade_root_pass_2024"
    },
    "redis": {
        "image": "redis:7-alpine",
        "port": 6379,
        "internal_port": 6379,
        "root_password": "selfmade_root_pass_2024"
    },
    "rabbitmq": {
        "image": "rabbitmq:3-management",
        "port": 5672,
        "management_port": 15673,
        "internal_port": 5672,
        "root_password": "selfmade_root_pass_2024"
    }
}

def generate_password(length=16):
    """Generate secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_email(email: str) -> str:
    """Generate short hash from email for database names"""
    return hashlib.md5(email.encode()).hexdigest()[:8]

def ensure_shared_container_running(service_id: str) -> bool:
    """Ensure shared container for service type is running"""
    container_name = SHARED_CONTAINERS[service_id]
    config = SERVICE_CONFIGS[service_id]

    # Check if container exists and is running
    check_cmd = f"docker ps -q -f name={container_name}"
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

    if result.stdout.strip():
        # Container is running
        return True

    # Check if container exists but is stopped
    check_stopped = f"docker ps -aq -f name={container_name}"
    result_stopped = subprocess.run(check_stopped, shell=True, capture_output=True, text=True)

    if result_stopped.stdout.strip():
        # Container exists, start it
        print(f"Starting existing shared container: {container_name}")
        start_cmd = f"docker start {container_name}"
        subprocess.run(start_cmd, shell=True)
        return True

    # Create new shared container
    print(f"Creating new shared container: {container_name}")

    if service_id == "mysql":
        cmd = (
            f"docker run -d "
            f"--name {container_name} "
            f"-p {config['port']}:{config['internal_port']} "
            f"-e MYSQL_ROOT_PASSWORD={config['root_password']} "
            f"{config['image']}"
        )
    elif service_id == "postgresql":
        cmd = (
            f"docker run -d "
            f"--name {container_name} "
            f"-p {config['port']}:{config['internal_port']} "
            f"-e POSTGRES_PASSWORD={config['root_password']} "
            f"{config['image']}"
        )
    elif service_id == "mongodb":
        cmd = (
            f"docker run -d "
            f"--name {container_name} "
            f"-p {config['port']}:{config['internal_port']} "
            f"-e MONGO_INITDB_ROOT_USERNAME=admin "
            f"-e MONGO_INITDB_ROOT_PASSWORD={config['root_password']} "
            f"{config['image']}"
        )
    elif service_id == "redis":
        cmd = (
            f"docker run -d "
            f"--name {container_name} "
            f"-p {config['port']}:{config['internal_port']} "
            f"{config['image']} "
            f"redis-server --requirepass {config['root_password']}"
        )
    elif service_id == "rabbitmq":
        cmd = (
            f"docker run -d "
            f"--name {container_name} "
            f"-p {config['port']}:{config['internal_port']} "
            f"-p {config['management_port']}:15672 "
            f"-e RABBITMQ_DEFAULT_USER=admin "
            f"-e RABBITMQ_DEFAULT_PASS={config['root_password']} "
            f"{config['image']}"
        )
    else:
        return False

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error creating shared container: {result.stderr}")
        return False

    # Wait for container to be ready
    import time
    time.sleep(3)

    return True

def create_user_database(service_id: str, user_email: str, db_name: str, user_password: str):
    """Create user-specific database in shared container"""
    container_name = SHARED_CONTAINERS[service_id]
    config = SERVICE_CONFIGS[service_id]

    if service_id == "mysql":
        # Create database and user
        sql_commands = f"""
        CREATE DATABASE IF NOT EXISTS {db_name};
        CREATE USER IF NOT EXISTS '{db_name}'@'%' IDENTIFIED BY '{user_password}';
        GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_name}'@'%';
        FLUSH PRIVILEGES;
        """
        cmd = f'docker exec {container_name} mysql -uroot -p{config["root_password"]} -e "{sql_commands}"'

    elif service_id == "postgresql":
        # Create database and user
        cmd = (
            f'docker exec {container_name} psql -U postgres -c '
            f'"CREATE DATABASE {db_name};" && '
            f'docker exec {container_name} psql -U postgres -c '
            f'"CREATE USER {db_name} WITH PASSWORD \'{user_password}\';" && '
            f'docker exec {container_name} psql -U postgres -c '
            f'"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_name};"'
        )

    elif service_id == "mongodb":
        # Create database (will be created on first use, but we can create user)
        mongo_cmd = f"""
        db = db.getSiblingDB('{db_name}');
        db.createUser({{
            user: '{db_name}',
            pwd: '{user_password}',
            roles: [{{ role: 'readWrite', db: '{db_name}' }}]
        }});
        """
        cmd = f'docker exec {container_name} mongosh -u admin -p {config["root_password"]} --authenticationDatabase admin --eval "{mongo_cmd}"'

    else:
        # Redis and RabbitMQ don't need database creation
        return True

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error creating user database: {result.stderr}")
        return False

    return True

def start_service(user_email: str, service_id: str):
    """Start a service for user (create user database in shared container)"""

    # Check if user already has this service running
    existing = service_instances.find_one({
        "user_email": user_email,
        "service": service_id,
        "status": "running"
    })

    if existing:
        return {
            "error": f"You already have {service_id} running. Stop it first before starting a new one.",
            "existing_service": existing
        }

    # Ensure shared container is running
    if not ensure_shared_container_running(service_id):
        return {"error": f"Failed to start shared {service_id} container"}

    config = SERVICE_CONFIGS[service_id]

    # Generate user-specific database name and credentials
    email_hash = hash_email(user_email)
    db_name = f"user_{email_hash}"
    db_password = generate_password()

    # Create user database (for MySQL, PostgreSQL, MongoDB)
    if service_id in ["mysql", "postgresql", "mongodb"]:
        if not create_user_database(service_id, user_email, db_name, db_password):
            return {"error": f"Failed to create user database in {service_id}"}

    # For Redis, assign a DB number (0-15)
    redis_db = None
    if service_id == "redis":
        # Get all Redis instances and find unused DB number
        redis_instances = list(service_instances.find({
            "service": "redis",
            "status": "running"
        }))
        used_dbs = [inst.get("credentials", {}).get("database", 0) for inst in redis_instances]
        redis_db = next((i for i in range(16) if i not in used_dbs), 0)

    # For RabbitMQ, create virtual host
    rabbitmq_vhost = None
    if service_id == "rabbitmq":
        rabbitmq_vhost = f"/user_{email_hash}"
        # Create virtual host
        container_name = SHARED_CONTAINERS[service_id]
        vhost_cmd = f'docker exec {container_name} rabbitmqctl add_vhost {rabbitmq_vhost}'
        subprocess.run(vhost_cmd, shell=True)
        # Set permissions
        perm_cmd = f'docker exec {container_name} rabbitmqctl set_permissions -p {rabbitmq_vhost} admin ".*" ".*" ".*"'
        subprocess.run(perm_cmd, shell=True)

    # Build credentials and connection info
    credentials = {
        "host": "localhost",
        "port": config["port"]
    }

    if service_id in ["mysql", "postgresql", "mongodb"]:
        credentials["username"] = db_name
        credentials["password"] = db_password
        credentials["database"] = db_name
    elif service_id == "redis":
        credentials["password"] = config["root_password"]
        credentials["database"] = redis_db
    elif service_id == "rabbitmq":
        credentials["username"] = "admin"
        credentials["password"] = config["root_password"]
        credentials["vhost"] = rabbitmq_vhost

    # Build connection string
    connection_string = build_connection_string(service_id, credentials)

    # Save service instance to database
    service_data = {
        "user_email": user_email,
        "service": service_id,
        "service_name": service_id.upper(),
        "container": SHARED_CONTAINERS[service_id],  # Shared container name
        "port": config["port"],
        "credentials": credentials,
        "connection_info": {
            "host": credentials["host"],
            "port": credentials["port"],
            "connection_string": connection_string
        },
        "status": "running",
        "started_at": datetime.utcnow()
    }

    result = service_instances.insert_one(service_data)
    service_data["_id"] = str(result.inserted_id)

    # Create notification
    create_notification(
        user_email=user_email,
        notif_type="service_started",
        title=f"{service_id.upper()} Started",
        message=f"Your {service_id} database is ready to use",
        metadata={"service_id": service_id, "port": config["port"]}
    )

    return service_data

def build_connection_string(service_id: str, credentials: dict) -> str:
    """Build connection string for service"""
    host = credentials["host"]
    port = credentials["port"]

    if service_id == "mysql":
        user = credentials["username"]
        password = credentials["password"]
        database = credentials["database"]
        return f"mysql://{user}:{password}@{host}:{port}/{database}"

    elif service_id == "postgresql":
        user = credentials["username"]
        password = credentials["password"]
        database = credentials["database"]
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    elif service_id == "mongodb":
        user = credentials["username"]
        password = credentials["password"]
        database = credentials["database"]
        return f"mongodb://{user}:{password}@{host}:{port}/{database}"

    elif service_id == "redis":
        password = credentials["password"]
        database = credentials["database"]
        return f"redis://:{password}@{host}:{port}/{database}"

    elif service_id == "rabbitmq":
        user = credentials["username"]
        password = credentials["password"]
        vhost = credentials["vhost"]
        return f"amqp://{user}:{password}@{host}:{port}{vhost}"

    return f"{host}:{port}"

def stop_service(user_email: str, service_id: str):
    """Stop a service (delete user database from shared container)"""

    # Find user's service instance
    instance = service_instances.find_one({
        "user_email": user_email,
        "service": service_id,
        "status": "running"
    })

    if not instance:
        return {"error": f"No running {service_id} service found"}

    container_name = SHARED_CONTAINERS[service_id]
    config = SERVICE_CONFIGS[service_id]

    # Delete user database (for MySQL, PostgreSQL, MongoDB)
    if service_id in ["mysql", "postgresql", "mongodb"]:
        db_name = instance["credentials"]["database"]

        if service_id == "mysql":
            sql_commands = f"""
            DROP DATABASE IF EXISTS {db_name};
            DROP USER IF EXISTS '{db_name}'@'%';
            FLUSH PRIVILEGES;
            """
            cmd = f'docker exec {container_name} mysql -uroot -p{config["root_password"]} -e "{sql_commands}"'
            subprocess.run(cmd, shell=True)

        elif service_id == "postgresql":
            cmd = (
                f'docker exec {container_name} psql -U postgres -c '
                f'"DROP DATABASE IF EXISTS {db_name};" && '
                f'docker exec {container_name} psql -U postgres -c '
                f'"DROP USER IF EXISTS {db_name};"'
            )
            subprocess.run(cmd, shell=True)

        elif service_id == "mongodb":
            mongo_cmd = f"db.getSiblingDB('{db_name}').dropDatabase();"
            cmd = f'docker exec {container_name} mongosh -u admin -p {config["root_password"]} --authenticationDatabase admin --eval "{mongo_cmd}"'
            subprocess.run(cmd, shell=True)

    # For RabbitMQ, delete virtual host
    if service_id == "rabbitmq":
        vhost = instance["credentials"]["vhost"]
        cmd = f'docker exec {container_name} rabbitmqctl delete_vhost {vhost}'
        subprocess.run(cmd, shell=True)

    # Update database
    service_instances.update_one(
        {"_id": instance["_id"]},
        {"$set": {"status": "stopped"}}
    )

    # Create notification
    create_notification(
        user_email=user_email,
        notif_type="service_stopped",
        title=f"{service_id.upper()} Stopped",
        message=f"Your {service_id} database has been stopped",
        metadata={"service_id": service_id}
    )

    return {"message": f"Service {service_id} stopped successfully"}

def get_service_status(user_email: str):
    """Get all running services for user"""
    services = list(service_instances.find({
        "user_email": user_email,
        "status": "running"
    }))

    # Convert ObjectId to string
    for service in services:
        service["_id"] = str(service["_id"])

    return services

def get_service_credentials(user_email: str, service_id: str):
    """Get credentials for user's service"""
    instance = service_instances.find_one({
        "user_email": user_email,
        "service": service_id,
        "status": "running"
    })

    if not instance:
        return {"error": "Service not found or not running"}

    return {
        "service_name": instance["service_name"],
        "host": instance["credentials"]["host"],
        "port": instance["credentials"]["port"],
        "username": instance["credentials"].get("username"),
        "password": instance["credentials"].get("password"),
        "database": instance["credentials"].get("database"),
        "vhost": instance["credentials"].get("vhost"),
        "connection_string": instance["connection_info"]["connection_string"]
    }

def list_service_catalog():
    """List available services"""
    from app.db import service_catalog
    services = list(service_catalog.find())

    for service in services:
        service["_id"] = str(service["_id"])

    return services
