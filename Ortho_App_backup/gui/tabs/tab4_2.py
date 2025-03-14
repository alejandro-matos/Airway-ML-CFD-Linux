# gui/tabs/tab4.py
import os
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
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
import threading
import open3d as o3d
from config.settings import UI_SETTINGS


class Tab4Manager:
    def __init__(self, app):
        """Initialize Tab4Manager with a reference to the main app"""
        self.app = app
        self.processing_active = False
        self.logger = AppLogger()  # Initialize logger
        self.render_images = {}  # Fix: Add this to prevent AttributeError

        # Add a cancellation flag that threads can check
        self.cancel_requested = False
        # Keep track of processing thread
        self.processing_thread = None

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
            width=120,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
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
        analysis_section = FormSection(parent, "Analysis Options", fg_color="transparent", font=UI_SETTINGS["FONTS"]["HEADER"])
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
            width=300,
            height=30,
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        )
        analysis_dropdown.pack(pady=(5, 10))

        # Processing details label
        self.processing_details_label = ctk.CTkLabel(
            analysis_section.content,
            text="",
            font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
            wraplength=280,
            justify="center"
        )
        self.processing_details_label.pack(pady=(0, 10))

    def _create_processing_section(self, parent):
        """Create the processing section with progress bar"""
        processing_section = FormSection(parent, "Processing", fg_color="transparent", font=UI_SETTINGS["FONTS"]["HEADER"])
        processing_section.pack(fill="x", pady=10)

        # Start button
        self.process_button = ctk.CTkButton(
            processing_section.content,
            text="Start Processing",
            command=self._validate_and_start_processing,
            width=300,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"]
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

        # Create a container for the notebook with fixed dimensions if desired
        notebook_container = ctk.CTkFrame(notebook_frame, width=700, height=500,
                                        fg_color=results_section.content.cget("fg_color"))
        notebook_container.pack(pady=10)
        notebook_container.pack_propagate(False)  # Prevent automatic resizing

        # Configure ttk style before creating the notebook
        style = ttk.Style()
        
        # Configure the tab font (common for all tabs)
        style.configure('TNotebook.Tab', font=UI_SETTINGS["FONTS"]["NORMAL"])

        # Create the notebook widget inside the container
        self.results_notebook = ttk.Notebook(notebook_container)
        self.results_notebook.pack(fill="both", expand=True)

        # Create frames for each tab
        self.segmentation_frame = ctk.CTkFrame(self.results_notebook,
                                                fg_color=results_section.content.cget("fg_color"))
        self.postprocessing_frame = ctk.CTkFrame(self.results_notebook,
                                                fg_color=results_section.content.cget("fg_color"))
        self.cfd_frame = ctk.CTkFrame(self.results_notebook,
                                    fg_color=results_section.content.cget("fg_color"))

        self.results_notebook.add(self.segmentation_frame, text="Segmentation")
        self.results_notebook.add(self.postprocessing_frame, text="Post-processed")
        self.results_notebook.add(self.cfd_frame, text="CFD Simulation")
        self.results_notebook.bind("<<NotebookTabChanged>>", self._highlight_active_tab)

        # Update highlight method to preserve font configuration
        self._configure_tab_styles()

        # Create a frame for the buttons along the right side
        button_frame = ctk.CTkFrame(results_section, fg_color=results_section.cget("fg_color"))
        button_frame.pack(side="right", padx=20, pady=10)  # Changed from center to right side

        # Export button (now Save Report), initially disabled
        self.export_button = ctk.CTkButton(
            button_frame,
            text="Save Report as PDF",  # Renamed from "Export Results as PDF"
            command=self._export_results_to_pdf,
            width=200,
            height=40,  # Made slightly taller for better proportion
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],  # Using standard button color
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            state="disabled"
        )
        self.export_button.pack(pady=(0, 10))  # Add padding between buttons

        # Open Report button, initially disabled
        self.open_report_button = ctk.CTkButton(
            button_frame,
            text="Open Report",
            command=self._open_report,
            width=200,
            height=40,  # Made slightly taller for better proportion
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],  # Using standard button color
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            state="disabled"
        )
        self.open_report_button.pack()
        
        # --- In the Segmentation tab, create a container for both the image and the button ---
        self.segmentation_container = ctk.CTkFrame(self.segmentation_frame,
                                                fg_color=self.segmentation_frame.cget("fg_color"))
        self.segmentation_container.pack(fill="both", expand=True)
        # Frame for the segmentation image (take most vertical space)
        self.segmentation_image_frame = ctk.CTkFrame(self.segmentation_container,
                                                    fg_color=self.segmentation_container.cget("fg_color"))
        self.segmentation_image_frame.pack(fill="x", side="top", pady=(0, 5))
        # Frame for the STL button (fixed height)
        self.stl_button_frame = ctk.CTkFrame(self.segmentation_container,
                                            fg_color=self.segmentation_container.cget("fg_color"),
                                            height=50)
        self.stl_button_frame.pack(fill="x", side="bottom", pady=(5, 10))
        self.stl_button_frame.pack_propagate(False)  # Prevent resizing to its content

        return results_section
    
    def _create_emoji_icon(self, emoji, size=(20, 20)):
        """Create an icon with an emoji character."""
        # Create a blank image with transparent background
        img = Image.new('RGBA', (size[0]*2, size[1]*2), (255, 255, 255, 0))
        
        # Create ImageDraw object
        draw = ImageDraw.Draw(img)
        
        # Calculate font size based on image size
        font_size = min(size) * 1.5
        
        try:
            # Try to use a system font that supports emoji
            # Common fonts with emoji support
            font_options = [
                "segoeui.ttf",        # Windows
                "AppleColorEmoji.ttf", # macOS
                "NotoColorEmoji.ttf",  # Linux
                "arial.ttf",           # Fallback
            ]
            
            font = None
            for font_name in font_options:
                try:
                    font = ImageFont.truetype(font_name, int(font_size))
                    break
                except IOError:
                    continue
                    
            if font is None:
                font = ImageFont.load_default()
        except Exception:
            # Last resort: default font
            font = ImageFont.load_default()
        
        # Calculate text position to center it
        # Handle different PIL versions with try/except
        try:
            w, h = draw.textsize(emoji, font=font)
        except AttributeError:
            # For newer PIL versions
            w, h = font.getsize(emoji) if hasattr(font, 'getsize') else (size[0], size[1])
        
        position = ((size[0]*2 - w)//2, (size[1]*2 - h)//2)
        
        # Draw the emoji text
        draw.text(position, emoji, fill=(0, 0, 0, 255), font=font)
        
        # Resize to desired dimensions
        img = img.resize(size, Image.LANCZOS)
        
        # Convert to CTkImage
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        return ctk_img

    def _configure_tab_styles(self):
        """Configure the tab styles with consistent font size."""
        style = ttk.Style()
        
        # Define common font settings
        tab_font = UI_SETTINGS["FONTS"]["NORMAL"]  # Adjust size as needed (was previously configured inline)
        
        # Set the base style for all tabs
        style.configure('TNotebook.Tab', font=tab_font)
        
        # Configure individual tab styles with the same font but different colors
        for i in range(3):  # For the three tabs
            style.configure(f"TNotebook.Tab{i}", font=tab_font, background="#d9d9d9", foreground="black")
    
    def _highlight_active_tab(self, event=None):
        """Highlight the active tab in the notebook while preserving font settings."""
        # Get the currently selected tab index
        selected_tab_index = self.results_notebook.index(self.results_notebook.select())

        # Configure styles
        style = ttk.Style()
        tab_font = UI_SETTINGS["FONTS"]["NORMAL"]  # Keep the same font size
        
        # Reset all tabs to default style, preserving font
        for i in range(3):  # Assuming 3 tabs (Segmentation, Post-processed, CFD)
            style.configure(f"TNotebook.Tab{i}", font=tab_font, background="#d9d9d9", foreground="black")

        # Highlight the selected tab, preserving font
        style.configure(f"TNotebook.Tab{selected_tab_index}", font=tab_font, 
                    background="#005f87", foreground="white")



    def _update_processing_details(self, choice):
        """Update the processing details based on selected analysis type"""
        details = {
            "Upper Airway Segmentation": 
                "This will perform automatic segmentation of the upper airway "
                "from the DICOM images.",
            
            "Airflow Simulation":
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
                    "2. Calculate airway volume in (mm³)" \
                    "3. Generate 3D mesh\n" \
                    "4. Run CFD simulation\n" \
                    "5. Analyze airflow patterns"
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
            
            # Set up cancel callback before starting the progress bar
            def cancel_processing():
                """Cancel the processing and stop the progress bar"""
                # Set flag to indicate processing is cancelled
                self.processing_active = False
                # Enable the Start button again
                self.process_button.configure(state="normal")
                # Stop the progress bar
                self.progress_section.stop("Processing Cancelled")
                # Clear any scheduled updates
                for after_id in self.scheduled_updates:
                    self.app.after_cancel(after_id)
                self.scheduled_updates = []
                    
            # Initialize list to track scheduled updates
            self.scheduled_updates = []
            
            # Set the cancel callback
            self.progress_section.set_cancel_callback(cancel_processing)
            
            # Start the progress bar with indeterminate mode
            self.progress_section.start("Initializing processing...", indeterminate=True)

            analysis_type = self.analysis_option.get()

            # Schedule all update steps and track their IDs
            self.scheduled_updates.append(
                self.app.after(2000, lambda: self._update_processing_stage(10, "Converting DICOM to NIfTI..."))
            )
            
            # Start displaying log messages
            self.scheduled_updates.append(
                self.app.after(5000, self._display_log_messages)
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process:\n{str(e)}")
            self.processing_active = False
            self.process_button.configure(state="normal")

    def _display_log_messages(self, line_index=0):
        """Display log messages line by line from the prediction log file."""
        # Check cancellation flag before proceeding
        if self.cancel_requested:
            self.logger.log_info("Log display cancelled")
            return
            
        # log_file_path = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/prediction/pred_log.txt" # linux path tk
        log_file_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\prediction\pred_log.txt"

        try:
            # with open(log_file_path, "r") as log_file:  # Works with linux tk
            #     lines = log_file.readlines()
            with open(log_file_path, "r", encoding="utf-8", errors="replace") as log_file:  # To work with Windows
                lines = log_file.readlines()

            if line_index < len(lines) and not self.cancel_requested:
                # First, ensure the output text in progress_section has larger font
                if line_index == 0:
                    # Only update the font once at the beginning of log display
                    self.app.after(0, lambda: self.progress_section.output_text.configure(
                        font=UI_SETTINGS["FONTS"]["SMALL"] 
                    ))
                
                self.progress_section.update_progress(
                    30, 
                    "Performing AI-based airway segmentation...", 
                    output_line=lines[line_index].strip()
                )
                
                # Check cancellation again before scheduling next update
                if not self.cancel_requested:
                    self.app.after(25, lambda: self._display_log_messages(line_index + 1))  # Schedule next line tk

            elif not self.cancel_requested:
                # Once log file is fully displayed and no cancellation requested, continue with processing
                self._schedule_processing_steps()
            
        except FileNotFoundError:
            if not self.cancel_requested:
                messagebox.showerror("Error", f"Log file not found:\n{log_file_path}")
                self.app.after(500, lambda: self._update_processing_stage(50, "Segmentation completed successfully."))
    
    def _schedule_processing_steps(self):
        """Schedule the remaining processing steps if not cancelled"""
        if self.cancel_requested:
            return
            
        # Clear any previously scheduled updates
        for after_id in self.scheduled_updates:
            self.app.after_cancel(after_id)
        self.scheduled_updates = []
        
        # Schedule new processing steps that check cancellation
        self.scheduled_updates.append(
            self.app.after(500, lambda: self._update_processing_stage_if_not_cancelled(
                50, "Segmentation completed successfully."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(3000, lambda: self._update_processing_stage_if_not_cancelled(
                70, "Converting segmentation into 3D model..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(3000, lambda: self._update_processing_stage_if_not_cancelled(
                85, "Generating 3D visualization..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(7000, lambda: self._update_render_display_if_not_cancelled(
                "segmentation",
                r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\IIB_2019-12-20_pred.png"
            ))
        )

        if "Simulation" in self.analysis_option.get():
            self._schedule_simulation_steps()
        else:
            self.scheduled_updates.append(
                self.app.after(8000, self._finalize_processing_if_not_cancelled)
            )
    
    def _schedule_simulation_steps(self):
        """Schedule simulation-specific processing steps"""
        if self.cancel_requested:
            return
            
        self.scheduled_updates.append(
            self.app.after(9000, lambda: self._update_processing_stage_if_not_cancelled(
                88, "Preparing 3D model for airflow analysis..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(12000, lambda: self._update_processing_stage_if_not_cancelled(
                92, "Generating computational model preview..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(13000, lambda: self._update_render_display_if_not_cancelled(
                "postprocessing",
                r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\IIB_2019-12-20_assem.png"
            ))
        )

        # Switch to Post-processed tab after showing model if not cancelled
        self.scheduled_updates.append(
            self.app.after(13050, lambda: self._select_tab_if_not_cancelled(self.postprocessing_frame))
        )

        self.scheduled_updates.append(
            self.app.after(15000, lambda: self._update_processing_stage_if_not_cancelled(
                96, "Running airflow simulation..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(18000, lambda: self._update_processing_stage_if_not_cancelled(
                100, "Generating airflow simulation results..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(13000, lambda: self._update_render_display_if_not_cancelled(
                "cfd",
                r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\IIB_2019-12-20_CFD.png"
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(20000, self._finalize_processing_if_not_cancelled)
        )
    
    # Helper methods that check cancellation flag
    
    def _update_processing_stage_if_not_cancelled(self, progress, message):
        """Update processing stage only if cancellation wasn't requested"""
        if not self.cancel_requested:
            self._update_processing_stage(progress, message)
    
    def _update_render_display_if_not_cancelled(self, stage, image_path):
        """Update render display only if cancellation wasn't requested"""
        if not self.cancel_requested:
            self._update_render_display(stage, image_path)
    
    def _select_tab_if_not_cancelled(self, tab_frame):
        """Select a tab only if cancellation wasn't requested"""
        if not self.cancel_requested:
            self.results_notebook.select(tab_frame)
            self._highlight_active_tab()
    
    def _finalize_processing_if_not_cancelled(self):
        """Finalize processing only if cancellation wasn't requested"""
        if not self.cancel_requested:
            self._finalize_processing()

    def _update_processing_stage(self, progress, message):
        """Update progress bar asynchronously with larger font for messages."""
        # Configure the progress label with a larger font before updating
        self.app.after(0, lambda: self.progress_section.progress_label.configure(
            font=UI_SETTINGS["FONTS"]["NORMAL"],  # Larger, bold font for better visibility
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]  # Optional: Use a primary color if defined
        ))
        
        # Then update the progress with the message
        self.progress_section.update_progress(progress, message)

    def _finalize_processing(self):
        """Final step: show preview image after processing."""
        self.processing_active = False
        self.process_button.configure(state="normal")
        
        # Always stop the progress bar properly
        self.progress_section.stop("Processing complete!")
        
        # Enable the Export Results button if simulation is complete
        if "Simulation" in self.analysis_option.get():
            self.export_button.configure(state="normal")
            
            # For simulation, make sure all tabs have proper content
            # 1. Segmentation tab (already handled elsewhere)
            segmentation_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\IIB_2019-12-20_pred.png"
            
            # 2. Post-processed tab
            postprocessed_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\IIB_2019-12-20_assem.png"
            
            # 3. CFD tab
            cfd_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\IIB_2019-12-20_CFD.png"
            
            # Update all tabs with their respective images
            self._display_segmentation_image(segmentation_path)
            self._update_postprocessed_display(postprocessed_path)
            self._update_render_display("cfd", cfd_path)
            
            # Explicitly select the CFD tab before finalizing as it's the final result
            self.results_notebook.select(self.cfd_frame)
        else:
            # For segmentation only, just update the segmentation tab
            preview_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\IIB_2019-12-20_pred.png"
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
                max_width = 600  # Change this as needed
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
                # The display_stl button is now created inside _display_segmentation_image
                # No need to reference it here
            else:
                messagebox.showerror("Error", "Segmentation preview image not found!")
        else:
            messagebox.showerror("Error", "Processing failed. Could not load segmentation preview.")


    def _display_segmentation_image(self, image_path):
        """
        Display the segmentation preview image in the segmentation frame.
        Ensures the container exists before attempting to display content.
        """
        # First, make sure segmentation_frame exists
        if not hasattr(self, 'segmentation_frame') or not self.segmentation_frame.winfo_exists():
            return
            
        # Clear existing widgets in the segmentation frame
        for widget in self.segmentation_frame.winfo_children():
            widget.destroy()
        
        # Create container frame if it doesn't exist or was destroyed
        self.segmentation_container = ctk.CTkFrame(
            self.segmentation_frame,
            fg_color=self.segmentation_frame.cget("fg_color")
        )
        self.segmentation_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create image frame within container
        self.segmentation_image_frame = ctk.CTkFrame(
            self.segmentation_container,
            fg_color=self.segmentation_container.cget("fg_color")
        )
        self.segmentation_image_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create button frame within container
        self.stl_button_frame = ctk.CTkFrame(
            self.segmentation_container,
            fg_color=self.segmentation_container.cget("fg_color"),
            height=50
        )
        self.stl_button_frame.pack(fill="x", side="bottom", pady=10)
        self.stl_button_frame.pack_propagate(False)  # Prevent resizing
        
        try:
            # Load and display image
            pil_image = Image.open(image_path)
            
            # Set a fixed width and calculate height to maintain aspect ratio
            max_width = 400
            orig_width, orig_height = pil_image.size
            aspect_ratio = orig_height / orig_width
            new_height = int(max_width * aspect_ratio)
            
            # Resize while keeping aspect ratio
            pil_image = pil_image.resize((max_width, new_height), Image.LANCZOS)
            
            # Convert to CTkImage
            ctk_image = ctk.CTkImage(light_image=pil_image, size=(max_width, new_height))
            
            # Store reference to avoid garbage collection
            self.render_images["segmentation"] = ctk_image
            
            # Create and pack image label
            label = ctk.CTkLabel(self.segmentation_image_frame, image=ctk_image, text="")
            label.pack(expand=True, pady=10)
            
        except Exception as e:
            error_msg = f"Error loading image: {str(e)}"
            ctk.CTkLabel(
                self.segmentation_image_frame, 
                text=error_msg,
                font=("Arial", 12)
            ).pack(expand=True)
            self.logger.log_error(error_msg)

        # Create STL button
        self.display_stl = ctk.CTkButton(
            self.stl_button_frame,
            text="🔄 Open Airway Prediction Model in 3D Viewer",
            command=lambda: self._display_interactive_stl(
                r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\P5T1.stl"),
            width=300,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        self.display_stl.pack(pady=5)

    def _update_postprocessed_display(self, image_path):
        """
        Display the post-processed model image and add a button to view the
        inlet, outlet, and wall components interactively.
        """
        # First, make sure postprocessing_frame exists
        if not hasattr(self, 'postprocessing_frame') or not self.postprocessing_frame.winfo_exists():
            return
            
        # Clear existing widgets in the postprocessing frame
        for widget in self.postprocessing_frame.winfo_children():
            widget.destroy()
        
        # Create container frame
        postprocessed_container = ctk.CTkFrame(
            self.postprocessing_frame,
            fg_color=self.postprocessing_frame.cget("fg_color")
        )
        postprocessed_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create image frame within container
        postprocessed_image_frame = ctk.CTkFrame(
            postprocessed_container,
            fg_color=postprocessed_container.cget("fg_color")
        )
        postprocessed_image_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create button frame within container
        components_button_frame = ctk.CTkFrame(
            postprocessed_container,
            fg_color=postprocessed_container.cget("fg_color"),
            height=50
        )
        components_button_frame.pack(fill="x", side="bottom", pady=10)
        components_button_frame.pack_propagate(False)  # Prevent resizing
        
        try:
            # Load and display image
            pil_image = Image.open(image_path)
            
            # Set a fixed width and calculate height to maintain aspect ratio
            max_width = 400
            orig_width, orig_height = pil_image.size
            aspect_ratio = orig_height / orig_width
            new_height = int(max_width * aspect_ratio)
            
            # Resize while keeping aspect ratio
            pil_image = pil_image.resize((max_width, new_height), Image.LANCZOS)
            
            # Convert to CTkImage
            ctk_image = ctk.CTkImage(light_image=pil_image, size=(max_width, new_height))
            
            # Store reference to avoid garbage collection
            self.render_images["postprocessed"] = ctk_image
            
            # Create and pack image label
            label = ctk.CTkLabel(postprocessed_image_frame, image=ctk_image, text="")
            label.pack(expand=True, pady=10)
            
            # Add a label explaining what's shown
            ctk.CTkLabel(
                postprocessed_image_frame,
                text="Post-processed model with inlet (green), and outlet (red) components",
                font=("Arial", 11),
                text_color="gray"
            ).pack(pady=(0, 5))
            
        except Exception as e:
            error_msg = f"Error loading image: {str(e)}"
            ctk.CTkLabel(
                postprocessed_image_frame, 
                text=error_msg,
                font=("Arial", 12)
            ).pack(expand=True)
            self.logger.log_error(error_msg)

        # Create view components button
        self.view_components_button = ctk.CTkButton(
            components_button_frame,
            text="🔄 Open Model with Processed Boundaries in 3D Viewer",
            command=self._display_interactive_components,
            width=300,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        self.view_components_button.pack(pady=5)

    def _display_interactive_components(self):
        """
        Launch an interactive viewer for the inlet, outlet, and wall components
        with color coding.
        """
        try:
            def view_components():
                # Base path for components
                base_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl"
                
                # Load inlet (green)
                inlet_path = os.path.join(base_path, "inlet.stl")
                inlet_mesh = o3d.io.read_triangle_mesh(inlet_path)
                inlet_mesh.compute_vertex_normals()
                inlet_mesh.paint_uniform_color([0, 1, 0])  # Green
                
                # Load outlet (red)
                outlet_path = os.path.join(base_path, "outlet.stl")
                outlet_mesh = o3d.io.read_triangle_mesh(outlet_path)
                outlet_mesh.compute_vertex_normals()
                outlet_mesh.paint_uniform_color([1, 0, 0])  # Red
                
                # Load wall (gray)
                wall_path = os.path.join(base_path, "wall.stl")
                wall_mesh = o3d.io.read_triangle_mesh(wall_path)
                wall_mesh.compute_vertex_normals()
                wall_mesh.paint_uniform_color([0.7, 0.7, 0.7])  # Gray
                
                # Create visualization window with title
                vis = o3d.visualization.Visualizer()
                vis.create_window(window_name="Airway Components Viewer", width=800, height=600)
                
                # Add all geometries
                vis.add_geometry(inlet_mesh)
                vis.add_geometry(outlet_mesh)
                vis.add_geometry(wall_mesh)
                
                # Set rendering options
                render_option = vis.get_render_option()
                render_option.background_color = [1, 1, 1]  # White background
                render_option.point_size = 1.0
                render_option.show_coordinate_frame = False
                
                # Set view control for better initial view
                view_control = vis.get_view_control()
                view_control.set_zoom(0.8)
                
                # Add text explaining the color coding
                vis.run()
                vis.destroy_window()
            
            # Start in a separate thread
            threading.Thread(target=view_components, daemon=True).start()
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to display component viewer:\n{e}")

    def _display_interactive_stl(self, stl_path):   # Previous method when I only had prediction STL tk
        """
        Launch an interactive STL viewer for the given STL file
        """
        try:
            def view_mesh():
                # Load the STL file
                mesh = o3d.io.read_triangle_mesh(stl_path)
                mesh.compute_vertex_normals()

                # Create a Visualizer instance
                vis = o3d.visualization.Visualizer()
                vis.create_window(window_name="Interactive STL Viewer", width=800, height=600)
                vis.add_geometry(mesh)

                # Optionally, adjust render options:
                render_option = vis.get_render_option()
                render_option.mesh_show_wireframe = False  # Disable wireframe
                render_option.background_color = [1, 1, 1]   # White background
                render_option.show_coordinate_frame = False

                # Run the visualizer and then destroy the window when done
                vis.run()
                vis.destroy_window()

            # Start the viewer in a daemon thread so it doesn't block the main GUI.
            threading.Thread(target=view_mesh, daemon=True).start()
        
            def view_mesh2():
                inlet_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\inlet.stl"
                inlet_mesh = o3d.io.read_triangle_mesh(inlet_path)
                inlet_mesh.compute_vertex_normals()
                inlet_mesh.paint_uniform_color([0, 1, 0])  # Green

                outlet_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\outlet.stl"
                outlet_mesh = o3d.io.read_triangle_mesh(outlet_path)
                outlet_mesh.compute_vertex_normals()
                outlet_mesh.paint_uniform_color([1, 0, 0])  # Red

                wall_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\wall.stl"
                wall_mesh = o3d.io.read_triangle_mesh(wall_path)
                wall_mesh.compute_vertex_normals()
                wall_mesh.paint_uniform_color([0.7, 0.7, 0.7])  # Gray

                o3d.visualization.draw_geometries([inlet_mesh, outlet_mesh,wall_mesh])

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to display interactive STL viewer:\n{e}")
    
    def _export_results_to_pdf(self):
        """Save the report as a PDF file with a specific location."""
        # Default PDF path
        pdf_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\exported_results.pdf"
        
        try:
            # Generate and save the report
            if self._generate_report(pdf_path, show_confirmation=True):
                # Enable the Open Report button if it isn't already
                if self.open_report_button.cget("state") == "disabled":
                    self.open_report_button.configure(state="normal")
        except Exception:
            # Error is already handled in _generate_report
            pass

    def _open_report(self):
        """Open the report, generating it on-the-fly if it doesn't exist yet."""
        default_report_path = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\exported_results.pdf"
        
        # Check if report exists (either from previous export or as default)
        report_exists = hasattr(self, "report_pdf_path") and os.path.exists(self.report_pdf_path)
        
        if not report_exists:
            # If analysis has been completed but report not saved, generate it first
            if self.processing_active is False and self.results_frame.winfo_children():
                # Generate report on-the-fly without showing confirmation message
                try:
                    self._generate_report(default_report_path, show_confirmation=False)
                    self.report_pdf_path = default_report_path
                    report_exists = True
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to generate report:\n{str(e)}")
                    return
            else:
                messagebox.showinfo("Info", "No analysis results to display. Please complete an analysis first.")
                return
        
        # Open the report with the appropriate system application
        try:
            if platform.system() == "Windows":
                os.startfile(self.report_pdf_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", self.report_pdf_path])
            else:  # Linux and other
                subprocess.call(["xdg-open", self.report_pdf_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open report:\n{str(e)}")
    
    def _generate_report(self, pdf_path, show_confirmation=True):
        """Generate and save a PDF report of the results with enhanced formatting."""
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
            segmentation_img = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\stl\IIB_2019-12-20_pred.png"
            processed_img = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\IIB_2019-12-20_assem.png"

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
            cfd_img = r"C:\Users\aleja\Desktop\Geometries\Airway-ML-CFD-Linux\Ortho_App\amatos (copy 1)\Ilyass Idrissi Boutaybi\OSA\CFD\IIB_2019-12-20_CFD.png"
            if os.path.exists(cfd_img):
                c.drawImage(cfd_img, 175, y_position - 250, width=300, height=200)
                c.setFont("Helvetica-Oblique", 10)
                c.drawCentredString(100 + 150, y_position - 310, "Figure 3: CFD Simulation Contour Plot")
            else:
                c.drawString(50, y_position - 30, "CFD simulation image not found.")

            # Save the PDF
            c.save()
            
            # Store the path for future reference
            self.report_pdf_path = pdf_path
            
            # Show confirmation if requested
            if show_confirmation:
                messagebox.showinfo("Save Complete", f"Report saved to:\n{pdf_path}")

            return True
        except Exception as e:
            if show_confirmation:
                messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
            raise