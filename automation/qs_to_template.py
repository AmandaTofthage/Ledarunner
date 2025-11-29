"""
QS Template Generator
---------------------
Generates a QS template from an original QS file by replacing user-controlled values with placeholders.
"""

import re
from pathlib import Path

def make_template_from_qs(input_qs: Path, output_template: Path):
    """
    Reads the original .qs file and replaces key user-controlled values
    with placeholders. Produces template.qs.
    """

    text = input_qs.read_text()

    # -----------------------------
    # Replace SOURCE (inlet) BC2 flowrate + temperature
    # -----------------------------
    text = re.sub(
        r"BC2\.massFlowrate\s*=\s*\[[^\]]+\]",
        "BC2.massFlowrate = {SOURCE_MFR}",
        text
    )

    text = re.sub(
        r"BC2\.temperature\s*=\s*\[[^\]]+\]",
        "BC2.temperature = {SOURCE_TEMP_K}",
        text
    )

    # Replace BC2.time (time vector for SOURCE) with a placeholder so source time-series
    # is independent from other boundaries
    text = re.sub(
        r"BC2\.time\s*=\s*\[[^\]]+\]",
        "BC2.time = {SOURCE_TIME}",
        text
    )


    # -----------------------------
    # Replace VALVE opening
    # -----------------------------
    text = re.sub(
        r"VALVE1\.opening\s*=\s*\[[^\]]+\]",
        "VALVE1.opening = {VALVE_OPENING}",
        text
    )

    # Replace VALVE time vector
    text = re.sub(
        r"VALVE1\.time\s*=\s*\[[^\]]+\]",
        "VALVE1.time = {VALVE_TIME}",
        text
    )

    # -----------------------------
    # Replace WELLHEAD BC1 pressure + temperature
    # -----------------------------
    text = re.sub(
        r"BC1\.pressure\s*=\s*\[[^\]]+\]",
        "BC1.pressure = {WH_PRESS}",
        text
    )

    text = re.sub(
        r"BC1\.temperature\s*=\s*\[[^\]]+\]",
        "BC1.temperature = {WH_TEMP_K}",
        text
    )

    # Replace BC1.time (use distinct placeholders for pressure and temperature if desired)
    # We'll add a dedicated placeholder for temperature time so pressure/time can be independent
    text = re.sub(
        r"BC1\.time\s*=\s*\[[^\]]+\]",
        "BC1.time = {WH_TIME}",
        text
    )

    # Save the template
    output_template.write_text(text)
    print(f"Template generated:\n → {output_template}")