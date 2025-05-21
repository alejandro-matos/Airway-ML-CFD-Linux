# config/settings.py

from typing import Dict, Any
import os
from pathlib import Path

# Application settings
APP_SETTINGS: Dict[str, Any] = {
    "TITLE": "Ortho CFD v0.2",
    "THEME": "green",
    "APPEARANCE_MODE": "dark",
    "FULLSCREEN": True,
    "MIN_SIZE": (600, 750)
}

# Path configurations
PATH_SETTINGS: Dict[str, Path] = {
    "HOME_DIR": Path.home(),
    "BASE_DIR": Path(__file__).resolve().parents[2],
    "USER_DATA": Path.home() / "Desktop" / "CFD_GUI" / "User_Data",
    "ICONS_DIR": Path(__file__).resolve().parents[2] / "gui" / "components" / "icons",
    "CFD_ICON": "CFDLab-blogo2.png",
    "GIF": "ualberta.gif",
    "LOGS_DIR": "logs",
    "TEMP_DIR": "temp",
    "OUTPUT_DIR": "output",
    "CONTRIB_DIR": Path(__file__).resolve().parents[2] / "contributors.json",
}

# UI settings
UI_SETTINGS: Dict[str, Any] = {
    "FONTS": {
        "TITLE": ("Times_New_Roman", 30),
        "HEADER": ("Arial", 28, "bold"),
        "NORMAL": ("Arial", 20),
        "CATEGORY":("Arial", 20, "bold"),
        "SMALL": ("Arial", 16),
        "BUTTON_TEXT":("Arial", 24, "bold"),
        "BUTTON_LABEL":("Arial", 20),
        # For contributors section
        "CONTRIB_BUTTON":("Arial", 18, "bold"),
        "CONTRIB_NAME": ("Roboto", 20, "bold"),
        "NORMAL_ITALIC": ("Roboto", 16, "italic"),
        "SMALL_CONTR": ("Roboto", 14),
        "LARGE_SYMBOL": ("Roboto", 22, "bold"),  # For the close button X
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
        "SUCCESS": "green",
        "SECTION_ACTIVE": "#2B2B2B",  # Normal background for active section
        "SECTION_INACTIVE": "#1E1E1E",  # Darker background for inactive section
        "TEXT_DISABLED": "#666666",  # Gray text for inactive sections
        "TEXT_HIGHLIGHT": "#4CAF50",  # Green for active step indicators
        "DISABLED_BUTTON": "#333333",  # Darker button for disabled state
        "DISABLED_BG": "#333333",  # Darker background for disabled inputs
        # For contributors section:
        "SECONDARY": "#3A7CA5",       # A complementary blue for headers
        "CARD_BG": "#F5F5F5",         # Light background for contributor cards
        "BG_LIGHT": "#FFFFFF",        # White background
        "LINK": "#0066CC",            # Blue for clickable links
        "PANEL_BG": "#E8F0F6",        # Light blue background for the side panel
    },
    "HOME_BUTTON": {
        "WIDTH": 120,
        "HEIGHT": 50,
    },
    "PADDING": {
        "SMALL": 5,
        "MEDIUM": 10,
        "LARGE": 20
    },
    "CT_SLICE_SIZE": {
        "SMALL_SCREEN": "300", # 16 inch
        "LARGE_SCREEN": "500" # 24 inch
    },
    "WINDOW": {
        "CORNER_RADIUS": 10, 
        "PAD_X": 10, 
        "PAD_Y": 10
    },
    "LOGO":{
        "WIDTH": 350,
        "HEIGHT": 170,
        "ANIMATION_DELAY_MS": 50
    },
    "PLACEHOLDERS": {
        "ANALYSIS_MENU": "Select Analysis Type"
    }
}

# File handling settings
FILE_SETTINGS: Dict[str, Any] = {
    "ALLOWED_EXTENSIONS": {
        "DICOM": [".dcm"],
        "MESH": [".stl", ".obj"],
        "RESULTS": [".vtk", ".vtu", ".csv"]
    },
    "MAX_FILE_SIZE":  500* 1024 * 1024,  # 500MB
    "TEMP_FILE_EXPIRY": 24 * 60 * 60 * 30  # 24 hours in seconds
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
        "PATH": r"/usr/bin/blender",
        "VERSION": "2.82",
        "REQUIRED": True
    },
    "OPENFOAM": {
        "PATH": r"/usr/bin/openfoam",
        "VERSION": "2412",
        "REQUIRED": True
    },
    "PARAVIEW": {
        "PATH": r"/opt/paraview",
        "VERSION": "5.13.3",
        "REQUIRED": True
    }
}


