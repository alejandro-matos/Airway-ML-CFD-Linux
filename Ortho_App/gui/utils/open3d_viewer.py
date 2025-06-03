# gui/utils/open3d_viewer.py
"""
Open3D 3D Viewer Module for OrthoCFD Application

This module provides fullscreen 3D viewers for STL files and airway components
with integrated text instructions and proper window management.

Author: Alejandro Matos Camarillo
Based on OrthoCFD Application
"""

import os
import time
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox

import open3d as o3d


class Open3DViewer:
    """
    A class to handle 3D visualization of STL files and airway components
    using Open3D with fullscreen capabilities and text overlays.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the Open3D viewer.
        
        Args:
            logger: Optional logger instance for debugging
        """
        self.logger = logger
    
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
    
    def _create_instruction_text(self, mesh_bounds):
        """
        Create a single 3D text mesh instruction
        
        Args:
            mesh_bounds: Open3D AxisAlignedBoundingBox object
            
        Returns:
            Open3D TriangleMesh object or None if creation fails
        """
        try:
            from open3d.t.geometry import TriangleMesh
            
            # Calculate position based on mesh bounds
            max_bound = mesh_bounds.max_bound
            min_bound = mesh_bounds.min_bound
            
            # Position text in the upper area of the view
            text_x = min_bound[0] + (max_bound[0] - min_bound[0]) * 0.1
            text_y = max_bound[1] + (max_bound[1] - min_bound[1]) * 0.15
            text_z = max_bound[2]
            
            # Create "Press ESC to Exit" text
            esc_text_mesh = o3d.t.geometry.TriangleMesh.create_text("Press ESC to Exit", depth=0.05).to_legacy()
            esc_text_mesh.paint_uniform_color([1, 0, 0])  # Red color for visibility
            
            # Scale and position the text
            scale = min(max_bound[0] - min_bound[0], max_bound[1] - min_bound[1]) * 0.01
            transform_matrix = [
                [scale, 0, 0, text_x],
                [0, scale, 0, text_y],
                [0, 0, scale, text_z],
                [0, 0, 0, 1]
            ]
            esc_text_mesh.transform(transform_matrix)
            
            return esc_text_mesh
            
        except Exception as e:
            self._log_error(f"Could not create text mesh: {e}")
            return None
    
    def _make_window_fullscreen(self, window_name, max_attempts=3):
        """
        Attempt to make the specified window fullscreen using wmctrl
        
        Args:
            window_name: Name of the window to make fullscreen
            max_attempts: Maximum number of attempts to try
        """
        for attempt in range(max_attempts):
            try:
                # Try fullscreen first
                result = subprocess.run([
                    "wmctrl", "-r", window_name, "-b", "add,fullscreen"
                ], check=False, capture_output=True)
                
                if result.returncode == 0:
                    self._log_info(f"Successfully made window fullscreen: {window_name}")
                    return True
                    
            except Exception as e:
                self._log_error(f"Fullscreen attempt {attempt + 1} failed: {e}")
            
            # If fullscreen fails, try maximized as fallback
            try:
                result = subprocess.run([
                    "wmctrl", "-r", window_name, "-b", "add,maximized_vert,maximized_horz"
                ], check=False, capture_output=True)
                
                if result.returncode == 0:
                    self._log_info(f"Successfully maximized window: {window_name}")
                    return True
                    
            except Exception as e:
                self._log_error(f"Maximize attempt {attempt + 1} failed: {e}")
            
            # Brief pause between attempts
            time.sleep(0.5)
        
        self._log_error(f"Failed to make window fullscreen after {max_attempts} attempts")
        return False
    
    def view_stl_file(self, stl_path):
        """
        Launch a fullscreen interactive STL viewer with text instruction
        
        Args:
            stl_path: Path to the STL file to view
        """
        if not os.path.exists(stl_path):
            messagebox.showerror("Error", f"STL file not found: {stl_path}")
            return
        
        try:
            def view_mesh():
                # Load mesh
                mesh = o3d.io.read_triangle_mesh(stl_path)
                
                if len(mesh.vertices) == 0:
                    self._log_error(f"Empty mesh loaded from: {stl_path}")
                    return
                
                mesh.compute_vertex_normals()

                # Create large window
                vis = o3d.visualization.Visualizer()
                window_name = "3D Airway Viewer - PRESS ESC TO EXIT"
                vis.create_window(
                    window_name=window_name,
                    width=1600, 
                    height=1000,
                    left=50,
                    top=50
                )
                
                vis.add_geometry(mesh)
                
                # Add single 3D text instruction
                bbox = mesh.get_axis_aligned_bounding_box()
                instruction_text = self._create_instruction_text(bbox)
                if instruction_text:
                    vis.add_geometry(instruction_text)

                # Configure rendering options
                render_option = vis.get_render_option()
                render_option.background_color = [1, 1, 1]
                render_option.point_size = 1.0
                render_option.show_coordinate_frame = False
                # Enable back-face rendering so text is visible from both sides
                render_option.mesh_show_back_face = True

                view_control = vis.get_view_control()
                view_control.set_zoom(0.8)

                # Wait for window to appear, then make it fullscreen
                time.sleep(1.5)
                self._make_window_fullscreen(window_name)

                vis.run()
                vis.destroy_window()
            
            # Show pre-launch message
            messagebox.showinfo(
                "3D Viewer", 
                "Opening 3D airway viewer in fullscreen mode.\n\n"
                "Press ESC to Exit viewer window.\n\n"
                "Mouse controls: Click+drag to rotate, scroll to zoom."
            )
            
            # Start the viewer in a separate thread
            threading.Thread(target=view_mesh, daemon=True).start()
            
        except Exception as e:
            self._log_error(f"Failed to display STL viewer: {e}")
            messagebox.showerror("Error", f"Failed to display STL viewer:\n{e}")
    
    def view_airway_components(self, cfd_base_path):
        """
        Launch a fullscreen viewer for airway components with exit instruction
        
        Args:
            cfd_base_path: Base path to the CFD directory containing triSurface folder
        """
        try:
            def view_components():
                tri_surface_path = os.path.join(cfd_base_path, "constant", "triSurface")
                
                # Check if triSurface directory exists
                if not os.path.exists(tri_surface_path):
                    self._log_error(f"triSurface directory not found: {tri_surface_path}")
                    return
                
                # Define component file paths
                inlet_path = os.path.join(tri_surface_path, "inlet.stl")
                outlet_path = os.path.join(tri_surface_path, "outlet.stl")
                wall_path = os.path.join(tri_surface_path, "wall.stl")
                
                # Check if all component files exist
                missing_files = []
                for name, path in [("inlet", inlet_path), ("outlet", outlet_path), ("wall", wall_path)]:
                    if not os.path.exists(path):
                        missing_files.append(name)
                
                if missing_files:
                    self._log_error(f"Missing component files: {missing_files}")
                    messagebox.showerror("Error", f"Missing component files: {', '.join(missing_files)}")
                    return

                # Load inlet (green)
                inlet_mesh = o3d.io.read_triangle_mesh(inlet_path)
                inlet_mesh.compute_vertex_normals()
                inlet_mesh.paint_uniform_color([0, 1, 0])

                # Load outlet (red)
                outlet_mesh = o3d.io.read_triangle_mesh(outlet_path)
                outlet_mesh.compute_vertex_normals()
                outlet_mesh.paint_uniform_color([1, 0, 0])

                # Load wall (gray)
                wall_mesh = o3d.io.read_triangle_mesh(wall_path)
                wall_mesh.compute_vertex_normals()
                wall_mesh.paint_uniform_color([0.7, 0.7, 0.7])

                # Create visualization window
                vis = o3d.visualization.Visualizer()
                window_name = "Airway Components Viewer - PRESS ESC TO EXIT"
                vis.create_window(
                    window_name=window_name,
                    width=1600, 
                    height=1000,
                    left=50,
                    top=50
                )

                vis.add_geometry(inlet_mesh)
                vis.add_geometry(outlet_mesh)
                vis.add_geometry(wall_mesh)
                
                # Add simple exit instruction text
                # Use the combined geometry bounds for positioning
                combined_mesh = inlet_mesh + outlet_mesh + wall_mesh
                bbox = combined_mesh.get_axis_aligned_bounding_box()
                exit_text = self._create_instruction_text(bbox)
                if exit_text:
                    vis.add_geometry(exit_text)

                # Configure rendering options
                render_option = vis.get_render_option()
                render_option.background_color = [1, 1, 1]
                render_option.point_size = 1.0
                render_option.show_coordinate_frame = False
                # Enable back-face rendering so text is visible from both sides
                render_option.mesh_show_back_face = True

                view_control = vis.get_view_control()
                view_control.set_zoom(0.8)

                # Make fullscreen
                time.sleep(1.5)
                self._make_window_fullscreen(window_name)

                vis.run()
                vis.destroy_window()
            
            # Show pre-launch message
            messagebox.showinfo(
                "Component Viewer", 
                "Opening airway components viewer in fullscreen mode.\n\n"
                "Component colors:\n"
                "• Green = Inlet (air entry)\n"
                "• Red = Outlet (air exit)\n"
                "• Gray = Airway walls\n\n"
                "Press ESC to Exit viewer window."
            )
            
            # Start viewer in a separate thread
            threading.Thread(target=view_components, daemon=True).start()
                
        except Exception as e:
            self._log_error(f"Failed to display component viewer: {e}")
            messagebox.showerror("Error", f"Failed to display component viewer:\n{e}")


# Convenience functions for backward compatibility and simpler imports
def create_viewer(logger=None):
    """
    Create and return an Open3DViewer instance
    
    Args:
        logger: Optional logger instance
        
    Returns:
        Open3DViewer instance
    """
    return Open3DViewer(logger)


def view_stl_fullscreen(stl_path, logger=None):
    """
    Convenience function to view an STL file in fullscreen mode
    
    Args:
        stl_path: Path to the STL file
        logger: Optional logger instance
    """
    viewer = Open3DViewer(logger)
    viewer.view_stl_file(stl_path)


def view_airway_components_fullscreen(cfd_base_path, logger=None):
    """
    Convenience function to view airway components in fullscreen mode
    
    Args:
        cfd_base_path: Base path to CFD directory
        logger: Optional logger instance
    """
    viewer = Open3DViewer(logger)
    viewer.view_airway_components(cfd_base_path)