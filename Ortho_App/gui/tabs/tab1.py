# gui/tabs/tab1.py

import customtkinter as ctk
from PIL import Image, ImageTk
from customtkinter import CTkImage
import os
import tkinter as tk
import tkinter.messagebox as messagebox
from gui.utils.app_logger import AppLogger
from config.settings import UI_SETTINGS 

class Tab1Manager:
    def __init__(self, app):
        """Initialize Tab1Manager with a reference to the main app"""
        self.app = app
        self.username_var = app.username_var  # Use the centralized variable
        self.logger = AppLogger()  # Use the shared logger
        
    def create_tab(self):
        """Create and set up the home page"""
        self._create_logo_section()
        self._create_title_section()
        self._create_description_section()
        self._create_username_section()
        self._create_next_button()
        
        # Set focus to username entry and bind enter key
        self.app.bind_enter_key(self.validate_username)
        self.username_entry.focus()

    def _create_logo_section(self):
        """Create the logo section at the top of the page with animated GIF support"""
        logo_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        logo_frame.pack(pady=UI_SETTINGS["PADDING"]["LARGE"])  # More space around logo

        try:
            # Path to the GIF file
            gif_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\gui\components\Images\ualberta.gif"
            
            # Create a standard Tkinter label (not CTkLabel) for the animated GIF
            self.gif_frames = []
            self.current_frame = 0

            # Add animation control attribute
            self.animation_running = True
            self.animation_after_id = None
            
            # Load the GIF and extract frames
            gif = Image.open(gif_path)
            
            # Determine desired size (adjust as needed)
            target_width = 250
            target_height = 120
            
            # Count frames in the GIF
            try:
                frame_count = 0
                while True:
                    # Extract and resize each frame
                    gif.seek(frame_count)
                    frame = gif.copy()
                    frame = frame.resize((target_width, target_height), Image.LANCZOS)
                    frame_tk = ImageTk.PhotoImage(frame)
                    self.gif_frames.append(frame_tk)
                    frame_count += 1
            except EOFError:
                # End of frames reached
                pass
            
            # Create a standard tkinter Label (not CTkLabel) for animation
            self.gif_label = tk.Label(logo_frame, image=self.gif_frames[0], bg=self._get_frame_bg_color(logo_frame))
            self.gif_label.pack()
            
            # Start animation if there are multiple frames
            if len(self.gif_frames) > 1:
                self._animate_gif(0)
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load logo: {str(e)}"
            )
            
    def _animate_gif(self, frame_index):
        """Animate the GIF by cycling through frames with safety checks"""
        # Safety check: if label doesn't exist anymore, stop animation
        try:
            if not self.animation_running or not self.gif_label.winfo_exists():
                self.animation_running = False
                return
                
            # Update the image
            self.gif_label.configure(image=self.gif_frames[frame_index])
            
            # Calculate next frame index (loop back to 0 when reaching the end)
            next_frame = (frame_index + 1) % len(self.gif_frames)
            
            # Schedule the next frame update after a delay
            # You can adjust the delay (in ms) to control animation speed
            # Store the after ID so we can cancel it if needed
            self.animation_after_id = self.app.after(50, self._animate_gif, next_frame)
        except Exception as e:
            # If there's any error (like widget destroyed), stop animation
            self.animation_running = False
            self.logger.log_error(f"Animation error: {str(e)}")

    def _stop_animation(self):
        """Stop the GIF animation properly"""
        self.animation_running = False
        if hasattr(self, 'animation_after_id') and self.animation_after_id:
            self.app.after_cancel(self.animation_after_id)
            self.animation_after_id = None
        
    def _get_frame_bg_color(self, frame):
        """Get the background color of the frame for the tkinter Label to match"""
        # Get the actual hex color from the CTkFrame
        if hasattr(frame, 'cget') and frame.cget("fg_color") != "transparent":
            if isinstance(frame.cget("fg_color"), tuple):
                # CTk often uses tuples for colors (light/dark mode)
                return frame.cget("fg_color")[0]  # Use light mode color
            return frame.cget("fg_color")
        # Default to a standard background color if transparent
        return "#F0F0F0"  # Light gray fallback
            
    def _create_title_section(self):
        """Create the title section with app name and welcome message"""
        title_label = ctk.CTkLabel(
            self.app.main_frame,
            text="Ortho CFD Application v0.2\n\nWelcome",
            font=UI_SETTINGS["FONTS"]["TITLE"],  # Using global font settings
            fg_color=UI_SETTINGS["COLORS"]["PRIMARY"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            justify="center",
            width=500,
            height=150
        )
        title_label.pack(fill="x", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])

    def _create_description_section(self):
        """Create the description section with app information"""
        description_text = (
            "[ApplicationTK] calculates the pressure difference in the \n"
            "nasal cavity from 3D X-RAY scans using Computational Fliud Dynamics analysis.\n"
            "Supported file formats: DICOM (.dcm), NIfTI (.nii.gz).\n\n"
            "This application was built using: Python 3.11, nnUNetv2, Blender 2.82, OpenFOAM v2306, ParaView 5.12.\n\n"
            "For inquiries, contact:\n"            "Dr. Carlos Lange - clange@ualberta.ca"
        )

        description_label = ctk.CTkLabel(
            self.app.main_frame,
            text=description_text,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            justify="center",
            wraplength=600  # Ensures text is readable on wider screens
        )
        description_label.pack(pady=UI_SETTINGS["PADDING"]["MEDIUM"])
    
    def _create_username_section(self):
        """Create the username input section with a modern design"""
        username_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        username_frame.pack(pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Label
        username_label = ctk.CTkLabel(
            username_frame,
            text="Enter Username:",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        username_label.pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Recreate username entry and bind it to username_var
        self.username_entry = ctk.CTkEntry(
            username_frame,
            textvariable=self.app.username_var,  # Rebind to the reinitialized variable
            width=250,
            fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        )
        self.username_entry.pack(side="left", padx=UI_SETTINGS["PADDING"]["SMALL"])

    def _create_next_button(self):
        """Create a well-sized 'Next' button with a modern design"""
        next_button = ctk.CTkButton(
            self.app.main_frame,
            text="Next",
            command=self.validate_username,
            width=160,
            height=50,
            font=UI_SETTINGS["FONTS"]["HEADER"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        next_button.pack(pady=(UI_SETTINGS["PADDING"]["MEDIUM"], UI_SETTINGS["PADDING"]["LARGE"]))

    def validate_username(self):
        """Check if username is valid before proceeding"""
        username = self.app.username_var.get().strip()  # Use the centralized variable

        if not username:
            error_message = "Please enter a username."
            self.logger.log_error(error_message)
            tk.messagebox.showerror("Error", error_message)
            return False

        if not username.isalnum():
            error_message = f"Username '{username}' must contain only letters and numbers."
            self.logger.log_error(error_message)
            tk.messagebox.showerror("Error", "Username must contain only letters and numbers.")
            return False
        
        self._stop_animation()
        self.logger.log_info(f"User logged in: {username}")
        self.app.stored_username = username
        self.app.create_tab2()  # Navigate to next tab
        return True
