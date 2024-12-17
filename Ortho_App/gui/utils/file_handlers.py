# gui/utils/file_handlers.py
import os
import shutil
from typing import Optional, List
import pydicom

def create_patient_folder(base_path: str, username: str, patient_name: str, 
                         folder_name: str) -> str:
    """
    Create a folder structure for patient data.
    
    Args:
        base_path: Base directory path
        username: Username
        patient_name: Patient's name
        folder_name: Name for the new folder
        
    Returns:
        Full path to created folder
    """
    full_path = os.path.join(base_path, username, patient_name, folder_name)
    os.makedirs(full_path, exist_ok=True)
    return full_path

def get_existing_folders(base_path: str, username: str, 
                        patient_name: str) -> List[str]:
    """
    Get list of existing folders for a patient.
    
    Args:
        base_path: Base directory path
        username: Username
        patient_name: Patient's name
        
    Returns:
        List of folder names
    """
    patient_path = os.path.join(base_path, username, patient_name)
    if os.path.exists(patient_path):
        return sorted([
            folder for folder in os.listdir(patient_path)
            if os.path.isdir(os.path.join(patient_path, folder))
        ])
    return []

def validate_dicom_folder(folder_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a folder contains valid DICOM files.
    
    Args:
        folder_path: Path to folder to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not os.path.exists(folder_path):
            return False, "Folder does not exist"

        dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dcm')]
        if not dicom_files:
            return False, "No DICOM files found in folder"

        # Validate first DICOM file
        test_file = os.path.join(folder_path, dicom_files[0])
        pydicom.dcmread(test_file)
        
        return True, None
        
    except Exception as e:
        return False, f"Error validating DICOM folder: {str(e)}"