#!/usr/bin/env python3
"""
add_show_doctors_button.py — add a sticky bottom-right "Show Doctors" pill
(circled up-arrow + label, #004d71) that appears once the user scrolls down
to the `.seo-page-content` div (fallback: --offset px if that div is
missing) and smooth-scrolls back to the doctor listing. Responsive on
mobile and desktop.

Usage:
  python3 tools/add_show_doctors_button.py --in PAGE.html --out PAGE.html [--offset 650]

Byte-preserving; idempotent via MH_SHOWDOC markers; injected before </body>.
"""
import re, argparse, sys

START = "<!-- MH_SHOWDOC_START -->"
END = "<!-- MH_SHOWDOC_END -->"

TEMPLATE = START + '''
<style>
#mhShowDoc{ position:fixed; right:16px; bottom:18px; z-index:99999; display:inline-flex; align-items:center; gap:7px; background:#004d71; color:#fff; border:none; border-radius:999px; padding:6px 14px 6px 7px; font-size:13px; font-weight:500; line-height:1; cursor:pointer; box-shadow:0 4px 14px rgba(0,20,30,.28); opacity:0; visibility:hidden; transform:translateY(14px); transition:opacity .25s ease, transform .25s ease, visibility .25s; }
#mhShowDoc.show{ opacity:1; visibility:visible; transform:translateY(0); }
#mhShowDoc:hover{ background:#01608d; }
#mhShowDoc .mh-arr{ width:22px; height:22px; min-width:22px; border-radius:50%; border:1.5px solid #fff; display:flex; align-items:center; justify-content:center; box-sizing:border-box; }
#mhShowDoc .mh-arr svg{ width:11px; height:11px; display:block; }
@media (max-width:768px){
  #mhShowDoc{ right:12px; bottom:14px; font-size:12px; padding:5px 12px 5px 6px; gap:6px; }
  #mhShowDoc .mh-arr{ width:20px; height:20px; min-width:20px; }
  #mhShowDoc .mh-arr svg{ width:10px; height:10px; }
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
        var seo=document.querySelector('.seo-page-content');
        function onScroll(){
            var on;
            if(seo){
                // show once the seo-page-content div has entered the viewport
                on = seo.getBoundingClientRect().top <= window.innerHeight;
            }else{
                var y=window.pageYOffset||document.documentElement.scrollTop||0;
                on = y>OFFSET;
            }
            if(on) btn.classList.add('show'); else btn.classList.remove('show');
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
