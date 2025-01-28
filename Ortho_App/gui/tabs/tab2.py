# gui/tabs/tab2.py

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import pydicom
from pathlib import Path

from ..components.buttons import CircularButton
from ..components.forms import FormSection, LabeledEntry
from ..components.navigation import NavigationFrame
from ..utils.tooltips import ToolTip

# Constants
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
        
    def create_tab(self):
        """Create and set up the patient information page"""
        self._create_header()
        self.main_frame = self._create_main_frame()
        self._create_upload_section()
        self._create_patient_info_section()
        self._create_folder_section()
        self._create_navigation()

    def _create_header(self):
        """Create the header with home button and step indicator"""
        top_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 5))

        # Home button
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=self.app.go_home,
            width=80,
            height=40,
            font=("Times_New_Roman", 16)
        ).pack(side="left", padx=5)

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text="Step 1 of 4: Upload Patient Scans & Information",
            font=("Arial", 15),
            anchor="center"
        ).pack(side="left", expand=True)

    def _create_main_frame(self):
        """Create the main content frame with grid layout"""
        main_frame = ctk.CTkFrame(self.app.main_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        return main_frame

    def _create_upload_section(self):
        """Create the file upload section"""
        upload_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        upload_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            upload_frame,
            text="Upload Patient Scans",
            font=("Arial", 15, "bold")
        ).pack(pady=(5, 0))

        self.folder_status_label = ctk.CTkLabel(
            upload_frame,
            text="",
            font=("Arial", 12)
        )
        self.folder_status_label.pack(pady=(5, 0))

        ctk.CTkButton(
            upload_frame,
            text="Select Patient Folder",
            command=self._handle_folder_selection,
            font=("Times_New_Roman", 14)
        ).pack(pady=(5, 10))

    def _create_patient_info_section(self):
        """Create the patient information form section with grid layout"""
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            info_frame,
            text="Patient Information",
            font=("Arial", 15, "bold")
        ).pack(pady=(5, 10))

        form_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Patient Name:", self.app.patient_name),
            ("Date of Birth (YYYY-MM-DD):", self.app.dob),
            ("Scan Date (YYYY-MM-DD):", self.app.scandate),
            ("Referring Physician:", self.app.patient_doctor_var)
        ]

        for i, (label_text, variable) in enumerate(fields):
            ctk.CTkLabel(
                form_frame,
                text=label_text,
                anchor="e"
            ).grid(row=i, column=0, padx=(0, 10), pady=5, sticky="e")

            ctk.CTkEntry(
                form_frame,
                textvariable=variable,
                width=300,
                fg_color="white",
                text_color="black"
            ).grid(row=i, column=1, pady=5, sticky="w")

    def _create_info_button(self, parent, tooltip_text):
        """Create a circular info button with tooltip"""
        info_button = CircularButton(
            parent,
            text="?",
            diameter=20,
            bg_color="#007bff",
            text_color="white",
            border_color="white",
            border_width=1,
            font=("Arial", 10, "bold")
        )
        
        tooltip = ToolTip(info_button, text=tooltip_text)
        info_button.bind('<Enter>', lambda e: tooltip.show_tooltip())
        info_button.bind('<Leave>', lambda e: tooltip.hide_tooltip())
        
        return info_button

    def _create_folder_section(self):
        """Create the folder selection section"""
        folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            folder_frame,
            text="Case Label",
            font=("Arial", 15, "bold")
        ).pack(pady=(5, 10))

        selection_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        selection_frame.pack(fill="x", padx=20, pady=(0, 10))
        selection_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            selection_frame,
            text="Enter or select folder name:",
            anchor="e"
        ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")

        combo_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        combo_frame.grid(row=0, column=1, sticky="w")

        initial_values = self._get_existing_folders() or [""]
        
        self.app.folder_combobox = ctk.CTkComboBox(
            combo_frame,
            width=150,
            variable=self.app.folder_name_var,
            values=initial_values,
            fg_color="white",
            text_color="black",
            state="normal",
            command=self._on_combobox_select
        )
        self.app.folder_combobox.pack(side="left", padx=(0, 5))

        info_button = self._create_info_button(
            combo_frame,
            "Name folder by condition (e.g., 'OSA', 'TMD').\n"
            "Use existing folder name if following up on same condition."
        )
        info_button.pack(side="left")

        ctk.CTkButton(
            selection_frame,
            text="Browse Save Location",
            command=self._handle_save_location,
            font=("Times_New_Roman", 14)
        ).grid(row=1, column=1, pady=(5, 0), sticky="w")

    def _create_navigation(self):
        """Create navigation buttons with descriptive labels"""
        nav_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        nav_frame.pack(fill="x", side="bottom", pady=10)

        # Back button and label
        back_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        back_frame.pack(side="left", padx=20)
        
        ctk.CTkButton(
            back_frame,
            text="Back",
            command=self.app.create_tab1,
            width=100,
            font=("Times_New_Roman", 16)
        ).pack()
        
        ctk.CTkLabel(
            back_frame,
            text="Home Page",
            font=("Arial", 12),
            text_color="gray"
        ).pack()

        # Next button and label
        next_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        next_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(
            next_frame,
            text="Next",
            command=self._validate_and_proceed,
            width=100,
            font=("Times_New_Roman", 16)
        ).pack()
        
        ctk.CTkLabel(
            next_frame,
            text="Review and Confirm",
            font=("Arial", 12),
            text_color="gray"
        ).pack()

    def _on_combobox_select(self, choice):
        """Handle ComboBox selection"""
        if choice:
            self.app.folder_name_var.set(choice)

    def _update_folder_dropdown(self):
        """Update folder dropdown values"""
        if hasattr(self.app, 'folder_combobox'):
            current_folders = self._get_existing_folders() or [""]
            
            if set(self.app.folder_combobox.cget("values")) != set(current_folders):
                self.app.folder_combobox.configure(
                    values=current_folders,
                    state="normal"
                )
                self.app.folder_combobox.set("")

    def _get_existing_folders(self):
        """Get list of existing folders for the current patient"""
        if not all([self.app.username_var.get(), self.app.patient_name.get()]):
            return []

        try:
            patient_path = BASE_PATH / self.app.username_var.get() / self.app.patient_name.get()
            
            if patient_path.exists():
                folders = [
                    folder.name for folder in patient_path.iterdir()
                    if folder.is_dir()
                ]
                return sorted(folders)
            return []
        except Exception as e:
            print(f"Error getting folders: {e}")
            return []

    def _handle_folder_selection(self):
        """Handle the selection of DICOM folder"""
        folder_path = filedialog.askdirectory(title="Select Patient Folder")
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
            messagebox.showerror("Error", f"Failed to read patient details: {e}")
            self.folder_status_label.configure(text="")

    def _extract_patient_info(self, dicom_data):
        """Extract patient information from DICOM data"""
        # Name
        self.app.patient_name.set(str(dicom_data.PatientName))

        # Doctor
        if hasattr(dicom_data, "ReferringPhysicianName"):
            doctor = dicom_data.ReferringPhysicianName
            self.app.patient_doctor_var.set(f"{doctor.family_name}, {doctor.given_name}")
        else:
            self.app.patient_doctor_var.set("Not available")

        # Dates
        for date_attr, var in [
            ("PatientBirthDate", self.app.dob),
            ("StudyDate", self.app.scandate)
        ]:
            if hasattr(dicom_data, date_attr):
                date_str = getattr(dicom_data, date_attr)
                if len(date_str) == 8:
                    formatted_date = datetime.strptime(
                        date_str, "%Y%m%d"
                    ).strftime("%Y-%m-%d")
                    var.set(formatted_date)
                else:
                    var.set("Invalid Date")

    def _setup_output_folder(self):
        """Set up the output folder path"""
        missing_fields = [
            name for attr_name, name in REQUIRED_FIELDS 
            if not getattr(self.app, attr_name).get()
        ]
        
        if missing_fields:
            messagebox.showerror(
                "Error",
                f"Please provide: {', '.join(missing_fields)}"
            )
            return False

        try:
            folder_path = (
                BASE_PATH / 
                self.app.username_var.get() / 
                self.app.patient_name.get() / 
                self.app.folder_name_var.get()
            )
            self.app.full_folder_path = str(folder_path)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not set up folder path: {e}")
            return False

    def _handle_save_location(self):
        """Handle the selection of save location"""
        if not self._setup_output_folder():
            return

        selected_folder = filedialog.askdirectory(
            title="Confirm or Adjust Folder Location",
            initialdir=self.app.full_folder_path
        )

        if selected_folder:
            self.app.folder_name_var.set(Path(selected_folder).name)
            self.app.full_folder_path = selected_folder
            messagebox.showinfo(
                "Success", 
                f"Selected output folder:\n{selected_folder}"
            )

        self._update_folder_dropdown()

    def _validate_and_proceed(self):
        """Validate the form and proceed to next tab"""
        if not self._setup_output_folder():
            return
            
        self.app.create_tab3()