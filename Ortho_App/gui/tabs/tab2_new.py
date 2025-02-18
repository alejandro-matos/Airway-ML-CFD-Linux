# gui/tabs/tab2.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import pydicom
from pathlib import Path

from config.settings import UI_SETTINGS  # Import global UI settings
from gui.utils.app_logger import AppLogger

BASE_PATH = Path.home() / "Desktop"
REQUIRED_FIELDS = [
    ('patient_name', "Patient Name"),
    ('dob', "Date of Birth"),
    ('scandate', "Scan Date"),
    ('patient_doctor_var', "Referring Physician"),
    ('folder_name_var', "Patient Results Folder")
]

class Tab2Manager:
    def __init__(self, app):
        """Initialize Tab2Manager with a reference to the main app"""
        self.app = app
        if not hasattr(self.app, 'folder_name_var'):
            self.app.folder_name_var = tk.StringVar()
        self.logger = AppLogger()

    def create_tab(self):
        """Create and set up the patient information page"""
        self._create_header()
        
        # Ensure main frame expands properly
        self.main_frame = ctk.CTkFrame(self.app.main_frame)
        self.main_frame.pack(fill="both", expand=True, padx=UI_SETTINGS["PADDING"]["LARGE"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        self._create_upload_section()
        self._create_patient_info_section()
        self._create_folder_section()
        self._create_navigation()

    def _create_header(self):
        """Create the header with home button and step indicator"""
        top_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Home button
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=self.app.go_home,
            width=80,
            height=40,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            fg_color=UI_SETTINGS["COLORS"]["BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["HOVER"]
        ).pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text="Step 1 of 4: Upload Patient Scans & Information",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            anchor="center"
        ).pack(side="left", expand=True)

    def _create_upload_section(self):
        """Create the file upload section with uniform styling"""
        upload_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        upload_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        ctk.CTkLabel(
            upload_frame,
            text="Upload Patient Scans",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

        self.folder_status_label = ctk.CTkLabel(
            upload_frame,
            text="No folder selected",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        self.folder_status_label.pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

        # Folder selection button
        select_button = ctk.CTkButton(
            upload_frame,
            text="Select Patient Folder",
            command=self._handle_folder_selection,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            fg_color=UI_SETTINGS["COLORS"]["BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["HOVER"]
        )
        select_button.pack(pady=UI_SETTINGS["PADDING"]["MEDIUM"])

    def _create_patient_info_section(self):
        """Create the patient information form section with uniform styling"""
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        ctk.CTkLabel(
            info_frame,
            text="Patient Information",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

        form_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        form_frame.pack(fill="x")

        fields = [
            ("Patient Name:", self.app.patient_name),
            ("Date of Birth (YYYY-MM-DD):", self.app.dob),
            ("Scan Date (YYYY-MM-DD):", self.app.scandate),
            ("Referring Physician:", self.app.patient_doctor_var)
        ]

        for label_text, variable in fields:
            row_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["SMALL"])

            ctk.CTkLabel(
                row_frame,
                text=label_text,
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                width=200,
                anchor="e"
            ).pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

            ctk.CTkEntry(
                row_frame,
                textvariable=variable,
                width=250,
                fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
            ).pack(side="left")

    def _create_folder_section(self):
        """Create the case label/folder selection section with uniform styling"""
        folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        folder_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        ctk.CTkLabel(
            folder_frame,
            text="Case Label",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

        ctk.CTkEntry(
            folder_frame,
            textvariable=self.app.folder_name_var,
            width=300,
            fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        ).pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

    def _create_navigation(self):
        """Create navigation buttons with uniform styling"""
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["LARGE"])

        # Back button
        back_button = ctk.CTkButton(
            nav_frame,
            text="Back",
            command=self.app.create_tab1,
            width=120,
            height=40,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            fg_color=UI_SETTINGS["COLORS"]["BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["HOVER"]
        )
        back_button.pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Next button
        next_button = ctk.CTkButton(
            nav_frame,
            text="Next",
            command=self._validate_and_proceed,
            width=120,
            height=40,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            fg_color=UI_SETTINGS["COLORS"]["BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["HOVER"]
        )
        next_button.pack(side="right", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

    def _validate_and_proceed(self):
        """Validate the form and proceed to the next tab"""
        if not self.app.folder_name_var.get():
            messagebox.showerror("Error", "Please enter a case label.")
            return

        self.app.create_tab3()

    def _handle_folder_selection(self):
        """Handle the selection of DICOM folder"""
        folder_path = filedialog.askdirectory(title="Select Patient Folder")
        self.logger.log_info(f"Patient folder selected: {folder_path}")
        if not folder_path:
            return

        try:
            dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dcm')]
            if not dicom_files:
                raise ValueError("No DICOM files found in the selected directory.")

            self.app.selected_dicom_folder = folder_path
            self.folder_status_label.configure(
                text=f"Selected folder: {Path(folder_path).name}"
            )

            dicom_path = Path(folder_path) / dicom_files[0]
            self._extract_patient_info(pydicom.dcmread(str(dicom_path)))
            self._update_folder_dropdown()
            
            messagebox.showinfo("Success", "Patient details loaded successfully.")
            
        except Exception as e:
            self.logger.log_error("Failed to read patient details", e)
            messagebox.showerror("Error", f"Failed to read patient details: {e}")
            self.folder_status_label.configure(text="")
