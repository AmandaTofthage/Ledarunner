"""
simulation_pipeline.py
-----------------------

Central orchestration of LedaFlow simulations using the
QS templating workflow + SoftSH execution + LedaFlow result extraction.

Main responsibilities:
  - Create result folders
  - Build QS files from template
  - Run SoftSH simulation
  - Load case into LedaFlow
  - Run initialization + dynamic simulation
  - Export results
"""

import json
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd

from automation.template_engine import generate_qs_from_template
from automation.run_softsh import run_ledaflow_qs


# --- CREATE RESULT FOLDER ---
def create_result_folder(base_dir: Path) -> Path:
    """
    Create new result folder under runs/<DD_MM_YY>/run_<HH_MM>.
    Example:
        runs/03_11_25/run_14_07
    """
    now = datetime.now()
    date_folder = base_dir / now.strftime("%d_%m_%y")
    time_folder = date_folder / f"run_{now.strftime('%H_%M')}"
    time_folder.mkdir(parents=True, exist_ok=True)
    print(f"> Created result folder: {time_folder}")
    return time_folder

# --- VALIDATE TIMESERIES INPUTS ---
def validate_timeseries(name, time_points, values):
    """
    Ensures time_points and values match length.
    - If values longer → trimmed
    - If values shorter → padded with last value
    Generates Streamlit warnings instead of silently fixing.
    """
    t_len = len(time_points)
    v_len = len(values)

    if t_len == v_len:
        return values   # perfect match

    # Too many values → trim
    if v_len > t_len:
        st.warning(
            f"'{name}': You entered {v_len} values but only {t_len} time points. "
            f"Excess values will be trimmed to match the time vector."
        )
        return values[:t_len]

    # Too few values → pad
    if v_len < t_len:
        st.warning(
            f"'{name}': You entered {v_len} values but {t_len} time points. "
            f"The missing points will be filled by the last value: ({values[-1]}) to match the time vector."
        )
        return values + [values[-1]] * (t_len - v_len)


# --- SAVE USER INPUTS (for tracability) ---
def save_inputs(inputs: dict, result_folder: Path):
    """
    Save the user-defined inputs to a JSON file in the result folder.
    """
    inputs_file = result_folder / "inputs.json"
    with open(inputs_file, "w") as f:
        json.dump(inputs, f, indent=4)
    print(f"> Saved input configuration to {inputs_file}")


# --- HELPERS FOR CSV LOADING ---
@st.cache_data(ttl=600)
def load_csv_with_units(file_path):
    """
    Load CSV file and extract SI units from second header row.
    Returns: (dataframe, units_dict)
    where units_dict maps column names to their SI units.
    """
    # First, extract units from the second row before loading
    units = {}
    try:
        # Try to read with different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        second_row = lines[1].strip().split(',')
                        first_row = lines[0].strip().split(',')

                        # Check if second row looks like units (contains square brackets)
                        if len(second_row) == len(first_row) and all('[' in cell for cell in second_row):
                            for col, unit_cell in zip(first_row, second_row):
                                # Extract unit from [unit] format
                                unit = unit_cell.strip().strip('[]')
                                units[col] = unit
                break
            except UnicodeDecodeError:
                continue
    except Exception as e:
        print(f"[WARNING] Could not extract units from {file_path}: {e}")

    # Load CSV, skipping the unit header row (row 1, index 1)
    # Try different encodings
    df = None
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            df = pd.read_csv(file_path, skiprows=[1], encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"[WARNING] Could not load {file_path} with encoding {encoding}: {e}")
            continue

    if df is None:
        # Last resort: try without specifying encoding
        df = pd.read_csv(file_path, skiprows=[1], encoding='latin-1', on_bad_lines='skip')

    # Convert numeric columns to float
    for col in df.columns:
        if col.lower() not in ["time", "position"]:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                print(f"[DEBUG] Could not convert {col} to numeric: {e}")
                pass

    return df, units


# --- BUILD QS CASE FROM TEMPLATE ---
def build_qs_case(template_path: Path, out_qs_path: Path, user_inputs: dict, ):
    """
    Generate a QS file from the template and user-specified input values.
    """
    print("> Building QS model from template...")
    generate_qs_from_template(template_path, out_qs_path, user_inputs)
    print(f"> QS model generated → {out_qs_path}")
    
    
