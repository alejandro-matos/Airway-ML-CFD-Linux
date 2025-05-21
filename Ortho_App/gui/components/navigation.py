import customtkinter as ctk
from gui.config.settings import UI_SETTINGS
from tkinter import messagebox
import os
import platform
import subprocess
from datetime import datetime

class NavigationFrame(ctk.CTkFrame):
    """A navigation frame with back/next buttons and labels, ensuring no duplicates"""
    def __init__(self, parent, previous_label="", next_label="", 
                 back_command=None, next_command=None):
        
        # First, remove any existing NavigationFrame instances in the parent
        for widget in parent.winfo_children():
            if isinstance(widget, NavigationFrame):
                widget.destroy()

        # Set background color to provide an outline effect
        super().__init__(parent, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        # Create container for back button
        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=40, pady=(5, 10))  # Ensure spacing

        # Create container for next button
        self.next_frame = self._create_button_frame("Next", next_label, next_command)
        self.next_frame.pack(side="right", padx=40, pady=(5, 10))  # Ensure spacing

        # Store references to parent, commands, and buttons for later use
        self.parent = parent
        self.back_command = back_command
        self.next_command = next_command
        
        # Store reference to the buttons
        self.back_button = None
        self.next_button = None

    def _create_button_frame(self, button_text, label_text, command):
        """Create a frame containing a label above a button"""
        frame = ctk.CTkFrame(self, fg_color="transparent")

        if label_text:
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
                text_color="gray70"
            )
            label.pack(side="top", pady=(0, 5))  # Keep label above button

        button = ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            width=150,
            height=50,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        )
        button.pack(side="top")  # Button stays below label
        
        # Store button references
        if button_text == "Back":
            self.back_button = button
        elif button_text == "Next":
            self.next_button = button

        return frame

class NavigationFrame2(ctk.CTkFrame):
    """A navigation frame with back/next buttons and labels, ensuring no duplicates"""
    def __init__(self, parent, previous_label="", next_label="", 
                 back_command=None, next_command=None):
        
        # First, remove any existing NavigationFrame instances in the parent
        for widget in parent.winfo_children():
            if isinstance(widget, NavigationFrame):
                widget.destroy()

        # Set background color to provide an outline effect
        super().__init__(parent, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        # Create container for back button
        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=40, pady=(5, 10))  # Ensure spacing
        
        # Store references for later use
        self.parent = parent
        self.back_command = back_command
        self.back_button = None
        
    def _create_button_frame(self, button_text, label_text, command):
        """Create a frame containing a label above a button"""
        frame = ctk.CTkFrame(self, fg_color="transparent")

        if label_text:
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
                text_color="gray70"
            )
            label.pack(side="top", pady=(0, 5))  # Keep label above button

        button = ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            width=150,
            height=50,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        )
        button.pack(side="top")  # Button stays below label
        
        # Store button reference
        if button_text == "Back":
            self.back_button = button

        return frame
    
    def add_shutdown_restart_button(self):
        """Add a shutdown/restart button to the navigation frame."""
        shutdown_btn = ctk.CTkButton(
            self,
            text="Shutdown / Restart",
            command=self._prompt_shutdown_restart,
            fg_color="#8b0000",
            hover_color="#a80000",
            text_color="white",
            font=("Arial", 14),
            width=160,
            height=40
        )
        shutdown_btn.grid(row=0, column=2, padx=10, pady=5)

    def _prompt_shutdown_restart(self):
        """Prompt the user to shutdown or restart the computer."""
        choice = messagebox.askquestion(
            "System Action",
            "Do you want to shut down or restart the computer?",
            icon="question"
        )

        if choice == "yes":
            response = messagebox.askyesno("Confirm Action", "Yes = Shutdown\nNo = Restart")
            if response:
                self._shutdown()
            else:
                self._restart()
        else:
            messagebox.showinfo("Cancelled", "No action taken.")

    def _shutdown(self):
        try:
            if platform.system() == "Linux":
                subprocess.call(["systemctl", "poweroff"])
            elif platform.system() == "Windows":
                subprocess.call(["shutdown", "/s", "/t", "1"])
        except Exception as e:
            messagebox.showerror("Error", f"Shutdown failed: {e}")

    def _restart(self):
        try:
            if platform.system() == "Linux":
                subprocess.call(["systemctl", "reboot"])
            elif platform.system() == "Windows":
                subprocess.call(["shutdown", "/r", "/t", "1"])
        except Exception as e:
            messagebox.showerror("Error", f"Restart failed: {e}")
    
    def add_shutdown_restart_button(self, shutdown_cmd, restart_cmd):
        """
        Call this *after* __init__ to add two buttons on the right:
        a “Shutdown” and a “Restart”.
        """
        # Create a little frame to hold both buttons side by side
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(side="right", padx=40, pady=(5,10))

        # Shutdown button
        restart_btn = ctk.CTkButton(
            btn_container,
            text="Restart PC",
            command=restart_cmd,
            width=150, height=50,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        )
        restart_btn.pack(side="left", padx=(0,10))

        # Restart button
        shutdown_btn = ctk.CTkButton(
            btn_container,
            text="Shutdown PC",
            command=shutdown_cmd,
            width=150, height=50,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["WARNING"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        )
        shutdown_btn.pack(side="left")

class ShutdownRestartFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.shutdown_btn = ctk.CTkButton(self, text="Shutdown / Restart", command=self.prompt_action)
        self.shutdown_btn.pack(pady=20)

    def prompt_action(self):
        choice = messagebox.askquestion(
            "System Action",
            "Do you want to shut down or restart the computer?",
            icon='question'
        )

        if choice == "yes":
            response = messagebox.askyesno("Confirm Action", "Yes = Shutdown\nNo = Restart")
            if response:
                self.shutdown()
            else:
                self.restart()
        else:
            messagebox.showinfo("Cancelled", "No action was taken.")

    def _log(self, message):
        log_path = "/home/cfdapp/cfdapp_log.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a") as log:
            log.write(f"[{timestamp}] {message}\n")

    def _cleanup_processes(self):
        self._log("Flushing file system buffers with sync.")
        subprocess.call(["sync"])
        self._log("Killing related processes.")
        for proc in ["nnUNet", "blender", "paraview", "main.py", "python", "snappyHexMesh", 'simpleFoam']:
            subprocess.call(["killall", "-f", proc])

    def shutdown(self):
        if platform.system() == "Linux":
            self._cleanup_processes()
            self._log("Shutting down system.")
            subprocess.call(["sudo", "/sbin/poweroff"])

    def restart(self):
        if platform.system() == "Linux":
            self._cleanup_processes()
            self._log("Restarting system.")
            subprocess.call(["sudo", "/sbin/reboot"])
