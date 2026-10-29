"""CustomTkinter User Interface for Downloads Organizer."""

import threading
from pathlib import Path
import customtkinter as ctk
from watcher import start_watching, IGNORED_FILES
from organizer import undo_move, organize_folder

# Set appearance mode and color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DownloadsOrganizerApp(ctk.CTk):
    """Main application window for Downloads Organizer."""

    def __init__(self):
        super().__init__()

        self.title("Downloads Organizer")
        self.geometry("500x480")
        self.minsize(450, 420)

        self.observer = None
        self.is_running = False
        self.history = []  # list of (original_path, new_path)
        self.downloads_path = Path.home() / "Downloads"

        # --- UI Layout ---

        # Title
        self.title_label = ctk.CTkLabel(
            self, text="Downloads Organizer", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))

        # Subtitle / Folder path
        self.folder_label = ctk.CTkLabel(
            self, text=f"Watching: {self.downloads_path}", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.folder_label.pack(pady=(0, 15))

        # Switch Frame (Switch + Status Label side-by-side)
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=(0, 10))

        self.switch_var = ctk.StringVar(value="off")
        self.switch = ctk.CTkSwitch(
            self.control_frame,
            text="Organizer Active",
            command=self.toggle_organizer,
            variable=self.switch_var,
            onvalue="on",
            offvalue="off",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.switch.pack(side="left", padx=10)

        self.status_label = ctk.CTkLabel(
            self.control_frame, text="Status: OFF", font=ctk.CTkFont(size=13), text_color="orange"
        )
        self.status_label.pack(side="left", padx=10)

        # Folder path entry (editable)
        self.path_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.path_frame.pack(pady=(0, 5))

        self.path_entry = ctk.CTkEntry(self.path_frame, width=300, font=ctk.CTkFont(size=11))
        self.path_entry.insert(0, str(self.downloads_path))
        self.path_entry.pack(side="left", padx=5)

        self.set_path_button = ctk.CTkButton(
            self.path_frame,
            text="Set Folder",
            command=self.set_watching_path,
            font=ctk.CTkFont(size=11),
            width=80
        )
        self.set_path_button.pack(side="left", padx=5)

        # Undo Button
        self.undo_button = ctk.CTkButton(
            self,
            text="Undo last move",
            command=self.undo_last_move,
            font=ctk.CTkFont(size=13),
            width=140
        )
        self.undo_button.pack(pady=(0, 8))

        # Organize Now Button
        self.organize_now_button = ctk.CTkButton(
            self,
            text="Organize folder now",
            command=self.organize_now,
            font=ctk.CTkFont(size=13),
            width=160
        )
        self.organize_now_button.pack(pady=(0, 15))

        # Log Box (scrolling text box)
        self.log_textbox = ctk.CTkTextbox(self, width=440, height=240, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        self.log_textbox.configure(state="disabled")

        # Handle window close event gracefully
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_message(self, message):
        """Append a message to the scrolling log box (thread-safe)."""
        def _append():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", message + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")

        # Ensure UI updates happen on the main thread
        self.after(0, _append)

    def set_watching_path(self):
        """Update the folder path that is being watched."""
        new_path = Path(self.path_entry.get().strip())
        if new_path.exists():
            self.downloads_path = new_path
            self.folder_label.configure(text=f"Watching: {self.downloads_path}")
            self.log_message(f"Changed watched folder to: {self.downloads_path}")
        else:
            self.log_message(f"Error: Folder does not exist: {new_path}")

    def remove_log_entry(self, original_path, new_path):
        """Remove the log entry for a specific move from the log box."""
        filename = Path(original_path).name
        category = Path(new_path).parent.name
        expected_line = f"Moved {filename} to {category}"

        def _remove():
            content = self.log_textbox.get("1.0", "end-1c")
            lines = content.split("\n")
            # Find and remove the latest matching line
            for i in range(len(lines) - 1, -1, -1):
                if lines[i] == expected_line:
                    lines.pop(i)
                    break
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            new_text = "\n".join(lines)
            if new_text:
                self.log_textbox.insert("1.0", new_text + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")

        self.after(0, _remove)

    def on_file_moved(self, original_path, new_path):
        """Callback when the watcher moves a file."""
        self.history.append((original_path, new_path))
        filename = Path(original_path).name
        category = Path(new_path).parent.name
        self.log_message(f"Moved {filename} to {category}")

    def undo_last_move(self):
        """Undo the most recent file move."""
        if not self.history:
            self.log_message("Nothing to undo.")
            return

        original_path, new_path = self.history.pop()
        current_file = Path(new_path)

        # Handle the case where the file no longer exists
        if not current_file.exists():
            self.log_message(f"Cannot undo: {current_file.name} no longer exists.")
            self.remove_log_entry(original_path, new_path)
            return

        # Temporarily ignore the restored file so watcher doesn't re-organize it
        target_path = Path(original_path)
        IGNORED_FILES.add(target_path.resolve())

        # Move the file back
        restored_path = undo_move(original_path, new_path)

        if restored_path:
            # If renamed on undo, update ignored set
            IGNORED_FILES.add(Path(restored_path).resolve())
            self.remove_log_entry(original_path, new_path)
        else:
            IGNORED_FILES.discard(target_path.resolve())
            self.log_message(f"Failed to undo move for {current_file.name}")

    def toggle_organizer(self):
        """Start or stop the folder watcher based on the switch state."""
        if self.switch_var.get() == "on":
            self.start_organizer()
        else:
            self.stop_organizer()

    def start_organizer(self):
        """Start the background watcher thread."""
        if self.is_running:
            return

        self.log_message(f"Starting watcher on {self.downloads_path}...")

        # Run watcher in background thread so UI never freezes
        def run_watcher():
            try:
                self.observer = start_watching(self.downloads_path, on_move=self.on_file_moved)
            except Exception as e:
                self.log_message(f"Error starting watcher: {e}")

        threading.Thread(target=run_watcher, daemon=True).start()
        self.is_running = True
        self.status_label.configure(text="Status: ON", text_color="green")
        self.log_message("Organizer is now RUNNING.")

    def stop_organizer(self):
        """Stop the background watcher."""
        if not self.is_running:
            return

        self.log_message("Stopping watcher...")
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception as e:
                self.log_message(f"Error stopping watcher: {e}")
            self.observer = None

        self.is_running = False
        self.status_label.configure(text="Status: OFF", text_color="orange")
        self.log_message("Organizer is now STOPPED.")

    def organize_now(self):
        """Organize the current folder immediately."""
        self.log_message(f"Organizing folder: {self.downloads_path}")
        try:
            moves = organize_folder(self.downloads_path)
            if moves:
                for original, new in moves:
                    self.log_message(f"Moved {original} to {new}")
            else:
                self.log_message("No files to organize.")
        except Exception as e:
            self.log_message(f"Error organizing folder: {e}")

    def on_closing(self):
        """Stop watcher and close window when X button is clicked."""
        if self.is_running:
            self.stop_organizer()
        self.destroy()
