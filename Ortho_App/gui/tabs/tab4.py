# gui/tabs/tab4.py
import os
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from tkinter import ttk, messagebox
import time
from ..components.navigation import NavigationFrame2
from ..components.progress import ProgressSection
from ..components.forms import FormSection, ResultsFormSection
from ..components.pdf_viewer import PDFViewerFrame
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
import math
from config.settings import UI_SETTINGS


class Tab4Manager:
    def __init__(self, app):
        """Initialize Tab4Manager with a reference to the main app"""
        self.app = app
        self.processing_active = False
        self.logger = AppLogger()  # Initialize logger
        self.render_images = {}  # Fix: Add this to prevent AttributeError

        self.flow_rate = ctk.DoubleVar(value=10)

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
        """Create the header with home button and context information with shading"""
        # Top frame with light shading
        top_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 10), padx=20)
        
        # Configure grid layout
        top_frame.columnconfigure(0, weight=1)  # Home button
        top_frame.columnconfigure(1, weight=3)  # Context info
        top_frame.columnconfigure(2, weight=1)  # Right padding

        # Home button with confirmation check
        ctk.CTkButton(
            top_frame,
            text="Home",
            command=self._confirm_home,  # Changed to use our new method
            width=80,
            height=40,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Step indicator
        ctk.CTkLabel(
            top_frame,
            text="Step 3 of 3: Analysis",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            anchor="center"
        ).grid(row=0, column=1)

        # # Context header
        # context_text = (
        #     f"Patient: {self.app.patient_name.get()} | "
        #     f"DOB: {self.app.dob.get()} | "
        #     f"Physician: {self.app.patient_doctor_var.get()}"
        # )
        # ctk.CTkLabel(
        #     top_frame,
        #     text=context_text,
        #     font=("Arial", 13),
        #     anchor="center"
        # ).grid(row=1, column=1, padx=10, pady=1)
    
    def _create_navigation(self):
        """Create navigation with only a Back button in the style of NavigationFrame"""
        # Use the NavigationFrame class instead of creating custom frames
        self.nav_frame = NavigationFrame2(
            self.app.main_frame,
            previous_label="Review and Confirm",
            next_label="",  # Empty label for next (won't display)
            back_command=self._confirm_back,
        )

    def _confirm_back(self):
        """Prompt the user for confirmation before going back if analysis data exists."""
        # Check if analysis is in progress or results exist
        if self._should_confirm_navigation():
            response = messagebox.askyesno(
                "Confirm Navigation",
                "An analysis is in process or has been completed. Going back will erase all data. Are you sure you want to proceed?"
            )
            if response:
                self.app.create_tab3()
        else:
            # No analysis in progress or completed, just go back without confirmation
            self.app.create_tab3()

    def _confirm_home(self):
        """Confirm going home if analysis data exists."""
        # Check if analysis is in progress or results exist
        if self._should_confirm_navigation():
            response = messagebox.askyesno(
                "Confirm Navigation",
                "An analysis is in process or has been completed. Going home will erase all data. Are you sure you want to proceed?"
            )
            if response:
                self.app.go_home()
        else:
            # No analysis in progress or completed, just go home without confirmation
            self.app.go_home()

    def _should_confirm_navigation(self):
        """Helper method to check if confirmation is needed before navigation."""
        # Check if processing is active or if results have been generated
        return self.processing_active or (
            hasattr(self, 'preview_button') and 
            self.preview_button.cget("state") == "normal"
        )

    def _create_main_content(self):
        """Create the main content area with analysis options on the left and results on the right."""
        # Create main content frame using grid layout with shading
        content_frame = ctk.CTkFrame(self.app.main_frame, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        # Create left and right frames
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=20, pady=5, sticky="nsew")

        right_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=20, pady=5, sticky="nsew")

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
        analysis_section.pack(fill="x", pady=5)

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
            width=375,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"]
        )
        analysis_dropdown.pack(pady=(5, 10))

        # Processing details label
        self.processing_details_label = ctk.CTkLabel(
            analysis_section.content,
            text="",
            font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
            wraplength=350,
            justify="center"
        )
        self.processing_details_label.pack(pady=(0, 5))

        # Create flow rate frame (initially hidden)
        self.flow_rate_frame = ctk.CTkFrame(analysis_section.content, fg_color="transparent")

        # Flow rate label
        flow_rate_title = ctk.CTkLabel(
            self.flow_rate_frame,
            text="Flow Rate (LPM):",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            anchor="w"
        )
        flow_rate_title.pack(side="top", pady=(2, 0), anchor="w")

        # Flow rate control frame (horizontal layout)
        flow_control_frame = ctk.CTkFrame(self.flow_rate_frame, fg_color="transparent")
        flow_control_frame.pack(fill="x", pady=(2, 2))
        
        # Flow rate slider
        self.flow_rate_slider = ctk.CTkSlider(
            flow_control_frame,
            from_=0.1,
            to=50.0,
            number_of_steps=499,  # 0.1 LPM increments
            variable=self.flow_rate,
            width=200,
            command=self._update_flow_rate_label
        )
        self.flow_rate_slider.pack(side="left", padx=(0, 10))
        
        # Create input/display frame (for entry, value, and unit)
        input_frame = ctk.CTkFrame(flow_control_frame, fg_color="transparent")
        input_frame.pack(side="left")
        
        # Flow rate entry field - directly input value
        self.flow_rate_entry = ctk.CTkEntry(
            input_frame,
            width=50,
            height=28,
            justify="right",
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        )
        self.flow_rate_entry.pack(side="left")
        self.flow_rate_entry.insert(0, f"{self.flow_rate.get():.1f}")
        
        # Add validation and real-time update for the entry
        self.flow_rate_entry.bind("<FocusOut>", self._validate_flow_rate_entry)
        self.flow_rate_entry.bind("<Return>", self._validate_flow_rate_entry)
        self.flow_rate_entry.bind("<KeyRelease>", self._update_slider_on_keyrelease)
        
        # Flow rate unit label
        unit_label = ctk.CTkLabel(
            input_frame,
            text="LPM",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
        )
        unit_label.pack(side="left", padx=(5, 0))

    def _update_flow_rate_label(self, value=None):
        """Update the flow rate value when slider changes"""
        # Round to nearest 0.1 LPM for clean display
        rate_value = round(self.flow_rate.get() * 10) / 10
        
        # Update the entry field
        if hasattr(self, 'flow_rate_entry'):
            current_text = self.flow_rate_entry.get()
            new_text = f"{rate_value:.1f}"
            
            # Only update if the text has changed to avoid cursor jumping
            if current_text != new_text:
                self.flow_rate_entry.delete(0, "end")
                self.flow_rate_entry.insert(0, new_text)
    
    def _update_slider_on_keyrelease(self, event=None):
        """Update the slider in real-time as the user types in the entry field"""
        # Don't process special keys like arrows, backspace, etc.
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'BackSpace', 'Delete', 'Tab'):
            return
            
        try:
            # Get current text and try to convert to float
            entry_text = self.flow_rate_entry.get().strip()
            
            # Handle empty string
            if not entry_text:
                return
                
            # Replace comma with period if present
            entry_text = entry_text.replace(',', '.')
            
            # Try to convert to float - don't enforce range limits during typing
            value = float(entry_text)
            
            # Only update if value is within range
            if 1.0 <= value <= 50.0:
                # Update the DoubleVar to move the slider in real-time
                self.flow_rate.set(value)
        except ValueError:
            # Ignore conversion errors during typing
            pass
            
    def _validate_flow_rate_entry(self, event=None):
        """Validate the flow rate entry when focus leaves or Enter is pressed"""
        try:
            # Get the current value from the entry
            entry_text = self.flow_rate_entry.get().strip()
            
            # Replace comma with period if present
            entry_text = entry_text.replace(',', '.')
            
            # Convert to float
            value = float(entry_text)
            
            # Check if value is outside valid range
            if value < 1.0 or value > 50.0:
                # Show notification to user
                import tkinter as tk
                messagebox = tk.messagebox
                messagebox.showwarning(
                    "Invalid Flow Rate", 
                    "Please enter a value between 1.0 and 50.0 LPM"
                )
                
                # Reset to current value or nearest valid value
                if value < 1.0:
                    value = 1.0
                elif value > 50.0:
                    value = 50.0
            
            # Round to 1 decimal place
            value = round(value * 10) / 10
            
            # Update the DoubleVar to change the slider position
            self.flow_rate.set(value)
            
            # Update the entry field with the formatted value
            self.flow_rate_entry.delete(0, "end")
            self.flow_rate_entry.insert(0, f"{value:.1f}")
            
            # Remove focus from entry field
            if event and event.widget == self.flow_rate_entry:
                self.app.main_frame.focus_set()
            
            # Important: Stop event propagation when Enter is pressed
            if event and event.keysym == 'Return':
                return "break"
            
        except ValueError:
            # If conversion fails, show notification and reset
            import tkinter as tk
            messagebox = tk.messagebox
            messagebox.showwarning(
                "Invalid Input", 
                "Please enter a valid number with up to one decimal place"
            )
            
            # Reset to the current slider value
            self.flow_rate_entry.delete(0, "end")
            self.flow_rate_entry.insert(0, f"{self.flow_rate.get():.1f}")
            
            # Remove focus from entry field
            if event and event.widget == self.flow_rate_entry:
                self.app.main_frame.focus_set()
                
            # Important: Stop event propagation when Enter is pressed
            if event and event.keysym == 'Return':
                return "break"


    def _create_processing_section(self, parent):
        """Create the processing section with progress bar"""
        processing_section = FormSection(parent, "Processing", fg_color="transparent", font=UI_SETTINGS["FONTS"]["HEADER"])
        processing_section.pack(fill="x", pady=5)

        # Start button
        self.process_button = ctk.CTkButton(
            processing_section.content,
            text="Start Processing",
            command=self._validate_and_start_processing,
            width=300,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"]
        )
        self.process_button.pack(pady=(2,2))

        # Progress section
        self.progress_section = ProgressSection(processing_section.content)
        self.progress_section.pack(fill="x", pady=(0,2))

    def _create_results_section(self, parent):
        """Create the results section with a Notebook to view different stages."""
        results_section = ResultsFormSection(parent, "Results")
        results_section.pack(fill="both", padx=20, pady=(5, 5), expand=True)

        notebook_frame = results_section.content

        # Add description label below the Results header
        results_description = ctk.CTkLabel(
            results_section.content,
            text="Switch between tabs to view different analysis stages. \nUse the Preview and Save buttons below to access complete results.",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"],
            wraplength=650,  # Allow text to wrap
            justify="center"
        )
        results_description.pack(pady=(5, 2))

        # Create a container for the notebook
        notebook_container = ctk.CTkFrame(notebook_frame, width=700, height=400,
                                        fg_color=results_section.content.cget("fg_color"))
        notebook_container.pack(pady=(3, 5), fill="both", expand=True)
        notebook_container.pack_propagate(False)

        # Define tab colors
        self.tab_colors = {
            "Segmentation": "#00734d",     # Green for segmentation
            "Post-processed": "#006a9f",    # Blue for post-processed
            "CFD Simulation": "#a63600"     # Orange/red for CFD
        }

        # Create tab container with padding to allow for "popped up" active tab
        tabs_container = ctk.CTkFrame(notebook_container, fg_color=notebook_container.cget("fg_color"), height=50)
        tabs_container.pack(fill="x", side="top", padx=10, pady=(10, 0))
        
        # Add shadow container under the tabs to create the illusion of elevation for active tab
        self.shadow_container = ctk.CTkFrame(notebook_container, fg_color="#ababab", height=3)
        self.shadow_container.pack(fill="x", side="top", padx=15, pady=(0, 0))
        
        # Content frame that will hold the content of the selected tab
        self.content_frame = ctk.CTkFrame(notebook_container, fg_color=notebook_container.cget("fg_color"))
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create the tab frames and initialize them
        self.segmentation_frame = ctk.CTkFrame(self.content_frame, fg_color=results_section.content.cget("fg_color"))
        self.postprocessing_frame = ctk.CTkFrame(self.content_frame, fg_color=results_section.content.cget("fg_color"))
        self.cfd_frame = ctk.CTkFrame(self.content_frame, fg_color=results_section.content.cget("fg_color"))
        
        # Store references to tab frames
        self.tab_frames = {
            "Segmentation": self.segmentation_frame,
            "Post-processed": self.postprocessing_frame,
            "CFD Simulation": self.cfd_frame
        }
        
        # Create the tab buttons with even spacing
        tab_names = ["Segmentation", "Post-processed", "CFD Simulation"]
        self.tab_buttons = {}
        
        # Configure tabs container to distribute tabs evenly
        for i in range(len(tab_names)):
            tabs_container.columnconfigure(i, weight=1)
        
        # Set heights for tabs
        self.normal_tab_height = 35
        self.active_tab_height = 40
        
        # Shadow frames for each tab
        self.tab_shadows = {}
        
        for i, tab_name in enumerate(tab_names):
            # Create a frame to hold both the button and its shadow
            tab_frame = ctk.CTkFrame(tabs_container, fg_color="transparent")
            tab_frame.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            
            # Create the tab button
            self.tab_buttons[tab_name] = ctk.CTkButton(
                tab_frame,
                text=tab_name,
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                fg_color="#d9d9d9",
                text_color="#505050",
                hover_color=self.tab_colors[tab_name],
                height=self.normal_tab_height,
                corner_radius=6,
                command=lambda name=tab_name: self._select_tab(name)
            )
            self.tab_buttons[tab_name].pack(fill="x", expand=True)
            
            # Create shadow frame for this tab (initially hidden)
            self.tab_shadows[tab_name] = ctk.CTkFrame(
                tab_frame, 
                fg_color="#777777",
                height=4,
                corner_radius=2
            )
        
        # Default to first tab (Segmentation) initially selected
        self._select_tab("Segmentation")
        
        # Create a frame for the buttons along the bottom
        button_frame = ctk.CTkFrame(results_section, fg_color=results_section.cget("fg_color"))
        button_frame.pack(side="bottom", fill="x", padx=20, pady=10)

        # Preview button
        eye_icon = self._load_icon("eye", width=32) # Fallback to emoji if image loading fails
        self.preview_button = ctk.CTkButton(
            button_frame,
            text="Preview Report",
            image=eye_icon,
            compound="left",
            command=self._preview_report,
            width=250,  # Make wider to take up 50% of space
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            state="disabled"
        )
        self.preview_button.pack(side="left", padx=(0, 5), fill="x", expand=True)

        # Export button
        save_icon = self._create_custom_icon("save", size=(24, 24))
        self.export_button = ctk.CTkButton(
            button_frame,
            text="Save Report as PDF",
            image=save_icon,
            compound="left",
            command=self._export_results_to_pdf,
            width=250,  # Make wider to take up 50% of space
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            state="disabled"
        )
        self.export_button.pack(side="left", fill="x", expand=True)
        
        return results_section

    def _load_icon(self, icon_name, width=24):
        try:
            # Path to your icons folder
            icon_path = os.path.join("gui", "components", "Images", f"{icon_name}.png")
            
            # Open the image to get its dimensions
            img = Image.open(icon_path)
            orig_width, orig_height = img.size
            
            # Calculate height to maintain aspect ratio
            aspect_ratio = orig_height / orig_width
            height = int(width * aspect_ratio)
            
            # Return the CTkImage with the calculated dimensions
            return ctk.CTkImage(img, size=(width, height))
        except Exception as e:
            print(f"Error loading icon {icon_name}: {e}")
            # Fallback to emoji
            return None
    
    def _create_custom_icon(self, icon_type, size=(24, 24)):
        """Create a custom icon using PIL"""
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if icon_type == "save":
            # Draw save icon (floppy disk)
            icon_color = (41, 98, 255)  # Blue
            # Main rectangle
            draw.rectangle([(2, 2), (size[0]-2, size[1]-2)], outline=icon_color, width=2)
            # Top part of floppy
            draw.rectangle([(5, 2), (size[0]-5, 7)], fill=icon_color)
            # Inner rectangle (label part)
            draw.rectangle([(6, 9), (size[0]-6, size[1]-6)], outline=icon_color)
            # Small square (metal part)
            draw.rectangle([(8, 3), (14, 6)], fill=(255, 255, 255))
            
        elif icon_type == "document":
            # Create a folder icon similar to the reference image
            # Colors based on the image
            outline_color = (12, 30, 30)  # Dark teal/black outline
            back_color = (221, 126, 50)   # Orange/brown for back part
            front_color = (252, 207, 49)  # Yellow for front part
            
            # Back part of folder (tab part)
            draw.polygon([
                (4, 4),           # Top left
                (size[0]//2-2, 4), # Tab width
                (size[0]//2+3, 9), # Tab corner
                (size[0]-4, 9),   # Top right
                (size[0]-4, size[1]-4), # Bottom right
                (4, size[1]-4)    # Bottom left
            ], fill=back_color, outline=outline_color, width=2)
            
            # Front part of folder (main face)
            draw.polygon([
                (4, 9),           # Top left
                (size[0]-4, 9),   # Top right
                (size[0]-4, size[1]-4), # Bottom right
                (4, size[1]-4)    # Bottom left
            ], fill=front_color, outline=outline_color, width=2)
        
        elif icon_type == "eye":
            # Create a simple eye icon exactly like the reference image - more horizontally elongated
            
            # Eye dimensions - emphasize horizontal elongation
            eye_width = size[0] - 2  # Use more horizontal space
            eye_height = size[1] // 3  # Reduce vertical height for more elongated look
            eye_center_x = size[0] // 2
            eye_center_y = size[1] // 2
            
            # Draw the outer eye shape (black silhouette)
            # Use a more direct approach with polygon points for football/almond shape
            outer_points = []
            
            # Create horizontal elongated pointed eye shape
            for angle in range(0, 360, 5):
                # Use different x,y scaling to create elongated shape
                x = eye_center_x + (eye_width/2) * math.cos(math.radians(angle))
                # Reduce y component for flatter look
                y = eye_center_y + (eye_height/2) * math.sin(math.radians(angle))
                outer_points.append((x, y))
            
            # Draw the eye outline
            draw.polygon(outer_points, fill=(0, 0, 0))
            
            # Create the white space inside (scaled down version of the outer shape)
            inner_width = eye_width * 0.7
            inner_height = eye_height * 0.7
            inner_points = []
            
            for angle in range(0, 360, 5):
                x = eye_center_x + (inner_width/2) * math.cos(math.radians(angle))
                y = eye_center_y + (inner_height/2) * math.sin(math.radians(angle))
                inner_points.append((x, y))
            
            # Draw the inner white part
            draw.polygon(inner_points, fill=(255, 255, 255))
            
            # Draw the pupil as a solid black circle in the center
            # Make pupil slightly smaller compared to overall eye size
            pupil_radius = min(inner_width, inner_height) * 0.4
            draw.ellipse(
                [(eye_center_x - pupil_radius, eye_center_y - pupil_radius),
                 (eye_center_x + pupil_radius, eye_center_y + pupil_radius)],
                fill=(0, 0, 0)
            )
                    
        # Convert to CTkImage
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        return ctk_img
    
    def _select_tab(self, tab_name):
        """Select a tab and update styling with enhanced visual cues."""
        # Make sure we have the tab frames initialized
        if not hasattr(self, 'tab_frames') or not self.tab_frames:
            return
            
        # Hide all tab frames first
        for frame in self.tab_frames.values():
            frame.pack_forget()
        
        # Show the selected tab frame
        if tab_name in self.tab_frames:
            self.tab_frames[tab_name].pack(fill="both", expand=True)
        
        # Update button styling
        for name, button in self.tab_buttons.items():
            # First hide all shadows
            if hasattr(self, 'tab_shadows'):
                if name in self.tab_shadows:
                    self.tab_shadows[name].pack_forget()
            
            if name == tab_name:
                # Selected tab styling
                button.configure(
                    fg_color=self.tab_colors[name],
                    text_color="white",
                    border_width=3,
                    border_color="#222222",
                    height=self.active_tab_height
                )
                
                # Show shadow for active tab if available
                if hasattr(self, 'tab_shadows') and name in self.tab_shadows:
                    self.tab_shadows[name].pack(fill="x", side="bottom", padx=5, pady=(0, 0))
                    
            else:
                # Unselected tabs
                button.configure(
                    fg_color="#d9d9d9",
                    text_color=self.tab_colors[name],
                    border_width=0,
                    height=self.normal_tab_height
                )
        
        # Add indicator bar if applicable
        if hasattr(self, 'tab_indicator') and self.tab_indicator is not None:
            self.tab_indicator.destroy()
        
        # Create a thicker colored indicator at the top of the active tab content
        if tab_name in self.tab_frames:
            self.tab_indicator = ctk.CTkFrame(
                self.tab_frames[tab_name], 
                height=5,
                fg_color=self.tab_colors[tab_name],
                corner_radius=0
            )
            self.tab_indicator.pack(fill="x", side="top")
            
        # Update shadow container if it exists
        if hasattr(self, 'shadow_container'):
            self.shadow_container.configure(fg_color="#ababab")
        
        # Lift buttons above shadow line if needed
        for tab_button in self.tab_buttons.values():
            tab_button.lift()
            
        # Force UI update to ensure changes are visible
        self.app.update_idletasks()
    
    def _create_emoji_icon(self, emoji, size=(20, 20)):
        """Create a more visually engaging icon with an emoji character."""
        # Create a blank image with transparent background
        img = Image.new('RGBA', (size[0]*2, size[1]*2), (255, 255, 255, 0))
        
        # Create ImageDraw object
        draw = ImageDraw.Draw(img)
        
        # Calculate font size based on image size - make it larger for visibility
        font_size = min(size) * 1.8  # Increased from 1.5 to 1.8
        
        # Custom colors for specific emojis to make them more engaging
        emoji_colors = {
            "💾": (41, 98, 255, 255),   # Blue for save icon
            "📄": (0, 0, 0, 255),       # Black for document icon
            "🔄": (0, 115, 76, 255),    # Dark green for refresh/open icons to match app theme
        }
        
        # Use the custom color if defined, otherwise default to black
        fill_color = emoji_colors.get(emoji, (0, 0, 0, 255))
        
        try:
            # Try to use a system font that supports emoji
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
        
        # Draw the emoji text with the chosen color
        draw.text(position, emoji, fill=fill_color, font=font)
        
        # Resize to desired dimensions
        img = img.resize(size, Image.LANCZOS)
        
        # Convert to CTkImage
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        return ctk_img

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
        
        # Show/hide flow rate controls based on selection
        if choice == "Airflow Simulation":
            self.flow_rate_frame.pack(fill="x", pady=(5, 10))
        else:
            self.flow_rate_frame.pack_forget()

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

        # For airflow simulation, check if results already exist for this flow rate
        if "Simulation" in self.analysis_option.get():
            if self._cfd_results_exist():
                # Results already exist - ask if user wants to use existing results
                flow_str = f"{self.flow_rate.get():.1f}"
                response = messagebox.askquestion(
                    "Existing Results Found",
                    f"CFD results for flow rate {flow_str} LPM already exist. Would you like to use these existing results instead of running a new simulation?",
                    icon="question"
                )
                
                if response == "yes":
                    # Use existing results - skip to finalization step
                    self._finalize_processing()
                    return

        # Show confirmation dialog focused on analysis type
        analysis_type = self.analysis_option.get()
        message = f"Would you like to proceed with {analysis_type}?\n\n"
        
        if "Simulation" in analysis_type:
            message += f"This will:\n" \
                    f"1. Perform airway segmentation\n" \
                    f"2. Generate 3D model (in STL format)\n" \
                    f"3. Calculate airway volume in (mm³)\n" \
                    f"4. Generate 3D mesh\n" \
                    f"5. Run CFD simulation at {self.flow_rate.get():.1f} LPM\n" \
                    f"6. Provide pressure and velocity images of the 3D-scanned model"
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
            # Initialize render_images if it doesn't exist
            if not hasattr(self, 'render_images'):
                self.render_images = {}
                
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
                self.cancel_requested = True
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

    def _display_log_messages(self, line_index=0):
        """Display log messages line by line from the prediction log file."""
        # Check cancellation flag before proceeding
        if self.cancel_requested:
            self.logger.log_info("Log display cancelled")
            return
            
        # log_file_path = "/home/amatos/Desktop/amatos/Ilyass Idrissi Boutaybi/OSA/prediction/pred_log.txt" # linux path tk
        log_file_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/prediction/pred_log.txt"

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
                    self.app.after(5, lambda: self._display_log_messages(line_index + 1))  # Schedule next line tk

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
                "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/IIB_2019-12-20_pred.png"
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
        
        # Use dynamic path with flow rate for postprocessing image
        # postprocessed_img_path = r"C:\Users\aleja\Desktop\amatos\Qadra Hussein\Test_1\Test Run\IIB_2019-12-20_assem.png"
        postprocessed_img_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test_1/Test Run/IIB_2019-12-20_assem.png"
        self.scheduled_updates.append(
            self.app.after(13000, lambda: self._update_render_display_if_not_cancelled(
                "postprocessing",
                postprocessed_img_path
            ))
        )

        # Switch to Post-processed tab after showing model if not cancelled
        self.scheduled_updates.append(
            self.app.after(13050, lambda: self._select_tab_if_not_cancelled("Post-processed"))
        )

        self.scheduled_updates.append(
            self.app.after(15000, lambda: self._update_processing_stage_if_not_cancelled(
                96, f"Running airflow simulation at {self.flow_rate.get():.1f} LPM..."
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(18000, lambda: self._update_processing_stage_if_not_cancelled(
                100, "Generating airflow simulation results..."
            ))
        )
        
        # Use dynamic path for CFD image
        # cfd_img_path = os.path.join(self._get_full_cfd_path(), "IIB_2019-12-20_CFD.png") # replae when simulation works tk
        cfd_img_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test_1/Test Run/IIB_2019-12-20_CFD.png"
        self.scheduled_updates.append(
            self.app.after(20000, lambda: self._update_render_display_if_not_cancelled(
                "cfd",
                cfd_img_path
            ))
        )
        
        self.scheduled_updates.append(
            self.app.after(22000, self._finalize_processing_if_not_cancelled)
        )
    
    # Helper methods that check cancellation flag
    
    def _update_processing_stage_if_not_cancelled(self, progress, message):
        """Update processing stage only if cancellation wasn't requested"""
        if not self.cancel_requested and hasattr(self, 'progress_section'):
            self._update_processing_stage(progress, message)

    
    def _update_render_display_if_not_cancelled(self, stage, image_path):
        """Update render display only if cancellation wasn't requested"""
        if not self.cancel_requested:
            self._update_render_display(stage, image_path)

    
    def _select_tab_if_not_cancelled(self, tab_name):
        """Select a tab only if cancellation wasn't requested"""
        if not self.cancel_requested:
            self._select_tab(tab_name)

    
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
        """Final step: update all tabs with content and ensure buttons are visible."""
        self.processing_active = False
        self.process_button.configure(state="normal")
        
        # Stop the progress bar
        self.progress_section.stop("Processing complete!")
        
        # Enable the Preview and Export buttons
        self.preview_button.configure(state="normal")
        self.export_button.configure(state="normal")
        
        # Populate all tabs with content
        self.app.update_idletasks()  # Force UI update before rendering tabs
        
        # Segmentation tab
        # segmentation_path = r"C:\Users\aleja\Desktop\amatos\Qadra Hussein\Test\stl\IIB_2019-12-20_pred.png" # Windows tktk
        segmentation_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/IIB_2019-12-20_pred.png"
        self._update_render_display("segmentation", segmentation_path)
        
        # If simulation was selected, populate other tabs
        if "Simulation" in self.analysis_option.get():
            # Get paths based on selected flow rate
            cfd_base_path = self._get_full_cfd_path()
            
            # Post-processed tab
            # postprocessed_path = os.path.join(cfd_base_path, "IIB_2019-12-20_assem.png") # Change when legit tk
            postprocessed_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test_1/Test Run/IIB_2019-12-20_assem.png"
            self._update_render_display("postprocessing", postprocessed_path)
            
            # CFD tab
            # cfd_path = os.path.join(cfd_base_path, "IIB_2019-12-20_CFD.png") tk
            cfd_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test_1/Test Run/IIB_2019-12-20_CFD.png"
            self._update_render_display("cfd", cfd_path)
            
            # Select CFD tab as it's the final result
            self._select_tab("CFD Simulation")
        else:
            # Just select the segmentation tab
            self._select_tab("Segmentation")

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
            self.app.after(5000, lambda: self._update_processing_stage_if_not_cancelled(
                85, "Generating 3D visualization..."
            ))
        )
        
        # Ensure we use the unified method for updating the display
        self.scheduled_updates.append(
            self.app.after(7000, lambda: self._update_render_display_if_not_cancelled(
                "segmentation",
                "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/IIB_2019-12-20_pred.png"
            ))
        )

        if "Simulation" in self.analysis_option.get():
            self._schedule_simulation_steps()
        else:
            self.scheduled_updates.append(
                self.app.after(8000, self._finalize_processing_if_not_cancelled)
            )

    def _update_render_display(self, stage, image_path, placeholder=False):
        """Update the display with proper button sizing and handle tab selection."""
        # Map stage to tab name
        tab_name_map = {
            "segmentation": "Segmentation",
            "postprocessing": "Post-processed", 
            "cfd": "CFD Simulation"
        }
        
        tab_name = tab_name_map.get(stage)
        if not tab_name:
            return
            
        # Get the frame for this tab
        frame = self.tab_frames[tab_name]
        
        # Clear previous content
        for widget in frame.winfo_children():
            if hasattr(self, 'tab_indicator') and widget != self.tab_indicator:  # Preserve tab indicator
                widget.destroy()

        # Create main container
        main_container = ctk.CTkFrame(
            frame,
            fg_color=frame.cget("fg_color")
        )
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create image container with fixed height
        image_container = ctk.CTkFrame(
            main_container,
            fg_color=main_container.cget("fg_color"),
            height=240
        )
        image_container.pack(fill="x", expand=False, pady=(5, 5))
        image_container.pack_propagate(False)
        
        if placeholder or image_path is None:
            # Display placeholder message
            ctk.CTkLabel(image_container, text=f"{stage.capitalize()} render will appear here.", font=("Arial", 12)).pack(expand=True)
        else:
            try:
                # Load and display image
                pil_image = Image.open(image_path)
                
                # Calculate sizing based on stage
                if stage == "cfd":
                    max_width = 450
                else:
                    max_width = 300
                max_height = 200
                
                # Calculate aspect ratio-preserving dimensions
                orig_width, orig_height = pil_image.size
                width_ratio = max_width / orig_width
                height_ratio = max_height / orig_height
                scale_ratio = min(width_ratio, height_ratio)
                
                new_width = int(orig_width * scale_ratio)
                new_height = int(orig_height * scale_ratio)
                
                # Resize image
                pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=pil_image, size=(new_width, new_height))
                
                # Store reference to avoid garbage collection
                self.render_images[stage] = ctk_image
                
                # Display image centered
                image_label = ctk.CTkLabel(image_container, image=ctk_image, text="")
                image_label.pack(pady=(10, 5))
                
                # Add caption
                if stage == "cfd":
                    caption_text = "CFD simulation results showing pressure and velocity contours"
                elif stage == "postprocessing":
                    caption_text = "Post-processed model with inlet (green), and outlet (red) components"
                else:
                    caption_text = "Segmentation visualization"
                    
                ctk.CTkLabel(
                    image_container,
                    text=caption_text,
                    font=("Arial", 12),
                    text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
                ).pack(pady=(0, 5))
                
                # Store the path for the STL file to be viewed
                if stage == "segmentation":
                    # Try to derive the STL path from the image path
                    self.current_stl_path = str(Path(image_path).with_suffix(".stl"))
                
            except Exception as e:
                error_msg = f"Error loading image: {str(e)}"
                ctk.CTkLabel(image_container, text=error_msg, font=("Arial", 12)).pack(expand=True)
                self.logger.log_error(error_msg)
        
        # Create a dedicated button frame with transparent background
        button_frame = ctk.CTkFrame(
            main_container,
            fg_color="transparent"
        )
        button_frame.pack(fill="x", pady=(15, 5))
        
        # Create the appropriate button based on the stage
        if stage == "segmentation":
            segmentation_button = ctk.CTkButton(
                button_frame,
                text="🔄 Open Airway Prediction Model in 3D Viewer",
                command=lambda: self._display_interactive_stl(self.current_stl_path if hasattr(self, 'current_stl_path') else None),
                width=350,
                height=40,
                font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                fg_color="#00734d",
                hover_color="#005a3e",
                text_color="white"
            )
            segmentation_button.pack(pady=5)
            
        elif stage == "postprocessing":
            postprocessed_button = ctk.CTkButton(
                button_frame,
                text="🔄 Open Model with Processed Boundaries in 3D Viewer",
                command=self._display_interactive_components,
                width=350,
                height=40,
                font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                fg_color="#00734d",
                hover_color="#005a3e",
                text_color="white"
            )
            postprocessed_button.pack(pady=5)
            
        elif stage == "cfd":
            cfd_button = ctk.CTkButton(
                button_frame,
                text="🔄 Open Interactive CFD Results Viewer",
                command=self._display_interactive_cfd,
                width=350,
                height=40,
                font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                fg_color="#00734d",
                hover_color="#005a3e",
                text_color="white"
            )
            cfd_button.pack(pady=5)
        
        # Force update the UI
        self.app.update_idletasks()
        
        # Select the tab to show the content if needed
        self._select_tab(tab_name)

    def _handle_processing_completion(self, success, results):
        """Handle completion of processing"""
        self.processing_active = False
        self.process_button.configure(state="normal")

        if success:
            self.progress_section.stop("Processing Complete!")

            # Store the airway volume for use in reports
            self.airway_volume = results['volume']

            # Show success message with results
            message = (
                f"Processing completed successfully!\n\n"
                f"Airway Volume: {results['volume']:.2f} mm³\n\n"
                f"Files created:\n"
                f"- NIfTI: {Path(results['nifti_path']).name}\n"
                f"- Prediction: {Path(results['prediction_path']).name}\n"
                f"- STL: {Path(results['stl_path']['stl_path']).name}"
            )
            messagebox.showinfo("Success", message)

            # Show results section
            self.results_frame.pack(fill="both", expand=True, pady=(5, 5))

            # Show render in display section
            if 'preview_path' in results['stl_path'] and os.path.exists(results['stl_path']['preview_path']):
                self._update_render_display("segmentation", results['stl_path']['preview_path'])
            else:
                messagebox.showwarning("Warning", "Preview image not found. Using default visualization.")
                self._update_render_display("segmentation", None)

            # Enable the Preview and Export buttons
            self.preview_button.configure(state="normal")
            self.export_button.configure(state="normal")

            # If airflow simulation was selected, proceed with CFD (keep your current approach for simulation)
            if "Simulation" in self.analysis_option.get():
                response = messagebox.askquestion(
                    "Continue to CFD",
                    "Would you like to proceed with CFD analysis?"
                )
                if response == "yes":
                    # Start the second phase of processing for CFD
                    self._schedule_simulation_steps()
        else:
            # Display error message
            error_message = results if isinstance(results, str) else "Unknown error occurred"
            messagebox.showerror(
                "Error",
                f"Processing failed:\n{error_message}"
            )
            # Log the error
            self.logger.log_error(f"Processing failed: {error_message}")

    def _display_segmentation_image(self, image_path):
        """Just call the unified update method for consistency"""
        self._update_render_display("segmentation", image_path)

    def _display_interactive_stl(self, stl_path):
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
            
        except ImportError:
            tk.messagebox.showerror("Error", "3D visualization requires the open3d library. Please install it with 'pip install open3d'.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to display interactive STL viewer:\n{e}")

    def _update_postprocessed_display(self, image_path):
        """
        Display the post-processed model with proper button sizing.
        """
        if not hasattr(self, 'postprocessing_frame') or not self.postprocessing_frame.winfo_exists():
            return
            
        for widget in self.postprocessing_frame.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ctk.CTkFrame(
            self.postprocessing_frame,
            fg_color=self.postprocessing_frame.cget("fg_color")
        )
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create image container - reduced fixed height to leave room for button
        image_container = ctk.CTkFrame(
            main_container,
            fg_color=main_container.cget("fg_color"),
            height=320  # Reduced height to ensure space for button
        )
        image_container.pack(fill="x", expand=False, pady=(5, 5))
        image_container.pack_propagate(False)
        
        try:
            # Load and display image
            pil_image = Image.open(image_path)
            
            # Set reduced image dimensions to ensure button space
            max_width = 300
            max_height = 240  # Reduced height
            
            # Calculate aspect ratio-preserving dimensions
            orig_width, orig_height = pil_image.size
            width_ratio = max_width / orig_width
            height_ratio = max_height / orig_height
            scale_ratio = min(width_ratio, height_ratio)
            
            new_width = int(orig_width * scale_ratio)
            new_height = int(orig_height * scale_ratio)
            
            # Resize image
            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=pil_image, size=(new_width, new_height))
            
            # Store reference to avoid garbage collection
            self.render_images["postprocessed"] = ctk_image
            
            # Display image centered
            image_label = ctk.CTkLabel(image_container, image=ctk_image, text="")
            image_label.pack(pady=(10, 5))
            
            # Add caption with consistent styling
            ctk.CTkLabel(
                image_container,
                text="Post-processed model with inlet (green), and outlet (red) components",
                font=("Arial", 11)
            ).pack(pady=(0, 5))
            
        except Exception as e:
            error_msg = f"Error loading image: {str(e)}"
            ctk.CTkLabel(image_container, text=error_msg, font=("Arial", 12)).pack(expand=True)
            self.logger.log_error(error_msg)
        
        # Create a dedicated, spacious button frame with sufficient height
        button_frame = ctk.CTkFrame(
            main_container,
            fg_color=main_container.cget("fg_color")
        )
        button_frame.pack(fill="x", side="bottom", pady=(10, 10), ipady=10)
        
        # Create the button with explicit sizing - made wider and taller
        self.view_components_button = ctk.CTkButton(
            button_frame,
            text="🔄 Open Model with Processed Boundaries in 3D Viewer",
            command=self._display_interactive_components,
            width=350,  # Explicit width
            height=50,  # Taller height
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color="#00734d",  # Consistent green color
            hover_color="#005a3e",
            text_color="white"
        )
        self.view_components_button.pack(pady=10, padx=20, fill="x", expand=True)

    def _display_interactive_components(self):
        """
        Launch an interactive viewer for the inlet, outlet, and wall components
        with color coding.
        """
        try:
            def view_components():
                # Base path for components
                base_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl"
                
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
                vis.create_window(window_name="Airway Components Viewer", width=700, height=450)
                
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
                vis.create_window(window_name="Interactive STL Viewer", width=700, height=450)
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
                inlet_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/inlet.stl"
                inlet_mesh = o3d.io.read_triangle_mesh(inlet_path)
                inlet_mesh.compute_vertex_normals()
                inlet_mesh.paint_uniform_color([0, 1, 0])  # Green

                outlet_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/outlet.stl"
                outlet_mesh = o3d.io.read_triangle_mesh(outlet_path)
                outlet_mesh.compute_vertex_normals()
                outlet_mesh.paint_uniform_color([1, 0, 0])  # Red

                wall_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/wall.stl"
                wall_mesh = o3d.io.read_triangle_mesh(wall_path)
                wall_mesh.compute_vertex_normals()
                wall_mesh.paint_uniform_color([0.7, 0.7, 0.7])  # Gray

                o3d.visualization.draw_geometries([inlet_mesh, outlet_mesh,wall_mesh])

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to display interactive STL viewer:\n{e}")
    
    def _export_results_to_pdf(self):
        """Save the report as a PDF file automatically to a predetermined location."""
        try:
            # Get flow rate formatted with underscore for filename
            flow_str = f"{self.flow_rate.get():.1f}".replace('.', '_')
            
            # Use predetermined path with flow rate in the filename
            # Get directory path based on flow rate
            output_dir = os.path.join("/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test", f"CFD_{flow_str}")
            os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
            
            # Construct the full path for the PDF file
            save_path = os.path.join(output_dir, f"exported_results_flow_{flow_str}.pdf")
            
            # If we already have a preview PDF, use it as a basis
            if hasattr(self, "preview_pdf_path") and os.path.exists(self.preview_pdf_path):
                # Generate new PDF without the watermark
                if self._generate_report(save_path, show_confirmation=True):
                    # Store the path for reference
                    self.report_pdf_path = save_path
                    return True
            else:
                # No preview exists, so generate directly
                if self._generate_report(save_path, show_confirmation=True):
                    # Store the path for reference
                    self.report_pdf_path = save_path
                    return True
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report:\n{str(e)}")
            return False

    # def _open_report(self):
    #     """Open the report, generating it on-the-fly if it doesn't exist yet."""
    #     default_report_path = r"C:\Users\aleja\Desktop\amatos\Qadra Hussein\Test_1\Test Run\exported_results_flow_10_0.pdf"
        
    #     # Check if report exists (either from previous export or as default)
    #     report_exists = hasattr(self, "report_pdf_path") and os.path.exists(self.report_pdf_path)
        
    #     if not report_exists:
    #         # If analysis has been completed but report not saved, generate it first
    #         if self.processing_active is False and self.results_frame.winfo_children():
    #             # Generate report on-the-fly without showing confirmation message
    #             try:
    #                 self._generate_report(default_report_path, show_confirmation=False)
    #                 self.report_pdf_path = default_report_path
    #                 report_exists = True
    #             except Exception as e:
    #                 messagebox.showerror("Error", f"Failed to generate report:\n{str(e)}")
    #                 return
    #         else:
    #             messagebox.showinfo("Info", "No analysis results to display. Please complete an analysis first.")
    #             return
        
    #     # Open the report with the appropriate system application
    #     try:
    #         if platform.system() == "Windows":
    #             os.startfile(self.report_pdf_path)
    #         elif platform.system() == "Darwin":  # macOS
    #             subprocess.call(["open", self.report_pdf_path])
    #         else:  # Linux and other
    #             subprocess.call(["xdg-open", self.report_pdf_path])
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Failed to open report:\n{str(e)}")
    
    def _get_cfd_dir_name(self, flow_rate=None):
        """
        Get the name of the CFD directory based on flow rate, using underscore instead of decimal.
        If flow_rate is None, uses the current user-selected flow rate.
        """
        if flow_rate is None:
            flow_rate = self.flow_rate.get()
        
        # Format with exactly one decimal place
        flow_str = f"{flow_rate:.1f}"
        # Replace decimal point with underscore
        flow_dir = flow_str.replace('.', '_')
        
        return f"CFD_{flow_dir}"
    
    def _get_full_cfd_path(self, flow_rate=None):
        """
        Get the full path to the CFD directory for the specified flow rate.
        """
        cfd_dir = self._get_cfd_dir_name(flow_rate)
        
        # Base path where CFD results are stored
        base_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/"
        
        return os.path.join(base_path, cfd_dir)

    def _cfd_results_exist(self, flow_rate=None):
        """
        Check if CFD results already exist for the specified flow rate.
        Returns True if the case.foam file exists in the CFD directory.
        """
        cfd_path = self._get_full_cfd_path(flow_rate)
        
        # Check if directory exists
        if not os.path.exists(cfd_path):
            return False
        
        # Check if case.foam file exists (indicator that simulation completed)
        case_foam_path = os.path.join(cfd_path, "case.foam")
        return os.path.exists(case_foam_path)
    
    def _display_interactive_cfd(self):
        """Launch an interactive viewer for CFD simulation results"""
        try:
            def view_cfd_results():
                # Use dynamic path based on selected flow rate
                cfd_path = self._get_full_cfd_path()
                
                # Load mesh for airway
                mesh_path = os.path.join(cfd_path, "cfd_mesh.stl")  # Adjust filename as needed
                
                # Fallback if the specific mesh file doesn't exist
                if not os.path.exists(mesh_path):
                    # Use the wall mesh as a fallback
                    mesh_path = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/wall.stl"
                
                mesh = o3d.io.read_triangle_mesh(mesh_path)
                mesh.compute_vertex_normals()
                
                # Create a semi-transparent visualization
                mesh.paint_uniform_color([0.7, 0.7, 0.7])  # Gray base color
                
                # Create visualization window
                vis = o3d.visualization.Visualizer()
                vis.create_window(window_name=f"CFD Results Viewer - {self.flow_rate.get():.1f} LPM", width=800, height=600)
                vis.add_geometry(mesh)
                
                # Set rendering options for better visualization
                render_option = vis.get_render_option()
                render_option.background_color = [1, 1, 1]  # White background
                render_option.point_size = 1.0
                render_option.mesh_show_wireframe = True  # Show wireframe for better visibility
                render_option.mesh_show_back_face = True
                
                # Set view control for better initial view
                view_control = vis.get_view_control()
                view_control.set_zoom(0.8)
                
                # Run the visualizer
                vis.run()
                vis.destroy_window()
            
            # Start in a separate thread
            threading.Thread(target=view_cfd_results, daemon=True).start()
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to display CFD viewer:\n{e}")
    
    def _create_consistent_button(self, parent_frame, text, command, icon="🔄"):
        """
        Create a consistent button with uniform styling across all tabs
        
        Args:
            parent_frame: The frame to place the button in
            text: The button text
            command: The function to call when clicked
            icon: Optional icon to prepend to the text (default: 🔄)
        
        Returns:
            The created button
        """
        button = ctk.CTkButton(
            parent_frame,
            text=f"{icon} {text}",
            command=command,
            width=400,  # Consistent width for all buttons
            height=50,  # Consistent height for all buttons
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color="#00734d",  # Consistent green color matching app theme
            hover_color="#005a3e",  # Slightly darker green on hover
            text_color="white",
            corner_radius=6  # Consistent rounded corners
        )
        return button
    
    def _create_report_pdf(self, pdf_path, add_preview_elements=True):
        """Common helper method to generate the PDF report
        
        Args:
            pdf_path: The path where the PDF should be saved
            add_preview_elements: Whether to add preview-specific elements (watermark, note)
        
        Returns:
            True if successful, False otherwise
        """
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

            # Section: Patient Information
            y_position = height - 110
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "Patient Information:")
            c.setFont("Helvetica", 12)

            # Patient details
            c.drawString(70, y_position - 20, f"Name: {self.app.patient_name.get()}")
            c.drawString(70, y_position - 35, f"Date of Birth: {self.app.dob.get()}")
            c.drawString(70, y_position - 50, f"Physician: {self.app.patient_doctor_var.get()}")
            
            # Adjust the y_position for the next section
            y_position -= 75

            # Section: Quantitative Measurements
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "Quantitative Measurements:")
            c.setFont("Helvetica", 12)
            airway_volume = getattr(self, "airway_volume", "13990.01 mm³")
            c.drawString(70, y_position - 20, f"Airway Volume: {airway_volume} cm³")

            # Section: Airflow Simulation Summary
            y_position -= 45
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "Airflow Simulation Summary:")
            c.setFont("Helvetica", 12)

            # Add flow rate information
            c.drawString(70, y_position - 20, f"Flow Rate: {self.flow_rate.get():.1f} LPM")
            c.drawString(70, y_position - 35, f"Air Density (ρ): 1.122 kg/m³")
            c.drawString(70, y_position - 50, f"Kinematic viscosity (ν): 1.539 x 10^-5 m²/s")
            c.drawString(70, y_position - 65, f"Initial velocity: 0 m/s (Initially at rest)")
            c.drawString(70, y_position - 80, f"Flow type: Turbulent")

            y_position -= 80

            # Note the simulation software version
            c.setFont("Helvetica", 12)
            c.drawString(70, y_position - 30, "Simulation performed using OpenFoam v2306.")

            # Move y_position for images (reduce excessive spacing)
            y_position -= 45

            # Add segmentation images side by side
            segmentation_img = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test/stl/IIB_2019-12-20_pred.png"
            processed_img = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test_1/Test Run/IIB_2019-12-20_assem.png"

            if os.path.exists(segmentation_img) and os.path.exists(processed_img):
                # Calculate center positions for better horizontal alignment
                first_image_x = (width - 200) / 2 - 100  # Center-left
                second_image_x = first_image_x + 250     # Center-right
                
                # Standard version (no white background)
                c.drawImage(segmentation_img, first_image_x, y_position - 120, width=200, height=120)
                c.drawImage(processed_img, second_image_x, y_position - 120, width=200, height=120)
                c.setFont("Helvetica-Oblique", 10)
                c.drawCentredString(first_image_x + 100, y_position - 130, "Figure 1: Initial Segmentation")
                c.drawCentredString(second_image_x + 100, y_position - 130, "Figure 2: Processed Segmentation")
            else:
                c.drawString(50, y_position - 30, "Segmentation images not found.")

            # Adjust y_position after segmentation images - reduce this value to move CFD section up
            y_position -= 150  # Changed from 170 to 150

            # CFD Simulation Results
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "CFD Simulation Results:")
            y_position -= 15
            c.setFont("Helvetica", 12)
            c.drawString(50, y_position, "Airflow velocity and pressure contours with a scale bar are shown below.")
            y_position -= 10

            # Add CFD Simulation Image - centered and moved up
            cfd_img = "/home/cfduser/Desktop/CFD_GUI/User_Data/amatos/Qadra Hussein/Test_1/Test Run/IIB_2019-12-20_CFD.png"
            if os.path.exists(cfd_img):
                cfd_x = (width - 200) / 2  # Center the CFD image
                cfd_y = y_position - 200   # Moved up by increasing value
                
                c.drawImage(cfd_img, cfd_x-70, cfd_y, width=400, height=200)
                c.setFont("Helvetica-Oblique", 10)
                c.drawCentredString(cfd_x + 150, cfd_y - 10, "Figure 3: CFD Simulation Contour Plot")
            else:
                c.drawString(75 if not add_preview_elements else 50, y_position - 30, "CFD simulation image not found.")

            # Add preview-specific elements
            if add_preview_elements:
                # Add a note that this is a preview
                c.setFont("Helvetica", 10)  # Use standard Helvetica
                c.setFillColorRGB(0.5, 0.5, 0.5)  # Dark gray
                c.drawString(50, 30, "This is a preview. Click 'Save Report as PDF' to save the final version.")

            # Save the PDF
            c.save()
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error generating PDF: {str(e)}")
            return False

    def _preview_report(self):
        """Generate and show a preview of the report directly in the application."""
        try:
            import tempfile
            
            # Create a temporary file for the preview
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_pdf_path = temp_file.name
            
            # Generate the report with preview elements
            if self._create_report_pdf(temp_pdf_path, add_preview_elements=False):
                # Store the path for reference when saving
                self.preview_pdf_path = temp_pdf_path
                
                # Create and show PDF Viewer dialog
                self._display_pdf_in_viewer(temp_pdf_path, is_preview=True)
                    
                # Enable the save button if it isn't already
                if self.export_button.cget("state") == "disabled":
                    self.export_button.configure(state="normal")
                    
                return True
            else:
                raise Exception("Failed to generate report PDF")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF preview:\n{str(e)}")
            return False

    def _generate_report(self, pdf_path, show_confirmation=True):
        """Generate and save a PDF report of the results with enhanced formatting."""
        try:
            # Generate the report without preview elements
            if self._create_report_pdf(pdf_path, add_preview_elements=False):
                # Store the path for future reference
                self.report_pdf_path = pdf_path
                
                # Show confirmation if requested
                if show_confirmation:
                    messagebox.showinfo("Save Complete", f"Report saved to:\n{pdf_path}")

                return True
            else:
                raise Exception("Failed to generate report PDF")
                
        except Exception as e:
            if show_confirmation:
                messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
            raise
        
    def _display_pdf_in_viewer(self, pdf_path, is_preview=False):
        """Display the PDF in an embedded viewer"""
        try:
            # Check if we need to import PyMuPDF first
            try:
                import fitz  # PyMuPDF
            except ImportError:
                response = messagebox.askquestion(
                    "Missing Dependency",
                    "The PDF viewer requires PyMuPDF (fitz) to be installed. "
                    "Would you like to continue with external viewer instead?"
                )
                if response == "yes":
                    # Fall back to external viewer
                    self._open_with_external_viewer(pdf_path)
                return

            # Create a new top-level window for the viewer
            if not hasattr(self, 'viewer_window') or not self.viewer_window.winfo_exists():
                self.viewer_window = ctk.CTkToplevel(self.app)
                self.viewer_window.title("Report Preview" if is_preview else "Report Viewer")
                self.viewer_window.geometry("780x1000")
                self.viewer_window.minsize(600, 800)
                
                # Make it modal (blocks interaction with main window)
                self.viewer_window.transient(self.app)
                self.viewer_window.grab_set()

                # Create PDF viewer frame and pass UI settings
                self.pdf_viewer = PDFViewerFrame(
                    self.viewer_window, 
                    ui_settings=UI_SETTINGS  # Pass your UI settings
                )
                self.pdf_viewer.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Set close callback to destroy the window
                self.pdf_viewer.set_close_callback(lambda: self.viewer_window.destroy())
                
                # Set window close protocol
                self.viewer_window.protocol("WM_DELETE_WINDOW", self.viewer_window.destroy)
            
            # Load the PDF
            self.pdf_viewer.load_pdf(pdf_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display PDF in viewer:\n{str(e)}")
            # Fall back to external viewer
            self._open_with_external_viewer(pdf_path)
    
    def _open_with_external_viewer(self, pdf_path):
        """Open PDF with external viewer as fallback"""
        try:
            import platform
            import subprocess
            import os
            
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", pdf_path])
            else:  # Linux and other
                subprocess.call(["xdg-open", pdf_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF with external viewer:\n{str(e)}")