# Msc Ortho CFD paraview 5.12 script File
# Computational Fluid Dynamics Lab
# Author = Uday Tummala
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2024-01-07
# cmd opens gui = paraview --script=home/uday/Desktop/msc_ortho/paraview_ortho.py
# cmd for local = pvbatch paraview_ortho.py
# cmd for server no GUI = pvpython paraview_ortho.py

import paraview
import time
import os

# version details

paraview.compatibility.major = 5
paraview.compatibility.minor = 12

from paraview.simple import *

# disable automatic camera reset on 'Show'

paraview.simple._DisableFirstRenderCameraReset()
start_time = time.time()

# Open case.foam file

file = open("sdir.txt", "r")
path1 = file.readline()
file.close()
path111 = os.path.join(path1, "case.foam")
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

# pressure & velocity pic-1 export

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
pLUTColorBar.Position = [0.145, 0.019]
pLUTColorBar.ScalarBarLength = 0.34
# current camera placement for renderView1
renderView1.CameraPosition = [0.193, -0.0203, -0.0642]
renderView1.CameraFocalPoint = [0.0654, 0.0892, 0.0417]
renderView1.CameraViewUp = [0.514, -0.205, 0.833]
renderView1.CameraParallelScale = 0.0515
path2 = os.path.join(path1, "p_full_1.png")
SaveScreenshot(path2, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
ColorBy(casefoamDisplay, ('POINTS', 'U', 'Magnitude'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
casefoamDisplay.SetScalarBarVisibility(renderView1, True)
uLUT = GetColorTransferFunction('U')
uPWF = GetOpacityTransferFunction('U')
uTF2D = GetTransferFunction2D('U')
uLUT.ApplyPreset('Rainbow Uniform', True)
renderView1.Update()
casefoamDisplay.SetScalarBarVisibility(renderView1, True)
uLUTColorBar = GetScalarBar(uLUT, renderView1)
uLUTColorBar.Orientation = 'Horizontal'
uLUTColorBar.WindowLocation = 'Any Location'
uLUTColorBar.Position = [0.145, 0.019]
uLUTColorBar.ScalarBarLength = 0.34
casefoamDisplay.RescaleTransferFunctionToDataRange(True, False)
path3 = os.path.join(path1, "v_full_1.png")
SaveScreenshot(path3, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')

# pressure pic-2,3,4,5 export

ColorBy(casefoamDisplay, ('POINTS', 'p'))
HideScalarBarIfNotNeeded(uLUT, renderView1)
casefoamDisplay.SetScalarBarVisibility(renderView1, True)
renderView1.ResetActiveCameraToPositiveX()
renderView1.ResetCamera(False, 0.9)
renderView1.CameraPosition = [-0.1596, 0.0083, 0.0482]
renderView1.CameraFocalPoint = [0.0392, 0.0083, 0.049]
renderView1.CameraViewUp = [0.0, 0.0, 1.0]
renderView1.CameraParallelScale = 0.05146098720456678
casefoamDisplay.RescaleTransferFunctionToDataRange(True, False)
path4 = os.path.join(path1, "p_full_2.png")
SaveScreenshot(path4, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
renderView1.ResetActiveCameraToNegativeX()
renderView1.ResetCamera(False, 0.9)
renderView1.CameraPosition = [0.33, 0.096, 0.05]
renderView1.CameraFocalPoint = [0.039, 0.096, 0.05]
renderView1.CameraViewUp = [0.0, 0.0, 1.0]
renderView1.CameraParallelScale = 0.052
casefoamDisplay.RescaleTransferFunctionToDataRange(True, False)
path5 = os.path.join(path1, "p_full_3.png")
SaveScreenshot(path5, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
renderView1.ResetActiveCameraToPositiveY()
renderView1.ResetCamera(False, 0.9)
renderView1.CameraPosition = [0.072, -0.244, 0.0494]
renderView1.CameraFocalPoint = [0.073, 0.0469, 0.0498]
renderView1.CameraViewUp = [0.0, 0.0, 1.0]
renderView1.CameraParallelScale = 0.0518
casefoamDisplay.RescaleTransferFunctionToDataRange(True, False)
path6 = os.path.join(path1, "p_full_5.png")
SaveScreenshot(path6, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
renderView1.ApplyIsometricView()
renderView1.ResetCamera(False, 0.9)
renderView1.CameraPosition = [0.177, 0.25, 0.22]
renderView1.CameraFocalPoint = [0.01, 0.082, 0.0497]
renderView1.CameraViewUp = [-0.3, -0.51, 0.81]
renderView1.CameraParallelScale = 0.063
casefoamDisplay.RescaleTransferFunctionToDataRange(True, False)
path7 = os.path.join(path1, "p_full_4.png")
SaveScreenshot(path7, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')

# pressure & velocity section view pic-1 export

clip1 = Clip(registrationName='Clip1', Input=casefoam)
clip1.ClipType = 'Plane'
clip1.HyperTreeGridClipper = 'Plane'
clip1.Scalars = ['POINTS', 'p']
clip1.Value = 24.54
clip1.HyperTreeGridClipper.Origin = [0.039, 0.0468, 0.05385]
clip1.ClipType.Origin = [0.0364, 0.0468, 0.0538]
renderView1.Update()
clip1Display = Show(clip1, renderView1, 'UnstructuredGridRepresentation')
Hide(casefoam, renderView1)
ColorBy(clip1Display, ('POINTS', 'p'))
clip1Display.RescaleTransferFunctionToDataRange(True, False)
clip1Display.SetScalarBarVisibility(renderView1, True)
HideInteractiveWidgets(proxy=clip1.ClipType)
renderView1.CameraPosition = [0.2033, 0.0156, 0.0884]
renderView1.CameraFocalPoint = [0.0598, 0.0873, 0.0523]
renderView1.CameraViewUp = [-0.18498, 0.12046, 0.975]
renderView1.CameraParallelScale = 0.052
path8 = os.path.join(path1, "p_cut_1.png")
SaveScreenshot(path8, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
ColorBy(clip1Display, ('POINTS', 'U', 'Magnitude'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
clip1Display.RescaleTransferFunctionToDataRange(True, False)
clip1Display.SetScalarBarVisibility(renderView1, True)
path9 = os.path.join(path1, "v_cut_1.png")
SaveScreenshot(path9, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')

# pressure & velocity section view pic-2 export

clip1.ClipType.Origin = [0.04306, 0.0468, 0.05385]
ColorBy(clip1Display, ('POINTS', 'U', 'Magnitude'))
renderView1.Update()
renderView1.CameraPosition = [0.2381, 0.10142, 0.0492]
renderView1.CameraFocalPoint = [0.0216, 0.10142, 0.0493]
renderView1.CameraViewUp = [0.0, 0.0, 1.0]
renderView1.CameraParallelScale = 0.056
path10 = os.path.join(path1, "v_cut_2.png")
SaveScreenshot(path10, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
ColorBy(clip1Display, ('POINTS', 'p'))
HideScalarBarIfNotNeeded(uLUT, renderView1)
clip1Display.RescaleTransferFunctionToDataRange(True, False)
clip1Display.SetScalarBarVisibility(renderView1, True)
pLUT.RescaleTransferFunction(-13, 66)
pPWF.RescaleTransferFunction(-13, 66)
path11 = os.path.join(path1, "p_cut_2.png")
SaveScreenshot(path11, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
# rescale color and/or opacity maps used to exactly fit the current data range
clip1Display.RescaleTransferFunctionToDataRange(False, True)
Delete(clip1)

# export velocity plot with streamlines pic 1

SetActiveSource(casefoam)
casefoamDisplay = Show(casefoam, renderView1, 'UnstructuredGridRepresentation')
ColorBy(casefoamDisplay, ('FIELD', 'vtkBlockColors'))
casefoamDisplay.Opacity = 0.30
streamTracer1 = StreamTracer(registrationName='StreamTracer1', Input=casefoam,
    SeedType='Line')
streamTracer1.Vectors = ['POINTS', 'U']
streamTracer1.MaximumStreamlineLength = 0.12;
streamTracer1.SeedType.Point1 = [5.0e-05, -0.0003, 0.01]
streamTracer1.SeedType.Point2 = [0.08, 0.1, 0.1]
streamTracer1Display = Show(streamTracer1, renderView1, 'GeometryRepresentation')
streamTracer1Display.SetScalarBarVisibility(renderView1, True)
ColorBy(streamTracer1Display, ('POINTS', 'U', 'Magnitude'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
streamTracer1Display.RescaleTransferFunctionToDataRange(True, False)
streamTracer1Display.SetScalarBarVisibility(renderView1, True)
renderView1.Update()
tube1 = Tube(registrationName='Tube1', Input=streamTracer1)
tube1.Scalars = ['POINTS', 'p']
tube1.Vectors = ['POINTS', 'Normals']
tube1.Radius = 0.0004
tube1Display = Show(tube1, renderView1, 'GeometryRepresentation')
Hide(streamTracer1, renderView1)
tube1Display.SetScalarBarVisibility(renderView1, True)
ColorBy(tube1Display, ('POINTS', 'U', 'Magnitude'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
tube1Display.RescaleTransferFunctionToDataRange(True, False)
tube1Display.SetScalarBarVisibility(renderView1, True)
tube1Display.RescaleTransferFunctionToDataRange(False, True)
renderView1.Update()
uLUTColorBar = GetScalarBar(uLUT, renderView1)
uLUTColorBar.Orientation = 'Horizontal'
uLUTColorBar.WindowLocation = 'Any Location'
uLUTColorBar.Position = [0.152, 0.022]
uLUTColorBar.ScalarBarLength = 0.34
uLUT.RescaleTransferFunction(0.0, 12.026)
uPWF.RescaleTransferFunction(0.0, 12.026)

# export velocity plot with streamlines pic 2

SetActiveSource(casefoam)
streamTracer2 = StreamTracer(registrationName='StreamTracer2', Input=casefoam,
    SeedType='Line')
streamTracer2.Vectors = ['POINTS', 'U']
streamTracer2.MaximumStreamlineLength = 0.0942
streamTracer2.SeedType.Point1 = [5.0e-05, -0.0003, 0.01]
streamTracer2.SeedType.Point2 = [0.08, 0.1, 0.1]
streamTracer2.MaximumStreamlineLength = 0.12
streamTracer2Display = Show(streamTracer2, renderView1, 'GeometryRepresentation')
streamTracer2Display.SetScalarBarVisibility(renderView1, True)
ColorBy(streamTracer2Display, ('POINTS', 'U', 'Magnitude'))
streamTracer2Display.RescaleTransferFunctionToDataRange(True, False)
streamTracer2Display.SetScalarBarVisibility(renderView1, True)
renderView1.Update()
tube2 = Tube(registrationName='Tube2', Input=streamTracer2)
tube2.Scalars = ['POINTS', 'p']
tube2.Vectors = ['POINTS', 'Normals']
tube2.Radius = 0.0004
tube2Display = Show(tube2, renderView1, 'GeometryRepresentation')
Hide(streamTracer2, renderView1)
ColorBy(tube2Display, ('POINTS', 'U', 'Magnitude'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
tube2Display.RescaleTransferFunctionToDataRange(True, False)
tube2Display.SetScalarBarVisibility(renderView1, True)
renderView1.Update()
uLUTColorBar.Position = [0.139, 0.034]
uLUTColorBar.ScalarBarLength = 0.34
uLUT.RescaleTransferFunction(0.0, 12.026)
uPWF.RescaleTransferFunction(0.0, 12.026)
casefoamDisplay = Show(casefoam, renderView1, 'UnstructuredGridRepresentation')
renderView1.InteractionMode = '2D'
renderView1.ResetActiveCameraToPositiveY()
renderView1.ResetCamera(False, 0.9)
renderView1.CameraPosition = [0.072, -0.244, 0.0494]
renderView1.CameraFocalPoint = [0.073, 0.0469, 0.0498]
renderView1.CameraViewUp = [0.0, 0.0, 1.0]
renderView1.CameraParallelScale = 0.0518
path12 = os.path.join(path1, "v_streamlines1.png")
SaveScreenshot(path12, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')
# current camera placement for renderView1
renderView1.InteractionMode = '3D'
renderView1.CameraPosition = [0.216, -0.027, -0.02]
renderView1.CameraFocalPoint = [0.0663, 0.0866, 0.0473]
renderView1.CameraViewUp = [0.272, -0.2, 0.942]
renderView1.CameraParallelScale = 0.0513
path13 = os.path.join(path1, "v_streamlines2.png")
SaveScreenshot(path13, renderView1, 16, ImageResolution=[1577, 733], OverrideColorPalette='WhiteBackground')

# Quit Paraview
print("Finished taking photos of CFD Model in Paraview_v5.12")
print("Please check output images p & v .png files")
print("Time taken for postprocessing: ",time.time()-start_time)
