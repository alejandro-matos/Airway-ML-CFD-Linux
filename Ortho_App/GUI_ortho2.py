import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, Canvas, ttk
from customtkinter import CTkImage
import os
import openpyxl
import subprocess
import shutil
from tkinter.ttk import Spinbox  # Import Spinbox
from PIL import ImageTk, Image
import pydicom
import numpy as np
from datetime import datetime

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 10)
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class CircularButton(Canvas):
    def __init__(self, parent, text, command=None, diameter=30, **kwargs):
        super().__init__(parent, width=diameter, height=diameter, bg="gray20", highlightthickness=0)
        
        self.diameter = diameter
        self.command = command

        # Draw the circular button
        self.circle = self.create_oval(
            2, 2, diameter - 2, diameter - 2,  # Adjust for border
            fill=kwargs.get("bg_color", "blue"),  # Button color
            outline=kwargs.get("border_color", "white"),  # Border color
            width=kwargs.get("border_width", 2)
        )
        # Add the text
        self.text = self.create_text(
            diameter // 2, diameter // 2,  # Center the text
            text=text,
            fill=kwargs.get("text_color", "white"),
            font=kwargs.get("font", ("Arial", 12, "bold"))
        )

        # Bind click events to the command
        if command:
            self.bind("<Button-1>", lambda event: self.command())

    def change_color(self, new_color):
        self.itemconfig(self.circle, fill=new_color)


class OrthoCFDApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ortho CFD v0.2")
        self.geometry("600x750")
        self.minsize(600, 750)
        self.maxsize(700, 1000)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # ==== Variable initializations ======

        # New folder where data will be saved
        self.folder_name_var = tk.StringVar()   # Folder within user
        self.full_folder_path = None            # Complete save path to new folder

        # Patient information variables
        self.patient_name = tk.StringVar()
        self.dob = tk.StringVar()
        self.scandate = tk.StringVar()
        self.username_var = tk.StringVar()
        self.patient_age_var = tk.StringVar(value="0")
        self.patient_doctor_var = tk.StringVar()
        
        # Analysis and processing variables
        self.analysis_option = tk.StringVar(value="Select Analysis Type")
        self.selected_dicom_folder = None
        
        # UI component references (initialized as None, will be set later)
        self.progress_bar = None
        self.progress_label = None
        self.process_button = None
        self.processing_details = None
        self.folder_combobox = None

        # Add a flag to track if we're going home
        self.going_home = False

        # Set the application icon
        self.setup_icon()

        self.setup_gui()

    def setup_icon(self):
        """
        Sets the application icon from the beginning.
        """
        try:
            icon_image = Image.open("CFDLab-blogo2.png")
            icon_image.save("CFDLab-blogo2.ico", format="ICO", sizes=[(64, 64)])
            self.iconbitmap("CFDLab-blogo2.ico")
        except Exception as e:
            print(f"Could not set icon: {e}")

    def setup_gui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_tab1()

    # To implement the use of the enter key one info is added and progress to next tab
    def bind_enter_key(self, method):
        """Bind the Enter key to the given method."""
        self.unbind("<Return>")  # Unbind any previous Enter key binding
        self.bind("<Return>", lambda event: method())

    def unbind_enter_key(self):
        """Unbind the Enter key."""
        self.unbind("<Return>")

    # To implement the blue circular info button
    def create_info_button(self, parent, tooltip_text, command=None, diameter=30, **kwargs):
        """
        Creates a reusable info button with tooltip.
        """
        # Create the circular button
        button = CircularButton(
            parent,
            text="i",
            diameter=diameter,
            bg_color=kwargs.get("bg_color", "blue"),  # Default blue button
            border_color=kwargs.get("border_color", "white"),
            border_width=kwargs.get("border_width", 1),
            text_color=kwargs.get("text_color", "white"),
            font=kwargs.get("font", ("Arial", 12, "bold")),
            command=command
        )
        
        # Attach the tooltip
        ToolTip(button, tooltip_text)
        return button
    
    def get_existing_folders(self, username, patient_name):
        """Get list of existing folders for this patient"""
        try:
            base_path = os.path.expanduser("~\\Desktop")
            patient_path = os.path.join(base_path, username, patient_name)
            
            if os.path.exists(patient_path):
                return sorted([folder for folder in os.listdir(patient_path) 
                            if os.path.isdir(os.path.join(patient_path, folder))])
            return []
        except Exception:
            return []
    
    def update_folder_dropdown(self, *args):
        """Update folder suggestions when username or patient name changes"""
        if hasattr(self, 'folder_combobox'):
            try:
                existing_folders = self.get_existing_folders(
                    self.username_var.get(),
                    self.patient_name.get()
                )
                self.folder_combobox.configure(values=existing_folders)
            except Exception:
                pass  # Silently handle any widget-related errors

    def create_navigation_frame(self, parent, current_tab, previous_label, next_label, back_command, next_command):
        """
        Creates a navigation frame with Back and Next buttons, including labels for the previous and next sections.
        """
        nav_frame = ctk.CTkFrame(parent, corner_radius=10)
        nav_frame.pack(fill="x", side="bottom", pady=20)

        # Back button with label below
        back_button_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        back_button_frame.pack(side="left", padx=20)

        back_button = ctk.CTkButton(
            back_button_frame,
            text="Back",
            command=back_command,
            width=100,
            font=("Times_New_Roman", 16)
        )
        back_button.pack(pady=(5, 0))

        back_label = ctk.CTkLabel(
            back_button_frame,
            text=f"{previous_label}" if previous_label else "",
            font=("Arial", 12),
            text_color="gray"
        )
        back_label.pack(pady=(0, 0))  # Add some spacing below the button

        # Next button with label below
        next_button_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        next_button_frame.pack(side="right", padx=20)

        next_button = ctk.CTkButton(
            next_button_frame,
            text="Next",
            command=next_command,
            width=100,
            font=("Times_New_Roman", 16)
        )
        next_button.pack(pady=(5, 0))

        next_label = ctk.CTkLabel(
            next_button_frame,
            text=f"{next_label}" if next_label else "",
            font=("Arial", 12),
            text_color="gray"
        )
        next_label.pack(pady=(0, 0))  # Add some spacing below the button

    def clear_all_data(self):
        """Clear all data when going home"""
        self.patient_name.set("")
        self.dob.set("")
        self.scandate.set("")
        self.username_var.set("")
        self.patient_age_var.set("0")
        self.patient_doctor_var.set("")
        self.folder_name_var.set("")
        self.full_folder_path = None
        self.selected_dicom_folder = None
        self.analysis_option.set("Select Analysis Type")
        # Reset the home flag
        self.going_home = False

    # ======================= TABS =======================================

    def create_tab1(self):
        """Modified home page creation with data clearing"""
        self.going_home = True
        self.clear_all_data()
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Add a frame for the top logo
        logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        logo_frame.pack(side="top", pady=10)

        # Load and display the logo at the top
        try:
            logo_image = Image.open("ualbertalogo.png")
            logo_ctk_image = CTkImage(logo_image, size=(150, 80))  # Resize and use CTkImage

            logo_label = ctk.CTkLabel(logo_frame, image=logo_ctk_image, text="")
            logo_label.pack()

        except FileNotFoundError:
            messagebox.showerror("Error", "Logo file not found. Please place 'ualbertalogo.png' in the same directory.")

        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Ortho CFD Application v0.2\n\nWelcome",
            font=("Times_New_Roman", 25),
            fg_color='#255233',
            text_color="white",
            justify="center",
            width=450,  # Increase the width
            height=100  # Increase the height
        )
        title_label.pack(pady=10)

        description_label = ctk.CTkLabel(
            self.main_frame,
            text=(
                "This app calculates the pressure difference in the \n"
                "nasal cavity from 3D X-RAY scans using CFD analysis.\n"
                "Input files must be in STL or OBJ format.\n\n"
                "This app uses Blender, OpenFOAM, and Paraview.\n\n"
                "For more information, contact Dr. Carlos Lange\n"
                "email: clange@ualberta.ca"
            ),
            font=("Times_New_Roman", 15),
            justify="center"
        )
        description_label.pack(pady=20)

        # Add a frame for username input
        username_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        username_frame.pack(pady=20)

        # Use grid layout within the frame for label and entry field
        username_frame.columnconfigure(0, weight=1)  # Add some spacing on the left
        username_frame.columnconfigure(1, weight=1)  # Allow space for label and field alignment
        username_frame.columnconfigure(2, weight=1)  # Add spacing on the right

        # Username label and input field in the same row
        username_label = ctk.CTkLabel(username_frame, text="Username:", font=("Arial", 15))
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.username_var = ctk.StringVar()
        username_entry = ctk.CTkEntry(username_frame, textvariable=self.username_var, width=300, fg_color="white", text_color="black")
        username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Set focus to the username entry field
        self.after(100, lambda: username_entry.focus())  # Small delay to ensure widget is fully created

        # Add the Next button
        next_button = ctk.CTkButton(
            self.main_frame,
            text="Next",
            command=self.validate_username,
            width=140,  # Increase the width
            height=40,  # Increase the height
            font=("Times_New_Roman", 20),
        )
        next_button.pack(pady=(10, 20))

        self.bind_enter_key(self.validate_username)

    def validate_username(self):
        if not self.username_var.get():
            messagebox.showerror("Error", "Please enter your username before proceeding.")
        else:
            self.create_tab2()

    
    def create_tab2(self):
        """Modified tab 2 creation with safer trace handling"""
        # Clear the main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Initialize variables if they don't exist
        if not hasattr(self, 'patient_name'):
            self.patient_name = tk.StringVar()
            self.dob = tk.StringVar()
            self.scandate = tk.StringVar()
            self.user_name_var = tk.StringVar()
            self.patient_age_var = tk.StringVar(value="0")
            self.patient_doctor_var = tk.StringVar()
            self.folder_name_var = tk.StringVar()

        # Create a top frame for the Home button and step label
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 10))

        # Configure grid layout for the top frame
        top_frame.columnconfigure(0, weight=1)  # Home button alignment
        top_frame.columnconfigure(1, weight=3)  # Step label centered
        top_frame.columnconfigure(2, weight=1)  # Placeholder for right alignment

        # Home button in the left column
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=lambda: [setattr(self, 'going_home', True), self.create_tab1()],
            width=80,
            height=40,
            font=("Times_New_Roman", 16)
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Step indicator in the center column
        step_label = ctk.CTkLabel(
            top_frame,
            text="Step 1 of 4: Upload Patient Scans & Information",
            font=("Arial", 15),
            anchor="center"
        )
        step_label.grid(row=0, column=1)

        form_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Configure layout
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=2)

        # Initialize or reuse the StringVar objects
        if not hasattr(self, 'patient_name'):
            self.patient_name = tk.StringVar()
            self.dob = tk.StringVar()
            self.scandate = tk.StringVar()
            self.user_name_var = tk.StringVar()
            self.patient_age_var = tk.StringVar(value="0")
            self.patient_doctor_var = tk.StringVar()
            self.folder_name_var = tk.StringVar()

        # Section 1: File Upload
        ctk.CTkLabel(form_frame, text="Step 1: Upload Patient Scans", font=("Arial", 15, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w")

        # Create a label to show selected folder
        self.folder_status_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=("Arial", 12)
        )
        self.folder_status_label.grid(row=1, column=0, columnspan=2, pady=(80, 0))

        def select_dicom():
            folder_path = filedialog.askdirectory(title="Select Patient Folder")
            if folder_path:
                try:
                    # Save the selected folder path
                    self.selected_dicom_folder = folder_path
                    # Update the status label
                    self.folder_status_label.configure(text=f"Selected folder: {os.path.basename(folder_path)}")

                    # Find the first valid .dcm file in the directory
                    dicom_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".dcm")]

                    if not dicom_files:
                        raise ValueError("No DICOM files found in the selected directory.")

                    # Read metadata from the first DICOM file
                    dicom_data = pydicom.dcmread(dicom_files[0])

                    # Extract patient name
                    self.patient_name.set(dicom_data.PatientName)

                    # Extracting and formatting doctor's name
                    if hasattr(dicom_data, "ReferringPhysicianName"):
                        raw_doctor_name = dicom_data.ReferringPhysicianName  # This is a PersonName object

                        # Accessing the name components directly
                        last_name = raw_doctor_name.family_name  # Extracts the last name
                        first_name = raw_doctor_name.given_name  # Extracts the first name

                        # Combine into the desired format
                        self.patient_doctor_var.set(f"{last_name}, {first_name}")
                    else:
                        self.patient_doctor_var.set("Not available")

                    # Extract and format date of birth and scan
                    raw_dob = dicom_data.PatientBirthDate  # Expected format: YYYYMMDD
                    raw_scandate = dicom_data.StudyDate
                    if len(raw_dob) == 8:  # Ensure it's a valid date
                        formatted_dob = datetime.strptime(raw_dob, "%Y%m%d").strftime("%Y-%m-%d")
                        formatted_scandate = datetime.strptime(raw_scandate, "%Y%m%d").strftime("%Y-%m-%d")
                        self.dob.set(formatted_dob)
                        self.scandate.set(formatted_scandate)
                    else:
                        self.dob.set("Invalid Date")
                        self.scandate.set("Invalid Date")

                    messagebox.showinfo("Success", "Patient details loaded successfully.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read Patient details: {e}")
                    self.folder_status_label.configure(text="")  # Clear the status label on error

        ctk.CTkButton(
            form_frame,
            text="Select Patient Folder",
            command=select_dicom,
            font=("Times_New_Roman", 14)
        ).grid(row=1, column=0, columnspan=2, pady=20)

         # If we had previously selected a DICOM folder, show it
        if hasattr(self, 'selected_dicom_folder') and self.selected_dicom_folder:
            self.folder_status_label.configure(text=f"Selected folder: {os.path.basename(self.selected_dicom_folder)}")

        # Section 2: Patient Information
        ctk.CTkLabel(form_frame, text="Step 2: Patient Information",font=("Arial", 15, "bold")).grid(row=2, column=0, columnspan=2, pady=(20, 10), sticky="w")

        # Create entry fields with current values
        entries = [
            ("Patient Name:", self.patient_name, 3),
            ("Date of Birth (YYYY-MM-DD):", self.dob, 4),
            ("Scan Date (YYYY-MM-DD):", self.scandate, 5),
            ("Referring Physician:", self.patient_doctor_var, 6)
        ]

        for label_text, variable, row in entries:
            ctk.CTkLabel(form_frame, text=label_text).grid(row=row, column=0, sticky="e", padx=10, pady=10)
            entry = ctk.CTkEntry(form_frame, textvariable=variable, fg_color="white", text_color="black")
            entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")

        # Folder name section
        ctk.CTkLabel(form_frame, text="Enter a new or existing folder name to save results:").grid(row=7, column=0, padx=10, pady=10, sticky="e")

        
        def browse_save_folder():
            # Construct the base folder path
            username = self.username_var.get()  # Assuming username is a StringVar
            patient_name = self.patient_name.get()  # Use .get() to retrieve the actual value
            new_folder = self.folder_name_var.get()  # The folder name entered by the user

            if not username or not patient_name or not new_folder:
                messagebox.showerror("Input Error", "Please provide Username, Patient Name, and Folder Name.")
                return

            # Create the full path
            base_path = os.path.expanduser("~\\Desktop")  # Start from the user's home directory
            main_folder = os.path.join(base_path, username)
            subfolder = os.path.join(main_folder, patient_name)
            full_path = os.path.join(subfolder, new_folder)

            try:
                # Create the directory if it does not exist
                os.makedirs(full_path, exist_ok=True)

                # Allow user to confirm or select the final folder
                selected_folder = filedialog.askdirectory(title="Confirm or Adjust Folder Location", initialdir=full_path)
                if selected_folder:
                    # Keep only the last folder name from the path
                    folder_name = os.path.basename(selected_folder)
                    self.folder_name_var.set(folder_name)  # Set just the folder name for ease of reference for user
                    # Store the full path separately
                    self.full_folder_path = selected_folder  # You might want to add this as a class variable
            except Exception as e:
                messagebox.showerror("Error", f"Could not create folder: {e}")

        # Create combo box frame
        combo_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        combo_frame.grid(row=7, column=1, padx=10, pady=10, sticky="w")

        # Create the combobox
        self.folder_combobox = ctk.CTkComboBox(
            combo_frame,
            width=150,
            variable=self.folder_name_var,
            values=[],  # Will be populated when username/patient name are set
            fg_color="white",
            text_color="black",
            state="normal"  # Allows both selection and free text entry
        )
        self.folder_combobox.pack(side="left", padx=(0, 5))

        # Add info button beside the combobox
        info_button = self.create_info_button(
            combo_frame,
            tooltip_text="Name folder by condition (e.g., 'OSA_1', 'TMD_followup').\nUse existing folder name if following up on same condition.",
            diameter=25
        )
        info_button.pack(side="left")

        # Add the "Browse Save Folder" button below the combobox
        browse_button = ctk.CTkButton(
            form_frame,
            text="Browse Save Folder",
            command=browse_save_folder,
            width=100,
            font=("Times_New_Roman", 14)
        )
        browse_button.grid(row=8, column=1, padx=(10, 10), pady=10, sticky="w")

        # Navigation buttons
        self.create_navigation_frame(
            parent=self.main_frame,
            current_tab="Tab 2",
            previous_label="Home Page",
            next_label="Review and Confirm",
            back_command=self.create_tab1,
            next_command=self.validate_tab2
        )

        self.bind_enter_key(self.validate_tab2)

    def validate_tab2(self):
        fields_to_validate = [
            (self.patient_name.get(), "Patient Name"),
            (self.dob.get(), "Date of Birth"),
            (self.scandate.get(), "Scan Date"),
            (self.patient_doctor_var.get(), "Referring Physican"),
            (self.folder_name_var.get(), "Patient Results Folder")
        ]

        invalid_fields = [name for field, name in fields_to_validate if not field]

        if invalid_fields:
            fields_list = ", ".join(invalid_fields)
            messagebox.showerror("Error", f"The following fields are missing or invalid: {fields_list}. Please provide the required information.")
            return

        self.create_tab3()

    def create_tab3(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create a top frame for the Home button and step label
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 10))

        # Configure grid layout for the top frame
        top_frame.columnconfigure(0, weight=1)  # Home button alignment
        top_frame.columnconfigure(1, weight=3)  # Step label centered
        top_frame.columnconfigure(2, weight=1)  # Placeholder for right alignment

        # Home button in the left column
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=lambda: [setattr(self, 'going_home', True), self.create_tab1()],
            width=80,
            height=40,
            font=("Times_New_Roman", 16)
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Step indicator in the center column
        step_label = ctk.CTkLabel(
            top_frame,
            text="Step 3 of 4: Review and Confirm",
            font=("Arial", 15),
            anchor="center"
        )
        step_label.grid(row=0, column=1)

        # Summary Section
        summary_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        summary_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Configure grid layout for the summary frame
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=2)

        # Display Patient Details
        ctk.CTkLabel(summary_frame, text="Patient Details", font=("Arial", 15, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 5), sticky="w"
        )
        ctk.CTkLabel(summary_frame, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(summary_frame, textvariable=self.patient_name).grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(summary_frame, text="Date of Birth:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(summary_frame, textvariable=self.dob).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(summary_frame, text="Physician:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(summary_frame, textvariable=self.patient_doctor_var).grid(row=3, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(summary_frame, text="Folder Name:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(summary_frame, textvariable=self.folder_name_var).grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Scan Previews Section
        ctk.CTkLabel(summary_frame, text="Scan Previews", font=("Arial", 15, "bold")).grid(row=5, column=0, columnspan=2, pady=(20, 5), sticky="w")

        # Generate and display the three slices
        try:
            slices = self.generate_slices()

            # Create a frame to hold the preview images
            slice_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
            slice_frame.grid(row=6, column=0, columnspan=2, pady=(10, 5))

            # Add labels for each slice
            for i, (view_name, image) in enumerate(slices.items()):
                view_label = ctk.CTkLabel(slice_frame, text=view_name.capitalize(), font=("Arial", 12))
                view_label.grid(row=0, column=i, padx=10, pady=(0, 5))
                
                # Convert the PIL image to CTkImage
                ctk_image = CTkImage(image, size=(150, 150))
                
                # Display the image using CTkLabel
                image_label = ctk.CTkLabel(slice_frame, image=ctk_image, text="")
                image_label.grid(row=1, column=i, padx=10)

        except Exception as e:
            error_label = ctk.CTkLabel(summary_frame, text=f"Error loading slices: {e}", fg_color="red")
            error_label.grid(row=6, column=0, columnspan=2, pady=(10, 5), sticky="w")

        # Navigation buttons
        self.create_navigation_frame(
            parent=self.main_frame,
            current_tab="Tab 3",
            previous_label="Upload Patient Scan",
            next_label="Analysis Selection",
            back_command=self.create_tab2,
            next_command=self.validate_tab3
        )

        self.bind_enter_key(self.validate_tab3)


    def generate_slices(self):
        """
        Generate the middle slice images optimized for dental CBCT (seated position).
        """
        if not hasattr(self, "selected_dicom_folder") or not self.selected_dicom_folder:
            raise ValueError("No DICOM folder selected.")

        dicom_files = [
            os.path.join(self.selected_dicom_folder, f)
            for f in os.listdir(self.selected_dicom_folder)
            if f.endswith(".dcm")
        ]
        if not dicom_files:
            raise ValueError("No DICOM files found in the folder.")

        # Load and sort slices
        slices = [pydicom.dcmread(f) for f in dicom_files]
        slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))

        # Create 3D volume array
        volume = np.stack([s.pixel_array for s in slices], axis=0)

        # Enhance contrast using histogram equalization approach
        def enhance_contrast(image):
            # Calculate histogram
            p2 = np.percentile(image, 2)
            p98 = np.percentile(image, 98)
            
            # Clip and stretch the image
            image_clipped = np.clip(image, p2, p98)
            image_normalized = ((image_clipped - p2) / (p98 - p2) * 255).astype(np.uint8)
            return image_normalized

        # Apply enhancement to whole volume
        volume = enhance_contrast(volume)

        # Get middle slices
        axial = volume[len(volume) // 2, :, :]
        coronal = volume[:, volume.shape[1] // 2, :]
        sagittal = volume[:, :, volume.shape[2] // 2]

        # Apply correct orientations for seated position CBCT
        # For axial: patient is facing up (anterior is up)
        axial = np.flipud(axial)  # Flip vertically to get anterior up
        
        # For coronal: patient is facing forward (anterior is right)
        coronal = np.flipud(coronal)  # Flip vertically to match seated position
        
        # For sagittal: patient is facing left (anterior is right)
        sagittal = np.flipud(sagittal)  # Flip vertically for seated position
        sagittal = np.fliplr(sagittal)  # Flip horizontally to get anterior to right

        def slice_to_image(slice_data, spacing):
            target_width = 150
            aspect_ratio = spacing[0] / spacing[1]
            target_height = int(target_width * aspect_ratio)
            
            pil_image = Image.fromarray(slice_data)
            return pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Get pixel spacing
        pixel_spacing = slices[0].PixelSpacing

        return {
            "axial": slice_to_image(axial, pixel_spacing),
            "coronal": slice_to_image(coronal, pixel_spacing),
            "sagittal": slice_to_image(sagittal, pixel_spacing)
        }


    def validate_tab3(self):
        messagebox.showinfo("Success", "Details confirmed. \n Proceeding to the prediction/simulation step.")
        self.create_tab4()

    def create_tab4(self):
        """
        Tab 4: Prediction and Simulation with centered and consistent UI elements
        """
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create a top frame for the Home button and context header
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 10))

        # Configure grid layout for the top frame
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=3)
        top_frame.columnconfigure(2, weight=1)

        # Home button in the left column
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=lambda: [setattr(self, 'going_home', True), self.create_tab1()],
            width=80,
            height=40,
            font=("Times_New_Roman", 16)
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Context header
        context_label = ctk.CTkLabel(
            top_frame,
            text=f"Patient: {self.patient_name.get()} | DOB: {self.dob.get()} | Physician: {self.patient_doctor_var.get()}",
            font=("Arial", 13),
            anchor="center"
        )
        context_label.grid(row=0, column=1, padx=10, pady=5)

        # Main content frame
        content_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Center everything in the content frame
        content_frame.grid_columnconfigure(0, weight=1)

        # Analysis Options Section
        analysis_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        analysis_frame.grid(row=0, column=0, pady=(20, 10), sticky="nsew")
        analysis_frame.grid_columnconfigure(0, weight=1)  # Center the contents

        # Title
        title_label = ctk.CTkLabel(
            analysis_frame, 
            text="Select Analysis Option", 
            font=("Arial", 15, "bold")
        )
        title_label.pack(pady=(10, 15))

        # Dropdown with consistent styling
        self.analysis_option = tk.StringVar(value="Select Analysis Type")
        analysis_dropdown = ctk.CTkOptionMenu(
            analysis_frame,
            variable=self.analysis_option,
            values=["Upper Airway Segmentation", "Airflow Simulation (includes segmentation)"],
            command=self.update_processing_details,
            width=300,  # Match button width
            height=40,  # Match button height
            font=("Arial", 14)
        )
        analysis_dropdown.pack(pady=(0, 15))

        # Processing details label
        self.processing_details = ctk.CTkLabel(
            analysis_frame,
            text="",
            font=("Arial", 12),
            wraplength=300,
            justify="center"  # Center the text
        )
        self.processing_details.pack(pady=(0, 20))

        # Processing Section
        processing_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        processing_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        processing_frame.grid_columnconfigure(0, weight=1)  # Center the contents

        # Start Processing button with consistent styling
        self.process_button = ctk.CTkButton(
            processing_frame,
            text="Start Processing",
            command=self.validate_processing,
            width=300,  # Match dropdown width
            height=40,  # Match dropdown height
            font=("Arial", 14)
        )
        self.process_button.pack(pady=10)

        # Progress bar and label
        self.progress_bar = ttk.Progressbar(processing_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=50, pady=(10, 5))  # Add padding to center it

        self.progress_label = ctk.CTkLabel(processing_frame, text="")
        self.progress_label.pack(pady=5)

        # Results frame
        results_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        results_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)

        # Navigation buttons at the bottom
        button_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        button_frame.pack(fill="x", side="bottom", pady=20)

        ctk.CTkButton(
            button_frame,
            text="Back",
            command=self.create_tab3,
            width=100,
            font=("Times_New_Roman", 16)
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            button_frame,
            text="Next",
            command=lambda: messagebox.showinfo("Info", "Further tabs not yet implemented."),
            width=100,
            font=("Times_New_Roman", 16)
        ).pack(side="right", padx=20)
    
    def update_processing_details(self, choice):
        """
        Update the processing details label based on the selected option
        """
        if choice == "Upper Airway Segmentation":
            details = "This will perform automatic segmentation of the upper airway from the DICOM images."
        elif choice == "Airflow Simulation (includes segmentation)":
            details = "This will first perform airway segmentation, followed by CFD analysis to simulate airflow patterns and pressure changes."
        else:
            details = "Please select an analysis type to proceed."
        
        self.processing_details.configure(text=details)

    def validate_processing(self):
        """
        Validate the selected option before processing
        """
        if self.analysis_option.get() == "Select Analysis Type":
            messagebox.showerror("Error", "Please select an analysis type before proceeding.")
            return

        # Show a confirmation dialog with selected options
        option = self.analysis_option.get()
        msg = f"Selected analysis: {option}\n\nDo you want to proceed?"
        
        response = messagebox.askquestion("Confirm Analysis", msg, icon="warning")
        
        if response == "yes":
            self.start_processing()

    def start_processing(self):
        """
        Start the processing based on selected option
        """
        option = self.analysis_option.get()
        
        # Disable the button and update progress label
        self.process_button.configure(state="disabled")
        self.progress_label.configure(text=f"Processing: {option}")
        self.progress_bar.start()

        # Simulate processing steps
        if option == "Airflow Simulation (includes segmentation)":
            self.process_with_steps([
                ("Segmenting airway...", 2000),
                ("Generating mesh...", 2000),
                ("Running CFD simulation...", 3000),
                ("Analyzing results...", 1000)
            ])
        else:
            self.process_with_steps([
                ("Segmenting airway...", 2000),
                ("Finalizing results...", 1000)
            ])

    def process_with_steps(self, steps):
        """
        Process multiple steps with different timing
        """
        def run_step(step_index):
            if step_index < len(steps):
                message, duration = steps[step_index]
                self.progress_label.configure(text=message)
                self.after(duration, lambda: run_step(step_index + 1))
            else:
                self.complete_processing()
        
        run_step(0)

    def complete_processing(self):
        """
        Handle the completion of the processing task
        """
        # Stop the progress bar
        self.progress_bar.stop()
        
        # Update labels and button state
        self.progress_label.configure(text="Processing Complete!")
        self.process_button.configure(state="normal")

        # Get the selected analysis option
        option = self.analysis_option.get()

        # Create success message based on the selected option
        if option == "Upper Airway Segmentation":
            success_msg = "Airway segmentation completed successfully!"
        else:  # Airflow Simulation
            success_msg = "Airway segmentation and CFD simulation completed successfully!"

        # Show completion message
        messagebox.showinfo("Success", success_msg)

        # Enable results section
        try:
            # Find the results frame in the content frame
            results_frame = [child for child in self.main_frame.winfo_children() 
                            if isinstance(child, ctk.CTkFrame)][-1]
            
            # Clear existing widgets in results frame
            for widget in results_frame.winfo_children():
                widget.destroy()

            # Add results header
            ctk.CTkLabel(results_frame, 
                        text="Results Available:", 
                        font=("Arial", 15, "bold")).pack(pady=(10, 5))

            # Add results buttons
            def save_results():
                messagebox.showinfo("Save Results", "Results saved successfully!")

            def export_reports():
                messagebox.showinfo("Export Reports", "Reports exported successfully!")

            def visualize_data():
                messagebox.showinfo("Visualize Data", "Opening visualization tool...")

            # Create button frame for better organization
            button_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
            button_frame.pack(pady=10)

            # Add results buttons with consistent styling
            ctk.CTkButton(button_frame, 
                        text="Save Results", 
                        command=save_results,
                        width=120,
                        height=32).pack(side="left", padx=5)
            
            ctk.CTkButton(button_frame, 
                        text="Export Reports", 
                        command=export_reports,
                        width=120,
                        height=32).pack(side="left", padx=5)
            
            ctk.CTkButton(button_frame, 
                        text="Visualize Data", 
                        command=visualize_data,
                        width=120,
                        height=32).pack(side="left", padx=5)

            # Make the results frame visible
            results_frame.pack(fill="x", pady=10)
            
        except Exception as e:
            print(f"Error displaying results section: {e}")

if __name__ == "__main__":
    app = OrthoCFDApp()
    app.mainloop()
