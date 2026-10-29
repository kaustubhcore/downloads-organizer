"""File organization logic - moves files into category subfolders."""

import shutil
from pathlib import Path
from config import FILE_TYPES, SKIP_EXTENSIONS


def get_category_for_file(filename):
    """Return the category folder name for a file, or 'Other' if unknown."""
    ext = Path(filename).suffix.lower()

    for category, extensions in FILE_TYPES.items():
        if ext in extensions:
            return category

    return "Other"


def organize_folder(folder_path):
    """
    Move all files in folder_path into category subfolders.
    Returns list of (original_path, new_path) tuples for moved files.
    """
    moves = []
    folder_path = Path(folder_path)

    if not folder_path.exists():
        print(f"Error: Folder does not exist: {folder_path}")
        return moves

    if not folder_path.is_dir():
        print(f"Error: Path is not a folder: {folder_path}")
        return moves

    # Get all files in the folder (not subfolders)
    try:
        files = [f for f in folder_path.iterdir() if f.is_file()]
    except PermissionError:
        print(f"Error: Permission denied reading folder: {folder_path}")
        return moves

    for file_path in files:
        # Skip files that are downloading
        if file_path.suffix.lower() in SKIP_EXTENSIONS:
            continue

        # Get category and create subfolder
        category = get_category_for_file(file_path.name)
        category_folder = folder_path / category

        try:
            category_folder.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Error: Could not create folder {category_folder}: {e}")
            continue

        # Build destination path
        destination = category_folder / file_path.name

        # If file exists at destination, add number suffix
        if destination.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while destination.exists():
                new_name = f"{stem} ({counter}){suffix}"
                destination = category_folder / new_name
                counter += 1

        # Move the file
        try:
            shutil.move(str(file_path), str(destination))
            moves.append((str(file_path), str(destination)))
        except PermissionError:
            print(f"Error: Permission denied moving {file_path.name}")
        except Exception as e:
            print(f"Error: Could not move {file_path.name}: {e}")

    return moves


def organize_file(folder_path, file_path):
    """
    Move a single file into its category subfolder.
    Returns the new path if successful, None otherwise.
    """
    folder_path = Path(folder_path)
    file_path = Path(file_path)

    if not file_path.exists():
        return None

    # Get category and create subfolder
    category = get_category_for_file(file_path.name)
    category_folder = folder_path / category

    try:
        category_folder.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Error: Could not create folder {category_folder}: {e}")
        return None

    # Build destination path
    destination = category_folder / file_path.name

    # If file exists at destination, add number suffix
    if destination.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        counter = 1
        while destination.exists():
            new_name = f"{stem} ({counter}){suffix}"
            destination = category_folder / new_name
            counter += 1

    # Move the file
    try:
        shutil.move(str(file_path), str(destination))
        return str(destination)
    except PermissionError:
        print(f"Error: Permission denied moving {file_path.name}")
    except Exception as e:
        print(f"Error: Could not move {file_path.name}: {e}")

    return None


def undo_move(original_path, new_path):
    """
    Move a file back to its original location.
    If destination already exists, adds a number suffix (1), (2).
    Returns the restored path if successful, None otherwise.
    """
    current_path = Path(new_path)
    dest_path = Path(original_path)

    if not current_path.exists():
        return None

    # Ensure destination directory exists
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: Could not access destination folder: {e}")
        return None

    # If file exists at destination, add number suffix to avoid overwriting
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_path.parent / f"{stem} ({counter}){suffix}"
            counter += 1

    try:
        shutil.move(str(current_path), str(dest_path))
        return str(dest_path)
    except PermissionError:
        print(f"Error: Permission denied moving {current_path.name}")
    except Exception as e:
        print(f"Error: Could not move {current_path.name}: {e}")

    return None

