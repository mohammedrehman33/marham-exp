#!/usr/bin/env python3
"""
apply_psychologist.py — add the affordable-specialists section using the
PSYCHOLOGIST doctors (doctors_psychologist.json). Separate from the general and
gyne flows so psychology pages get their own doctors without touching any other
already-done pages.

Usage:
  python3 tools/apply_psychologist.py --in PAGE.html --out PAGE.html [--disease "-"] [extra engine args]

Default heading is the generic "Consult a Specialist ...".
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "inject_cmd_section.py")
DOCTORS = os.path.join(HERE, "doctors_psychologist.json")

extra = sys.argv[1:]
cmd = ["python3", ENGINE, "--doctors", DOCTORS]
if "--disease" not in extra:
    cmd += ["--disease", "-"]
cmd += extra
sys.exit(subprocess.call(cmd))
