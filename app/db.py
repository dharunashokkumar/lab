from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize MongoDB Client
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "selfmade_labs")

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
users = db["users"]
lab_instances = db["lab_instances"]
service_instances = db["service_instances"]
notifications = db["notifications"]
audit_logs = db["audit_logs"]
lab_catalog = db["lab_catalog"]
service_catalog = db["service_catalog"]

# Seed Lab Catalog if empty
if lab_catalog.count_documents({}) == 0:
    lab_catalog.insert_many([
        {
            "id": "ubuntu-ssh",
            "name": "Essentials Lab",
            "icon": "terminal",
            "type": "machine",
            "description": "Ubuntu 22.04 with SSH access",
            "image": "ubuntu-ssh-lab",
            "port": 22
        },
        {
            "id": "kali-linux",
            "name": "Kali Linux",
            "icon": "security",
            "type": "machine",
            "description": "Pentesting environment",
            "image": "kalilinux/kali-rolling",
            "port": 22
        },
        {
            "id": "n8n",
            "name": "n8n Lab",
            "icon": "hub",
            "type": "machine",
            "description": "Workflow automation",
            "image": "n8nio/n8n",
            "port": 5678
        }
    ])
    print("[OK] Lab catalog seeded")

# Seed Service Catalog if empty
if service_catalog.count_documents({}) == 0:
    service_catalog.insert_many([
        {
            "id": "mysql",
            "name": "MySQL Server",
            "icon": "storage",
            "type": "database",
            "description": "MySQL 8.0 relational database",
            "image": "mysql:8.0",
            "port": 3306,
            "env_template": {
                "MYSQL_ROOT_PASSWORD": "{password}"
            }
        },
        {
            "id": "postgresql",
            "name": "PostgreSQL",
            "icon": "database",
            "type": "database",
            "description": "PostgreSQL 16 database server",
            "image": "postgres:16",
            "port": 5432,
            "env_template": {
                "POSTGRES_PASSWORD": "{password}"
            }
        },
        {
            "id": "mongodb",
            "name": "MongoDB",
            "icon": "account_tree",
            "type": "database",
            "description": "MongoDB 7.0 NoSQL database",
            "image": "mongo:7.0",
            "port": 27017,
            "env_template": {}
        },
        {
            "id": "redis",
            "name": "Redis",
            "icon": "memory",
            "type": "cache",
            "description": "Redis 7 in-memory data store",
            "image": "redis:7-alpine",
            "port": 6379,
            "env_template": {}
        },
        {
            "id": "rabbitmq",
            "name": "RabbitMQ",
            "icon": "sync_alt",
            "type": "messaging",
            "description": "RabbitMQ 3 message broker",
            "image": "rabbitmq:3-management",
            "port": 5672,
            "management_port": 15672,
            "env_template": {}
        }
    ])
    print("[OK] Service catalog seeded")
