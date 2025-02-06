import os
import logging
import subprocess
import threading
import SimpleITK as sitk
import nibabel as nib
import numpy as np
import vtk
from pathlib import Path
import re
from gui.utils.app_logger import AppLogger

class AirwayProcessor:
    def __init__(self, input_folder, output_folder, callback=None):
        """
        Initialize the airway processing pipeline
        
        Args:
            input_folder (str): Path to folder containing DICOM files
            output_folder (str): Path to output folder for all processing steps
            callback (callable): Optional callback function for progress updates
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.callback = callback
        self.current_subprocess = None
        self.logger = AppLogger() 
        
        # Create necessary subfolders
        self.nifti_folder = self.output_folder / "nifti"
        self.prediction_folder = self.output_folder / "prediction"
        self.stl_folder = self.output_folder / "stl"
        
        for folder in [self.nifti_folder, self.prediction_folder, self.stl_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
    def update_progress(self, message, percentage, output_line=None):
        """Update progress through callback if available"""
        if self.callback:
            self.callback(message, percentage, output_line)

    # def _stream_subprocess_output(self, process, stage_name, base_progress):
    #     """Stream subprocess output and update progress"""
    #     while True:
    #         if process.poll() is not None:
    #             break
                
    #         output_line = process.stdout.readline().strip()
    #         if output_line:
    #             # Extract progress from nnUNet output if possible
    #             if "processing case" in output_line.lower():
    #                 try:
    #                     case_num = int(output_line.split()[2])
    #                     total_cases = int(output_line.split()[4])
    #                     progress = base_progress + (case_num / total_cases) * 20
    #                     self.update_progress(
    #                         f"{stage_name}: Processing case {case_num}/{total_cases}",
    #                         progress,
    #                         output_line
    #                     )
    #                 except (IndexError, ValueError):
    #                     self.update_progress(f"{stage_name}: {output_line}", base_progress, output_line)
    #             else:
    #                 self.update_progress(f"{stage_name}: {output_line}", base_progress, output_line)

    #     # Check for any remaining output
    #     remaining_output = process.stdout.read()
    #     if remaining_output:
    #         for line in remaining_output.splitlines():
    #             if line.strip():
    #                 self.update_progress(f"{stage_name}: {line}", base_progress, line)

    def _stream_subprocess_output(self, process, stage_name, base_progress):
        """Stream subprocess output and update progress"""
        # Regular expression to match percentage at start of line
        percentage_pattern = re.compile(r'^\d+%')
        
        while True:
            if process.poll() is not None:
                break
                
            output_line = process.stdout.readline().strip()
            if output_line:
                # Get raw output line
                self.logger.log_info(f"{stage_name}: {output_line}")
                # Only show lines that start with a percentage
                if percentage_pattern.match(output_line):
                    try:
                        # Extract percentage value
                        percentage = int(output_line.split('%')[0])
                        # Scale the percentage to fit within the stage's progress range
                        progress = base_progress + (percentage / 100) * 20
                        
                        self.update_progress(
                            f"{stage_name}: {output_line}",
                            progress,
                            output_line
                        )
                    except (IndexError, ValueError):
                        pass  # Skip malformed percentage lines
                elif "processing case" in output_line.lower():
                    try:
                        case_num = int(output_line.split()[2])
                        total_cases = int(output_line.split()[4])
                        progress = base_progress + (case_num / total_cases) * 20
                        self.update_progress(
                            f"{stage_name}: Processing case {case_num}/{total_cases}",
                            progress,
                            output_line
                        )
                    except (IndexError, ValueError):
                        pass

        # Check for any remaining output
        remaining_output = process.stdout.read()
        if remaining_output:
            for line in remaining_output.splitlines():
                if line.strip(): 
                    self.logger.log_info(f"{stage_name}: {line}")
                    if percentage_pattern.match(line):
                        self.update_progress(f"{stage_name}: {line}", base_progress, line)

    def run_nnunet_prediction(self):
        """Run nnUNet prediction on the NIfTI file with real-time output"""
        try:
            self.update_progress("Starting nnUNet prediction...", 30)
            
            # Create subprocess with pipe for output
            process = subprocess.Popen(
                [
                    'nnUNetv2_predict',
                    '-i', str(self.nifti_folder),
                    '-o', str(self.prediction_folder),
                    '-d', 'Dataset014_Airways',
                    '-c', '3d_fullres',
                    '-device', 'cpu',
                    '-f', 'all'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )
            
            self.current_subprocess = process
            
            # Stream output in a separate thread
            output_thread = threading.Thread(
                target=self._stream_subprocess_output,
                args=(process, "nnUNet Prediction", 30)
            )
            output_thread.start()
            
            # Wait for process to complete
            process.wait()
            output_thread.join()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode,
                    process.args,
                    process.stdout,
                    process.stderr
                )
            
            # Rename prediction file to add _pred suffix
            pred_files = list(self.prediction_folder.glob('*.nii.gz'))
            if pred_files:
                old_path = pred_files[0]
                new_name = old_path.stem.replace('.nii', '') + '_pred.nii.gz'
                new_path = old_path.parent / new_name
                old_path.rename(new_path)
            
            # Remove nnUNet internal files (*.json)
            for json_file in self.prediction_folder.glob('*.json'):
                json_file.unlink()
            
            self.update_progress("nnUNet prediction completed", 50)
            return str(new_path)
            
        except Exception as e:
            logging.error(f"Error in nnUNet prediction: {e}")
            raise
                
    def cancel_processing(self):
        """Cancel the current processing if any subprocess is running"""
        if self.current_subprocess and self.current_subprocess.poll() is None:
            self.current_subprocess.terminate()
            try:
                self.current_subprocess.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_subprocess.kill()
            return True
        return False

    def convert_dicom_to_nifti(self):
        """Convert DICOM series to NIfTI format with filename as Initials_YYYY-MM-DD"""
        try:
            self.update_progress("Converting DICOM to NIfTI...", 10)
            
            # Read DICOM series
            reader = sitk.ImageSeriesReader()
            dicom_names = reader.GetGDCMSeriesFileNames(str(self.input_folder))
            
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
            
            # Now read the full series
            reader.SetFileNames(dicom_names)
            reader.MetaDataDictionaryArrayUpdateOn()
            image = reader.Execute()
            
            # Check and correct orientation if needed
            direction = image.GetDirection()
            if direction[8] < 0:
                image = sitk.Flip(image, [False, False, True])
            
            # Create filename with initials and formatted date
            filename = f"{initials}_{formatted_date}_0000.nii.gz"
            nifti_path = self.nifti_folder / filename
            
            # Save as NIfTI
            sitk.WriteImage(image, str(nifti_path))
            
            return str(nifti_path)
            
        except Exception as e:
            logging.error(f"Error in DICOM to NIfTI conversion: {e}")
            raise

    def calculate_volume(self, nifti_path):
        """Calculate volume of the segmented airway"""
        try:
            self.update_progress("Calculating airway volume...", 70)
            
            nifti_img = nib.load(nifti_path)
            data = nifti_img.get_fdata()
            voxel_sizes = nifti_img.header.get_zooms()
            
            voxel_volume = np.prod(voxel_sizes)  # mm³
            airway_voxel_count = np.sum(data == 1)  # assuming label 1 for airway
            total_volume_mm3 = airway_voxel_count * voxel_volume
        
            # Save volume calculation
            with open(self.output_folder / "volume_calculation.txt", "w") as f:
                f.write(f"Airway Volume: {total_volume_mm3:.2f} mm³\n")
            
            return total_volume_mm3

        except Exception as e:
            logging.error(f"Error in volume calculation: {e}")
            raise

    def create_stl(self, nifti_path, threshold_value=1, decimate=True, decimate_target_reduction=0.5):
        """Convert segmentation to STL format with advanced smoothing and transformations"""
        try:
            self.update_progress("Creating STL model...", 85)

            # Extract filename without extension
            nifti_filename = Path(nifti_path).stem  # Get filename without extension
            if nifti_filename.endswith("_pred"):
                nifti_filename = nifti_filename.replace("_pred", "_geo")  # Remove _pred suffix if exists
            
            stl_path = self.stl_folder / f"{nifti_filename}.stl"  # Set STL filename
            
            # Load NIfTI file
            reader = vtk.vtkNIFTIImageReader()
            reader.SetFileName(str(nifti_path))
            reader.Update()
            
            # Apply vtkDiscreteFlyingEdges3D
            discrete_flying_edges = vtk.vtkDiscreteFlyingEdges3D()
            discrete_flying_edges.SetInputConnection(reader.GetOutputPort())
            discrete_flying_edges.SetValue(0, threshold_value)
            discrete_flying_edges.Update()
            
            output_polydata = discrete_flying_edges.GetOutput()

            # Apply decimation if requested
            if decimate:
                decimator = vtk.vtkDecimatePro()
                decimator.SetInputData(output_polydata)
                decimator.SetTargetReduction(decimate_target_reduction)
                decimator.PreserveTopologyOn()
                decimator.Update()
                output_polydata = decimator.GetOutput()

            # Apply smoothing
            # smoothing_filter = vtk.vtkSmoothPolyDataFilter()
            # smoothing_filter.SetInputData(output_polydata)
            # smoothing_filter.SetNumberOfIterations(5)
            # smoothing_filter.SetRelaxationFactor(0.05)
            # smoothing_filter.FeatureEdgeSmoothingOff()
            # smoothing_filter.BoundarySmoothingOn()
            # smoothing_filter.Update()
            # output_polydata = smoothing_filter.GetOutput()
            smoothing_filter = vtk.vtkWindowedSincPolyDataFilter()
            smoothing_filter.SetInputData(output_polydata)
            smoothing_filter.SetNumberOfIterations(10)
            smoothing_filter.NonManifoldSmoothingOn()
            smoothing_filter.NormalizeCoordinatesOn()
            smoothing_filter.FeatureEdgeSmoothingOff()
            smoothing_filter.BoundarySmoothingOn()
            smoothing_filter.Update()
            output_polydata = smoothing_filter.GetOutput()


            # Get QForm matrix
            qform_matrix = reader.GetQFormMatrix()

            # Create IJK to RAS transformation
            ijk_to_ras = vtk.vtkMatrix4x4()
            ijk_to_ras.DeepCopy(qform_matrix)

            # Adjust for VTK's coordinate system
            flip_xy = vtk.vtkMatrix4x4()
            flip_xy.SetElement(0, 0, -1)
            flip_xy.SetElement(1, 1, -1)

            vtk.vtkMatrix4x4.Multiply4x4(flip_xy, ijk_to_ras, ijk_to_ras)

            # Create transformation matrix
            transform = vtk.vtkTransform()
            transform.SetMatrix(ijk_to_ras)

            # Apply transformation
            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetInputData(output_polydata)
            transform_filter.SetTransform(transform)
            transform_filter.Update()
            transformed_polydata = transform_filter.GetOutput()

            # Compute normals
            normals = vtk.vtkPolyDataNormals()
            normals.SetInputData(transformed_polydata)
            normals.SetFeatureAngle(60.0)
            normals.ConsistencyOn()
            normals.SplittingOff()
            normals.Update()

            # Write STL file
            stl_writer = vtk.vtkSTLWriter()
            stl_writer.SetFileTypeToBinary()
            stl_writer.SetFileName(str(stl_path))
            stl_writer.SetInputData(normals.GetOutput())
            stl_writer.Write()
            
            return str(stl_path)
            
        except Exception as e:
            self.logger.log_error(f"Error in STL creation: {e}")
            raise

    def process(self):
        """Run the complete processing pipeline"""
        try:
            # Switch to determinate mode before starting actual processing
            self.update_progress(
                "Starting DICOM conversion...",
                0,
                "Beginning processing pipeline"
            )
            
            # Convert DICOM to NIfTI
            nifti_path = self.convert_dicom_to_nifti()
            
            # Run nnUNet prediction
            pred_path = self.run_nnunet_prediction()
            
            # Calculate volume
            volume = self.calculate_volume(pred_path)
            
            # Create STL
            stl_path = self.create_stl(pred_path)
            
            self.update_progress("Processing complete!", 100)
            
            return {
                'nifti_path': nifti_path,
                'prediction_path': pred_path,
                'volume': volume,
                'stl_path': stl_path
            }
            
        except Exception as e:
            self.update_progress(f"Error: {str(e)}", 0)
            raise