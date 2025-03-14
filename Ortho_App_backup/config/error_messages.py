# config/error_messages.py

from typing import Dict

ERROR_MESSAGES: Dict[str, str] = {
    # File operations
    "FILE_NOT_FOUND": "The specified file could not be found: {0}",
    "INVALID_FILE_TYPE": "Invalid file type. Expected {0}, got {1}",
    "FILE_TOO_LARGE": "File size exceeds maximum limit of {0}MB",
    
    # DICOM handling
    "NO_DICOM_FILES": "No DICOM files found in the selected directory",
    "INVALID_DICOM": "Invalid or corrupted DICOM file: {0}",
    "MISSING_DICOM_TAG": "Required DICOM tag {0} is missing",
    
    # Form validation
    "REQUIRED_FIELD": "Please fill in the required field: {0}",
    "INVALID_DATE": "Invalid date format. Please use YYYY-MM-DD",
    "INVALID_NAME": "Invalid name format. Only letters, spaces, hyphens, and apostrophes are allowed",
    
    # Processing
    "PROCESSING_FAILED": "Processing failed: {0}",
    "SEGMENTATION_FAILED": "Airway segmentation failed: {0}",
    "CFD_FAILED": "CFD analysis failed: {0}",
    
    # External applications
    "APP_NOT_FOUND": "Required application not found: {0}",
    "APP_VERSION_MISMATCH": "Incompatible version of {0}. Required: {1}, Found: {2}",
    
    # System
    "INSUFFICIENT_MEMORY": "Insufficient system memory to complete operation",
    "DISK_SPACE_LOW": "Insufficient disk space. Required: {0}GB, Available: {1}GB"
}