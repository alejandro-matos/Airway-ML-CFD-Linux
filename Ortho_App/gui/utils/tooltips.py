# gui/utils/tooltips.py
import tkinter as tk

class ToolTip:
    """
    Creates a tooltip for a given widget with customizable appearance.
    """
    def __init__(self, widget, text, font=("Arial", 12)):
        self.widget = widget
        self.text = text
        self.font = font
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        """Display the tooltip window with text."""
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        # make the window itself lightyellow, no highlight/border
        self.tooltip_window.configure(bg="lightyellow", highlightthickness=0, bd=0)
        self.tooltip_window.geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            bg="lightyellow",        # match the window bg
            relief="flat",           # no border
            borderwidth=0,
            font=self.font,
            wraplength=650,
            justify="left",
            anchor="w",
            padx=10, pady=8          # internal padding now
        )
        label.pack(fill="both")
        
    def hide_tooltip(self, event=None):
        """Hide/destroy the tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None