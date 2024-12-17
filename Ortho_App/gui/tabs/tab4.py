# gui/tabs/tab4.py

import customtkinter as ctk
from tkinter import ttk, messagebox
import time
from ..components.navigation import NavigationFrame
from ..components.progress import ProgressSection
from ..components.forms import FormSection

class Tab4Manager:
    def __init__(self, app):
        """Initialize Tab4Manager with a reference to the main app"""
        self.app = app
        self.processing_active = False
        
    def create_tab(self):
        """Create and set up the analysis and processing page"""
        self._create_header()
        self._create_main_content()
        self._create_navigation()

    def _create_header(self):
        """Create the header with home button and context information"""
        # Top frame
        top_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 10))
        
        # Configure grid layout
        top_frame.columnconfigure(0, weight=1)  # Home button
        top_frame.columnconfigure(1, weight=3)  # Context info
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

        # Context header
        context_text = (
            f"Patient: {self.app.patient_name.get()} | "
            f"DOB: {self.app.dob.get()} | "
            f"Physician: {self.app.patient_doctor_var.get()}"
        )
        ctk.CTkLabel(
            top_frame,
            text=context_text,
            font=("Arial", 13),
            anchor="center"
        ).grid(row=0, column=1, padx=10, pady=5)

    def _create_main_content(self):
        """Create the main content area with analysis options and processing sections"""
        # Main content frame
        content_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Analysis options section
        self._create_analysis_section(content_frame)
        
        # Processing section
        self._create_processing_section(content_frame)
        
        # Results section (initially hidden)
        self.results_frame = self._create_results_section(content_frame)

    def _create_analysis_section(self, parent):
        """Create the analysis options section"""
        analysis_section = FormSection(parent, "Analysis Options")
        analysis_section.pack(fill="x", pady=10)

        # Analysis type dropdown
        self.analysis_option = ctk.StringVar(value="Select Analysis Type")
        analysis_dropdown = ctk.CTkOptionMenu(
            analysis_section.content,
            variable=self.analysis_option,
            values=[
                "Upper Airway Segmentation",
                "Airflow Simulation (includes segmentation)"
            ],
            command=self._update_processing_details,
            width=300,
            height=40,
            font=("Arial", 14)
        )
        analysis_dropdown.pack(pady=(10, 15))

        # Processing details label
        self.processing_details_label = ctk.CTkLabel(
            analysis_section.content,
            text="",
            font=("Arial", 12),
            wraplength=300,
            justify="center"
        )
        self.processing_details_label.pack(pady=(0, 20))

    def _create_processing_section(self, parent):
        """Create the processing section with progress bar"""
        processing_section = FormSection(parent, "Processing")
        processing_section.pack(fill="x", pady=10)

        # Start button
        self.process_button = ctk.CTkButton(
            processing_section.content,
            text="Start Processing",
            command=self._validate_and_start_processing,
            width=300,
            height=40,
            font=("Arial", 14)
        )
        self.process_button.pack(pady=10)

        # Progress section
        self.progress_section = ProgressSection(processing_section.content)
        self.progress_section.pack(fill="x", pady=10)

    def _create_results_section(self, parent):
        """Create the results section (initially hidden)"""
        results_frame = ctk.CTkFrame(parent, corner_radius=10)
        
        # Title
        ctk.CTkLabel(
            results_frame,
            text="Results",
            font=("Arial", 15, "bold")
        ).pack(pady=(10, 5))

        # Buttons frame
        button_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        # Result action buttons
        actions = [
            ("Save Results", self._save_results),
            ("Export Reports", self._export_reports),
            ("Visualize Data", self._visualize_data)
        ]

        for text, command in actions:
            ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                width=120,
                height=32
            ).pack(side="left", padx=5)

        return results_frame

    def _update_processing_details(self, choice):
        """Update the processing details based on selected analysis type"""
        details = {
            "Upper Airway Segmentation": 
                "This will perform automatic segmentation of the upper airway "
                "from the DICOM images.",
            
            "Airflow Simulation (includes segmentation)":
                "This will first perform airway segmentation, followed by CFD "
                "analysis to simulate airflow patterns and pressure changes."
        }
        
        self.processing_details_label.configure(
            text=details.get(choice, "Please select an analysis type to proceed.")
        )

    def _validate_and_start_processing(self):
        """Validate selection and start processing"""
        if self.processing_active:
            return

        if self.analysis_option.get() == "Select Analysis Type":
            messagebox.showerror("Error", "Please select an analysis type before proceeding.")
            return

        # Show confirmation dialog
        response = messagebox.askquestion(
            "Confirm Analysis",
            f"Selected analysis: {self.analysis_option.get()}\n\nDo you want to proceed?",
            icon="warning"
        )
        
        if response == "yes":
            self._start_processing()

    def _start_processing(self):
        """Start the processing sequence"""
        self.processing_active = True
        self.process_button.configure(state="disabled")
        
        # Define processing steps based on analysis type
        if self.analysis_option.get() == "Airflow Simulation (includes segmentation)":
            steps = [
                ("Segmenting airway...", 2),
                ("Generating mesh...", 2),
                ("Running CFD simulation...", 3),
                ("Analyzing results...", 1)
            ]
        else:
            steps = [
                ("Segmenting airway...", 2),
                ("Finalizing results...", 1)
            ]

        self._process_steps(steps)

    def _process_steps(self, steps):
        """Process multiple steps sequentially"""
        def run_step(step_index):
            if step_index < len(steps):
                message, duration = steps[step_index]
                self.progress_section.start(message)
                # Schedule next step
                self.app.after(
                    duration * 1000,  # Convert to milliseconds
                    lambda: run_step(step_index + 1)
                )
            else:
                self._complete_processing()

        run_step(0)

    def _complete_processing(self):
        """Handle processing completion"""
        self.processing_active = False
        self.process_button.configure(state="normal")
        self.progress_section.stop("Processing Complete!")

        # Show completion message
        analysis_type = self.analysis_option.get()
        success_msg = (
            "Airflow simulation and analysis completed successfully!"
            if "Simulation" in analysis_type else
            "Airway segmentation completed successfully!"
        )
        messagebox.showinfo("Success", success_msg)

        # Show results section
        self.results_frame.pack(fill="x", pady=10)

    def _save_results(self):
        """Handle saving results"""
        messagebox.showinfo("Save Results", "Results saved successfully!")

    def _export_reports(self):
        """Handle exporting reports"""
        messagebox.showinfo("Export Reports", "Reports exported successfully!")

    def _visualize_data(self):
        """Handle data visualization"""
        messagebox.showinfo("Visualize Data", "Opening visualization tool...")

    def _create_navigation(self):
        """Create the navigation buttons"""
        NavigationFrame(
            self.app.main_frame,
            previous_label="Review and Confirm",
            next_label="Future Implementation",
            back_command=self.app.create_tab3,
            next_command=lambda: messagebox.showinfo(
                "Info",
                "Further tabs not yet implemented."
            )
        ).pack(fill="x", side="bottom", pady=20)