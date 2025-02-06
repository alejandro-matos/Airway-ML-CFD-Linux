import customtkinter as ctk
from tkinter import ttk

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
        
        # Progress bar that supports both determinate and indeterminate modes
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
            height=150,
            font=("Courier", 10)
        )
        self.output_text.pack(fill="both", expand=True)
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            self,
            text="Cancel",
            command=self._cancel_callback,
            width=100,
            state="disabled"
        )
        self.cancel_button.pack(pady=5)
        
        self._cancel_callback = None

    def _safe_update(self, func):
        """Safely update GUI from any thread"""
        if self.winfo_exists():
            self.parent.after(0, func)
        
    def set_cancel_callback(self, callback):
        """Set the callback for cancel button"""
        self._cancel_callback = callback
        self._safe_update(
            lambda: self.cancel_button.configure(state="normal" if callback else "disabled")
        )
        
    def _cancel_callback(self):
        """Internal cancel callback"""
        if self._cancel_callback:
            self._cancel_callback()
            
    def start(self, message="Processing...", indeterminate=False):
        """Start the progress bar with a message"""
        def _start():
            self.progress_label.configure(text=message)
            self.output_text.delete("1.0", "end")
            
            if indeterminate:
                self.progress_bar.configure(mode='indeterminate')
                self.progress_bar.start(10)  # Start animation, update every 10ms
            else:
                self.progress_bar.configure(mode='determinate')
                self.progress_bar['value'] = 0
                
            self.cancel_button.configure(state="normal" if self._cancel_callback else "disabled")
        
        self._safe_update(_start)
        
    def stop(self, message="Complete"):
        """Stop the progress bar and update message"""
        def _stop():
            # Explicitly stop the progress bar animation
            self.progress_bar.stop()
            # Reset the value to 0 for consistency
            self.progress_bar['value'] = 0

            # Update the progress label
            self.progress_label.configure(text=message)
            # Disable the cancel button
            self.cancel_button.configure(state="disabled")
        
        self._safe_update(_stop)

        
    def update_progress(self, value, message=None, output_line=None):
        """Update progress bar value and optionally add output line"""
        def _update():
            if self.progress_bar['mode'] == 'determinate':
                self.progress_bar['value'] = value
                
            if message:
                self.progress_label.configure(text=message)
                
            if output_line:
                self.output_text.insert("end", output_line + "\n")
                self.output_text.see("end")  # Auto-scroll to bottom
        
        self._safe_update(_update)
            
    def clear_output(self):
        """Clear the output text"""
        self._safe_update(lambda: self.output_text.delete("1.0", "end"))