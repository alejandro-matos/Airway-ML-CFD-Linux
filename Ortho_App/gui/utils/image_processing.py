# gui/utils/image_processing.py
import os
import numpy as np
import pydicom
from PIL import Image
from typing import Dict, List, Tuple

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance the contrast of a medical image using percentile-based normalization.
    
    Args:
        image: Input image array
        
    Returns:
        Contrast-enhanced image array
    """
    p2, p98 = np.percentile(image, (2, 98))
    image_clipped = np.clip(image, p2, p98)
    image_normalized = ((image_clipped - p2) / (p98 - p2) * 255).astype(np.uint8)
    return image_normalized

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
    slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
    
    # Stack into 3D array
    volume = np.stack([s.pixel_array for s in slices], axis=0)
    
    return slices, volume

def generate_slices(dicom_folder: str) -> Dict[str, Image.Image]:
    """
    Generate middle slice previews in three orientations.
    
    Args:
        dicom_folder: Path to DICOM folder
        
    Returns:
        Dictionary with axial, sagittal, and coronal preview images
    """
    # Load DICOM series
    slices, volume = load_dicom_series(dicom_folder)
    
    # Apply contrast enhancement
    volume = enhance_contrast(volume)
    
    # Extract middle slices
    axial = volume[len(volume) // 2, :, :]
    coronal = volume[:, volume.shape[1] // 2, :]
    sagittal = volume[:, :, volume.shape[2] // 2]
    
    # Apply correct orientations for seated position CBCT
    axial = np.flipud(axial)      # Flip vertically for anterior-up
    coronal = np.flipud(coronal)  # Flip vertically for seated position
    sagittal = np.flipud(np.fliplr(sagittal))  # Flip for anterior-right
    
    # Convert to PIL images with proper sizing
    def slice_to_image(slice_data: np.ndarray) -> Image.Image:
        """Convert slice array to properly sized PIL Image."""
        target_width = 150
        target_height = int(target_width * (slice_data.shape[0] / slice_data.shape[1]))
        
        pil_image = Image.fromarray(slice_data)
        return pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    return {
        'axial': slice_to_image(axial),
        'coronal': slice_to_image(coronal),
        'sagittal': slice_to_image(sagittal)
    }