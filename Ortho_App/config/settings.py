# config/settings.py

from typing import Dict, Any
import os

# Application settings
APP_SETTINGS: Dict[str, Any] = {
    "TITLE": "Ortho CFD v0.2",
    "MIN_SIZE": (600, 750),
    "MAX_SIZE": (700, 1000),
    "THEME": "green",
    "APPEARANCE_MODE": "dark"
}

# Path configurations
PATH_SETTINGS: Dict[str, str] = {
    "BASE_DIR": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "LOGS_DIR": "logs",
    "TEMP_DIR": "temp",
    "OUTPUT_DIR": "output",
    "ICONS_DIR": "assets/icons",
    "IMAGES_DIR": "assets/images"
}

# UI settings
UI_SETTINGS: Dict[str, Any] = {
    "FONTS": {
        "TITLE": ("Times_New_Roman", 25),
        "HEADER": ("Arial", 15, "bold"),
        "NORMAL": ("Arial", 12),
        "SMALL": ("Arial", 10)
    },
    "COLORS": {
        "PRIMARY": "#255233",
        "SECONDARY": "gray20",
        "TEXT_LIGHT": "white",
        "TEXT_DARK": "black",
        "BACKGROUND": "gray20",
        "BUTTON": "blue",
        "WARNING": "red",
        "SUCCESS": "green"
    },
    "PADDING": {
        "SMALL": 5,
        "MEDIUM": 10,
        "LARGE": 20
    }
}

# File handling settings
FILE_SETTINGS: Dict[str, Any] = {
    "ALLOWED_EXTENSIONS": {
        "DICOM": [".dcm"],
        "MESH": [".stl", ".obj"],
        "RESULTS": [".vtk", ".vtu", ".csv"]
    },
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100MB
    "TEMP_FILE_EXPIRY": 24 * 60 * 60  # 24 hours in seconds
}

# Analysis settings
ANALYSIS_SETTINGS: Dict[str, Any] = {
    "SEGMENTATION": {
        "DEFAULT_THRESHOLD": -400,  # HU value
        "MARGIN": 1.0,  # mm
        "MIN_REGION_SIZE": 100  # voxels
    },
    "CFD": {
        "MESH_SIZE": {
            "COARSE": 1.0,  # mm
            "MEDIUM": 0.5,  # mm
            "FINE": 0.25    # mm
        },
        "INLET_PRESSURE": 0,      # Pa
        "OUTLET_PRESSURE": -10,    # Pa
        "MAX_ITERATIONS": 1000,
        "CONVERGENCE_CRITERIA": 1e-6
    }
}

# External applications
EXTERNAL_APPS: Dict[str, Dict[str, Any]] = {
    "BLENDER": {
        "PATH": r"C:\Program Files\Blender Foundation\Blender 3.6",
        "VERSION": "3.6",
        "REQUIRED": True
    },
    "OPENFOAM": {
        "PATH": r"C:\Program Files\OpenFOAM",
        "VERSION": "10",
        "REQUIRED": True
    },
    "PARAVIEW": {
        "PATH": r"C:\Program Files\ParaView 5.11.0",
        "VERSION": "5.11.0",
        "REQUIRED": True
    }
}