#!/usr/bin/env python3
"""Fill the redesign with real data scraped from
https://www.marham.pk/doctors/dermatologist (extract.py -> real_data.json).

Every value rendered comes from that page. Sections the live page cannot supply
(patient review text, before/after photos) are removed, not invented."""
import io, json, re, html

D    = json.load(io.open('real_data.json', encoding='utf-8'))
src  = io.open('redesign_template.fixed.html', encoding='utf-8').read()
TOTAL  = D['h1'].split()[0]                    # "1,167"
RATING = D['aggregateRating']
esc    = lambda t: html.escape(t, quote=False)

def sub(old, new, count=None):
    """Replace old with new. count pins the expected number of hits; None means
    'at least one, replace them all'."""
    global src
    n = src.count(old)
    assert n >= 1 and (count is None or n == count), \
        "expected %s got %d for: %s" % (count or '>=1', n, old[:80])
    src = src.replace(old, new)

def cut_section(needle):
    """Delete the whole <section …> … </section> that contains `needle`."""
    global src
    k = src.index(needle)
    i = src.rindex('<section', 0, k)
    j = src.index('</section>', k) + len('</section>')
    assert src[i:j].count('<section') == 1, 'nested section'
    src = src[:i] + src[j:]

# ══ 1. Copy — the live page is Pakistan-wide, not Karachi ════════════════
for old, new in [
    ('Meet the Experts Behind Your Transformation', '%s Best Dermatologists in Pakistan' % TOTAL),
    ('Tap a concern to see only the Karachi dermatologists who treat it.',
     "Each condition opens Marham's specialist list for that condition."),
    ('See all 440 dermatologists →', 'See all %s dermatologists →' % TOTAL),
    ('Frequently Asked Questions about Best Dermatologists in Karachi',
     'Frequently Asked Questions about Best Dermatologists in Pakistan'),
    ('Best Dermatologists in top Hospitals of Karachi', 'Best Hospitals in Pakistan'),
    ('All 440 PMDC-verified dermatologists in Karachi, sorted by patient satisfaction.',
     'All %s dermatologists listed on Marham, sorted by patient satisfaction.' % TOTAL),
]:
    sub(old, new)

# ══ 2. Sections with no real source — remove rather than fake ════════════
cut_section('<div class="mr-stories-head"')          # before/after photos: none exist
# testimonial quote cards: the live page exposes only an aggregate, no review text
i = src.index('<div class="mr-testi-grid"')
j = src.index('</div>\n<p style="font-size:12.5px', i)
src = src[:i] + src[j:]
sub('<p style="font-size:12.5px;color:var(--mr-text-subtle);margin:16px 0 0;max-width:80ch">Reviews are '
    "published with the patient's consent. Marham does not edit review text or remove negative reviews, "
    'and a doctor cannot pay to have a review taken down.</p>',
    '<p style="font-size:12.5px;color:var(--mr-text-subtle);margin:16px 0 0;max-width:80ch">Rating is the '
    'sitewide aggregate published on marham.pk/doctors/dermatologist. Individual review text is not '
    'exposed on that page.</p>')
# retitle + repoint the testimonial block at the real aggregate rating
sub('Reviews from patients treated in Karachi', 'Patient satisfaction across Marham')
sub("Left only by patients who booked the appointment through Marham and attended it.",
    'Aggregate rating published on the Marham dermatologist listing.')
sub('<div style="font-size:30px;font-weight:800;letter-spacing:-.02em;color:var(--mr-success);'
    'line-height:1">4.8</div>',
    '<div style="font-size:30px;font-weight:800;letter-spacing:-.02em;color:var(--mr-success);'
    'line-height:1">%s</div>' % RATING['ratingValue'])
sub('across 12,400+ verified reviews',
    'across %s reviews' % format(int(RATING['reviewCount']), ','))

# ══ 3. Doctor cards — real photos, real profile links, real city ═════════
# onerror hides a photo the CDN refuses, leaving the tinted circle behind it
# rather than a broken-image icon.
IMG = ('<img src="{{ d.photo }}" alt="{{ d.name }}" loading="lazy" width="78" height="78" '
       'onerror="this.style.display=\'none\'" '
       'style="width:100%;height:100%;object-fit:cover">')
