#!/usr/bin/env python3
"""
redesign_doctor_card.py — replace a doctor's listing card with the
"Booking Panel Split" layout: profile on the left, dedicated booking
rail on the right (Video Call / In-Clinic tabs), review strip under the
profile. Fully responsive: the rail stacks under the profile on mobile.

Usage:
  python3 tools/redesign_doctor_card.py --in PAGE.html --out PAGE.html \
      --config tools/card_imran_zia.json

The config JSON carries all card data (see card_imran_zia.json).
Idempotent per doctor (MH_CARD2_<id> markers); byte-preserving elsewhere.
Original card is located via its preceding doctor-impression-id span.
"""
import re, json, html, argparse, sys

STYLE_MARK = "<!-- MH_CARD2_STYLE -->"
STYLE = STYLE_MARK + '''<style>
.mh2-card{ display:flex; align-items:stretch; background:#fff; border:1px solid #e8ecef; border-radius:14px; box-shadow:0 2px 10px rgba(16,42,60,.06); margin:10px 0 16px; overflow:hidden; }
.mh2-main{ flex:1 1 auto; min-width:0; padding:20px 22px; }
.mh2-head{ display:flex; gap:16px; }
.mh2-photo{ width:92px; height:92px; min-width:92px; border-radius:50%; object-fit:cover; border:1px solid #e2e8ec; background:#f4f7f9; }
.mh2-namerow{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.mh2-name{ margin:0; font-size:20px; font-weight:700; color:#1b2a3a; line-height:1.2; }
.mh2-name a{ color:#1b2a3a; text-decoration:none; }
.mh2-topbooked{ background:#3aa981; color:#fff; font-size:11px; font-weight:700; letter-spacing:.4px; padding:4px 10px; border-radius:6px; white-space:nowrap; }
.mh2-pmdc{ color:#0d7a4f; font-size:13px; font-weight:600; margin-top:4px; }
.mh2-spec{ color:#43555f; font-size:14px; margin-top:4px; }
.mh2-stats{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
.mh2-stat{ background:#f2f5f7; color:#3c4b57; font-size:12.5px; font-weight:500; padding:5px 12px; border-radius:999px; white-space:nowrap; }
.mh2-stat .st{ color:#f5a623; }
.mh2-chips{ display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }
.mh2-chip{ border:1px solid #cfdbe2; color:#136c8f; background:#fff; font-size:12.5px; padding:6px 13px; border-radius:8px; white-space:nowrap; }
.mh2-review{ margin-top:14px; border-left:3px solid #2BB3A3; background:#f7fbfc; border-radius:0 10px 10px 0; padding:10px 14px; }
.mh2-rev-top{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:4px; }
.mh2-rev-stars{ color:#f5a623; font-size:12px; letter-spacing:2px; }
.mh2-rev-verified{ color:#0d7a4f; font-size:12px; font-weight:600; }
.mh2-rev-quote{ margin:0; font-size:13px; color:#43555f; font-style:italic; line-height:1.55; }
.mh2-rev-link{ display:inline-block; margin-top:5px; font-size:12.5px; font-weight:600; color:#004d71; text-decoration:none; }
.mh2-rev-link:hover{ text-decoration:underline; }
.mh2-rail{ flex:0 0 320px; max-width:320px; background:#fafbfc; border-left:1px solid #eceff2; padding:18px 20px; display:flex; flex-direction:column; box-sizing:border-box; }
.mh2-tabs{ display:flex; background:#eef1f4; border-radius:10px; padding:3px; }
.mh2-tab{ flex:1; border:1px solid transparent; background:transparent; color:#5a6b77; font-size:13.5px; font-weight:600; padding:8px 4px; border-radius:8px; cursor:pointer; text-align:center; transition:all .15s; }
.mh2-tab.on{ background:#fff; color:#1b2a3a; border-color:#1b2a3a; }
.mh2-pane{ padding-top:14px; }
.mh2-avail{ display:flex; align-items:center; gap:6px; color:#1aa260; font-size:13px; font-weight:500; margin-bottom:6px; }
.mh2-avail .dot{ width:8px; height:8px; border-radius:50%; background:#1aa260; }
.mh2-pricerow{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.mh2-price{ font-size:24px; font-weight:700; color:#1b2a3a; }
.mh2-oldprice{ font-size:14px; color:#9aa7b0; text-decoration:line-through; }
.mh2-save{ background:#fff3e0; color:#c77700; font-size:12px; font-weight:700; padding:3px 9px; border-radius:6px; }
.mh2-offer{ font-size:12.5px; color:#5a6b77; margin-top:4px; }
.mh2-clinic{ font-size:14px; font-weight:600; color:#136c8f; margin-bottom:4px; line-height:1.35; }
.mh2-cta{ display:block; width:100%; text-align:center; text-decoration:none; font-size:15px; font-weight:600; padding:13px 12px; border-radius:10px; margin-top:14px; box-sizing:border-box; line-height:1.2; }
.mh2-cta.video{ background:#3aa981; color:#fff; }
.mh2-cta.video:hover{ background:#329270; color:#fff; }
.mh2-cta.clinic{ background:#084c61; color:#fff; }
.mh2-cta.clinic:hover{ background:#063b4c; color:#fff; }
.mh2-note{ margin-top:auto; padding-top:14px; font-size:12px; color:#8a97a1; text-align:center; }
@media (max-width:900px){
  .mh2-card{ flex-direction:column; }
  .mh2-rail{ flex:1 1 auto; max-width:none; border-left:none; border-top:1px solid #eceff2; }
  .mh2-photo{ width:72px; height:72px; min-width:72px; }
  .mh2-name{ font-size:17px; }
  .mh2-main{ padding:16px; }
  .mh2-rail{ padding:16px; }
}
</style>'''

