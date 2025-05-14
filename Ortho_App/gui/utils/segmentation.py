import os
import subprocess
import threading
import SimpleITK as sitk
import nibabel as nib
import numpy as np
import vtk
from pathlib import Path
import re
from gui.utils.basic_utils import AppLogger
import time
from scipy.spatial import ConvexHull

class AirwaySegmentator:
    def __init__(self, input_file=None, input_folder=None, output_folder=None, callback=None, input_type="dicom"):
        """
        Initialize the airway processing pipeline
        
        Args:
            input_folder (str): Path to folder containing DICOM files
            output_folder (str): Path to output folder for all processing steps
            callback (callable): Optional callback function for progress updates
        """
        self.input_file = Path(input_file) if input_file else None
        self.input_folder = Path(input_folder) if input_folder else None
        self.output_folder = Path(output_folder)
        self.callback = callback
        self.input_type = input_type.lower()
        self.current_subprocess = None
        self.logger = AppLogger()

        # For cancelling the procedure
        self.cancel_event = threading.Event()
        
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

    def _stream_subprocess_output(self, process, stage_name, base_progress):
        """Stream subprocess output and update progress"""
        # Regular expression to match percentage at start of line
        percentage_pattern = re.compile(r'^\d+%')
        
        while True:
            # bail out if user hit cancel
            if self.cancel_event.is_set():
                break
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
            self.update_progress("Starting nnUNet prediction...", 30, "Starting nnUNet prediction...")
            
            # Create subprocess with pipe for output
            process = subprocess.Popen(
                [
                    'nnUNetv2_predict',
                    '-i', str(self.nifti_folder),
                    '-o', str(self.prediction_folder),
                    '-d', 'Dataset014_Airways',
                    '-c', '3d_fullres_bs4',
                    '-device', 'cuda',
                    '-f', 'all',
                    '-step_size', '0.7', # Increased from default 0.5
                    '--disable_tta',  # TODO: Disable for 5x faster inference but segmentation is less accurate
                    '-npp', '8',  # Increase preprocessing threads (up from default 2)
                    '-nps', '8',  # Increase segmentation export threads (up from default 2)
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
            pred_folder = Path(self.prediction_folder)
            for old_path in pred_folder.glob('*.nii.gz'):
                # remove .gz then .nii
                noext = old_path.with_suffix("").with_suffix("")   # → Path(".../case")
                new_name = f"{noext.name}_pred.nii.gz"
                new_path = noext.parent / new_name

                if new_path.exists() and not new_path.samefile(old_path):
                    new_path.unlink()

                old_path.rename(new_path)
                # return the _new_ path
                nifti_path = new_path
            
            # Remove nnUNet internal files (*.json)
            for json_file in self.prediction_folder.glob('*.json'):
                json_file.unlink()
            
            self.update_progress("nnUNet prediction completed", 50, "nnUNet prediction completed")
            return str(nifti_path)

        except Exception as e:
            self.logger.log_error(f"Error in nnUNet prediction: {e}")
            raise
                
    def cancel_processing(self):
        """Cancel the current processing if any subprocess is running"""
        # Log that cancellation was requested
        self.logger.log_info("Cancellation requested by user")
        
        # tell Python loops to stop
        self.cancel_event.set()

        # kill any live subprocess
        if self.current_subprocess and self.current_subprocess.poll() is None:
            self.logger.log_info("Terminating subprocess...")
            self.current_subprocess.terminate()
            try:
                self.current_subprocess.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.log_info("Subprocess didn't terminate, killing it...")
                self.current_subprocess.kill()
        
        self.logger.log_info("Cancellation complete")
        return True

    def convert_dicom_to_nifti(self):
        """
        Convert a single DICOM series to NIfTI format.
        The output file is named based on the input folder name (e.g. ABC.nii.gz).
        """
        try:
            self.logger.log_info("Converting DICOM to NIfTI...")
            reader = sitk.ImageSeriesReader()
            dicom_names = reader.GetGDCMSeriesFileNames(str(self.input_folder))
            if not dicom_names:
                raise ValueError("No DICOM series found in input directory")
            reader.SetFileNames(dicom_names)
            image = reader.Execute()
            # Optional: adjust orientation if needed.
            if image.GetDirection()[8] < 0:
                image = sitk.Flip(image, [False, False, True])
            # Use the input folder’s name to generate the output filename.
            folder_name = self.input_folder.stem
            output_file = self.nifti_folder / f"{folder_name}_0000.nii.gz"
            sitk.WriteImage(image, str(output_file))
            self.logger.log_info(f"NIfTI file saved: {output_file}")
            return str(output_file)
        except Exception as e:
            self.logger.log_error(f"Error in DICOM to NIfTI conversion: {e}")
            raise

    def calculate_volume(self, nifti_path):
        """Calculate volume of the segmented airway"""
        try:
            
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
            self.logger.log_error(f"Error in volume calculation: {e}")
            raise

    def create_stl(self, nifti_path, threshold_value=1, decimate=True, decimate_target_reduction=0.10):
        """Convert segmentation to STL format with advanced smoothing and transformations"""
        try:
            self.update_progress("Calculating airway volume and creating 3D model...", 85, "Calculating airway volume and creating 3D model...")

            # Extract filename without both extensions (.nii.gz)
            nifti_path = Path(nifti_path)
            nifti_filename = nifti_path.stem  # Removes the .gz
            if nifti_filename.endswith('.nii'):
                nifti_filename = Path(nifti_filename).stem  # Removes the .nii

            # Then handle the _pred suffix
            if nifti_filename.endswith("_pred"):
                nifti_filename = nifti_filename.replace("_pred", "_geo")  # Remove _pred suffix if exists
            
            stl_path = self.stl_folder / f"{nifti_filename}.stl"  # Set STL filename
            stl_path = stl_path.resolve()  # Ensures it's absolute
            
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

            # First clean the mesh to remove duplicate points
            cleaner = vtk.vtkCleanPolyData()
            cleaner.SetInputData(output_polydata)
            cleaner.SetTolerance(0.0001)
            cleaner.ConvertLinesToPointsOff()
            cleaner.ConvertPolysToLinesOff()
            cleaner.ConvertStripsToPolysOff()
            cleaner.PointMergingOn()
            cleaner.Update()
            output_polydata = cleaner.GetOutput()

            # # Improve triangle quality - deemed not necessary because mesh is dense enough to avoid too much tirangle distortion
            # triangle_filter = vtk.vtkTriangleFilter()
            # triangle_filter.SetInputData(output_polydata)
            # triangle_filter.PassLinesOff()
            # triangle_filter.PassVertsOff()
            # triangle_filter.Update()
            # output_polydata = triangle_filter.GetOutput()

            # Ensure model is completely closed and manifold
            connected_filter = vtk.vtkPolyDataConnectivityFilter()
            connected_filter.SetInputData(output_polydata)
            connected_filter.SetExtractionModeToLargestRegion()
            connected_filter.Update()
            output_polydata = connected_filter.GetOutput()

            # Apply smoothing
            smoothing_filter = vtk.vtkSmoothPolyDataFilter()
            smoothing_filter.SetInputData(output_polydata)
            smoothing_filter.SetNumberOfIterations(25)
            smoothing_filter.SetRelaxationFactor(0.2)  
            smoothing_filter.FeatureEdgeSmoothingOff()
            smoothing_filter.BoundarySmoothingOn()
            smoothing_filter.Update()
            output_polydata = smoothing_filter.GetOutput()

            # # Apply decimation? Not worth it because the triangles get distorted
            # decimator = vtk.vtkDecimatePro()
            # decimator.SetInputData(output_polydata)
            # decimator.SetTargetReduction(decimate_target_reduction)
            # decimator.PreserveTopologyOn()
            # decimator.BoundaryVertexDeletionOff()
            # decimator.SplittingOff()
            # decimator.Update()
            # output_polydata = decimator.GetOutput()
            
            # Apply Windowed Sinc smoothing with conservative settings
            smoother = vtk.vtkWindowedSincPolyDataFilter()
            smoother.SetInputData(output_polydata)
            smoother.SetNumberOfIterations(20)
            smoother.FeatureEdgeSmoothingOff()
            smoother.SetFeatureAngle(60)
            smoother.SetPassBand(0.2)
            smoother.SetBoundarySmoothing(True)
            smoother.Update()
            output_polydata = smoother.GetOutput()

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

            # Extract largest region again after transformation
            connected_filter = vtk.vtkPolyDataConnectivityFilter()
            connected_filter.SetInputData(transformed_polydata)
            connected_filter.SetExtractionModeToLargestRegion()
            connected_filter.Update()
            clean_polydata = connected_filter.GetOutput()

            # Compute normals 
            normals = vtk.vtkPolyDataNormals()
            normals.SetInputData(clean_polydata)
            normals.SetFeatureAngle(60.0)
            normals.ConsistencyOn()
            normals.SplittingOff()
            normals.AutoOrientNormalsOn()
            normals.Update()
            output_polydata = normals.GetOutput()
            
            # Final clean to ensure high quality
            final_cleaner = vtk.vtkCleanPolyData()
            final_cleaner.SetInputData(output_polydata)
            final_cleaner.Update()

            # Write STL file
            stl_writer = vtk.vtkSTLWriter()
            stl_writer.SetFileTypeToBinary()
            stl_writer.SetFileName(str(stl_path))
            stl_writer.SetInputData(output_polydata)
            stl_writer.Write()

            # Generate STL Preview
            preview_path = self.generate_stl_preview(str(stl_path))

            # Minimum cross section computation
            min_csa = self.approx_min_cross_section_area(clean_polydata, num_slices=50)  ## TODO: Change approx_min_cross_section_area function to the final version
            with open(self.output_folder/"min_csa.txt", "w") as f:
                f.write(f"Min CSA (approx): {min_csa:.2f} mm²\n")

            return {'stl_path': str(stl_path), 'preview_path': preview_path, 'min_csa': min_csa}
            
        except Exception as e:
            self.logger.log_error(f"Error in STL creation: {e}")
            raise

    def process(self):
        """Run the complete processing pipeline for DICOM or NIfTI input"""
        try:
            if self.input_type == "nifti":
                # Use the provided NIfTI file directly
                nifti_path = Path(self.input_file)
                self.update_progress("Using provided NIfTI file...", 10, "Using provided NIfTI file...")
                # Copy NIfTI file into expected folder
                target_path = self.nifti_folder / (nifti_path.stem + ".nii.gz")
                target_path.write_bytes(nifti_path.read_bytes())
                nifti_path = target_path
            else:
                # DICOM input — convert to NIfTI
                self.update_progress("Converting DICOM to NIfTI...", 10, "Converting DICOM to NIfTI...")
                nifti_path = self.convert_dicom_to_nifti()
                if self.cancel_event.is_set():
                   raise RuntimeError("User cancelled during DICOM→NIfTI")

            # Run nnUNet prediction
            pred_path = self.run_nnunet_prediction()
            if self.cancel_event.is_set():
                   raise RuntimeError("User cancelled during nnUNet prediction")

            # Calculate volume
            volume = self.calculate_volume(pred_path)
            if self.cancel_event.is_set():
                   raise RuntimeError("User cancelled during volume computation")

            # Create STL
            stl_result = self.create_stl(pred_path)
            if self.cancel_event.is_set():
                   raise RuntimeError("User cancelled during STL creation")

            return {
                'nifti_path': str(nifti_path),
                'prediction_path': pred_path,
                'volume': volume,
                'stl_path': stl_result  # Dict with 'stl_path', 'preview_path' adn min_csa
            }

        except Exception as e:
            self.update_progress(f"Error: {str(e)}", 0)
            raise


    def generate_stl_preview(self, stl_path, view_type="perspective"):
        """
        Generate a 2D preview image of an STL model with enhanced lighting and rendering.
        
        Args:
            stl_path (str): Path to the STL file
            view_type (str): View type - "perspective" (default), "front", "side", "anatomical_front", etc.
            
        Returns:
            str: Path to the generated PNG image, or None if failed
        """
        try:
            preview_path = str(Path(stl_path).with_suffix(".png"))
            self.logger.log_info(f"Generating STL preview for: {stl_path}")
            
            # Read STL file
            reader = vtk.vtkSTLReader()
            reader.SetFileName(stl_path)
            reader.Update()
            
            # Create mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            
            # Create actor with optimized properties
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
            # Set light blue-gray color that works well for airway models
            actor.GetProperty().SetColor(0.7, 0.7, 0.9)
            
            # Optimize material properties for medical visualization
            actor.GetProperty().SetAmbient(0.4)
            actor.GetProperty().SetDiffuse(0.8)
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(15)
            
            # Create renderer with white background
            renderer = vtk.vtkRenderer()
            renderer.AddActor(actor)
            renderer.SetBackground(1, 1, 1)  # Pure white background
            renderer.SetTwoSidedLighting(True)  # Illuminate both sides of surfaces
            
            # Get model bounds and center for camera and light positioning
            bounds = actor.GetBounds()
            center = [(bounds[0] + bounds[1])/2, (bounds[2] + bounds[3])/2, (bounds[4] + bounds[5])/2]
            
            # Add multiple lights for better illumination
            
            # Main light from front
            light1 = vtk.vtkLight()
            light1.SetPosition(center[0], center[1] - (bounds[3] - bounds[2]) * 3, center[2])
            light1.SetFocalPoint(center[0], center[1], center[2])
            light1.SetIntensity(0.8)
            light1.SetLightTypeToSceneLight()
            renderer.AddLight(light1)
            
            # Secondary light from top-right
            light2 = vtk.vtkLight()
            light2.SetPosition(
                center[0] + (bounds[1] - bounds[0]), 
                center[1], 
                center[2] + (bounds[5] - bounds[4])
            )
            light2.SetFocalPoint(center[0], center[1], center[2])
            light2.SetIntensity(0.6)
            light2.SetLightTypeToSceneLight()
            light2.SetColor(0.9, 0.9, 1.0)  # Slightly blue tint
            renderer.AddLight(light2)
            
            # Fill light from left
            light3 = vtk.vtkLight()
            light3.SetPosition(
                center[0] - (bounds[1] - bounds[0]) * 2, 
                center[1], 
                center[2]
            )
            light3.SetFocalPoint(center[0], center[1], center[2])
            light3.SetIntensity(0.4)
            light3.SetLightTypeToSceneLight()
            renderer.AddLight(light3)
            
            # Set up the render window
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)  # Ensure no window appears
            render_window.AddRenderer(renderer)
            render_window.SetSize(800, 600)
            
            # Configure camera based on the desired view
            camera = renderer.GetActiveCamera()
            
            if view_type == "front":
                # Standard front view
                camera.SetPosition(bounds[1] + (bounds[1] - bounds[0]) * 2, center[1], center[2])
                camera.SetFocalPoint(center[0], center[1], center[2])
                camera.SetViewUp(0, 0, 1)
                
            elif view_type == "perspective" or view_type not in ["front", "anatomical_front", "side", "top"]:
                # 3/4 perspective view - works well for airway models
                camera.SetPosition(
                    center[0] - (bounds[1] - bounds[0])*1.2,
                    center[1] - (bounds[3] + bounds[2]) * 1.5,
                    center[2] - (bounds[5] - bounds[4])
                )
                camera.SetFocalPoint(center[0], center[1], center[2])
                camera.SetViewUp(0, 0, 1)
            
            # Reset camera to fit model properly
            # Zoom in by 20%
            camera.Zoom(1.2)
            renderer.ResetCamera()
            
            # Use parallel projection for orthographic views
            if view_type != "perspective":
                camera.ParallelProjectionOn()
                camera.SetParallelScale((bounds[3] - bounds[2]) * 0.6)
            
            # Reset clipping planes
            renderer.ResetCameraClippingRange()
            
            # Render the scene
            render_window.Render()
            
            # Capture as PNG with solid white background
            window_to_image = vtk.vtkWindowToImageFilter()
            window_to_image.SetInput(render_window)
            window_to_image.SetScale(2)  # High resolution
            window_to_image.SetInputBufferTypeToRGB()  # RGB instead of RGBA (no alpha channel)
            window_to_image.ReadFrontBufferOff()  # Read from back buffer
            window_to_image.Update()
            
            # Write PNG file
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(preview_path)
            writer.SetInputConnection(window_to_image.GetOutputPort())
            writer.Write()
            
            self.logger.log_info(f"STL preview saved to: {preview_path}")
            return preview_path
            
        except Exception as e:
            self.logger.log_error(f"Error generating STL preview: {str(e)}")
            return None
    
    def approx_min_cross_section_area(self, polydata, num_slices=50):
        """
        Placeholder: approximate the minimum cross‐sectional area in Z by
        slicing the mesh into `num_slices` and taking the smallest bounding‑box.
        """
        # 1) grab all mesh vertices
        n_pts = polydata.GetNumberOfPoints()
        pts = np.array([polydata.GetPoint(i) for i in range(n_pts)])
        if pts.size == 0:
            return 0.0

        z = pts[:, 2]
        zmin, zmax = z.min(), z.max()
        if zmax <= zmin:
            return 0.0

        edges = np.linspace(zmin, zmax, num_slices + 1)
        min_area = float('inf')

        for i in range(num_slices):
            mask = (z >= edges[i]) & (z < edges[i+1])
            slice_xy = pts[mask][:, :2]
            if slice_xy.shape[0] < 3:
                continue

            # --- Simple bounding‐box area --- 
            dx = np.ptp(slice_xy[:, 0])   # max(slice_xy[:,0]) - min(...)
            dy = np.ptp(slice_xy[:, 1])
            area = dx * dy

            min_area = min(min_area, area)

        return min_area if min_area != float('inf') else 0.0
    