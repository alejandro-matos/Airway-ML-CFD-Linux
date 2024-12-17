# gui/utils/image_processing.py
import os
import numpy as np
import pydicom
from PIL import Image
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

def load_dicom_series(folder_path: str) -> Tuple[List[pydicom.dataset.FileDataset], np.ndarray]:
    """
    Load a series of DICOM files and create a 3D volume.
    
    Args:
        folder_path: Path to folder containing DICOM files
        
    Returns:
        Tuple of (list of DICOM datasets, 3D volume array)
    """
    dicom_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith('.dcm')
    ]
    
    if not dicom_files:
        raise ValueError("No DICOM files found in the specified folder")

    # Load and sort slices
    slices = [pydicom.dcmread(f) for f in dicom_files]
    
    # Sort by slice location
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    
    # Create volume with proper scaling
    pixel_arrays = [s.pixel_array for s in slices]
    
    # Rescale to Hounsfield Units if possible
    volume = np.stack(pixel_arrays, axis=0)
    
    # Apply rescale slope and intercept if available
    if hasattr(slices[0], 'RescaleSlope') and hasattr(slices[0], 'RescaleIntercept'):
        slope = float(slices[0].RescaleSlope)
        intercept = float(slices[0].RescaleIntercept)
        volume = volume * slope + intercept
    
    return slices, volume

def generate_slices(dicom_folder: str) -> Dict[str, Image.Image]:
    """
    Generate middle slice previews in three orientations for dental CBCT.
    
    Args:
        dicom_folder: Path to DICOM folder
        
    Returns:
        Dictionary with axial, sagittal, and coronal preview images
    """
    # Load DICOM series
    slices, volume = load_dicom_series(dicom_folder)
    
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
        
        # Convert to PIL image with proper sizing
        target_width = 150
        aspect_ratio = enhanced.shape[0] / enhanced.shape[1]
        target_height = int(target_width * aspect_ratio)
        
        pil_image = Image.fromarray(enhanced)
        processed_slices[orientation] = pil_image.resize(
            (target_width, target_height),
            Image.Resampling.LANCZOS
        )
    
    return processed_slices