# ----------------------------------------------------------------------
#  Full simulation pipeline for a single case
# ----------------------------------------------------------------------
def run_single_case_simulation(qs_out: Path, result_folder: Path, lf, dynamic_time: float):

    # 1. SoftSH loads QS and creates case
    uuid = run_ledaflow_qs(lf.softsh, qs_out, result_folder)

    # 2. Select that case in the LedaFlow API
    lf.selectcase(uuid)
    
    # 3. Reload the generated QS so that all loggers/materials/devices attach properly
    lf.load_case_by_qs(str(qs_out)) 

    # 4. Initialization (steady-state pre-processor)
    lf.initialize_case()
    print("> Initialization complete.")

    # 5. Run dynamic simulation
    lf.rundynamic(dynamic_time)
    print("> Dynamic simulation complete.")
    

    # 6. Export trend logs
    try:
        lf.export_all_trends(result_folder / "trends")
    except Exception as e:
        try:
            (result_folder / "export_trends_error.txt").write_text(str(e))
        except Exception:
            pass
        print(f"[ERROR] Failed to export trends: {e}")

    # 7. Export profile logs
    try:
        for p in lf.safe_available_profiles():
            try:
                lf.export_all_profiles(result_folder / "profiles", p)
            except Exception as e:
                try:
                    (result_folder / f"export_profiles_error_{p}.txt").write_text(str(e))
                except Exception:
                    pass
                print(f"[ERROR] Failed to export profiles for {p}: {e}")
    except Exception as e:
        try:
            (result_folder / "export_profiles_error.txt").write_text(str(e))
        except Exception:
            pass
        print(f"[ERROR] Failed to list/ export profiles: {e}")

    return uuid


# ----------------------------------------------------------------------
#  Full simulation pipeline for parameter study
# ----------------------------------------------------------------------
def run_parameter_study_simulation(
    base_inputs: dict,
    varying_keys: list,
    all_combinations: list,
    template_path: Path,
    results_dir: Path,
    lf,
    dynamic_time: float,
    progress_callback=None,
):
    """
    Run a multi-parameter study given a list of combinations.

    Parameters
    - base_inputs: dict with time vectors and base values (same format used by template engine)
    - varying_keys: list of parameter keys corresponding to positions in each combo
    - all_combinations: list of tuples with values for each varying key
    - template_path, results_dir, lf, dynamic_time: as usual
    - progress_callback: optional callable(progress_index, total, case_folder)

    Returns a list of result dicts with keys: case_index, folder, uuid, parameters
    """
    study_results = []
    total = len(all_combinations)

    for i, combo in enumerate(all_combinations, start=1):
        # Build case-specific input dict (shallow copy ok)
        case_inputs = dict(base_inputs)

        # Override each varying parameter
        for k, value in zip(varying_keys, combo):
            if k == "SOURCE_MFR":
                case_inputs["SOURCE_MFR"] = value
            elif k == "SOURCE_TEMP":
                case_inputs["SOURCE_TEMP_K"] = value + 273.15
            elif k == "VALVE_OPENING":
                case_inputs["VALVE_OPENING"] = value
            elif k == "WH_PRESS":
                case_inputs["WH_PRESS"] = value * 1e5
            elif k == "WH_TEMP":
                case_inputs["WH_TEMP_K"] = value + 273.15
            else:
                # Generic override if key matches base_inputs naming
                case_inputs[k] = value

        # Create subfolder for this case under the provided root results_dir
        case_folder = results_dir / f"case_{i:03d}"
        case_folder.mkdir(parents=True, exist_ok=True)

        # Build QS case
        qs_out = case_folder / "model.qs"
        build_qs_case(template_path, qs_out, case_inputs)

        # Run LF simulation
        uuid = run_single_case_simulation(qs_out, case_folder, lf, dynamic_time)

        # Store metadata
        study_results.append({
            "case_index": i,
            "folder": str(case_folder),
            "uuid": uuid,
            "parameters": {k: v for k, v in zip(varying_keys, combo)},
        })

        # Progress callback (if provided)
        if progress_callback is not None:
            try:
                progress_callback(i, total, case_folder)
            except Exception:
                # swallow errors from callback to avoid stopping study
                pass

    return study_results