# gui/tabs/tab2.py

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import os
from datetime import datetime
import pydicom
from pathlib import Path
import getpass
## From other scripts
from ..components.buttons import _create_info_button
from ..components.forms import FormSection, LabeledEntry
from ..components.navigation import NavigationFrame
from ..utils.tooltips import ToolTip
from gui.utils.basic_utils import AppLogger
from gui.config.settings import UI_SETTINGS, PATH_SETTINGS,TAB2_SETTINGS


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

        # Add workflow explanation at the top
        self._create_workflow_guide()
        
        # Create all sections but start with only upload section active
        self._create_upload_section(active=True)
        self._create_patient_info_section(active=False)
        self._create_folder_section(active=False)
        self._create_navigation()
        
        # Clear any existing traces to avoid duplicate triggers
        for trace_id in getattr(self.app, '_name_traces', []):
            try:
                self.app.patient_name.trace_remove("write", trace_id)
            except Exception:
                pass  # Ignore if trace doesn't exist
                
        # Store trace IDs for later cleanup
        self.app._name_traces = []
        
        # Add trace to patient_name for both folder dropdown updates and section activation
        trace_id = self.app.patient_name.trace_add("write", lambda *args: self._update_folder_dropdown())
        self.app._name_traces.append(trace_id)
        
        trace_id = self.app.patient_name.trace_add("write", lambda *args: self._check_activate_folder_section())
        self.app._name_traces.append(trace_id)
        
        self.app.bind_enter_key(self._validate_and_proceed)
    
    def _create_workflow_guide(self):
        """Create a workflow guide explaining the steps"""
        guide_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        guide_frame.pack(fill="x", pady=(0, UI_SETTINGS["PADDING"]["MEDIUM"]))
        
        ctk.CTkLabel(
            guide_frame,
            text="Complete the following steps in order:",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(anchor="w", pady=(0, 5))
        
        steps = [
            "1. Connect external drive and click on Browse for Medical Images to upload patient scan",
            "2. Review and/or complete patient information",
            "3. Type or select a case label"
        ]
        
        for step in steps:
            ctk.CTkLabel(
                guide_frame,
                text=step,
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
            ).pack(anchor="w", padx=20)

    def _create_header(self):
        """Create the header with home button and step indicator"""
        top_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Home button
        ctk.CTkButton(
            top_frame,
            text=TAB2_SETTINGS["TEXT"]["HOME_BUTTON"],
            command=self.app.go_home,
            width=UI_SETTINGS["HOME_BUTTON"]["WIDTH"],
            height=UI_SETTINGS["HOME_BUTTON"]["HEIGHT"],
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        ).pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text=TAB2_SETTINGS["TEXT"]["STEP_HEADER"],
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            anchor="center"
        ).pack(side="left", expand=True)

    def _create_main_frame(self):
        """Create the main content frame with grid layout"""
        main_frame = ctk.CTkFrame(self.app.main_frame)
        main_frame.pack(fill="both", expand=True, padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])
        return main_frame

    def _create_upload_section(self, active=True):
        """Create the file upload section using a single file selection button with filtering."""
        upload_frame = ctk.CTkFrame(
            self.main_frame, 
            fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"] if active else UI_SETTINGS["COLORS"]["SECTION_INACTIVE"]
        )
        upload_frame.pack(fill="x", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])
        self.upload_frame = upload_frame  # Store reference for later activation
        
        # Section header with step indicator
        header_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=UI_SETTINGS["PADDING"]["SMALL"])
        
        step_indicator = ctk.CTkLabel(
            header_frame,
            text="Step 1",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_HIGHLIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        )
        step_indicator.pack(side="left", padx=(5, 10))
        
        ctk.CTkLabel(
            header_frame,
            text=TAB2_SETTINGS["TEXT"]["UPLOAD_LABEL"],
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        ).pack(side="left", pady=UI_SETTINGS["PADDING"]["SMALL"])

        # Rest of the existing code...
        self.folder_status_label = ctk.CTkLabel(
            upload_frame,
            text=TAB2_SETTINGS["TEXT"]["UPLOAD_STATUS_NO_FILES"],
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        )
        self.folder_status_label.pack(pady=UI_SETTINGS["PADDING"]["SMALL"])

        # Single selection button
        selection_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        selection_frame.pack(pady=(5, 10))

        select_button = ctk.CTkButton(
            selection_frame,
            text=TAB2_SETTINGS["TEXT"]["BROWSE_BUTTON"],
            command=self._handle_folder_selection,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"] if active else UI_SETTINGS["COLORS"]["DISABLED_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"] if active else UI_SETTINGS["COLORS"]["DISABLED_BUTTON"],
            state="normal" if active else "disabled",
            **TAB2_SETTINGS["DIMENSIONS"]["BROWSE_BUTTON"]
        )
        select_button.pack(side="left", padx=(0, 5))
        self.select_button = select_button  # Store reference

        # Info button with tooltip explanation
        info_button = _create_info_button(
            selection_frame,
            "Connect an external drive with patient scan files in DICOM or NIfTI format,\nfind drive from the dropdown menu, and click on SCAN DRIVE. \n" 
            "Wait for the drive to finish mounting if screen remains clear. \n"
            "If no files appear after 1 minute, inspect files in another computer"
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

    def _create_patient_info_section(self, active=False):
        """Create the patient information form section with centered alignment"""
        info_frame = ctk.CTkFrame(
            self.main_frame, 
            fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"] if active else UI_SETTINGS["COLORS"]["SECTION_INACTIVE"]
        )
        info_frame.pack(fill="both", expand=True, padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])
        self.info_frame = info_frame  # Store reference for later activation
        
        # Section header with step indicator
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=UI_SETTINGS["PADDING"]["SMALL"])
        
        step_indicator = ctk.CTkLabel(
            header_frame,
            text="Step 2",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_HIGHLIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        )
        step_indicator.pack(side="left", padx=(5, 10))

        # Title Label
        ctk.CTkLabel(
            header_frame,
            text=TAB2_SETTINGS["TEXT"]["PATIENT_INFO_TITLE"],
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        ).pack(side="left", pady=UI_SETTINGS["PADDING"]["SMALL"])

        # Create entries but make them disabled if section is not active
        # Rest of existing code with state and color adjustments...
        
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

        # Store entry widgets for later enabling/disabling
        self.patient_info_entries = []

        label_font = UI_SETTINGS["FONTS"]["NORMAL"]

        for i, (label_text, variable) in enumerate(fields):
            ctk.CTkLabel(
                form_frame,
                text=label_text,
                font=label_font,
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"],
                anchor="e"
            ).grid(row=i, column=0, padx=(0, 10), pady=5, sticky="e")

            entry = ctk.CTkEntry(
                form_frame,
                textvariable=variable,
                width=300,
                fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["DISABLED_BG"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"],
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                state="normal" if active else "disabled"
            )
            entry.grid(row=i, column=1, padx=(0, 10), pady=5, sticky="w")
            self.patient_info_entries.append(entry)

    def _create_folder_section(self, active=False):
        """Create the folder selection section and reduce vertical spacing"""
        folder_frame = ctk.CTkFrame(
            self.main_frame, 
            fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"] if active else UI_SETTINGS["COLORS"]["SECTION_INACTIVE"]
        )
        folder_frame.pack(fill="both", expand=True, padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["SMALL"])
        self.folder_frame = folder_frame  # Store reference for later activation
        
        # Section header with step indicator
        header_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=UI_SETTINGS["PADDING"]["SMALL"])
        
        step_indicator = ctk.CTkLabel(
            header_frame,
            text="Step 3",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_HIGHLIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        )
        step_indicator.pack(side="left", padx=(5, 10))

        # Title Label (Reduced padding)
        ctk.CTkLabel(
            header_frame,
            text="Case Label",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]
        ).pack(side="left", pady=(2, 2))  # Reduced spacing

        # Centered Selection Frame
        selection_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        selection_frame.pack(expand=True, anchor="center", pady=(2, 5))  # Reduced spacing

        selection_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_columnconfigure(1, weight=1)

        # Label
        ctk.CTkLabel(
            selection_frame,
            text="Enter folder label:",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"],
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
            fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["DISABLED_BG"],
            dropdown_fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"] if active else UI_SETTINGS["COLORS"]["DISABLED_BG"],
            dropdown_text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"] if active else UI_SETTINGS["COLORS"]["TEXT_DISABLED"],
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            dropdown_font=UI_SETTINGS["FONTS"]["NORMAL"],
            state="normal" if active else "disabled",
            command=self._on_combobox_select
        )
        self.app.folder_combobox.pack(side="left", padx=(0, 5))

        # Info Button (Tooltip)
        info_button = _create_info_button(
            combo_frame,
            "This label can be used to differentiate and organize anonymized patient results. \n"
            "No need to specify breathing rate at this point: Simulation results for different breathing rates are saved in separate subfolders automatically.",
        )
        info_button.pack(side="left")


    # ===========================================================================================
    # ======================= LOGIC TO ACTIVATE SECTION HIGHLIGHT ===============================
    # ===========================================================================================

    def _process_files(self, files, folder_path):
        """Process selected files, auto-detect DICOM series, and update UI."""
        dicom_files, nifti_files = [], []
        for file_path in files:
            if self._is_dicom_file(file_path):
                dicom_files.append(file_path)
            elif file_path.lower().endswith(('.nii', '.nii.gz')):
                nifti_files.append(file_path)

        # If a single DICOM file was selected, load the whole series from its folder
        if len(dicom_files) == 1:
            parent_folder = os.path.dirname(dicom_files[0])
            dicom_files = [os.path.join(parent_folder, f) 
                            for f in os.listdir(parent_folder) 
                            if self._is_dicom_file(os.path.join(parent_folder, f))]

        file_type_str = "DICOM" if dicom_files else "NIfTI"
        file_count = len(dicom_files) if dicom_files else len(nifti_files)
        
        self.folder_status_label.configure(
            text=f"Found: {file_count} {file_type_str} files in {Path(folder_path).name}"
        )
        
        self.app.selected_files = dicom_files + nifti_files
        self.app.selected_dicom_folder = folder_path if dicom_files else ""

        # Process patient info if needed
        if dicom_files:
            self._extract_patient_info_from_dicom(dicom_files[0])
        else:
            self._clear_patient_fields()
            
        # After successful file processing, activate the patient info section
        self._activate_patient_info_section()
        
        messagebox.showinfo(
            "Success",
            TAB2_SETTINGS["TEXT"]["LOAD_SUCCESS"].format(count=file_count, type=file_type_str)
            )

    def _activate_patient_info_section(self):
        """Activate the patient info section after files are uploaded"""
        # Change background colors to show active state
        self.info_frame.configure(fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"])
        
        # Find and update all labels in the info frame recursively
        def update_labels(widget):
            if isinstance(widget, ctk.CTkLabel):
                if widget.cget("text") == "Step 2":
                    widget.configure(text_color=UI_SETTINGS["COLORS"]["TEXT_HIGHLIGHT"])
                else:
                    widget.configure(text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"])
            elif hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    update_labels(child)
        
        update_labels(self.info_frame)
        
        # Enable all entry widgets
        for entry in self.patient_info_entries:
            entry.configure(
                state="normal",
                fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
            )
        
        # If a patient name is already entered, activate the folder section immediately
        if self.app.patient_name.get().strip():
            self._check_activate_folder_section()

    def _check_activate_folder_section(self):
        """Check if patient name is filled and activate folder section if it is"""
        if hasattr(self, 'folder_frame') and self.app.patient_name.get().strip():
            # Change background colors to show active state
            self.folder_frame.configure(fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"])
            
            # Find and update all labels in the folder frame recursively
            def update_labels(widget):
                if isinstance(widget, ctk.CTkLabel):
                    if widget.cget("text") == "Step 3":
                        widget.configure(text_color=UI_SETTINGS["COLORS"]["TEXT_HIGHLIGHT"])
                    else:
                        widget.configure(text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"])
                elif hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        update_labels(child)
            
            update_labels(self.folder_frame)
            
            # Enable the combobox
            if hasattr(self.app, 'folder_combobox'):
                self.app.folder_combobox.configure(
                    state="normal",
                    fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                    text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"],
                    dropdown_fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                    dropdown_text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
                )
                
            # Log that the section has been activated for debugging
            self.logger.log_info("Case Label section activated")

    # ============================================================================================================

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
            back_command=self.app.go_home,
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
            # Sanitize the patient name to remove spaces
            sanitized_patient_name = self.app.patient_name.get().replace(" ", "")
            
            patient_path = PATH_SETTINGS["USER_DATA"] / self.app.username_var.get() / sanitized_patient_name
            
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

    def _is_within_drive(self, base_path, target_path):
        """Return True if target_path is inside base_path."""
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        try:
            target.relative_to(base)
            return True
        except ValueError:
            return False

    def _handle_folder_selection(self):
        """Let the user pick a drive and manually choose a DICOM folder or NIfTI file(s)."""
        # Discover mounted drives
        mounts = []
        for d in Path("/media").iterdir() if Path("/media").exists() else []:
            if d.is_dir():
                mounts.append(str(d))
        user_media = Path("/run/media") / getpass.getuser()
        for d in user_media.iterdir() if user_media.exists() else []:
            if d.is_dir():
                mounts.append(str(d))

        if not mounts:
            messagebox.showerror(
                "No External Drives Detected",
                "No external storage devices were found. \n"
                "Please connect an external drive (e.g. USB) and try again.",
                parent=self.app
            )
            return

        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Select Medical Images")
        # Keep the dialog compact and scaled to the current screen
        cfg_w, cfg_h = TAB2_SETTINGS["DIMENSIONS"]["DIALOG_SIZE"]
        screen_w = self.app.winfo_screenwidth()
        screen_h = self.app.winfo_screenheight()
        w = min(cfg_w, int(screen_w * 0.7))
        h = min(cfg_h, int(screen_h * 0.7))
        dlg.geometry(f"{w}x{h}")
        dlg.grid_columnconfigure(0, weight=1)
        dlg.grid_rowconfigure(1, weight=1)
        dlg.grid_rowconfigure(2, weight=0)

        drive_frame = ctk.CTkFrame(dlg, fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"])
        drive_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            drive_frame,
            text="Select an external drive, then browse within this window:",
            font=UI_SETTINGS["FONTS"]["CATEGORY"]
        ).pack(side="left", padx=(20, 10), pady=15)

        drive_var = tk.StringVar()
        drive_dropdown = ttk.Combobox(
            drive_frame,
            values=[f"{os.path.basename(m)} ({m})" for m in mounts],
            textvariable=drive_var,
            width=50,
            state="readonly",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
        )
        drive_dropdown.pack(side="left", padx=10, pady=15)
        if mounts:
            drive_dropdown.set(f"{os.path.basename(mounts[0])} ({mounts[0]})")

        current_path_label = ctk.CTkLabel(
            drive_frame,
            text="",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            wraplength=600,
            justify="left"
        )
        current_path_label.pack(side="left", padx=10, pady=15)

        def get_drive_path():
            value = drive_var.get()
            if "(" in value and value.endswith(")"):
                return value.split("(", 1)[1][:-1]
            messagebox.showwarning("Drive Required", "Please select a valid drive.", parent=dlg)
            return None

        # Icons for tree rows (kept as attributes to prevent garbage collection)
        back_xbm = r"""
#define back_width 24
#define back_height 12
static unsigned char back_bits[] = {
 0x00,0x00,0x00,
 0x04,0x00,0x00,
 0x0c,0x00,0x00,
 0x1c,0x00,0x00,
 0x3c,0x00,0x00,
 0x7c,0x00,0x00,
 0xfc,0x00,0x00,
 0x7c,0x00,0x00,
 0x3c,0x00,0x00,
 0x1c,0x00,0x00,
 0x0c,0x00,0x00,
 0x04,0x00,0x00};
"""

        folder_xbm = r"""
#define folder_width 24
#define folder_height 12
static unsigned char folder_bits[] = {
 0xf8,0x07,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0xfe,0x0f,0x00,
 0x00,0x00,0x00};
"""
        file_xbm = r"""
#define file_width 24
#define file_height 12
static unsigned char file_bits[] = {
 0xff,0xff,0x03,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0x01,0x00,0x02,
 0xff,0xff,0x03,
 0x00,0x00,0x00};
"""
        icons = {
            "back": tk.BitmapImage(data=back_xbm, foreground="red"),
            "folder": tk.BitmapImage(data=folder_xbm, foreground="blue"),
            "file": tk.BitmapImage(data=file_xbm, foreground=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]),
        }
        self._browse_icons = icons

        style = ttk.Style(dlg)
        style.configure(
            "DriveTree.Treeview",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            rowheight=28
        )

        list_frame = ctk.CTkFrame(dlg)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        tree = ttk.Treeview(
            list_frame,
            columns=("name",),
            show="tree",
            selectmode="extended",
            style="DriveTree.Treeview"
        )
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.tag_configure("back", foreground="red")
        tree.tag_configure("folder", foreground="blue")

        current_path = {"path": None}

        def refresh_list(path):
            drive_root = get_drive_path()
            if not drive_root or not self._is_within_drive(drive_root, path):
                return
            current_path["path"] = path
            current_path_label.configure(text=path)
            for item in tree.get_children(""):
                tree.delete(item)

            entries = []
            try:
                for entry in os.listdir(path):
                    full = os.path.join(path, entry)
                    entries.append((entry, full, os.path.isdir(full)))
            except Exception:
                return
            entries.sort(key=lambda x: (not x[2], x[0].lower()))

            drive_root_resolved = Path(drive_root).resolve()
            path_resolved = Path(path).resolve()
            if path_resolved != drive_root_resolved:
                tree.insert(
                    "",
                    "end",
                    iid="__back__",
                    text="Back",
                    image=icons["back"],
                    tags=("back",)
                )

            for name, full, is_dir in entries:
                img = icons["folder"] if is_dir else icons["file"]
                tags = ("folder",) if is_dir else ()
                tree.insert("", "end", iid=full, text=name, image=img, tags=tags)

        def on_drive_change(event=None):
            drive_root = get_drive_path()
            if drive_root:
                refresh_list(drive_root)

        drive_dropdown.bind("<<ComboboxSelected>>", on_drive_change)

        def on_item_activate(event=None):
            selection = tree.selection()
            if not selection:
                return
            target = selection[0]
            if target == "__back__":
                if current_path["path"]:
                    parent_path = str(Path(current_path["path"]).parent)
                    refresh_list(parent_path)
                return
            if os.path.isdir(target):
                refresh_list(target)

        tree.bind("<Double-Button-1>", on_item_activate)
        tree.bind("<Return>", on_item_activate)

        def choose_dicom_folder():
            drive_path = get_drive_path()
            if not drive_path:
                return
            folder_path = current_path["path"]
            selected = [iid for iid in tree.selection() if iid != "__back__"]
            if len(selected) == 1 and os.path.isdir(selected[0]):
                folder_path = selected[0]
            if not folder_path:
                messagebox.showwarning("Folder Required", "Browse to a folder first.", parent=dlg)
                return
            if not self._is_within_drive(drive_path, folder_path):
                messagebox.showwarning("Invalid Selection", "Please select a valid DICOM folder on the desired drive.", parent=dlg)
                return
            if not os.path.isdir(folder_path):
                messagebox.showwarning("Invalid Selection", "Please select a folder (not a file).", parent=dlg)
                return
            files = []
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path) and self._is_dicom_file(file_path):
                    files.append(file_path)
            if not files:
                messagebox.showwarning("No DICOM Files", "No DICOM files found in current folder.", parent=dlg)
                return
            # Persist the selected drive root for later export
            self.app.selected_drive_path.set(drive_path)
            dlg.destroy()
            self._process_files(files, folder_path)

        def choose_nifti_files():
            drive_path = get_drive_path()
            if not drive_path:
                return
            selected = [iid for iid in tree.selection() if iid != "__back__"]
            if not selected:
                messagebox.showwarning("Select Files", "Select NIfTI file.", parent=dlg)
                return
            valid_paths = [
                p for p in selected
                if os.path.isfile(p) and p.lower().endswith((".nii", ".nii.gz")) and self._is_within_drive(drive_path, p)
            ]
            if not valid_paths or len(valid_paths) != len(selected):
                messagebox.showwarning("Invalid Selection", "Please select valid NIfTI file (.nii.gz).", parent=dlg)
                return
            # Persist the selected drive root for later export
            self.app.selected_drive_path.set(drive_path)
            dlg.destroy()
            self._process_files(list(valid_paths), Path(valid_paths[0]).parent)

        # Initialize browser
        on_drive_change()

        # Action buttons
        btn_frame = ctk.CTkFrame(dlg)
        btn_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        btn_kwargs = dict(width=180, height=44, font=("Arial", 15, "bold"))

        ctk.CTkButton(
            btn_frame,
            text="Select DICOM Folder",
            command=choose_dicom_folder,
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            **btn_kwargs
        ).grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Select NIfTI File",
            command=choose_nifti_files,
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            **btn_kwargs
        ).grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dlg.destroy,
            fg_color=UI_SETTINGS["COLORS"]["DISABLED_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["WARNING"],
            **btn_kwargs
        ).grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        # Modal behavior
        dlg.transient(self.app)
        dlg.grab_set()
        dlg.focus_force()

        # Center the dialog on the parent window
        self.app.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - dlg.winfo_width()) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

        self.app.wait_window(dlg)


    def _is_dicom_file(self, file_path):
        """
        Check if a file is a DICOM file without relying on file extension.
        This method handles the PyDICOM issue of appending .dcm to files without extensions,
        and is more tolerant of VR variations.
        
        Args:
            file_path (str): Path to the file to check
        Returns:
            bool: True if the file is a valid DICOM file, False otherwise
        """
        try:
            # Skip directories and specifically CASEDATA
            path_obj = Path(file_path)
            if path_obj.is_dir():
                return False
            # Skip files within directories named CASEDATA
            if "CASEDATA" in path_obj.parts:
                return False
                
            # Open file in binary mode to check for DICOM magic number
            with open(file_path, 'rb') as f:
                # Skip the 128-byte preamble
                f.seek(128)
                # Check for DICM magic number
                magic = f.read(4)
                if magic == b'DICM':
                    # It's a standard DICOM file with proper header
                    return True
                    
            # If no magic number, try to read it with PyDICOM directly
            # This is a workaround for the extension issue
            import pydicom
            import warnings
            
            # Temporarily suppress the VR warnings during file validation
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="pydicom")
                
                # Force read without assuming an extension, and be more tolerant
                # stop_before_pixels=True speeds up validation by not reading pixel data
                # specific_tags helps target just the key tags we need to validate
                dataset = pydicom.dcmread(
                    file_path, 
                    force=True,
                    stop_before_pixels=True,
                    specific_tags=['SOPClassUID', 'Modality', 'PatientID', 'StudyInstanceUID']
                )
                
                # Check for some basic DICOM attributes to confirm it's a valid file
                # This helps filter out files that PyDICOM reads but aren't actually DICOM
                return (hasattr(dataset, 'SOPClassUID') or 
                        hasattr(dataset, 'Modality') or 
                        hasattr(dataset, 'PatientID') or
                        hasattr(dataset, 'StudyInstanceUID'))
                        
        except Exception as e:
            # Change this to debug level since it's expected for non-DICOM files
            if "CASEDATA" not in file_path:  # Only log if not CASEDATA
                self.logger.log_debug(f"Not DICOM: {os.path.basename(file_path)}, reason: {str(e)}")
            return False

    def _extract_patient_info_from_dicom(self, dicom_path):
        """Extract patient information from a DICOM file, ensuring missing dates are replaced with a placeholder."""
        try:
            dicom_data = pydicom.dcmread(str(dicom_path), force=True)

            # Extract Name
            self.app.patient_name.set(str(dicom_data.PatientName) if hasattr(dicom_data, "PatientName") else "")

            # Extract Referring Physician
            if hasattr(dicom_data, "ReferringPhysicianName"):
                doctor = dicom_data.ReferringPhysicianName
                self.app.patient_doctor_var.set(
                    f"{doctor.family_name}, {doctor.given_name}" if hasattr(doctor, "family_name") else str(doctor)
                )
            else:
                self.app.patient_doctor_var.set("")

            # Extract Dates (Birthdate and Scan Date)
            default_date = "1900-01-01"
            for date_attr, var in [("PatientBirthDate", self.app.dob), ("StudyDate", self.app.scandate)]:
                if hasattr(dicom_data, date_attr):
                    date_str = getattr(dicom_data, date_attr)
                    if len(date_str) == 8:  # Ensure valid format
                        formatted_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
                        var.set(formatted_date)
                    else:
                        var.set(default_date)
                else:
                    var.set(default_date)

        except Exception as e:
            self.logger.log_error(f"Error extracting DICOM patient info: {str(e)}")

    
    def _clear_patient_fields(self):
        """Clear patient information fields when using NIfTI files"""
        self.app.patient_name.set("")
        self.app.patient_doctor_var.set("")
        self.app.dob.set("")
        self.app.scandate.set("")

    def _setup_output_folder(self):
        """Set up and create the output folder path if all required fields are filled"""
        missing_fields = [
            name for attr_name, name in TAB2_SETTINGS["REQUIRED_FIELDS"] 
            if not getattr(self.app, attr_name).get()
        ]
        
        if missing_fields:
            # Determine if scans are missing
            scan_missing = not hasattr(self.app, 'selected_files') or not self.app.selected_files
            
            if scan_missing:
                # Only scans are missing
                messagebox.showerror(
                    "Patient Scans Required",
                    "Please upload the patient scan files before proceeding."
                )
            else:
                # Only fields are missing
                # Create the bullet list without using f-string for the bullets
                bullet_list = ""
                for field in missing_fields:
                    bullet_list += "• " + field + "\n"
                    
                messagebox.showerror(
                    "Required Information Missing",
                    f"Please complete the following required fields:\n\n{bullet_list}"
                )
            return False

        try:
            # Sanitize the patient name to remove spaces
            sanitized_patient_name = self.app.patient_name.get().replace(" ", "")
            
            folder_path = (
                PATH_SETTINGS["USER_DATA"] /
                self.app.username_var.get() / 
                sanitized_patient_name / 
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

    def _bind_enter_key_to_all_widgets(self, parent):
        """Recursively bind the Enter key to all real Entry widgets."""
        for child in parent.winfo_children():
            # CTkEntry wraps a real tk.Entry in its private _entry attribute
            if isinstance(child, ctk.CTkEntry):
                child._entry.bind("<Return>", lambda e: self._validate_and_proceed())

            # CTkComboBox wraps a real tk.Entry in _combobox_entry
            elif isinstance(child, ctk.CTkComboBox):
                child._combobox_entry.bind("<Return>", lambda e: self._validate_and_proceed())

            # Recurse into any container
            if child.winfo_children():
                self._bind_enter_key_to_all_widgets(child)

    def _validate_and_proceed(self):
        """Validate the form and proceed to next tab"""
        if not self._setup_output_folder():
            return
            
        self.app.create_tab3()
