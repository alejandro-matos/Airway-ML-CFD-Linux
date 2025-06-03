import subprocess
import re
import numpy as np
import os
import argparse
import math


# TODO: Change all -time 20 to -time 100 or whatever number of steps used

def run_command(command, case_dir=None):
    """Run a shell command and return its output"""
    if case_dir:
        # Change to the case directory to run the command
        command = f"cd {case_dir} && {command}"
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout



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
    inlet_file = os.path.join(case_dir, "postProcessing", "avgsurf_in", "0", "surfaceFieldValue.dat")
    outlet_file = os.path.join(case_dir, "postProcessing", "avgsurf_out", "0", "surfaceFieldValue.dat")

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


def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Extract pressure and velocity from OpenFOAM case')
    parser.add_argument('--case', '-c', type=str, help='Path to OpenFOAM case directory', default=os.getcwd())
    parser.add_argument('--time', '-t', type=str, help='Time to extract (default: 20)', default='20')
    parser.add_argument('--boundaries', '-b', nargs='+', help='Boundaries to extract (default: inlet and outlet)', 
                        default=['inlet', 'outlet'])
    
    args = parser.parse_args()
    
    # Make sure the case directory is an absolute path
    case_dir = os.path.abspath(args.case)
    
    # Check if the directory exists
    if not os.path.isdir(case_dir):
        print(f"Error: Case directory '{case_dir}' does not exist.")
        return
    
    boundaries = args.boundaries
    results = extract_cfd_data(case_dir, time=args.time, boundaries=args.boundaries)
    # Print or return as you like for CLI usage
    print("results:", results)
    return results

if __name__ == "__main__":
    main()
    