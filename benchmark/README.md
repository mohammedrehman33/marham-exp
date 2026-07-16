# Benchmark — karachi-gp treatment

`karachi-gp.benchmark.html` is the frozen reference of the approved page
treatment (as of PR #4). Every new page gets EXACTLY this treatment via
one command:

```
python3 tools/apply_benchmark.py \
    --in NEW-PAGE.html --out NEW-PAGE.html \
    --doctors tools/doctors_<page>.json \
    --utm-source <page_slug>_page \
    --female-ids "id1,id2,..."
```

## The treatment (checklist)

1. **Call-My-Doctors section** (inserted before `<!--Doctors-->`)
   - Heading: `Consult a Specialist for as Low as Rs. <lowest fee>`
   - Red badge in Urdu: `7 دن تک ڈاکٹر سے مرہم ایپ سے مفت رہنمائی حاصل کریں`
     with Lucide stethoscope icon + slow glossy shimmer (4.5s)
   - Note: "Book online consultation — limited-time offer, ends soon!"
   - 3 doctor cards, full-width flex, circular photos, "Available Today"
   - Book CTAs UTM-tagged: `utm_source=<page>_page`,
     `utm_medium=cmd_section`, `utm_campaign=call_my_doctors`,
     `utm_content=<doctor-slug>`
2. **Search bar removed → working filter chips** (border `#004d71`,
   small/light: 13px, weight 400)
   - Female Doctors / Most Experienced / Lowest Fee / Highest Rated /
     Available Today / Video Consultation + dashed "✕ Clear All"
     (visible only while something is active)
   - Client-side, sorts globally across both listing containers
3. **Sticky "Show Doctors" button** — bottom-right, compact, `#004d71`,
   appears when `.seo-page-content` enters the viewport, smooth-scrolls
   back to the listing

## Per-page inputs needed from content team

- The saved page HTML
- 3 doctors (name, profile link, photo URL, reviews, exp yrs, fee, book link)
- Which listed doctors are female (ids) — for the Female Doctors filter
- utm_source slug (defaults to the page name)

## New page steps

1. Save doctors JSON as `tools/doctors_<page>.json`
   (same shape as `tools/doctors_gp_karachi.json`)
2. Run the command above
3. Verify in a browser: section renders, chips filter/sort, button
   appears at the SEO content block
