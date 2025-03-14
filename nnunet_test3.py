import os
import logging
import SimpleITK as sitk
from pathlib import Path
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def convert_dicom_to_nifti(self):
    """
    Convert a single DICOM series to NIfTI format.
    For simplicity, extra metadata (e.g. patient initials) is omitted.
    """
    logging.info("Converting DICOM to NIfTI...")
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(str(self.input_folder))
    if not dicom_names:
        raise ValueError("No DICOM series found in input directory")
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    # Optional: adjust orientation if needed
    if image.GetDirection()[8] < 0:
        image = sitk.Flip(image, [False, False, True])
    sitk.WriteImage(image, str(self.nifti_folder))
    logging.info(f"NIfTI file saved: {output_file}")
    return output_file

def run_segmentation(nifti_file, output_file):
    """Run nnUNet segmentation on a single NIfTI file."""
    logging.info("Initializing nnUNet Predictor...")
    predictor = nnUNetPredictor(
        tile_step_size=0.7,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,  # Use GPU if available
        device=torch.device('cuda', 0),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True
    )
    # Update the model folder path to your trained model
    predictor.initialize_from_trained_model_folder(
        "/home/cfduser/Desktop/CFD_GUI/Airway-ML-CFD-Linux/nnUNet/nnUNet_results/Dataset014_Airways/nnUNetTrainer__nnUNetPlans__3d_fullres",
        use_folds="all",
        checkpoint_name="checkpoint_final.pth"
    )
    
    # nnUNetPredictor expects a nested list for input files
    input_files = [[str(nifti_file)]]
    output_files = [str(output_file)]
    
    predictor.predict_from_files(
        input_files, output_files,
        save_probabilities=False, overwrite=True,
        num_processes_preprocessing=2, num_processes_segmentation_export=2
    )
    logging.info(f"Segmentation completed. Result saved: {output_file}")

def main(input_dicom_folder):
    """
    Process a single DICOM series:
      1. Convert DICOM to NIfTI.
      2. Run segmentation on the NIfTI file.
    The output filenames are based on the original folder name.
    """
    input_dicom_folder = Path(input_dicom_folder)
    folder_name = input_dicom_folder.stem

    # Define output file paths in the parent folder
    output_nifti = input_dicom_folder.parent / f"{folder_name}.nii.gz"
    output_segmentation = input_dicom_folder.parent / f"{folder_name}_seg.nii.gz"
    
    # Convert DICOM to NIfTI
    nifti_file = convert_dicom_to_nifti(input_dicom_folder, output_nifti)
    # Run segmentation
    run_segmentation(nifti_file, output_segmentation)

if __name__ == "__main__":
    # Replace with your actual DICOM folder path
    dicom_folder_path = "/path/to/your/dicom/folder"
    main(dicom_folder_path)
