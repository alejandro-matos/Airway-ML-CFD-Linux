# gui/tabs/tab4.py
import os
import customtkinter as ctk
from tkinter import ttk, messagebox
import time
from ..components.navigation import NavigationFrame
from ..components.progress import ProgressSection
from ..components.forms import FormSection
from ..utils.segmentation import AirwayProcessor
from pathlib import Path
import threading
import sys
from gui.utils.app_logger import AppLogger


class Tab4Manager:
    def __init__(self, app):
        """Initialize Tab4Manager with a reference to the main app"""
        self.app = app
        self.processing_active = False
        self.logger = AppLogger()  # Initialize logger

        # # Redirect standard output (stdout) and errors (stderr) to AppLogger
        # sys.stdout = self.LoggerWriter(self.logger.log_info)
        # sys.stderr = self.LoggerWriter(self.logger.log_error)

        # # Capture Python warnings and log them
        # warnings.showwarning = self._log_warning
        
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
    
    def _create_navigation(self):
        """Create navigation buttons with descriptive labels"""
        self.nav_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        self.nav_frame.pack(fill="x", side="bottom", pady=5)  # Adjust bottom padding

        # Back button and label
        back_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        back_frame.pack(side="left", padx=15)  # Adjust padding for better positioning

        ctk.CTkButton(
            back_frame,
            text="Back",
            command=self.app.create_tab3,  # Navigate back to Tab3
            width=100,
            font=("Times_New_Roman", 16)
        ).pack()

        ctk.CTkLabel(
            back_frame,
            text="Review and Confirm",
            font=("Arial", 12),
            text_color="gray"
        ).pack()

        # Next button and label (Initially hidden)
        self.next_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.next_frame.pack(side="right", padx=15)
        self.next_frame.pack_forget()  # Hide the Next button initially

    
    def _show_next_button(self):
        """Show the Next button and label"""
        self.next_frame.pack(side="right", padx=20)

        ctk.CTkButton(
            self.next_frame,
            text="Next",
            command=self._validate_and_proceed,  # Proceed to the next step
            width=100,
            font=("Times_New_Roman", 16)
        ).pack()

        ctk.CTkLabel(
            self.next_frame,
            text="Further Analysis",
            font=("Arial", 12),
            text_color="gray"
        ).pack()

    def _validate_and_proceed(self):
        """Validate current state and proceed to the next tab"""
        # Add validation logic if necessary
        messagebox.showinfo(
            "Next Tab",
            "This is a placeholder for the next tab. Implementation is pending."
        )

    def _create_main_content(self):
        """Create the main content area with analysis options and processing sections"""
        # Main content frame - this should be transparent too
        content_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))  # Reduce bottom padding

        # Analysis options section
        self._create_analysis_section(content_frame)
        
        # Processing section
        self._create_processing_section(content_frame)
        
        # Results section (initially hidden)
        self.results_frame = self._create_results_section(content_frame)

    def _create_analysis_section(self, parent):
        """Create the analysis options section"""
        analysis_section = FormSection(parent, "Analysis Options", fg_color="transparent")
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
            width=280,
            height=30,
            font=("Arial", 12)
        )
        analysis_dropdown.pack(pady=(5, 10))

        # Processing details label
        self.processing_details_label = ctk.CTkLabel(
            analysis_section.content,
            text="",
            font=("Arial", 12),
            wraplength=280,
            justify="center"
        )
        self.processing_details_label.pack(pady=(0, 10))

    def _create_processing_section(self, parent):
        """Create the processing section with progress bar"""
        processing_section = FormSection(parent, "Processing", fg_color="transparent")
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
        results_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="transparent")
        
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

        # Validate folder path exists
        if not hasattr(self.app, 'full_folder_path'):
            messagebox.showerror("Error", "No output folder specified. Please return to the patient information page and try again.")
            return

        # Show confirmation dialog focused on analysis type
        analysis_type = self.analysis_option.get()
        message = f"Would you like to proceed with {analysis_type}?\n\n"
        
        if "Simulation" in analysis_type:
            message += "This will:\n" \
                    "1. Perform airway segmentation\n" \
                    "2. Generate 3D mesh\n" \
                    "3. Run CFD simulation\n" \
                    "4. Analyze airflow patterns"
        else:
            message += "This will:\n" \
                    "1. Perform airway segmentation\n" \
                    "2. Generate 3D model\n" \
                    "3. Calculate airway volume"
        
        response = messagebox.askquestion(
            "Confirm Analysis",
            message,
            icon="question"
        )
        
        if response == "yes":
            self._start_processing()

    def _start_processing(self):
        """Start the processing sequence"""
        try:
            # Check if DICOM folder is set
            if not hasattr(self.app, 'selected_dicom_folder'):
                messagebox.showerror(
                    "Error",
                    "No DICOM folder selected. Please return to the patient information page and select a DICOM folder."
                )
                return

            # Check if DICOM folder exists
            if not os.path.exists(self.app.selected_dicom_folder):
                messagebox.showerror(
                    "Error",
                    f"Selected DICOM folder does not exist: {self.app.selected_dicom_folder}"
                )
                return

            # Ensure output folder exists
            os.makedirs(self.app.full_folder_path, exist_ok=True)
            
            self.processing_active = True
            self.process_button.configure(state="disabled")
            
            def progress_callback(message, percentage, output_line=None):
                """Update progress bar and message"""
                # Use after() to ensure thread safety when updating GUI
                self.app.after(0, lambda: self.progress_section.update_progress(
                    percentage,
                    message=message,
                    output_line=output_line
                ))
            
            # Initialize processor
            processor = AirwayProcessor(
                input_folder=self.app.selected_dicom_folder,
                output_folder=self.app.full_folder_path,
                callback=progress_callback
            )
            
            # Set up cancel callback
            def cancel_processing():
                """Cancel the processing and stop the progress bar"""
                if processor.cancel_processing():
                    # Ensure the progress bar animation is stopped
                    self.app.after(0, lambda: self.progress_section.stop("Processing Cancelled"))
                    # Reset the processing flag
                    self.processing_active = False
                    # Enable the Start button again
                    self.process_button.configure(state="normal")
                    
            self.progress_section.set_cancel_callback(cancel_processing)
            
            def process_thread():
                try:
                    # Clear previous output
                    self.app.after(0, self.progress_section.clear_output)
                    
                    # Start with indeterminate mode during initialization
                    self.app.after(0, lambda: self.progress_section.start(
                        "Initializing processing...",
                        indeterminate=True
                    ))
                    
                    # Run the processing
                    results = processor.process()
                    
                    # Schedule completion handling in main thread
                    self.app.after(0, lambda: self._handle_processing_completion(True, results))
                    
                except Exception as exc:
                    # Store the exception message for the lambda
                    error_message = str(exc)
                    self.app.after(0, lambda: self._handle_processing_completion(False, error_message))
                
                finally:
                    # Reset cancel callback
                    self.app.after(0, lambda: self.progress_section.set_cancel_callback(None))
            
            # Start processing thread
            thread = threading.Thread(target=process_thread)
            thread.daemon = True  # Thread will be terminated when main program exits
            thread.start()
            
        except Exception as e:
            self.processing_active = False
            self.process_button.configure(state="normal")
            messagebox.showerror("Error", f"Failed to start processing:\n{str(e)}")

    def _handle_processing_completion(self, success, results):
        """Handle completion of processing"""
        self.processing_active = False
        self.process_button.configure(state="normal")

        if success:
            self.progress_section.stop("Processing Complete!")

            # Show success message with results
            message = (
                f"Processing completed successfully!\n\n"
                f"Airway Volume: {results['volume']:.2f} mm³\n\n"
                f"Files created:\n"
                f"- NIfTI: {Path(results['nifti_path']).name}\n"
                f"- Prediction: {Path(results['prediction_path']).name}\n"
                f"- STL: {Path(results['stl_path']).name}"
            )
            messagebox.showinfo("Success", message)

            # Show results section
            self.results_frame.pack(fill="x", pady=10)

            # Show the Next button
            self._show_next_button()

            # If airflow simulation was selected, proceed with CFD
            if self.analysis_option.get() == "Airflow Simulation (includes segmentation)":
                if messagebox.askyesno(
                    "Continue to CFD",
                    "Would you like to proceed with CFD analysis?"
                ):
                    self._start_cfd_simulation(results['stl_path'])
        else:
            messagebox.showerror(
                "Error",
                f"Processing failed:\n{results}"  # Results contain error message in this case
            )

    def _save_results(self):
        """Handle saving results"""
        messagebox.showinfo("Save Results", "Results saved successfully!")

    def _export_reports(self):
        """Handle exporting reports"""
        messagebox.showinfo("Export Reports", "Reports exported successfully!")

    def _visualize_data(self):
        """Handle data visualization"""
        messagebox.showinfo("Visualize Data", "Opening visualization tool...")