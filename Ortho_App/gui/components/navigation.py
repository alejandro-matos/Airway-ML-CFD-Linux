# gui/components/navigation.py
import customtkinter as ctk

class NavigationFrame(ctk.CTkFrame):
    """A navigation frame with back/next buttons and labels"""
    def __init__(self, parent, previous_label="", next_label="", 
                 back_command=None, next_command=None):
        super().__init__(parent, corner_radius=10)
        
        # Back button section
        self.back_frame = self._create_button_frame("Back", previous_label, back_command)
        self.back_frame.pack(side="left", padx=20)
        
        # Next button section
        self.next_frame = self._create_button_frame("Next", next_label, next_command)
        self.next_frame.pack(side="right", padx=20)

    def _create_button_frame(self, button_text, label_text, command):
        """Create a frame containing a button and its label"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        
        button = ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            width=100,
            font=("Times_New_Roman", 16)
        )
        button.pack(pady=(5, 0))

        if label_text:
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=("Arial", 12),
                text_color="gray"
            )
            label.pack(pady=(0, 0))
            
        return frame