### TAB2 ##### 
TAB2_SETTINGS: Dict[str, Any] = {
    # Which fields must be filled before proceeding
    "REQUIRED_FIELDS": [
        ("patient_name",       "Patient Name"),
        ("dob",                "Date of Birth"),
        ("scandate",           "Scan Date"),
        ("patient_doctor_var", "Referring Physician"),
        ("folder_name_var",    "Patient Results Folder"),
    ],

    # Text labels and messages
    "TEXT": {
        "HOME_BUTTON":           "Home",
        "STEP_HEADER":           "Step 1 of 3: Upload Patient Scans & Information",
        "UPLOAD_LABEL":          "Upload Patient Scans",
        "BROWSE_BUTTON":         "Browse for Medical Images",
        "UPLOAD_STATUS_NO_FILES":"No files selected",
        "PATIENT_INFO_TITLE":    "Patient Information",
        "FOLDER_SECTION_TITLE":  "Case Label",
        "NO_DRIVES_ERROR": (
            "No external storage devices were found.\n"
            "Please connect a USB drive and try again."
        ),
        "NO_FILES_WARNING":      "Please select one or more files (not folders).",
        "LOAD_SUCCESS":          "{count} {type} file(s) loaded successfully.",
        "INVALID_FIELDS_ERROR":  "Please provide: {fields}",
    },

    # Sizes and dimensions
    "DIMENSIONS": {
        "BROWSE_BUTTON":   {"width": 220, "height": 50},
        "INFO_BUTTON":     {"DIAMETER": 30},
        "ENTRY_WIDTH":     300,
        "DIALOG_SIZE":     (1000, 700),
        "TREEVIEW_FONT":       ("Arial", 16),
        "TREEVIEW_ROWHEIGHT":  28,
        "TREEVIEW_HEADING_FONT":("Arial", 18),
        "ACTION_BUTTON":   {"width": 120, "height": 40},
    },


    # File-type dropdown options and their internal mappings
    "FILE_TYPES": {
        "DICOM_ONLY": "DICOM files only",
        "NIFTI_ONLY": "NIfTI files only",
        "ALL":        "All Files",
        "MAPPING": {
            "DICOM files only": "dicom",
            "NIfTI files only": "nifti",
            "All Files":         "all",
        },
    },

}


### TAB 4 ###
TAB4_UI: Dict[str, Any] = {
    "ANALYSIS_TYPE_MENU": {
        "WIDTH": 375,
        "HEIGHT": 40,
    },
     # Data for dynamic tab creation
    "TABS": [
        {"name": "Segmentation",             "color": "#00734d"},
        {"name": "Post-processed Geometry",  "color": "#006a9f"},
        {"name": "CFD Simulation",           "color": "#a63600"},
    ],
    "TAB_HEIGHTS": {
        "normal": 35,
        "active": 40
    }
}

TAB4_SETTINGS: Dict[str, Any] = {
    # 1) the tabs, in order:
    "TABS": [
        "Segmentation",
        "Post-processed Geometry",
        "CFD Simulation"
    ],
    # 2) each tab’s “active” color:
    "COLORS": {
        "Segmentation":             "#00734d",
        "Post-processed Geometry":  "#006a9f",
        "CFD Simulation":           "#a63600"
    },
    # 3) styling to apply only when a tab is active:
    "ACTIVE": {
        "border_width": 3,
        "border_color": "#222222"
    },
    # 4) styling to apply when a tab is *not* active:
    "INACTIVE": {
        "fg_color":    "#d9d9d9",
        "border_width": 0
    },
    # 5) optional: shadow-bar color under the tabs container
    "SHADOW_COLOR": "#ababab",
    "RENDER_BUTTON": {
        "FG_COLOR":    "#006a9f",
        "HOVER_COLOR": "#005380",
        "WIDTH": 350,
        "HEIGHT": 60,
    },
}
