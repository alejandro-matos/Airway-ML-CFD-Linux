# Medical Imaging Analysis & CFD Simulation GUI

A comprehensive graphical user interface designed for medical professionals to perform automated airway segmentation and computational fluid dynamics (CFD) simulations. This tool streamlines the workflow from image processing to final report generation.

## Features

- **User-Specific Data Management**: Secure data organization with individual user folders
- **Automated Image Processing**: Streamlined extraction of relevant medical image data using nnUNet
- **Advanced Segmentation Options**: CFD simulation integration
- **Automated Reporting**: Generation of clear, concise analysis reports

If you use AppNameTk for your work, please cite <!--our paper and -->nnU-Net:

<!-- Matos Camarillo A, Capenakas-Gianoni S, Punithakumar K, Lagravere-Vich M. AirwaySegmentator: A deep learning-based method for Nasopharyngeal airway segmentation. Published online Month day, 2024:2024.xx.xx.xxxxxxxx. doi:10.1101/2024.xx.xx.xxxxxxxx-->
> Add Uday's and Dr. Lange's work? tk

> Isensee F, Jaeger PF, Kohl SAA, Petersen J, Maier-Hein KH. nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. Nat Methods. 2021;18(2):203-211. doi:10.1038/s41592-020-01008-z
<img src="https://github.com/alejandro-matos/SlicerUpperAirwaySegmentator/raw/main/Screenshots/angles.png" width="500"/>

## System Requirements

### Operating System
- OpenSUSE 15.6 or later
- Linux kernel version [specify minimum version]

### Required Software
- Python 3.11
- Blender [version]
- OpenFOAM [version]
- ParaView [version]
- nnUNetv2

### Hardware Requirements
[To be determined based on processing needs]
- Recommended RAM: 
- Processor: 
- GPU: 

## Installation

```bash
# System dependencies
sudo zypper install requirements.txt

# Python dependencies
pip install -r requirements.txt

# Additional software setup
[Instructions for Blender, OpenFOAM, ParaView, and nnUNet installation]
```

## Quick Start Guide

1. Launch the application:
```bash
python main.py
```

2. Enter your username when prompted
3. Select and import medical images
4. Choose analysis options:
   - Airway segmentation only
   - Segmentation with CFD simulation
5. Review the generated report in your user folder

## Project Structure

```
project/
├── src/
│   ├── main.py
│   ├── segmentation/
│   ├── cfd/
│   └── reporting/
├── user_data/
├── models/
└── config/
```

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
Supported by (Add funding sources tk)

---
**Note**: This is a medical tool intended for professional use only. Users should ensure compliance with local medical data handling regulations.
