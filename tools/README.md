# Call My Doctors — affordable-specialists section injector

> Also in this folder: `add_listing_filters.py` — replaces a listing page's
> search bar with working pill-chip filters (Female / Most Experienced /
> Lowest Fee / Highest Rated / Available Today / Video Consultation),
> border `#004d71`. Pass female doctor ids via `--female-ids` since gender
> isn't in the page markup. Byte-preserving + idempotent (MH_FILTERS markers).

Adds the `#callMyDoctors` "Consult a Specialist for as Low as Rs. X" section
(with the 30% OFF lab-test FOMO subtitle, circular photos, card grid) to any
Marham disease/listing page.

## Separate flows (share one engine, different doctor lists)

| Flow | Script | Doctors file |
|------|--------|--------------|
| General | `tools/apply_general.py` | `tools/doctors_general.json` (Waqas / Salman / Usama) |
| Gyne    | `tools/apply_gyne.py`    | `tools/doctors_gyne.json` (gyne doctors) |
| Psychologist | `tools/apply_psychologist.py` | `tools/doctors_psychologist.json` (psychology doctors) |
| Karachi GP | `tools/apply_gp_karachi.py` | `tools/doctors_gp_karachi.json` (Saba / Zahid / Akhtar) |

All are thin wrappers over the shared engine `tools/inject_cmd_section.py`,
so changing one flow never affects the others. To add a new specialty flow,
copy a doctors JSON + an `apply_<name>.py` wrapper.

### General pages
```
python3 tools/apply_general.py --in PAGE.html --out PAGE.html
```

### Gyne pages
1. Put the 3 gyne doctors in `tools/doctors_gyne.json` (same shape as
   `doctors_general.json`: name, profile, photo, reviews, exp, fee, book).
2. Run:
```
python3 tools/apply_gyne.py --in PAGE.html --out PAGE.html
```

## Engine (advanced / direct use)
```
python3 tools/inject_cmd_section.py --in PAGE.html --out PAGE.html \
    --doctors tools/doctors_general.json --disease "-"
```
- `--disease "-"` → generic heading "Consult a Specialist ...".
  `--disease "Piles"` → "Consult a Piles Specialist ...".
  Omit `--disease` → auto-detect from the page `<h1>`/`<title>`.
- `--auto` (instead of `--doctors`) pulls the cheapest doctors from the page's own listing.
- Section inserted before `<!--Doctors-->` (override with `--anchor`).
- **Byte-preserving:** keeps the page's original bytes and CRLF line endings; only the section is added.
- **Idempotent:** re-running replaces the existing section (marked by `CMD_SECTION_START/END`) instead of duplicating it.
