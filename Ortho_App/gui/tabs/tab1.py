# gui/tabs/tab1.py

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import os
import tkinter.messagebox as messagebox

class Tab1Manager:
    def __init__(self, app):
        """Initialize Tab1Manager with a reference to the main app"""
        self.app = app
        
    def create_tab(self):
        """Create and set up the home page"""
        self._create_logo_section()
        self._create_title_section()
        self._create_description_section()
        self._create_username_section()
        self._create_next_button()
        
        # Set focus to username entry and bind enter key
        self.app.bind_enter_key(self.app.validate_username)
        self.username_entry.focus()

    def _create_logo_section(self):
        """Create the logo section at the top of the page"""
        logo_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        logo_frame.pack(side="top", pady=10)

        try:
            logo_image = Image.open("ualbertalogo.png")
            logo_ctk_image = CTkImage(logo_image, size=(150, 80))
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
            font=("Times_New_Roman", 25),
            fg_color='#255233',
            text_color="white",
            justify="center",
            width=450,
            height=100
        )
        title_label.pack(pady=10)

    def _create_description_section(self):
        """Create the description section with app information"""
        description_text = (
            "This app calculates the pressure difference in the \n"
            "nasal cavity from 3D X-RAY scans using CFD analysis.\n"
            "Input files must be in STL or OBJ format.\n\n"
            "This app uses Blender, OpenFOAM, and Paraview.\n\n"
            "For more information, contact Dr. Carlos Lange\n"
            "email: clange@ualberta.ca"
        )
        
        description_label = ctk.CTkLabel(
            self.app.main_frame,
            text=description_text,
            font=("Times_New_Roman", 15),
            justify="center"
        )
        description_label.pack(pady=20)

    def _create_username_section(self):
        """Create the username input section"""
        username_frame = ctk.CTkFrame(
            self.app.main_frame,
            fg_color="transparent"
        )
        username_frame.pack(pady=20)

        # Configure grid layout
        username_frame.columnconfigure(0, weight=1)
        username_frame.columnconfigure(1, weight=1)
        username_frame.columnconfigure(2, weight=1)

        # Create username label
        username_label = ctk.CTkLabel(
            username_frame,
            text="Username:",
            font=("Arial", 15)
        )
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        # Create username entry
        self.username_entry = ctk.CTkEntry(
            username_frame,
            textvariable=self.app.username_var,
            width=300,
            fg_color="white",
            text_color="black"
        )
        self.username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    def _create_next_button(self):
        """Create the next button to proceed to Tab 2"""
        next_button = ctk.CTkButton(
            self.app.main_frame,
            text="Next",
            command=self.app.validate_username,
            width=140,
            height=40,
            font=("Times_New_Roman", 20)
        )
        next_button.pack(pady=(10, 20))

    def handle_enter_key(self, event=None):
        """Handle Enter key press"""
        self.app.validate_username()

    def destroy(self):
        """Clean up resources when tab is destroyed"""
        self.app.unbind_enter_key()