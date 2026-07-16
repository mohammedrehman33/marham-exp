#!/usr/bin/env python3
"""
inject_cmd_section.py — add the "Call My Doctors" affordable-specialists
section to ANY Marham disease/listing page.

Usage:
  python3 inject_cmd_section.py --in PAGE.html --out OUT.html [options]

Modes for doctor data:
  (default) --auto        Extract cheapest N doctors from the page's OWN listing.
  --doctors doctors.json  Use a provided JSON list (for hand-picked doctors).
                          Each item: {name, profile, photo, reviews, exp, fee, book}

Other options:
  --disease "Blood Pressure"   Override disease name in the heading (else auto from H1/title).
  --count 3                    How many cards to show (default 3).
  --anchor "<!--Doctors-->"    Marker to insert BEFORE (default tries a few).
  --fomo "..."                 Override the FOMO note text.

Idempotent: if the section already exists (CMD markers), it is replaced, not duplicated.
"""
import re, html, json, argparse, sys, urllib.parse

CMD_START = "<!-- CMD_SECTION_START -->"
CMD_END   = "<!-- CMD_SECTION_END -->"

STYLE = '''			<style>
			/* callMyDoctors - affordable-specialists cards. */
			#callMyDoctors .cmd-affordable{ background:#ffffff; border:1px solid #E7EAEE; border-radius:16px; padding:24px; box-shadow:5px 5px 16px 5px rgba(0,0,0,0.1); }
			#callMyDoctors .cmd-title{ margin:0; font-size:22px; font-weight:600; color:#16384a; line-height:1.25; }
			#callMyDoctors .cmd-sub{ margin:6px 0 20px; font-size:14px; font-weight:400; color:#4a5a68; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
			#callMyDoctors .cmd-fomo{ display:inline-flex; align-items:center; gap:6px; background:#fdecea; color:#d32f2f; font-weight:600; padding:4px 10px; border-radius:6px; font-size:13px; line-height:1.2; }
			#callMyDoctors .cmd-fomo .bolt{ font-size:14px; }
			#callMyDoctors .cmd-fomo-note{ color:#4a5a68; font-weight:500; }
			#callMyDoctors .cmd-grid{ display:flex; gap:16px; overflow-x:auto; padding-bottom:6px; scroll-snap-type:x mandatory; -webkit-overflow-scrolling:touch; }
			#callMyDoctors .cmd-card{ border:1px solid #E7EAEE; border-radius:12px; padding:16px; background:#fafafa; display:flex; flex-direction:column; flex:1 1 0; min-width:280px; max-width:none; scroll-snap-align:start; }
			#callMyDoctors .cmd-top{ display:flex; align-items:center; gap:12px; }
			#callMyDoctors .cmd-photo{ width:58px !important; height:58px !important; min-width:58px; min-height:58px; max-width:58px; max-height:58px; aspect-ratio:1 / 1; border-radius:50%; object-fit:cover !important; object-position:center; flex-shrink:0; border:2px solid #2BB3A3; padding:2px; background:#fff; box-sizing:border-box; }
			#callMyDoctors .cmd-name{ margin:0 0 4px; font-size:15px; line-height:1.2; }
			#callMyDoctors .cmd-name a{ color:#136c8f; text-decoration:none; font-weight:500; }
			#callMyDoctors .cmd-avail{ display:flex; align-items:center; gap:6px; font-size:13px; color:#1aa260; font-weight:500; margin-bottom:4px; }
			#callMyDoctors .cmd-avail .dot{ width:8px; height:8px; border-radius:50%; background:#1aa260; display:inline-block; flex-shrink:0; }
			#callMyDoctors .cmd-fee{ font-size:14px; font-weight:600; color:#1b2a3a; }
			#callMyDoctors .cmd-stats{ display:flex; align-items:center; gap:16px; margin:14px 0; font-size:12px; }
			#callMyDoctors .cmd-reviews{ color:#b4641d; font-weight:500; display:flex; align-items:center; gap:5px; }
			#callMyDoctors .cmd-reviews .star{ color:#f5a623; font-size:13px; }
			#callMyDoctors .cmd-exp{ color:#7a8a99; }
			#callMyDoctors .cmd-book{ margin-top:auto; display:block; width:100%; background:#084c61; color:#fff; text-align:center; text-decoration:none; font-size:14px; font-weight:500; padding:11px 12px; border-radius:8px; border:1px solid #084c61; line-height:1.2; }
			#callMyDoctors .cmd-book:hover{ background:#063b4c; color:#fff; }
			@media (max-width:768px){
				#callMyDoctors .cmd-affordable{ padding:18px; }
				#callMyDoctors .cmd-title{ font-size:19px; }
				#callMyDoctors .cmd-card{ flex:0 0 84%; max-width:84%; scroll-snap-align:start; }
			}
			</style>
'''

