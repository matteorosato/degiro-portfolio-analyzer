"""Log management utilities for viewing application logs."""
from pathlib import Path
from typing import Tuple, Optional


def get_log_file_path(log_type: str = "app") -> Optional[Path]:
    """Get the path to a log file.
    
    Args:
        log_type: Type of log file ('app', 'scheduler', or 'all')
        
    Returns:
        Path to the log file or None if not found
    """
    backend_logs_dir = Path(__file__).parent.parent.parent.parent / "backend" / "logs"

    if log_type == "app":
        return backend_logs_dir / "app.log"
    elif log_type == "scheduler":
        return backend_logs_dir / "scheduler.log"

    return None


def read_log_file(log_type: str = "app", max_lines: int = 50) -> str:
    """Read log file and return last N lines.
    
    Args:
        log_type: Type of log file ('app', 'scheduler', or 'all')
        max_lines: Maximum number of lines to return
        
    Returns:
        String containing log lines, or error message if file not found
    """
    if log_type == "all":
        # Combine both logs
        app_logs = read_log_file("app", max_lines)
        scheduler_logs = read_log_file("scheduler", max_lines)
        return f"=== APP LOGS ===\n{app_logs}\n\n=== SCHEDULER LOGS ===\n{scheduler_logs}"

    log_path = get_log_file_path(log_type)

    if log_path is None or not log_path.exists():
        return f"📭 Log file not found: {log_path}"

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # If max_lines is very large (simulate 'All'), return all
        if max_lines is None or max_lines >= 1000000:
            return ''.join(lines)

        # Return last N lines
        if len(lines) <= max_lines:
            return ''.join(lines)

        return ''.join(lines[-max_lines:])

    except Exception as e:
        return f"❌ Error reading log file: {str(e)}"


def get_log_files_info() -> Tuple[bool, bool]:
    """Check which log files exist.
    
    Returns:
        Tuple of (app_log_exists, scheduler_log_exists)
    """
    app_path = get_log_file_path("app")
    scheduler_path = get_log_file_path("scheduler")

    return (
        app_path and app_path.exists(),
        scheduler_path and scheduler_path.exists()
    )


def get_log_file_stats(log_type: str = "app") -> Optional[dict]:
    """Get statistics about a log file.
    
    Args:
        log_type: Type of log file ('app' or 'scheduler')
        
    Returns:
        Dictionary with file stats or None
    """
    log_path = get_log_file_path(log_type)

    if log_path is None or not log_path.exists():
        return None

    try:
        stat = log_path.stat()
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f)

        return {
            'size_kb': stat.st_size / 1024,
            'lines': line_count,
            'modified': stat.st_mtime
        }
    except Exception:
        return None