sub('<image-slot id="{{ d.slot }}" shape="circle" placeholder="Dr."></image-slot>', IMG)
sub('<image-slot id="{{ d.slotAlt }}" shape="circle" placeholder="Dr."></image-slot>', IMG)
sub('<a href="#" style="font-size:19px;font-weight:700;color:var(--mr-heading);letter-spacing:-.015em;'
    'text-decoration:none;display:block;line-height:1.25">{{ d.name }}</a>',
    '<a href="{{ d.url }}" style="font-size:19px;font-weight:700;color:var(--mr-heading);'
    'letter-spacing:-.015em;text-decoration:none;display:block;line-height:1.25">{{ d.name }}</a>', 2)
sub('<div style="font-size:14.5px;color:var(--mr-text-muted);line-height:1.4">Karachi</div>',
    '<div style="font-size:14.5px;color:var(--mr-text-muted);line-height:1.4">{{ d.city }}</div>', 2)
sub('<a href="#" style="flex:1;text-align:center;text-decoration:none;font-size:14.5px;font-weight:700;'
    'padding:12px 10px;border-radius:var(--mr-radius-base);background:var(--mr-primary);color:#fff"',
    '<a href="{{ d.url }}" style="flex:1;text-align:center;text-decoration:none;font-size:14.5px;'
    'font-weight:700;padding:12px 10px;border-radius:var(--mr-radius-base);'
    'background:var(--mr-primary);color:#fff"', 2)
# Concern tiles: the live page publishes neither per-condition artwork nor a
# per-condition doctor count, so the tile becomes a plain tinted block with the
# condition name set inside it — no empty image slot, no invented number.
sub('<div class="mr-concern-tile" style="height:150px;border-radius:var(--mr-radius-2xl);'
    'overflow:hidden;background:{{ c.tint }}">\n'
    '<image-slot id="{{ c.slot }}" shape="rect" placeholder="{{ c.label }}"></image-slot>\n'
    '</div>\n'
    '<div class="mr-concern-label" style="font-size:15.5px;font-weight:600;color:var(--mr-primary);'
    'letter-spacing:-.01em;margin-top:12px">{{ c.label }}</div>\n'
    '<div style="font-size:12.5px;font-weight:600;color:var(--mr-text-subtle);margin-top:2px">'
    '{{ c.count }}</div>',
    '<div class="mr-concern-tile" style="height:132px;border-radius:var(--mr-radius-2xl);'
    'background:{{ c.tint }};display:flex;align-items:center;justify-content:center;padding:14px">\n'
    '<span class="mr-concern-label" style="font-size:16px;font-weight:700;color:var(--mr-primary);'
    'letter-spacing:-.01em;text-align:center;line-height:1.3">{{ c.label }}</span>\n'
    '</div>')

# ══ 4. SEO prose — the live page's own copy, verbatim ════════════════════
prose = []
for n, sec in enumerate(D['prose']):
    tag = 'h2' if n == 0 else 'h3'
    style = ('font-size:28px;line-height:1.2;font-weight:800;letter-spacing:-.02em;'
             'color:var(--mr-heading);margin:0 0 14px') if n == 0 else ''
    prose.append('<%s%s>%s</%s>' % (tag, ' style="%s"' % style if style else '', esc(sec['h']), tag))
    prose += ['<p>%s</p>' % esc(p) for p in sec['p']]
    if sec['li']:
        prose.append('<ul>' + ''.join('<li>%s</li>' % esc(x) for x in sec['li']) + '</ul>')
i = src.index('<div class="seo-prose mr-section"')
i = src.index('>', i) + 1
j = src.index('\n</div>\n\n<div class="mr-section"', i)
src = src[:i] + '\n' + '\n'.join(prose) + src[j:]

# ══ 5. Link blocks — real hospitals / conditions / cities ════════════════
def block(title, rows):
    lis = ''.join('<li><a href="%s">%s</a></li>' % (r['href'], esc(r['text'])) for r in rows)
    return ('<div>\n<h2 style="font-size:20px;font-weight:700;color:var(--mr-heading);margin:0 0 14px">'
            '%s</h2>\n<ul class="linklist">%s</ul>\n</div>' % (esc(title), lis))
blocks = '\n'.join(block(k, v) for k, v in D['linkBlocks'].items())
i = src.index('<div class="mr-section" style="max-width:1200px;margin:0 auto;padding:48px 32px 0;'
              'display:flex;flex-direction:column;gap:36px">')
i = src.index('>', i) + 1
j = src.index('\n</div>\n\n<footer', i)
src = src[:i] + '\n' + blocks + src[j:]

