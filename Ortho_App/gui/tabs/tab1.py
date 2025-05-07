# gui/tabs/tab1.py

import customtkinter as ctk
from PIL import Image, ImageTk
from customtkinter import CTkImage
import os
import tkinter as tk
import tkinter.messagebox as messagebox
from gui.utils.basic_utils import AppLogger
from gui.config.settings import APP_SETTINGS, UI_SETTINGS, PATH_SETTINGS
from gui.components.buttons import _create_info_button
import json

# Build these once, at import time
USER_DATA_DIR = PATH_SETTINGS["USER_DATA"]

class Tab1Manager:
    def __init__(self, app):
        """Initialize Tab1Manager with a reference to the main app"""
        self.app = app
        self.username_var = app.username_var  # Use the centralized variable
        self.logger = AppLogger()  # Use the shared logger
        
    def create_tab(self):
        """Create and set up the home page"""
        self._create_logo_section()
        self._create_title_section()
        self._create_description_section()
        self._create_contributors_section()
        self._create_username_section()
        self._create_next_button()
        self._create_corner_logos()
        
        # Set focus to username entry and bind enter key
        self.app.bind_enter_key(self.validate_username)
        self.username_entry.focus()

    def _create_logo_section(self):
        """Create the logo section at the top of the page with animated GIF support"""
        logo_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        logo_frame.pack(pady=UI_SETTINGS["PADDING"]["LARGE"])  # More space around logo

        try:
            # Path to the GIF file
            gif_path = os.path.join(PATH_SETTINGS["ICONS_DIR"],PATH_SETTINGS["GIF"])

            # Create a standard Tkinter label (not CTkLabel) for the animated GIF
            self.gif_frames = []
            self.current_frame = 0

            # Add animation control attribute
            self.animation_running = True
            self.animation_after_id = None
            
            # Load the GIF and extract frames
            gif = Image.open(gif_path)
            
            # Determine desired size (adjust as needed)
            w = UI_SETTINGS["LOGO"]["WIDTH"]
            h = UI_SETTINGS["LOGO"]["HEIGHT"]
            
            # Count frames in the GIF
            try:
                frame_count = 0
                while True:
                    # Extract and resize each frame
                    gif.seek(frame_count)
                    frame = gif.copy()
                    frame = frame.resize((w,h), Image.LANCZOS)
                    frame_tk = ImageTk.PhotoImage(frame)
                    self.gif_frames.append(frame_tk)
                    frame_count += 1
            except EOFError:
                # End of frames reached
                pass
            
            # Create a standard tkinter Label (not CTkLabel) for animation
            self.gif_label = tk.Label(logo_frame, image=self.gif_frames[0], bg=self._get_frame_bg_color(logo_frame))
            self.gif_label.pack()
            
            # Start animation if there are multiple frames
            if len(self.gif_frames) > 1:
                self._animate_gif(0)
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load logo: {str(e)}"
            )
            
    def _animate_gif(self, frame_index):
        """Animate the GIF by cycling through frames with safety checks"""
        # Safety check: if label doesn't exist anymore, stop animation
        try:
            if not self.animation_running or not self.gif_label.winfo_exists():
                self.animation_running = False
                return
                
            # Update the image
            self.gif_label.configure(image=self.gif_frames[frame_index])
            
            # Calculate next frame index (loop back to 0 when reaching the end)
            next_frame = (frame_index + 1) % len(self.gif_frames)
            
            # Schedule the next frame update after a delay
            # You can adjust the delay (in ms) to control animation speed
            # Store the after ID so we can cancel it if needed
            delay = UI_SETTINGS["LOGO"]["ANIMATION_DELAY_MS"]
            self.animation_after_id = self.app.after(delay, self._animate_gif, next_frame)
        except Exception as e:
            # If there's any error (like widget destroyed), stop animation
            self.animation_running = False
            self.logger.log_error(f"Animation error: {str(e)}")

    def _stop_animation(self):
        """Stop the GIF animation properly"""
        self.animation_running = False
        if hasattr(self, 'animation_after_id') and self.animation_after_id:
            self.app.after_cancel(self.animation_after_id)
            self.animation_after_id = None
        
    def _get_frame_bg_color(self, frame):
        """Get the background color of the frame for the tkinter Label to match"""
        # Get the actual hex color from the CTkFrame
        if hasattr(frame, 'cget') and frame.cget("fg_color") != "transparent":
            if isinstance(frame.cget("fg_color"), tuple):
                # CTk often uses tuples for colors (light/dark mode)
                return frame.cget("fg_color")[0]  # Use light mode color
            return frame.cget("fg_color")
        # Default to a standard background color if transparent
        return "#F0F0F0"  # Light gray fallback
            
    def _create_title_section(self):
        """Create the title section with app name and welcome message"""
        title_label = ctk.CTkLabel(
            self.app.main_frame,
            text=f"{APP_SETTINGS['TITLE']}\n\nWelcome",
            font=UI_SETTINGS["FONTS"]["TITLE"],  # Using global font settings
            fg_color=UI_SETTINGS["COLORS"]["PRIMARY"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            justify="center",
            width=500,
            height=150
        )
        title_label.pack(fill="x", padx=UI_SETTINGS["PADDING"]["MEDIUM"], pady=UI_SETTINGS["PADDING"]["MEDIUM"])

    def _create_description_section(self):
        """Create the description section with app information"""
        description_text = (
            "Ortho CFD provides orthodontists with upper airway pressure measurements derived from patient 3D scans. "
            "This clinical tool helps quantify breathing obstruction severity and evaluate treatment outcomes.\n"
            "WARNING: Scans must be aligned with the septum to ensure accurate and successful simulations.\n\n"
            "• Upload patient scans in DICOM (.dcm) or NIfTI (.nii.gz) format\n"
            "• Receive detailed pressure differential measurements across the upper airway\n"
            "• Generate concise and informative CFD analysis reports\n\n"

            "Developed at the University of Alberta using medical imaging technology and validated computational models.\n\n"
            "For clinical support:\n"
            "Dr. Silvia Gianoni-Capenakas - capenaka@ualberta.ca\n"
            "Dr. Manuel Lagravere-Vich - manuel@ualberta.ca\n\n"

            "For technical inquiries:\n"
            "Dr. Carlos F. Lange - clange@ualberta.ca\n"
        )

        description_label = ctk.CTkLabel(
            self.app.main_frame,
            text=description_text,
            font=UI_SETTINGS["FONTS"]["NORMAL"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            justify="center",
            wraplength=1000  # Ensures text is readable on wider screens
        )
        description_label.pack(pady=UI_SETTINGS["PADDING"]["MEDIUM"])
    
    def _create_username_section(self):
        """Create the username input section with a modern design"""
        username_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        username_frame.pack(pady=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Label
        username_label = ctk.CTkLabel(
            username_frame,
            text="Enter Username:",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        username_label.pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        # Recreate username entry and bind it to username_var
        self.username_entry = ctk.CTkEntry(
            username_frame,
            textvariable=self.app.username_var,  # Rebind to the reinitialized variable
            width=250,
            height=40,
            fg_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"],
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        )
        self.username_entry.pack(side="left", padx=UI_SETTINGS["PADDING"]["SMALL"])

        # help‑tooltip beside the username field
        info_button = _create_info_button(
            username_frame,
            "Please enter your last name as your username (no spaces or upper case letters)"
        )
        info_button.pack(side="right", padx=UI_SETTINGS["PADDING"]["SMALL"])

    def _create_next_button(self):
        """Create a well-sized 'Next' button with a modern design"""
        next_button = ctk.CTkButton(
            self.app.main_frame,
            text="Next",
            command=self.validate_username,
            width=160,
            height=50,
            font=UI_SETTINGS["FONTS"]["HEADER"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        next_button.pack(pady=(UI_SETTINGS["PADDING"]["MEDIUM"], UI_SETTINGS["PADDING"]["LARGE"]))

    def validate_username(self):
        """Check if username is valid before proceeding"""
        username = self.app.username_var.get().strip()  # Use the centralized variable

        if not username:
            error_message = "Please enter a username."
            self.logger.log_error(error_message)
            tk.messagebox.showerror("Error", error_message)
            return False

        if not username.isalnum():
            error_message = f"Username '{username}' must contain only letters and numbers (e.g. No spaces or special characters)."
            self.logger.log_error(error_message)
            tk.messagebox.showerror("Error", "Username must contain only letters and numbers (e.g. No spaces or special characters).")
            return False
        
        # Define user folder path
        user_folder = os.path.join(USER_DATA_DIR, username)
        
        try:
            os.makedirs(user_folder, exist_ok=True)
            self.logger.log_info(f"User folder created: {user_folder}")
        except Exception as e:
            self.logger.log_error(f"Failed to create user folder: {e}")
            tk.messagebox.showerror("Error", f"Could not create user folder: {e}")
            return False    
        
        self._stop_animation()
        self.logger.log_info(f"User logged in: {username}")
        self.app.stored_username = username
        self.app.create_tab2()  # Navigate to next tab
        return True

    def _create_corner_logos(self):
        """Add logos to the bottom left and right corners of the main frame"""
        # Create a frame for the bottom area that will contain both logos
        bottom_frame = ctk.CTkFrame(self.app.main_frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=UI_SETTINGS["PADDING"]["SMALL"])
        
        # Left corner logo
        try:
            left_logo_path = os.path.join(PATH_SETTINGS["ICONS_DIR"], "CFDLab-blogo2.png")
            left_logo_img = Image.open(left_logo_path)
            
            # Desired new height
            new_height = 45
            # Calculate the new width to maintain aspect ratio
            original_width, original_height = left_logo_img.size
            aspect_ratio = original_width / original_height
            new_width = int(new_height * aspect_ratio)

            # Resize with the new dimensions
            resized_img = left_logo_img.resize((new_width, new_height), Image.LANCZOS)

            # Convert to CTkImage
            left_ctk_img = CTkImage(light_image=resized_img, dark_image=resized_img, size=(new_width, new_height))

            # Create label with the image
            left_logo_label = ctk.CTkLabel(bottom_frame, image=left_ctk_img, text="")
            left_logo_label.pack(side="left", padx=UI_SETTINGS["PADDING"]["MEDIUM"])

        except Exception as e:
            self.logger.log_error(f"Failed to load left corner logo: {str(e)}")
        
        # Add a spacer in the middle to push logos to corners
        spacer = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
        # Right corner logo
        try:
            right_logo_path = os.path.join(PATH_SETTINGS["ICONS_DIR"], "UpperAirwaySegmentator3.png")
            right_logo_img = Image.open(right_logo_path)
            
            # Desired new height
            new_height = 80
            # Calculate the new width to maintain aspect ratio
            original_width, original_height = right_logo_img.size
            aspect_ratio = original_width / original_height
            new_width = int(new_height * aspect_ratio)

            # Resize with the new dimensions
            resized_img = right_logo_img.resize((new_width, new_height), Image.LANCZOS)

            # Convert to CTkImage
            right_ctk_img = CTkImage(light_image=resized_img, dark_image=resized_img, size=(new_width, new_height))

            # Create label with the image
            right_logo_label = ctk.CTkLabel(bottom_frame, image=right_ctk_img, text="")
            right_logo_label.pack(side="right", padx=UI_SETTINGS["PADDING"]["MEDIUM"])
        except Exception as e:
            self.logger.log_error(f"Failed to load right corner logo: {str(e)}")
    
    # =================================================================================
    # ==================== FOR CONTRIBUTORS SECTION ===================================
    # =================================================================================

    def _create_contributors_section(self):
        """Create a side-expandable panel that displays contributors without affecting layout"""
        # Track panel state
        self.panel_visible = False
        
        # Define panel width - we'll need this consistently
        self.panel_width = 300
        
        # Create the vertical tab button on the right edge
        self.toggle_panel_button = ctk.CTkButton(
            self.app.main_frame,
            text="Click to see \nContributors / Team",
            font=UI_SETTINGS["FONTS"]["CONTRIB_BUTTON"],
            fg_color=UI_SETTINGS["COLORS"]["SECONDARY"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            width=40,
            height=200,
            corner_radius=10,
            command=self._toggle_contributors_panel
        )
        # Place the button at the right edge, vertically centered
        self.toggle_panel_button.place(relx=0.98, rely=0.1, anchor="e")
        
        # Create the panel that will be shown/hidden (initially hidden)
        # CRITICAL: Set width and height here in the constructor, not in place()
        self.contributors_panel = ctk.CTkFrame(
            self.app.main_frame,  # Attach directly to main_frame
            fg_color=UI_SETTINGS["COLORS"]["PANEL_BG"],
            width=self.panel_width,  # Must set width here
            height=600,  # Set a reasonable height - will be adjusted by relheight
            corner_radius=10
        )
        # Note: We don't place it yet - will be placed when shown
        
        # Load contributors data
        self.contributors_data = self._load_contributors_data()
        
        # Pre-build the contributors panel content
        self._build_contributors_panel()

    def _toggle_contributors_panel(self):
        """Toggle the visibility of the side contributors panel"""
        if not self.panel_visible:
            # Calculate the position for the panel (right side, full height)
            button_width = 40  # Width of the toggle button
            
            # Position the panel to the left of the button
            # relx=1.0 means right edge, then offset by button_width + a small gap
            self.contributors_panel.place(
                relx=1.0, 
                rely=0.0, 
                anchor="ne",  # North-east (top-right) corner
                relheight=1.0,  # Full height relative to parent
                x=-(button_width + 5)  # Offset to the left of the button (with 5px gap)
            )
            
            # Update button text
            self.toggle_panel_button.configure(text="Close")
            
            # Update state
            self.panel_visible = True
        else:
            # Hide the panel
            self.contributors_panel.place_forget()
            
            # Reset button text
            self.toggle_panel_button.configure(text="Click for \nContributors / Team")
            
            # Update state
            self.panel_visible = False

    def _build_contributors_panel(self):
        """Build the contents of the contributors panel"""
        # Add a header with close button
        header_frame = ctk.CTkFrame(
            self.contributors_panel, 
            fg_color=UI_SETTINGS["COLORS"]["SECONDARY"],
            corner_radius=0
        )
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Title label
        title_label = ctk.CTkLabel(
            header_frame,
            text="Contributors & Development Team",
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # Close button (X)
        close_button = ctk.CTkButton(
            header_frame,
            text="×",
            width=30,
            height=30,
            font=UI_SETTINGS["FONTS"]["LARGE_SYMBOL"],
            fg_color="transparent",
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
            command=self._toggle_contributors_panel
        )
        close_button.pack(side="right", padx=5, pady=5)
        
        # Create scrollable frame for contributors
        scrollable_frame = ctk.CTkScrollableFrame(
            self.contributors_panel,
            fg_color="transparent",
            width=330
        )
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add contributors to the scrollable frame
        for contributor in self.contributors_data:
            self._create_contributor_card(scrollable_frame, contributor)

    def _create_contributor_card(self, parent_frame, contributor):
        """Create a visual card for a single contributor"""
        # Create a card frame for the contributor
        card = ctk.CTkFrame(parent_frame, fg_color=UI_SETTINGS["COLORS"]["CARD_BG"])
        card.pack(fill="x", padx=5, pady=5)
        
        # Name with larger font
        name_label = ctk.CTkLabel(
            card,
            text=contributor["name"],
            font=UI_SETTINGS["FONTS"]["CONTRIB_NAME"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        )
        name_label.pack(padx=10, pady=(5, 2), anchor="w")
        
        # Title
        title_label = ctk.CTkLabel(
            card,
            text=contributor["title"],
            font=UI_SETTINGS["FONTS"]["NORMAL_ITALIC"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
        )
        title_label.pack(padx=10, pady=1, anchor="w")
        
        # Department
        if "department" in contributor:
            dept_label = ctk.CTkLabel(
                card,
                text=contributor["department"],
                font=UI_SETTINGS["FONTS"]["SMALL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_DARK"]
            )
            dept_label.pack(padx=10, pady=1, anchor="w")
        
        # Email 
        if "email" in contributor:
            email_label = ctk.CTkLabel(
                card,
                text=contributor["email"],
                font=UI_SETTINGS["FONTS"]["SMALL_CONTR"],
                text_color=UI_SETTINGS["COLORS"]["LINK"]  # Keeps the same color for visual consistency
            )
            email_label.pack(padx=10, pady=(1, 5), anchor="w")

    def _load_contributors_data(self):
        """Load contributors data from a JSON file"""
        contributors_file = PATH_SETTINGS["CONTRIB_DIR"]
        
        # Load existing contributors data with error handling
        try:
            if os.path.exists(contributors_file):
                with open(contributors_file, 'r') as f:
                    data = json.load(f)
                    self.logger.log_info(f"Successfully loaded {len(data)} contributors")
                    return data
            else:
                self.logger.log_error(f"Contributors file not found: {contributors_file}")
                # Handling if contributor file is not found
                return [
                    {
                        "name": "Carlos F. Lange, Ph.D., P.Eng.",
                        "title": "Associate Professor, Faculty of Engineering",
                        "email": "clange@ualberta.ca",
                        "department": "Mechanical Engineering"
                    },
                    {
                        "name": "Manuel Lagravere Vich, DDS, Ph.D.",
                        "title": "Professor, Faculty of Medicine & Dentistry",
                        "email": "manuel@ualberta.ca",
                        "department": "Dentistry"
                    },
                    {
                        "name": "Silvia Gianoni-Capenakas, DDS, Ph.D.",
                        "title": "Professor, Faculty of Medicine & Dentistry",
                        "email": "capenaka@ualberta.ca",
                        "department": "Dentistry"
                    },
                    {
                        "name": "Alejandro Matos Camarillo, MSc.",
                        "title": "Research Assistant",
                        "email": "amatos@ualberta.ca",
                        "department": "Mechanical Engineering"
                    },
                    {
                        "name": "Uday Tummala, MSc.",
                        "title": "Research Assistant",
                        "email": "utummala@ualberta.ca",
                        "department": "Mechanical Engineering"
                    }
                ]
        except json.JSONDecodeError as e:
            # Specific handling in case JSON file contains syntax errors
            self.logger.log_error(f"JSON syntax error in contributors file: {str(e)}")
            messagebox.showwarning(
                "Contributors File Error", 
                f"The contributors.json file contains syntax errors. Using default contributors instead.\n\nDetails: {str(e)}"
            )
            # Return updated contributors list (from user's input)
            return [
                {
                    "name": "Carlos F. Lange, Ph.D., P.Eng.",
                    "title": "Associate Professor, Faculty of Engineering",
                    "email": "clange@ualberta.ca",
                    "department": "Mechanical Engineering"
                },
                {
                    "name": "Manuel Lagravere Vich, DDS, Ph.D.",
                    "title": "Professor, Faculty of Medicine & Dentistry",
                    "email": "manuel@ualberta.ca",
                    "department": "Dentistry"
                },
                {
                    "name": "Silvia Gianoni-Capenakas, DDS, Ph.D.",
                    "title": "Professor, Faculty of Medicine & Dentistry",
                    "email": "capenaka@ualberta.ca",
                    "department": "Dentistry"
                },
                {
                    "name": "Alejandro Matos Camarillo, MSc.",
                    "title": "Research Assistant",
                    "email": "amatos@ualberta.ca",
                    "department": "Mechanical Engineering"
                },
                {
                    "name": "Uday Tummala, MSc.",
                    "title": "Research Assistant",
                    "email": "utummala@ualberta.ca",
                    "department": "Mechanical Engineering"
                }
            ]
        except Exception as e:
            # General error handling
            self.logger.log_error(f"Failed to load contributors data: {str(e)}")
            return []
