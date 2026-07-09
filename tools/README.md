# Call My Doctors — affordable-specialists section injector

Adds the `#callMyDoctors` "Consult a … Specialist for as Low as Rs. X" section
(with the 30% OFF lab-test FOMO subtitle, circular photos, card grid) to any
Marham disease/listing page.

## Usage

Auto — pull the cheapest doctors from the page's own listing:
```
python3 tools/inject_cmd_section.py --in PAGE.html --out PAGE.html --auto --count 3
```

Hand-picked doctors (when you supply new doctors + their fee/reviews/photos):
```
python3 tools/inject_cmd_section.py --in PAGE.html --out PAGE.html \
    --doctors tools/doctors.example.json --disease "Blood Pressure"
```

- Disease name auto-detected from the page `<h1>`/`<title>` (override with `--disease`).
- Section inserted before `<!--Doctors-->` (override with `--anchor`).
- **Idempotent:** re-running replaces the existing section (marked by
  `CMD_SECTION_START/END`) instead of duplicating it.
