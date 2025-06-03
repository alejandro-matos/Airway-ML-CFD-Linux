# gui/utils/blender_processor.py
"""
Blender Processing Module for OrthoCFD Application

This module handles all Blender-related operations including:
- Running Blender scripts to process STL files
- Creating inlet and outlet geometries
- Generating assembly preview images
- Managing Blender process lifecycle and cancellation

Author: Alejandro Matos Camarillo
Based on OrthoCFD Application
"""

import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from tkinter import messagebox


class BlenderProcessor:
    """
    A class to handle Blender processing operations for airway geometry preparation.
    """
    
    def __init__(self, logger=None, progress_callback=None, cancel_check_callback=None):
        """
        Initialize the Blender processor.
        
        Args:
            logger: Optional logger instance for debugging
            progress_callback: Function to call for progress updates (message, percentage, output_line)
            cancel_check_callback: Function to check if cancellation was requested
        """
        self.logger = logger
        self.progress_callback = progress_callback
        self.cancel_check_callback = cancel_check_callback
        self.current_process = None
        self.cancel_requested = False
    
    def _log_info(self, message):
        """Helper method to log info messages"""
        if self.logger:
            self.logger.log_info(message)
        else:
            print(f"INFO: {message}")
    
    def _log_error(self, message):
        """Helper method to log error messages"""
        if self.logger:
            self.logger.log_error(message)
        else:
            print(f"ERROR: {message}")
    
    def _update_progress(self, message, percentage=None, output_line=None):
        """Helper method to update progress"""
        if self.progress_callback:
            self.progress_callback(message, percentage, output_line)
        else:
            print(f"Progress: {message} ({percentage}%)")
    
    def _is_cancelled(self):
        """Check if cancellation was requested"""
        if self.cancel_check_callback:
            return self.cancel_check_callback()
        return self.cancel_requested
    
    def request_cancel(self):
        """Request cancellation of current processing"""
        self.cancel_requested = True
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self._log_info("Blender process terminated due to cancellation")
            except Exception as e:
                self._log_error(f"Error terminating Blender process: {e}")
    
    def _setup_blender_environment(self, stl_path, cfd_output_dir):
        """
        Set up the environment for Blender processing.
        
        Args:
            stl_path: Path to the input STL file
            cfd_output_dir: Output directory for CFD files
            
        Returns:
            tuple: (trisurf_dir, project_root, blender_script_path)
        """
        # Create required directories
        trisurf_dir = os.path.join(cfd_output_dir, "constant", "triSurface")
        os.makedirs(trisurf_dir, exist_ok=True)
        
        # Write the input files for Blender
        with open("sdir.txt", "w") as f:
            f.write(cfd_output_dir)
        
        with open("geo_in.txt", "w") as f:
            f.write(stl_path)

        # Get the root dir of the project
        project_root = Path(__file__).resolve().parents[2]
        source_dir = project_root / "data" / "Master_cfd_file"
        
        # Copy CFD template files
        shutil.copytree(source_dir, cfd_output_dir, symlinks=False, ignore=None, 
                            ignore_dangling_symlinks=False, dirs_exist_ok=True)
        
        blender_script_path = project_root / "blender_ortho.py"
        
        return trisurf_dir, project_root, blender_script_path
    
    def _run_blender_process(self, blender_script_path):
        """
        Run the Blender process and monitor its output.
        
        Args:
            blender_script_path: Path to the Blender script to execute
            
        Returns:
            tuple: (returncode, stdout, stderr)
        """
        try:
            # Store the process reference for cancellation
            self.current_process = subprocess.Popen(
                ["blender", "--background", "--python", str(blender_script_path)],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Process output in real-time
            while self.current_process.poll() is None:
                # Check if cancellation was requested
                if self._is_cancelled():
                    self.current_process.terminate()
                    self._update_progress("Blender processing cancelled")
                    return -1, "", "Process cancelled by user"
                    
                line = self.current_process.stdout.readline()
                if line:
                    line_stripped = line.strip()
                    self._log_info(f"Blender: {line_stripped}")
                    self._update_progress("Processing geometry in Blender...", None, line_stripped)
            
            stdout, stderr = self.current_process.communicate()
            returncode = self.current_process.returncode
            
            return returncode, stdout, stderr
            
        except Exception as e:
            self._log_error(f"Error running Blender process: {e}")
            return -1, "", str(e)
    
    def _check_output_files(self, cfd_output_dir, max_attempts=10, check_interval=0.5):
        """
        Check if Blender has generated the required output files.
        
        Args:
            cfd_output_dir: CFD output directory
            max_attempts: Maximum number of attempts to check
            check_interval: Time between checks in seconds
            
        Returns:
            tuple: (files_exist, inlet_path, outlet_path, wall_path)
        """
        inlet_path = os.path.join(cfd_output_dir, "constant", "triSurface", "inlet.stl")
        outlet_path = os.path.join(cfd_output_dir, "constant", "triSurface", "outlet.stl")
        wall_path = os.path.join(cfd_output_dir, "constant", "triSurface", "wall.stl")
        
        self._log_info(f"Checking for STL files: {inlet_path}, {outlet_path}, {wall_path}")
        
        for attempt in range(max_attempts):
            if self._is_cancelled():
                return False, None, None, None
                
            files_exist = (os.path.exists(inlet_path) and 
                          os.path.exists(outlet_path) and 
                          os.path.exists(wall_path))
            
            if files_exist:
                self._log_info("All STL files found")
                return True, inlet_path, outlet_path, wall_path
            
            if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                self._log_info(f"STL files not ready yet, checking again in {check_interval}s (attempt {attempt + 1}/{max_attempts})")
                time.sleep(check_interval)
        
        self._log_error("STL files were not created within the expected time")
        return False, None, None, None
    
    def process_geometry(self, stl_path, cfd_output_dir, render_callback=None):
        """
        Main method to process geometry using Blender.
        
        Args:
            stl_path: Path to the input STL file
            cfd_output_dir: Output directory for CFD files
            render_callback: Optional callback to handle assembly image rendering
            
        Returns:
            dict: Processing results with keys:
                - success: bool
                - error_message: str (if success is False)
                - inlet_path: str (if success is True)
                - outlet_path: str (if success is True)
                - wall_path: str (if success is True)
                - assembly_image_path: str (if render_callback provided and successful)
        """
        try:
            self.cancel_requested = False
            
            # Check if cancellation was requested before starting
            if self._is_cancelled():
                return {"success": False, "error_message": "Processing cancelled before starting"}
            
            self._update_progress("Setting up Blender environment...", 50)
            
            # Set up environment
            trisurf_dir, project_root, blender_script_path = self._setup_blender_environment(
                stl_path, cfd_output_dir
            )
            
            self._log_info(f"Starting Blender with STL path: {stl_path}")
            self._log_info(f"Output directory: {trisurf_dir}")
            
            if self._is_cancelled():
                return {"success": False, "error_message": "Processing cancelled during setup"}
            
            self._update_progress("Running Blender script...", 60)
            
            # Run Blender process
            returncode, stdout, stderr = self._run_blender_process(blender_script_path)
            
            if self._is_cancelled():
                return {"success": False, "error_message": "Processing cancelled during Blender execution"}
            
            # Check for Blender errors
            if returncode != 0:
                error_msg = stderr if stderr else "Unknown Blender error occurred"
                self._log_error(f"Blender process failed with return code {returncode}: {error_msg}")
                return {"success": False, "error_message": error_msg}
            
            self._update_progress("Checking output files...", 70)
            
            # Check if output files were created
            files_exist, inlet_path, outlet_path, wall_path = self._check_output_files(cfd_output_dir)
            
            if not files_exist:
                return {"success": False, "error_message": "Required STL files were not generated"}
            
            result = {
                "success": True,
                "inlet_path": inlet_path,
                "outlet_path": outlet_path,
                "wall_path": wall_path
            }
            
            # Generate assembly image if render callback is provided
            if render_callback and not self._is_cancelled():
                self._update_progress("Generating assembly preview...", 80)
                try:
                    assembly_image_path = render_callback(inlet_path, outlet_path, wall_path, cfd_output_dir)
                    if assembly_image_path and os.path.exists(assembly_image_path):
                        result["assembly_image_path"] = assembly_image_path
                        self._log_info(f"Assembly image created: {assembly_image_path}")
                    else:
                        self._log_error("Failed to generate assembly image")
                except Exception as e:
                    self._log_error(f"Error generating assembly image: {e}")
            
            self._update_progress("Blender processing complete", 85)
            return result
            
        except Exception as e:
            self._log_error(f"Blender processing error: {e}")
            return {"success": False, "error_message": str(e)}
    
    def process_geometry_async(self, stl_path, cfd_output_dir, completion_callback, render_callback=None):
        """
        Process geometry asynchronously in a separate thread.
        
        Args:
            stl_path: Path to the input STL file
            cfd_output_dir: Output directory for CFD files
            completion_callback: Function to call when processing completes (result)
            render_callback: Optional callback to handle assembly image rendering
        """
        def worker():
            result = self.process_geometry(stl_path, cfd_output_dir, render_callback)
            completion_callback(result)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread


# Convenience functions for backward compatibility
def create_blender_processor(logger=None, progress_callback=None, cancel_check_callback=None):
    """
    Create and return a BlenderProcessor instance.
    
    Args:
        logger: Optional logger instance
        progress_callback: Function for progress updates
        cancel_check_callback: Function to check cancellation status
        
    Returns:
        BlenderProcessor instance
    """
    return BlenderProcessor(logger, progress_callback, cancel_check_callback)


def process_geometry_with_blender(stl_path, cfd_output_dir, logger=None, progress_callback=None):
    """
    Convenience function to process geometry with Blender.
    
    Args:
        stl_path: Path to input STL file
        cfd_output_dir: CFD output directory
        logger: Optional logger instance
        progress_callback: Optional progress callback
        
    Returns:
        Processing result dictionary
    """
    processor = BlenderProcessor(logger, progress_callback)
    return processor.process_geometry(stl_path, cfd_output_dir)
