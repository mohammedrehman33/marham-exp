#!/usr/bin/env python3
"""
apply_general.py — add the affordable-specialists section using the GENERAL
doctors (doctors_general.json: Waqas / Salman / Usama).

Usage:
  python3 tools/apply_general.py --in PAGE.html --out PAGE.html [--disease "-"] [extra engine args]

Thin wrapper around inject_cmd_section.py; keeps the general flow separate
from the gyne flow. Default heading is the generic "Consult a Specialist ...".
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "inject_cmd_section.py")
DOCTORS = os.path.join(HERE, "doctors_general.json")

# default disease "-" => generic heading; --price 1000 keeps the approved
# general heading ("as Low as Rs. 1,000") consistent with the already-done pages.
extra = sys.argv[1:]
cmd = ["python3", ENGINE, "--doctors", DOCTORS]
if "--disease" not in extra:
    cmd += ["--disease", "-"]
if "--price" not in extra:
    cmd += ["--price", "1000"]
cmd += extra
sys.exit(subprocess.call(cmd))