TPL = '''{style}<!-- MH_CARD2_START_{did} -->
<div class="mh2-card" id="mh2-{did}">
  <div class="mh2-main">
    <div class="mh2-head">
      <a href="{profile}" class="dr_profile_opened_from_listing" data-location="doctor image"><img class="mh2-photo" src="{photo}" alt="{name}" width="92" height="92" loading="lazy"></a>
      <div style="min-width:0;">
        <div class="mh2-namerow"><h3 class="mh2-name"><a href="{profile}" class="dr_profile_opened_from_listing">{name}</a></h3>{topbooked}</div>
        {pmdc}
        <div class="mh2-spec">{spec}</div>
        <div class="mh2-stats"><span class="mh2-stat"><span class="st">&#9733;</span> {reviews} reviews</span><span class="mh2-stat">{exp} yrs experience</span><span class="mh2-stat">{sat}% satisfaction</span></div>
      </div>
    </div>
    <div class="mh2-chips">{chips}</div>
    <div class="mh2-review">
      <div class="mh2-rev-top"><span class="mh2-rev-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span class="mh2-rev-verified">&#10003; Verified patient review</span></div>
      <p class="mh2-rev-quote">&ldquo;{quote}&rdquo;</p>
      <a class="mh2-rev-link" href="{revurl}" target="_blank" rel="noopener">Read all {reviews} reviews &rarr;</a>
    </div>
  </div>
  <div class="mh2-rail">
    <div class="mh2-tabs">
      <button type="button" class="mh2-tab on" data-pane="video">Video Call</button>
      <button type="button" class="mh2-tab" data-pane="clinic">In-Clinic</button>
    </div>
    <div class="mh2-pane" data-pane="video">
      <div class="mh2-avail"><span class="dot"></span> Available today</div>
      <div class="mh2-pricerow"><span class="mh2-price">{vfee}</span><span class="mh2-oldprice">{voldfee}</span><span class="mh2-save">{vsave}</span></div>
      <div class="mh2-offer">{voffer}</div>
      <a class="mh2-cta video dr_profile_opened_from_listing_btn_vcall" href="{vurl}">{vcta}</a>
    </div>
    <div class="mh2-pane" data-pane="clinic" style="display:none;">
      <div class="mh2-clinic">{cname}</div>
      <div class="mh2-avail"><span class="dot"></span> Available today</div>
      <div class="mh2-pricerow"><span class="mh2-price">{cfee}</span></div>
      <a class="mh2-cta clinic dr_profile_open_frm_listing_btn_vprofile" href="{curl}">{ccta}</a>
    </div>
    <div class="mh2-note">{footnote}</div>
  </div>
</div>
<script>(function(){{var c=document.getElementById('mh2-{did}');if(!c)return;var tabs=c.querySelectorAll('.mh2-tab'),panes=c.querySelectorAll('.mh2-pane');tabs.forEach(function(t){{t.addEventListener('click',function(){{tabs.forEach(function(x){{x.classList.remove('on');}});t.classList.add('on');var k=t.getAttribute('data-pane');panes.forEach(function(p){{p.style.display=(p.getAttribute('data-pane')===k)?'':'none';}});}});}});}})();</script>
<!-- MH_CARD2_END_{did} -->
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--config", required=True)
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    did = cfg["doctor_id"]
    doc = open(a.inp, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in doc else "\n"

    esc = lambda u: (u or "").replace("&", "&amp;")
    chips = "".join('<span class="mh2-chip">%s</span>' % html.escape(c) for c in cfg.get("chips", []))
    block = TPL.format(
        style="" if STYLE_MARK in doc else STYLE,
        did=did, name=html.escape(cfg["name"]), photo=esc(cfg["photo"]), profile=esc(cfg["profile"]),
        topbooked='<span class="mh2-topbooked">&#9733; TOP BOOKED</span>' if cfg.get("top_booked") else "",
        pmdc='<div class="mh2-pmdc">&#10003; PMDC Verified</div>' if cfg.get("pmdc") else "",
        spec=cfg["specialty_line"], reviews=cfg["reviews"], exp=cfg["exp"], sat=cfg["satisfaction"],
        chips=chips, quote=html.escape(cfg["review_quote"]), revurl=esc(cfg["reviews_url"]),
        vfee=cfg["video"]["fee"], voldfee=cfg["video"].get("old_fee", ""), vsave=cfg["video"].get("save", ""),
        voffer=cfg["video"].get("note", ""), vcta=cfg["video"]["cta"], vurl=esc(cfg["video"]["url"]),
        cname=cfg["clinic"]["name"], cfee=cfg["clinic"]["fee"], ccta=cfg["clinic"]["cta"], curl=esc(cfg["clinic"]["url"]),
        footnote=cfg.get("footer_note", ""),
    ).replace("\n", nl)

    smark, emark = "<!-- MH_CARD2_START_%s -->" % did, "<!-- MH_CARD2_END_%s -->" % did
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
        zone_end = card_start + (m_next.start() if m_next else len(doc) - card_start)
        close_idx = doc.rfind("</div>", card_start, zone_end)
        if close_idx < 0:
            sys.exit("ERROR: card closing tag not found")
        doc = doc[:card_start] + block + doc[close_idx + len("</div>"):]
        placed = "replaced-original-card"

    open(a.out, "w", encoding="utf-8", newline="").write(doc)
    print("OK  doctor=%s  %s" % (did, placed))

if __name__ == "__main__":
    main()
