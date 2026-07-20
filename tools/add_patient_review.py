#!/usr/bin/env python3
"""
add_patient_review.py — inject a story-based patient review strip into a
specific doctor's listing card (proof close to the CTA).

Principles baked in ($100M Leads-style proof + Don't-Make-Me-Think UI):
  - REAL review text, verbatim (authentic > polished)
  - story hook headline that kills an objection (e.g. patient travelled
    from another city)
  - scannable at a glance: gold stars, score chip, verified badge
  - 2-line clamp with a pure-CSS "Read full story" toggle (no JS)
  - link out to ALL reviews for deeper proof

Usage:
  python3 tools/add_patient_review.py --in PAGE.html --out PAGE.html \
      --doctor-id 6955 \
      --headline "Why a patient travelled from Faisalabad to see Dr. Imran Zia" \
      --review "Dr sb is very caring person ..." \
      --author "Patient from Faisalabad" \
      --reviews-url "https://www.marham.pk/doctors/lahore/dentist/dr-imran-zia/reviews" \
      --reviews-count 474

Idempotent per doctor (MH_REVIEW_<id> markers); byte-preserving elsewhere.
The card is located via its preceding doctor-impression-id span.
"""
import re, html, argparse, sys

STYLE_MARK = "<!-- MH_REVIEW_STYLE -->"
STYLE = STYLE_MARK + '''<style>
.mh-review{ width:100%; margin:12px 0 2px; background:#f5fbfd; border:1px solid #d9eaf1; border-left:3px solid #2BB3A3; border-radius:10px; padding:12px 16px; box-sizing:border-box; }
.mh-rev-top{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:6px; }
.mh-rev-stars{ color:#f5a623; font-size:13px; letter-spacing:2px; }
.mh-rev-score{ background:#e8f6f0; color:#0d7a4f; font-weight:600; font-size:12px; padding:2px 8px; border-radius:6px; }
.mh-rev-verified{ display:inline-flex; align-items:center; gap:4px; color:#0d7a4f; font-size:12px; font-weight:500; }
.mh-rev-head{ margin:0 0 4px; font-size:14px; font-weight:600; color:#16384a; line-height:1.35; }
.mh-rev-check{ display:none !important; position:absolute !important; opacity:0 !important; width:0 !important; height:0 !important; margin:0 !important; }
.mh-rev-text{ margin:0; font-size:13px; color:#43555f; line-height:1.55; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.mh-rev-check:checked ~ .mh-rev-text{ -webkit-line-clamp:unset; display:block; }
.mh-rev-more{ display:inline-block; margin-top:4px; font-size:12.5px; font-weight:600; color:#004d71; cursor:pointer; user-select:none; }
.mh-rev-more::after{ content:attr(data-more); }
.mh-rev-check:checked ~ .mh-rev-more::after{ content:attr(data-less); }
.mh-rev-foot{ margin-top:6px; font-size:12px; color:#7a8a99; }
.mh-rev-foot a{ color:#004d71; font-weight:500; text-decoration:none; }
.mh-rev-foot a:hover{ text-decoration:underline; }
@media (max-width:768px){ .mh-review{ padding:10px 12px; } .mh-rev-head{ font-size:13px; } }
</style>
<script>(function(){function f(){document.querySelectorAll('.mh-review').forEach(function(r){var t=r.querySelector('.mh-rev-text'),l=r.querySelector('.mh-rev-more'),c=r.querySelector('.mh-rev-check');if(!t||!l||!c)return;if(!c.checked){l.style.display=(t.scrollHeight>t.offsetHeight+2)?'inline-block':'none';}});}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',f);else f();window.addEventListener('resize',f);})();</script>'''

BLOCK = '''{style}<!-- MH_REVIEW_START_{did} -->
<div class="mh-review">
    <div class="mh-rev-top"><span class="mh-rev-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span class="mh-rev-score">{score}</span><span class="mh-rev-verified">&#10003; Verified Patient Review</span></div>
    <p class="mh-rev-head">{headline}</p>
    <input type="checkbox" id="mhrev-{did}" class="mh-rev-check">
    <p class="mh-rev-text">&ldquo;{review}&rdquo;</p>
    <label for="mhrev-{did}" class="mh-rev-more" data-more="Read full story" data-less="Show less"></label>
    <div class="mh-rev-foot">&mdash; {author} &nbsp;&middot;&nbsp; <a href="{url}" target="_blank" rel="noopener">Read all {count} reviews</a></div>
</div>
<!-- MH_REVIEW_END_{did} -->
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--doctor-id", required=True)
    ap.add_argument("--headline", required=True)
    ap.add_argument("--review", required=True)
    ap.add_argument("--author", default="Verified Patient")
    ap.add_argument("--score", default="10/10")
    ap.add_argument("--reviews-url", required=True)
    ap.add_argument("--reviews-count", default="")
    a = ap.parse_args()

    doc = open(a.inp, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in doc else "\n"
    did = a.doctor_id

    style = "" if STYLE_MARK in doc else STYLE
    block = BLOCK.format(style=style, did=did, headline=html.escape(a.headline),
                         review=html.escape(a.review), author=html.escape(a.author),
                         score=html.escape(a.score),
                         url=a.reviews_url.replace("&", "&amp;"), count=a.reviews_count or "the")
    block = block.replace("\n", nl)

    smark, emark = "<!-- MH_REVIEW_START_%s -->" % did, "<!-- MH_REVIEW_END_%s -->" % did
    if smark in doc and emark in doc:
        doc = re.sub(re.escape(smark) + r".*?" + re.escape(emark) + r"\r?\n?", lambda m: block, doc, flags=re.S)
        placed = "replaced-existing"
    else:
        span = re.search(r'<span class="doctor-impression-id" data-doctor-id="%s"></span>' % did, doc)
        if not span:
            sys.exit("ERROR: impression span for doctor %s not found" % did)
        card_start = doc.find('<div class="row shadow-card">', span.end())
        if card_start < 0:
            sys.exit("ERROR: card after span not found")
        m_next = re.search(r'<span class="doctor-impression-id"|<!--Doctors-->|id="doctor-listing2"', doc[card_start:])
        card_end_zone = card_start + (m_next.start() if m_next else len(doc) - card_start)
        close_idx = doc.rfind("</div>", card_start, card_end_zone)
        if close_idx < 0:
            sys.exit("ERROR: card closing tag not found")
        doc = doc[:close_idx] + block + doc[close_idx:]
        placed = "inserted-in-card"

    open(a.out, "w", encoding="utf-8", newline="").write(doc)
    print("OK  doctor=%s  %s" % (did, placed))

if __name__ == "__main__":
    main()
