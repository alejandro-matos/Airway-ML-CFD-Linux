import os
import logging
import SimpleITK as sitk
from pathlib import Path
import torch
from batchgenerators.utilities.file_and_folder_operations import join
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
from nnunetv2.imageio.simpleitk_reader_writer import SimpleITKIO

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def convert_dicom_to_nifti(input_folder, output_folder):
    """Convert DICOM series to NIfTI format and rename it with '_0000' suffix."""
    try:
        logging.info("Converting DICOM to NIfTI...")

        # Read DICOM series
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(str(input_folder))
        
        if not dicom_names:
            raise ValueError("No DICOM series found in input directory")
        
        # Read first slice to get metadata
        first_slice = sitk.ReadImage(dicom_names[0])
        
        # Extract scan date and patient name from metadata
        scan_date = first_slice.GetMetaData("0008|0020")  # Format is YYYYMMDD
        full_name = first_slice.GetMetaData("0010|0010").replace("^", " ").strip()
        
        # Generate initials from patient name
        name_parts = full_name.split()
        initials = ''.join(part[0].upper() for part in name_parts if part)
        
        # Format the date from YYYYMMDD to YYYY-MM-DD
        formatted_date = f"{scan_date[:4]}-{scan_date[4:6]}-{scan_date[6:8]}"
        
        # Read the full DICOM series
        reader.SetFileNames(dicom_names)
        reader.MetaDataDictionaryArrayUpdateOn()
        image = reader.Execute()
        
        # Check and correct orientation if needed
        direction = image.GetDirection()
        if direction[8] < 0:
            image = sitk.Flip(image, [False, False, True])
        
        # Use folder name as base filename
        folder_name = Path(input_folder).stem
        nifti_filename = f"{folder_name}_0000.nii.gz"
        nifti_path = Path(output_folder) / nifti_filename
        
        # Save as NIfTI
        sitk.WriteImage(image, str(nifti_path))

        logging.info(f"NIfTI file saved: {nifti_path}")
        return nifti_path
    except Exception as e:
        logging.error(f"Error in DICOM to NIfTI conversion: {e}")
        raise


def run_nnunet_segmentation(nifti_paths, output_folder):
    """Run optimized nnUNet segmentation on a list of NIfTI files and save results."""
    try:
        logging.info("Initializing nnUNet Predictor...")

        # Initialize the nnUNetPredictor
        predictor = nnUNetPredictor(
            tile_step_size=0.7,
            use_gaussian=True,
            use_mirroring=True,
            perform_everything_on_device=True,  # Use GPU
            device=torch.device('cuda', 0),  # Ensure GPU is used
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=True
        )

        # Load trained model (update with your dataset/model)
        predictor.initialize_from_trained_model_folder(
            join("/home/cfduser/Desktop/CFD_GUI/Airway-ML-CFD-Linux/nnUNet/nnUNet_results", "Dataset014_Airways/nnUNetTrainer__nnUNetPlans__3d_fullres"),
            use_folds="all",
            checkpoint_name="checkpoint_final.pth"
        )

        # Ensure output folder exists
        Path(output_folder).mkdir(parents=True, exist_ok=True)

        # Run prediction in batch
        logging.info("Running nnUNet segmentation on input files...")
        
        input_files = [[str(path)] for path in nifti_paths]  # Nested list required for 3D images
        output_files = [str(Path(output_folder) / Path(path).name.replace("_0000.nii.gz", ".nii.gz")) for path in nifti_paths]

        predictor.predict_from_files(
            input_files, output_files,
            save_probabilities=False, overwrite=True,
            num_processes_preprocessing=6, num_processes_segmentation_export=6
        )

        logging.info(f"Segmentation completed. Results saved in {output_folder}")

    except Exception as e:
        logging.error(f"Error in nnUNet segmentation: {e}")
        raise


def main(input_folder):
    """Main function to convert DICOM to NIfTI, rename it, and run segmentation."""
    input_folder = Path(input_folder)
    parent_folder = input_folder.parent

    # Define output folders
    nifti_folder = parent_folder / "NIfTI_Converted"
    segmentation_folder = parent_folder / "Segmentation_Results"

    nifti_folder.mkdir(parents=True, exist_ok=True)
    segmentation_folder.mkdir(parents=True, exist_ok=True)

    nifti_paths = []
    reader = sitk.ImageSeriesReader()
    
    # First, check if the input folder itself contains DICOM files
    dicom_names = reader.GetGDCMSeriesFileNames(str(input_folder))
    if dicom_names:
        try:
            nifti_path = convert_dicom_to_nifti(input_folder, nifti_folder)
            nifti_paths.append(nifti_path)
        except Exception as e:
            logging.warning(f"Error processing {input_folder}: {e}")
    else:
        # Otherwise, iterate over subdirectories
        for dicom_subfolder in input_folder.iterdir():
            if dicom_subfolder.is_dir():
                try:
                    nifti_path = convert_dicom_to_nifti(dicom_subfolder, nifti_folder)
                    nifti_paths.append(nifti_path)
                except Exception as e:
                    logging.warning(f"Skipping {dicom_subfolder}: {e}")

    if not nifti_paths:
        logging.error("No valid NIfTI files found. Exiting.")
        return

    # Run segmentation on all converted NIfTI files
    run_nnunet_segmentation(nifti_paths, segmentation_folder)



if __name__ == "__main__":
    # Hardcoded input folder path (update this path as needed)
    input_folder = "/home/cfduser/Desktop/CFD_GUI/Airway-ML-CFD-Linux/nnUNet/nnUNet_raw/HU138T2/"
    main(input_folder)