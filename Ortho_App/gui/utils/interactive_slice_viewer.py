import customtkinter as ctk
import sys
import os
import traceback

def open_interactive_slice_viewer(vtk_file_path, parent):
    """
    Opens a Toplevel window with an interactive slice viewer.
    
    Args:
        vtk_file_path (str): Path to the VTK file to load.
        parent: The parent widget (typically your main application window).
    """
    # Create a separate function to handle ParaView imports
    # This way the main imports don't fail if ParaView is missing
    def load_paraview():
        # Set ParaView paths - adjust these to match your installation
        paraview_python_path = "/opt/paraview/lib/python3.10/site-packages"
        paraview_lib_path = "/opt/paraview/lib"

        # Add to Python path for module imports
        if paraview_python_path not in sys.path:
            sys.path.insert(0, paraview_python_path)

        # Check if we need to set LD_LIBRARY_PATH
        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        
        if paraview_lib_path not in ld_path:
            # Instead of restarting the script, just update the environment
            # This approach keeps the current Python process running
            os.environ["LD_LIBRARY_PATH"] = f"{paraview_lib_path}:{ld_path}"
            
            # Set library path for the dynamic loader to find ParaView's libraries
            try:
                # This lets the dynamic loader find libraries without restart
                import ctypes
                ctypes.CDLL("libpython3.10.so", mode=ctypes.RTLD_GLOBAL)
            except Exception as e:
                print(f"Warning: Could not set library loading mode: {e}")
        
        # Now try to import ParaView modules
        try:
            from paraview.simple import (
                OpenDataFile, Slice, UpdatePipeline, Render,
                GetActiveViewOrCreate, ResetCamera, GetActiveCamera,
                ColorBy, GetColorTransferFunction, Show
            )
            
            return {
                'OpenDataFile': OpenDataFile,
                'Slice': Slice,
                'UpdatePipeline': UpdatePipeline,
                'Render': Render,
                'GetActiveViewOrCreate': GetActiveViewOrCreate,
                'ResetCamera': ResetCamera,
                'GetActiveCamera': GetActiveCamera,
                'ColorBy': ColorBy, 
                'GetColorTransferFunction': GetColorTransferFunction,
                'Show': Show
            }
        except ImportError as e:
            error_msg = f"Failed to import ParaView: {str(e)}"
            print(error_msg)
            
            # Create a simple error dialog
            error_window = ctk.CTkToplevel(parent)
            error_window.title("ParaView Import Error")
            error_window.geometry("600x400")
            
            # Display the error details
            ctk.CTkLabel(
                error_window, 
                text="Error loading ParaView modules",
                font=("Arial", 16, "bold")
            ).pack(pady=(20, 10))
            
            # Show the exact error
            ctk.CTkLabel(
                error_window,
                text=f"Error: {str(e)}",
                wraplength=550
            ).pack(pady=10)
            
            # Show the traceback
            tb_frame = ctk.CTkFrame(error_window)
            tb_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            tb_text = ctk.CTkTextbox(tb_frame, height=200)
            tb_text.pack(fill="both", expand=True, padx=5, pady=5)
            tb_text.insert("1.0", traceback.format_exc())
            
            # Add some help text
            help_text = (
                "To fix this error:\n\n"
                "1. Ensure ParaView is installed correctly\n"
                "2. Check that the path to ParaView is set correctly in the script\n"
                "3. Try running the script with 'LD_PRELOAD=/opt/paraview/lib/libpython3.10.so'\n"
                "   before your Python command"
            )
            
            ctk.CTkLabel(
                error_window,
                text=help_text,
                justify="left",
                wraplength=550
            ).pack(pady=10)
            
            return None

    # Check if the VTK file exists
    if not vtk_file_path or not os.path.exists(vtk_file_path):
        error_dialog = ctk.CTkToplevel(parent)
        error_dialog.title("Error")
        error_dialog.geometry("400x200")
        ctk.CTkLabel(
            error_dialog,
            text=f"VTK file not found:\n{vtk_file_path}",
            wraplength=350
        ).pack(pady=20)
        
        ctk.CTkButton(
            error_dialog,
            text="OK",
            command=error_dialog.destroy,
            width=100
        ).pack(pady=20)
        
        return
    
    # Try to load ParaView modules
    pv = load_paraview()
    
    if not pv:
        return  # Error already displayed by load_paraview()
    
    try:
        # Load the data from the specified VTK file
        data = pv['OpenDataFile'](vtk_file_path)

        # Create a slice filter on the data
        sliceFilter = pv['Slice'](Input=data)
        sliceFilter.SliceType = "Plane"

        # Compute the center of the data bounds
        bounds = data.GetDataInformation().GetBounds()
        center = [
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0
        ]
        # Set the initial slice origin
        sliceFilter.SliceType.Origin = center
        # Set the slice normal (here, slicing perpendicular to the X-axis)
        sliceFilter.SliceType.Normal = [1.0, 0.0, 0.0]
        pv['UpdatePipeline']()

        # Create (or get) the render view and set the background to white
        renderView = pv['GetActiveViewOrCreate']("RenderView")
        renderView.Background = [1.0, 1.0, 1.0]

        # Display the slice in the render view
        sliceDisplay = pv['Show'](sliceFilter, renderView)

        # Adjust the camera to face the slice head-on
        pv['ResetCamera']()
        camera = pv['GetActiveCamera']()
        camera.SetFocalPoint(center[0], center[1], center[2])
        camera.SetPosition(center[0] - 200, center[1], center[2])  # Offset along -X
        camera.SetViewUp(0.0, 0.0, 1.0)
        renderView.CameraParallelProjection = True
        pv['Render']()

        # Define a callback function for the slider
        def update_slice(offset_str):
            try:
                offset = float(offset_str)
            except ValueError:
                offset = 0.0
            # Adjust only the x-coordinate since our slice normal is [1,0,0]
            new_origin = [center[0] + offset, center[1], center[2]]
            sliceFilter.SliceType.Origin = new_origin
            pv['UpdatePipeline']()
            pv['Render']()

        # Create a new Toplevel window for the interactive viewer
        viewer_window = ctk.CTkToplevel(parent)
        viewer_window.title("Interactive Slice Viewer")
        viewer_window.geometry("600x300")

        # Add an instruction label with more details
        instruction_label = ctk.CTkLabel(
            viewer_window, 
            text="Use the slider to move the slice plane along the X-axis\n" +
                 f"File: {os.path.basename(vtk_file_path)}",
            wraplength=550
        )
        instruction_label.pack(pady=10, padx=10)

        # Add a frame for the field selector
        field_frame = ctk.CTkFrame(viewer_window, fg_color="transparent")
        field_frame.pack(pady=(5, 10), padx=10, fill="x")

        # Label for the field selector
        field_label = ctk.CTkLabel(field_frame, text="Color by field:")
        field_label.pack(side="left", padx=(0, 10))

        # Get available array names (point data)
        array_info = data.GetPointDataInformation()
        array_names = [array_info.GetArrayInformation(i).GetName() for i in range(array_info.GetNumberOfArrays())]

        # Dropdown for field selection
        field_var = ctk.StringVar(value="p" if "p" in array_names else array_names[0] if array_names else "")
        field_dropdown = ctk.CTkOptionMenu(
            field_frame,
            variable=field_var,
            values=array_names,
            width=150
        )
        field_dropdown.pack(side="left")

        # Function to update the colored field
        def update_field(field_name):
            pv['ColorBy'](sliceDisplay, ('POINT_DATA', field_name))
            lut = pv['GetColorTransferFunction'](field_name)
            lut.RescaleTransferFunctionToDataRange()
            pv['Render']()

        # Connect the dropdown to the update function
        field_dropdown.configure(command=update_field)
        
        # Initial field coloring
        if array_names:
            update_field(field_var.get())

        # Create a slider
        # Calculate reasonable range based on model size
        model_width = bounds[1] - bounds[0]
        slider_range = model_width / 2
        
        slice_slider = ctk.CTkSlider(
            viewer_window, 
            from_=-slider_range, 
            to=slider_range, 
            number_of_steps=100
        )
        slice_slider.pack(pady=10, padx=10, fill="x")

        # Create a label to display the current offset
        current_offset_label = ctk.CTkLabel(viewer_window, text="Offset: 0 mm")
        current_offset_label.pack(pady=5, padx=10)

        # Define a slider callback that updates the label and the slice
        def slider_callback(val):
            current_offset_label.configure(text=f"Offset: {val:.2f} mm")
            update_slice(val)

        # Link the slider to the callback
        slice_slider.configure(command=slider_callback)
        
        # Add buttons for axis selection
        axis_frame = ctk.CTkFrame(viewer_window, fg_color="transparent")
        axis_frame.pack(pady=10, padx=10, fill="x")
        
        axis_label = ctk.CTkLabel(axis_frame, text="Slice orientation:")
        axis_label.pack(side="left", padx=(0, 10))
        
        # Function to change slice axis
        def change_axis(axis):
            if axis == "X":
                sliceFilter.SliceType.Normal = [1.0, 0.0, 0.0]
                camera.SetPosition(center[0] - 200, center[1], center[2])
            elif axis == "Y":
                sliceFilter.SliceType.Normal = [0.0, 1.0, 0.0]
                camera.SetPosition(center[0], center[1] - 200, center[2])
            elif axis == "Z":
                sliceFilter.SliceType.Normal = [0.0, 0.0, 1.0]
                camera.SetPosition(center[0], center[1], center[2] - 200)
                
            camera.SetFocalPoint(center[0], center[1], center[2])
            camera.SetViewUp(0.0, 0.0, 1.0)
            pv['UpdatePipeline']()
            pv['ResetCamera']()
            pv['Render']()
            
            # Reset the slider position
            slice_slider.set(0)
            current_offset_label.configure(text="Offset: 0 mm")
            
        # Add axis buttons
        for axis in ["X", "Y", "Z"]:
            axis_button = ctk.CTkButton(
                axis_frame,
                text=f"{axis}-Axis",
                command=lambda a=axis: change_axis(a),
                width=80,
                height=30
            )
            axis_button.pack(side="left", padx=5)

        # Start with the X axis (already default in the code above)
        
        # Start the Tkinter event loop for this window
        viewer_window.mainloop()
        
    except Exception as e:
        # Show error dialog with details
        error_dialog = ctk.CTkToplevel(parent)
        error_dialog.title("Error")
        error_dialog.geometry("600x400")
        
        ctk.CTkLabel(
            error_dialog,
            text="Error in Interactive Slice Viewer",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            error_dialog,
            text=f"Error: {str(e)}",
            wraplength=550
        ).pack(pady=10)
        
        # Show traceback
        tb_frame = ctk.CTkFrame(error_dialog)
        tb_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tb_text = ctk.CTkTextbox(tb_frame, height=200)
        tb_text.pack(fill="both", expand=True, padx=5, pady=5)
        tb_text.insert("1.0", traceback.format_exc())
        
        ctk.CTkButton(
            error_dialog,
            text="Close",
            command=error_dialog.destroy,
            width=100
        ).pack(pady=20)