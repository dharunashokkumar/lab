"""
Database Migration Script
Migrates from username-based to email-based authentication
"""
from datetime import datetime
from app.db import users, lab_instances

def migrate_users():
    """Convert existing users to new schema"""
    print("Starting user migration...")

    migrated = 0
    for user in users.find():
        # Skip if already migrated
        if "email" in user:
            print(f"  Skipping {user.get('username', 'unknown')} - already migrated")
            continue

        # Create email from username
        username = user.get("username", "user")
        email = f"{username}@selfmade.local"

        # Update user document
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "email": email,
                "full_name": username.capitalize(),
                "avatar_url": f"https://ui-avatars.com/api/?name={username}&background=6366f1&color=fff",
                "oauth_provider": "legacy",
                "oauth_id": "",
                "theme_preference": "auto",
                "notifications_enabled": True,
                "last_login": datetime.utcnow()
            }}
        )

        migrated += 1
        print(f"  [OK] Migrated: {username} -> {email}")

    print(f"Migrated {migrated} users\n")

def migrate_lab_instances():
    """Update lab instances to use email instead of username"""
    print("Starting lab instances migration...")

    migrated = 0
    for instance in lab_instances.find():
        # Skip if already migrated
        if "user_email" in instance:
            print(f"  Skipping instance {instance.get('_id')} - already migrated")
            continue

        # Find user by old username
        user_id = instance.get("user_id")
        user = users.find_one({"username": user_id})

        if user and "email" in user:
            lab_instances.update_one(
                {"_id": instance["_id"]},
                {"$set": {"user_email": user["email"]}}
            )
            migrated += 1
            print(f"  [OK] Updated instance for {user['email']}")
        else:
            print(f"  [WARN] Could not find user for instance {instance.get('_id')}")

    print(f"Migrated {migrated} lab instances\n")

def run_migration():
    """Run all migrations"""
    print("=" * 60)
    print("SELFMADE LABS - DATABASE MIGRATION")
    print("=" * 60)
    print()

    try:
        migrate_users()
        migrate_lab_instances()

        print("=" * 60)
        print("[SUCCESS] Migration completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
