#  Application for the Nasal and Oropharyngeal Segmentation and Simulation of Airflow

A comprehensive graphical user interface designed for medical professionals to perform automated upper airway segmentation and computational fluid dynamics (CFD) simulations starting from CT or CBCT scans. This tool streamlines the workflow from image processing to final report generation.

<!-- TODO: Add a project logo or header image here -->
![Project Logo](path/to/logo.png)

## Features

- **Automated Image Processing**: Streamlined extraction of relevant medical image data using nnUNet
- **Advanced Segmentation Options**: Integrated CFD simulation features
- **Automated Reporting**: Generation of clear, concise analysis reports
- **User-Specific Data Management**: Secure data organization with individual user folders

If you use {AppName} for your work, please cite:
- **Research group work**:  
  <!-- TODO: Add Uday and Dr. Lange's work citation if applicable -->
  > Uday and Dr. Lange's work on simulation verification
  > Silvia's and Alejandro's work

- **nnU-Net**:  
  > Isensee F, Jaeger PF, Kohl SAA, Petersen J, Maier-Hein KH. nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. Nat Methods. 2021;18(2):203-211. doi:10.1038/s41592-020-01008-z



## System Requirements

### Operating System
- OpenSUSE 15.6 or later

### Required Software
- Python 3.11
- Blender 2.82
- OpenFOAM 2306
- ParaView 5.12
- nnUNetv2 

### Hardware Specifications
<!-- TODO: Specify hardware recommendations -->
- Recommended RAM: 32 GB
- GPU: NVIDIA processor

## Software Installation Scripts
If starting from a fresh OpenSUSE installation, you can run the following scripts to set up all necessary software:

<!-- TODO: Review what packages to install -->
[Script still needs to be written]
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/alejandro-matos/OpenSUSE-Setup-Scripts/main/OpenSUSE_Installation.sh)"
```
If you need to manually install the required software, you can do so using the following commands:

### System Dependencies Installation
Run the following command to install essential system packages:
[Review commands]
```bash
sudo zypper install -y python311 blender openfoam paraview
```
This command will:
- Install Python 3.11
- Install Blender 2.82 (adjust package name if needed)
- Install OpenFOAM 2306
- Install ParaView 5.12

### Python packages
Once system dependencies are installed, install the required Python libraries:
```bash
pip install -r requirements.txt
```


## {AppName} Quick Start Guide

<!-- TODO: Add video demo link or embed code -->
[![Watch the demo](path/to/demo_thumbnail.png)](https://link.to/demo)

1. Launch the application by clicking on the icon: [Insert icon]
2. Enter your username when prompted
3. Select and import medical images
4. Choose analysis options:
   - Airway segmentation only
   - Segmentation with CFD simulation
5. Review the generated report in your user folder

## Project Structure

```
Ortho_App/
├── main.py
├── src/
│   ├── main.py
│   ├── segmentation/
│   ├── cfd/
│   └── reporting/
├── user_data/
├── models/
└── config/
├── logs/
```

Logs are generated to help troubleshoot issues. These logs capture user activity, and system status. These logs can be found in the `logs/` directory and are useful for debugging potential issues.

## Data Management

All user data is stored in individual folders under the `user_data` directory:
```
user_data/
├── [username1]/
│   ├── images/
│   ├── segmentation/
│   ├── cfd_results/
│   └── reports/
└── [username2]/
    └── ...
```

## Troubleshooting
This section will list the most commonly encountered issues and how to solve them.
<!--tk Add issues and how to solve them-->

## Contributing

[Instructions for contributors]

## License

[Specify license]

## Contact

[Contact information]

## Acknowledgments
Authors: A. Matos Camarillo (University of Alberta), U. Tummala (University of Alberta), S. Capenakas-Gianoni (University of Alberta), K. Punithakumar (University of Alberta), C.F. Lange (University of Alberta), M. Lagravere-Vich (University of Alberta)
Supported by [Add funding sources tk]

---
**Note**: This is a medical tool intended for professional use only. Users should ensure compliance with local medical data handling regulations.
