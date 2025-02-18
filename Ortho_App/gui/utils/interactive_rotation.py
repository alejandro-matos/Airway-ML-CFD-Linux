# At the top of your file, add VTK-related imports (ensure you have vtk installed)
import vtk
from vtk.tk.vtkTkRenderWindowInteractor import vtkTkRenderWindowInteractor

def _create_interactive_cfd_view(self, parent):
    """
    Create an interactive 3D view for the CFD results.
    This function sets up a VTK render window embedded in the Tkinter frame.
    """
    # Create the render window and interactor
    self.vtk_frame = parent
    self.vtk_widget = vtkTkRenderWindowInteractor(self.vtk_frame, width=400, height=300)
    self.vtk_widget.pack(expand=True, fill='both')
    
    # Set up VTK renderer, render window, and interactor
    self.renderer = vtk.vtkRenderer()
    render_window = self.vtk_widget.GetRenderWindow()
    render_window.AddRenderer(self.renderer)
    
    interactor = render_window.GetInteractor()
    
    # Load your 3D model (for example, a .stl file) using vtkSTLReader
    reader = vtk.vtkSTLReader()
    reader.SetFileName("path/to/cfd_model.stl")  # Update with your file
    reader.Update()
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    
    self.renderer.AddActor(actor)
    self.renderer.ResetCamera()
    
    # Optionally, add an interactor style for rotation
    style = vtk.vtkInteractorStyleTrackballCamera()
    interactor.SetInteractorStyle(style)
    
    # Start the interactor
    interactor.Initialize()
    interactor.Start()
