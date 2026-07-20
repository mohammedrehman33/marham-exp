#!/usr/bin/env python3
"""
apply_benchmark.py — apply the FULL karachi-gp benchmark treatment to a
Marham listing page in one command. This is the reference pipeline for
the look frozen in benchmark/karachi-gp.benchmark.html.

What it applies (in order):
  1. Call-My-Doctors section (inject_cmd_section.py)
       - generic "Consult a Specialist for as Low as Rs. <lowest fee>" heading
       - Urdu badge "7 دن تک ڈاکٹر سے مفت رہنمائی حاصل کریں" + stethoscope icon + shimmer
       - UTM-tagged Book Appointment CTAs (per-doctor utm_content)
  2. Pill-chip filters replacing the search bar (add_listing_filters.py)
       - Female / Most Experienced / Lowest Fee / Highest Rated /
         Available Today / Video Consultation + Clear All, border #004d71
  3. Sticky bottom-right "Show Doctors" button (add_show_doctors_button.py)
       - appears when .seo-page-content enters the viewport

Usage:
  python3 tools/apply_benchmark.py --in PAGE.html --out PAGE.html \
      --doctors DOCTORS.json --utm-source karachi_gp_page \
      [--female-ids "id1,id2"] [--badge "..."] [--disease "-"] [--price N]

  --doctors      JSON list of the 3 hand-picked doctors
                 (name, profile, photo, reviews, exp, fee, book)
  --utm-source   utm_source for the Book CTAs (medium/campaign are fixed:
                 cmd_section / call_my_doctors)
  --female-ids   doctor ids on the page to treat as female for the filter
                 (look at the listing names; gender is not in the markup)

Each sub-tool is byte-preserving and idempotent, so re-running is safe.
"""
import os, sys, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_BADGE = "7 دن تک ڈاکٹر سے مرہم ایپ سے مفت رہنمائی حاصل کریں"
DEFAULT_FOMO = "Book online consultation — limited-time offer, ends soon!"

def run(script, args):
    cmd = ["python3", os.path.join(HERE, script)] + args
    print(">>", script, " ".join(args))
    r = subprocess.call(cmd)
    if r != 0:
        sys.exit(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--doctors", required=True, help="doctors JSON for the CMD section")
    ap.add_argument("--utm-source", required=True, help='e.g. "karachi_gp_page"')
    ap.add_argument("--female-ids", default="", help="comma-separated female doctor ids for the filter")
    ap.add_argument("--interests", default="", help='areas-of-interest chips, "English=اردو" pairs comma-separated (passed through to add_listing_filters)')
    ap.add_argument("--badge", default=DEFAULT_BADGE)
    ap.add_argument("--fomo", default=DEFAULT_FOMO)
    ap.add_argument("--disease", default="-")
    ap.add_argument("--price", type=int, default=None, help="override heading price (default: lowest card fee)")
    ap.add_argument("--offset", type=int, default=650, help="Show-Doctors fallback scroll offset")
    a = ap.parse_args()

    utm = "utm_source=%s&utm_medium=cmd_section&utm_campaign=call_my_doctors" % a.utm_source

    cmd_args = ["--in", a.inp, "--out", a.out, "--doctors", a.doctors,
                "--disease", a.disease, "--badge", a.badge, "--fomo", a.fomo, "--utm", utm]
    if a.price:
        cmd_args += ["--price", str(a.price)]
    run("inject_cmd_section.py", cmd_args)
    filter_args = ["--in", a.out, "--out", a.out, "--female-ids", a.female_ids]
    if a.interests:
        filter_args += ["--interests", a.interests]
    run("add_listing_filters.py", filter_args)
    run("add_show_doctors_button.py", ["--in", a.out, "--out", a.out, "--offset", str(a.offset)])
    print("OK  benchmark treatment applied to", a.out)

if __name__ == "__main__":
    main()
