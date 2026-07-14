from datetime import datetime, timezone
from pathlib import Path


def append_error_log(path: str, source: str, message: str) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not log_path.exists():
        log_path.write_text("Error Log\n=========\n\n", encoding="utf-8")

    timestamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}]\n")
        file.write(f"Source: {source}\n")
        file.write(f"Error: {message}\n\n")
