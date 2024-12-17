# gui/components/buttons.py
from tkinter import Canvas
import customtkinter as ctk

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
            font=kwargs.get("font", ("Arial", 12, "bold"))
        )

        # Bind click events
        if command:
            self.bind("<Button-1>", lambda event: self.command())

    def change_color(self, new_color):
        """Change the button's background color"""
        self.itemconfig(self.circle, fill=new_color)