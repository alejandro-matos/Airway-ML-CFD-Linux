import vtk
import nibabel as nib
import numpy as np
from pathlib import Path
import argparse

def calculate_volume(nifti_path):
    """
    Calculate the volume of the segmented airway in mm³.
    
    Args:
        nifti_path (str): Path to the NIfTI segmentation file.
    
    Returns:
        float: Total airway volume in mm³.
    """
    try:
        nifti_img = nib.load(nifti_path)
        data = nifti_img.get_fdata()
        voxel_sizes = nifti_img.header.get_zooms()
        
        voxel_volume = np.prod(voxel_sizes)  # mm³ per voxel
        airway_voxel_count = np.sum(data == 1)  # Assuming label 1 for airway
        total_volume_mm3 = airway_voxel_count * voxel_volume

        return total_volume_mm3

    except Exception as e:
        print(f"Error calculating volume: {e}")
        return None

def nifti_to_stl(nifti_file_path, output_folder, threshold_value=1, decimate=True, decimate_target_reduction=0.5):
    """
    Convert a NIfTI file to an STL file with optional decimation and smoothing.
    """
    try:
        nifti_file_path = Path(nifti_file_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        stl_filename = nifti_file_path.stem.replace("_pred", "_geo") + "_30_fixes2.stl"
        stl_file_path = output_folder / stl_filename

        reader = vtk.vtkNIFTIImageReader()
        reader.SetFileName(str(nifti_file_path))
        reader.Update()

        discrete_flying_edges = vtk.vtkDiscreteFlyingEdges3D()
        discrete_flying_edges.SetInputConnection(reader.GetOutputPort())
        discrete_flying_edges.SetValue(0, threshold_value)
        discrete_flying_edges.Update()

        output_polydata = discrete_flying_edges.GetOutput()

        num_cells = output_polydata.GetNumberOfCells()
        print(f"🔍 Number of triangles after flying edges: {num_cells}")

        # FIX: Ensure Separate Components in the Mesh
        connectivity_filter = vtk.vtkConnectivityFilter()
        connectivity_filter.SetInputData(output_polydata)
        connectivity_filter.SetExtractionModeToAllRegions()  # Extracts all connected parts
        connectivity_filter.ColorRegionsOn()  # Assigns different colors to regions
        connectivity_filter.Update()

        num_regions = connectivity_filter.GetNumberOfExtractedRegions()
        print(f"🔍 Number of detected regions: {num_regions}")

        output_polydata = connectivity_filter.GetOutput()

        # Ensure Triangulation Before Processing
        triangle_filter = vtk.vtkTriangleFilter()
        triangle_filter.SetInputData(output_polydata)
        triangle_filter.Update()
        output_polydata = triangle_filter.GetOutput()

        if decimate:
            decimator = vtk.vtkDecimatePro()
            decimator.SetInputData(output_polydata)
            decimator.SetTargetReduction(decimate_target_reduction) 
            decimator.PreserveTopologyOn()
            decimator.Update()
            output_polydata = decimator.GetOutput()

        # Adjust Smoothing for More Defined Geometry
        smoothing_filter = vtk.vtkWindowedSincPolyDataFilter()
        smoothing_filter.SetInputData(output_polydata)
        smoothing_filter.SetNumberOfIterations(30) 
        smoothing_filter.NonManifoldSmoothingOn()
        smoothing_filter.NormalizeCoordinatesOn()
        smoothing_filter.FeatureEdgeSmoothingOff()
        smoothing_filter.BoundarySmoothingOn()
        smoothing_filter.Update()
        output_polydata = smoothing_filter.GetOutput()

        # Ensure Proper Normal Calculation
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(output_polydata)
        normals.SetFeatureAngle(30.0)  # Sharper edges
        normals.ConsistencyOn()
        normals.SplittingOn()  # Allow edge splitting
        normals.Update()

        # Save STL in ASCII Format
        stl_writer = vtk.vtkSTLWriter()
        stl_writer.SetFileTypeToASCII()  # Easier debugging
        stl_writer.SetFileName(str(stl_file_path))
        stl_writer.SetInputData(normals.GetOutput())
        stl_writer.Write()

        return str(stl_file_path)

    except Exception as e:
        print(f"Error in STL creation: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test STL creation, smoothing, and volume calculation")
    parser.add_argument("nifti_file", help="Path to the existing NIfTI segmentation file")
    parser.add_argument("output_folder", help="Folder where STL will be saved")
    args = parser.parse_args()

    nifti_file = args.nifti_file
    output_folder = args.output_folder

    print("\n🔍 Processing Existing Segmentation File...")
    
    # Calculate volume
    volume = calculate_volume(nifti_file)
    if volume is not None:
        print(f"✅ Airway Volume: {volume:.2f} mm³")
    else:
        print("❌ Volume calculation failed.")

    # Convert to STL
    stl_path = nifti_to_stl(nifti_file, output_folder)
    if stl_path:
        print(f"✅ STL file created: {stl_path}")
    else:
        print("❌ STL conversion failed.")
