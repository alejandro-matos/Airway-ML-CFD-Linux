# gui/components/custom_notebook.py

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class EnhancedNotebook(ttk.Notebook):
    """A notebook with enhanced tab styling."""
    
    def __init__(self, parent, **kwargs):
        """Initialize with custom styling for tabs"""
        # Initialize the notebook
        ttk.Notebook.__init__(self, parent, **kwargs)
        
        # Configure style
        self.style = ttk.Style()
        
        # Create custom style for our notebook
        self.style.configure("Enhanced.TNotebook", 
                            background='gray20',
                            borderwidth=0)
        
        # Configure tab appearance
        self.style.configure("Enhanced.TNotebook.Tab",
                            padding=[12, 6],
                            background='gray30',
                            foreground='white',
                            borderwidth=2,
                            relief="raised",
                            font=("Arial", 11))
        
        # Dynamic state mappings
        self.style.map("Enhanced.TNotebook.Tab",
                      background=[("selected", "#007acc"), ("!selected", "gray30")],
                      foreground=[("selected", "white"), ("!selected", "gray80")],
                      relief=[("selected", "ridge"), ("!selected", "groove")])
        
        # Apply our custom style
        self.configure(style="Enhanced.TNotebook")
        
        # Track active tabs with a dictionary of custom frame classes
        self.tab_frames = {}
        
        # Bind tab change events
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def add_styled_tab(self, title, content_color="#333333"):
        """Add a tab with consistent styling and return the content frame"""
        # Create a frame for the tab content
        frame = ctk.CTkFrame(self, fg_color=content_color, corner_radius=0)
        
        # Add to notebook
        self.add(frame, text=title)
        
        # Store reference to the frame
        tab_id = len(self.tab_frames)
        self.tab_frames[tab_id] = {
            'frame': frame,
            'title': title
        }
        
        return frame
    
    def _on_tab_changed(self, event):
        """Handle tab change events with enhanced styling"""
        # Get the selected tab
        selected_tab = self.select()
        selected_index = self.index(selected_tab)
        
        # Instead of trying to style individual tabs, we'll modify the global tab style
        # and force a refresh of the notebook appearance
        
        # First update the tab text to show which one is active
        for i, tab_info in self.tab_frames.items():
            # Update tab text to indicate selection state
            if i == selected_index:
                # Make active tab text bold with asterisks
                new_text = f"• {tab_info['title']} •"
                self.tab(i, text=new_text)
            else:
                # Restore original text for inactive tabs
                self.tab(i, text=tab_info['title'])
        
        # Now update the overall tab style
        self.style.configure("Enhanced.TNotebook.Tab", 
                            padding=[12, 6],
                            background='gray30',
                            foreground='white',
                            borderwidth=2,
                            relief="raised")
        
        # Update the state mappings
        self.style.map("Enhanced.TNotebook.Tab",
                      background=[("selected", "#007acc"), ("!selected", "gray30")],
                      foreground=[("selected", "white"), ("!selected", "gray80")],
                      relief=[("selected", "ridge"), ("!selected", "groove")])
                      
        # Force a visual refresh
        self.update_idletasks()