import subprocess
import re
import numpy as np
import os
import argparse


# TODO: Change all -time 20 to -time 100 or whatever number of steps used

def run_command(command, case_dir=None):
    """Run a shell command and return its output"""
    if case_dir:
        # Change to the case directory to run the command
        command = f"cd {case_dir} && {command}"
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def get_pressure(boundary_name, case_dir=None):
    """Get pressure at specified boundary"""
    command = f"postProcess -time 20 -func \"patchAverage(name={boundary_name},p)\""
    output = run_command(command, case_dir)
    
    # Extract pressure value
    match = re.search(r'areaAverage\(' + boundary_name + r'\) of p = ([\d\.]+)', output)
    if match:
        return float(match.group(1))
    return None

def get_velocity(boundary_name, case_dir=None):
    """Get velocity at specified boundary"""
    command = f"postProcess -time 20 -func \"patchAverage(name={boundary_name},U)\""
    output = run_command(command, case_dir)
    
    # Extract velocity components
    match = re.search(r'areaAverage\(' + boundary_name + r'\) of U = \(([\d\.\-e+]+) ([\d\.\-e+]+) ([\d\.\-e+]+)\)', output)
    if match:
        ux = float(match.group(1))
        uy = float(match.group(2))
        uz = float(match.group(3))
        magnitude = np.sqrt(ux**2 + uy**2 + uz**2)
        return {
            "magnitude": magnitude,
            "components": [ux, uy, uz]
        }
    return None

def extract_cfd_data(case_dir, time="20", boundaries=("inlet", "outlet")):
    """
    Extract average pressure and velocity from the OpenFOAM case
    and return them in a dictionary.
    """
    results = {}
    for boundary in boundaries:
        pval = get_pressure(boundary, case_dir)
        vval = get_velocity(boundary, case_dir)

        results[f"{boundary}_pressure"] = pval
        results[f"{boundary}_velocity"] = vval

    # Optionally compute pressure drop if both inlet and outlet are present
    inlet_key = "inlet_pressure"
    outlet_key = "outlet_pressure"
    if inlet_key in results and outlet_key in results:
        if results[inlet_key] is not None and results[outlet_key] is not None:
            results["pressure_drop"] = results[inlet_key] - results[outlet_key]

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
    