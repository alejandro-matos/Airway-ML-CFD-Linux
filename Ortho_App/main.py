# Ortho CFD App entry point script
# Computational Fluid Dynamics Lab
# Author = Alejandro Matos Camarillo
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2025-04-30
# cmd = python main.py
# main.py

# OrthoCFD application entry point:
# - Sets up the environment (creates required directories, verifies external tools)
# - Configures global exception handling
# - Instantiates and launches the OrthoCFDApp GUI
# - Defines cleanup logic on application close

# Key Components:

# setup_environment():  
#     Creates 'logs' folder and checks for Blender, OpenFOAM, ParaView;  

# handle_exception():  
#     logs the error and shows a simple popup directing the user to check the log file.

# main():  
#     Calls setup_environment(), logs success or shows an error popup;  
#     instantiates OrthoCFDApp(), binds the window close event to on_closing(), and starts app.mainloop().

# on_closing(app):  
#     Deletes all files in the 'temp' directory, logs a closing banner with timestamp, and calls app.destroy().

# if __name__ == "__main__":  
#     Initializes AppLogger, sets sys.excepthook to handle_exception, logs a startup banner with timestamp,  
#     then calls main() to launch the application.


import sys
import os
from datetime import datetime
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from gui.app import OrthoCFDApp
from gui.utils.basic_utils import AppLogger
from gui.config.settings import APP_SETTINGS, UI_SETTINGS , PATH_SETTINGS, EXTERNAL_APPS

def setup_environment():
    """
    Set up the application environment and verify requirements.
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """

    try:
        # Create necessary directories
        required_dirs = [
            PATH_SETTINGS["LOGS_DIR"],
        ]
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            
        # Verify required external applications (Blender, openfoam, paraview)
        required_apps = {
            name: props["PATH"]
            for name, props in EXTERNAL_APPS.items()
            if props.get("REQUIRED", False)
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
        logger.log_info(f"Starting {APP_SETTINGS['TITLE']} Application")
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
    Handle application closing. Always allow close and clean up.
    """
    try:
        # TEMP directory not implemented, using /tmp instead
        # # Clean up temporary files
        # temp_dir = PATH_SETTINGS["TEMP_DIR"]
        # if os.path.exists(temp_dir):
        #     for fname in os.listdir(temp_dir):
        #         path = os.path.join(temp_dir, fname)
        #         if os.path.isfile(path):
        #             try:
        #                 os.unlink(path)
        #             except Exception as e:
        #                 logger.log_warning(f"Error deleting temp file {path}: {e}")

        # Log application close
        logger.log_info("=" * 50)
        logger.log_info(f"{APP_SETTINGS['TITLE']} Application closing - {datetime.now()}")
        logger.log_info("=" * 50)
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
    logger.log_info(f"{APP_SETTINGS['TITLE']} Application Starting - {datetime.now()}")
    logger.log_info("=" * 50)
    
    # Run the application
    main()