def esc(u): return (u or "").replace("&", "&amp;")

def avatar(initials):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='58' height='58' viewBox='0 0 58 58'>"
           "<rect width='58' height='58' rx='29' fill='#e6f4f5'/>"
           "<text x='29' y='38' font-family='Figtree,Arial,sans-serif' font-size='22' font-weight='700' "
           "fill='#2BB3A3' text-anchor='middle'>" + initials + "</text></svg>")
    return "data:image/svg+xml," + urllib.parse.quote(svg)

def initials_of(name):
    parts = [p for p in re.sub(r'(Dr\.|Prof\.|Asst\.|Assoc\.|Mr\.|Ms\.|Consultant|Homeopathic|Gold-Medalist)', '', name).split() if p]
    ini = "".join(p[0] for p in parts[:2]).upper()
    return ini or "DR"

def guess_disease(doc):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', doc, re.S)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1))
        t = html.unescape(t).strip()
        # "1,985 Best Doctors For Blood Pressure In Lahore" -> "Blood Pressure"
        mm = re.search(r'[Ff]or\s+(.*?)\s+[Ii]n\s+', t)
        if mm: return mm.group(1).strip()
    m = re.search(r'<title>\s*Best\s+Doctors\s+for\s+(.*?)\s+in\s+', doc, re.S)
    if m: return html.unescape(m.group(1)).strip()
    return "Specialist"

