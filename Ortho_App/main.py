# main.py

import sys
import os
from datetime import datetime
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from gui.app import OrthoCFDApp
from gui.utils.app_logger import AppLogger


def setup_environment():
    """
    Set up the application environment and verify requirements.
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """

    try:
        # Create necessary directories
        required_dirs = ['logs', 'temp', 'output']
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            
        # Verify required external applications
        # Note: Implement actual checks based on your system
        required_apps = {
            # Linux
            # 'Blender': '/usr/bin/blender',
            # 'OpenFOAM': '/usr/lib/openfoam/openfoam2306',
            # 'ParaView': '/usr/bin/paraview'
            # Windows testing tk
            'Blender': r'C:\Users\aleja\Desktop\Geometries\summary.txt',
            'OpenFOAM': r'C:\Users\aleja\Desktop\Geometries\summary.txt',
            'ParaView': r'C:\Users\aleja\Desktop\Geometries\summary.txt'
        }
        
        missing_apps = []
        for app_name, app_path in required_apps.items():
            if not os.path.exists(app_path):
                missing_apps.append(app_name)
                
        if missing_apps:
            return False, f"Missing required applications: {', '.join(missing_apps)}"
            
        return True, None
        
    except Exception as e:
        return False, f"Environment setup failed: {str(e)}"

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler to log unhandled exceptions.
    """
    # Don't handle KeyboardInterrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logger.log_error("Unhandled exception", exc_value)
    
    # Show error message to user
    tk.messagebox.showerror(
        "Error",
        "An unexpected error occurred. Please check the log file for details."
    )

def main():
    """
    Main application entry point.
    """
    try:
        # Set up environment
        success, error_message = setup_environment()
        if not error_message:
            logger.log_info("Environment setup successful")
        else:
            logger.log_error(f"Environment setup failed: {error_message}")
            tk.messagebox.showerror("Setup Error", error_message)
            return

        # Create and start the application
        logger.log_info("Starting OrthoCFD Application")
        app = OrthoCFDApp()
        
        # Configure application
        app.protocol("WM_DELETE_WINDOW", lambda: on_closing(app))
        
        # Start the main loop
        app.mainloop()
        
    except Exception as e:
        logger.log_error("Failed to start application", e)
        tk.messagebox.showerror(
            "Startup Error",
            f"Failed to start application: {str(e)}\n\nPlease check the log file for details."
        )

def on_closing(app):
    """
    Handle application closing.
    """
    try:
        # Clean up temporary files
        temp_dir = 'temp'
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.log_warning(f"Error deleting temporary file {file_path}: {str(e)}")

        logger.log_info("Application closed by user")
        app.destroy()
        
    except Exception as e:
        logger.log_error("Error during application shutdown", e)
        app.destroy()

if __name__ == "__main__":
    # Initialize logger
    logger = AppLogger()
    
    # Set up global exception handler
    sys.excepthook = handle_exception
    
    # Log application start
    logger.log_info("=" * 50)
    logger.log_info(f"OrthoCFD Application Starting - {datetime.now()}")
    logger.log_info("=" * 50)
    
    # Run the application
    main()