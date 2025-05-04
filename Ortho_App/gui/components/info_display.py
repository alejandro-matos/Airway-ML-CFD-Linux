# gui/components/info_display.py
# InfoDisplay: Frame for displaying information such as patient details, results, etc.
import customtkinter as ctk
from gui.config.settings import UI_SETTINGS

class InfoDisplay(ctk.CTkFrame):
    def __init__(self, parent, title, info_dict, **kwargs):
        """
        Create an information display panel
        
        Args:
            parent: The parent widget
            title: The title for this info panel
            info_dict: Dictionary of information to display as key-value pairs
            **kwargs: Additional arguments to pass to CTkFrame
        """
        super().__init__(parent, corner_radius=10, **kwargs)
        
        # Create title
        ctk.CTkLabel(
            self,
            text=title,
            font=UI_SETTINGS["FONTS"]["HEADER"],
            text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
        ).pack(pady=(10, 5))
        
        # Create content frame with grid layout
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Configure grid to center the form
        content_frame.columnconfigure(0, weight=1)  # Right-aligned labels
        content_frame.columnconfigure(1, weight=1)  # Left-aligned values
        
        # Populate with info
        for row, (key, value) in enumerate(info_dict.items()):
            # Key label with bold font, right-aligned
            key_label = ctk.CTkLabel(
                content_frame,
                text=f"{key}:",
                font=UI_SETTINGS["FONTS"]["CATEGORY"],  # Make the category name bold
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                anchor="e",  # Right-align the text
                width=170
            )
            key_label.grid(row=row, column=0, pady=1, padx=(0, 10), sticky="e")
            
            # Value label, left-aligned
            value_label = ctk.CTkLabel(
                content_frame,
                text=str(value),
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"],
                anchor="w",  # Left-align the text
                width=200
            )
            value_label.grid(row=row, column=1, pady=1, sticky="w")