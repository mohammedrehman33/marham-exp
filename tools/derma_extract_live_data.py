#!/usr/bin/env python3
"""Pull real listing data out of the live marham.pk/doctors/dermatologist HTML.
Cards anchor on the profile-photo alt text (present on every card, carries the
doctor's display name and city verbatim). Nothing here is invented."""
import re, io, json, html

s = io.open('live.html', encoding='utf-8', errors='replace').read()
clean = lambda t: html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t))).strip()

def lines_of(seg):
    seg = re.sub(r'<(script|style).*?</\1>', ' ', seg, flags=re.S)
    return [html.unescape(l).strip() for l in re.sub(r'<[^>]+>', '\n', seg).split('\n') if l.strip()]

phys, faq_block, agg = {}, None, None
for b in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', s, re.S):
    try: d = json.loads(b.strip())
    except Exception: continue
    if not isinstance(d, dict): continue
    if d.get('@type') == 'Physician':        phys[d['name']] = d
    elif d.get('@type') == 'FAQPage':        faq_block = d
    elif d.get('@type') == 'MedicalWebPage': agg = d

# ── doctors ──
STOP = {'Video Consultation', 'Fast Confirm', 'Available Today', 'Book Video Call',
        'Book Appointment', 'Available Tomorrow'}
CARD = re.compile(r'alt="Profile Photo of Dermatologist in ([^-"]+) - ([^"]+)"')
hits = [(m.start(), m.group(1).strip(), html.unescape(m.group(2))) for m in CARD.finditer(s)]
doctors = []
for i, (pos, city, name) in enumerate(hits):
    end = hits[i + 1][0] if i + 1 < len(hits) else pos + 16000
    lines = lines_of(s[pos:end])
    nxt = lambda lab: next((lines[j + 1] for j, l in enumerate(lines)
                            if l == lab and j + 1 < len(lines)), None)
    qual = next((l for l in lines if re.search(
        r'\b(MBBS|BDS|FCPS|MCPS|MD|MRCP|MRCGP|ECFMG|Diploma|D\. ?DERM)\b', l) and len(l) > 12), None)
    spec = None
    if name in lines:
        for l in lines[lines.index(name) + 1: lines.index(name) + 7]:
            if l in ('Top Booked Doctor', 'PMDC Verified'): continue
            if l == qual: break
            if re.search(r'Dermatolog|Physician|Surgeon|Cosmetolog', l): spec = l; break
    svc = []
    if 'Book Appointment' in lines:
        for l in lines[lines.index('Book Appointment') + 1:][:10]:
            if l in STOP or l.startswith('Rs.') or len(l) > 40: break
            svc.append(l)
    sc = phys.get(name, {})
    clinics = [{'place': h.get('name'), 'area': (h.get('address') or {}).get('addressLocality'),
                'city': (h.get('address') or {}).get('addressRegion'),
                'fee': h.get('priceRange'), 'url': h.get('url')}
               for h in (sc.get('hospitalAffiliation') or [])]
    fees = [int(re.sub(r'\D', '', c['fee'])) for c in clinics if c.get('fee') and re.search(r'\d', c['fee'])]
    online = sc.get('priceRange')
    if online and re.search(r'\d', online): fees.append(int(re.sub(r'\D', '', online)))
    doctors.append({'name': name, 'city': city, 'url': sc.get('url'),
                    'photo': (sc.get('image') or {}).get('url'),
                    'specialty': spec, 'qualifications': qual,
                    'reviews': nxt('Reviews'), 'experience': nxt('Experience'),
                    'satisfaction': nxt('Satisfaction'),
                    'topBooked': 'Top Booked Doctor' in lines, 'pmdc': 'PMDC Verified' in lines,
                    'minFee': min(fees) if fees else None,
                    'hasVideo': 'Video Consultation' in lines or 'Book Video Call' in lines,
                    'services': svc, 'clinics': clinics})

# ── FAQs ──
# Answers come from the FAQPage schema, questions from the visible accordion:
# the live page's schema sets the first entry's `name` to just "Dermatologist",
# while the rendered <h4> carries the real question. Visible wording wins.
_f = s.find('Frequently Asked Questions about Best Dermatologists')
vis = [clean(x) for x in re.findall(
    r'class="accordion-header">.*?<h4[^>]*>(.*?)</h4>', s[_f:_f + 30000], re.S)]
vis = [re.sub(r'\s{2,}', ' ', v) for v in vis]
faqs = []
for n, q in enumerate((faq_block or {}).get('mainEntity', [])):
    a = q.get('acceptedAnswer', {}).get('text', '')
    faqs.append({'q': vis[n] if n < len(vis) else clean(q.get('name', '')),
                 'a': re.sub(r'\s{2,}', ' ', clean(a.split('<ol>')[0] if '<ol>' in a else a)),
                 'list': [clean(x) for x in
                          re.findall(r'<li[^>]*>.*?<span[^>]*>(.*?)</span>', a, re.S)]})

# ── link blocks, bounded between their own headings ──
HEADS = ['Best Hospitals in Pakistan', 'Dermatologist Related Diseases',
         'Best Dermatologist in other cities of Pakistan']
idx = sorted((s.find('>' + h + '<'), h) for h in HEADS)
links = {}
for n, (start, head) in enumerate(idx):
    stop = idx[n + 1][0] if n + 1 < len(idx) else start + 8000
    got = [{'text': clean(t), 'href': h} for h, t in
           re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', s[start:stop], re.S)]
    links[head] = [g for g in got if g['text'] and '/appointments-policy' not in g['href']]

# ── SEO prose: every h2 from "About Dermatologist" to the FAQ heading ──
a0 = s.find('>About Dermatologist<')
a1 = s.find('Frequently Asked Questions about Best Dermatologists')
prose = []
for m in re.finditer(r'<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|\Z)', s[a0 - 200:a1], re.S):
    body = m.group(2)
    paras = [clean(x) for x in re.findall(r'<p[^>]*>(.*?)</p>', body, re.S)]
    items = [clean(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', body, re.S)]
    prose.append({'h': clean(m.group(1)),
                  'p': [x for x in paras if x], 'li': [x for x in items if x]})

h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
out = {'source': 'https://www.marham.pk/doctors/dermatologist',
       'title': clean(re.search(r'<title>(.*?)</title>', s, re.S).group(1)),
       'h1': clean(h1.group(1)) if h1 else None,
       'metaDescription': (re.search(r'<meta name="description" content="([^"]*)"', s) or [None, None])[1],
       'aggregateRating': (agg or {}).get('aggregateRating'),
       'doctors': doctors, 'faqs': faqs, 'linkBlocks': links, 'prose': prose}
json.dump(out, io.open('real_data.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

print("h1      :", out['h1'])
print("rating  :", out['aggregateRating'])
print("doctors : %d   faqs: %d   prose sections: %d" % (len(doctors), len(faqs), len(prose)))
for k, v in links.items(): print("  link block [%2d] %s" % (len(v), k))
print()
for d in doctors:
    print("  %-44s %-11s %-7s %-5s fee=%-6s vid=%-5s svc=%s" % (
        d['name'][:44], d['city'], d['experience'], d['satisfaction'],
        d['minFee'], d['hasVideo'], ', '.join(d['services'][:3])[:40]))
