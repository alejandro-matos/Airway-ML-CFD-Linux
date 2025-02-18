# config/settings.py

from typing import Dict, Any
import os

# Application settings
APP_SETTINGS: Dict[str, Any] = {
    "TITLE": "Ortho CFD v0.2",
    "MIN_SIZE": (600, 750),
    "MAX_SIZE": "FULL SCREEN",
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
        "TITLE": ("Times_New_Roman", 30),
        "HEADER": ("Arial", 20, "bold"),
        "NORMAL": ("Arial", 16),
        "SMALL": ("Arial", 12),
        "BUTTON_TEXT":("Arial", 18, "bold"),
        "BUTTON_LABEL":("Arial", 16),
    },
    "COLORS": {
        "PRIMARY": "#255233",
        "SECONDARY": "gray20",
        "TEXT_LIGHT": "white",
        "TEXT_DARK": "black",
        "BACKGROUND": "gray20",
        "REG_BUTTON": "#025d34",
        "REG_HOVER": "#12251c",
        "NAV_BUTTON": "#D39E00",
        "NAV_HOVER": "#946C00",
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