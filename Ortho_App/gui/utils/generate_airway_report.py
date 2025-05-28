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
    airway_volume=None,    # from segmentation results
    flow_rate_val=0.0,     # LPM
    airway_resistance=None,
    postprocessed_image_path=None, 
    cfd_pressure_plot_path=None,  
    cfd_velocity_plot_path=None,  
    add_preview_elements=True,
    date_of_report=None,
    additional_images=None,
    include_all_paraview_images=True,
    min_csa=None
):
    """
    Generates a multi-page PDF report showing Patient Info, Summary, Post-processed image,
    and CFD images (pressure + velocity). CFD data (pressure drop, velocities) is 
    automatically retrieved by calling extract_cfd_data(cfd_dir).
    """

    # 1) Extract CFD data from the specified case directory
    cfd_data = extract_cfd_data(cfd_dir) or {}


    # 2) Convert/compute any fields you want
    inlet_velocity = None
    outlet_velocity = None
    pressure_drop_pa = None
    pressure_drop_kpa = None

    if cfd_data:
        inlet_velocity = (cfd_data.get("inlet_velocity") or {}).get("magnitude")
        outlet_velocity = (cfd_data.get("outlet_velocity") or {}).get("magnitude")
        pressure_drop_pa = (cfd_data or {}).get("pressure_drop")
        pressure_drop_kpa = pressure_drop_pa / 1000.0 if pressure_drop_pa else None

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

        # ensure numeric types for formatting
        try:
            flow_rate_val = float(flow_rate_val)
        except (TypeError, ValueError):
            flow_rate_val = 0.0

        try:
            airway_volume = float(airway_volume) if airway_volume is not None else None
        except (TypeError, ValueError):
            airway_volume = None

        try:
            min_csa = float(min_csa) if min_csa is not None else None
        except (TypeError, ValueError):
            min_csa = None

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
        airway_volume_str = f"{airway_volume:.2f}" if airway_volume else "Not calculated"
        min_csa_str = f"{min_csa:.2f}" if min_csa else "Not calculated"
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
        c.drawString(70, y_position - 20, f"Airway Volume: {airway_volume_str}")
        c.drawString(70, y_position - 35, f"Minimum Cross-Sectional Area: {min_csa_str} mm² (rough estimate)") ##TODO: Remove the approximate label when using final min CSA function
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

        if (cfd_pressure_plot_path and os.path.exists(cfd_pressure_plot_path)
                and cfd_velocity_plot_path and os.path.exists(cfd_velocity_plot_path)):

            image_width = 400
            image_height = 250
            x_centered = (width - image_width) / 2

            # 1) Pressure plot
            c.drawImage(
                cfd_pressure_plot_path, 
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
                cfd_velocity_plot_path, 
                x_centered, 
                y_position - image_height,
                width=image_width,
                height=image_height,
                preserveAspectRatio=True,
            )
            c.drawCentredString(x_centered + image_width / 2, y_position - image_height - 10, "Figure 3: Velocity Plot")

            y_position -= (image_height + 30)
        else:
            c.drawString(50, y_position - 30, "CFD pressure/velocity plots not provided or not found.")
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

        # ------ Additional ParaView Images (2 per page) ------
        if include_all_paraview_images and paraview_images:
            imgs_per_page = 2
            page_number = 3
            total_imgs = len(paraview_images)
            total_pages = 2 + (total_imgs + imgs_per_page - 1) // imgs_per_page

            for batch_start in range(0, total_imgs, imgs_per_page):
                batch = paraview_images[batch_start:batch_start + imgs_per_page]
                
                # For each image in this batch, draw it in its half of the page
                for i, img_path in enumerate(batch):
                    if not os.path.exists(img_path):
                        continue

                    # Caption logic (you can reuse yours)
                    img_filename = os.path.basename(img_path)
                    if "p_full" in img_filename:
                        caption = f"Pressure Distribution - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "v_full" in img_filename:
                        caption = f"Velocity Distribution - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "p_cut" in img_filename:
                        caption = f"Pressure Distribution (Section) - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "v_cut" in img_filename:
                        caption = f"Velocity Distribution (Section) - View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "streamline" in img_filename:
                        caption = f"Streamline Visualization - View {img_filename.split('_')[-1].split('.')[0]}"
                    else:
                        caption = f"CFD Visualization: {img_filename}"

                    # Load to compute aspect and size
                    with Image.open(img_path) as img:
                        iw, ih = img.size

                    # Target width is 80% of page width
                    display_w = width * 0.8
                    display_h = display_w * (ih / iw)

                    # If too tall for half‑page, scale down
                    max_half_h = (height - 200) / imgs_per_page
                    if display_h > max_half_h:
                        display_h = max_half_h
                        display_w = display_h * (iw / ih)

                    x_pos = (width - display_w) / 2
                    # y_pos shifts down for the second image
                    y_pos = height - 60 - 1.1*i * (max_half_h + 20) - display_h

                    # Draw the image
                    c.drawImage(
                        img_path,
                        x_pos, y_pos,
                        width=display_w,
                        height=display_h,
                        preserveAspectRatio=True
                    )

                    # Figure number underneath
                    fig_num = batch_start + i + 4
                    c.setFont("Helvetica-Oblique", 10)
                    c.drawCentredString(width / 2, y_pos - 10, f"Figure {fig_num}: {caption}")

                # Preview watermark / page number
                if add_preview_elements:
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
        pdf_path=preview_pdf,
        cfd_dir=paths["cfd_dir"],
        patient_name=self.app.patient_name.get(),
        patient_dob=self.app.dob.get(),
        physician=self.app.patient_doctor_var.get(),
        analysis_type=self.analysis_option.get(),
        airway_volume=self.airway_volume,
        flow_rate_val=self.flow_rate.get(),
        airway_resistance=None,
        postprocessed_image_path=paths["postprocessed_image_path"],
        cfd_pressure_plot_path=paths["cfd_pressure_plot_path"],
        cfd_velocity_plot_path=paths["cfd_velocity_plot_path"],
        add_preview_elements=True, 
        date_of_report=None,
        min_csa=self.min_csa
    )

    if success:
        print("PDF generated successfully!")
    else:
        print("PDF generation failed.")


if __name__ == "__main__":
    main()
