import vtk
import sys
from pathlib import Path

def add_text_label(text, position, color, renderer):
    """Helper function to add a text label at a specific viewport position."""
    text_actor = vtk.vtkTextActor()
    text_actor.SetTextScaleModeToNone()
    text_actor.SetPosition(position[0], position[1])
    text_actor.GetTextProperty().SetFontSize(40)
    text_actor.GetTextProperty().SetColor(color)
    text_actor.GetTextProperty().SetBold(True)
    renderer.AddActor2D(text_actor)
    text_actor.SetInput(text)

def render_assembly(inlet_path, outlet_path, wall_path, offscreen=False):
    """
    Load three STL files, assign colors, render them together, and save an image.
    
    Colors:
        - inlet.stl: Green
        - outlet.stl: Red
        - wall.stl: Gray
    """
    # Create a renderer with a white background.
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1, 1, 1)
    
    # --- Inlet ---
    inlet_reader = vtk.vtkSTLReader()
    inlet_reader.SetFileName(inlet_path)
    inlet_reader.Update()

    inlet_mapper = vtk.vtkPolyDataMapper()
    inlet_mapper.SetInputConnection(inlet_reader.GetOutputPort())

    inlet_actor = vtk.vtkActor()
    inlet_actor.SetMapper(inlet_mapper)
    inlet_actor.GetProperty().SetColor(0, 1, 0)  # Green

    renderer.AddActor(inlet_actor)
    
    # --- Outlet ---
    outlet_reader = vtk.vtkSTLReader()
    outlet_reader.SetFileName(outlet_path)
    outlet_reader.Update()

    outlet_mapper = vtk.vtkPolyDataMapper()
    outlet_mapper.SetInputConnection(outlet_reader.GetOutputPort())

    outlet_actor = vtk.vtkActor()
    outlet_actor.SetMapper(outlet_mapper)
    outlet_actor.GetProperty().SetColor(1, 0, 0)  # Red

    renderer.AddActor(outlet_actor)
    
    # --- Wall ---
    wall_reader = vtk.vtkSTLReader()
    wall_reader.SetFileName(wall_path)
    wall_reader.Update()

    wall_mapper = vtk.vtkPolyDataMapper()
    wall_mapper.SetInputConnection(wall_reader.GetOutputPort())

    wall_actor = vtk.vtkActor()
    wall_actor.SetMapper(wall_mapper)
    wall_actor.GetProperty().SetColor(0.9, 0.9, 0.9)  # Gray

    renderer.AddActor(wall_actor)
    
    # --- Compute combined bounds for all models ---
    def get_bounds(reader):
        return reader.GetOutput().GetBounds()

    inlet_bounds = get_bounds(inlet_reader)
    outlet_bounds = get_bounds(outlet_reader)
    wall_bounds = get_bounds(wall_reader)
    
    # Calculate overall bounds
    xmin = min(inlet_bounds[0], outlet_bounds[0], wall_bounds[0])
    xmax = max(inlet_bounds[1], outlet_bounds[1], wall_bounds[1])
    ymin = min(inlet_bounds[2], outlet_bounds[2], wall_bounds[2])
    ymax = max(inlet_bounds[3], outlet_bounds[3], wall_bounds[3])
    zmin = min(inlet_bounds[4], outlet_bounds[4], wall_bounds[4])
    zmax = max(inlet_bounds[5], outlet_bounds[5], wall_bounds[5])
    
    center = [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]
    max_dim = max(xmax - xmin, ymax - ymin, zmax - zmin)
    
    # --- Set up the camera ---
    camera = vtk.vtkCamera()
    camera.SetFocalPoint(center)
    camera.SetPosition(center[0] - max_dim, center[1] - max_dim*1.1, center[2] - max_dim*0.7)
    camera.SetViewUp(0, 0, 1)
    renderer.SetActiveCamera(camera)
    
    # Optional: adjust camera zoom by dollying (factor < 1 zooms out)
    camera.Dolly(0.7)
    renderer.ResetCameraClippingRange()
    
    # --- Create a legend ---
    add_text_label("Inlet", [1200, 250], (0, 1, 0), renderer)  # Green text
    add_text_label("Outlet", [1200, 150], (1, 0, 0), renderer)  # Red text
    
    # --- Create the render window ---
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 600)
    
    if offscreen:
        render_window.SetOffScreenRendering(1)
    else:
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)
    
    render_window.Render()
    
    # --- Capture the rendered image ---
    window_to_image = vtk.vtkWindowToImageFilter()
    window_to_image.SetInput(render_window)
    window_to_image.SetScale(2)  # Increase resolution (optional)
    window_to_image.SetInputBufferTypeToRGBA()
    window_to_image.Update()
    
    # Save the output image as assembly.png in the same directory as the inlet file.
    output_path = str(Path(inlet_path).parent / "assembly.png")
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(output_path)
    writer.SetInputConnection(window_to_image.GetOutputPort())
    writer.Write()
    
    print(f"Assembly saved to: {output_path}")
    
    if not offscreen:
        interactor.Start()

if __name__ == "__main__":
   
    inlet_path = "./inlet.stl"
    outlet_path = "./outlet.stl"
    wall_path = "./wall.stl"
    
    render_assembly(inlet_path, outlet_path, wall_path)
