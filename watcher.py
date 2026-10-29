"""Folder watcher - monitors a folder and organizes new files."""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from organizer import organize_file
from config import SKIP_EXTENSIONS

# File paths to temporarily ignore (e.g., files restored by undo)
IGNORED_FILES = set()


class DownloadHandler(FileSystemEventHandler):
    """Handles new file events in the watched folder."""

    def __init__(self, folder_path, on_move=None):
        self.folder_path = Path(folder_path)
        self.on_move = on_move  # optional callback(original_path, new_path)

    def on_created(self, event):
        """Called when a new file is created."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Skip temporary files
        if file_path.suffix.lower() in SKIP_EXTENSIONS:
            return

        # Skip files that were restored by undo
        if file_path.resolve() in IGNORED_FILES:
            IGNORED_FILES.discard(file_path.resolve())
            return

        # Wait for download to finish
        time.sleep(2)

        # Skip if file was deleted during wait
        if not file_path.exists():
            return

        # Move the file
        print(f"\nNew file detected: {file_path.name}")
        result = organize_file(self.folder_path, file_path)

        if result:
            print(f"  → Moved to: {result}")
            if self.on_move:
                self.on_move(str(file_path), result)
        else:
            print("  → Skipped (could not move)")


def start_watching(folder_path, on_move=None):
    """Start watching a folder for new files. Returns the observer instance."""
    folder_path = Path(folder_path)

    if not folder_path.exists():
        print(f"Error: Folder does not exist: {folder_path}")
        return None

    print(f"Watching: {folder_path}")

    handler = DownloadHandler(folder_path, on_move=on_move)
    observer = Observer()
    observer.schedule(handler, str(folder_path), recursive=False)
    observer.start()
    return observer
