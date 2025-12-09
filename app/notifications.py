"""
Notifications Module
Manages user notifications for lab/service events
"""
from datetime import datetime
from app.db import notifications
from bson import ObjectId

def create_notification(user_email: str, notif_type: str, title: str, message: str, metadata: dict = None):
    """Create a new notification"""
    notification = {
        "user_email": user_email,
        "type": notif_type,
        "title": title,
        "message": message,
        "read": False,
        "created_at": datetime.utcnow(),
        "metadata": metadata or {}
    }

    result = notifications.insert_one(notification)
    return str(result.inserted_id)

def get_user_notifications(user_email: str, unread_only: bool = False, limit: int = 50):
    """Get notifications for a user"""
    query = {"user_email": user_email}
    if unread_only:
        query["read"] = False

    cursor = notifications.find(query).sort("created_at", -1).limit(limit)

    # Convert ObjectId to string for JSON serialization
    notifs = []
    for notif in cursor:
        notif["_id"] = str(notif["_id"])
        notifs.append(notif)

    return notifs

def get_unread_count(user_email: str):
    """Get count of unread notifications"""
    return notifications.count_documents({
        "user_email": user_email,
        "read": False
    })

def mark_as_read(notification_id: str, user_email: str):
    """Mark a notification as read"""
    try:
        result = notifications.update_one(
            {"_id": ObjectId(notification_id), "user_email": user_email},
            {"$set": {"read": True}}
        )
        return result.modified_count > 0
    except Exception:
        return False

def mark_all_as_read(user_email: str):
    """Mark all notifications as read for a user"""
    result = notifications.update_many(
        {"user_email": user_email, "read": False},
        {"$set": {"read": True}}
    )
    return result.modified_count

def delete_notification(notification_id: str, user_email: str):
    """Delete a notification"""
    try:
        result = notifications.delete_one({
            "_id": ObjectId(notification_id),
            "user_email": user_email
        })
        return result.deleted_count > 0
    except Exception:
        return False

def delete_all_notifications(user_email: str):
    """Delete all notifications for a user"""
    result = notifications.delete_many({"user_email": user_email})
    return result.deleted_count

def cleanup_old_notifications(days_old: int = 30):
    """Delete notifications older than specified days"""
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    result = notifications.delete_many({
        "created_at": {"$lt": cutoff_date},
        "read": True  # Only delete read notifications
    })

    return result.deleted_count
