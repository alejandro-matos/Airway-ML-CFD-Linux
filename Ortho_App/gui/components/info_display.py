# gui/components/info_display.py
# InfoDisplay: Frame for displaying information such as patient details, results, etc.
import customtkinter as ctk

class InfoDisplay(ctk.CTkFrame):
    """A frame for displaying information with a title and content"""
    def __init__(self, parent, title, content_dict):
        super().__init__(parent, corner_radius=10)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=("Arial", 15, "bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Content
        for key, value in content_dict.items():
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            key_label = ctk.CTkLabel(
                row,
                text=f"{key}:",
                font=("Arial", 12)
            )
            key_label.pack(side="left", padx=5)
            
            value_label = ctk.CTkLabel(
                row,
                text=str(value),
                font=("Arial", 12)
            )
            value_label.pack(side="left", padx=5)