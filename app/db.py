from pymongo import MongoClient

# Initialize MongoDB Client
client = MongoClient("mongodb://localhost:27017/")
db = client["selfmade_labs"]

# Collections
users = db["users"]
instances = db["lab_instances"]
services = db["services"]
lab_catalog = db["lab_catalog"]

# Seed Catalog if empty (simple init)
if lab_catalog.count_documents({}) == 0:
    lab_catalog.insert_many([
        {
            "id": "ubuntu-ssh",
            "name": "Essentials Lab",
            "icon": "ubuntu",
            "type": "machine",
            "description": "Ubuntu 22.04 with SSH access",
            "image": "ubuntu-ssh-lab"
        },
        {
            "id": "kali-linux",
            "name": "Kali Linux",
            "icon": "linux",
            "type": "machine",
            "description": "Pentesting environment",
            "image": "kali-rolling"
        },
        {
            "id": "n8n",
            "name": "n8n Lab",
            "icon": "workflow",
            "type": "machine",
            "description": "Workflow automation",
            "image": "n8nio/n8n"
        }
    ])
