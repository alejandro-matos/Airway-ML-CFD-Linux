# gui/utils/image_processing.py
import os
import numpy as np
import pydicom
from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance the contrast of a medical image using window/level adjustment.
    
    Args:
        image: Input image array
        
    Returns:
        Contrast-enhanced image array
    """
    # Use different window/level values for dental CBCT
    p1, p99 = np.percentile(image, (1, 99))  # Changed from 2,98 to 1,99 for better contrast
    window = p99 - p1
    level = (p99 + p1) / 2
    
    # Apply window/level transformation
    image_windowed = np.clip(image, level - window/2, level + window/2)
    image_normalized = ((image_windowed - (level - window/2)) / window * 255).astype(np.uint8)
    
    return image_normalized

def get_orientation_matrices() -> Dict[str, np.ndarray]:
    """
    Get orientation matrices for dental CBCT.
    These matrices help ensure consistent orientation across views.
    """
    return {
        'axial': np.array([
            [0, -1],  # Rotate 90° clockwise
            [-1, 0]
        ]),
        'sagittal': np.array([
            [-1, 0],  # Flip horizontally and vertically
            [0, -1]
        ]),
        'coronal': np.array([
            [1, 0],   # Flip vertically only
            [0, -1]
        ])
    }

def orient_slice(slice_data: np.ndarray, orientation: str) -> np.ndarray:
    """
    Orient a slice according to dental CBCT conventions.
    
    Args:
        slice_data: 2D array of the slice
        orientation: One of 'axial', 'sagittal', 'coronal'
        
    Returns:
        Properly oriented slice
    """
    # Get orientation matrices
    matrices = get_orientation_matrices()
    
    # Apply orientation transform
    if orientation in matrices:
        # Apply the transformation matrix
        oriented = np.zeros_like(slice_data)
        matrix = matrices[orientation]
        
        if orientation == 'axial':
            oriented = np.flipud(np.rot90(slice_data, k=2))  # Flip axis
        elif orientation == 'sagittal':
            oriented = np.flipud(slice_data)  # Flip both axis
        else:  # coronal
            oriented = np.flipud(slice_data)  # Flip vertical only
            
        return oriented
    return slice_data

def is_dicom_file(file_path):
    """
    Check if a file is a valid DICOM file containing image data.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if the file is a valid DICOM image file, False otherwise
    """
    # Skip files that should be ignored
    if should_skip_file(file_path):
        return False
        
    try:
        # Quick check: If DCM appears in the filename, try reading it
        if "DCM" in os.path.basename(file_path).upper():
            try:
                ds = pydicom.dcmread(file_path, force=True)
                # Make sure it contains image data
                if hasattr(ds, 'pixel_array'):
                    return True
                return False
            except:
                pass
        
        # For files without DCM in the name, do a more thorough check
        try:
            with open(file_path, 'rb') as f:
                # Skip the 128-byte preamble
                f.seek(128)
                # Check for DICM magic number
                magic = f.read(4)
                if magic == b'DICM':
                    # It's a standard DICOM file with proper header
                    # Now check if it contains image data
                    ds = pydicom.dcmread(file_path, force=True)
                    if hasattr(ds, 'pixel_array'):
                        return True
                    return False
                    
            # If no magic number, try a last resort read
            ds = pydicom.dcmread(file_path, force=True)
            # Verify it has pixel data
            if hasattr(ds, 'pixel_array'):
                return True
        except:
            return False
    except:
        return False
        
    return False

def load_dicom_series(folder_path: str) -> Tuple[List[pydicom.dataset.FileDataset], np.ndarray]:
    """
    Load a series of DICOM files and create a 3D volume.
    Enhanced to work with non-standard DICOM files and filter out non-image files.
    
    Args:
        folder_path: Path to folder containing DICOM files
        
    Returns:
        Tuple of (list of DICOM datasets, 3D volume array)
    """
    # Find all files in the folder - don't filter by extension
    all_files = []
    folder = Path(folder_path)
    
    for f in folder.iterdir():
        if f.is_file():
            all_files.append(str(f))
    
    if not all_files:
        raise ValueError("No files found in the specified folder")
    
    print(f"Found {len(all_files)} total files in folder")
    
    # Filter for DICOM files by checking file content
    dicom_files = []
    for file_path in all_files:
        if is_dicom_file(file_path):
            dicom_files.append(file_path)
            # print(f"Valid DICOM: {os.path.basename(file_path)}") # For troubleshooting
    
    print(f"Identified {len(dicom_files)} DICOM image files")
    
    if not dicom_files:
        raise ValueError("No DICOM image files found in the specified folder.")

    # Load and sort slices - use force=True for non-standard files
    slices = []
    for f in dicom_files:
        try:
            ds = pydicom.dcmread(f, force=True)
            # Double-check that it has pixel data
            if not hasattr(ds, 'pixel_array'):
                continue
            slices.append(ds)
        except Exception as e:
            print(f"Warning: Could not read {os.path.basename(f)}: {e}")
    
    if not slices:
        raise ValueError("Could not read any DICOM files successfully")
    
    # Try to sort by slice location - use multiple sorting strategies for robustness
    try:
        # First try: Sort by ImagePositionPatient[2] if available
        if hasattr(slices[0], 'ImagePositionPatient'):
            slices.sort(key=lambda s: float(s.ImagePositionPatient[2]) if hasattr(s, 'ImagePositionPatient') else 0)
        # Second try: Sort by InstanceNumber if available
        elif hasattr(slices[0], 'InstanceNumber'):
            slices.sort(key=lambda s: int(s.InstanceNumber) if hasattr(s, 'InstanceNumber') else 0)
        # Last resort: Just use the file name order
        else:
            print("Warning: No standard DICOM sorting attributes found. Using original file order.")
    except Exception as e:
        print(f"Warning: Could not sort slices properly: {e}. Using original file order.")
    
    # Create volume with proper scaling
    try:
        pixel_arrays = [s.pixel_array for s in slices]
        
        # Check if all arrays have the same dimensions
        if len(set(arr.shape for arr in pixel_arrays)) > 1:
            print("Warning: Not all DICOM slices have the same dimensions. Filtering inconsistent slices.")
            # Get the most common dimension
            from collections import Counter
            shapes = [arr.shape for arr in pixel_arrays]
            most_common_shape = Counter(shapes).most_common(1)[0][0]
            
            # Filter slices with the most common dimension
            consistent_slices = []
            consistent_arrays = []
            for i, arr in enumerate(pixel_arrays):
                if arr.shape == most_common_shape:
                    consistent_slices.append(slices[i])
                    consistent_arrays.append(arr)
            
            slices = consistent_slices
            pixel_arrays = consistent_arrays
            
            print(f"After filtering: {len(slices)} consistent slices with shape {most_common_shape}")
            
            if len(slices) < 3:
                raise ValueError("Not enough consistent DICOM slices to create a 3D volume")
        
        volume = np.stack(pixel_arrays, axis=0)
        
        # Apply rescale slope and intercept if available
        if hasattr(slices[0], 'RescaleSlope') and hasattr(slices[0], 'RescaleIntercept'):
            slope = float(slices[0].RescaleSlope)
            intercept = float(slices[0].RescaleIntercept)
            volume = volume * slope + intercept
        
        return slices, volume
    except Exception as e:
        raise ValueError(f"Failed to create 3D volume: {str(e)}")

def generate_slices(dicom_folder: str) -> Dict[str, Image.Image]:
    """
    Generate middle slice previews in three orientations for dental CBCT.
    Enhanced to work with non-standard DICOM files.

    Args:
        dicom_folder: Path to DICOM folder

    Returns:
        Dictionary with axial, sagittal, and coronal preview images
    """
    print(f"Generating slices from: {dicom_folder}")
    
    # Load DICOM series - enhanced to work with non-standard files
    slices, volume = load_dicom_series(dicom_folder)
    
    print(f"Scan shape: {volume.shape}")
    
    # Extract middle slices
    middle_slices = {
        'axial': volume[len(volume) // 2, :, :],
        'coronal': volume[:, volume.shape[1] // 2, :],
        'sagittal': volume[:, :, volume.shape[2] // 2]
    }
    
    # Process each slice
    processed_slices = {}
    for orientation, slice_data in middle_slices.items():
        # Orient the slice
        oriented = orient_slice(slice_data, orientation)
        
        # Enhance contrast
        enhanced = enhance_contrast(oriented)
        
        # Convert to PIL image with larger sizing
        target_width = 700  # Increased for better visibility
        aspect_ratio = enhanced.shape[0] / enhanced.shape[1]
        target_height = int(target_width * aspect_ratio)

        pil_image = Image.fromarray(enhanced)
        processed_slices[orientation] = pil_image.resize(
            (target_width, target_height),
            Image.Resampling.LANCZOS
        )
    
    return processed_slices

def generate_nifti_slices(nifti_file: str) -> Dict[str, Image.Image]:
    """
    Generate orthogonal slices from a NIfTI file with proper orientation
    
    Args:
        nifti_file: Path to NIfTI file
        
    Returns:
        Dictionary with orthogonal views as PIL images
    """
    try:
        import nibabel as nib
        import numpy as np
        
        print(f"Reading NIfTI file: {nifti_file}")
        # Load the NIfTI file
        img = nib.load(nifti_file)
        data = img.get_fdata()
        
        print(f"NIfTI volume shape: {data.shape}")
        
        # Get the middle slice index for each dimension
        x_mid = data.shape[0] // 2
        y_mid = data.shape[1] // 2
        z_mid = data.shape[2] // 2
        
        # Extract the middle slices - get raw data first
        axial_raw = data[:, :, z_mid]
        coronal_raw = data[:, y_mid, :]
        sagittal_raw = data[x_mid, :, :]
        
        # Apply specific orientation adjustments for NIfTI
        # These transformations might need fine-tuning based on your specific data
        axial = np.flip(np.rot90(axial_raw, k=3), axis=1)  # Rotate and flip to match DICOM convention
        axial = np.flip(axial, axis=1)
        coronal = np.flip(np.rot90(coronal_raw, k=1), axis=1)  # Rotate and flip
        coronal = np.flip(coronal, axis=1)
        sagittal = np.flip(np.rot90(sagittal_raw, k=1), axis=1)  # Rotate and flip
        sagittal = np.flip(sagittal, axis=1)

        # For debugging orientation issues:
        print(f"Axial shape after orientation: {axial.shape}")
        print(f"Coronal shape after orientation: {coronal.shape}")
        print(f"Sagittal shape after orientation: {sagittal.shape}")
        
        # Create dictionary of oriented slices
        slices = {
            'axial': axial,
            'coronal': coronal,
            'sagittal': sagittal
        }
        
        # Process each slice similar to DICOM processing
        processed_slices = {}
        for orientation, slice_data in slices.items():
            # Enhance contrast - This function should work the same for both DICOM and NIfTI
            enhanced = enhance_contrast(slice_data)
            
            # Convert to PIL image with consistent sizing
            target_width = 700  # Same as DICOM for consistency
            aspect_ratio = enhanced.shape[0] / enhanced.shape[1]
            target_height = int(target_width * aspect_ratio)

            pil_image = Image.fromarray(enhanced)
            processed_slices[orientation] = pil_image.resize(
                (target_width, target_height),
                Image.Resampling.LANCZOS
            )
        
        return processed_slices
        
    except ImportError:
        print("Error: nibabel library is not installed. Please install with 'pip install nibabel'")
        raise
    except Exception as e:
        import traceback
        print(f"Error generating NIfTI slices: {e}")
        print(traceback.format_exc())
        raise ValueError(f"Could not generate slices from NIfTI file: {str(e)}")

# Alternative implementation using SimpleITK if PyDICOM approach fails
def generate_slices_sitk(dicom_folder: str) -> Dict[str, Image.Image]:
    """
    Alternative slice generation using SimpleITK - more robust for non-standard DICOM files.
    
    Args:
        dicom_folder: Path to DICOM folder
    
    Returns:
        Dictionary with axial, sagittal, and coronal preview images
    """
    import SimpleITK as sitk
    
    try:
        # Read DICOM series
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(str(dicom_folder))
        
        if not dicom_names:
            # Try to find files manually and read them
            all_files = list(Path(dicom_folder).glob('*'))
            if not all_files:
                raise ValueError("No files found in the specified folder")
                
            # Get a list of valid files by trying to read each one
            valid_files = []
            for file_path in all_files:
                if file_path.is_file():
                    try:
                        _ = sitk.ReadImage(str(file_path))
                        valid_files.append(str(file_path))
                    except:
                        pass
            
            if not valid_files:
                raise ValueError("No DICOM files found in the specified folder")
                
            dicom_names = valid_files
        
        reader.SetFileNames(dicom_names)
        image = reader.Execute()
        
        # Get dimensions
        size = image.GetSize()
        
        # Extract middle slices for each view
        axial_slice = sitk.GetArrayFromImage(
            sitk.Extract(image, 
                        [size[0], size[1], 0], 
                        [0, 0, size[2]//2])
        )[0]
        
        sagittal_slice = sitk.GetArrayFromImage(
            sitk.Extract(image, 
                        [0, size[1], size[2]], 
                        [size[0]//2, 0, 0])
        )
        
        coronal_slice = sitk.GetArrayFromImage(
            sitk.Extract(image, 
                        [size[0], 0, size[2]], 
                        [0, size[1]//2, 0])
        )
        
        # Convert to PIL Images with contrast enhancement
        def array_to_image(array):
            # Use the same contrast enhancement logic
            enhanced = enhance_contrast(array)
            
            # Convert to PIL image
            target_width = 500
            aspect_ratio = enhanced.shape[0] / enhanced.shape[1]
            target_height = int(target_width * aspect_ratio)
            
            pil_image = Image.fromarray(enhanced)
            return pil_image.resize(
                (target_width, target_height),
                Image.Resampling.LANCZOS
            )
        
        return {
            "axial": array_to_image(axial_slice),
            "sagittal": array_to_image(sagittal_slice),
            "coronal": array_to_image(coronal_slice)
        }
    
    except Exception as e:
        print(f"SimpleITK slice generation error: {e}")
        raise

def should_skip_file(file_path):
    """
    Determines if a file should be skipped in DICOM processing.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if the file should be skipped, False otherwise
    """
    file_name = os.path.basename(file_path).upper()
    
    # Skip common non-image DICOM files
    if file_name == "DICOMDIR":
        return True
        
    # Skip certain folders
    parent_folder = os.path.basename(os.path.dirname(file_path)).upper()
    if parent_folder in ["CASEDATA"]:
        return True
        
    # Skip files with known non-image extensions
    excluded_extensions = ['.ini', '.txt', '.xml', '.json', '.log', '.dat', '.exe', '.dll']
    if any(file_path.lower().endswith(ext) for ext in excluded_extensions):
        return True
    
    # Skip files that are very small (likely not DICOM images)
    try:
        file_size = os.path.getsize(file_path).utils.image_processing
        if file_size < 4096:  # Files smaller than 4KB are unlikely to be image data
            return True
    except:
        pass
        
    return False