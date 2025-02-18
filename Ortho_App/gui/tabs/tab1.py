# gui/tabs/tab1.py

import customtkinter as ctk
from PIL import Image
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
        """Create the logo section at the top of the page"""
        logo_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        logo_frame.pack(pady=UI_SETTINGS["PADDING"]["LARGE"])  # More space around logo

        try:
            logo_image = Image.open("/home/amatos/Desktop/GUI/Airway-ML-CFD-Linux/Ortho_App/gui/components/Images/ualbertalogo.png")
            logo_ctk_image = CTkImage(logo_image, size=(250,120))
            logo_label = ctk.CTkLabel(logo_frame, image=logo_ctk_image, text="")
            logo_label.pack()
        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                "Logo file not found. Please place 'ualbertalogo.png' in the same directory."
            )
            
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

        self.logger.log_info(f"User logged in: {username}")
        self.app.stored_username = username
        self.app.create_tab2()  # Navigate to next tab
        return True
