"""
SoftSH Runner
--------------
Handles execution of SoftSH to load QS scripts and create LedaFlow cases programmatically.
"""

import subprocess
from pathlib import Path
import time
from LedaFlow import LedaFlow

def _write_js_runner(js_path: Path, qs_path: Path):
    """
    Create a JS file that SoftSH can execute to load a QS script and return its UUID.
    """
    qs_path_str = str(qs_path).replace("\\", "/")
    
    script = [
        'try {',
        '  var CASES = ledaModules.CASES();',
        f'  var c = CASES.createCaseFrom("{qs_path_str}");',
        '  print("UUID:", c.uuid);',
        '  print("CASE_DIR:", c.caseFolder);',
        '} catch (e) {',
        '  try { print("CASES_ERROR:", e.toString()); } catch (ee) {}',
        '  try { if (e.stack) print("CASES_STACK:", e.stack); } catch (ee) {}',
        '  throw e;',
        '}'
    ]

    js_path.write_text("\n".join(script))


def run_ledaflow_qs(softsh_path: Path, qs_path: Path, result_folder: Path):
    """
    Runs SoftSH to load the QS file and create a LedaFlow case.
    Returns the UUID.
    """
    
    # Build JS runner file
    js_runner = result_folder / "run_case.js"
    _write_js_runner(js_runner, qs_path)

    # Single SoftSH invocation (no -run / -without_gui)
    proc = subprocess.run([str(softsh_path), str(js_runner)], capture_output=True, text=True)
    stdout, stderr = proc.stdout, proc.stderr

    # Extract UUID
    uuid = None
    for line in (stdout + stderr).splitlines():
        if "UUID:" in line:
            uuid = line.split(":", 1)[1].strip()

    if not uuid:
        raise RuntimeError(f"Failed to extract case UUID.\nSoftSH stdout: {stdout}\nSoftSH stderr: {stderr}")
    
    # wait until LedaFlow API can "see" the case
    for _ in range(20):
        try:
            lf_test = LedaFlow("2.11.271.018")
            lf_test.selectcase(uuid)
            break   
        except:
            time.sleep(0.5)
    else:
        raise RuntimeError("Case UUID created by SoftSH but not visible to LedaFlow")
    # Write uuid to file in the result folder for traceability
    try:
        (result_folder / "case_uuid.txt").write_text(uuid)
    except Exception:
        pass

    return uuid
