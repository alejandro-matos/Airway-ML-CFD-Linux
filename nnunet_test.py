import os
import logging
import re
import subprocess
import SimpleITK as sitk
from pathlib import Path
import threading

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

def run_nnunet_segmentation(nifti_path, output_folder):
    """Run nnUNet segmentation on the given NIfTI file and save results."""
    try:
        logging.info("Running nnUNet segmentation...")

        # Create subprocess with pipe for output
        process = subprocess.Popen(
            [
                'nnUNetv2_predict',
                '-i', str(nifti_path.parent),
                '-o', str(output_folder),
                '-d', 'Dataset014_Airways',
                '-c', '3d_fullres',
                '-f', 'all',
                '-npp', '4'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output in a separate thread
        output_thread = threading.Thread(
            target=_stream_subprocess_output,
            args=(process, "nnUNet Prediction", 30)
        )
        output_thread.start()

        process.wait()
        output_thread.join()  # Ensure the thread completes

        if process.returncode == 0:
            logging.info(f"Segmentation completed successfully. Results saved in {output_folder}")
        else:
            logging.error("nnUNet segmentation failed. Check logs for details.")

    except Exception as e:
        logging.error(f"Error in segmentation: {e}")
        raise

def _stream_subprocess_output(process, stage_name, base_progress):
    """Stream subprocess output for logging and progress tracking."""
    percentage_pattern = re.compile(r'^\d+%')

    while True:
        if process.poll() is not None:
            break

        output_line = process.stdout.readline().strip()
        if output_line:
            logging.info(f"{stage_name}: {output_line}")
            if percentage_pattern.match(output_line):
                try:
                    percentage = int(output_line.split('%')[0])
                    progress = base_progress + (percentage / 100) * 20
                    logging.info(f"{stage_name}: {progress}% completed")
                except (IndexError, ValueError):
                    pass

    remaining_output = process.stdout.read()
    if remaining_output:
        for line in remaining_output.splitlines():
            if line.strip():
                logging.info(f"{stage_name}: {line}")

def main(input_folder):
    """Main function to convert DICOM to NIfTI, rename it, and run segmentation."""
    input_folder = Path(input_folder)
    parent_folder = input_folder.parent

    # Define output folders
    nifti_folder = parent_folder / "NIfTI_Converted"
    segmentation_folder = parent_folder / "Segmentation_Results"

    nifti_folder.mkdir(parents=True, exist_ok=True)
    segmentation_folder.mkdir(parents=True, exist_ok=True)

    # Convert DICOM to NIfTI
    nifti_path = convert_dicom_to_nifti(input_folder, nifti_folder)

    # Run segmentation
    run_nnunet_segmentation(nifti_path, segmentation_folder)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert DICOM to NIfTI and run nnUNet segmentation.")
    parser.add_argument("input_folder", type=str, help="Path to the input DICOM folder.")
    args = parser.parse_args()

    main(args.input_folder)
