#!/usr/bin/env python3
"""
apply_gp_karachi.py — add the affordable-specialists section using the
KARACHI GP doctors (doctors_gp_karachi.json: Saba / Zahid / Akhtar).

Usage:
  python3 tools/apply_gp_karachi.py --in PAGE.html --out PAGE.html [--disease "-"] [extra engine args]

Thin wrapper around inject_cmd_section.py; keeps the Karachi-GP flow separate
from the general/gyne/psychologist flows. Default heading is the generic
"Consult a Specialist ..." with the lowest card fee (Rs. 1,000).
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "inject_cmd_section.py")
DOCTORS = os.path.join(HERE, "doctors_gp_karachi.json")

extra = sys.argv[1:]
cmd = ["python3", ENGINE, "--doctors", DOCTORS]
if "--disease" not in extra:
    cmd += ["--disease", "-"]
cmd += extra
sys.exit(subprocess.call(cmd))
