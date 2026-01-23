"""
Helper functions to reuse the legacy CFD run workflow (from GUI_ortho.py)
without pulling in the Tkinter UI.

This mirrors the core steps:
1) Write the flow rate file (pvfr.txt)
2) Run Allclean
3) Rebuild combined.stl from the triSurface parts
4) Run Allrun

It accepts the case directory and flow rate so Tab4 (or other callers)
can delegate the CFD stage to the legacy scripts.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def _log(logger, level: str, message: str):
    """Tiny logging helper."""
    if logger:
        getattr(logger, f"log_{level}", logger.log_info)(message)
    else:
        print(f"{level.upper()}: {message}")


def run_cfd(case_dir: str, flow_rate_lpm: float, logger=None) -> Tuple[bool, str]:
    """
    Run the legacy CFD workflow in a prepared case directory.

    Args:
        case_dir: Path to the OpenFOAM case (contains Allclean/Allrun).
        flow_rate_lpm: Volume flow rate in LPM to write into 0/pvfr.txt.
        logger: Optional logger with log_info/log_error methods.

    Returns:
        (success, message) tuple.
    """
    case_path = Path(case_dir)
    allclean = case_path / "Allclean"
    allrun = case_path / "Allrun"

    if not allclean.exists() or not allrun.exists():
        msg = f"Missing Allclean/Allrun in {case_dir}"
        _log(logger, "error", msg)
        return False, msg

    try:
        # 1) write pvfr file (after clean in legacy flow, but harmless before)
        step0 = case_path / "0"
        step0.mkdir(exist_ok=True)
        pvfr_path = step0 / "pvfr.txt"
        pvfr_path.write_text(f"vfr {flow_rate_lpm:.1f};\n#inputMode merge")
        _log(logger, "info", f"Wrote {pvfr_path}")

        # 2) Allclean
        _log(logger, "info", f"Running Allclean in {case_dir}")
        subprocess.run(["bash", "./Allclean"], cwd=case_dir, check=True)

        # 3) rebuild combined.stl from triSurface
        tri_dir = case_path / "constant" / "triSurface"
        combined = tri_dir / "combined.stl"
        if combined.exists():
            combined.unlink()
        stl_list = sorted(p for p in tri_dir.glob("*.stl") if p.name != "combined.stl")
        if not stl_list:
            msg = f"No STL files found in {tri_dir}"
            _log(logger, "error", msg)
            return False, msg
        # concatenate
        cat_cmd = "cat *.stl > combined.stl"
        subprocess.run(cat_cmd, shell=True, cwd=tri_dir, check=True)
        _log(logger, "info", f"Rebuilt {combined}")

        # 4) Allrun
        _log(logger, "info", f"Running Allrun in {case_dir}")
        allrun_proc = subprocess.run(
            ["bash", "./Allrun"],
            cwd=case_dir,
            check=False,
            capture_output=True,
            text=True,
        )
        if allrun_proc.returncode != 0:
            msg = f"Allrun failed (code {allrun_proc.returncode})"
            _log(logger, "error", msg)
            _log(logger, "error", allrun_proc.stdout or "")
            _log(logger, "error", allrun_proc.stderr or "")
            return False, msg

        _log(logger, "info", "Allrun completed")
        return True, "Allrun completed"

    except subprocess.CalledProcessError as e:
        msg = f"{e.cmd} failed with code {e.returncode}"
        _log(logger, "error", msg)
        return False, msg
    except Exception as e:  # pragma: no cover - general safety
        msg = f"{type(e).__name__}: {e}"
        _log(logger, "error", msg)
        return False, msg

