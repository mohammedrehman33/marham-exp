#!/usr/bin/env python3
"""
apply_gyne.py — add the affordable-specialists section using the GYNE doctors
(doctors_gyne.json). Separate from the general flow so gyne pages get gyne
doctors without touching any of the already-done general pages.

Usage:
  python3 tools/apply_gyne.py --in PAGE.html --out PAGE.html [--disease "-"] [extra engine args]

Fill tools/doctors_gyne.json with the 3 gyne doctors first (same shape as
doctors_general.json). Default heading is the generic "Consult a Specialist ...".
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "inject_cmd_section.py")
DOCTORS = os.path.join(HERE, "doctors_gyne.json")

extra = sys.argv[1:]
cmd = ["python3", ENGINE, "--doctors", DOCTORS]
if "--disease" not in extra:
    cmd += ["--disease", "-"]
cmd += extra
sys.exit(subprocess.call(cmd))
