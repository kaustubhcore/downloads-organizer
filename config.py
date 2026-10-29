"""File type categorization rules for Downloads Organizer."""

FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi"],
    "Audio": [".mp3", ".wav", ".m4a"],
    "Archives": [".zip", ".rar", ".7z"],
    "Installers": [".exe", ".msi"],
}

# Files currently downloading - skip these
SKIP_EXTENSIONS = [".crdownload", ".tmp", ".part"]

# Folder path to organize (can override at runtime)
DEFAULT_FOLDER = None