# ══ 6. Component data — real doctors, FAQs, concerns ═════════════════════
def jsobj(d, keys):
    return '{ ' + ', '.join('%s: %s' % (k, json.dumps(d[k], ensure_ascii=False)) for k in keys) + ' }'

TINTS = ['var(--mr-error-bg)', 'var(--mr-medium-bg)', 'var(--mr-success-bg)',
         'var(--mr-primary-25)', '#FDF6E3', '#E9F8FA', 'var(--mr-warning-bg)']
concerns = []
for n, d in enumerate(D['linkBlocks']['Dermatologist Related Diseases']):
    label = d['text'].replace('Best ', '').replace(' Doctor in Pakistan', '')
    concerns.append({'label': label, 'href': d['href'],
                     'slot': 'c-' + re.sub(r'\W+', '-', label.lower()), 'tint': TINTS[n % len(TINTS)]})

docs = []
for d in D['doctors']:
    docs.append({'name': d['name'], 'url': d['url'], 'photo': d['photo'], 'city': d['city'],
                 'specialty': d['specialty'] or 'Dermatologist',
                 'experience': d['experience'] or '', 'reviews': d['reviews'] or '0',
                 'satisfaction': d['satisfaction'] or '', 'hasVideo': bool(d['hasVideo']),
                 'feeLine': ('Fee from Rs. %s' % format(d['minFee'], ',')) if d['minFee'] else '',
                 'services': d['services']})

data_js = (
'      concerns: %s,\n\n'
'      crumbLast: "Dermatologist in Pakistan",\n'
'      listHeading: "%s Best Dermatologists in Pakistan",\n'
'      listSubline: "All %s dermatologists listed on Marham, sorted by patient satisfaction.",\n'
'      hasConcern: false,\n'
'      onClearConcern: () => {},\n\n'
'      doctors: %s,\n\n'
'      faqs: %s\n'
) % (
    json.dumps(concerns, indent=8, ensure_ascii=False),
    TOTAL, TOTAL,
    json.dumps(docs, indent=8, ensure_ascii=False),
    json.dumps([{'q': f['q'], 'a': f['a'], 'hasList': bool(f['list']), 'list': f['list']}
                for f in D['faqs']], indent=8, ensure_ascii=False),
)

i = src.index('      concerns: this.concernData().map')
j = src.index('    });', i)
src = src[:i] + data_js + src[j:]
# concernData()/stories/testimonials arrays are now unreferenced
src = re.sub(r'  concernData\(\) \{.*?\n  \}\n\n', '', src, flags=re.S)
src = re.sub(r'\n    out\.concernDoctors = sel.*?: \[\];\n', '\n    out.concernDoctors = [];\n', src, flags=re.S)
# renderVals() opened by deriving state from concernData()/matchData, all of which
# the real-data arrays above replace. Strip that dead preamble or the call throws.
i = src.index('  renderVals() {')
j = src.index('    const out = {};', i)
src = src[:i] + """  renderVals() {
    const s = this.state;
    const mkFilter = (label) => {
      const on = !!s.filters[label];
      return Object.assign(
        { label, onClick: () => this.setState(p => ({ filters: Object.assign({}, p.filters, { [label]: !on }) })) },
        this.chip(label, on));
    };

""" + src[j:]

# designer's note must describe what the page now actually is
sub('The page now opens straight on the skin-concern tile row, which filters into real Marham '
    'disease pages, plus before/after results and verified patient reviews.',
    'Real listing data pulled from marham.pk/doctors/dermatologist on 22 Sep 2026: %d doctors with '
    'live photos, fees and profile links, %d FAQs, %d link blocks and the page&#39;s own SEO copy.'
    % (len(docs), len(D['faqs']), len(D['linkBlocks'])))
sub('Every doctor card, filter, About/FAQ word and link block below is unchanged — no SEO surface '
    'was cut or collapsed.',
    'Every FAQ, About paragraph and link block is the live page&#39;s own wording, copied verbatim.')
sub("skinnsi's fixed-price packages and trial offers. Marham brokers independent doctors, so the "
    'page sells consults, fees and discounts you can actually honour.',
    'Before/after photos and patient review quotes — the live page publishes neither, so those '
    'sections were removed rather than filled with invented content.')

io.open('redesign_real.html', 'w', encoding='utf-8').write(src)
print('built  %d bytes   doctors=%d  faqs=%d  concerns=%d  prose=%d'
      % (len(src), len(docs), len(D['faqs']), len(concerns), len(D['prose'])))
