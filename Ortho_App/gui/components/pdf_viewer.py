import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import sys
import threading
import fitz  # PyMuPDF
from ..utils.basic_utils import AppLogger

class PDFViewerFrame(ctk.CTkFrame):
    """A frame that displays a PDF file within the application"""
    def __init__(self, master, pdf_path=None, ui_settings=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pdf_path = pdf_path
        self.current_page = 0
        self.page_count = 0
        self.zoom_level = 0.6
        self.images = []  # Store converted page images
        self.ui_settings = ui_settings  # Pass UI settings from main app
        self.logger = AppLogger()  # Initialize logger for error tracking
        self.close_callback = None
        
        self._create_ui()
        if pdf_path:
            self.load_pdf(pdf_path)
    
    def _create_ui(self):
        """Create the UI components for the PDF viewer"""
        # Use UI settings if provided, otherwise use defaults
        button_font = self.ui_settings["FONTS"]["BUTTON_TEXT"] if self.ui_settings else ("Arial", 12)
        normal_font = self.ui_settings["FONTS"]["NORMAL"] if self.ui_settings else ("Arial", 12)
        button_color = self.ui_settings["COLORS"]["REG_BUTTON"] if self.ui_settings else "#3498db"
        button_hover = self.ui_settings["COLORS"]["REG_HOVER"] if self.ui_settings else "#2980b9"
        
        # Top toolbar
        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.pack(fill="x", side="top", padx=5, pady=5)
        
        # Navigation buttons
        self.prev_button = ctk.CTkButton(
            self.toolbar, 
            text="< Previous",
            command=self._previous_page,
            width=100,
            height=30,
            font=button_font,
            fg_color=button_color,
            hover_color=button_hover,
        )
        self.prev_button.pack(side="left", padx=5)
        
        # Page indicator
        self.page_indicator = ctk.CTkLabel(
            self.toolbar,
            text="Page 0 of 0",
            width=100,
            font=normal_font,
        )
        self.page_indicator.pack(side="left", padx=10)
        
        # Next button
        self.next_button = ctk.CTkButton(
            self.toolbar, 
            text="Next >",
            command=self._next_page,
            width=100,
            height=30,
            font=button_font,
            fg_color=button_color,
            hover_color=button_hover,
        )
        self.next_button.pack(side="left", padx=5)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        zoom_frame.pack(side="right", padx=10)
        
        self.zoom_out_button = ctk.CTkButton(
            zoom_frame,
            text="−",
            command=self._zoom_out,
            width=40,
            height=30,
            font=button_font,
            fg_color=button_color,
            hover_color=button_hover,
        )
        self.zoom_out_button.pack(side="left", padx=2)
        
        self.zoom_indicator = ctk.CTkLabel(
            zoom_frame,
            text="60%",
            width=60,
            font=normal_font,
        )
        self.zoom_indicator.pack(side="left", padx=5)
        
        self.zoom_in_button = ctk.CTkButton(
            zoom_frame,
            text="+",
            command=self._zoom_in,
            width=40,
            height=30,
            font=button_font,
            fg_color=button_color,
            hover_color=button_hover,
        )
        self.zoom_in_button.pack(side="left", padx=2)
        
        # Close button
        self.close_button = ctk.CTkButton(
            self.toolbar,
            text="Close",
            command=self._close_viewer,
            width=80,
            height=30,
            font=button_font,
            fg_color="#e74c3c",  # Red color for close button
            hover_color="#c0392b",
        )
        self.close_button.pack(side="right", padx=5)
        
        # Create a frame to contain the page display with scrollbars
        self.display_container = ctk.CTkFrame(self)
        self.display_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add scrollbars
        self.v_scrollbar = ctk.CTkScrollbar(self.display_container)
        self.v_scrollbar.pack(side="right", fill="y")
        
        self.h_scrollbar = ctk.CTkScrollbar(self.display_container, orientation="horizontal")
        self.h_scrollbar.pack(side="bottom", fill="x")
        
        # Canvas for displaying the PDF page
        self.canvas = tk.Canvas(
            self.display_container,
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Connect scrollbars to canvas
        self.v_scrollbar.configure(command=self.canvas.yview)
        self.h_scrollbar.configure(command=self.canvas.xview)
        
        # Add mouse wheel bindings for scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows and macOS
        # self.canvas.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up tk
        # self.canvas.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down tk
        
        # Placeholder message
        self.canvas.create_text(
            self.canvas.winfo_reqwidth() // 2,
            self.canvas.winfo_reqheight() // 2,
            text="No PDF loaded",
            font=("Arial", 14),
            fill="gray"
        )
        
        # Update navigation buttons
        self._update_navigation()
    
    def load_pdf(self, pdf_path):
        """Load a PDF file and convert its pages to images"""
        try:
            self.fitz = fitz
            
            self.pdf_path = pdf_path
            self.doc = fitz.open(pdf_path)
            self.page_count = len(self.doc)
            self.current_page = 0
            
            # Pre-render the first few pages
            self.images = []
            for i in range(min(3, self.page_count)):  # Pre-render first 3 pages
                self._render_page(i)
            
            # Update navigation and display first page
            self._update_navigation()
            self._display_current_page()
            
        except ImportError:
            from tkinter import messagebox
            messagebox.showerror(
                "Error", 
                "PyMuPDF (fitz) library is required for PDF viewing. "
                "Please install it with: pip install PyMuPDF"
            )
            self.logger.log_error("PyMuPDF library not found when trying to load PDF")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")
            self.logger.log_error(f"Error loading PDF: {str(e)}")
    
    def _render_page(self, page_num):
        """Render a specific page to an image"""
        try:
            # Ensure we have enough slots in our images list
            while len(self.images) <= page_num:
                self.images.append(None)
                
            if self.images[page_num] is None:
                page = self.doc.load_page(page_num)
                # Use the stored fitz module
                pix = page.get_pixmap(matrix=self.fitz.Matrix(2, 2))  # Scale factor for better quality
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                self.images[page_num] = img
            
            return self.images[page_num]
        except AttributeError:
            # This might happen if fitz isn't available or properly initialized
            self.logger.log_error("PyMuPDF not properly initialized when rendering page")
            return None
        except Exception as e:
            self.logger.log_error(f"Error rendering page {page_num}: {str(e)}")
            return None
    
    def _display_current_page(self):
        """Display the current page on the canvas"""
        if not hasattr(self, 'doc') or self.current_page >= self.page_count:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        # Get the current page image
        img = self._render_page(self.current_page)
        if img is None:
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text=f"Error loading page {self.current_page + 1}",
                font=("Arial", 14),
                fill="red"
            )
            return
        
        # Apply zoom
        if self.zoom_level != 1.0:
            new_width = int(img.width * self.zoom_level)
            new_height = int(img.height * self.zoom_level)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to Tkinter PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Keep a reference to avoid garbage collection
        self.current_photo = photo
        
        # Display on canvas
        self.canvas.create_image(0, 0, anchor="nw", image=photo)
        
        # Update canvas scroll region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Update page indicator
        self.page_indicator.configure(text=f"Page {self.current_page + 1} of {self.page_count}")
    
    def _next_page(self):
        """Go to the next page"""
        if hasattr(self, 'doc') and self.current_page < self.page_count - 1:
            self.current_page += 1
            self._display_current_page()
            self._update_navigation()
    
    def _previous_page(self):
        """Go to the previous page"""
        if hasattr(self, 'doc') and self.current_page > 0:
            self.current_page -= 1
            self._display_current_page()
            self._update_navigation()
    
    def _update_navigation(self):
        """Update navigation buttons based on current state"""
        if not hasattr(self, 'doc'):
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            self.page_indicator.configure(text="Page 0 of 0")
            return
            
        # Enable/disable previous button
        if self.current_page <= 0:
            self.prev_button.configure(state="disabled")
        else:
            self.prev_button.configure(state="normal")
            
        # Enable/disable next button
        if self.current_page >= self.page_count - 1:
            self.next_button.configure(state="disabled")
        else:
            self.next_button.configure(state="normal")
    
    def _zoom_in(self):
        """Increase zoom level"""
        if self.zoom_level < 3.0:  # Maximum zoom of 300%
            self.zoom_level += 0.1
            self._update_zoom_indicator()
            self._display_current_page()
    
    def _zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_level > 0.5:  # Minimum zoom of 50%
            self.zoom_level -= 0.1
            self._update_zoom_indicator()
            self._display_current_page()
    
    def _update_zoom_indicator(self):
        """Update the zoom level indicator"""
        self.zoom_indicator.configure(text=f"{int(self.zoom_level * 100)}%")
    
    def _close_viewer(self):
        """Close the PDF viewer"""
        if hasattr(self, 'doc'):
            self.doc.close()
        
        # Call the close callback if defined
        if self.close_callback:
            self.close_callback()
    
    def set_close_callback(self, callback):
        """Set a callback function to be called when the viewer is closed"""
        self.close_callback = callback
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling across platforms"""
        # Windows and macOS use event.delta
        if hasattr(event, 'delta'):
            delta = event.delta
            if sys.platform == 'darwin':  # macOS
                self.canvas.yview_scroll(int(-1 * delta), "units")
            else:  # Windows
                self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        # Linux uses event.num
        elif hasattr(event, 'num'):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")