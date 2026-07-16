#!/usr/bin/env python3
"""
add_show_doctors_button.py — add a sticky bottom-left "Show Doctors" pill
(circled up-arrow + label, #004d71) that appears after scrolling past a
threshold (default 650px) and smooth-scrolls back to the doctor listing.
Responsive on mobile and desktop.

Usage:
  python3 tools/add_show_doctors_button.py --in PAGE.html --out PAGE.html [--offset 650]

Byte-preserving; idempotent via MH_SHOWDOC markers; injected before </body>.
"""
import re, argparse, sys

START = "<!-- MH_SHOWDOC_START -->"
END = "<!-- MH_SHOWDOC_END -->"

TEMPLATE = START + '''
<style>
#mhShowDoc{ position:fixed; left:16px; bottom:20px; z-index:99999; display:inline-flex; align-items:center; gap:10px; background:#004d71; color:#fff; border:none; border-radius:999px; padding:9px 20px 9px 10px; font-size:15px; font-weight:600; line-height:1; cursor:pointer; box-shadow:0 6px 18px rgba(0,20,30,.3); opacity:0; visibility:hidden; transform:translateY(14px); transition:opacity .25s ease, transform .25s ease, visibility .25s; }
#mhShowDoc.show{ opacity:1; visibility:visible; transform:translateY(0); }
#mhShowDoc:hover{ background:#01608d; }
#mhShowDoc .mh-arr{ width:30px; height:30px; min-width:30px; border-radius:50%; border:2px solid #fff; display:flex; align-items:center; justify-content:center; box-sizing:border-box; }
#mhShowDoc .mh-arr svg{ width:14px; height:14px; display:block; }
@media (max-width:768px){
  #mhShowDoc{ left:12px; bottom:16px; font-size:13px; padding:7px 16px 7px 8px; gap:8px; }
  #mhShowDoc .mh-arr{ width:26px; height:26px; min-width:26px; }
  #mhShowDoc .mh-arr svg{ width:12px; height:12px; }
}
</style>
<button id="mhShowDoc" type="button" aria-label="Show Doctors">
  <span class="mh-arr"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg></span>
  Show Doctors
</button>
<script>
(function(){
    var OFFSET={__OFFSET__};
    function init(){
        var btn=document.getElementById('mhShowDoc');
        if(!btn) return;
        var target=document.getElementById('mhFilters')||document.getElementById('doctor-listing1');
        function onScroll(){
            var y=window.pageYOffset||document.documentElement.scrollTop||0;
            if(y>OFFSET) btn.classList.add('show'); else btn.classList.remove('show');
        }
        window.addEventListener('scroll', onScroll, {passive:true});
        onScroll();
        btn.addEventListener('click', function(){
            if(target&&target.scrollIntoView) target.scrollIntoView({behavior:'smooth', block:'start'});
            else window.scrollTo({top:0, behavior:'smooth'});
        });
    }
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
</script>
''' + END + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--offset", type=int, default=650, help="scroll px after which the button appears")
    a = ap.parse_args()

    doc = open(a.inp, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in doc else "\n"
    block = TEMPLATE.replace("{__OFFSET__}", str(a.offset)).replace("\n", nl)

    if START in doc and END in doc:
        doc = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\r?\n?", lambda m: block, doc, flags=re.S)
        placed = "replaced-existing"
    else:
        idx = doc.rfind("</body>")
        if idx < 0:
            sys.exit("ERROR: </body> not found")
        doc = doc[:idx] + block + doc[idx:]
        placed = "inserted-before:</body>"

    open(a.out, "w", encoding="utf-8", newline="").write(doc)
    print("OK  offset=%dpx  %s" % (a.offset, placed))

if __name__ == "__main__":
    main()
