#!/usr/bin/env python3
"""
add_listing_filters.py — replace the search bar + old filter selects on a
Marham listing page with a pill-chip filter bar (bordered #004d71) that
ACTUALLY filters/sorts the doctor cards on the page, client-side.

Chips:
  Female Doctors      toggle  (needs --female-ids, gender is not in the markup)
  Most Experienced    sort    (Experience "NN Yrs", desc)
  Lowest Fee          sort    (min data-amount in the card, asc)
  Highest Rated       sort    (Satisfaction %, then reviews, desc)
  Available Today     toggle  ("Available Today" text in the card)
  Video Consultation  toggle  ("Video Consultation" clinic card present)

Usage:
  python3 tools/add_listing_filters.py --in PAGE.html --out PAGE.html \
      --female-ids "33127,13273,7872,69980"

It removes the block from `<div class="container mb-0">` (search-bar row +
filter selects) up to the `id="banner"` container and puts the chip bar in
its place. Byte-preserving elsewhere; idempotent via MH_FILTERS markers.
"""
import re, argparse, sys

START = "<!-- MH_FILTERS_START -->"
END = "<!-- MH_FILTERS_END -->"

TEMPLATE = START + '''
<style>
#mhFilters{ padding-top:12px; }
#mhFilters .mh-chips{ display:flex; gap:10px; overflow-x:auto; padding:6px 2px 12px; -webkit-overflow-scrolling:touch; scrollbar-width:none; scroll-behavior:smooth; }
#mhFilters .mh-chips::-webkit-scrollbar{ display:none; }
#mhFilters .mh-car{ position:relative; }
#mhFilters .mh-car-btn{ position:absolute; top:50%; transform:translateY(-50%); width:34px; height:34px; border-radius:50%; background:#fff; border:1px solid #dfe6ea; box-shadow:0 2px 10px rgba(10,40,60,.18); display:flex; align-items:center; justify-content:center; cursor:pointer; z-index:5; color:#004d71; padding:0; }
#mhFilters .mh-car-btn:hover{ background:#f2f8fb; }
#mhFilters .mh-car-btn svg{ width:16px; height:16px; display:block; }
#mhFilters .mh-car-btn.left{ left:-8px; }
#mhFilters .mh-car-btn.right{ right:-8px; }
#mhFilters .mh-car-btn.off{ display:none; }
@media (max-width:768px){ #mhFilters .mh-car-btn{ width:28px; height:28px; } #mhFilters .mh-car-btn svg{ width:13px; height:13px; } #mhFilters .mh-car-btn.left{ left:-4px; } #mhFilters .mh-car-btn.right{ right:-4px; } }
#mhFilters .mh-chip{ display:inline-flex; align-items:center; white-space:nowrap; padding:6px 14px; border:1px solid #004d71; border-radius:999px; background:#fff; color:#004d71; font-weight:400; font-size:13px; line-height:1.2; cursor:pointer; user-select:none; transition:background .15s,color .15s,box-shadow .15s; }
#mhFilters .mh-chip:hover{ box-shadow:0 1px 6px rgba(0,77,113,.25); }
#mhFilters .mh-chip.active{ background:#004d71; color:#fff; }
#mhFilters .mh-chip-ur{ font-family:system-ui, -apple-system, "Segoe UI", sans-serif; }
#mhFilters .mh-clear{ display:none; align-items:center; white-space:nowrap; padding:6px 14px; border:1px dashed #9aabb5; border-radius:999px; background:#fff; color:#5a6b77; font-weight:400; font-size:13px; line-height:1.2; cursor:pointer; user-select:none; }
#mhFilters .mh-clear:hover{ color:#004d71; border-color:#004d71; }
#mhFilters .mh-clear.show{ display:inline-flex; }
#mhFilters .mh-nores{ display:none; margin:4px 2px 10px; padding:12px 16px; border:1px dashed #004d71; border-radius:10px; color:#004d71; font-size:14px; background:#f2f8fb; }
/* hide the areas-of-interest chips row inside doctor cards */
.row.shadow-card .col-12.horizontal-scroll.smart-bar.mb-10{ display:none !important; }
</style>
<div class="container mb-0" id="mhFilters">
    <div class="mh-car">
    <button type="button" class="mh-car-btn left off" aria-label="Scroll left"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg></button>
    <div class="mh-chips" id="mhChips">
        <span class="mh-clear" id="mhClear">&#10005; Clear All</span>
        <span class="mh-chip" data-kind="toggle" data-key="female">Female Doctors</span>
        <span class="mh-chip" data-kind="sort" data-key="exp">Most Experienced</span>
        <span class="mh-chip" data-kind="sort" data-key="fee">Lowest Fee</span>
        <span class="mh-chip" data-kind="sort" data-key="rated">Highest Rated</span>
        <span class="mh-chip" data-kind="toggle" data-key="avail">Available Today</span>
        <span class="mh-chip" data-kind="toggle" data-key="video">Video Consultation</span>
{interest_chips}    </div>
    <button type="button" class="mh-car-btn right off" aria-label="Scroll right"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg></button>
    </div>
    <div class="mh-nores" id="mhNoRes">No doctors match the selected filters. Tap a filter again to remove it.</div>
</div>
<script>
(function(){
    var FEMALE_IDS = {__FEMALE_IDS__};
    function num(s){ s=(s||'').replace(/,/g,''); var n=parseInt(s,10); return isNaN(n)?0:n; }
    function docId(card){
        var el=card.querySelector('[data-doctorid],[data-doctorId]');
        if(el) return el.getAttribute('data-doctorid')||el.getAttribute('data-doctorId');
        // fallback: the impression span rendered just before the card
        var p=card.previousElementSibling, hops=0;
        while(p&&hops<4){
            if(p.classList&&p.classList.contains('doctor-impression-id')) return p.getAttribute('data-doctor-id');
            if(p.classList&&p.classList.contains('shadow-card')) break;
            p=p.previousElementSibling; hops++;
        }
        return '';
    }
    function init(){
        var cards=[].slice.call(document.querySelectorAll('.row.shadow-card'));
        if(!cards.length) return;
        var items=cards.map(function(card,i){
            var t=card.textContent||'';
            var interests=[].slice.call(card.querySelectorAll('[data-location="area of interest"]')).map(function(e){return e.textContent.trim();});
            var fees=[].slice.call(card.querySelectorAll('[data-amount]')).map(function(el){return num(el.getAttribute('data-amount'));}).filter(function(n){return n>0;});
            var mExp=t.match(/Experience\\s*([0-9]+)\\s*Yrs/); var mSat=t.match(/Satisfaction\\s*([0-9]+)%/);
            var revEl=card.querySelector('.text-golden');
            var did=docId(card);
            return { card:card, order:i,
                fee:fees.length?Math.min.apply(null,fees):999999,
                exp:mExp?num(mExp[1]):0,
                sat:mSat?num(mSat[1]):0,
                rev:revEl?num(revEl.textContent):0,
                female:FEMALE_IDS.indexOf(String(did))>-1,
                interests:interests,
                avail:t.indexOf('Available Today')>-1,
                video:t.indexOf('Video Consultation')>-1 };
        });
        // one slot marker per original card position, so sorting works
        // globally even when cards live in multiple listing containers
        var slots=items.map(function(it){
            var m=document.createComment('mh-slot');
            it.card.parentNode.insertBefore(m, it.card);
            return m;
        });
        var toggles={}, sortKey=null, interestsOn={};
        var chips=[].slice.call(document.querySelectorAll('#mhChips .mh-chip, #mhInterests .mh-chip'));
        function apply(){
            var wanted=Object.keys(interestsOn).filter(function(k){return interestsOn[k];});
            var visible=items.filter(function(it){
                if(toggles.female&&!it.female) return false;
                if(toggles.avail&&!it.avail) return false;
                if(toggles.video&&!it.video) return false;
                if(wanted.length&&!it.interests.some(function(x){return wanted.indexOf(x)>-1;})) return false;
                return true;
            });
            items.forEach(function(it){ it.card.style.display='none'; });
            var ordered=visible.slice().sort(function(a,b){
                if(sortKey==='exp') return b.exp-a.exp||a.order-b.order;
                if(sortKey==='fee') return a.fee-b.fee||a.order-b.order;
                if(sortKey==='rated') return b.sat-a.sat||b.rev-a.rev||a.order-b.order;
                return a.order-b.order;
            });
            ordered.forEach(function(it,i){
                slots[i].parentNode.insertBefore(it.card, slots[i]);
                it.card.style.display='';
            });
            document.getElementById('mhNoRes').style.display=visible.length?'none':'block';
            var any=sortKey||Object.keys(toggles).some(function(k){return toggles[k];})||wanted.length;
            document.getElementById('mhClear').classList.toggle('show',!!any);
        }
        document.getElementById('mhClear').addEventListener('click',function(){
            toggles={}; sortKey=null; interestsOn={};
            chips.forEach(function(c){ c.classList.remove('active'); });
            apply();
        });
        // carousel arrows for each chip row
        [].slice.call(document.querySelectorAll('#mhFilters .mh-car')).forEach(function(car){
            var row=car.querySelector('.mh-chips'),L=car.querySelector('.mh-car-btn.left'),R=car.querySelector('.mh-car-btn.right');
            if(!row||!L||!R) return;
            function upd(){
                var max=row.scrollWidth-row.clientWidth;
                if(max<=4){ L.classList.add('off'); R.classList.add('off'); return; }
                L.classList.toggle('off',row.scrollLeft<=2);
                R.classList.toggle('off',row.scrollLeft>=max-2);
            }
            L.addEventListener('click',function(){ row.scrollBy({left:-Math.round(row.clientWidth*0.7),behavior:'smooth'}); });
            R.addEventListener('click',function(){ row.scrollBy({left:Math.round(row.clientWidth*0.7),behavior:'smooth'}); });
            row.addEventListener('scroll',upd,{passive:true});
            window.addEventListener('resize',upd);
            upd();
        });
        chips.forEach(function(ch){
            ch.addEventListener('click',function(){
                var kind=ch.getAttribute('data-kind'), key=ch.getAttribute('data-key');
                if(kind==='interest'){ interestsOn[key]=!interestsOn[key]; ch.classList.toggle('active',!!interestsOn[key]); }
                else if(kind==='toggle'){ toggles[key]=!toggles[key]; ch.classList.toggle('active',!!toggles[key]); }
                else{
                    if(sortKey===key){ sortKey=null; ch.classList.remove('active'); }
                    else{ sortKey=key; chips.forEach(function(c){ if(c.getAttribute('data-kind')==='sort') c.classList.remove('active'); }); ch.classList.add('active'); }
                }
                apply();
            });
        });
    }
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
</script>
''' + END + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--female-ids", default="", help='comma-separated doctor ids to treat as female, e.g. "33127,7872"')
    ap.add_argument("--interests", default="", help='comma-separated areas-of-interest to offer as filter chips. Plain "Nasal Polyps" or "Nasal Polyps=ناک کے غدود" to show an Urdu label as "اردو (English)" while matching the English span text')
    a = ap.parse_args()

    doc = open(a.inp, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in doc else "\n"
    ids = [s.strip() for s in a.female_ids.split(",") if s.strip()]
    interests = [s.strip() for s in a.interests.split(",") if s.strip()]
    import html as _html
    def interest_chip(x):
        # "English=اردو" -> key stays English (matches card spans), label shows "اردو (English)"
        if "=" in x:
            eng, urdu = [s.strip() for s in x.split("=", 1)]
            label = "%s (%s)" % (_html.escape(urdu), _html.escape(eng))
            return ('        <span class="mh-chip mh-chip-ur" dir="auto" data-kind="interest" data-key="%s">%s</span>\n'
                    % (_html.escape(eng, quote=True), label))
        return ('        <span class="mh-chip" data-kind="interest" data-key="%s">%s</span>\n'
                % (_html.escape(x, quote=True), _html.escape(x)))
    interest_chips = "".join(interest_chip(x) for x in interests)
    block = (TEMPLATE.replace("{__FEMALE_IDS__}", "[" + ",".join('"%s"' % i for i in ids) + "]")
                     .replace("{interest_chips}", interest_chips).replace("\n", nl))

    if START in doc and END in doc:
        doc = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\r?\n?", lambda m: block, doc, flags=re.S)
        placed = "replaced-existing"
    else:
        m_start = re.search(r'[ \t]*<div class="container mb-0">\s*\r?\n\s*<div class="row search-bar">', doc)
        if not m_start:
            sys.exit("ERROR: search-bar container not found")
        m_end = doc.find('<div class="container" id="banner"', m_start.start())
        if m_end < 0:
            sys.exit("ERROR: banner container (end anchor) not found")
        doc = doc[:m_start.start()] + block + doc[m_end:]
        placed = "replaced-search-bar-block"

    open(a.out, "w", encoding="utf-8", newline="").write(doc)
    print("OK  " + placed + "  female-ids=" + ",".join(ids))

if __name__ == "__main__":
    main()
