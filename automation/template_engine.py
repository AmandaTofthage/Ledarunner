"""
QS Template Engine
------------------
Generates QS files from templates with proper handling of both single case values and time-series inputs.
"""
from pathlib import Path

# --- HELPERS ---
def _is_timeseries_list(value):
    """Return True if value is a list of values (NOT list of (t,v))."""
    return isinstance(value, list) and len(value) > 0 and not isinstance(value[0], (list, tuple))


def _expand_constant(value, length):
    """
    Expand constant into an array of identical values.
    Example: value=4, length=3 → [4,4,4]
    """
    return [float(value)] * length
   

def _validate_or_expand(values, time_vector, name=""):
    """
    Ensure 'values' matches the length of time_vector.
      - If values is a list:
            If length matches → OK
            Else → ERROR
      - If values is a constant:
            Auto-expand to length of time_vector
    """
    n = len(time_vector)

    # Case: CONSTANT (float/int)
    if isinstance(values, (int, float)):
        return _expand_constant(values, n)

    # Case: LIST OF VALUES
    if _is_timeseries_list(values):
        if len(values) != n:
            raise RuntimeError(
                f"Input '{name}' has {len(values)} points, "
                f"but its component time vector has {n} points."
            )
        # Convert temp if needed
        return [float(v) for v in values]

    raise RuntimeError(f"Invalid input for '{name}': {values}")


def _format_array(arr):
    """Format Python list → QS array syntax: [1,2,3]"""
    return "[" + ",".join(str(v) for v in arr) + "]"


# --- MAIN FUNCTION ---
def generate_qs_from_template(template_path: Path, output_path: Path, raw_inputs: dict):
    """
    NEW fully-correct template engine matching GUI behavior.

    RULES:
      - User explicitly defines time arrays:
            SOURCE_TIME, VALVE_TIME, WH_TIME

      - Each component (source, valve, wellhead) must use its own time vector.

      - Variables inside a component (e.g., SOURCE_MFR and SOURCE_TEMP_K)
        must match the component's time vector length:
            - Constants → auto-expanded
            - Lists → must match length or error
    """

    text = template_path.read_text()

  
    # SOURCE COMPONENTS
    source_time = raw_inputs["SOURCE_TIME"]             # user gives list
    source_mfr  = raw_inputs["SOURCE_MFR"]              # constant or list
    source_temp = raw_inputs["SOURCE_TEMP_K"]           # constant or list

    # Validate or expand mfr
    source_mfr_vals = _validate_or_expand(
        source_mfr, source_time,  name="SOURCE_MFR"
    )

    # Validate or expand temperature
    source_temp_vals = _validate_or_expand(
        source_temp, source_time, name="SOURCE_TEMP_K"
    )


    # VALVE COMPONENT
    valve_time = raw_inputs["VALVE_TIME"]
    valve_opening = raw_inputs["VALVE_OPENING"]

    valve_opening_vals = _validate_or_expand(
        valve_opening, valve_time,  name="VALVE_OPENING"
    )


    # WELLHEAD COMPONENTS
    wh_time = raw_inputs["WH_TIME"]
    wh_press = raw_inputs["WH_PRESS"]
    wh_temp = raw_inputs["WH_TEMP_K"]

    wh_press_vals = _validate_or_expand(
        wh_press, wh_time,  name="WH_PRESS"
    )

    wh_temp_vals = _validate_or_expand(
        wh_temp, wh_time,  name="WH_TEMP_K"
    )


    # 
    # --- BUILD REPLACEMENTS ---
    replacements = {
        "{SOURCE_TIME}": _format_array(source_time),
        "{SOURCE_MFR}": _format_array(source_mfr_vals),
        "{SOURCE_TEMP_K}": _format_array(source_temp_vals),

        "{VALVE_TIME}": _format_array(valve_time),
        "{VALVE_OPENING}": _format_array(valve_opening_vals),

        "{WH_TIME}": _format_array(wh_time),
        "{WH_PRESS}": _format_array(wh_press_vals),
        "{WH_TEMP_K}": _format_array(wh_temp_vals),
    }

    print(">>> Template replacements:")
    for k, v in replacements.items():
        print(f"  {k} = {v}")

    # Apply replacements
    for key, val in replacements.items():
        text = text.replace(key, val)

    # Unreplaced placeholders → ERROR
    import re
    missing = re.findall(r"\{[A-Z0-9_]+\}", text)
    if missing:
        raise RuntimeError(f"Missing placeholders in QS template: {missing}")

    # Write output
    output_path.write_text(text)
    print(f">>> QS written to {output_path}")

    return output_path

