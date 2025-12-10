"""
Volume Manager Module
Manages persistent Docker volumes for user labs.
Each user gets ONE volume shared across ALL their labs.
"""

import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_user_volume_name(user_email: str) -> str:
    """
    Generate consistent volume name for user.

    Args:
        user_email: User's email address

    Returns:
        Volume name in format: user_{username}_home

    Example:
        dharuna457@gmail.com -> user_dharuna457_home
        john.doe@example.com -> user_john_doe_home
    """
    # Extract username from email and sanitize
    username = user_email.split('@')[0].replace('.', '_').replace('-', '_')
    return f"user_{username}_home"


def volume_exists(volume_name: str) -> bool:
    """
    Check if a Docker volume exists.

    Args:
        volume_name: Name of the volume to check

    Returns:
        True if volume exists, False otherwise
    """
    try:
        cmd = ["docker", "volume", "ls", "-q", "-f", f"name=^{volume_name}$"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking volume {volume_name}: {e}")
        return False


def create_user_volume_if_not_exists(user_email: str) -> str:
    """
    Create persistent volume for user if it doesn't exist.

    Args:
        user_email: User's email address

    Returns:
        Volume name that was created or already exists

    Raises:
        RuntimeError: If volume creation fails
    """
    volume_name = get_user_volume_name(user_email)

    # Check if volume already exists
    if volume_exists(volume_name):
        logger.info(f"Volume {volume_name} already exists")
        return volume_name

    # Create volume
    try:
        cmd = ["docker", "volume", "create", volume_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Created volume: {volume_name}")
        return volume_name
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to create volume {volume_name}: {e.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def delete_user_volume(user_email: str) -> bool:
    """
    Delete user's persistent volume.
    WARNING: This will delete all user data permanently!

    Args:
        user_email: User's email address

    Returns:
        True if volume was deleted, False if volume didn't exist or deletion failed
    """
    volume_name = get_user_volume_name(user_email)

    # Check if volume exists
    if not volume_exists(volume_name):
        logger.warning(f"Volume {volume_name} does not exist, nothing to delete")
        return False

    # Delete volume
    try:
        cmd = ["docker", "volume", "rm", volume_name]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Deleted volume: {volume_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete volume {volume_name}: {e.stderr}")
        return False


def get_volume_info(user_email: str) -> Optional[dict]:
    """
    Get information about user's volume.

    Args:
        user_email: User's email address

    Returns:
        Dictionary with volume info or None if volume doesn't exist

    Example return:
        {
            "name": "user_dharuna457_home",
            "driver": "local",
            "mountpoint": "/var/lib/docker/volumes/user_dharuna457_home/_data"
        }
    """
    volume_name = get_user_volume_name(user_email)

    if not volume_exists(volume_name):
        return None

    try:
        cmd = ["docker", "volume", "inspect", volume_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse JSON output
        import json
        volume_data = json.loads(result.stdout)

        if volume_data:
            vol = volume_data[0]
            return {
                "name": vol.get("Name"),
                "driver": vol.get("Driver"),
                "mountpoint": vol.get("Mountpoint"),
                "created": vol.get("CreatedAt")
            }
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
        logger.error(f"Failed to get volume info for {volume_name}: {e}")
        return None


def list_all_user_volumes() -> list[dict]:
    """
    List all user volumes in the system.

    Returns:
        List of volume information dictionaries
    """
    try:
        cmd = ["docker", "volume", "ls", "-f", "name=^user_", "--format", "{{.Name}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        volumes = []
        for volume_name in result.stdout.strip().split('\n'):
            if volume_name:
                # Extract email from volume name
                # user_dharuna457_home -> dharuna457
                username = volume_name.replace("user_", "").replace("_home", "")
                volumes.append({
                    "volume_name": volume_name,
                    "username": username
                })

        return volumes
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list user volumes: {e}")
        return []


def get_volume_size(user_email: str) -> Optional[str]:
    """
    Get the size of user's volume (disk usage).
    Note: This requires docker system df -v command.

    Args:
        user_email: User's email address

    Returns:
        Size string (e.g., "1.2GB") or None if unable to determine
    """
    volume_name = get_user_volume_name(user_email)

    try:
        cmd = ["docker", "system", "df", "-v", "--format", "{{.Name}}\t{{.Size}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse output to find our volume
        for line in result.stdout.strip().split('\n'):
            if '\t' in line:
                name, size = line.split('\t', 1)
                if name == volume_name:
                    return size

        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get volume size for {volume_name}: {e}")
        return None
