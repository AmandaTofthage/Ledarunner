"""
QS Template Generation Script
----------------------
Run this script to create a QS template from an existing QS file.
"""
from qs_to_template import make_template_from_qs
from pathlib import Path

orig = Path("C:/cases/CO2_pipe.qs")
tplt = Path("C:/cases/template.qs")

make_template_from_qs(orig, tplt)