def extract_doctors(doc):
    """Pull doctors from the page's own listing (cards start with row shadow-card)."""
    docs = []
    for block in doc.split('<div class="row shadow-card">')[1:]:
        mname = re.search(r'doctor-listing-name-block.*?<h3[^>]*>(.*?)</h3>', block, re.S)
        if not mname: continue
        name = html.unescape(re.sub(r'<[^>]+>', '', mname.group(1))).strip()
        mprof = (re.search(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*dr_profile_opened_from_listing[^"]*"', block)
                 or re.search(r'class="[^"]*dr_profile_opened_from_listing[^"]*"[^>]*href="([^"]+)"', block))
        profile = html.unescape(mprof.group(1)) if mprof else '#'
        srcs = re.findall(r'<source[^>]*srcset="([^"]+)"', block[:2000])
        photo = srcs[-1].split(',')[0].strip().split(' ')[0] if srcs else ''
        mrev = (re.search(r'dr_profile_opened_from_listing_reviews.*?thumbs-up[^>]*></i>\s*([0-9,]+)', block, re.S)
                or re.search(r'dr_profile_opened_from_listing_reviews.*?</i>\s*([0-9,]+)\s*</p>', block, re.S))
        reviews = mrev.group(1).replace(',', '') if mrev else ''
        mexp = re.search(r'Experience\s*</p>\s*<p[^>]*>\s*([0-9]+)\s*Yrs', block, re.S)
        exp = mexp.group(1) if mexp else ''
        amounts = [int(x) for x in re.findall(r'data-amount="([0-9]+)"', block)]
        prices = [int(x.replace(',', '')) for x in re.findall(r'class="[^"]*\bprice\b[^"]*"[^>]*>\s*Rs\.\s*([0-9,]+)', block)]
        fees = [a for a in amounts + prices if a > 0]
        fee = min(fees) if fees else 0
        mbook = (re.search(r'dr_profile_opened_from_listing_btn_vcall"\s*href="([^"]+)"', block)
                 or re.search(r'href="([^"]+)"\s*[^>]*dr_profile_opened_from_listing_btn_vcall', block))
        book = html.unescape(mbook.group(1)) if mbook else profile
        docs.append(dict(name=name, profile=profile, photo=photo, reviews=reviews, exp=exp, fee=fee, book=book))
    return docs

def build_section(docs, disease, fomo_note, price=None, badge="FLAT 30% OFF on Lab Tests"):
    # "as Low as Rs. X": X is the LOWEST fee among the cards (or an explicit --price override).
    fees = [(d.get("fee") or 0) for d in docs if (d.get("fee") or 0) > 0]
    head_price = price if price else (min(fees) if fees else 0)
    # disease="" (or "-") -> generic "Consult a Specialist ..."; otherwise "Consult a <Disease> Specialist ..."
    label = (disease.strip() + " Specialist") if (disease and disease.strip() and disease.strip() != "-") else "Specialist"
    title = "Consult a {} for as Low as Rs. {}".format(label, f"{head_price:,}") if head_price \
            else "Consult a {} Online".format(label)
    cards = ""
    for d in docs:
        prof, book = esc(d["profile"]), esc(d.get("book") or d["profile"])
        photo = esc(d["photo"]) if d.get("photo") else avatar(initials_of(d["name"]))
        fee = f"Rs. {d['fee']:,}" if d.get("fee") else ""
        rev = f'<span class="cmd-reviews"><span class="star">★</span> {d["reviews"]} Reviews</span>' if d.get("reviews") else ""
        exp = f'<span class="cmd-exp">{d["exp"]}+ Years Exp</span>' if d.get("exp") else ""
        nm = html.escape(d["name"])
        cards += (f'<div class="cmd-card"><div class="cmd-top">'
                  f'<a class="instant_doctor_clicked" href="{prof}" data-url="{prof}"><img class="cmd-photo" src="{photo}" alt="{nm}" width="58" height="58" loading="lazy"></a>'
                  f'<div><p class="cmd-name"><a class="instant_doctor_clicked" href="{prof}" data-url="{prof}">{nm}</a></p>'
                  f'<div class="cmd-avail"><span class="dot"></span> Available Today</div>'
                  f'<div class="cmd-fee">{fee}</div></div></div>'
                  f'<div class="cmd-stats">{rev}{exp}</div>'
                  f'<a class="cmd-book instant_doctor_call_now_btn_clicked" href="{book}" data-url="{book}">Book Appointment</a></div>')
    section = (CMD_START + "\n" + STYLE +
               f'''			<div class="container mt-10" id="callMyDoctors">
				<div class="cmd-affordable" id="cmdPanel">
					<h2 class="cmd-title" id="cmdTitle">{title}</h2>
					<p class="cmd-sub"><span class="cmd-fomo" dir="auto"><span class="bolt">⚡</span> {html.escape(badge)}</span> <span class="cmd-fomo-note">{html.escape(fomo_note)}</span></p>
					<div class="cmd-grid" id="cmdGrid">{cards}</div>
				</div>
			</div>
''' + CMD_END + "\n")
    return section, title

def choose_anchor(doc, anchor):
    if anchor and anchor in doc:
        return anchor
    for cand in ["    <!--Doctors-->", "<!--Doctors-->", '<div class="container bg-white mt-10 pb-10" id="doctor-listing1">']:
        if cand in doc:
            return cand
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--doctors")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--disease")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--anchor", default="<!--Doctors-->")
    ap.add_argument("--fomo", default="Book today — limited-time offer, ends soon!")
    ap.add_argument("--badge", default="FLAT 30% OFF on Lab Tests", help="red highlight badge text (next to the bolt)")
    ap.add_argument("--price", type=int, default=None, help="force the heading 'as Low as Rs. X' number; default = lowest card fee")
    a = ap.parse_args()

    doc = open(a.inp, encoding="utf-8", newline="").read()  # newline="" preserves original CRLF/LF
    nl = "\r\n" if "\r\n" in doc else "\n"
    disease = a.disease or guess_disease(doc)

    if a.doctors:
        docs = json.load(open(a.doctors, encoding="utf-8"))
    else:
        docs = extract_doctors(doc)
        docs = [d for d in docs if (d.get("fee") or 0) > 0]
        docs.sort(key=lambda d: d["fee"])
        docs = docs[:a.count]
    if not docs:
        sys.exit("ERROR: no doctors found/provided. Use --doctors doctors.json")

    section, title = build_section(docs, disease, a.fomo, price=a.price, badge=a.badge)
    section = section.replace("\n", nl)  # match the page's own line endings

    # Idempotent: replace existing section if present.
    if CMD_START in doc and CMD_END in doc:
        doc = re.sub(re.escape(CMD_START) + r".*?" + re.escape(CMD_END) + r"\n?", section, doc, flags=re.S)
        placed = "replaced-existing"
    else:
        anchor = choose_anchor(doc, a.anchor)
        if not anchor:
            sys.exit("ERROR: no insertion anchor found; pass --anchor")
        doc = doc.replace(anchor, section + anchor, 1)
        placed = f"inserted-before:{anchor.strip()}"

    open(a.out, "w", encoding="utf-8", newline="").write(doc)  # newline="" keeps bytes intact
    print(f"OK  disease={disease!r}  cards={len(docs)}  title={title!r}  {placed}")

if __name__ == "__main__":
    main()
