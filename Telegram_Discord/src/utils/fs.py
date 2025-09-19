"""
Filesystem utilities with Windows path handling and atomic operations
"""
import os
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional


BASE_PATH = Path("C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord")


def ensure_dirs(*paths):
    """Create directories if they don't exist"""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def write_json(path: str, data: Any, atomic: bool = True) -> None:
    """
    Write JSON data to file atomically (write to temp, then rename)

    Args:
        path: Target file path
        data: Data to serialize
        atomic: Use atomic write (safer)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if atomic:
        # Write to temp file first
        temp_path = path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        # Atomic rename
        temp_path.replace(path)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def read_json(path: str) -> Any:
    """Read and parse JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_json_safe(path: str, default: Any = None) -> Any:
    """Read JSON file, return default if file doesn't exist or is invalid"""
    try:
        if Path(path).exists():
            return read_json(path)
    except (json.JSONDecodeError, IOError):
        pass
    return default


def list_json_files(directory: str) -> List[str]:
    """List all JSON files in a directory"""
    path = Path(directory)
    if not path.exists():
        return []
    return sorted([str(f) for f in path.glob("*.json")])


def timestamp() -> str:
    """ISO timestamp for filenames and logs"""
    return datetime.utcnow().isoformat(timespec="seconds").replace(":", "-") + "Z"


def dated_path(base_dir: str) -> str:
    """Create dated subdirectory path (YYYYMMDD)"""
    today = datetime.now().strftime("%Y%m%d")
    path = Path(base_dir) / today
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def move(src: str, dst_dir: str) -> str:
    """
    Move file to destination directory

    Args:
        src: Source file path
        dst_dir: Destination directory

    Returns:
        New file path
    """
    src_path = Path(src)
    dst_path = Path(dst_dir)
    dst_path.mkdir(parents=True, exist_ok=True)

    # Generate unique name if file exists
    target = dst_path / src_path.name
    if target.exists():
        stem = src_path.stem
        suffix = src_path.suffix
        target = dst_path / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"

    shutil.move(str(src), str(target))
    return str(target)


def copy_preserve(src: str, dst: str) -> None:
    """Copy file preserving metadata"""
    shutil.copy2(src, dst)


def archive_message(message_path: str, queue_name: str) -> str:
    """
    Archive processed message to dated archive directory

    Args:
        message_path: Path to message JSON
        queue_name: Queue name for organization

    Returns:
        Archive path
    """
    archive_base = BASE_PATH / "sent_archive"
    today = datetime.now().strftime("%Y%m%d")
    archive_dir = archive_base / today / queue_name
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique archive name
    msg_id = Path(message_path).stem
    timestamp = datetime.now().strftime("%H%M%S")
    archive_name = f"{msg_id}_{timestamp}.json"
    archive_path = archive_dir / archive_name

    shutil.move(str(message_path), str(archive_path))
    return str(archive_path)


def cleanup_old_archives(days: int = 30) -> int:
    """
    Remove archives older than specified days

    Returns:
        Number of directories removed
    """
    archive_base = BASE_PATH / "sent_archive"
    if not archive_base.exists():
        return 0

    cutoff = datetime.now().timestamp() - (days * 86400)
    removed = 0

    for dated_dir in archive_base.iterdir():
        if dated_dir.is_dir():
            # Check directory age
            if dated_dir.stat().st_mtime < cutoff:
                shutil.rmtree(dated_dir)
                removed += 1

    return removed


def get_queue_backlog(queue_name: str) -> int:
    """Get number of pending messages in queue"""
    queue_path = BASE_PATH / "message_queue" / queue_name
    if not queue_path.exists():
        return 0
    return len(list(queue_path.glob("*.json")))