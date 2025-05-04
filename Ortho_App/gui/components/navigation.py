import customtkinter as ctk
from gui.config.settings import UI_SETTINGS

class NavigationFrame(ctk.CTkFrame):
    """A navigation frame with back/next buttons and labels, ensuring no duplicates"""
    def __init__(self, parent, previous_label="", next_label="", 
                 back_command=None, next_command=None):
        
        # First, remove any existing NavigationFrame instances in the parent
        for widget in parent.winfo_children():
            if isinstance(widget, NavigationFrame):
                widget.destroy()

        # Set background color to provide an outline effect
        super().__init__(parent, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        # Create container for back button
        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=40, pady=(5, 10))  # Ensure spacing

        # Create container for next button
        self.next_frame = self._create_button_frame("Next", next_label, next_command)
        self.next_frame.pack(side="right", padx=40, pady=(5, 10))  # Ensure spacing

        # Store references to parent, commands, and buttons for later use
        self.parent = parent
        self.back_command = back_command
        self.next_command = next_command
        
        # Store reference to the buttons
        self.back_button = None
        self.next_button = None

    def _create_button_frame(self, button_text, label_text, command):
        """Create a frame containing a label above a button"""
        frame = ctk.CTkFrame(self, fg_color="transparent")

        if label_text:
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
                text_color="gray70"
            )
            label.pack(side="top", pady=(0, 5))  # Keep label above button

        button = ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            width=150,
            height=50,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        )
        button.pack(side="top")  # Button stays below label
        
        # Store button references
        if button_text == "Back":
            self.back_button = button
        elif button_text == "Next":
            self.next_button = button

        return frame

class NavigationFrame2(ctk.CTkFrame):
    """A navigation frame with back/next buttons and labels, ensuring no duplicates"""
    def __init__(self, parent, previous_label="", next_label="", 
                 back_command=None, next_command=None):
        
        # First, remove any existing NavigationFrame instances in the parent
        for widget in parent.winfo_children():
            if isinstance(widget, NavigationFrame):
                widget.destroy()

        # Set background color to provide an outline effect
        super().__init__(parent, fg_color=UI_SETTINGS["COLORS"]["BACKGROUND"], corner_radius=10)
        self.pack(fill="x", side="bottom", padx=UI_SETTINGS["PADDING"]["LARGE"], pady=10)

        # Create container for back button
        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=40, pady=(5, 10))  # Ensure spacing
        
        # Store references for later use
        self.parent = parent
        self.back_command = back_command
        self.back_button = None
        
    def _create_button_frame(self, button_text, label_text, command):
        """Create a frame containing a label above a button"""
        frame = ctk.CTkFrame(self, fg_color="transparent")

        if label_text:
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=UI_SETTINGS["FONTS"]["BUTTON_LABEL"],
                text_color="gray70"
            )
            label.pack(side="top", pady=(0, 5))  # Keep label above button

        button = ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            width=150,
            height=50,
            font=UI_SETTINGS["FONTS"]["BUTTON_TEXT"],
            fg_color=UI_SETTINGS["COLORS"]["NAV_BUTTON"],
            hover_color=UI_SETTINGS["COLORS"]["NAV_HOVER"]
        )
        button.pack(side="top")  # Button stays below label
        
        # Store button reference
        if button_text == "Back":
            self.back_button = button

        return frame