# Ortho CFD App entry point script
# Computational Fluid Dynamics Lab
# Author = Alejandro Matos Camarillo
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2025-04-30

# gui/app.py
# Serves as main application controller:
# Handles window configuration
# Initializes all variables
# Sets up the main GUI framework
# Manages tab creation and navigation

# Key Components:

# initialize_variables(): Sets up all application state variables
# init_tab_managers(): Creates instances of tab managers
# setup_gui(): Sets up the main GUI framework
# Tab creation methods (create_tab1(), etc.)
# Validation methods for each step
# Utility methods for common operations

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import os

from .tabs.tab1 import Tab1Manager
from .tabs.tab2 import Tab2Manager
from .tabs.tab3 import Tab3Manager
from .tabs.tab4 import Tab4Manager
from .components.navigation import NavigationFrame
from .utils.image_processing import generate_slices
from .config.settings import APP_SETTINGS, PATH_SETTINGS, UI_SETTINGS

BASE_DIR = PATH_SETTINGS["BASE_DIR"]

class OrthoCFDApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize the window
        self.setup_window()
        
        # Initialize all variables
        self.initialize_variables()
        
        # Initialize tab managers
        self.init_tab_managers()
        
        # Setup the main GUI
        self.setup_gui()

    def setup_window(self):
        """Configure the main window settings"""
        self.title(APP_SETTINGS["TITLE"])

        # Fullscreen with window decorations
        if APP_SETTINGS["FULLSCREEN"]:
            self.attributes("-fullscreen", True)
        else:
            self.geometry(f"{w}x{h}")

        # self.resizable(True, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(APP_SETTINGS["THEME"])
        self.setup_icon()

    
    def setup_icon(self):
        """Set up the application icon"""
        try:
            # Build the path from the module-level BASE_DIR
            icon_path = os.path.join(PATH_SETTINGS["ICONS_DIR"],PATH_SETTINGS["CFD_ICON"])

            # 1) Open with PIL
            pil_img = Image.open(icon_path)

            # 2) Convert to a Tk PhotoImage
            photo = ImageTk.PhotoImage(pil_img)

            # 3) Keep a reference and set as window icon
            self._icon_image = photo
            self.wm_iconphoto(False, photo)

        except Exception as e:
            print(f"Could not set icon: {e}")

    def initialize_variables(self):
        """Initialize all application variables"""
        # Folder variables
        self.folder_name_var = tk.StringVar()
        self.full_folder_path = None
        self.selected_dicom_folder = None
        
        # Patient information variables
        self.patient_name = tk.StringVar()
        self.dob = tk.StringVar()
        self.scandate = tk.StringVar()
        self.username_var = tk.StringVar()
        self.patient_age_var = tk.StringVar(value="0")
        self.patient_doctor_var = tk.StringVar()
        # self.folder_name_var = None
        
        # Analysis variables
        self.analysis_option = tk.StringVar(value="Select Analysis Type")
        
        # UI References
        self.progress_bar = None
        self.progress_label = None
        self.process_button = None
        self.processing_details = None
        self.folder_combobox = None
        
        # State flags
        self.going_home = False

    def init_tab_managers(self):
        """Initialize tab manager instances"""
        self.tab1_manager = Tab1Manager(self)
        self.tab2_manager = Tab2Manager(self)
        self.tab3_manager = Tab3Manager(self)
        self.tab4_manager = Tab4Manager(self)

    def setup_gui(self):
        """Set up the main GUI framework with a main frame."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=UI_SETTINGS["WINDOW"]["CORNER_RADIUS"])
        self.main_frame.pack(fill="both", expand=True,
                            padx=UI_SETTINGS["WINDOW"]["PAD_X"],
                            pady=UI_SETTINGS["WINDOW"]["PAD_Y"])

        # Start with Tab 1
        self.create_tab1()

    def clear_main_frame(self):
        """Clear all widgets from the main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def clear_all_data(self):
        """Reset all application data and reinitialize StringVars"""
        self.patient_name = tk.StringVar()
        self.dob = tk.StringVar()
        self.scandate = tk.StringVar()
        self.username_var = tk.StringVar()  # Recreate username_var
        self.patient_age_var = tk.StringVar(value="0")
        self.patient_doctor_var = tk.StringVar()
        self.folder_name_var = tk.StringVar()
        self.full_folder_path = None
        self.selected_dicom_folder = None
        self.analysis_option = tk.StringVar(value=UI_SETTINGS["PLACEHOLDERS"]["ANALYSIS_MENU"])
        self.going_home = False


    # Tab Creation Methods
    def create_tab1(self):
        """Create Tab 1 (Home Page)"""
        self.clear_main_frame()  # Clear the previous frame
        self.tab1_manager.create_tab()  # Recreate Tab 1 widgets


    def create_tab2(self):
        """Create Tab 2 (Patient Information)"""
        self.clear_main_frame()
        self.tab2_manager.create_tab()

    def create_tab3(self):
        """Create Tab 3 (Review and Confirm)"""
        self.clear_main_frame()
        self.tab3_manager.create_tab()

    def create_tab4(self):
        """Create Tab 4 (Analysis)"""
        self.clear_main_frame()
        self.tab4_manager.create_tab()

    # =========== Navigation Methods ==========
    def go_home(self):
        """Return to home page and reset application state"""
        self.going_home = True
        self.clear_all_data()  # Reset all application data, including username_var
        self.clear_main_frame()  # Clear the GUI frame
        self.create_tab1()  # Recreate Tab 1

    # Event Binding Methods
    def bind_enter_key(self, method):
        """Bind the Enter key to a method"""
        self.unbind("<Return>")
        self.bind("<Return>", lambda event: method())

    def unbind_enter_key(self):
        """Unbind the Enter key"""
        self.unbind("<Return>")

    # Validation Methods
    def validate_tab2(self):
        """Validate Tab 2 input before proceeding"""
        fields_to_validate = [
            (self.patient_name.get(), "Patient Name"),
            (self.dob.get(), "Date of Birth"),
            (self.scandate.get(), "Scan Date"),
            (self.patient_doctor_var.get(), "Referring Physician"),
            (self.folder_name_var.get(), "Patient Results Folder")
        ]
        
        invalid_fields = [name for field, name in fields_to_validate if not field]
        
        if invalid_fields:
            fields_list = ", ".join(invalid_fields)
            tk.messagebox.showerror("Error", 
                f"The following fields are missing or invalid: {fields_list}")
            return False
            
        self.create_tab3()
        return True

    # Utility Methods
    def get_existing_folders(self, username, patient_name):
        """Get list of existing folders for the patient"""
        try:
            user_data_path = PATH_SETTINGS["USER_DATA"]
            patient_path = os.path.join(user_data_path, username, patient_name)
            
            if os.path.exists(patient_path):
                return sorted([folder for folder in os.listdir(patient_path) 
                             if os.path.isdir(os.path.join(patient_path, folder))])
            return []
        except Exception:
            return []

    def update_folder_dropdown(self, *args):
        """Update folder suggestions dropdown"""
        if hasattr(self, 'folder_combobox'):
            try:
                existing_folders = self.get_existing_folders(
                    self.username_var.get(),
                    self.patient_name.get()
                )
                self.folder_combobox.configure(values=existing_folders)
            except Exception:
                pass