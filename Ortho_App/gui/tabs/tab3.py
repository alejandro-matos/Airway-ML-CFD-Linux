# gui/tabs/tab3.py

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
from ..components.navigation import NavigationFrame
from ..components.info_display import InfoDisplay
from ..utils.image_processing import generate_slices
from config.settings import UI_SETTINGS

class Tab3Manager:
    def __init__(self, app):
        """Initialize Tab3Manager with a reference to the main app"""
        self.app = app

    def create_tab(self):
        """Create and set up the review and confirm page"""
        self._create_header()
        self._create_main_content()
        self._create_navigation()

    def _create_header(self):
        """Create the header with home button and step indicator"""
        top_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 10))
        
        # Configure grid layout
        top_frame.columnconfigure(0, weight=1)  # Home button
        top_frame.columnconfigure(1, weight=3)  # Step label
        top_frame.columnconfigure(2, weight=1)  # Right padding

        # Home button
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=self.app.go_home,
            width=80,
            height=40,
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text="Step 2 of 3: Review and Confirm",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            anchor="center"
        ).grid(row=0, column=1)

    def _create_main_content(self):
        """Create the main content area with patient details and scan previews"""
        # Create main content frame
        content_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Add patient details section
        self._create_patient_details(content_frame)
        
        # Add scan previews section
        self._create_scan_previews(content_frame)

    def _create_patient_details(self, parent):
        """Create the patient details summary section"""
        # Create info display with patient details
        patient_info = {
            "Name": self.app.patient_name.get(),
            "Date of Birth": self.app.dob.get(),
            "Scan Date": self.app.scandate.get(),
            "Referring Physician": self.app.patient_doctor_var.get(),
            "Save Location": self.app.folder_name_var.get()
        }
        
        info_display = InfoDisplay(
            parent,
            "Patient Details",
            patient_info,
        )
        info_display.pack(fill="x", padx=10, pady=10)

    def _create_scan_previews(self, parent):
        """Create the scan previews section"""
        preview_frame = ctk.CTkFrame(parent, corner_radius=10)
        preview_frame.pack(fill="x", padx=10, pady=10)

        # Title
        ctk.CTkLabel(
            preview_frame,
            text="Scan Previews",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=(10, 0))

        try:
            # Generate slices
            slices = self._generate_preview_slices()
            
            # Create frame for slice previews
            slice_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
            slice_frame.pack(pady=10)

            # Display each slice
            for i, (view_name, image) in enumerate(slices.items()):
                # Create frame for each view
                view_frame = ctk.CTkFrame(slice_frame, fg_color="transparent")
                view_frame.pack(side="left", padx=10)

                # Add view label
                ctk.CTkLabel(
                    view_frame,
                    text=view_name.capitalize(),
                    font=UI_SETTINGS["FONTS"]["NORMAL"],
                    text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
                ).pack(pady=(0, 5))

                # Convert and display image
                ctk_image = CTkImage(image, size=(200, 200))
                ctk.CTkLabel(
                    view_frame,
                    image=ctk_image,
                    text=""
                ).pack()

        except Exception as e:
            # Display error message if slice generation fails
            error_label = ctk.CTkLabel(
                preview_frame,
                text=f"Error loading scan previews: {str(e)}",
                text_color="red",
                font=UI_SETTINGS["FONTS"]["NORMAL"]
            )
            error_label.pack(pady=10)

    def _generate_preview_slices(self):
        """Generate preview slices from DICOM data"""
        if not self.app.selected_dicom_folder:
            raise ValueError("No DICOM folder selected")

        return generate_slices(self.app.selected_dicom_folder)

    def _create_navigation(self):
        """Create navigation buttons with descriptive labels, ensuring no duplicates."""
        
        # Remove any existing navigation frame in the parent before creating a new one
        for widget in self.app.main_frame.winfo_children():
            if isinstance(widget, NavigationFrame):
                widget.destroy()

        # Create new navigation
        nav_frame = NavigationFrame(
            self.app.main_frame,
            previous_label="Patient File Upload",
            next_label="Analysis Selection",
            back_command=self.app.create_tab2,
            next_command=self._validate_and_proceed
        )
        nav_frame.pack(fill="x", side="bottom", pady=10)

    def _validate_and_proceed(self):
        """Validate the review and proceed to next tab"""
        # Here we could add any final validation if needed
        
        # For now, just show a confirmation message and proceed
        self.app.create_tab4()