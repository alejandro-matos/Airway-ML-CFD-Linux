import customtkinter as ctk
from gui.config.settings import UI_SETTINGS
from tkinter import messagebox
import os
import subprocess
from datetime import datetime

class NavigationFrame(ctk.CTkFrame):
    """Back/Next navigation with no duplicates."""
    def __init__(self, parent, previous_label="", next_label="", back_command=None, next_command=None):
        # Remove any old nav frames
        for w in parent.winfo_children():
            if w.__class__.__name__ in ("NavigationFrame", "NavigationFrame2"):
                w.destroy()

        super().__init__(parent, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        self.back_button = None
        self.next_button = None

        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=(5,10))

        self.next_frame = self._create_button_frame("Next", next_label, next_command)
        self.next_frame.pack(side="right", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=(5,10))

    def _create_button_frame(self, btn_text, label_text, cmd):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        if label_text:
            lbl = ctk.CTkLabel(frame,
                               text=label_text,
                               font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
                               text_color="gray70")
            lbl.pack(side="top", pady=(0,5))
        btn = ctk.CTkButton(frame,
                            text=btn_text,
                            command=cmd,
                            width=150, height=50,
                            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
                            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"])
        btn.pack(side="top")
        if btn_text == "Back":
            self.back_button = btn
        else:
            self.next_button = btn
        return frame


class NavigationFrame2(ctk.CTkFrame):
    """Back button + optional Shutdown/Restart buttons."""
    def __init__(self, parent, previous_label="", back_command=None):
        for w in parent.winfo_children():
            if w.__class__.__name__ in ("NavigationFrame", "NavigationFrame2"):
                w.destroy()

        super().__init__(parent, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        self.back_button = None
        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=(5,10))

    def _create_button_frame(self, btn_text, label_text, cmd):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        if label_text:
            lbl = ctk.CTkLabel(frame,
                               text=label_text,
                               font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
                               text_color="gray70")
            lbl.pack(side="top", pady=(0,5))
        btn = ctk.CTkButton(frame,
                            text=btn_text,
                            command=cmd,
                            width=150, height=50,
                            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
                            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"])
        btn.pack(side="top")
        if btn_text == "Back":
            self.back_button = btn
        return frame

    def add_shutdown_restart_buttons(self, shutdown_cmd=None, restart_cmd=None):
        """Adds two buttons: Restart PC and Shutdown PC."""
        shutdown_cmd = shutdown_cmd or self._shutdown
        restart_cmd  = restart_cmd  or self._restart

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(side="right", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=(5,10))

        restart_btn = ctk.CTkButton(container,
                                    text="Restart PC",
                                    command=restart_cmd,
                                    width=150, height=50,
                                    font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                                    fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
                                    hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"])
        restart_btn.pack(side="left", padx=(0,10))

        shutdown_btn = ctk.CTkButton(container,
                                     text="Shutdown PC",
                                     command=shutdown_cmd,
                                     width=150, height=50,
                                     font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                                     fg_color=UI_SETTINGS["COLORS"]["WARNING"],
                                     hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"])
        shutdown_btn.pack(side="left")

    def _cleanup_before_shutdown(self):
        """Perform cleanup operations before shutdown/restart."""
        # First sync to flush pending operations
        subprocess.call(["sync"])
        
        # Kill potentially running processes
        for process in ["nnUNet", "blender", "paraview", "python", "snappyHexMesh", "simpleFoam"]:
            try:
                subprocess.call(["killall", "-f", process])
            except Exception as e:
                print(f"Error killing {process}: {e}")
        
        # Final sync to ensure everything is written to disk
        subprocess.call(["sync"])
        
        # Log the cleanup action if possible
        try:
            log_path = os.path.expanduser("~/cfdapp_log.txt")
            with open(log_path, "a") as f:
                f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Cleanup performed before system action\n")
        except:
            pass  # Ignore logging errors

    def _shutdown(self):
        """Perform cleanup and shut down the system."""
        # Confirm with the user
        if messagebox.askyesno("Confirm Shutdown", "Are you sure you want to shut down the computer?"):
            # Perform cleanup
            self._cleanup_before_shutdown()
            
            # Execute shutdown command for Linux
            subprocess.call(["sudo", "/sbin/poweroff"])
        
    def _restart(self):
        """Perform cleanup and restart the system."""
        # Confirm with the user
        if messagebox.askyesno("Confirm Restart", "Are you sure you want to restart the computer?"):
            # Perform cleanup
            self._cleanup_before_shutdown()
            
            # Execute restart command for Linux
            subprocess.call(["sudo", "/sbin/reboot"])


class ShutdownRestartFrame(ctk.CTkFrame):
    """Standalone Shutdown/Restart prompt button."""
    def __init__(self, master):
        super().__init__(master, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        btn = ctk.CTkButton(self,
                            text="Shutdown / Restart",
                            command=self.prompt_action,
                            width=160, height=50,
                            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                            fg_color=UI_SETTINGS["COLORS"]["WARNING"],
                            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
                            text_color="white")
        btn.pack(pady=20)

    def prompt_action(self):
        choice = messagebox.askquestion("System Action",
                                        "Do you want to shut down or restart the computer?",
                                        icon="question")
        if choice == "yes":
            confirm = messagebox.askyesno("Confirm Action", "Yes = Shutdown\nNo = Restart")
            if confirm:
                self._shutdown()
            else:
                self._restart()
        else:
            messagebox.showinfo("Cancelled", "No action taken.")

    def _cleanup_before_shutdown(self):
        """Perform cleanup operations before shutdown/restart."""
        # Log the action
        self._log("Cleaning up before system action")
        
        # First sync
        subprocess.call(["sync"])
        
        # Kill processes
        for p in ["nnUNet", "blender", "paraview", "python", "snappyHexMesh", "simpleFoam"]:
            try:
                subprocess.call(["killall", "-f", p])
            except:
                pass
        
        # Final sync
        subprocess.call(["sync"])

    def _shutdown(self):
        """Clean up and shut down."""
        self._cleanup_before_shutdown()
        subprocess.call(["sudo", "/sbin/poweroff"])

    def _restart(self):
        """Clean up and restart."""
        self._cleanup_before_shutdown()
        subprocess.call(["sudo", "/sbin/reboot"])

    def _log(self, message):
        """Write message to log file."""
        path = os.path.expanduser("~/cfdapp_log.txt")
        try:
            with open(path, "a") as f:
                f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")
        except:
            pass  # Ignore logging errors