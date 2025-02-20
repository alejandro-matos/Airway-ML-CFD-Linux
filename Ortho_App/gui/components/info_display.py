# gui/components/info_display.py
# InfoDisplay: Frame for displaying information such as patient details, results, etc.
import customtkinter as ctk
from config.settings import UI_SETTINGS

class InfoDisplay(ctk.CTkFrame):
    """A frame for displaying information with a title and content"""
    def __init__(self, parent, title, content_dict):
        super().__init__(parent, corner_radius=10)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=UI_SETTINGS["FONTS"]["HEADER"]
        )
        self.title_label.pack(pady=(10, 5))
        
        # Content
        for key, value in content_dict.items():
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            key_label = ctk.CTkLabel(
                row,
                text=f"{key}:",
                font=UI_SETTINGS["FONTS"]["NORMAL"]
            )
            key_label.pack(side="left", padx=5)
            
            value_label = ctk.CTkLabel(
                row,
                text=str(value),
                font=UI_SETTINGS["FONTS"]["NORMAL"]
            )
            value_label.pack(side="left", padx=5)