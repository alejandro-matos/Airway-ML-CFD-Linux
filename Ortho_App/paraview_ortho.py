# Msc Ortho CFD paraview 5.12 script File
# Computational Fluid Dynamics Lab
# Author = Uday Tummala
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2025-10-21
# cmd opens gui = paraview --script=home/uday/Desktop/msc_ortho/paraview_ortho.py
# cmd for local = pvbatch paraview_ortho.py
# cmd for server no GUI = pvpython paraview_ortho.py

import paraview
import time
import os

paraview.compatibility.major = 5
paraview.compatibility.minor = 12

from paraview.simple import *
# disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

start_time = time.time()

# Open case.foam file
file = open("sdir.txt", "r")
path1 = os.path.expandvars(os.path.expanduser(file.readline().strip()))
file.close()
path111 = os.path.join(path1, "case.foam")
path22 = os.path.join(path1, "system/face_centers_i.txt")

# --- Step 2: Read coordinates from the file ---
with open(path22, "r") as f:
    lines = [line.strip() for line in f if line.startswith("(")]

point1 = tuple(float(x) for x in lines[0].strip("()").split())
point2 = tuple(float(x) for x in lines[1].strip("()").split())

# --- Step 3: Extract X-values and compute range ---
x1 = point1[0]
x2 = point2[0]

casefoam = OpenFOAMReader(registrationName='case.foam', FileName=path111)
casefoam.MeshRegions = ['internalMesh']
casefoam.CellArrays = ['U', 'p']

# Define parameters
animationScene1 = GetAnimationScene()
animationScene1.UpdateAnimationUsingDataTimeSteps()
renderView1 = GetActiveViewOrCreate('RenderView')
casefoamDisplay = Show(casefoam, renderView1, 'UnstructuredGridRepresentation')
materialLibrary1 = GetMaterialLibrary()
casefoamDisplay.SetScalarBarVisibility(renderView1, True)
casefoam = GetActiveSource()
casefoamDisplay = GetDisplayProperties(casefoam, view=renderView1)
casefoamDisplay.RescaleTransferFunctionToDataRange(True, False)
layout1 = GetLayout()
layout1.SetSize(1577, 733)
ColorBy(casefoamDisplay, ('POINTS', 'p'))
renderView1.InteractionMode = '2D'
pLUT = GetColorTransferFunction('p')
pPWF = GetOpacityTransferFunction('p')
pLUT.ApplyPreset('Rainbow Uniform', True)
pTF2D = GetTransferFunction2D('p')
renderView1.Update()
casefoamDisplay.SetScalarBarVisibility(renderView1, True)
pLUTColorBar = GetScalarBar(pLUT, renderView1)
pLUTColorBar.Orientation = 'Horizontal'
pLUTColorBar.WindowLocation = 'Any Location'
pLUTColorBar.Position = [0.10, 0.019]
pLUTColorBar.ScalarBarLength = 0.6
pLUTColorBar.Title = "Pressure (Pa)"
pLUTColorBar.ComponentTitle = ""
pLUTColorBar.LabelFormat = "%.2f"
pLUTColorBar.TitleFontSize = 16
pLUTColorBar.LabelFontSize = 14

# p & v section view pic-1 export
clip1 = Clip(registrationName='Clip1', Input=casefoam)
clip1.ClipType = 'Plane'
clip1.HyperTreeGridClipper = 'Plane'
clip1.Scalars = ['POINTS', 'p']
clip1.HyperTreeGridClipper.Origin = [x1, 0, 0]
clip1.ClipType.Origin = [x1, 0, 0]
clip1.ClipType.Normal = [1, 0, 0]  # normal along X-axis
renderView1.Update()
clip1Display = Show(clip1, renderView1, 'UnstructuredGridRepresentation')
Hide(casefoam, renderView1)
ColorBy(clip1Display, ('POINTS', 'p'))
clip1Display.RescaleTransferFunctionToDataRange(True, False)
clip1Display.SetScalarBarVisibility(renderView1, True)
HideInteractiveWidgets(proxy=clip1.ClipType)
renderView1.CameraPosition = [1, 0, 0]      # Position of the camera
renderView1.CameraFocalPoint = [0, 0, 0]    # Where the camera looks (the origin)
renderView1.CameraViewUp = [0, 0, 1]        # "Up" direction (Z is up)
ResetCamera()
renderView1.CameraParallelProjection = 1
path8 = os.path.join(path1, "p_cut_1.png")
SaveScreenshot(path8, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
ColorBy(clip1Display, ('POINTS', 'U', 'Magnitude'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
clip1Display.RescaleTransferFunctionToDataRange(True, False)
clip1Display.SetScalarBarVisibility(renderView1, True)
uLUT = GetColorTransferFunction('U')
uPWF = GetOpacityTransferFunction('U')
uTF2D = GetTransferFunction2D('U')
uLUT.ApplyPreset('Rainbow Uniform', True)
renderView1.Update()
uLUTColorBar = GetScalarBar(uLUT, renderView1)
uLUTColorBar.Orientation = 'Horizontal'
uLUTColorBar.WindowLocation = 'Any Location'
uLUTColorBar.Position = [0.145, 0.019]
uLUTColorBar.ScalarBarLength = 0.425
uLUTColorBar.Title = "Velocity (m/s)"
uLUTColorBar.ComponentTitle = ""
uLUTColorBar.LabelFormat = "%.2f"
uLUTColorBar.TitleFontSize = 16
uLUTColorBar.LabelFontSize = 14
path9 = os.path.join(path1, "v_cut_1.png")
SaveScreenshot(path9, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')

# p & v section view pic-2 export
clip1.ClipType.Origin = [x2, 0, 0]
ColorBy(clip1Display, ('POINTS', 'U', 'Magnitude'))
renderView1.Update()
uLUTColorBar.Title = "Velocity (m/s)"
uLUTColorBar.ComponentTitle = ""
renderView1.CameraPosition = [1, 0, 0]      # Position of the camera
renderView1.CameraFocalPoint = [0, 0, 0]    # Where the camera looks (the origin)
renderView1.CameraViewUp = [0, 0, 1]        # "Up" direction (Z is up)
ResetCamera()
renderView1.CameraParallelProjection = 1
path10 = os.path.join(path1, "v_cut_2.png")
SaveScreenshot(path10, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
ColorBy(clip1Display, ('POINTS', 'p'))
HideScalarBarIfNotNeeded(uLUT, renderView1)
clip1Display.RescaleTransferFunctionToDataRange(True, False)
clip1Display.SetScalarBarVisibility(renderView1, True)
renderView1.Update()
Render()
path11 = os.path.join(path1, "p_cut_2.png")
SaveScreenshot(path11, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
clip1Display.RescaleTransferFunctionToDataRange(False, True)
Delete(clip1)

# Quit Paraview
print("Finished taking photos of CFD Model in Paraview_v5.12")
print("Please check output images p & v .png files")
print("Time taken for postprocessing: ",time.time()-start_time)
