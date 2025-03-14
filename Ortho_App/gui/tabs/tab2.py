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
from gui.utils.app_logger import AppLogger
from config.settings import UI_SETTINGS

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
        self.logger = AppLogger()  # Use the shared logge
        
    def create_tab(self):
        """Create and set up the patient information page"""
        self._create_header()
        
        # Make sure main frame expands properly
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
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        ).pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text="Step 1 of 3: Upload Patient Scans & Information",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            anchor="center"
        ).pack(side="left", expand=True)

    def _create_main_frame(self):
        """Create the main content frame with grid layout"""
        main_frame = ctk.CTkFrame(self.app.main_frame)
        main_frame.pack(fill="both", expand=True, padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])
        return main_frame

    def _create_upload_section(self):
        """Create the file upload section using only native file dialog filtering"""
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
            text="No files selected",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        self.folder_status_label.pack(pady=UI_SETTINGS["PADDING"]["SMALL"])
        
        # File selection button with adjacent info button
        selection_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        selection_frame.pack(pady=(5, 10))
        
        select_button = ctk.CTkButton(
            selection_frame,
            text="Browse for Medical Images",
            command=self._handle_folder_selection,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            width=220,
            height=50,
        )
        select_button.pack(side="left")
        
        # Info button with tooltip explanation
        info_button = self._create_info_button(
            selection_frame,
            "Select one or more medical image files.\nUse the file type dropdown in the file browser to filter for DICOM (.dcm) or NIfTI (.nii, .nii.gz) files."
        )
        info_button.pack(side="left", padx=5)

    def _on_filetype_change(self, choice):
        """Handle file type dropdown selection"""
        if choice == "DICOM files only":
            self.file_type_var.set("dicom")
        elif choice == "NIfTI files only":
            self.file_type_var.set("nifti")
        else:
            self.file_type_var.set("all")

    def _create_patient_info_section(self):
        """Create the patient information form section with centered alignment"""
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Title Label
        ctk.CTkLabel(
            info_frame,
            text="Patient Information",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

        # Centered Form Frame
        form_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        form_frame.pack(expand=True)  # Centered in available space
        form_frame.grid_columnconfigure(0, weight=1)  # Centering
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
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                anchor="e"
            ).grid(row=i, column=0, padx=(0, 10), pady=5, sticky="e")

            ctk.CTkEntry(
                form_frame,
                textvariable=variable,
                width=300,
                fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
            ).grid(row=i, column=1, padx=(0, 10), pady=5, sticky="w")


    def _create_info_button(self, parent, tooltip_text):
        """Create a circular info button with tooltip"""
        info_button = CircularButton(
            parent,
            text="?",
            diameter=30,
            bg_color="#007bff",
            text_color="white",
            border_color="white",
            border_width=1,
            font=("Arial", 14, "bold")
        )
        
        tooltip = ToolTip(info_button, text=tooltip_text)
        info_button.bind('<Enter>', lambda e: tooltip.show_tooltip())
        info_button.bind('<Leave>', lambda e: tooltip.hide_tooltip())
        
        return info_button

    def _create_folder_section(self):
        """Create the folder selection section and reduce vertical spacing"""
        folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        folder_frame.pack(fill="both", expand=True, pady=UI_SETTINGS["PADDING"]["SMALL"])

        # Title Label (Reduced padding)
        ctk.CTkLabel(
            folder_frame,
            text="Case Label",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=(2, 2))  # Reduced spacing

        # Centered Selection Frame
        selection_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        selection_frame.pack(expand=True, anchor="center", pady=(2, 5))  # Reduced spacing

        selection_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_columnconfigure(1, weight=1)

        # Label
        ctk.CTkLabel(
            selection_frame,
            text="Enter or select folder name:",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            anchor="e"
        ).grid(row=0, column=0, padx=(0, 10), pady=2, sticky="e")

        # Entry + Dropdown Frame
        combo_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        combo_frame.grid(row=0, column=1, sticky="w")

        initial_values = self._get_existing_folders() or [""]

        self.app.folder_combobox = ctk.CTkComboBox(
            combo_frame,
            width=180,
            variable=self.app.folder_name_var,
            values=initial_values,
            fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],  # Background color of the closed ComboBox
            dropdown_fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],  # Background color when opened
            dropdown_text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"],  # Ensures text is visible
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"],
            state="normal",
            command=self._on_combobox_select
        )
        self.app.folder_combobox.pack(side="left", padx=(0, 5))

        # Info Button (Tooltip)
        info_button = self._create_info_button(
            combo_frame,
            "Specify the case label (e.g., 'OSA', 'TMD').\n"
            "For returning patients, select a condition name from the dropdown to link visits."
        )
        info_button.pack(side="left")

    def _create_navigation(self):
        """Create navigation buttons with descriptive labels, ensuring no duplicates."""
        
        # Remove any existing navigation frame in the parent before creating a new one
        for widget in self.app.main_frame.winfo_children():
            if isinstance(widget, NavigationFrame):
                widget.destroy()

        # Create new navigation
        nav_frame = NavigationFrame(
            self.app.main_frame,
            previous_label="Home",
            next_label="Information Review",
            back_command=self.app.create_tab1,
            next_command=self._validate_and_proceed
        )
        nav_frame.pack(fill="x", side="bottom", pady=10)

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
            patient_path = BASE_PATH / "CFD_GUI/User_Data" / self.app.username_var.get() / self.app.patient_name.get()
            
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
        """Handle medical image selection with native file dialog filtering"""
        # Define all file type filters that will appear in the dialog dropdown
        filetypes = [
            ("All Medical Image Formats", "*.dcm *.DCM *.nii *.nii.gz *.NII *.NII.GZ"),
            ("DICOM Files", "*.dcm *.DCM"),
            ("NIfTI Files", "*.nii *.nii.gz *.NII *.NII.GZ"),
            ("All Files", "*.*")
        ]
        
        # Open file dialog with filter options
        files = filedialog.askopenfilenames(
            title="Select Medical Image Files",
            filetypes=filetypes
        )
        
        if not files:
            return
            
        # Get the folder from the first file
        folder_path = os.path.dirname(files[0])
        self.logger.log_info(f"Patient files selected: {len(files)} files from {folder_path}")
        
        try:
            # Check what types of files were selected
            dicom_files = [f for f in files if os.path.basename(f).lower().endswith('.dcm')]
            nifti_files = [f for f in files if os.path.basename(f).lower().endswith(('.nii', '.nii.gz'))]
            
            if not dicom_files and not nifti_files:
                raise ValueError("No DICOM or NIfTI files were selected.")
            
            # Store selected files in the app
            self.app.selected_files = files
            self.app.selected_dicom_folder = folder_path
            
            # Process based on file types available
            if dicom_files and not nifti_files:
                self.app.file_format = "DICOM"
                self._extract_patient_info_from_dicom(dicom_files[0])
                file_type_str = "DICOM"
                file_count = len(dicom_files)
            elif nifti_files and not dicom_files:
                self.app.file_format = "NIfTI"
                self._clear_patient_fields()
                file_type_str = "NIfTI"
                file_count = len(nifti_files)
            else:
                # Both types selected
                self.app.file_format = "Mixed"
                if dicom_files:
                    self._extract_patient_info_from_dicom(dicom_files[0])
                else:
                    self._clear_patient_fields()
                file_type_str = "mixed format"
                file_count = len(files)
                
            self.folder_status_label.configure(
                text=f"Selected: {file_type_str} files from {Path(folder_path).name}"
            )
            
            self._update_folder_dropdown()
            messagebox.showinfo("Success", f"{file_type_str} file(s) loaded successfully.")
                
        except Exception as e:
            self.logger.log_error(f"Failed to read medical image files", e)
            messagebox.showerror("Error", f"Failed to read medical image files: {e}")
            self.folder_status_label.configure(text="No files selected")

    def _extract_patient_info_from_dicom(self, dicom_path):
        """Extract patient information from DICOM file"""
        dicom_data = pydicom.dcmread(str(dicom_path))
        
        # Name
        if hasattr(dicom_data, "PatientName"):
            self.app.patient_name.set(str(dicom_data.PatientName))
        
        # Doctor
        if hasattr(dicom_data, "ReferringPhysicianName"):
            doctor = dicom_data.ReferringPhysicianName
            self.app.patient_doctor_var.set(f"{doctor.family_name}, {doctor.given_name}")
        else:
            self.app.patient_doctor_var.set("")

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
                    var.set("")
            else:
                var.set("")
    
    def _clear_patient_fields(self):
        """Clear patient information fields when using NIfTI files"""
        self.app.patient_name.set("")
        self.app.patient_doctor_var.set("")
        self.app.dob.set("")
        self.app.scandate.set("")

    def _setup_output_folder(self):
        """Set up and create the output folder path if all required fields are filled"""
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
                "CFD_GUI/User_Data" /
                self.app.username_var.get() / 
                self.app.patient_name.get() / 
                self.app.folder_name_var.get()
            )

            self.app.full_folder_path = str(folder_path)

            # **Ensure the directory is created**
            os.makedirs(self.app.full_folder_path, exist_ok=True)

            self.logger.log_info(f"Created/Verified output folder: {self.app.full_folder_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not set up folder path: {e}")
            self.logger.log_error(f"Folder creation error: {e}")
            return False


    def _validate_and_proceed(self):
        """Validate the form and proceed to next tab"""
        if not self._setup_output_folder():
            return
            
        self.app.create_tab3()