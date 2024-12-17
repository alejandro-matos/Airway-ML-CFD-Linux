# gui/components/forms.py
import customtkinter as ctk

class LabeledEntry(ctk.CTkFrame):
    """A frame containing a label and entry field"""
    def __init__(self, parent, label_text, variable, **kwargs):
        super().__init__(parent, fg_color="transparent")
        
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=kwargs.get("label_font", ("Arial", 12))
        )
        self.label.pack(side="left", padx=5)

        self.entry = ctk.CTkEntry(
            self,
            textvariable=variable,
            width=kwargs.get("width", 200),
            fg_color="white",
            text_color="black"
        )
        self.entry.pack(side="left", padx=5)

class FormSection(ctk.CTkFrame):
    """A section of the form with a title and content"""
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, corner_radius=10)
        
        self.title = ctk.CTkLabel(
            self,
            text=title,
            font=("Arial", 15, "bold")
        )
        self.title.pack(pady=(10, 5), anchor="w")
        
        self.content = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.content.pack(fill="both", expand=True, padx=10, pady=5)