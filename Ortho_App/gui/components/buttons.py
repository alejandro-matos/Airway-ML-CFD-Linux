# gui/components/buttons.py
from tkinter import Canvas
import customtkinter as ctk
from ..utils.tooltips import ToolTip

class CircularButton(Canvas):
    """A circular button widget with customizable appearance"""
    def __init__(self, parent, text, command=None, diameter=30, **kwargs):
        super().__init__(parent, width=diameter, height=diameter, 
                        bg="gray20", highlightthickness=0)
        
        self.diameter = diameter
        self.command = command

        # Draw the circular button
        self.circle = self.create_oval(
            2, 2, diameter - 2, diameter - 2,
            fill=kwargs.get("bg_color", "blue"),
            outline=kwargs.get("border_color", "white"),
            width=kwargs.get("border_width", 2)
        )
        
        # Add the text
        self.text = self.create_text(
            diameter // 2, diameter // 2,
            text=text,
            fill=kwargs.get("text_color", "white"),
            font=kwargs.get("font", ("Arial", 14, "bold"))
        )

        # Bind click events
        if command:
            self.bind("<Button-1>", lambda event: self.command())

    def change_color(self, new_color):
        """Change the button's background color"""
        self.itemconfig(self.circle, fill=new_color)
    
def _create_info_button(parent, tooltip_text, font=("Arial", 14)):
    """
    Create a circular info button with tooltip
    
    Args:
        parent: The parent widget
        tooltip_text: The text to display in the tooltip
        font: Font to use for tooltip text (default is Arial 16)
        
    Returns:
        CircularButton: The created info button
    """
    info_button = CircularButton(
        parent,
        text="?",
        diameter=30,
        bg_color="#007bff",
        text_color="white",
        border_color="white",
        border_width=1,
        font=("Arial", 14, "bold")
    )
    
    # Create tooltip with specified font
    tooltip = ToolTip(info_button, text=tooltip_text, font=font)
    
    return info_button