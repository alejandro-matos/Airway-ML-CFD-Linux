import customtkinter as ctk
from tkinter import ttk
from gui.config.settings import UI_SETTINGS

class ProgressSection(ctk.CTkFrame):
    """A progress section with progress bar and output display"""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent  # Store parent for after() calls
        
        # Progress label with improved font
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 12)
        )
        self.progress_label.pack(pady=(0, 5))
        
        # Frame to contain progress bar and ensure consistent width
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=50, pady=(0, 10))
        
        # Progress bar that supports both determinate and indeterminate modes (only got indeterminate to work so far)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            maximum=100
        )
        self.progress_bar.pack(fill="x", expand=True)
        
        # Output text display
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Output text with scrollbar
        self.output_text = ctk.CTkTextbox(
            self.output_frame,
            height=100,
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        )
        self.output_text.pack(fill="both", expand=True)
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            self,
            text="Cancel",
            command=self._handle_cancel,
            width=100,
            state="disabled",
            font=UI_SETTINGS["FONTS"]["NORMAL"]
        )
        self.cancel_button.pack(pady=5)
        
        # Renamed attribute to avoid conflict with method name
        self._cancel_callback_func = None
        # Track whether cancellation is in progress
        self.cancellation_in_progress = False

    def _safe_update(self, func):
        """Safely update GUI from any thread"""
        if self.winfo_exists():
            self.parent.after(0, func)
        
    def set_cancel_callback(self, callback):
        """Set the callback for cancel button"""
        self._cancel_callback_func = callback
        self.cancellation_in_progress = False  # Reset cancellation flag when setting a new callback
        self._safe_update(
            lambda: self.cancel_button.configure(state="normal" if callback else "disabled")
        )
        
    def _handle_cancel(self):
        """Internal method to handle cancel button click"""
        if self._cancel_callback_func and not self.cancellation_in_progress:
            # Disable the cancel button immediately to prevent multiple clicks
            self.cancel_button.configure(state="disabled")
            # Set the cancellation flag
            self.cancellation_in_progress = True
            # Update the progress label to show cancellation is in progress
            self.progress_label.configure(
                text="Cancellation in progress...",
                text_color="orange"  # Visual indication
            )
            # Add a message to the output
            self.output_text.insert("end", "Cancellation requested. Stopping process...\n")
            self.output_text.see("end")
            # Call the actual cancellation callback
            self._cancel_callback_func()
            
    def start(self, message="Processing...", indeterminate=False):
        """Start the progress bar with a message"""
        def _start():
            # Reset cancellation flag
            self.cancellation_in_progress = False
            
            self.progress_label.configure(
                text=message,
                font=UI_SETTINGS["FONTS"]["NORMAL"],
                text_color=UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
            )
            self.output_text.delete("1.0", "end")
            
            if indeterminate:
                self.progress_bar.configure(mode='indeterminate')
                self.progress_bar.start(50)  # Start animation, update every 50ms
            else:
                self.progress_bar.configure(mode='determinate')
                self.progress_bar['value'] = 0
                
            self.cancel_button.configure(state="normal" if self._cancel_callback_func else "disabled")
        
        self._safe_update(_start)
        
    def stop(self, message="Complete"):
        """Stop the progress bar and update message"""
        def _stop():
            # Explicitly stop the progress bar animation
            self.progress_bar.stop()
            # Reset the value to 0 for consistency
            self.progress_bar['value'] = 0

            # Update the progress label with appropriate color based on message
            text_color = UI_SETTINGS["COLORS"]["TEXT_LIGHT"]
            if "Cancel" in message:
                text_color = "orange"
            elif "Error" in message:
                text_color = "red"
            elif "Complete" in message:
                text_color = "green"
                
            self.progress_label.configure(
                text=message,
                text_color=text_color
            )
            
            # Reset cancellation flag
            self.cancellation_in_progress = False
            # Disable the cancel button
            self.cancel_button.configure(state="disabled")
            # Add a final message to the output if it was a cancellation
            if "Cancel" in message:
                self.output_text.insert("end", "Process was cancelled by user.\n")
                self.output_text.see("end")
        
        self._safe_update(_stop)

        
    def update_progress(self, value, message=None, output_line=None):
        """Update progress bar value and optionally add output line"""
        def _update():
            if not self.cancellation_in_progress:
                if self.progress_bar['mode'] == 'determinate':
                    self.progress_bar['value'] = value
                    
                if message:
                    self.progress_label.configure(text=message)
                
            # Always show output lines even during cancellation
            if output_line:
                self.output_text.insert("end", output_line + "\n")
                self.output_text.see("end")  # Auto-scroll to bottom
        
        self._safe_update(_update)
            
    def clear_output(self):
        """Clear the output text"""
        self._safe_update(lambda: self.output_text.delete("1.0", "end"))
        
    def is_cancellation_in_progress(self):
        """Check if cancellation is in progress"""
        return self.cancellation_in_progress