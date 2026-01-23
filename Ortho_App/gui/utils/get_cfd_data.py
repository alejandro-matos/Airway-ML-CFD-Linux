import os
import math


def read_latest_velocity_magnitude(file_path):
    """
    Reads the latest velocity vector (in format (ux uy uz)) and returns its magnitude.
    """
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        for line in reversed(lines):
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split(maxsplit=2)
                if len(parts) >= 3 and "(" in parts[2]:
                    vec_str = parts[2].strip("()")
                    components = vec_str.split()
                    if len(components) == 3:
                        ux, uy, uz = map(float, components)
                        magnitude = math.sqrt(ux**2 + uy**2 + uz**2)
                        return magnitude
    except Exception as e:
        print(f"Error reading velocity file {file_path}: {e}")
    return None

def read_latest_pressure_value(file_path):
    """
    Reads the last valid pressure value from a surfaceFieldValue.dat file.
    """
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        for line in reversed(lines):
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split()
                if len(parts) >= 2:
                    return float(parts[1])  # pressure value is in 2nd column
    except Exception as e:
        print(f"Error reading pressure file {file_path}: {e}")
    return None

def extract_cfd_data_from_files(case_dir):
    inlet_file = os.path.join(case_dir, "postProcessing", "avgsurf1", "0", "surfaceFieldValue.dat")
    outlet_file = os.path.join(case_dir, "postProcessing", "avgsurf11", "0", "surfaceFieldValue.dat")

    inlet_pressure = read_latest_pressure_value(inlet_file)
    outlet_pressure = read_latest_pressure_value(outlet_file)
    inlet_velocity = read_latest_velocity_magnitude(inlet_file)
    outlet_velocity = read_latest_velocity_magnitude(outlet_file)

    results = {
        "inlet_pressure": inlet_pressure,
        "outlet_pressure": outlet_pressure,
        "pressure_drop": None,
        "inlet_velocity": inlet_velocity, 
        "outlet_velocity": outlet_velocity
    }

    if inlet_pressure is not None and outlet_pressure is not None:
        results["pressure_drop"] = inlet_pressure - outlet_pressure

    return results
