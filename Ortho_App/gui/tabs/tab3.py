# gui/tabs/tab3.py

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
from ..components.navigation import NavigationFrame
from ..components.info_display import InfoDisplay
from ..utils.image_processing import generate_slices

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
            font=("Times_New_Roman", 16)
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text="Step 3 of 4: Review and Confirm",
            font=("Arial", 15),
            anchor="center"
        ).grid(row=0, column=1)

    def _create_main_content(self):
        """Create the main content area with patient details and scan previews"""
        # Create main content frame
        content_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

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
            patient_info
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
            font=("Arial", 15, "bold")
        ).pack(pady=(10, 5))

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
                    font=("Arial", 12)
                ).pack(pady=(0, 5))

                # Convert and display image
                ctk_image = CTkImage(image, size=(150, 150))
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
                text_color="red"
            )
            error_label.pack(pady=10)

    def _generate_preview_slices(self):
        """Generate preview slices from DICOM data"""
        if not self.app.selected_dicom_folder:
            raise ValueError("No DICOM folder selected")

        return generate_slices(self.app.selected_dicom_folder)

    def _create_navigation(self):
        """Create the navigation buttons"""
        NavigationFrame(
            self.app.main_frame,
            previous_label="Patient Information",
            next_label="Analysis Selection",
            back_command=self.app.create_tab2,
            next_command=self._validate_and_proceed
        ).pack(fill="x", side="bottom", pady=20)

    def _validate_and_proceed(self):
        """Validate the review and proceed to next tab"""
        # Here we could add any final validation if needed
        
        # For now, just show a confirmation message and proceed
        self.app.create_tab4()

# gui/utils/image_processing.py
import os
import numpy as np
import pydicom
from PIL import Image

def generate_slices(dicom_folder):
    """Generate the middle slice images for axial, sagittal, and coronal views"""
    # Get DICOM files
    dicom_files = [
        os.path.join(dicom_folder, f)
        for f in os.listdir(dicom_folder)
        if f.endswith('.dcm')
    ]
    
    if not dicom_files:
        raise ValueError("No DICOM files found")

    # Load and sort slices
    slices = [pydicom.dcmread(f) for f in dicom_files]
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))

    # Create 3D volume
    volume = np.stack([s.pixel_array for s in slices], axis=0)

    # Get middle slices
    axial = volume[len(volume) // 2, :, :]
    sagittal = volume[:, :, volume.shape[2] // 2]
    coronal = volume[:, volume.shape[1] // 2, :]

    # Process images for display
    def process_slice(slice_data):
        # Normalize to 0-255 range
        normalized = ((slice_data - slice_data.min()) * 
                     (255.0 / (slice_data.max() - slice_data.min())))
        return Image.fromarray(normalized.astype('uint8'))

    return {
        'axial': process_slice(axial),
        'sagittal': process_slice(sagittal),
        'coronal': process_slice(coronal)
    }