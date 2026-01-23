# File: generate_airway_report.py

import os
import time
import glob
import math
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

# Import your CFD extraction logic
from ..utils.get_cfd_data import extract_cfd_data_from_files


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
    include_all_paraview_images=True,
    min_csa=None
):
    """
    Generates a multi-page PDF report showing Patient Info, Summary, Post-processed image,
    and CFD images (pressure + velocity). CFD data (pressure drop, velocities) is 
    automatically retrieved by calling extract_cfd_data_from_files(cfd_dir).
    """
    def _safe_text(value, default=""):
        if value is None:
            return default
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def _get_latest_time_dir(base_dir):
        try:
            entries = [
                d for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d))
            ]
        except OSError:
            return None
        time_dirs = []
        for d in entries:
            try:
                time_dirs.append((float(d), d))
            except ValueError:
                continue
        if not time_dirs:
            return None
        return os.path.join(base_dir, max(time_dirs, key=lambda x: x[0])[1])

    def _read_slice_averages(case_dir):
        post_dir = os.path.join(case_dir, "postProcessing")
        if not os.path.isdir(post_dir):
            return []
        slices = []
        for entry in os.listdir(post_dir):
            if not entry.startswith("avgsurf"):
                continue
            suffix = entry.replace("avgsurf", "", 1)
            if not suffix.isdigit():
                continue
            slice_idx = int(suffix)
            time_dir = _get_latest_time_dir(os.path.join(post_dir, entry))
            if not time_dir:
                continue
            data_path = os.path.join(time_dir, "surfaceFieldValue.dat")
            if not os.path.isfile(data_path):
                continue
            try:
                with open(data_path, "r") as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except OSError:
                continue
            if not lines:
                continue
            last = lines[-1]
            parts = last.split()
            if len(parts) < 2:
                continue
            try:
                p_avg = float(parts[1])
            except ValueError:
                continue
            u_mag = None
            match = re.search(r"\(([^)]+)\)", last)
            if match:
                try:
                    comps = [float(v) for v in match.group(1).split()]
                    if len(comps) >= 3:
                        u_mag = math.sqrt(comps[0] ** 2 + comps[1] ** 2 + comps[2] ** 2)
                except ValueError:
                    u_mag = None
            slices.append((slice_idx, p_avg, u_mag))
        slices.sort(key=lambda s: s[0])
        return slices

    def _draw_line_plot(c, x, y, w, h, xs, ys, caption, y_label, x_label):
        if not xs or not ys:
            c.setFont("Helvetica", 9)
            c.drawCentredString(x + w / 2, y + h / 2, "No data")
            return
        min_y = min(ys)
        max_y = max(ys)
        if min_y == max_y:
            min_y -= 1.0
            max_y += 1.0
        min_x = min(xs)
        max_x = max(xs)
        if min_x == max_x:
            min_x -= 1.0
            max_x += 1.0
        plot_left = x + 50
        plot_right = x + w - 10
        plot_bottom = y + 28
        plot_top = y + h - 22
        c.line(plot_left, plot_bottom, plot_left, plot_top)
        c.line(plot_left, plot_bottom, plot_right, plot_bottom)
        pts = []
        for xi, yi in zip(xs, ys):
            px = plot_left + (xi - min_x) / (max_x - min_x) * (plot_right - plot_left)
            py = plot_bottom + (yi - min_y) / (max_y - min_y) * (plot_top - plot_bottom)
            pts.append((px, py))
        c.setStrokeColorRGB(0.1, 0.4, 0.8)
        for i in range(1, len(pts)):
            c.line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
        c.setStrokeColorRGB(0, 0, 0)
        c.setFont("Helvetica", 7)
        for i in range(5):
            y_val = min_y + (max_y - min_y) * i / 4
            y_pos = plot_bottom + (y_val - min_y) / (max_y - min_y) * (plot_top - plot_bottom)
            c.line(plot_left - 3, y_pos, plot_left, y_pos)
            c.drawRightString(plot_left - 5, y_pos - 2, f"{y_val:.2f}")
        for xi in xs:
            x_pos = plot_left + (xi - min_x) / (max_x - min_x) * (plot_right - plot_left)
            c.line(x_pos, plot_bottom, x_pos, plot_bottom - 3)
            c.drawCentredString(x_pos, y + 14, f"{xi:g}")
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + w / 2, y + 6, x_label)
        c.saveState()
        c.translate(x + 14, y + h / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, y_label)
        c.restoreState()
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(x + w / 2, y - 10, caption)

    # 1) Extract CFD data from the specified case directory
    cfd_data = extract_cfd_data_from_files(cfd_dir) or {}

    # 2) Convert/compute any fields you want
    inlet_velocity = None
    outlet_velocity = None
    pressure_drop_pa = None
    pressure_drop_kpa = None

    if cfd_data:
        inlet_velocity = cfd_data.get("inlet_velocity")
        outlet_velocity = cfd_data.get("outlet_velocity")
        pressure_drop_pa = cfd_data.get("pressure_drop")
        pressure_drop_kpa = pressure_drop_pa / 1000.0 if pressure_drop_pa is not None else None

        # Compute airway resistance if pressure drop and flow rate are valid
        airway_resistance = None
        try:
            flow_rate_Lps = float(flow_rate_val) / 60.0  # Convert LPM to L/s
            if flow_rate_Lps > 0 and pressure_drop_pa is not None:
                airway_resistance = (pressure_drop_pa / flow_rate_Lps) / 98.0665  # Convert Pa/L/s to cmH2O/L/s
        except (TypeError, ValueError, ZeroDivisionError):
            airway_resistance = None

    # Default the date if not specified
    if not date_of_report:
        date_of_report = time.strftime("%Y-%m-%d %H:%M:%S")

    # 3) Find all ParaView images if requested
    paraview_images = []
    if include_all_paraview_images and os.path.exists(cfd_dir):
        # Look for specific image patterns only
        patterns = [
            "p_cut_*.png",      # Pressure cut planes
            "p_full_*.png",     # Pressure surface views
            "v_cut_*.png",      # Velocity cut planes
            "v_full_*.png",     # Velocity surface views
            "v_streamlines*.png"   # Streamline visualizations
        ]

        for pattern in patterns:
            pattern_path = os.path.join(cfd_dir, pattern)
            paraview_images.extend(sorted(glob.glob(pattern_path)))

        # Remove duplicates and already-used images
        excluded_images = {cfd_pressure_plot_path, cfd_velocity_plot_path, postprocessed_image_path}
        paraview_images = [img for img in paraview_images if img not in excluded_images]

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
            min_csa = float(min_csa) if min_csa is not None else None
        except (TypeError, ValueError):
            min_csa = None

        try:
            airway_volume = float(airway_volume) if airway_volume is not None else None
        except (TypeError, ValueError):
            airway_volume = None

        #
        # ---------------- PAGE 1 ----------------
        #
        # Title Section
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 50, "Upper Airway Analysis Report")
        c.line(50, height - 60, width - 50, height - 60)

        # Header: Analysis Type + Date
        c.setFont("Helvetica", 12)
        analysis_text = f"Analysis Type: {_safe_text(analysis_type, 'CFD Simulation')}"
        c.drawString(50, height - 80, analysis_text)
        c.drawRightString(width - 50, height - 80, f"Processing Date: {_safe_text(date_of_report)}")

        y_position = height - 110

        #
        # 1) Patient Information
        #
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Patient Information:")
        c.setFont("Helvetica", 12)
        c.drawString(70, y_position - 20, f"Name: {_safe_text(patient_name)}")
        c.drawString(70, y_position - 35, f"Date of Birth: {_safe_text(patient_dob)}")
        c.drawString(70, y_position - 50, f"Physician: {_safe_text(physician)}")

        y_position -= 80

        #
        # 2) Summary of Results
        #
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Summary of Results:")
        c.setFont("Helvetica", 12)

        # Prepare strings
        airway_volume_str = f"{airway_volume:.2f}" if airway_volume is not None else "Not calculated"
        min_csa_str = f"{min_csa:.2f}" if min_csa is not None else "Not calculated"
        press_drop_pa_str = "Not calculated"
        press_drop_kpa_str = "N/A"
        if pressure_drop_pa is not None:
            press_drop_pa_str = f"{pressure_drop_pa:.2f}"
            press_drop_kpa_str = f"{pressure_drop_kpa:.3f}"

        # e.g. "40.0" LPM
        flow_rate_str = f"{flow_rate_val:.1f}"

        airway_resistance_str = f"{airway_resistance:.2f}" if airway_resistance is not None else "Not calculated"

        # Draw them
        c.drawString(70, y_position - 20, f"Airway volume: {airway_volume_str} mm³")
        c.drawString(70, y_position - 35, f"Minimum Cross-Sectional Area: {min_csa_str} mm²")
        c.drawString(70, y_position - 50, f"Pressure Drop: {press_drop_pa_str} Pa ({press_drop_kpa_str} kPa)")
        if inlet_velocity is not None:
            c.drawString(70, y_position - 65, f"Inlet Velocity: {inlet_velocity:.3f} m/s")
        else:
            c.drawString(70, y_position - 65, "Inlet Velocity: Not available")
        if outlet_velocity is not None:
            c.drawString(70, y_position - 80, f"Outlet Velocity: {outlet_velocity:.3f} m/s")
        else:
            c.drawString(70, y_position - 80, f"Outlet Velocity: Not available")
        c.drawString(70, y_position - 95, f"Airway Resistance: {airway_resistance_str} cmH2O / L / s")

        # Next section
        y_position -= 120
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
        c.drawString(50, y_position, "Airflow velocity and pressure summary plots shown below.")
        y_position -= 40

        slice_avgs = _read_slice_averages(cfd_dir)

        if slice_avgs:
            slice_nums = [s[0] for s in slice_avgs]
            p_vals = [s[1] for s in slice_avgs]
            u_pairs = [(s[0], s[2]) for s in slice_avgs if s[2] is not None]
            u_xs = [p[0] for p in u_pairs]
            u_vals = [p[1] for p in u_pairs]
            plot_width = 470
            plot_height = 200
            x_left = 60
            y_plot = y_position - plot_height - 10
            _draw_line_plot(
                c,
                x_left,
                y_plot,
                plot_width,
                plot_height,
                slice_nums,
                p_vals,
                "Figure 2: Average Pressure by Slice",
                "Pressure (Pa)",
                "Slice Number"
            )
            if u_vals:
                y_plot = y_plot - plot_height - 80
                _draw_line_plot(
                    c,
                    x_left,
                    y_plot,
                    plot_width,
                    plot_height,
                    u_xs,
                    u_vals,
                    "Figure 3: Average Velocity by Slice",
                    "Air Velocity (m/s)",
                    "Slice Number"
                )
            y_position = y_plot - 40
        else:
            c.drawString(50, y_position - 30, "CFD slice-average plots not provided or not found.")
            y_position -= 60

        # If preview watermark is desired
        if add_preview_elements:
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            page_number = 2
            if include_all_paraview_images and paraview_images:
                total_pages = 2 + len(paraview_images)
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

                    # Caption logic
                    img_filename = os.path.basename(img_path)
                    if "p_full" in img_filename:
                        caption = f"Pressure Distribution Surface View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "v_full" in img_filename:
                        caption = f"Velocity Distribution Surface View {img_filename.split('_')[-1].split('.')[0]}"
                    elif "p_cut" in img_filename:
                        caption = f"Pressure Distribution (Section {img_filename.split('_')[-1].split('.')[0].capitalize()})"
                    elif "v_cut" in img_filename:
                        caption = f"Velocity Distribution (Section {img_filename.split('_')[-1].split('.')[0].capitalize()})"
                    elif "v_streamlines" in img_filename:
                        # Extract number from v_streamlines1.png -> "1"
                        number = img_filename.replace("v_streamlines", "").replace(".png", "")
                        caption = f"Streamline Visualization {number}" if number else "Streamline Visualization"

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
