# File: generate_airway_report.py

import os
import time
import glob
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

# Import your CFD extraction logic
from ..utils.get_cfd_data import extract_cfd_data


def generate_airway_report(
    pdf_path,
    cfd_dir,               # The path to your OpenFOAM results folder (e.g. /path/to/CFD_10_0)
    patient_name,
    patient_dob,
    physician,
    analysis_type,         # e.g. "CFD Simulation"
    airway_volume=None,    # user-provided or from segmentation results
    flow_rate_val=0.0,     # LPM
    airway_resistance=None,
    postprocessed_image_path=None, # e.g. "assembly.png"
    cfd_pressure_image_path=None,  # e.g. "some_pressure_plot.png"
    cfd_velocity_image_path=None,  # e.g. "some_velocity_plot.png"
    add_preview_elements=True,
    date_of_report=None,
    additional_images=None,
    include_all_paraview_images=True  # New parameter to include all ParaView images
):
    """
    Generates a multi-page PDF report showing Patient Info, Summary, Post-processed image,
    and CFD images (pressure + velocity). CFD data (pressure drop, velocities) is 
    automatically retrieved by calling extract_cfd_data(cfd_dir).
    
    If include_all_paraview_images is True, it will look for all PNG files in cfd_dir 
    and include them in the report.
    """

    # 1) Extract CFD data from the specified case directory
    cfd_data = extract_cfd_data(cfd_dir)  # returns e.g. {"inlet_pressure", "outlet_pressure", "pressure_drop", "inlet_velocity", ...}

    # 2) Convert/compute any fields you want
    inlet_velocity = None
    outlet_velocity = None
    pressure_drop_pa = None
    pressure_drop_kpa = None

    if cfd_data:
        inlet_velocity  = cfd_data.get("inlet_velocity",  {}).get("magnitude", None)
        outlet_velocity = cfd_data.get("outlet_velocity", {}).get("magnitude", None)

        # If the CFD results included a pressure_drop, convert to Pa + kPa
        if "pressure_drop" in cfd_data and cfd_data["pressure_drop"] is not None:
            pressure_drop_pa = cfd_data["pressure_drop"]  # in Pa
            pressure_drop_kpa = pressure_drop_pa / 1000.0

    # Default the date if not specified
    if not date_of_report:
        date_of_report = time.strftime("%Y-%m-%d %H:%M:%S")
        
    # 3) Find all ParaView images if requested
    paraview_images = []
    if include_all_paraview_images and os.path.exists(cfd_dir):
        # Look for all PNG files in the CFD directory
        png_pattern = os.path.join(cfd_dir, "*.png")
        paraview_images = sorted(glob.glob(png_pattern))
        
        # Categorize images by their names for better organization
        pressure_images = [img for img in paraview_images if "p_" in os.path.basename(img)]
        velocity_images = [img for img in paraview_images if "v_" in os.path.basename(img)]
        streamline_images = [img for img in paraview_images if "streamline" in os.path.basename(img)]
        other_images = [img for img in paraview_images if img not in pressure_images + velocity_images + streamline_images]
        
        # Re-organize in a meaningful order
        paraview_images = pressure_images + velocity_images + streamline_images + other_images

    # Create PDF canvas with letter page size
    try:
        
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        c.setTitle("Upper Airway Analysis Report")

        #
        # ---------------- PAGE 1 ----------------
        #
        # Title Section
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 50, "Upper Airway Analysis Report")
        c.line(50, height - 60, width - 50, height - 60)

        # Header: Analysis Type + Date
        c.setFont("Helvetica", 12)
        analysis_text = f"Analysis Type: {analysis_type}"
        c.drawString(50, height - 80, analysis_text)
        c.drawRightString(width - 50, height - 80, f"Processing Date: {date_of_report}")

        y_position = height - 110

        #
        # 1) Patient Information
        #
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Patient Information:")
        c.setFont("Helvetica", 12)
        c.drawString(70, y_position - 20, f"Name: {patient_name}")
        c.drawString(70, y_position - 35, f"Date of Birth: {patient_dob}")
        c.drawString(70, y_position - 50, f"Physician: {physician}")

        y_position -= 80

        #
        # 2) Summary of Results
        #
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Summary of Results:")
        c.setFont("Helvetica", 12)

        # Prepare strings
        airway_volume_str = f"{airway_volume}" if airway_volume else "Not calculated"
        min_csa_str = f"{min_csa}" if min_csa else "Not calculated"
        press_drop_pa_str = "Not calculated"
        press_drop_kpa_str = "N/A"
        if pressure_drop_pa is not None:
            press_drop_pa_str = f"{pressure_drop_pa:.2f}"
            press_drop_kpa_str = f"{pressure_drop_kpa:.3f}"

        # e.g. "40.0" LPM
        flow_rate_str = f"{flow_rate_val:.1f}"

        if airway_resistance is None:
            airway_resistance = "Not calculated"

        # Draw them
        c.drawString(70, y_position - 20, f"Airway Volume: {airway_volume_str} cm³")
        c.drawString(70, y_position - 35, f"Minimum Cross-Sectional Area: {min_csa_str} cm³")
        c.drawString(70, y_position - 50, f"Pressure Drop: {press_drop_kpa_str} kPa ({press_drop_pa_str} Pa)")
        if inlet_velocity is not None:
            c.drawString(70, y_position - 65, f"Inlet Velocity: {inlet_velocity:.3f} m/s")
        if outlet_velocity is not None:
            c.drawString(70, y_position - 80, f"Outlet Velocity: {outlet_velocity:.3f} m/s")
        y_position -= 105

        #
        # 3) Simulation Conditions
        #
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Simulation Conditions:")
        c.setFont("Helvetica", 12)
        # line_height_offset = 80

        c.setFont("Helvetica-Bold", 12)
        c.drawString(90, y_position - 20, "Parameter")
        c.drawString(250, y_position - 20, "Value")
        c.setFont("Helvetica", 11)

        params = [
            ("Flow Rate",         f"{flow_rate_str} LPM"),
            ("Air Density",       "1.122 kg/m³"),
            ("Kinematic Visc.",   "1.539 x 10^-5 m²/s"),
            ("Initial Velocity",  "0 m/s (Initially at rest)"),
            ("Turbulence Model",  "kOmega"),
        ]
        # Write them in a mini table
        for i, (param, value) in enumerate(params):
            c.drawString(90, y_position - 40 - (i * 15), param)
            c.drawString(250, y_position - 40 - (i * 15), value)

        y_position -= 150

        #
        # Post-processed Geometry Image (if provided)
        #
        if postprocessed_image_path and os.path.exists(postprocessed_image_path):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, "Post-processed Geometry:")
            y_position -= 15
            c.setFont("Helvetica", 12)
            c.drawString(50, y_position, "Below is the model with extracted inlets/outlets.")
            y_position -= 200

            image_x = (width - 300) / 2
            c.drawImage(postprocessed_image_path, image_x, y_position, width=300, height=180)
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(image_x + 100, y_position - 10, "Figure 1: Post-processed Geometry")
            y_position -= 170
        else:
            c.drawString(50, y_position - 30, "Post-processed geometry image not provided/found.")
            y_position -= 70

        # Preview watermark if requested
        if add_preview_elements:
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(50, 30, "(Preview) Page 1 of 2")
            c.setFillColorRGB(0, 0, 0)

        c.showPage()

        #
        # -------------- PAGE 2 --------------
        #
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 50, "CFD Simulation Results")

        y_position = height - 90
        c.setFont("Helvetica", 12)
        c.drawString(50, y_position, "Airflow velocity and pressure contours shown below.")
        y_position -= 40

        # Title for the CFD images
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "CFD Plots (Pressure & Velocity):")
        y_position -= 20
        c.setFont("Helvetica", 12)

        if (cfd_pressure_image_path and os.path.exists(cfd_pressure_image_path)
                and cfd_velocity_image_path and os.path.exists(cfd_velocity_image_path)):

            image_width = 400
            image_height = 250
            x_centered = (width - image_width) / 2

            # 1) Pressure plot
            c.drawImage(
                cfd_pressure_image_path, 
                x_centered, 
                y_position - image_height, 
                width=image_width, 
                height=image_height,
                preserveAspectRatio=True,
            )
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(x_centered + image_width / 2, y_position - image_height - 10, "Figure 2: Pressure Plot")

            y_position -= (image_height + 40)  # space below figure

            # 2) Velocity plot
            c.drawImage(
                cfd_velocity_image_path, 
                x_centered, 
                y_position - image_height,
                width=image_width,
                height=image_height,
                preserveAspectRatio=True,
            )
            c.drawCentredString(x_centered + image_width / 2, y_position - image_height - 10, "Figure 3: Velocity Plot")

            y_position -= (image_height + 30)
        else:
            c.drawString(50, y_position - 30, "CFD pressure/velocity images not provided or not found.")
            y_position -= 60

        # If preview watermark is desired
        if add_preview_elements:
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            page_number = 2
            if include_all_paraview_images and paraview_images:
                total_pages = 2 + len(paraview_images)
            elif additional_images:
                total_pages = 2 + len(additional_images)
            else:
                total_pages = 2
            c.drawString(50, 30, f"(Preview) Page {page_number} of {total_pages}")
            c.setFillColorRGB(0, 0, 0)

        c.showPage()

        # ------ Additional ParaView Images (Each on New Page) ------
        page_number = 3
        
        if include_all_paraview_images and paraview_images:
            for idx, img_path in enumerate(paraview_images):
                if os.path.exists(img_path):
                    # Begin a new page for each image
                    
                    # Get image filename for the caption
                    img_filename = os.path.basename(img_path)
                    
                    # Generate appropriate caption based on filename
                    if "p_full" in img_filename:
                        caption = f"Pressure Distribution - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "v_full" in img_filename:
                        caption = f"Velocity Distribution - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "p_cut" in img_filename:
                        caption = f"Pressure Distribution (Section View) - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "v_cut" in img_filename:
                        caption = f"Velocity Distribution (Section View) - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "streamline" in img_filename:
                        caption = f"Streamline Visualization - View {img_filename.split('_')[-1].split('.')[0]}"
                    else:
                        caption = f"CFD Visualization: {img_filename}"
                    
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(width / 2, height - 50, caption)
                    
                    # Draw the image, preserving aspect ratio
                    try:
                        # Get image dimensions to calculate proper display size
                        img = Image.open(img_path)
                        img_width, img_height = img.size
                        img.close()
                        
                        # Calculate appropriate display dimensions
                        display_width = 480
                        display_height = int(display_width * img_height / img_width)
                        
                        # Ensure it fits on the page
                        if display_height > 600:
                            display_height = 600
                            display_width = int(display_height * img_width / img_height)
                        
                        # Center the image on the page
                        x_pos = (width - display_width) / 2
                        y_pos = height - 150 - display_height
                        
                        c.drawImage(
                            img_path,
                            x_pos, y_pos,
                            width=display_width,
                            height=display_height,
                            preserveAspectRatio=True
                        )
                        
                        # Add a helpful caption below the image
                        c.setFont("Helvetica-Oblique", 10)
                        c.drawCentredString(width/2, y_pos - 15, f"Figure {idx + 3}: {caption}")
                        
                    except Exception as e:
                        c.setFont("Helvetica", 12)
                        c.drawString(50, height - 100, f"Failed to load image {img_path}: {str(e)}")
                    
                    # Add page number
                    if add_preview_elements:
                        total_pages = 2 + len(paraview_images)
                        c.setFont("Helvetica", 10)
                        c.setFillColorRGB(0.5, 0.5, 0.5)
                        c.drawString(50, 30, f"(Preview) Page {page_number} of {total_pages}")
                        c.setFillColorRGB(0, 0, 0)
                        page_number += 1
                    
                    c.showPage()

        # ------ Optional Additional User-Provided Images (Each on New Page) ------
        if additional_images:
            for idx, img_path in enumerate(additional_images, start=1):
                if os.path.exists(img_path):
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(width / 2, height - 50, f"Additional Image {idx}")
                    try:
                        c.drawImage(
                            img_path,
                            100, 150,
                            width=400,
                            height=300,
                            preserveAspectRatio=True
                        )
                        
                        # Add caption
                        c.setFont("Helvetica-Oblique", 10)
                        img_filename = os.path.basename(img_path)
                        c.drawCentredString(width/2, 140, f"Figure: {img_filename}")
                        
                    except Exception as e:
                        c.setFont("Helvetica", 12)
                        c.drawString(50, height - 100, f"Failed to load image {img_path}: {str(e)}")
                    
                    # Add page number if preview is enabled
                    if add_preview_elements:
                        total_pages = page_number - 1 + len(additional_images)
                        c.setFont("Helvetica", 10)
                        c.setFillColorRGB(0.5, 0.5, 0.5)
                        c.drawString(50, 30, f"(Preview) Page {page_number} of {total_pages}")
                        c.setFillColorRGB(0, 0, 0)
                        page_number += 1
                        
                    c.showPage()

        c.save()

        print(f"Report saved to: {pdf_path}")
        return True

    except Exception as exc:
        print(f"Error generating PDF: {exc}")
        return False


def main():
    """
    Test the function by running:
      python generate_airway_report.py

    Adjust these sample variables to point to a real CFD folder and real images.
    """
    # Example usage:
    success = generate_airway_report(
        pdf_path="./example_airway_report.pdf",
        cfd_dir="/path/to/CFD_40_0",  # Where your case.foam + triSurface exist
        patient_name="Anonymous Patient",
        patient_dob="1999-05-10",
        physician="Dr. Lagravere",
        analysis_type="CFD Simulation",
        airway_volume=68.53,
        flow_rate_val=40.0,  # LPM
        airway_resistance=None,  # or a numeric value
        postprocessed_image_path="./postproc.png",
        cfd_pressure_image_path="./p_plot.png",
        cfd_velocity_image_path="./u_plot.png",
        add_preview_elements=True,
        include_all_paraview_images=True  # Set to True to include all ParaView images
    )

    if success:
        print("PDF generated successfully!")
    else:
        print("PDF generation failed.")


if __name__ == "__main__":
    main()
