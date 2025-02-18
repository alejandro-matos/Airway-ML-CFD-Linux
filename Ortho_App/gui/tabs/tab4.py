# gui/tabs/tab4.py
import os
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk 
from tkinter import ttk, messagebox
import time
from ..components.navigation import NavigationFrame
from ..components.progress import ProgressSection
from ..components.forms import FormSection, ResultsFormSection
from ..utils.segmentation import AirwayProcessor
from pathlib import Path
import threading
import sys
from gui.utils.app_logger import AppLogger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import platform
import subprocess


class Tab4Manager:
    def __init__(self, app):
        """Initialize Tab4Manager with a reference to the main app"""
        self.app = app
        self.processing_active = False
        self.logger = AppLogger()  # Initialize logger
        self.render_images = {}  # Fix: Add this to prevent AttributeError

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
        self.nav_frame.pack(fill="x", side="bottom", pady=5)

        back_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        back_frame.pack(side="left", padx=15)

        ctk.CTkButton(
            back_frame,
            text="Back",
            command=self._confirm_back,  # Use our custom confirmation method
            width=100,
            font=("Times_New_Roman", 16)
        ).pack()

        ctk.CTkLabel(
            back_frame,
            text="Review and Confirm",
            font=("Arial", 12),
            text_color="gray"
        ).pack()

    def _confirm_back(self):
        """Prompt the user for confirmation before going back if analysis data exists."""
        # Check if an analysis is in process or if data exists (e.g., results have been loaded)
        data_present = self.processing_active or bool(self.results_frame.winfo_children())
        if data_present:
            response = messagebox.askyesno(
                "Confirm Navigation",
                "An analysis is in process or has been completed. Going back will erase all data. Are you sure you want to proceed?"
            )
            if response:
                self.app.create_tab3()
        else:
            self.app.create_tab3()


    def _create_main_content(self):
        """Create the main content area with analysis options on the left and results on the right."""
        # Create main content frame using grid layout
        content_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        # Create left and right frames
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        right_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        # Configure grid weights for resizing
        content_frame.grid_columnconfigure(0, weight=1)  # Left frame (Analysis/Processing)
        content_frame.grid_columnconfigure(1, weight=2)  # Right frame (Results)
        content_frame.grid_rowconfigure(0, weight=1)  # Allow vertical expansion

        # Add sections to the left frame
        self._create_analysis_section(left_frame)
        self._create_processing_section(left_frame)

        # Add results section to the right frame
        self.results_frame = self._create_results_section(right_frame)


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
                "Airflow Simulation"
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
        """Create the results section with a Notebook to view different stages."""
        results_section = ResultsFormSection(parent, "Results")
        results_section.pack(fill="both", padx=20, pady=(5, 10), expand=False)

        notebook_frame = results_section.content

        # Configure styles for notebook tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=results_section.content.cget("fg_color"), borderwidth=0)
        style.configure("TNotebook.Tab", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#005f87")], foreground=[("selected", "white")])

        # Create the notebook widget
        self.results_notebook = ttk.Notebook(notebook_frame)
        self.results_notebook.pack(fill="both", expand=False)  # Restrict expansion

        # Create frames for each tab
        self.segmentation_frame = ctk.CTkFrame(self.results_notebook, fg_color=results_section.content.cget("fg_color"))
        self.postprocessing_frame = ctk.CTkFrame(self.results_notebook, fg_color=results_section.content.cget("fg_color"))
        self.cfd_frame = ctk.CTkFrame(self.results_notebook, fg_color=results_section.content.cget("fg_color"))

        self.results_notebook.add(self.segmentation_frame, text="Segmentation")
        self.results_notebook.add(self.postprocessing_frame, text="Post-processed")
        self.results_notebook.add(self.cfd_frame, text="CFD Simulation")
        self.results_notebook.bind("<<NotebookTabChanged>>", self._highlight_active_tab)

        # Create a frame to hold the two buttons side by side
        button_frame = ctk.CTkFrame(results_section, fg_color=results_section.cget("fg_color"))
        button_frame.pack(pady=10)

        # Export button, initially disabled (enabled later when processing completes)
        self.export_button = ctk.CTkButton(
            button_frame,
            text="Export Results as PDF",
            command=self._export_results_to_pdf,
            width=200,
            font=("Arial", 14),
            state="disabled"
        )
        self.export_button.pack(side="left", padx=5)

        # Open Report button, initially disabled
        self.open_report_button = ctk.CTkButton(
            button_frame,
            text="Open Report",
            command=self._open_report,
            width=200,
            font=("Arial", 14),
            state="disabled"
        )
        self.open_report_button.pack(side="left", padx=5)

        return results_section


    
    def _highlight_active_tab(self, event=None):
        """Highlight the active tab in the notebook."""
        # Get the currently selected tab index
        selected_tab_index = self.results_notebook.index(self.results_notebook.select())

        # Configure styles
        style = ttk.Style()
        
        # Reset all tabs to default style
        for i in range(3):  # Assuming 3 tabs (Segmentation, Post-processed, CFD)
            style.configure(f"TNotebook.Tab{i}", background="#d9d9d9", foreground="black")

        # Highlight the selected tab
        style.configure(f"TNotebook.Tab{selected_tab_index}", background="#005f87", foreground="white")



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
                    "2. Generate 3D model (in STL format)\n" \
                    "3. Calculate airway volume in (mm³)"
        
        response = messagebox.askquestion(
            "Confirm Analysis",
            message,
            icon="question"
        )
        
        if response == "yes":
            self._start_processing()

    # def _start_processing(self): # Uncomment for full functionality later tk
    #     """Start the processing sequence"""
    #     try:
    #         # Check if DICOM folder is set
    #         if not hasattr(self.app, 'selected_dicom_folder'):
    #             messagebox.showerror(
    #                 "Error",
    #                 "No DICOM folder selected. Please return to the patient information page and select a DICOM folder."
    #             )
    #             return

    #         # Check if DICOM folder exists
    #         if not os.path.exists(self.app.selected_dicom_folder):
    #             messagebox.showerror(
    #                 "Error",
    #                 f"Selected DICOM folder does not exist: {self.app.selected_dicom_folder}"
    #             )
    #             return

    #         # Ensure output folder exists
    #         os.makedirs(self.app.full_folder_path, exist_ok=True)
            
    #         self.processing_active = True
    #         self.process_button.configure(state="disabled")
            
    #         def progress_callback(message, percentage, output_line=None):
    #             """Update progress bar and message"""
    #             # Use after() to ensure thread safety when updating GUI
    #             self.app.after(0, lambda: self.progress_section.update_progress(
    #                 percentage,
    #                 message=message,
    #                 output_line=output_line
    #             ))
            
    #         # Initialize processor
    #         processor = AirwayProcessor(
    #             input_folder=self.app.selected_dicom_folder,
    #             output_folder=self.app.full_folder_path,
    #             callback=progress_callback
    #         )
            
    #         # Set up cancel callback
    #         def cancel_processing():
    #             """Cancel the processing and stop the progress bar"""
    #             if processor.cancel_processing():
    #                 # Ensure the progress bar animation is stopped
    #                 self.app.after(0, lambda: self.progress_section.stop("Processing Cancelled"))
    #                 # Reset the processing flag
    #                 self.processing_active = False
    #                 # Enable the Start button again
    #                 self.process_button.configure(state="normal")
                    
    #         self.progress_section.set_cancel_callback(cancel_processing)
            
    #         def process_thread():
    #             try:
    #                 # Clear previous output
    #                 self.app.after(0, self.progress_section.clear_output)
                    
    #                 # Start with indeterminate mode during initialization
    #                 self.app.after(0, lambda: self.progress_section.start(
    #                     "Initializing processing...",
    #                     indeterminate=True
    #                 ))
                    
    #                 # Run the processing
    #                 results = processor.process()
                    
    #                 # Schedule completion handling in main thread
    #                 self.app.after(0, lambda: self._handle_processing_completion(True, results))
                    
    #             except Exception as exc:
    #                 # Store the exception message for the lambda
    #                 error_message = str(exc)
    #                 self.app.after(0, lambda: self._handle_processing_completion(False, error_message))
                
    #             finally:
    #                 # Reset cancel callback
    #                 self.app.after(0, lambda: self.progress_section.set_cancel_callback(None))
            
    #         # Start processing thread
    #         thread = threading.Thread(target=process_thread)
    #         thread.daemon = True  # Thread will be terminated when main program exits
    #         thread.start()
            
    #     except Exception as e:
    #         self.processing_active = False
    #         self.process_button.configure(state="normal")
    #         messagebox.showerror("Error", f"Failed to start processing:\n{str(e)}")

    def _start_processing(self):
        """Simulate processing with staged updates, logs, and dynamic UI updates."""
        try:
            self.processing_active = True
            self.process_button.configure(state="disabled")
            self.progress_section.start("Initializing processing...", indeterminate=True)

            analysis_type = self.analysis_option.get()

            # Common steps for all processes
            self.app.after(2000, lambda: self._update_processing_stage(10, "Converting DICOM to NIfTI..."))
            
            # Start displaying log messages
            self.app.after(5000, self._display_log_messages)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process:\n{str(e)}")
            self.processing_active = False
            self.process_button.configure(state="normal")

    def _display_log_messages(self, line_index=0):
        """Display log messages line by line from the prediction log file."""
        log_file_path = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/prediction/pred_log.txt"

        try:
            with open(log_file_path, "r") as log_file:
                lines = log_file.readlines()

            if line_index < len(lines):
                self.progress_section.update_progress(30, "Performing AI-based airway segmentation...", output_line=lines[line_index].strip())
                self.app.after(50, lambda: self._display_log_messages(line_index + 1))  # Schedule next line

            else:
                # Once log file is fully displayed, continue with processing
                self.app.after(500, lambda: self._update_processing_stage(50, "Segmentation completed successfully."))
                self.app.after(3000, lambda: self._update_processing_stage(70, "Converting segmentation into 3D model..."))
                self.app.after(6000, lambda: self._update_processing_stage(85, "Generating 3D visualization..."))
                self.app.after(7000, lambda: self._update_render_display("segmentation", "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/stl/IIB_2019-12-20_pred.png"))

                if "Simulation" in self.analysis_option.get():
                    self.app.after(9000, lambda: self._update_processing_stage(88, "Preparing 3D model for airflow analysis..."))
                    self.app.after(12000, lambda: self._update_processing_stage(92, "Generating computational model preview..."))
                    self.app.after(13000, lambda: self._update_render_display("postprocessing", "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/CFD/IIB_2019-12-20_assem.png"))

                    # **Switch to Post-processed tab after showing model**
                    self.app.after(13050, lambda: self.results_notebook.select(self.postprocessing_frame))

                    self.app.after(15000, lambda: self._update_processing_stage(96, "Running airflow simulation..."))
                    self.app.after(18000, lambda: self._update_processing_stage(100, "Generating airflow simulation results..."))
                    self.app.after(13000, lambda: self._update_render_display("cfd", "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/CFD/IIB_2019-12-20_CFD.png"))
                    self.app.after(20000, self._finalize_processing)
                else:
                    self.app.after(8000, self._finalize_processing)

        except FileNotFoundError:
            messagebox.showerror("Error", f"Log file not found:\n{log_file_path}")
            self.app.after(500, lambda: self._update_processing_stage(50, "Segmentation completed successfully."))




    def _update_processing_stage(self, progress, message):
        """Update progress bar asynchronously."""
        self.progress_section.update_progress(progress, message)

    def _finalize_processing(self):
        """Final step: show preview image after processing."""
        self.progress_section.update_progress(100, "Processing complete!")
        
        # Enable the Export Results button if simulation is complete
        if "Simulation" in self.analysis_option.get():
            self.export_button.configure(state="normal")
            # Explicitly select the CFD tab before finalizing
            self.results_notebook.select(self.cfd_frame)
        
        # Load and display the segmentation preview (if needed)
        preview_path = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/stl/IIB_2019-12-20_pred.png"
        if not os.path.exists(preview_path):
            messagebox.showerror("Error", f"Segmentation preview not found at:\n{preview_path}")
            return

        self._handle_processing_completion(True, {'preview_path': preview_path})




    def _update_render_display(self, stage, image_path, placeholder=False):
        """
        Update the display in the notebook tab corresponding to the given stage.
        
        stage: a string "segmentation", "postprocessing", or "cfd"
        image_path: path to the image file to load (if None and placeholder is False, do nothing)
        placeholder: if True, display a default message
        """
        # Choose the frame based on stage
        frame = None
        if stage == "segmentation":
            frame = self.segmentation_frame
        elif stage == "postprocessing":
            frame = self.postprocessing_frame
            self.results_notebook.select(self.postprocessing_frame)
            self._highlight_active_tab()  
        elif stage == "cfd":
            frame = self.cfd_frame
            self.results_notebook.select(self.cfd_frame)
            self._highlight_active_tab()
        else:
            return

        # Clear previous content in the frame
        for widget in frame.winfo_children():
            widget.destroy()

        if placeholder or image_path is None:
            # Display a simple placeholder message
            ctk.CTkLabel(frame, text=f"{stage.capitalize()} render will appear here.", font=("Arial", 12)).pack(expand=True)
        else:
            try:
                # Open the image using PIL
                pil_image = Image.open(image_path)

                # Get original dimensions
                orig_width, orig_height = pil_image.size

                # Set a fixed width and calculate height to maintain aspect ratio
                max_width = 400  # Change this as needed
                aspect_ratio = orig_height / orig_width
                new_height = int(max_width * aspect_ratio)

                # Resize while keeping aspect ratio
                pil_image = pil_image.resize((max_width, new_height), Image.LANCZOS)

                # Convert to CTkImage
                ctk_image = ctk.CTkImage(light_image=pil_image, size=(max_width, new_height))

                # Store reference to avoid garbage collection
                self.render_images[stage] = ctk_image

                # Create and pack the label
                label = ctk.CTkLabel(frame, image=ctk_image, text="")
                label.pack(expand=True, pady=10)

            except Exception as e:
                ctk.CTkLabel(frame, text=f"Error loading image: {e}", font=("Arial", 12)).pack(expand=True)

    # def _handle_processing_completion(self, success, results):  # Uncomment for full functionality tk
    #     """Handle completion of processing"""
    #     self.processing_active = False
    #     self.process_button.configure(state="normal")

    #     if success:
    #         self.progress_section.stop("Processing Complete!")

    #         # Show success message with results

    #         message = (
    #             f"Processing completed successfully!\n\n"
    #             f"Airway Volume: {results['volume']:.2f} mm³\n\n"
    #             f"Files created:\n"
    #             f"- NIfTI: {Path(results['nifti_path']).name}\n"
    #             f"- Prediction: {Path(results['prediction_path']).name}\n"
    #             f"- STL: {Path(results['stl_path']).name}"
    #         )
    #         messagebox.showinfo("Success", message)

    #         # Show results section
    #         self.results_frame.pack(fill="x", pady=10)

    #         # Show render in display
    #         if os.path.exists(results['preview_path']):
    #             self._display_segmentation_image(results['preview_path'])

    #         # Show the Next button
    #         self._show_next_button()

    #         # If airflow simulation was selected, proceed with CFD
    #         if self.analysis_option.get() == "Airflow Simulation (includes segmentation)":
    #             if messagebox.askyesno(
    #                 "Continue to CFD",
    #                 "Would you like to proceed with CFD analysis?"
    #             ):
    #                 self._start_cfd_simulation(results['stl_path'])
                
    #             # Still need to properly place these so they appear as the things work
    #             self._update_render_display("postprocessing", "path/to/postprocessing_preview.png")
    #             self._update_render_display("cfd", "path/to/cfd_preview.png")
    #     else:
    #         messagebox.showerror(
    #             "Error",
    #             f"Processing failed:\n{results}"  # Results contain error message in this case
    #         )

    def _handle_processing_completion(self, success, results):
        """Directly handle displaying the pre-existing STL preview."""
        self.processing_active = False
        self.process_button.configure(state="normal")

        if success:
            self.progress_section.stop("Processing Complete!")

            # Ensure Results section fully expands
            self.results_frame.pack(fill="both", expand=True, pady=(5, 5))  # Reduce padding

            # Display segmentation preview image
            preview_path = results.get('preview_path')
            if preview_path and os.path.exists(preview_path):
                self._display_segmentation_image(preview_path)
            else:
                messagebox.showerror("Error", "Segmentation preview image not found!")
                
        else:
            messagebox.showerror("Error", "Processing failed. Could not load segmentation preview.")

    def _display_segmentation_image(self, image_path):
        """
        Display the segmentation preview image in the GUI instead of rendering in VTK.
        """
        # Clear previous image if any
        for widget in self.segmentation_frame.winfo_children():
            widget.destroy()

        try:
            # Open image using PIL
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((400, 300), Image.LANCZOS)

            # Convert to CTkImage
            ctk_image = ctk.CTkImage(light_image=pil_image, size=(400, 300))  # Use CTkImage
            
            # Store reference to avoid garbage collection
            self.render_images["segmentation"] = ctk_image

            # Create and pack the label
            label = ctk.CTkLabel(self.segmentation_frame, image=ctk_image, text="")
            label.pack(expand=True, pady=10, fill="both")

        except Exception as e:
            ctk.CTkLabel(self.segmentation_frame, text=f"Error loading image: {e}", font=("Arial", 12)).pack(expand=True)

    
    def _export_results_to_pdf(self):
        """Generate and save a PDF report of the results with enhanced formatting."""
        pdf_path = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/exported_results.pdf"

        try:
            # Create PDF canvas with letter page size
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            c.setTitle("Upper Airway Analysis Report")

            # Title Section
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(width / 2, height - 50, "Upper Airway Analysis Report")
            c.line(50, height - 60, width - 50, height - 60)

            # Header with Analysis Type and Date
            c.setFont("Helvetica", 12)
            analysis_text = f"Analysis Type: {self.analysis_option.get()}"
            date_text = "Processing Date: " + time.strftime("%Y-%m-%d %H:%M:%S")
            c.drawString(50, height - 80, analysis_text)
            c.drawRightString(width - 50, height - 80, date_text)

            # Section: Quantitative Measurements
            y_position = height - 110
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "Quantitative Measurements:")
            c.setFont("Helvetica", 12)
            airway_volume = getattr(self, "airway_volume", "13990.01 mm³")
            c.drawString(70, y_position - 20, f"Airway Volume: {airway_volume} cm³")

            # Section: Airflow Simulation Summary
            y_position -= 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "Airflow Simulation Summary:")
            c.setFont("Helvetica", 12)
            # airflow_summary = getattr(self, "airflow_summary", "Summary not available.") # Uncomment when adding full functionality tk
            # c.drawString(70, y_position - 20, airflow_summary)

            # # Section: Simulation Initial Conditions
            # y_position -= 50
            # c.setFont("Helvetica-Bold", 12)
            # c.drawString(50, y_position, "Simulation Initial Conditions:")
            # c.setFont("Helvetica", 12)

            # Define and print initial conditions
            initial_conditions = [
                "Density (ρ): 1.122 kg/m³",
                "Kinematic viscosity (ν): 1.539 x 10^-5 m²/s",
                "Initial velocity: 1 m/s",
                "Flow type: Laminar (Slow and steady, no turbulence)"
            ]
            y_position -= 20
            for condition in initial_conditions:
                c.drawString(70, y_position-10, condition)
                y_position -= 15

            # Note the simulation software version
            c.setFont("Helvetica", 12)
            c.drawString(70, y_position - 30, "Simulation performed using OpenFoam v2306.")

            # Move y_position for images (reduce excessive spacing)
            y_position -= 40

            # Add segmentation images side by side
            segmentation_img = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/stl/IIB_2019-12-20_pred.png"
            processed_img = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/stl/IIB_2019-12-20_assem.png"

            if os.path.exists(segmentation_img) and os.path.exists(processed_img):
                c.drawImage(segmentation_img, 50, y_position - 140, width=200, height=120)
                c.drawImage(processed_img, 300, y_position - 140, width=200, height=120)

                c.setFont("Helvetica-Oblique", 10)
                c.drawCentredString(50 + 100, y_position - 150, "Figure 1: Initial Segmentation")
                c.drawCentredString(300 + 100, y_position - 150, "Figure 2: Processed Segmentation")
            else:
                c.drawString(50, y_position - 30, "Segmentation images not found.")

            # Adjust y_position after segmentation images
            y_position -= 170

            # CFD Simulation Results
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "CFD Simulation Results:")
            y_position -= 15
            c.setFont("Helvetica", 12)
            c.drawString(50, y_position, "Airflow velocity and pressure contours with a scale bar are shown below.")
            y_position -= 10

            # Add CFD Simulation Image
            cfd_img = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/CFD/IIB_2019-12-20_CFD.png"
            if os.path.exists(cfd_img):
                c.drawImage(cfd_img, 175, y_position - 300, width=200, height=300)
                c.setFont("Helvetica-Oblique", 10)
                c.drawCentredString(100 + 150, y_position - 310, "Figure 3: CFD Simulation Contour Plot")
            else:
                c.drawString(50, y_position - 30, "CFD simulation image not found.")

            # Save the PDF
            c.save()
            messagebox.showinfo("Export Complete", f"Results saved to:\n{pdf_path}")

            # Enable the Open Report button
            self.open_report_button.configure(state="normal")
            
            # Optionally, store pdf_path for use when opening the file
            self.report_pdf_path = pdf_path

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF:\n{str(e)}")

    def _open_report(self):
        """Open the exported PDF report."""
        if hasattr(self, "report_pdf_path") and os.path.exists(self.report_pdf_path):
            if platform.system() == "Windows":
                os.startfile(self.report_pdf_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", self.report_pdf_path])
            else:  # Linux and other
                subprocess.call(["xdg-open", self.report_pdf_path])
        else:
            messagebox.showerror("Error", "Report file not found.")

