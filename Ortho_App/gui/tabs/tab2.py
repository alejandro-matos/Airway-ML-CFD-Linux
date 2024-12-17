# gui/tabs/tab2.py

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import pydicom

from ..components.buttons import CircularButton
from ..components.forms import FormSection, LabeledEntry
from ..components.navigation import NavigationFrame
from ..utils.tooltips import ToolTip

class Tab2Manager:
    def __init__(self, app):
        """Initialize Tab2Manager with a reference to the main app"""
        self.app = app
        
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
        top_frame.pack(fill="x", pady=(5, 5))  # Reduced top padding

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
        main_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))  # Reduced padding
        return main_frame

    def _create_upload_section(self):
        """Create the file upload section"""
        upload_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")  # Changed to transparent
        upload_frame.pack(fill="x", pady=(5, 10))

        # Section Title
        ctk.CTkLabel(
            upload_frame,
            text="Step 1: Upload Patient Scans",
            font=("Arial", 15, "bold")
        ).pack(pady=(5, 0))

        # Status Label
        self.folder_status_label = ctk.CTkLabel(
            upload_frame,
            text="",
            font=("Arial", 12)
        )
        self.folder_status_label.pack(pady=(5, 0))

        # Upload Button
        ctk.CTkButton(
            upload_frame,
            text="Select Patient Folder",
            command=self._handle_folder_selection,
            font=("Times_New_Roman", 14)
        ).pack(pady=(5, 10))


    def _create_patient_info_section(self):
        """Create the patient information form section"""
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")  # Changed to transparent
        info_frame.pack(fill="x", pady=(5, 10))

        # Section Title
        ctk.CTkLabel(
            info_frame,
            text="Step 2: Patient Information",
            font=("Arial", 15, "bold")
        ).pack(pady=(5, 10))

        # Create grid for form fields
        form_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Configure grid columns
        form_frame.grid_columnconfigure(1, weight=1)

        # Form fields with consistent spacing
        fields = [
            ("Patient Name:", self.app.patient_name),
            ("Date of Birth (YYYY-MM-DD):", self.app.dob),
            ("Scan Date (YYYY-MM-DD):", self.app.scandate),
            ("Referring Physician:", self.app.patient_doctor_var)
        ]

        for i, (label_text, variable) in enumerate(fields):
            # Label
            ctk.CTkLabel(
                form_frame,
                text=label_text,
                anchor="e"
            ).grid(row=i, column=0, padx=(0, 10), pady=5, sticky="e")

            # Entry
            ctk.CTkEntry(
                form_frame,
                textvariable=variable,
                width=300,
                fg_color="white",
                text_color="black"
            ).grid(row=i, column=1, pady=5, sticky="w")
    
    # Add this method to your Tab2Manager class
    def _create_info_button(self, parent, tooltip_text):
        """Create a circular info button with tooltip"""
        info_button = CircularButton(
            parent,
            text="?",
            diameter=20,
            bg_color="#007bff",  # Blue color
            text_color="white",
            border_color="white",
            border_width=1,
            font=("Arial", 10, "bold")
        )
        
        # Create tooltip with the text parameter
        tooltip = ToolTip(info_button, text=tooltip_text)
        
        def show_tooltip(event):
            tooltip.show_tooltip()  # Changed from showtip to show_tip
        
        def hide_tooltip(event):
            tooltip.hide_tooltip()  # Changed from hidetip to hide_tip
        
        info_button.bind('<Enter>', show_tooltip)
        info_button.bind('<Leave>', hide_tooltip)
        
        return info_button


    def _create_folder_section(self):
        """Create the folder selection section"""
        folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(5, 10))

        # Section Title
        ctk.CTkLabel(
            folder_frame,
            text="Save Location",
            font=("Arial", 15, "bold")
        ).pack(pady=(5, 10))

        # Folder selection frame
        selection_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        selection_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Configure grid
        selection_frame.grid_columnconfigure(1, weight=1)

        # Label
        ctk.CTkLabel(
            selection_frame,
            text="Enter or select folder name:",
            anchor="e"
        ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")

        # Combobox and info button frame
        combo_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        combo_frame.grid(row=0, column=1, sticky="w")

        # Initialize the folder name variable if it doesn't exist
        if not hasattr(self.app, 'folder_name_var'):
            self.app.folder_name_var = tk.StringVar()

        # Get initial values 
        initial_values = self._get_existing_folders()
        if not initial_values:  # If no folders exist
            initial_values = [""]  # Add empty string as fallback

        # Combobox with event binding
        self.app.folder_combobox = ctk.CTkComboBox(
            combo_frame,
            width=150,
            variable=self.app.folder_name_var,
            values=initial_values,
            fg_color="white",
            text_color="black",
            state="normal",  # Ensure it's enabled
            command=self._on_combobox_select  # Add callback for selection
        )
        self.app.folder_combobox.pack(side="left", padx=(0, 5))

        # Force an initial update of the dropdown values
        self._update_folder_dropdown()

        # Info button - using the app's create_info_button method
        info_button = self._create_info_button(
            combo_frame,
            "Name folder by condition (e.g., 'OSA', 'TMD').\n"
            "Use existing folder name if following up on same condition."
        )
        info_button.pack(side="left")

        # Browse button
        ctk.CTkButton(
            selection_frame,
            text="Browse Save Location",
            command=self._handle_save_location,
            font=("Times_New_Roman", 14)
        ).grid(row=1, column=1, pady=(5, 0), sticky="w")
    
    def _on_combobox_select(self, choice):
        """Handle ComboBox selection"""
        if choice:
            self.app.folder_name_var.set(choice)

    def _update_folder_dropdown(self, *args):
        """Update folder dropdown values only when necessary."""
        if hasattr(self.app, 'folder_combobox'):
            current_folders = self._get_existing_folders()
            if not current_folders:
                current_folders = [""]  # Fallback
            
            # Temporarily allow text editing (state="normal") during updates
            self.app.folder_combobox.configure(state="normal")

            # Check if values have changed before updating
            if set(self.app.folder_combobox.cget("values")) != set(current_folders):
                self.app.folder_combobox.configure(values=current_folders)

            # Explicitly clear the current value in the entry field
            self.app.folder_combobox.set("")
            
            # # Preserve the current value
            # current_value = self.app.folder_name_var.get()
            # if current_value in current_folders:
            #     self.app.folder_combobox.set(current_value)
            # elif current_folders:
            #     self.app.folder_combobox.set(current_folders[0])
            
            # Restore to "normal" or "readonly" based on desired behavior
            self.app.folder_combobox.configure(state="normal")  # Change to "readonly" if you don't want typing

    def _get_existing_folders(self):
        """Get list of existing folders for the current patient"""
        username = self.app.username_var.get()
        patient_name = self.app.patient_name.get()
        
        if not all([username, patient_name]):
            return []

        try:
            base_path = os.path.expanduser("~\\Desktop")
            patient_path = os.path.join(base_path, username, patient_name)
            
            if os.path.exists(patient_path):
                folders = [
                    folder for folder in os.listdir(patient_path)
                    if os.path.isdir(os.path.join(patient_path, folder))
                ]
                return sorted(folders) if folders else []
            return []
        except Exception as e:
            print(f"Error getting folders: {e}")  # Add error logging
            return []

    def _create_navigation(self):
        """Create the navigation buttons"""
        nav_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        nav_frame.pack(fill="x", side="bottom", pady=10)

        # Back button
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

        # Next button
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

    def _handle_folder_selection(self):
        """Handle the selection of DICOM folder"""
        folder_path = filedialog.askdirectory(title="Select Patient Folder")
        if not folder_path:
            return

        try:
            # Find DICOM files
            dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dcm')]
            if not dicom_files:
                raise ValueError("No DICOM files found in the selected directory.")

            # Save folder path
            self.app.selected_dicom_folder = folder_path
            self.folder_status_label.configure(
                text=f"Selected folder: {os.path.basename(folder_path)}"
            )

            # Extract patient information
            dicom_data = pydicom.dcmread(os.path.join(folder_path, dicom_files[0]))
            self._extract_patient_info(dicom_data)

            # Update the dropdown list of folders
            self._update_folder_dropdown()

            messagebox.showinfo("Success", "Patient details loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read patient details: {e}")
            self.folder_status_label.configure(text="")

    def _extract_patient_info(self, dicom_data):
        """Extract patient information from DICOM data"""
        # Extract name
        self.app.patient_name.set(str(dicom_data.PatientName))

        # Extract doctor's name
        if hasattr(dicom_data, "ReferringPhysicianName"):
            doctor = dicom_data.ReferringPhysicianName
            self.app.patient_doctor_var.set(
                f"{doctor.family_name}, {doctor.given_name}"
            )
        else:
            self.app.patient_doctor_var.set("Not available")

        # Extract dates
        for date_attr, var in [
            ("PatientBirthDate", self.app.dob),
            ("StudyDate", self.app.scandate)
        ]:
            if hasattr(dicom_data, date_attr):
                date_str = getattr(dicom_data, date_attr)
                if len(date_str) == 8:  # YYYYMMDD format
                    formatted_date = datetime.strptime(
                        date_str, "%Y%m%d"
                    ).strftime("%Y-%m-%d")
                    var.set(formatted_date)
                else:
                    var.set("Invalid Date")

    def _handle_save_location(self):
        """Handle the selection of save location"""
        username = self.app.username_var.get()
        patient_name = self.app.patient_name.get()
        new_folder = self.app.folder_name_var.get()

        if not all([username, patient_name, new_folder]):
            messagebox.showerror(
                "Input Error",
                "Please provide Username, Patient Name, and Folder Name."
            )
            return

        try:
            # Create path
            base_path = os.path.expanduser("~\\Desktop")
            full_path = os.path.join(base_path, username, patient_name, new_folder)
            
            # Let user confirm location
            selected_folder = filedialog.askdirectory(
                title="Confirm or Adjust Folder Location",
                initialdir=full_path
            )

            if selected_folder:
                # Update both the folder name and the full path
                self.app.folder_name_var.set(os.path.basename(selected_folder))
                self.app.full_folder_path = selected_folder
                
                # Show confirmation message with the selected path
                messagebox.showinfo(
                    "Success",
                    f"Selected output folder:\n{selected_folder}"
                )
            else:
                # If user cancels, set the original path
                self.app.full_folder_path = full_path

            # Update the dropdown list of folders
            self._update_folder_dropdown()

        except Exception as e:
            messagebox.showerror("Error", f"Could not set folder path: {e}")

    def _validate_and_proceed(self):
        """Validate the form and proceed to next tab"""
        fields_to_validate = [
            (self.app.patient_name.get(), "Patient Name"),
            (self.app.dob.get(), "Date of Birth"),
            (self.app.scandate.get(), "Scan Date"),
            (self.app.patient_doctor_var.get(), "Referring Physician"),
            (self.app.folder_name_var.get(), "Patient Results Folder")
        ]

        invalid_fields = [name for field, name in fields_to_validate if not field]

        if invalid_fields:
            fields_list = ", ".join(invalid_fields)
            messagebox.showerror(
                "Error",
                f"The following fields are missing or invalid: {fields_list}"
            )
            return

        # Automatically set up the folder path
        if not self._setup_folder_path():
            return

        self.app.create_tab3()

    def _setup_folder_path(self):
        """Automatically set up the folder path based on entered information"""
        try:
            username = self.app.username_var.get()
            patient_name = self.app.patient_name.get()
            folder_name = self.app.folder_name_var.get()

            if not all([username, patient_name, folder_name]):
                messagebox.showerror(
                    "Error",
                    "Please ensure Username, Patient Name, and Folder Name are all provided."
                )
                return False

            # Create the full path
            base_path = os.path.expanduser("~\\Desktop")
            full_path = os.path.join(base_path, username, patient_name, folder_name)
            
            # Store the full path
            self.app.full_folder_path = full_path
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Could not set up folder path: {e}")
            return False