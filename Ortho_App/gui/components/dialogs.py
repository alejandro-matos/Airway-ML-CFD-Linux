# gui/components/dialogs.py
import customtkinter as ctk

class ConfirmationDialog(ctk.CTkToplevel):
    """A custom confirmation dialog"""
    def __init__(self, parent, title, message):
        super().__init__(parent)
        
        self.title(title)
        self.result = False
        
        # Message
        message_label = ctk.CTkLabel(
            self,
            text=message,
            wraplength=300
        )
        message_label.pack(pady=20, padx=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="Yes",
            command=self._on_yes
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="No",
            command=self._on_no
        ).pack(side="left", padx=10)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()