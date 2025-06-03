# gui/tabs/tab4.py
import os
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageChops
from tkinter import ttk, messagebox, filedialog
import time
from pathlib import Path
import threading
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import platform
import subprocess
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering

import math
import shutil
import vtk
import tempfile
import fitz
import getpass
import glob
import re
import signal

from ..components.navigation import NavigationFrame2
from ..components.progress import ProgressSection
from ..components.forms import FormSection, ResultsFormSection
from ..components.pdf_viewer import PDFViewerFrame
from ..components.buttons import _create_info_button

from ..utils.segmentation import AirwaySegmentator
from ..utils.generate_airway_report import generate_airway_report
from ..utils.basic_utils import AppLogger
from ..utils.icons import create_icon, load_ctk_icon
from ..utils.open3d_viewer import Open3DViewer
from ..utils.blender_processor import BlenderProcessor
from ..utils.stl_assem_image_render import render_assembly

from gui.config.settings import UI_SETTINGS, TAB4_UI, TAB4_SETTINGS, PATH_SETTINGS


class Tab4Manager:
    def __init__(self, app):
        """Initialize Tab4Manager with a reference to the main app"""
        self.app = app
        self.processing_active = False
        self.logger = AppLogger()  # Initialize logger
        self.render_images = {}  
        self.cancel_requested = False
        self.current_process = None
        self.min_csa = None
        self.flow_rate = ctk.DoubleVar(value=10)
        self.viewer = Open3DViewer(logger=self.logger)
        self.blender_processor = BlenderProcessor(
            logger=self.logger,
            progress_callback=self.update_progress,
            cancel_check_callback=lambda: self.cancel_requested
        )

        # Add a cancellation flag that threads can check
        self.cancel_requested = False
        # Keep track of processing thread
        self.processing_thread = None
    
    def _refresh_patient_info(self):
        """Fetch and store key patient-related variables for easier access."""
        self.patient_name = self._safe_get_var("patient_name")
        self.dob = self._safe_get_var("dob")
        self.physician = self._safe_get_var("patient_doctor_var")
        self.scan_date = getattr(self.app, "scan_date", "No Date")

    def _safe_get_var(self, attr_name):
        """Helper to safely get a StringVar value from the app."""
        var = getattr(self.app, attr_name, None)
        return var.get() if var else ""
        
    def create_tab(self):
        # Create the main tab/frame
        self.tab = ctk.CTkFrame(self.app.main_frame)
        self.tab.pack(fill="both", expand=True)
        
        # Then create other elements INSIDE self.tab
        self._create_header()
        self._create_main_content()
        self._create_navigation()

    def _create_header(self):
        """Create the header with home button and context information with shading"""
        # Change parent from self.app.main_frame to self.tab
        top_frame = ctk.CTkFrame(self.tab, corner_radius=10, fg_color="transparent")
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
            width=UI_SETTINGS["HOME_BUTTON"]["WIDTH"],
            height=UI_SETTINGS["HOME_BUTTON"]["HEIGHT"],
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
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
    
    def _confirm_shutdown(self):
        """Ask the user – then shut the machine down."""
        if messagebox.askyesno(
            "Confirm Shutdown",
            "Are you sure you want to shut down the computer?"
        ):
            self.logger.log_info("User confirmed shutdown")
            # First cancel any ongoing processes
            if hasattr(self, 'progress_section') and self.progress_section._cancel_callback_func:
                self.progress_section._cancel_callback_func()
            # Clean up
            self._cleanup_before_shutdown()
            os.system("sudo /sbin/poweroff")

    def _cleanup_before_shutdown(self):
        """Perform cleanup operations before shutdown."""
        # Log the action
        self.logger.log_info("Cleaning up before shutdown")
        # Sync disk
        subprocess.call(["sync"])
        # Kill processes
        for p in ["nnUNet", "blender", "paraview", "python", "snappyHexMesh", "simpleFoam"]:
            try:
                subprocess.call(["killall", "-f", p])
            except:
                pass
        # Final sync
        subprocess.call(["sync"])
    
    def _confirm_restart(self):
        """Ask the user – then reboot."""
        if messagebox.askyesno(
            "Confirm Restart",
            "Are you sure you want to restart the computer?"
        ):
            self.logger.log_info("User confirmed restart")
            # on Linux; on Windows you might use "shutdown /r /t 0"
            self._cleanup_before_shutdown()
            os.system("reboot")
    
    def _create_navigation(self):
        """Create navigation with only a Back button in the style of NavigationFrame"""
        # Create navigation frame as a direct child of self.tab
        self.nav_frame = NavigationFrame2(
            parent=self.tab,
            previous_label="Patient Info Review",
            back_command=self._confirm_back
        )
        
        # Use NavigationFrame2's built-in methods 
        self.nav_frame.add_shutdown_restart_buttons()

    def _confirm_back(self):
        """Prompt the user for confirmation before going back if analysis data exists."""
        # Check if analysis is in progress or results exist
        if self._should_confirm_navigation():
            response = messagebox.askyesno(
                "Confirm Navigation",
                "An analysis is in progress. Going back will erase all data. Proceed?"
            )
            if not response:
                return

            # 1) invoke the same cancel logic as your Cancel buttont
            if self.progress_section._cancel_callback_func:
                self.progress_section._cancel_callback_func()

            # 2) clear any lingering state (just in case)
            self._reset_processing_state()

        # now actually navigate back
        self.app.create_tab3()

    def _confirm_home(self):
        if self._should_confirm_navigation():
            if messagebox.askyesno("Confirm Navigation",
                                   "Analysis in progress. Going Home will erase it. Proceed?"):
                if self.progress_section._cancel_callback_func:
                    self.progress_section._cancel_callback_func()
                self._reset_processing_state()
            else:
                return
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
        content_frame = ctk.CTkFrame(self.tab, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        # Create left and right frames
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(20,2), pady=5, sticky="nsew")

        right_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=(2,20), pady=5, sticky="nsew")

        # Configure grid weights for resizing
        content_frame.grid_columnconfigure(0, weight=1, minsize=200)
        content_frame.grid_columnconfigure(1, weight=4)
        content_frame.grid_rowconfigure(0, weight=1)

        # --- Instructions guide (Tab2 style) ---
        guide_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        guide_frame.pack(fill="x", pady=(0, UI_SETTINGS["PADDING"]["MEDIUM"]))

        ctk.CTkLabel(
            guide_frame,
            text="Instructions",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            wraplength=690,
            justify="left"
        ).pack(anchor="w", pady=(0, 5))

        instructions = [
            "1. Choose an analysis type:",
            "   – Upper Airway Segmentation: generate airway prediction from \n\tDICOM/NIfTI.\n"
            "   – Airflow Simulation: segmentation plus airflow & pressure simulation.\n\tSelect flow rate by dragging slider or typing number in box.",
            "2. Click 'Start Processing'.\n3. Switch between the Segmentation, Post‑processed Geometry, \n\tand CFD Simulation tabs to see the results once completed.",
            "4. Click on 3D render buttons to inspect predicted and post-processed \n\tgeometries more closely.",
            "5. Click “Preview Report” to open a PDF preview of your results.\n6. Click “Save Data” to export results/report to external drive."
        ]
        for instr in instructions:
            ctk.CTkLabel(
                guide_frame,
                text=instr,
                wraplength=650,
                font=UI_SETTINGS["FONTS"]["SMALL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                justify="left"
            ).pack(anchor="w", padx=20)
        # ----------------------------------------

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
                "Segmentation + Airflow Simulation"
            ],
            command=self._update_processing_details,
            width=TAB4_UI["ANALYSIS_TYPE_MENU"]["WIDTH"],
            dropdown_font=UI_SETTINGS["FONTS"]["NORMAL"],
            height=TAB4_UI["ANALYSIS_TYPE_MENU"]["HEIGHT"],
            font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"]
        )
        analysis_dropdown.pack(pady=(5, 10))

        # Processing details label
        self.processing_details_label = ctk.CTkLabel(
            analysis_section.content,
            text="",
            font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
            wraplength=550,
            justify="center"
        )
        self.processing_details_label.pack(pady=(0, 5))

        # Create flow rate frame (initially hidden)
        self.flow_rate_frame = ctk.CTkFrame(analysis_section.content, fg_color="transparent")
        # show it in the same spot you were before
        self.flow_rate_frame.pack(fill="x", pady=(5, 10))

        # Label + slider + entry + unit + info button all side by side
        flow_rate_title = ctk.CTkLabel(
            self.flow_rate_frame,
            text="Breathing Rate or Flow Rate:",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            anchor="w"
        )
        flow_rate_title.pack(side="left", padx=(0, 10))

        # Slider
        self.flow_rate_slider = ctk.CTkSlider(
            self.flow_rate_frame,
            from_=5,
            to=150.0,
            number_of_steps=29,
            variable=self.flow_rate,
            width=220,
            command=self._update_flow_rate_label
        )
        self.flow_rate_slider.pack(side="left", padx=(0, 10))

        # Entry
        self.flow_rate_entry = ctk.CTkEntry(
            self.flow_rate_frame,
            width=60,
            height=30,
            justify="right",
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        )
        self.flow_rate_entry.pack(side="left", padx=(0, 5))
        self.flow_rate_entry.insert(0, f"{self.flow_rate.get():.1f}")
        self.flow_rate_entry.bind("<FocusOut>", self._validate_flow_rate_entry)
        self.flow_rate_entry.bind("<Return>", self._validate_flow_rate_entry)
        self.flow_rate_entry.bind("<KeyRelease>", self._update_slider_on_keyrelease)

        # Unit + info button
        unit_label = ctk.CTkLabel(self.flow_rate_frame, text="LPM", font=UI_SETTINGS["FONTS"]["NORMAL"])
        unit_label.pack(side="left", padx=(0, 5))

        lpm_info_button = _create_info_button(
            self.flow_rate_frame,
            "LPM = Litres Per Minute\nThis is a volumetric measure of the breathing rate commonly used in respiratory medicine.\nWARNING: Simulations were experimentally validated only up to 90 LPM"
        )
        lpm_info_button.pack(side="left",padx=2)

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
            if value < 1.0 or value > 150.0:
                # Show notification to user
                messagebox = tk.messagebox
                messagebox.showwarning(
                    "Invalid Flow Rate", 
                    "Please enter a value between 5.0 and 150.0 LPM"
                )
                
                # Reset to current value or nearest valid value
                if value < 0.10:
                    value = 0.1
                elif value > 150.0:
                    value = 150.0
            
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
            height=55,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"]
        )
        self.process_button.pack(pady=(2,2))

        # Progress section
        self.progress_section = ProgressSection(processing_section.content)
        self.progress_section.pack(fill="x", pady=(0,2))

    def _create_results_section(self, parent, active=False):
        """Create the Results section; gray it out if not active."""
        # gray background vs. normal
        bg = (UI_SETTINGS["COLORS"]["SECTION_ACTIVE"]
            if active
            else UI_SETTINGS["COLORS"]["SECTION_INACTIVE"])
        results_section = ResultsFormSection(parent, "Results", fg_color=bg)
        results_section.pack(fill="both", padx=20, pady=5, expand=True)
        self.results_section_frame = results_section  # keep for activation

        # description label color
        self.results_description = ctk.CTkLabel(
            results_section.content,
            text="Switch between tabs to view different analysis stages…",
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=(UI_SETTINGS["COLORS"]["TEXT_DARK"]
                        if active
                        else UI_SETTINGS["COLORS"]["TEXT_DISABLED"]),
            wraplength=600,
            justify="center"
        )
        self.results_description.pack(pady=(5, 2))

        notebook_frame = results_section.content

        # Create a container for the notebook
        notebook_container = ctk.CTkFrame(notebook_frame, width=1100, height=400,
                                        fg_color=results_section.content.cget("fg_color"))
        notebook_container.pack(pady=(3, 5), fill="both", expand=True)
        notebook_container.pack_propagate(False)

        # Define tab colors
        self.tab_colors = {
            "Segmentation": "#00734d",     # Green for segmentation
            "Post-processed Geometry": "#006a9f",    # Blue for post-processed
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
            "Post-processed Geometry": self.postprocessing_frame,
            "CFD Simulation": self.cfd_frame
        }
        
        # Create the tab buttons with even spacing
        tab_names = ["Segmentation", "Post-processed Geometry", "CFD Simulation"]
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

        # ── after all buttons exist, disable them if not active ──
        if not active:
            for btn in self.tab_buttons.values():
                btn.configure(
                    state="disabled",
                    fg_color=UI_SETTINGS["COLORS"]["DISABLED_BUTTON"],
                    text_color=UI_SETTINGS["COLORS"]["TEXT_DISABLED"],
                    hover_color=UI_SETTINGS["COLORS"]["DISABLED_BUTTON"]
                )
        # Default to first tab (Segmentation) initially selected
        self._select_tab("Segmentation")
        
        # Create a frame for the buttons along the bottom
        button_frame = ctk.CTkFrame(results_section, fg_color=results_section.cget("fg_color"))
        button_frame.pack(side="bottom", fill="x", padx=20, pady=10)

        # Preview button
        eye_icon = load_ctk_icon("eye", width=32)
        self.preview_button = ctk.CTkButton(
            button_frame,
            text="Preview Report",
            image=eye_icon,
            compound="left",
            command=self._preview_report,
            width=250,
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            state="disabled"
        )
        self.preview_button.pack(side="left", padx=(0, 5), fill="x", expand=True)

        # Save Results to Drive button
        drive_icon = create_icon("save", (24, 24))
        drive_icon = ctk.CTkImage(light_image=drive_icon, dark_image=drive_icon, size=(24, 24))
        self.export_button = ctk.CTkButton(
            button_frame,
            text="Save Results to Drive",
            image=drive_icon,
            compound="left",
            command=self._save_results_to_drive,
            width=250, 
            height=40,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["REG_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["REG_HOVER"],
            state="disabled"
        )
        self.export_button.pack(side="left", fill="x", expand=True)

        
        return results_section
    
    def _activate_results_section(self):
        """Enable and recolor the Results section once processing is done."""
        # 1. Recolor the Results container
        self.results_section_frame.configure(
            fg_color=UI_SETTINGS["COLORS"]["SECTION_ACTIVE"]
        )

        # 2. Restore description text color
        self.results_description.configure(
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        )

        # 3. Re‑enable each tab button with its original colors
        for name, btn in self.tab_buttons.items():
            btn.configure(
                state="normal",
                fg_color="#d9d9d9",
                text_color="#505050",
                hover_color=self.tab_colors[name]
            )
        
        # 4. Re-apply the selected
        self._select_tab(getattr(self, "current_tab", "Segmentation"))

    def _select_tab(self, tab_name):
        """Select a tab and update styling with enhanced visual cues."""
        # Make sure we have the tab frames initialized
        self.current_tab = tab_name
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


    def _update_processing_details(self, choice):
        """Update the processing details based on selected analysis type"""
        details = {
            "Upper Airway Segmentation": 
                "This will perform automatic segmentation of the upper airway "
                "from the DICOM images.",
            
            "Segmentation + Airflow Simulation":
                "This will first perform airway segmentation, followed by CFD "
                "analysis to simulate airflow patterns and pressure changes."
        }
        
        self.processing_details_label.configure(
            text=details.get(choice, "Please select an analysis type to proceed.")
        )
        
        # Show/hide flow rate controls based on selection
        if choice == "Segmentation + Airflow Simulation":
            self.flow_rate_frame.pack(fill="x", pady=(5, 10))
        else:
            self.flow_rate_frame.pack_forget()

    def _validate_and_start_processing(self):
        """Validate selection and start processing, skipping segmentation if STL already exists"""
        if self.processing_active:
            return

        if self.analysis_option.get() == "Select Analysis Type":
            messagebox.showerror("Error", "Please select an analysis type before proceeding.")
            return

        # Validate input files exist - DICOM or NIfTI
        has_dicom = hasattr(self.app, 'selected_dicom_folder') and self.app.selected_dicom_folder
        has_nifti = hasattr(self.app, 'selected_files') and any(f.lower().endswith(('.nii', '.nii.gz')) 
                                                            for f in self.app.selected_files)
        
        # Check if segmentation already exists (STL files in stl folder)
        has_existing_segmentation = self._segmentation_results_exist()
        
        # Only validate inputs if we don't have existing segmentation results
        if not has_existing_segmentation and not (has_dicom or has_nifti):
            messagebox.showerror("Error", "No input files specified. Please return to the patient information page and select DICOM or NIfTI files.")
            return

        # Validate folder path exists
        if not hasattr(self.app, 'full_folder_path'):
            messagebox.showerror("Error", "No output folder specified. Please return to the patient information page and try again.")
            return

        # If "Segmentation only" and results already exist, offer to reuse
        if self.analysis_option.get() == "Upper Airway Segmentation":
            if has_existing_segmentation:
                reuse = self._show_custom_dialog(
                    title="Existing Segmentation Found",
                    message="You've already run segmentation here. Use existing results?",
                    icon="question"
                )
                if reuse:
                    self._load_existing_segmentation()
                    return

        # For airflow simulation, check if results already exist for this flow rate
        if "Simulation" in self.analysis_option.get():
            if has_existing_segmentation:
                # If we have segmentation but need to run CFD, inform the user we'll reuse segmentation
                self.logger.log_info("Existing segmentation found, will skip to CFD simulation")
            
            if self._cfd_results_exist():
                # Results already exist - ask if user wants to use existing results
                flow_str = f"{self.flow_rate.get():.1f}"
                
                response = self._show_custom_dialog(
                    title="Existing Results Found",
                    message=f"CFD results for flow rate {flow_str} LPM already exist. Would you like to use these existing results instead of running a new simulation?",
                    icon="question"
                )
                
                if response:  # User clicked Yes
                    # Use existing results
                    self._load_existing_cfd()
                    return

        # Show confirmation dialog focused on analysis type
        analysis_type = self.analysis_option.get()
        message = f"Would you like to proceed with {analysis_type}?\n\n"
        
        # Add skip segmentation info if segmentation results exist
        segmentation_status = "Skip segmentation (using existing results)" if has_existing_segmentation else ("Use NIfTI data directly" if has_nifti else "Perform airway segmentation")
        
        if "Simulation" in analysis_type:
            message += f"This will:\n" \
                    f"1. {segmentation_status}\n" \
                    f"2. Generate 3D model (in STL format)\n" \
                    f"3. Calculate airway volume in (mm³)\n" \
                    f"4. Generate 3D mesh\n" \
                    f"5. Run CFD simulation at {self.flow_rate.get():.1f} LPM\n" \
                    f"6. Provide pressure and velocity images of the 3D-scanned model"
        else:
            message += "This will:\n" \
                    f"1. {segmentation_status}\n" \
                    f"2. Generate 3D model (in STL format)\n" \
                    f"3. Calculate airway volume in (mm³)"
        
        # Use the custom dialog approach
        final_response = self._show_custom_dialog(
            title="Confirm Analysis",
            message=message,
            icon="question"
        )
        
        if final_response:  # User clicked Yes
            # Create a single unified cancel handler that will be maintained
            self.unified_cancel_handler = self._create_unified_cancel_handler()
            
            # Set up the unified cancel handler for the progress section
            self.progress_section.set_cancel_callback(self.unified_cancel_handler)
            
            # Initialize render_images if it doesn't exist
            if not hasattr(self, 'render_images'):
                self.render_images = {}
                
            # Reset cancellation flag before starting
            self.cancel_requested = False
            
            # Initialize empty list for scheduled update IDs
            self.scheduled_updates = []

            # Create a unified cancel handler
            unified_cancel_handler = self._create_unified_cancel_handler()

            # Set up the unified cancel handler for the progress section
            self.progress_section.set_cancel_callback(unified_cancel_handler)
            
            # Start processing with knowledge of existing segmentation
            self._start_processing(skip_segmentation=has_existing_segmentation)

    def _show_custom_dialog(self, title, message, icon="info"):
        """
        Display a custom dialog with larger text and return True for Yes, False for No.
        This is a safer implementation that avoids Tcl grab errors.
        """
        # Create a new dialog window
        dialog = tk.Toplevel(self.app)
        dialog.title(title)
        dialog.geometry("650x400")  # Large enough for all content
        dialog.minsize(500, 300)
        dialog.resizable(False, False)
        dialog.wm_attributes("-type", "dialog")
        
        # Make sure window is created and updated before further actions
        dialog.update()
        
        # Set modal behavior after window is updated
        dialog.transient(self.app)
        
        # Add padding
        content_frame = tk.Frame(dialog, padx=25, pady=15)
        content_frame.pack(fill="both", expand=True)
        
        # Add message
        message_label = tk.Label(
            content_frame,
            text=message,
            font=UI_SETTINGS["FONTS"]["SMALL"],
            justify="left",
            wraplength=550
        )
        message_label.pack(fill="both", expand=True, pady=(0, 20))
        
        # Add buttons
        button_frame = tk.Frame(content_frame)
        button_frame.pack(pady=(0, 15))
        
        result = [False]  # Use a list to store result by reference
        
        def on_yes():
            result[0] = True
            dialog.destroy()
        
        def on_no():
            result[0] = False
            dialog.destroy()
        
        yes_button = tk.Button(
            button_frame,
            text="Yes",
            font=("Arial", 12, "bold"),
            width=10,
            command=on_yes,
            bg="#007bff" if icon != "warning" else "#ff9800",
            fg="white"
        )
        yes_button.pack(side="left", padx=10)
        
        no_button = tk.Button(
            button_frame,
            text="No",
            font=("Arial", 12),
            width=10,
            command=on_no
        )
        no_button.pack(side="left", padx=10)
        
        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Wait until this window is destroyed
        dialog.wait_window()
        
        return result[0]

    def _start_processing(self, skip_segmentation=False):
        """
        Start the processing sequence for either DICOM or NIfTI input.
        If skip_segmentation is True, will skip segmentation and go straight to CFD.
        """
        try:
            # If skipping segmentation, go straight to post-segmentation workflow
            if skip_segmentation and "Simulation" in self.analysis_option.get():
                self._handle_existing_segmentation_for_cfd()
                return
                
            # Determine if we're using DICOM or NIfTI files
            has_dicom = hasattr(self.app, 'selected_dicom_folder') and self.app.selected_dicom_folder
            has_nifti = hasattr(self.app, 'selected_files') and any(f.lower().endswith(('.nii', '.nii.gz')) 
                                                                for f in self.app.selected_files)

            # Get NIfTI file path if present
            nifti_file = None
            if has_nifti:
                nifti_files = [f for f in self.app.selected_files if f.lower().endswith(('.nii', '.nii.gz'))]
                if nifti_files:
                    nifti_file = nifti_files[0]
            
            # Ensure output folder exists
            os.makedirs(self.app.full_folder_path, exist_ok=True)
            
            self.processing_active = True
            self.process_button.configure(state="disabled")

            # Set the cancel callback to enable the dedicated cancel button
            self.progress_section.set_cancel_callback(self._request_cancel)

            # immediately activate the Results area
            # (Tabs will show placeholders until each stage renders)
            self._activate_results_section()
            
            def progress_callback(message, percentage, output_line=None):
                """Update progress bar and message"""
                # Use after() to ensure thread safety when updating GUI
                self.app.after(0, lambda: self.progress_section.update_progress(
                    percentage,
                    message=message,
                    output_line=output_line
                ))
            
            # Initialize processor with the appropriate input
            if has_nifti and nifti_file:
                # For NIfTI input, pass the NIfTI file directly  
                processor = AirwaySegmentator(
                    input_file=nifti_file,  # Pass the file path instead of folder
                    output_folder=self.app.full_folder_path,
                    callback=progress_callback,
                    input_type="nifti"  # Specify input type
                )
            elif has_dicom:
                # For DICOM input, use the existing method
                processor = AirwaySegmentator(
                    input_folder=self.app.selected_dicom_folder,
                    output_folder=self.app.full_folder_path,
                    callback=progress_callback,
                    input_type="dicom"  # Specify input type
                )
            else:
                raise ValueError("No valid input files found")
            
            # Set up cancel callback with processor support
            self.progress_section.set_cancel_callback(
                self._create_unified_cancel_handler(processor=processor)
            )

            def cancel_processing():
                """Cancel the processing and stop the progress bar"""
                self.cancel_requested = True
                if processor.cancel_processing():
                    # Ensure the progress bar animation is stopped
                    self.app.after(0, lambda: self.progress_section.stop("Processing Cancelled"))
                    # Reset the processing flag
                    self.app.after(0, lambda: self._reset_processing_state())
                    # Re-enable the Start button
                    self.app.after(0, lambda: self.process_button.configure(state="normal"))
                        
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
                    
                    # Run the processing - using the updated processor that handles both input types
                    results = processor.process()

                    # Ensure cancel button is enabled by setting callback AFTER start
                    self.app.after(100, lambda: self.progress_section.set_cancel_callback(self._request_cancel))
        
                    
                    # Check if process was cancelled before proceeding
                    if self.cancel_requested:
                        self.app.after(0, lambda: self.progress_section.stop("Processing cancelled"))
                        self.app.after(0, lambda: self.process_button.configure(state="normal"))
                        self.app.after(0, lambda: self._reset_processing_state())
                        return
                    
                    # Schedule completion handling in main thread
                    self.app.after(0, lambda: self._handle_processing_completion(True, results))

                except RuntimeError as e:
                    # nnUNet is already stopped so just clean up the UI:
                    self.app.after(0, lambda: self.progress_section.stop("Processing cancelled"))
                    self.app.after(0, lambda: self.process_button.configure(state="normal"))
                    self.app.after(0, self._reset_processing_state)
                    return

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
            
            # Store reference to the thread
            self.processing_thread = thread
            
        except Exception as e:
            self.processing_active = False
            self.process_button.configure(state="normal")
            messagebox.showerror("Error", f"Failed to start processing:\n{str(e)}")

    def _handle_existing_segmentation_for_cfd(self):
        """Handle workflow when using existing segmentation for CFD simulation - updated"""
        try:
            # Start the processing UI
            self.processing_active = True
            self.process_button.configure(state="disabled")
            self.progress_section.start("Using existing segmentation for CFD...", indeterminate=True)
            
            # Activate results section
            self._activate_results_section()
            
            # Refresh patient info
            self._refresh_patient_info()
            
            # Find the STL file in the stl folder
            stl_folder = Path(self.app.full_folder_path) / "stl"
            stl_files = list(stl_folder.glob("*_geo.stl"))
            if not stl_files:  # Try more general pattern if specific naming not found
                stl_files = list(stl_folder.glob("*.stl"))
                
            if not stl_files:
                raise FileNotFoundError("No STL files found in the stl folder.")
                
            stl_path = str(stl_files[0])
            self.current_stl_path = stl_path
            self.logger.log_info(f"Using existing STL: {stl_path}")
            
            # Get the preview image if it exists
            preview_images = list(stl_folder.glob("*_geo.png"))
            if not preview_images:
                preview_images = list(stl_folder.glob("*.png"))  # Try more general pattern
                
            if preview_images:
                self._update_render_display("segmentation", str(preview_images[0]))
                self.logger.log_info(f"Using existing preview image: {preview_images[0]}")
            
            # Try to load the airway volume
            volume_file = Path(self.app.full_folder_path) / "volume_calculation.txt"
            if volume_file.exists():
                with open(volume_file, 'r') as f:
                    volume_str = f.read().strip()
                    self.airway_volume = float(volume_str) if volume_str.replace('.', '', 1).isdigit() else volume_str
                    self.logger.log_info(f"Loaded airway volume: {self.airway_volume}")
            
            # Look for min CSA
            min_csa_path = Path(self.app.full_folder_path) / "min_csa.txt"
            if min_csa_path.exists():
                text = min_csa_path.read_text()
                # find the first floating-point or integer in the text
                m = re.search(r"[-+]?\d*\.?\d+", text)
                if m:
                    self.min_csa = float(m.group(0))
                    self.logger.log_info(f"Loaded min CSA: {self.min_csa}")
            
            # Update progress
            self.progress_section.update_progress(
                30,
                "Loaded existing segmentation, proceeding to CFD...",
                "Using existing segmentation to proceed with CFD simulation"
            )
            
            # Select segmentation tab to show loaded data
            self._select_tab("Segmentation")
            
            # Proceed directly to Blender stage for CFD processing using the new processor
            self.update_progress("Creating inlet and outlet in Blender…", 50, "Creating inlet and outlet in Blender…")
            
            # Set up a CFD output directory based on flow rate
            cfd_output_dir = str(self._get_full_cfd_path())
            
            # Reset cancellation flag before starting Blender
            self.cancel_requested = False
            
            # Use the new Blender processor instead of the old worker method
            self._start_blender_processing(self.current_stl_path, cfd_output_dir)
            
        except Exception as e:
            error_msg = f"Error using existing segmentation: {str(e)}"
            self.logger.log_error(error_msg)
            messagebox.showerror("Error", error_msg)
            
            # Reset processing state
            self.processing_active = False
            self.progress_section.stop("Error in processing")
            self.process_button.configure(state="normal")

    def _reset_processing_state(self):
        """Reset all processing state variables and update UI accordingly"""
        # Add a guard for concurrent resets
        if hasattr(self, '_reset_in_progress') and self._reset_in_progress:
            return
            
        self._reset_in_progress = True
        
        # Only call stop() if we haven't already done so
        if not hasattr(self, '_cancellation_processed') or not self._cancellation_processed:
            self.progress_section.stop("Processing Cancelled")
            self._cancellation_processed = True
        
        self.processing_active = False
        self.cancel_requested = False
        self.current_process = None
        
        # Clear any scheduled updates
        if hasattr(self, 'scheduled_updates'):
            for after_id in self.scheduled_updates:
                try:
                    self.app.after_cancel(after_id)
                except:
                    pass
            self.scheduled_updates = []
        
        # Reset progress section callback
        self.progress_section.set_cancel_callback(None)
        
        # Reset process button
        self.process_button.configure(
            text="Start Processing", 
            state="normal", 
            command=self._validate_and_start_processing
        )
        
        # Clear the reset guard after a short delay
        self.app.after(500, lambda: setattr(self, '_reset_in_progress', False))
    
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

        self.processing_active = False
        self.process_button.configure(state="normal")
        self.progress_section.stop("Processing complete!")

        # ★ Activate the Results section now that we have output ★
        self._activate_results_section()

        # Enable the Preview and Export buttons (this was already here)
        self.preview_button.configure(state="normal")
        self.export_button.configure(state="normal")
        
        # Enable the Preview and Export buttons
        self.preview_button.configure(state="normal")
        self.export_button.configure(state="normal")
        
        # Populate all tabs with content
        self.app.update_idletasks()  # Force UI update before rendering tabs
        
        # Segmentation tab
        segmentation_path = None
        if hasattr(self.app, 'full_folder_path'):
            # Look in the stl subfolder
            stl_folder = Path(self.app.full_folder_path) / "stl"
            if stl_folder.exists():
                # Look for prediction images in the stl folder
                pred_images = list(stl_folder.glob("*_geo.png"))
                if pred_images:
                    segmentation_path = str(pred_images[0])
        
        # If simulation was selected, populate other tabs
        if "Simulation" in self.analysis_option.get():
            # Get paths based on selected flow rate
            cfd_base_path = self._get_full_cfd_path()
            # Post-processed tab - look for any assembly image in triSurface folder
            tri_surface_path = Path(cfd_base_path) / "constant" / "triSurface"
            assem = list(tri_surface_path.glob("*_assem.png"))
            if not assem:
                assem = list(tri_surface_path.glob("*assembly.png"))
            postprocessed_path = str(assem[0]) if assem else None
            self._update_render_display("postprocessing", postprocessed_path)
            
            # CFD tab - look for any CFD image
            cfd_files = list(Path(cfd_base_path).glob("*_CFD.png"))
            cfd_path = str(cfd_files[0]) if cfd_files else None
            self._update_render_display("cfd", cfd_path)
            
            # Select CFD tab as it's the final result
            self._select_tab("CFD Simulation")

            self.update_progress(
                "Processing complete!...",
                100,
                "Processing complete!..."
            )

        else:
            # Just select the segmentation tab
            self._select_tab("Segmentation")

    
    def _handle_processing_completion(self, success, results):
        """Handle completion of processing - updated to use new Blender processor"""
        self._refresh_patient_info()
        try:
            if not success:
                # Display error message
                error_message = results if isinstance(results, str) else "Unknown error occurred"
                messagebox.showerror(
                    "Error",
                    f"Processing failed:\n{error_message}"
                )
                # Log the error
                self.logger.log_error(f"Processing failed: {error_message}")
                
                # Reset processing state
                self.processing_active = False
                self.process_button.configure(state="normal")
                return
            
            # Log the full results structure to debug
            self.logger.log_info(f"Results structure: {results}")

            # Extract STL path correctly
            if isinstance(results['stl_path'], dict) and 'stl_path' in results['stl_path']:
                stl_path = results['stl_path']['stl_path']
            else:
                stl_path = results['stl_path']
                
            self.logger.log_info(f"Using STL path: {stl_path}")

            # Verify the STL file exists
            if not os.path.exists(stl_path):
                self.logger.log_error(f"STL file does not exist: {stl_path}")
                messagebox.showerror("Error", f"STL file not found at: {stl_path}")
                return
                
            # Store the STL path for later use
            self.current_stl_path = stl_path

            # Store the airway volume for use in reports
            self.airway_volume = results['volume']

            # Store the airway min csa for use in reports
            self.min_csa = results['stl_path']['min_csa']

            # Show segmentation result immediately
            if 'preview_path' in results['stl_path'] and os.path.exists(results['stl_path']['preview_path']):
                self._update_render_display("segmentation", results['stl_path']['preview_path'])
            else:
                messagebox.showwarning("Warning", "Preview image not found. Using default visualization.")
                self._update_render_display("segmentation", None)
            
            # Only activate Segmentation tab for now
            self._select_tab("Segmentation")
            
            # Enable the Preview and Export buttons only after segmentation
            # but disable them for now if we're doing a simulation (will be enabled later)
            if "Simulation" in self.analysis_option.get():
                self.preview_button.configure(state="disabled")
                self.export_button.configure(state="disabled")
            else:
                self.preview_button.configure(state="normal")
                self.export_button.configure(state="normal")
            
            # If airflow simulation was selected, proceed with simulation processing
            if "Simulation" in self.analysis_option.get() and not self.cancel_requested:
                # disable button so user can't re-click
                self.process_button.configure(state="disabled")
                self.progress_section.start(
                    "Creating inlet and outlet in Blender…",
                    indeterminate=True
                )

                # Use the new Blender processor instead of the old method
                cfd_output_dir = str(self._get_full_cfd_path())
                self._start_blender_processing(stl_path, cfd_output_dir)
            
            else:
                # Segmentation only - just finalize and show message
                self.progress_section.stop("Processing Complete!")
                
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
                
                # Finalize processing for segmentation only
                self._finalize_processing()
                
                # Just select the segmentation tab
                self._select_tab("Segmentation")
                
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self.logger.log_error(f"Unexpected error in processing completion: {str(e)}")
            
            # Reset processing state
            self.processing_active = False
            self.process_button.configure(state="normal")
    
    def _on_worker_error(self, stage, error_message):
        messagebox.showerror(f"{stage} Error", error_message)
        self._reset_processing_state()
    
    def _request_cancel(self):
        """Centralized cancellation method that handles all running processes"""
        # Only proceed if not already cancelled
        if not self.cancel_requested:
            self.cancel_requested = True
            self._cancellation_processed = True
            self.logger.log_info("Cancellation requested by user")
            
            # Terminate the main process if it exists
            if hasattr(self, 'current_process') and self.current_process and self.current_process.poll() is None:
                try:
                    self.logger.log_info("Terminating current process")
                    self.current_process.terminate()
                    try:
                        self.current_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.logger.log_info("Process did not terminate, killing it")
                        self.current_process.kill()
                except Exception as e:
                    self.logger.log_error(f"Error terminating process: {e}")
            
            # Update progress section - Stop the progress bar immediately
            self.progress_section.stop("Processing cancelled")
            
            # Add a log message here to verify execution flow
            self.logger.log_info("About to call _delete_cancelled_files from _request_cancel")
            
            # Schedule file cleanup with a short delay so the UI can update
            # Use a lambda to ensure direct method call
            self.app.after(3000, lambda: self._delete_cancelled_files())
            
            # Reset processing state after cleanup is done
            self.app.after(800, self._reset_processing_state)
    
    def _create_unified_cancel_handler(self, processor=None):
        """
        Creates a unified cancellation handler that can be used throughout the application.
        Returns a callback function that can be assigned to the progress section.
        """
        def unified_cancel_handler():
            """
            Universal cancellation handler that terminates any active process
            and resets the UI state appropriately.
            """
            self.logger.log_info("Cancellation requested by user")
            
            # Set the cancellation flag
            self.cancel_requested = True
            
            # Track cleanup information
            cleanup_info = None

            # Processor-specific cancellation (for segmentation)
            if processor is not None:
                if hasattr(processor, 'cancel_event'):
                    processor.cancel_event.set()
                
                if hasattr(processor, 'cancel_processing'):
                    self.logger.log_info("Calling cancel_processing on processor")
                    cleanup_info = processor.cancel_processing()
                    
                    # Log the returned info if any
                    if cleanup_info:
                        self.logger.log_info(f"Received cleanup info: {cleanup_info}")
            
            # Cancel Blender processor if it's running
            if hasattr(self, 'blender_processor'):
                self.blender_processor.request_cancel()
            
            # Terminate any active subprocess
            if hasattr(self, 'current_process') and self.current_process and self.current_process.poll() is None:
                self.logger.log_info("Terminating active subprocess...")
                try:
                    os.killpg(self.current_process.pid, signal.SIGTERM)
                    try:
                        self.current_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.logger.log_info("Subprocess didn't terminate, killing it...")
                        os.killpg(self.current_process.pid, signal.SIGKILL)
                except Exception as e:
                    self.logger.log_error(f"Error killing process group: {e}")
                    # Fall back to regular termination
                    try:
                        self.current_process.terminate()
                        self.current_process.wait(timeout=5)
                    except:
                        self.current_process.kill()
            
            # Also terminate Python subprocess if it exists
            if hasattr(self, 'current_subprocess') and self.current_subprocess and self.current_subprocess.poll() is None:
                self.logger.log_info("Terminating Python subprocess...")
                self.current_subprocess.terminate()
                try:
                    self.current_subprocess.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_subprocess.kill()
            
            # Signal any Python loops to stop
            if hasattr(self, 'cancel_event'):
                self.cancel_event.set()
            
            # Cancel any scheduled updates
            if hasattr(self, 'scheduled_updates'):
                for after_id in self.scheduled_updates:
                    try:
                        self.app.after_cancel(after_id)
                    except:
                        pass
                    self.scheduled_updates = []
            
            # Schedule file cleanup with direct folder information from the processor
            self.app.after(500, lambda: self._delete_cancelled_files(cleanup_info))
                    
            return True  # Return True to indicate successful cancellation request
        
        return unified_cancel_handler

    def update_progress(self, message, percentage, output_line=None):
        """Update the progress bar with a message and percentage"""
        if hasattr(self, 'progress_section'):
            self.progress_section.update_progress(percentage, message, output_line)
        else:
            # Log the message if progress section isn't available
            self.logger.log_info(f"Progress update ({percentage}%): {message}")

    def cancel_processing(self):
        """Cancel the current processing if any subprocess is running"""
        # tell every Python loop to stop
        self.cancel_event.set()

        # kill any live subprocess
        if self.current_subprocess and self.current_subprocess.poll() is None:
            self.current_subprocess.terminate()
            try:
                self.current_subprocess.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_subprocess.kill()
        return True

    def _stream_subprocess_output(self, process, stage_name, base_progress):
        """
        Stream subprocess output and update progress display, with cleaner output formatting
        
        Args:
            process: The subprocess.Popen object
            stage_name: Name of the current processing stage
            base_progress: Base progress percentage for this stage
        """
        # Regular expression to match percentage values (if present)
        percentage_pattern = re.compile(r'^\d+%')
        # Pattern to extract the command name from OpenFOAM output lines
        cmd_pattern = re.compile(r'Running (\w+)(?:\s+\([^)]*\))? on ')
        
        # Read output line by line while process is running
        while process.poll() is None:
            # Check if cancellation was requested
            if self.cancel_requested:
                process.terminate()
                return
            
            # Read a line (if available)
            output_line = process.stdout.readline().strip()
            if output_line:
                # Log the full output for debugging
                self.logger.log_info(f"{stage_name}: {output_line}")
                
                # Clean up OpenFOAM output lines for display
                display_line = output_line
                if "Running " in output_line and " on " in output_line:
                    # Extract just the command name for cleaner display
                    match = cmd_pattern.search(output_line)
                    if match:
                        command = match.group(1)
                        display_line = f"Running {command}"
                
                # Handle progress indication in the output
                if percentage_pattern.match(output_line):
                    try:
                        # Extract percentage value
                        percentage = int(output_line.split('%')[0])
                        # Scale the percentage to fit within the stage's progress range
                        progress = base_progress + (percentage / 100) * 20
                        
                        # Update the progress display
                        self.update_progress(
                            f"{stage_name}: {display_line}",
                            progress,
                            display_line
                        )
                    except (IndexError, ValueError):
                        pass  # Skip malformed percentage lines
                else:
                    # For non-percentage lines, just display the output
                    self.update_progress(
                        f"{stage_name}: {display_line}",
                        base_progress,
                        display_line
                    )

        # Check for any remaining output after process completion
        remaining_output = process.stdout.read()
        if remaining_output:
            for line in remaining_output.splitlines():
                if line.strip(): 
                    self.logger.log_info(f"{stage_name}: {line.strip()}")
                    # Clean up line for display
                    display_line = line.strip()
                    if "Running " in display_line and " on " in display_line:
                        match = cmd_pattern.search(display_line)
                        if match:
                            command = match.group(1)
                            display_line = f"Running {command}"
                    
                    # Again check for percentage indications
                    if percentage_pattern.match(line.strip()):
                        self.update_progress(f"{stage_name}: {display_line}", base_progress, display_line)
                    else:
                        self.update_progress(f"{stage_name}: {display_line}", base_progress, display_line)

    # ====================================================================================================================
    # ================================= IMAGE DISPLAY METHODS ==================================================================
    # ====================================================================================================================

    def _update_render_display(self, stage, image_path, placeholder=False):
        """Update the display with proper button sizing and handle tab selection."""
        # Map stage to tab name
        tab_name_map = {
            "segmentation": "Segmentation",
            "postprocessing": "Post-processed Geometry", 
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
        
        # For CFD simulation, handle differently to show pressure and velocity side by side
        if stage == "cfd":
            self._update_cfd_display(main_container)
        else:
            # Create image container with fixed height
            image_container = ctk.CTkFrame(
                main_container,
                fg_color=main_container.cget("fg_color"),
                height=350
            )
            image_container.pack(fill="x", expand=True, pady=(5, 5))
            
            # Initialize the render_images dictionary if it doesn't exist
            if not hasattr(self, 'render_images'):
                self.render_images = {}
                
            if image_path is None:
                # Display placeholder message
                ctk.CTkLabel(image_container, text=f"{stage.capitalize()} render will appear here.", font=("Arial", 12)).pack(expand=True)
            else:
                try:
                    # Load and display image
                    pil_image = Image.open(image_path)
                    
                    # Calculate sizing
                    max_width = 600
                    max_height = 450
                    
                    # Calculate aspect ratio-preserving dimensions
                    orig_width, orig_height = pil_image.size
                    width_ratio = max_width / orig_width
                    height_ratio = max_height / orig_height
                    scale_ratio = min(width_ratio, height_ratio)
                    
                    new_width = int(orig_width * scale_ratio)
                    new_height = int(orig_height * scale_ratio)
                    
                    # Resize image
                    pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Create CTkImage and store reference - important to use a consistent key
                    image_key = f"{stage}_image"
                    self.render_images[image_key] = ctk.CTkImage(light_image=pil_image, size=(new_width, new_height))
                    
                    # Save the path as a persistent attribute for future reference
                    setattr(self, f"{stage}_image_path", image_path)
                    
                    # Display image centered
                    image_label = ctk.CTkLabel(image_container, image=self.render_images[image_key], text="")
                    image_label.pack(pady=(10, 5))
                    
                    # Add caption
                    if stage == "postprocessing":
                        caption_text = "Post-processed model with inlet (green), and outlet (red) components"
                    else:
                        caption_text = "Segmentation preview image"
                        
                    ctk.CTkLabel(
                        image_container,
                        text=caption_text,
                        font=("Arial", 14),
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
                text="🔄 Click to See Predicted Airway in 3D Viewer",
                command=lambda: self._interactive_segmentation(self.current_stl_path if hasattr(self, 'current_stl_path') else None),
                width=TAB4_SETTINGS["RENDER_BUTTON"]["WIDTH"],
                height=TAB4_SETTINGS["RENDER_BUTTON"]["HEIGHT"],
                font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                fg_color=TAB4_SETTINGS["RENDER_BUTTON"]["FG_COLOR"],
                hover_color=TAB4_SETTINGS["RENDER_BUTTON"]["HOVER_COLOR"],
                text_color="white"
            )
            segmentation_button.pack(pady=5)
            
        elif stage == "postprocessing":
            postprocessed_button = ctk.CTkButton(
                button_frame,
                text="🔄 Click to See Model with Processed Boundaries in 3D Viewer",
                command=self._interactive_blender_results,
                width=TAB4_SETTINGS["RENDER_BUTTON"]["WIDTH"],
                height=TAB4_SETTINGS["RENDER_BUTTON"]["HEIGHT"],
                font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
                fg_color=TAB4_SETTINGS["RENDER_BUTTON"]["FG_COLOR"],
                hover_color=TAB4_SETTINGS["RENDER_BUTTON"]["HOVER_COLOR"],
                text_color="white"
            )
            postprocessed_button.pack(pady=5)
    
    def _segmentation_results_exist(self):
        """Return True if we’ve already run segmentation in this folder."""
        stl_folder = Path(self.app.full_folder_path) / "stl"
        # look for your STL (or image) marker
        return stl_folder.exists() and any(stl_folder.glob("*_geo.stl"))
    
    def _load_existing_segmentation(self):
        """Load the existing segmentation results into the UI."""
        stl_folder = Path(self.app.full_folder_path) / "stl"
        # pick the first preview image you generated in AirwaySegmentator
        img = next(stl_folder.glob("*_geo.png"), None)
        if img:
            self._update_render_display("segmentation", str(img))
            self.current_stl_path = str(img.with_suffix(".stl"))
            self.airway_volume = str((Path(self.app.full_folder_path) / "volume_calculation.txt").read_text()
            )
            self._finalize_processing()

            # segmentation-only → no PDF preview, but allow data export to external drive
            self.preview_button.configure(state="disabled")
            self.export_button.configure(state="normal")
        else:
            messagebox.showwarning("Warning", "Could not find existing segmentation files.")

    # ====================================================================================================================
    # ================================= BLENDER METHODS ==================================================================
    # ====================================================================================================================

    def _start_blender_processing(self, stl_path, cfd_output_dir):
        """Start Blender processing using the modular processor"""
        try:
            # Set up cancellation callback for the progress section
            self.progress_section.set_cancel_callback(self._request_cancel)
            
            def on_blender_complete(result):
                """Handle Blender processing completion"""
                if self.cancel_requested:
                    self.logger.log_info("Blender processing was cancelled")
                    return
                    
                if not result["success"]:
                    self.app.after(0, lambda: messagebox.showerror("Blender Error", result["error_message"]))
                    self.app.after(0, self._reset_processing_state)
                    return
                
                # Processing successful - proceed to next steps
                self.app.after(0, lambda: self._on_blender_success(result, cfd_output_dir))
            
            # Start async processing with render callback
            self.blender_processor.process_geometry_async(
                stl_path=stl_path,
                cfd_output_dir=cfd_output_dir,
                completion_callback=on_blender_complete,
                render_callback=self._render_assembly_image
            )
            
        except Exception as e:
            self.logger.log_error(f"Error starting Blender processing: {e}")
            messagebox.showerror("Error", f"Failed to start Blender processing: {e}")
            self._reset_processing_state()
    
    def _on_blender_success(self, result, cfd_output_dir):
        """Handle successful Blender processing"""
        try:
            # Update UI with assembly image if available
            if "assembly_image_path" in result:
                self._update_render_display("postprocessing", result["assembly_image_path"])
                self._select_tab("Post-processed Geometry")
            
            # Check if cancellation was requested during UI updates
            if self.cancel_requested:
                self.logger.log_info("Process cancelled after Blender completion")
                return
            
            # Start CFD simulation
            self.logger.log_info("Starting CFD simulation...")
            self.cancel_requested = False
            self.processing_active = True
            
            self.update_progress("Running CFD simulation…", 85)
            
            # Set up cancellation for CFD
            self.progress_section.set_cancel_callback(
                self._create_unified_cancel_handler()
            )
            
            # Start CFD processing
            threading.Thread(
                target=self._cfd_worker,
                args=(cfd_output_dir,),
                daemon=True
            ).start()
            
        except Exception as e:
            error_message = f"Error after Blender processing: {str(e)}"
            self.logger.log_error(error_message)
            messagebox.showerror("Error", error_message)
            self._reset_processing_state()


    # ====================================================================================================================
    # ================================= SIMULATION RELATED METHODS =======================================================
    # ====================================================================================================================

    def _get_full_cfd_path(self,flow_rate=None):
        """
        Get the full path to the CFD directory for the specified flow rate.
        """
        
        if flow_rate is None:
            flow_rate_read = self.flow_rate.get()
        
        # Format with exactly one decimal place
        flow_rate_str = f"{flow_rate_read:.1f}"
        # Replace decimal point with underscore
        flow_dir = flow_rate_str.replace('.', '_')
        # Add CFD_ suffix
        cfd_dir = f"CFD_{flow_dir}"
        
        # Get base path from the application's current patient folder
        if hasattr(self.app, 'full_folder_path') and self.app.full_folder_path:
            # Use the parent directory of the current patient folder
            base_path = str(Path(self.app.full_folder_path))
        else:
            self.logger.log_warning("Full_folder_path is not set")
        
        return os.path.join(base_path, cfd_dir)

    def _cfd_worker(self, cfd_dir):
        try:
            # Reset the cancellation processed flag at the start
            self._cancellation_processed = False

            # Make sure cancel button is properly enabled
            self.app.after(0, lambda: self.progress_section.set_cancel_callback(self._request_cancel))
            
            dirs = str(cfd_dir)

            # 1. Write flow rate to pvfr.txt
            step0 = os.path.join(dirs, "0")
            os.makedirs(step0, exist_ok=True)
            with open(os.path.join(step0, "pvfr.txt"), "w") as f:
                f.write(f"vfr {self.flow_rate.get():.1f};\n#inputMode merge")

            # 2. Combine STL files
            surf_dir = os.path.join(dirs, "constant", "triSurface")
            if not os.path.isdir(surf_dir):
                raise FileNotFoundError(f"triSurface directory not found: {surf_dir}")

            # Check for cancellation after each major step
            if self.cancel_requested:
                return

            # remove old combined.stl
            subprocess.run(["rm", "-f", "combined.stl"], cwd=surf_dir, check=True)
            # cat all .stl into combined.stl
            subprocess.run("cat *.stl >> combined.stl", cwd=surf_dir, shell=True, check=True)

            if not os.path.exists(os.path.join(surf_dir, "combined.stl")):
                raise FileNotFoundError("Failed to create combined.stl")

            # Check for cancellation again
            if self.cancel_requested:
                return

            # 3. Kick off residual monitoring in background with daemon=True
            self.residual_monitor_thread = threading.Thread(
                target=self._monitor_residuals, 
                args=(dirs,), 
                daemon=True  # Ensure this is a daemon thread so it exits when the main thread exits
            )
            self.residual_monitor_thread.start()

            # 4. Ensure Allclean/Allrun exist and are executable
            for script in ("Allclean", "Allrun"):
                path = os.path.join(dirs, script)
                if not os.path.isfile(path):
                    raise FileNotFoundError(f"{script} not found: {path}")
                if not os.access(path, os.X_OK):
                    os.chmod(path, 0o755)
                    self.logger.log_info(f"Made {script} executable")

            # Check for cancellation again
            if self.cancel_requested:
                return

            # 5. Run Allclean then Allrun, storing the process reference
            for script in ("Allclean", "Allrun"):
                if self.cancel_requested:
                    return
                    
                self.logger.log_info(f"Running {script} in {dirs}")
                self.current_process = subprocess.Popen(
                    [f"./{script}"], 
                    cwd=dirs, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Use the updated stream processing method to handle output
                self._stream_subprocess_output(
                    self.current_process, 
                    f"CFD {script}", 
                    85
                )
                
                # Check if process failed
                if self.current_process.returncode != 0:
                    stderr = self.current_process.stderr.read()
                    raise subprocess.CalledProcessError(
                        self.current_process.returncode,
                        script,
                        output=None,
                        stderr=stderr
                    )

            # 6. All done—back to main thread if not cancelled
            if not self.cancel_requested:
                self.app.after(0, lambda: self._on_sim_done(cfd_dir))
            else:
                self.app.after(0, self._on_sim_cancelled)

        except subprocess.CalledProcessError as e:
            # Only handle errors if not cancelled (since cancellation will cause errors)
            if not self.cancel_requested:
                msg = (
                    f"{e.cmd!r} failed (code {e.returncode}).\n"
                    f"Output: {e.output or 'n/a'}\n"
                    f"Error: {e.stderr or 'n/a'}"
                )
                self.logger.log_error(msg)
                self.app.after(0, lambda: self._on_worker_error("Simulation", msg))

        except Exception as e:
            # Only handle errors if not cancelled
            if not self.cancel_requested:
                msg = f"{type(e).__name__}: {e}"
                self.logger.log_error(msg)
                self.app.after(0, lambda: self._on_worker_error("Simulation", msg))

    def _on_sim_done(self, cfd_dir):
        """Process and visualize CFD results after simulation completes."""
        try:
            # Run ParaView script to generate visualization images
            self.update_progress(
                "Generating visualization images...",
                90,
                "Generating visualization images..."
            )
            success = self._run_paraview(cfd_dir)
            self.autocrop_whitespace(cfd_dir)
            
            if not success:
                messagebox.showwarning("Warning", "ParaView post-processing failed, some images may be missing.")
            
            # Update the CFD tab display with newly generated images
            pressure_images = list(Path(cfd_dir).glob("p_cut_1.png"))
            velocity_images = list(Path(cfd_dir).glob("v_cut_1.png"))
            
            # Now enable the CFD tab and display results
            if pressure_images or velocity_images:
                self._update_render_display("cfd", None)  # This will trigger the _update_cfd_display method
                self._select_tab("CFD Simulation")
            
            # Now finalize everything
            self._finalize_processing()
            self.process_button.configure(text="Start Processing", state="normal")
            
            # Enable preview and export buttons now that everything is done
            self.preview_button.configure(state="normal")
            self.export_button.configure(state="normal")

            # self.prune_cfd_folder(cfd_dir) # Comment out if not wanting to remove log files and other supplemental files # TODO: Uncomment this
            
        except Exception as e:
            error_msg = f"Error in post-processing: {str(e)}"
            self.logger.log_error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.process_button.configure(state="normal")
    
    def _run_paraview(self, cfd_dir):
        """Simple function to run paraview_ortho.py to generate visualization images."""
        try:
            # 1. Verify case.foam exists
            case_foam_path = os.path.join(cfd_dir, "case.foam")
            if not os.path.exists(case_foam_path):
                self.logger.log_error(f"case.foam file not found at: {case_foam_path}")
                return False
            
            # 2. Run the paraview script
            self.logger.log_info("Running ParaView script")
            self.update_progress("Generating visualization images...", 95)
            
            # Use absolute path for the script to avoid any path issues
            main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            script_path = os.path.join(main_dir, "paraview_ortho.py")
            
            # Run the command
            cmd = ["pvbatch", script_path]
            self.logger.log_info(f"Command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for completion and get output
            stdout, stderr = process.communicate()
            
            # Log significant output
            if stdout:
                self.logger.log_info(f"ParaView output: {stdout.strip()}")
            
            if stderr:
                self.logger.log_error(f"ParaView error: {stderr.strip()}")
            
            if process.returncode != 0:
                self.logger.log_error(f"ParaView process failed with return code: {process.returncode}")
                return False
            
            # 3. Create CFD-tagged copies of generated images
            for img in ["p_cut_1.png", "v_cut_1.png"]:
                img_path = os.path.join(cfd_dir, img)
                if os.path.exists(img_path):
                    # Create CFD-tagged copy
                    cfd_img = img.replace(".png", "_CFD.png")
                    cfd_img_path = os.path.join(cfd_dir, cfd_img)
                    shutil.copy(img_path, cfd_img_path)
                    self.logger.log_info(f"Created tagged copy: {cfd_img}")
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error running ParaView: {str(e)}")
            return False
    
    def autocrop_whitespace(self, folder, pattern="*.png"):
        # Crops out the white space in the images. Did this to not modify the paraview script provided by Uday
        for fname in glob.glob(os.path.join(folder, pattern)):
            img = Image.open(fname)
            # create a white background image the same size
            bg = Image.new(img.mode, img.size, (255,255,255))
            # find the bounding box of the non-white area
            diff = ImageChops.difference(img, bg)
            bbox = diff.getbbox()
            if bbox:
                cropped = img.crop(bbox)
                cropped.save(fname)  # overwrite
                print(f"Cropped whitespace from {os.path.basename(fname)}")

    def _on_sim_cancelled(self):
        """Handle cancellation completion cleanly"""
        # Avoid duplicate processing
        if hasattr(self, '_cancellation_processed') and self._cancellation_processed:
            return
            
        self._cancellation_processed = True
        
        # Log the cancellation
        self.logger.log_info("Simulation cancelled by user")

        # Update progress section with cancellation message
        self.app.after(0, lambda: self.progress_section.update_progress(
            None,  # No percentage change
            "Processing cancelled by user",  # Message
            "Cancellation complete - processing stopped"  # Output line
        ))

        # Clean up files - wait a sec for processes to end
        self.app.after(10000, self._delete_cancelled_files)
        
        # Reset the processing state through the "central" method
        self._reset_processing_state()

    def _cfd_results_exist(self, flow_rate=None):
        """Check if CFD results already exist (case.foam), or if segmentation has already been done (.stl in stl/)."""
        cfd_path = self._get_full_cfd_path(flow_rate)

        # 1) Segmentation AND CFD done?
        stl_folder = Path(self.app.full_folder_path) / "stl"
        case_foam = os.path.join(cfd_path, "case.foam")
        # 2) Check if time step 20 exists (indicating a completed simulation)
        time_step = os.path.join(cfd_path, "20") #TODO: Change this to whatever step number in controlDict
        
        # All conditions must be met: case.foam exists, stl folder with files exists, and time step 20 exists
        if (os.path.exists(case_foam) and 
            stl_folder.exists() and 
            any(stl_folder.glob("*.stl")) and
            os.path.exists(time_step)):
            return True

        return False
    
    def _monitor_residuals(self, dirs):
        """Monitor and update residual plots during simulation"""
        gnuplot_dir = os.path.join(dirs, "gnuplot")
        
        # Check if the directory exists
        if not os.path.exists(gnuplot_dir):
            self.logger.log_warning(f"Gnuplot directory not found at {gnuplot_dir}")
            return
            
        # Keep checking while the simulation is running and not cancelled
        while not self.cancel_requested:
            try:
                # Run the gnuplot script if it exists (same as GUI_ortho approach)
                if os.path.exists(os.path.join(gnuplot_dir, "gnuplot_residuals")):
                    # Only run if log file exists to prevent errors
                    log_file = os.path.join(gnuplot_dir, "log.simpleFoam")
                    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                        subprocess.run(
                            ['/bin/bash', '-c', "bash ./gnuplot_residuals"], 
                            cwd=gnuplot_dir, 
                            check=False,
                            stdout=subprocess.DEVNULL,  # Suppress stdout
                            stderr=subprocess.DEVNULL   # Suppress stderr
                        )
                
                # Check if the plot was generated
                if os.path.exists(os.path.join(gnuplot_dir, "residual_plot.png")):
                    self.residual_plot_path = os.path.join(gnuplot_dir, "residual_plot.png")
                
                # Sleep before checking again
                time.sleep(2)
                
                # Check if simulation is complete - use same condition as GUI_ortho
                if os.path.exists(os.path.join(dirs, "20", "U")):  #TODO: Change this to whatever step number in controlDict
                    break
                    
                # Also check for cancellation flag
                if self.cancel_requested:
                    self.logger.log_info("Residual monitoring cancelled")
                    break
                    
            except Exception as e:
                self.logger.log_error(f"Error monitoring residuals: {str(e)}")
                time.sleep(10)
                
                # Check for cancellation after error
                if self.cancel_requested:
                    break

    def _load_existing_cfd(self):
        """Load existing CFD results for the current flow rate."""
        try:
            # Show a progress indicator
            self.progress_section.start("Loading existing results...", indeterminate=True)
            
            # Get the CFD path for the current flow rate
            cfd_path = self._get_full_cfd_path()
            self.logger.log_info(f"Loading results from: {cfd_path}")
            
            # Update the processing state
            self.processing_active = True
            
            # Load segmentation results
            self.update_progress(
                "Loading segmentation results...",
                30,
                "Loading segmentation results..."
            )
            
            # Try to find the segmentation image - look in several possible locations
            segmentation_image = None
            segmentation_paths_to_check = [
                # Check in the stl folder first (where it's normally saved)
                Path(self.app.full_folder_path) / "stl",
                # Also check in the CFD folder (might be a copy there)
                Path(cfd_path)
            ]
            
            for folder in segmentation_paths_to_check:
                if folder.exists():
                    # Look for prediction images with various naming patterns
                    for pattern in ["*_pred.png", "*_prediction.png", "*_segmentation.png", "*_geo.png"]:
                        pred_images = list(folder.glob(pattern))
                        if pred_images:
                            segmentation_image = str(pred_images[0])
                            self.logger.log_info(f"Found segmentation image: {segmentation_image}")
                            break
                
                # If we found an image, we can stop looking
                if segmentation_image:
                    break
                    
            # If we found a segmentation image, update the display
            if segmentation_image:
                self._update_render_display("segmentation", segmentation_image)
                
                # Try to find the STL file corresponding to this image
                stl_file = Path(segmentation_image).with_suffix(".stl")
                if stl_file.exists():
                    self.current_stl_path = str(stl_file)
                    self.logger.log_info(f"Found STL file: {self.current_stl_path}")
                else:
                    # Look for any STL file in the stl folder or in the CFD folder
                    for folder in segmentation_paths_to_check:
                        stl_files = list(folder.glob("*.stl"))
                        for stl_file in stl_files:
                            # Skip component STL files
                            if stl_file.name in ["inlet.stl", "outlet.stl", "wall.stl"]:
                                continue
                            self.current_stl_path = str(stl_file)
                            self.logger.log_info(f"Found alternate STL file: {self.current_stl_path}")
                            break
                        
                        if hasattr(self, 'current_stl_path'):
                            break
            else:
                self.logger.log_warning("No segmentation image found. Skipping segmentation display.")

            # Check multiple possible volume file locations
            volume_file_paths = [
                Path(cfd_path) / "volume_calculation.txt",
                Path(self.app.full_folder_path) / "volume_calculation.txt",
                Path(self.app.full_folder_path) / "volume.txt",
                Path(self.app.full_folder_path) / "volume_calculation.txt"
            ]
            
            volume_found = False
            for volume_path in volume_file_paths:
                if volume_path.exists():
                    with open(volume_path, 'r') as f:
                        volume_str = f.read().strip()
                        self.airway_volume = float(volume_str) if volume_str.replace('.', '', 1).isdigit() else volume_str
                        self.logger.log_info(f"Loaded airway volume from {volume_path}: {self.airway_volume}")
                        volume_found = True
                        break
            
            # Look for min csa file
            main_out = Path(self.app.full_folder_path)
            min_csa_path = main_out / "min_csa.txt"
            if min_csa_path.exists():
                text = min_csa_path.read_text()
                # find the first floating‑point or integer in the text
                m = re.search(r"[-+]?\d*\.?\d+", text)
                if m:
                    self.min_csa = float(m.group(0))
                    self.logger.log_info(f"Loaded min CSA from {min_csa_path}: {self.min_csa}")
                else:
                    self.min_csa = None
                    self.logger.log_warning(f"No numeric value found in {min_csa_path}")
            else:
                self.min_csa = None
                self.logger.log_warning(f"min_csa.txt not found at {min_csa_path}")

            
            # Load post-processed geometry
            self.update_progress(
                "Loading post-processed geometry...",
                60,
                "Loading post-processed geometry..."
            )
            
            # Look for assembly image
            assembly_path = os.path.join(cfd_path, "constant", "triSurface")
            assembly_images = list(Path(assembly_path).glob("*_assem.png"))
            if not assembly_images:
                assembly_images = list(Path(assembly_path).glob("*assembly.png"))
            if assembly_images:
                self.logger.log_info(f"Found assembly image: {assembly_images[0]}")
                self._update_render_display("postprocessing", str(assembly_images[0]))
            else:
                self.logger.log_warning("No assembly visualization found.")
            
            # Load CFD simulation results
            self.update_progress(
                "Loading CFD simulation results...",
                90,
                "Loading CFD simulation results..."
            )
            
            # Check if the case.foam file exists
            case_foam_path = os.path.join(cfd_path, "case.foam")
            if not os.path.exists(case_foam_path):
                self.logger.log_warning(f"case.foam file not found at: {case_foam_path}")
                messagebox.showwarning(
                    "Missing Files",
                    "The simulation results appear to be incomplete. Some files may be missing."
                )
            
            # Check for CFD visualization images
            p_cut_1 = os.path.join(cfd_path, "p_cut_1.png")
            v_cut_1 = os.path.join(cfd_path, "v_cut_1.png")
            
            # If the images don't exist, run ParaView to generate them
            has_results   = os.path.exists(p_cut_1) and os.path.exists(v_cut_1)
            has_timesteps = any(
                d.isdigit() and int(d) >= 20 and os.path.isdir(os.path.join(cfd_path, d))  #TODO: change to number of steps in controlDict
                for d in os.listdir(cfd_path)
            )

            if not has_results and has_timesteps:
                self.logger.log_info("Sim appears done (found time‑step dirs), generating cut‑planes now")
                success = self._run_paraview(cfd_path)
                self.autocrop_whitespace(cfd_path)
                if not success:
                    self.logger.log_warning("Failed to generate CFD visualization images")
                    messagebox.showwarning(
                        "Visualization Failed",
                        "Failed to generate CFD visualization images. Some visualizations may be missing."
                    )
            
            # Update the CFD visualization
            self._update_render_display("cfd", None)  # This will trigger the _update_cfd_display method
            
            # Switch to CFD tab
            self._select_tab("CFD Simulation")
            
            # Finalize
            self._finalize_processing()
            
            # Show success message
            messagebox.showinfo(
                "Results Loaded",
                f"Existing results for flow rate {self.flow_rate.get():.1f} LPM have been successfully loaded."
            )

        except Exception as e:
            error_msg = f"Error loading existing results: {str(e)}"
            self.logger.log_error(error_msg)
            messagebox.showerror("Error", error_msg)
            
            # Reset processing state
            self.processing_active = False
            self.progress_section.stop("Error loading results")
            self.process_button.configure(state="normal")
    
    def _display_cfd_images(self, container, image_path, title):
        """Display a single CFD image with title in the given container"""
        # Add title
        ctk.CTkLabel(
            container,
            text=title,
            font=("Arial", 16, "bold"),
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        ).pack(pady=(0, 5))
        
        try:
            # Load and display image
            pil_image = Image.open(image_path)
            
            # Calculate sizing (smaller than when showing one image)
            max_width = 500
            max_height = 500
            
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
            
            # Generate a unique key for this image
            image_key = f"cfd_{title.lower().replace(' ', '_')}"
            
            # Store reference to avoid garbage collection
            self.render_images[image_key] = ctk_image
            
            # Display image centered
            image_label = ctk.CTkLabel(container, image=ctk_image, text="")
            image_label.pack(pady=5)
            
        except Exception as e:
            error_msg = f"Error loading {title} image: {str(e)}"
            ctk.CTkLabel(container, text=error_msg, font=("Arial", 12), wraplength=250).pack(expand=True)
            self.logger.log_error(error_msg)

    def _update_cfd_display(self, parent_container):
        """Create a side-by-side display of pressure and velocity images for CFD results"""
        # Create a container for the images
        images_container = ctk.CTkFrame(
            parent_container,
            fg_color=parent_container.cget("fg_color")
        )
        images_container.pack(fill="both", expand=True, pady=(5, 5))
        
        # Configure the grid layout for side-by-side images
        images_container.columnconfigure(0, weight=1)
        images_container.columnconfigure(1, weight=1)
        
        # Get pressure and velocity image paths
        cfd_path = self._get_full_cfd_path()
        
        # Look for specific files first, then fallback to pattern matching
        pressure_image_path = os.path.join(cfd_path, "p_cut_1.png")
        velocity_image_path = os.path.join(cfd_path, "v_cut_1.png")
        
        # If exact files don't exist, try pattern matching
        if not os.path.exists(pressure_image_path):
            # Look for pressure images with different possible naming patterns
            pressure_patterns = ["*pressure*.png", "*p_*cut*.png", "*p_plot.png", "pressure_*.png"]
            for pattern in pressure_patterns:
                pressure_images = list(Path(cfd_path).glob(pattern))
                if pressure_images:
                    pressure_image_path = str(pressure_images[0])
                    self.logger.log_info(f"Found pressure image: {pressure_image_path}")
                    break
        
        if not os.path.exists(velocity_image_path):
            # Look for velocity images with different possible naming patterns
            velocity_patterns = ["*velocity*.png", "*v_*cut*.png", "*u_plot.png", "*vel*.png", "velocity_*.png"]
            for pattern in velocity_patterns:
                velocity_images = list(Path(cfd_path).glob(pattern))
                if velocity_images:
                    velocity_image_path = str(velocity_images[0])
                    self.logger.log_info(f"Found velocity image: {velocity_image_path}")
                    break
        
        # Save the paths as instance variables for future reference
        self.pressure_image_path = pressure_image_path if os.path.exists(pressure_image_path) else None
        self.velocity_image_path = velocity_image_path if os.path.exists(velocity_image_path) else None
        
        # Create left frame for pressure
        pressure_frame = ctk.CTkFrame(
            images_container,
            fg_color=images_container.cget("fg_color")
        )
        pressure_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        
        # Create right frame for velocity
        velocity_frame = ctk.CTkFrame(
            images_container,
            fg_color=images_container.cget("fg_color")
        )
        velocity_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        
        # Display pressure image
        if os.path.exists(pressure_image_path):
            self._display_cfd_images(pressure_frame, pressure_image_path, "Pressure Distribution")
        else:
            self.logger.log_warning(f"Pressure image not found at: {pressure_image_path}")
            ctk.CTkLabel(
                pressure_frame,
                text=f"Pressure visualization not found.\nCheck {cfd_path} for image files.",
                font=("Arial", 12),
                wraplength=250
            ).pack(expand=True)
        
        # Display velocity image
        if os.path.exists(velocity_image_path):
            self._display_cfd_images(velocity_frame, velocity_image_path, "Velocity Distribution")
        else:
            self.logger.log_warning(f"Velocity image not found at: {velocity_image_path}")
            ctk.CTkLabel(
                velocity_frame,
                text=f"Velocity visualization not found.\nCheck {cfd_path} for image files.",
                font=("Arial", 12),
                wraplength=250
            ).pack(expand=True)
        
        # Add overall caption
        ctk.CTkLabel(
            parent_container,
            text="CFD simulation results showing pressure and velocity distributions",
            font=("Arial", 16),
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        ).pack(pady=(5, 0))
    

    def prune_cfd_folder(self, cfd_dir): #TODO: Re-check this to see which files to remove
        """
        Remove all OpenFOAM “scratch” folders so you only keep:
        - case.foam
        - *_CFD.png
        - constant/triSurface/
        """
        p = Path(cfd_dir)

        # 1) directories to nuke wholesale
        for d in ("0", "system", "gnuplot"):
            target = p / d
            if target.exists():
                shutil.rmtree(target)

        # 2) mesh & scripts
        mesh_dir = p / "constant" / "polyMesh"
        if mesh_dir.exists():
            shutil.rmtree(mesh_dir)

        for fname in ("Allrun", "Allclean"):
            f = p / fname
            if f.exists():
                f.unlink()

        # 3) any numeric time‐step directories
        for sub in p.iterdir():
            if sub.is_dir() and sub.name.isdigit():
                shutil.rmtree(sub)

        # 4) any log files
        for log in p.glob("log.*"):
            log.unlink()

        print(f"Pruned CFD folder; only case.foam, *_CFD.png, and triSurface remain in {cfd_dir}")

    # ==========================================================
    ###### IMAGE RENDER METHODS #######
    # ==========================================================
    def _get_patient_initials(self, name):
        # Extract initials from the full patient's name and gives the patient initials as a string. 
        # If patient name is Anonymous, it returns ANON as initials or gives XX as last resort

        try:
            # Check for Anonymous patient
            if name == "Anonymous":
                initials = "ANON"
            # Split the name by spaces
            name_parts = name.split()
            # Extract first letter from each part
            initials = ''.join(part[0].upper() for part in name_parts if part)
            
            if not initials:
                initials = "XX"
                
            return initials
        except Exception as e:
            self.logger.log_error(f"Error extracting patient initials: {str(e)}")
            return "XX"  # Return default if there's an error

    def _render_assembly_image(self, inlet_path, outlet_path, wall_path, output_dir):
        """
        Render the assembly.png and then rename it to <initials>_<scan_date>_assem.png
        in the directory where it was created.
        """
        try:
            inlet_path = str(inlet_path)
            outlet_path = str(outlet_path)
            wall_path = str(wall_path)

            # generate the default assembly.png in the triSurface folder
            render_assembly(inlet_path, outlet_path, wall_path, offscreen=True)

            # where the script always drops its assembly.png
            tri_dir = os.path.dirname(inlet_path)
            original_png = os.path.join(tri_dir, "assembly.png")
            if not os.path.exists(original_png):
                self.logger.log_error("Expected assembly.png but it was not created.")
                return None

            # Get initials and scan_date (a plain string, set in _refresh_patient_info)
            patient_name     = self.app.patient_name.get().strip() or "Anonymous"
            patient_initials = self._get_patient_initials(patient_name)

            # self.scan_date is set during _refresh_patient_info()
            scan_date = getattr(self, "scan_date", None)
            if not scan_date or scan_date in ("", "No Date"):
                # fallback if user never supplied a date
                scan_date = "NoDate"

            # build the new filename and move
            new_filename = f"{patient_initials}_{scan_date}_assem.png"
            target_png   = os.path.join(tri_dir, new_filename)

            # Renaming file with patient info
            os.replace(original_png, target_png)
            # Copying file to main cfd output directory
            main_cfd_dir = os.path.abspath(output_dir)   
            shutil.copy(target_png, main_cfd_dir)

            # if you also want a copy in output_dir root, just uncomment:
            main_cfd_dir = os.path.abspath(output_dir)   # e.g. ".../CFD_10_0"
            shutil.copy(target_png, os.path.join(main_cfd_dir, os.path.basename(target_png)))

            return target_png

        except Exception as e:
            self.logger.log_error(f"Error in assembly rendering: {e}")
            return None
    
    def _interactive_segmentation(self, stl_path):
        """
        Launch an interactive STL viewer using the Open3D viewer module
        """
        try:
            self.viewer.view_stl_file(stl_path)
        except Exception as e:
            self.logger.log_error(f"Failed to launch STL viewer: {e}")
            tk.messagebox.showerror("Error", f"Failed to display STL viewer:\n{e}")

    def _interactive_blender_results(self):
        """
        Launch an interactive viewer for airway components using the Open3D viewer module
        """
        try:
            cfd_base_path = str(self._get_full_cfd_path())
            self.viewer.view_airway_components(cfd_base_path)
        except Exception as e:
            self.logger.log_error(f"Failed to launch component viewer: {e}")
            tk.messagebox.showerror("Error", f"Failed to display component viewer:\n{e}")

    # ----------------------------------------------------------------------
    ######## RESULTS REPORT AND DATA EXPORT RELATED METHODS ################
    # ----------------------------------------------------------------------
    def _report_image_paths(self):
        """
        Gather up all the images needed for the report based on current flow rate.
        Returns a dict with:
          - cfd_dir                     : str
          - postprocessed_image_path    : str or None
          - cfd_pressure_plot_path     : str or None
          - cfd_velocity_plot_path     : str or None
        """
        self._refresh_patient_info()
        flow_str = f"{self.flow_rate.get():.1f}".replace('.', '_')
        cfd_dir = Path(self.app.full_folder_path) / f"CFD_{flow_str}"

        # 1) assembly / post‑processed geometry
        postprocessed = None
        tri_surface_dir = cfd_dir / "constant" / "triSurface"
        if tri_surface_dir.exists():
            # Try renamed file
            for p in tri_surface_dir.glob("*_assem.png"):
                postprocessed = str(p)
                break
            # fallback to old name if needed
            if not postprocessed:
                for p in tri_surface_dir.glob("*assembly.png"):
                    postprocessed = str(p)
                    break
    
        if not postprocessed:
            self.logger.log_warning("Assembly image not found for report")
            messagebox.showwarning("Warning", "Assembly image not found; report may be incomplete.")

        # 2) pressure & velocity   #TODO: Point these to the pressure and velocity plots that show change along airway path
        pressure = None

        velocity = None

        # 3) any other PNGs in cfd_dir **excluding** the above three
        reserved = {postprocessed, pressure, velocity}
        additional = []
        for p in sorted(cfd_dir.glob("*.png")):
            p_str = str(p)
            if p_str not in reserved:
                additional.append(p_str)

        return {
            "cfd_dir": str(cfd_dir),
            "postprocessed_image_path": postprocessed,
            "cfd_pressure_plot_path": pressure,
            "cfd_velocity_plot_path": velocity,
            "additional_images": additional
        }

    def _preview_report(self):
        # Generate a preview PDF and display it in the embedded viewer, automatically picking up all the images via _report_image_paths().
        self._refresh_patient_info()

        # gather image paths
        paths = self._report_image_paths()

        # create a temp PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            preview_pdf = tmp.name

        # call your report generator
        success = generate_airway_report(
            pdf_path=preview_pdf,
            cfd_dir=paths["cfd_dir"],
            patient_name=self.app.patient_name.get(),
            patient_dob=self.app.dob.get(),
            physician=self.app.patient_doctor_var.get(),
            analysis_type=self.analysis_option.get(),
            airway_volume=self.airway_volume,
            flow_rate_val=self.flow_rate.get(),
            airway_resistance=None,
            postprocessed_image_path=paths["postprocessed_image_path"],
            cfd_pressure_plot_path=paths["cfd_pressure_plot_path"],
            cfd_velocity_plot_path=paths["cfd_velocity_plot_path"],
            add_preview_elements=True, 
            date_of_report=None,
            min_csa=self.min_csa
        )

        if not success:
            messagebox.showerror("Error", "Failed to generate preview PDF.")
            return False

        self.preview_pdf_path = preview_pdf
        self._display_pdf_in_viewer(preview_pdf, is_preview=True)

        # enable export/save buttons if they were disabled
        if self.export_button.cget("state") == "disabled":
            self.export_button.configure(state="normal")

        return True
        
    def _display_pdf_in_viewer(self, pdf_path, is_preview=False):
        """Display the PDF in an embedded viewer"""
        try:
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

    
    def _save_results_to_drive(self):
        """Generate the PDF & copy the session onto the USB, showing a “Saving…” dialog."""
        src = getattr(self.app, "full_folder_path", None)
        if not src or not os.path.exists(src):
            tk.messagebox.showerror("Error", "No results folder to save.")
            return

        dest_root = getattr(self.app, "selected_drive_path", None)
        if not dest_root or not os.path.isdir(dest_root):
            tk.messagebox.showerror(
                "Error",
                "Could not find the original USB mount. Please go back and re‑select your drive."
            )
            return

        gui_user = self.app.username_var.get().strip() or "UnknownUser"
        patient  = self.app.patient_name.get().strip()   or "UnknownPatient"
        session  = os.path.basename(src.rstrip(os.sep))
        target   = os.path.join(dest_root, gui_user, patient, session)

        # create & show the saving dialog
        save_dialog = ctk.CTkToplevel(self.app)
        save_dialog.title("Saving Results")
        save_dialog.geometry("400x150")
        save_dialog.transient(self.app)

        ctk.CTkLabel(save_dialog, text="Saving to external drive…\nThis may take a few minutes.").pack(pady=(20,5))
        pb = ctk.CTkProgressBar(save_dialog, mode="indeterminate")
        pb.pack(fill="x", padx=20, pady=(0,10))
        pb.start()

        # **force the dialog to render** before grabbing
        save_dialog.update_idletasks()
        save_dialog.update()
        try:
            save_dialog.grab_set()
        except tk.TclError:
            # if it still fails, we’ll just let it run modeless
            pass

        cancel_event = threading.Event()

        # 1) add cancel button
        cancel_event = threading.Event()
        def on_cancel():
            cancel_event.set()
            pb.stop()
            btn_cancel.configure(state="disabled", text="Cancelling…")

        btn_cancel = ctk.CTkButton(
            save_dialog,
            text="Cancel",
            command=on_cancel
        )
        btn_cancel.pack(side="bottom", pady=(0, 10))

        def _do_copy():
            try:
                os.makedirs(target, exist_ok=True)

                # segmentation only
                if self.analysis_option.get() == "Upper Airway Segmentation":
                    for name in os.listdir(src):
                        if cancel_event.is_set():
                            raise RuntimeError("User cancelled save")
                        if name.startswith("CFD_"):
                            continue
                        s = os.path.join(src, name)
                        d = os.path.join(target, name)
                        if os.path.isdir(s):
                            ok = self._copy_dir_with_cancel(s, d, cancel_event)
                            if not ok:
                                raise RuntimeError("User cancelled save")
                        else:
                            if cancel_event.is_set():
                                raise RuntimeError("User cancelled save")
                            shutil.copy2(s, d)

                    self.app.after(0, lambda: tk.messagebox.showinfo(
                        "Cancelled" if cancel_event.is_set() else "Success",
                        f"{'Save cancelled' if cancel_event.is_set() else 'Segmentation results saved to:'}\n{target}"
                    ))
                    return

                # simulation: generate PDF first
                if "Simulation" in self.analysis_option.get():
                    flow_str = f"{self.flow_rate.get():.1f}".replace('.', '_')
                    pdf_name = f"airway_analysis_flow_{flow_str}.pdf"
                    pdf_path = os.path.join(src, pdf_name)

                    # gather image paths
                    paths = self._report_image_paths()

                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        preview_pdf = tmp.name

                    generate_airway_report(
                        pdf_path=preview_pdf,
                        cfd_dir=paths["cfd_dir"],
                        patient_name=self.app.patient_name.get(),
                        patient_dob=self.app.dob.get(),
                        physician=self.app.patient_doctor_var.get(),
                        analysis_type=self.analysis_option.get(),
                        airway_volume=self.airway_volume,
                        flow_rate_val=self.flow_rate.get(),
                        airway_resistance=None,
                        postprocessed_image_path=paths["postprocessed_image_path"],
                        cfd_pressure_plot_path=paths["cfd_pressure_plot_path"],
                        cfd_velocity_plot_path=paths["cfd_velocity_plot_path"],
                        add_preview_elements=True, 
                        date_of_report=None,
                        min_csa=self.min_csa
                    )

                    if cancel_event.is_set():
                        raise RuntimeError("User cancelled save")

                # copy everything
                for name in os.listdir(src):
                    if cancel_event.is_set():
                        raise RuntimeError("User cancelled save")
                    s = os.path.join(src, name)
                    d = os.path.join(target, name)
                    if os.path.isdir(s):
                        ok = self._copy_dir_with_cancel(s, d, cancel_event)
                        if not ok:
                            raise RuntimeError("User cancelled save")
                    else:
                        if cancel_event.is_set():
                            raise RuntimeError("User cancelled save")
                        shutil.copy2(s, d)

                if not cancel_event.is_set():
                    self.app.after(0, lambda: tk.messagebox.showinfo(
                        "Success",
                        f"All results & report saved to:\n{target}"
                    ))

            except Exception as e:
                # If it was our cancellation, show a friendly message
                msg = "Save aborted by user." if cancel_event.is_set() else f"Failed to save: {e}"
                self.app.after(0, lambda: messagebox.showerror("Error", msg))
            finally:
                # always tear down the dialog
                self.app.after(0, save_dialog.destroy)

        threading.Thread(target=_do_copy, daemon=True).start()
    
    def _copy_dir_with_cancel(self, src_dir, dst_dir, cancel_event):
        """
        Recursively copy src_dir → dst_dir, but before each file
        copy check if cancel_event.is_set(); if so, abort and return False.
        """
        for root, dirs, files in os.walk(src_dir):
            if cancel_event.is_set():
                return False
            # Recreate directory structure
            rel = os.path.relpath(root, src_dir)
            target_root = os.path.join(dst_dir, rel)
            os.makedirs(target_root, exist_ok=True)
            for fname in files:
                if cancel_event.is_set():
                    return False
                src_f = os.path.join(root, fname)
                dst_f = os.path.join(target_root, fname)
                try:
                    shutil.copy2(src_f, dst_f)
                except Exception:
                    # you might want to log or surface some errors here
                    return False
        return True
    
    def _delete_cancelled_files(self):
        """
        Delete files based on what operation was cancelled.
        Only deletes in-progress files, preserves completed results.
        """
        try:
            if not hasattr(self.app, 'full_folder_path') or not self.app.full_folder_path:
                print(self.app.full_folder_path)
                self.logger.log_warning("No folder path to clean up")
                return False
                
            # What was cancelled?
            is_simulation = "Simulation" in self.analysis_option.get()
            self.logger.log_info(f"Cleanup for {'simulation' if is_simulation else 'segmentation'}")
            
            if is_simulation:
                # For simulation, just delete the specific CFD folder for this flow rate
                cfd_path = self._get_full_cfd_path()
                if os.path.exists(cfd_path):
                    # Check if this is an incomplete simulation
                    case_foam_exists = os.path.exists(os.path.join(cfd_path, "case.foam"))
                    
                    # Find the highest numbered time directory
                    max_time_step = 0
                    has_time_dirs = False
                    
                    for d in os.listdir(cfd_path):
                        if d.isdigit() and os.path.isdir(os.path.join(cfd_path, d)):
                            has_time_dirs = True
                            step_num = int(d)
                            if step_num > max_time_step:
                                max_time_step = step_num
                    
                    # Consider simulation incomplete if:
                    # 1. case.foam doesn't exist, OR
                    # 2. time directories exist but highest step is < 20
                    incomplete = not case_foam_exists or (has_time_dirs and max_time_step < 20) #TODO: Change to number of steps in controlDict
                    
                    # If it looks incomplete OR user confirms, delete it
                    if incomplete or messagebox.askyesno(
                        "Delete Cancelled Simulation Files?", 
                        f"Delete the cancelled CFD simulation files for flow rate {self.flow_rate.get():.1f} LPM?\n\n"
                        f"This will free up disk space but you'll need to re-run the simulation if needed later."
                    ):
                        self.logger.log_info(f"Deleting cancelled simulation folder: {cfd_path}")
                        shutil.rmtree(cfd_path)
                        self.logger.log_info(f"Successfully deleted simulation folder")
                        return True
                else:
                    self.logger.log_info(f"CFD path not found: {cfd_path}")
            else:
                # For segmentation, check what folders actually exist first
                self.logger.log_info(f"Checking segmentation folder: {self.app.full_folder_path}")
                
                # Get a list of all subdirectories that actually exist
                existing_folders = []
                possible_folders = ["nifti", "prediction", "stl"]
                
                for folder in possible_folders:
                    folder_path = os.path.join(self.app.full_folder_path, folder)
                    if os.path.exists(folder_path) and os.path.isdir(folder_path):
                        existing_folders.append(folder)
                        self.logger.log_info(f"Found existing folder: {folder}")
                
                # If some folders exist, ask if user wants to delete them
                if existing_folders or any(f.endswith(".nii.gz") for f in os.listdir(self.app.full_folder_path)):
                    if messagebox.askyesno(
                        "Delete Cancelled Segmentation Files?", 
                        f"Delete the in-progress segmentation files?\n\n"
                        f"This will free up disk space but you'll need to re-run the segmentation if needed later."
                    ):
                        deleted_something = False
                        
                        # Delete existing folders
                        for folder in existing_folders:
                            folder_path = os.path.join(self.app.full_folder_path, folder)
                            try:
                                self.logger.log_info(f"Deleting folder: {folder_path}")
                                shutil.rmtree(folder_path)
                                deleted_something = True
                            except Exception as e:
                                self.logger.log_error(f"Error deleting {folder_path}: {e}")
                                
                        # Delete prediction NIfTI files
                        nifti_patterns = ["*_pred.nii.gz", "*prediction*.nii.gz", "*_seg.nii.gz", "*.nii.gz"]
                        for pattern in nifti_patterns:
                            for file_path in Path(self.app.full_folder_path).glob(pattern):
                                try:
                                    self.logger.log_info(f"Deleting file: {file_path}")
                                    file_path.unlink()
                                    deleted_something = True
                                except Exception as e:
                                    self.logger.log_error(f"Error deleting {file_path}: {e}")
                        
                        # Delete specific txt files
                        txt_files = ["volume_calculation.txt", "min_csa.txt"]
                        for txt_file in txt_files:
                            txt_path = os.path.join(self.app.full_folder_path, txt_file)
                            if os.path.exists(txt_path):
                                try:
                                    self.logger.log_info(f"Deleting file: {txt_path}")
                                    os.remove(txt_path)
                                    deleted_something = True
                                except Exception as e:
                                    self.logger.log_error(f"Error deleting {txt_path}: {e}")
                        
                        if deleted_something:
                            self.logger.log_info(f"Successfully cleaned up segmentation files")
                            return True
                        else:
                            self.logger.log_info(f"No files were deleted")
                            return False
                    else:
                        self.logger.log_info("User chose not to delete segmentation files")
                        return False
                else:
                    self.logger.log_info("No segmentation files found to delete")
                    return False
                    
            return False
        except Exception as e:
            self.logger.log_error(f"Error during file cleanup: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())
            return False