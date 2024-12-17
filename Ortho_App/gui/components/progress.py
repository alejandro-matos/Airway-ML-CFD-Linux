# gui/components/progress.py
import customtkinter as ctk
from tkinter import ttk

class ProgressSection(ctk.CTkFrame):
    """A progress section with progress bar and label"""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.progress_bar = ttk.Progressbar(self, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=50, pady=(10, 5))

        self.progress_label = ctk.CTkLabel(self, text="")
        self.progress_label.pack(pady=5)

    def start(self, message="Processing..."):
        """Start the progress bar with a message"""
        self.progress_label.configure(text=message)
        self.progress_bar.start()

    def stop(self, message="Complete"):
        """Stop the progress bar and update message"""
        self.progress_bar.stop()
        self.progress_label.configure(text=message)