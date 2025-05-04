# gui/tabs/tab2.py

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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

    def _handle_folder_selection(self):
        """
        Enhanced file-picker with special handling for NIfTI files to show file names.
        """
        # 1. Discover mounts
        mounts = []
        for d in Path("/media").iterdir() if Path("/media").exists() else []:
            if d.is_dir(): mounts.append(str(d))
        user_media = Path("/run/media") / getpass.getuser()
        for d in user_media.iterdir() if user_media.exists() else []:
            if d.is_dir(): mounts.append(str(d))

        if not mounts:
            messagebox.showerror(
                "No External Drives Detected",
                "No external storage devices were found. \n"
                "Please connect an external drive (e.g. USB) and try again."
            )
            return

        # 2. Dialog window - make it slightly larger
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Select Image Series")
        w, h = TAB2_SETTINGS["DIMENSIONS"]["DIALOG_SIZE"]
        w += 100  # Make wider
        h += 50   # Make taller
        dlg.geometry(f"{w}x{h}")
        
        # Configure grid
        dlg.grid_columnconfigure(0, weight=1)
        dlg.grid_rowconfigure(1, weight=1)  # Row 0 is for drive selection, Row 1 for treeview
        
        # 3. BIG DRIVE SELECTION at the top
        drive_frame = ctk.CTkFrame(dlg, fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"])
        drive_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Use large fonts for drive selection
        large_font = ("Arial", 18, "bold")
        button_font = ("Arial", 16, "bold")
        dropdown_font = ("Arial", 16)  # Font for dropdown items
        
        ctk.CTkLabel(
            drive_frame, 
            text="Select Drive:", 
            font=large_font
        ).pack(side="left", padx=(20, 10), pady=15)
        
        # Create drive dropdown
        drive_var = tk.StringVar()
        
        # CustomTkinter's combobox doesn't directly support setting the dropdown font size
        # So we need to use the underlying Tkinter combobox instead for better control
        
        # Create a custom styled ttk.Combobox to get bigger dropdown font
        style = ttk.Style(dlg)
        style.configure("BigCombo.TCombobox", padding=5)
        
        # Configure the dropdown list font - this is critical for readability
        dlg.option_add("*TCombobox*Listbox.font", dropdown_font)
        
        # Create the Combobox with the big style
        drive_dropdown = ttk.Combobox(
            drive_frame,
            values=[os.path.basename(m) for m in mounts],
            textvariable=drive_var,
            width=20,
            style="BigCombo.TCombobox",
            font=dropdown_font,  # This sets the entry part font
        )
        
        # Apply additional styling to make it larger
        drive_dropdown.pack(side="left", padx=10, pady=15)
        
        # Status label with larger font
        status_label = ctk.CTkLabel(
            drive_frame, 
            text="Select a drive and click Scan", 
            font=("Arial", 16),
            text_color=UI_SETTINGS["COLORS"]["TEXT_HIGHLIGHT"]
        )
        status_label.pack(side="right", padx=20, pady=15)
        
        # Larger scan button
        scan_button = ctk.CTkButton(
            drive_frame, 
            text="SCAN DRIVE", 
            font=button_font,
            width=160,
            height=40,
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"]
        )
        scan_button.pack(side="left", padx=20, pady=15)
        
        # 4. Treeview for series listing with much larger font
        tree_frame = ctk.CTkFrame(dlg)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style(dlg)
        style.configure(
            "BigTree.Treeview",
            font=("Arial", 16),
            rowheight=40
        )
        style.configure(
            "BigTree.Treeview.Heading",
            font=("Arial", 18, "bold")
        )

        # Create a treeview for series folders and files
        tree = ttk.Treeview(
            tree_frame, 
            columns=("path", "count", "type"), 
            show="headings", 
            selectmode="browse",
            style="BigTree.Treeview"
        )
        tree.heading("path", text="Series/File Name")
        tree.heading("count", text="Count/Size")
        tree.heading("type", text="Type")
        tree.column("path", width=450)
        tree.column("count", width=120, anchor="e")
        tree.column("type", width=120)
        tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        
        # Store information about selected items
        selected_info = {}
        
        def format_size(size_bytes):
            """Format file size in human-readable format"""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0 or unit == 'GB':
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
        
        def scan_drive():
            """Scan the selected drive for DICOM and NIfTI series, handling both folders and individual files"""
            # Clear previous entries
            for item in tree.get_children():
                tree.delete(item)
            
            selected_info.clear()
            
            # Get selected drive 
            drive_name = drive_var.get()
            if not drive_name:
                status_label.configure(text="⚠️ Please select a drive first")
                return
                
            # Find the full path matching this drive name
            drive_path = None
            for m in mounts:
                if os.path.basename(m) == drive_name:
                    drive_path = m
                    break
                    
            if not drive_path:
                status_label.configure(text="⚠️ Drive not found")
                return
                
            # Disable scan button and update status
            scan_button.configure(state="disabled", text="SCANNING...")
            status_label.configure(text="⏳ Scanning drive for image series...")
            dlg.update()  # Update UI to show status change
            
            # Use a thread to scan the drive without freezing UI
            def scan_thread():
                # Dictionary to track folders containing medical images
                dicom_folders = {}
                nifti_files = []
                
                # Walk through all directories on the drive
                for root, dirs, files in os.walk(drive_path):
                    # Skip certain folder patterns common in macOS/Windows
                    if any(skip in root for skip in ['.Trash', '$Recycle.Bin', 'System Volume Information']):
                        continue
                    
                    # For DICOM: track folders with DICOM files
                    dicom_count = 0
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_dicom_file(file_path):
                            dicom_count += 1
                    
                    # If folder contains DICOM images, add to tracking
                    if dicom_count > 0:
                        dicom_folders[root] = {
                            "path": root,
                            "name": os.path.basename(root),
                            "count": dicom_count,
                            "type": "DICOM",
                            "is_folder": True
                        }
                    
                    # For NIfTI: track individual files
                    for file in files:
                        if file.lower().endswith(('.nii', '.nii.gz')):
                            file_path = os.path.join(root, file)
                            try:
                                file_size = os.path.getsize(file_path)
                                # Only include NIfTI files larger than 1 MB (1,048,576 bytes)
                                # This is because segmentations are also saved in NIfTI format after nnUNet but weigh less than 1 MB
                                if file_size >= 1048576:
                                    nifti_files.append({
                                        "path": file_path,
                                        "name": file,  # Use file name, not folder name
                                        "size": file_size,
                                        "size_str": format_size(file_size),
                                        "type": "NIfTI",
                                        "is_folder": False
                                    })
                            except OSError:
                                # Skip files we can't access
                                pass
                
                # Sort DICOM folders by name
                sorted_dicom_folders = sorted(dicom_folders.values(), key=lambda x: x["name"].lower())
                
                # Sort NIfTI files by name
                sorted_nifti_files = sorted(nifti_files, key=lambda x: x["name"].lower())
                
                # Combine both lists, with DICOM folders first
                all_items = sorted_dicom_folders + sorted_nifti_files
                
                # Update UI from main thread
                dlg.after(0, lambda: update_list(all_items))
            
            def update_list(items):
                """Update the treeview with both folder and file information"""
                for item in items:
                    try:
                        # Different display for folders vs files
                        if item["is_folder"]:
                            # DICOM folder - show relative path
                            rel_path = os.path.relpath(item["path"], drive_path)
                            
                            # If it's a deep path, simplify it
                            if rel_path.count(os.sep) > 2:
                                path_parts = rel_path.split(os.sep)
                                # Show first folder + "..." + last two folders
                                display_path = f"{path_parts[0]}/.../{path_parts[-2]}/{path_parts[-1]}"
                            else:
                                display_path = rel_path
                                
                            # Add count info for folders
                            count_str = f"{item['count']} images"
                            
                        else:
                            # NIfTI file - show file name directly
                            display_path = item["name"]
                            count_str = item["size_str"]
                        
                        # Add to tree
                        item_id = tree.insert("", "end", values=(
                            display_path, 
                            count_str, 
                            item["type"]
                        ))
                        
                        # Store original info for later
                        selected_info[item_id] = item
                        
                    except Exception as e:
                        self.logger.log_error(f"Error adding item to tree: {e}")
                
                # Update status and re-enable scan button
                nifti_count = sum(1 for item in items if not item["is_folder"])
                dicom_count = sum(1 for item in items if item["is_folder"])
                status_label.configure(
                    text=f"✅ Found {dicom_count} DICOM series and {nifti_count} NIfTI files"
                )
                scan_button.configure(state="normal", text="SCAN DRIVE")
                
                # Select first item if available
                if tree.get_children():
                    tree.selection_set(tree.get_children()[0])
                    tree.focus(tree.get_children()[0])
            
            import threading
            scan_thread = threading.Thread(target=scan_thread)
            scan_thread.daemon = True
            scan_thread.start()
        
        # Connect scan button command
        scan_button.configure(command=scan_drive)
        
        # 5. Button bar at bottom with large buttons
        btn_frame = ctk.CTkFrame(dlg)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="e", pady=10, padx=10)

        def on_open():
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select a series or file.")
                return
                
            # Get the selected item info
            item_info = selected_info[selected_items[0]]
            
            # Handle differently based on if it's a folder (DICOM) or file (NIfTI)
            if item_info["is_folder"]:
                # DICOM folder - get all DICOM files in the folder
                folder_path = item_info["path"]
                files = []
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path) and self._is_dicom_file(file_path):
                        files.append(file_path)
                        
                if not files:
                    messagebox.showwarning("No Files", "No valid DICOM files found in the selected folder.")
                    return
                    
                dlg.destroy()
                self._process_files(files, folder_path)
                
            else:
                # NIfTI file - just use this single file
                file_path = item_info["path"]
                folder_path = os.path.dirname(file_path)
                
                dlg.destroy()
                self._process_files([file_path], folder_path)

        # Large buttons
        btn_kwargs = dict(
            width=150, 
            height=50, 
            font=("Arial", 16, "bold")
        )
        
        ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=dlg.destroy, 
            fg_color=UI_SETTINGS["COLORS"]["DISABLED_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["WARNING"],
            **btn_kwargs
        ).pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="Open Selection", 
            command=on_open,
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            **btn_kwargs
        ).pack(side="right", padx=10)

        # Double-click to open
        tree.bind("<Double-1>", lambda event: on_open())

        # Force update before grab
        dlg.update()
        
        # Center the dialog on the parent window
        self.app.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - dlg.winfo_width()) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        
        # Now it should be safe to grab
        try:
            dlg.grab_set()
        except Exception as e:
            self.logger.log_error(f"Dialog grab error: {e}")
            # Continue without grab - dialog will still work, just not modal
        
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