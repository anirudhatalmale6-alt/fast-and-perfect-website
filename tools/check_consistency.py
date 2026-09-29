#!/usr/bin/env python3
"""Site-wide consistency check.

Catches copy that contradicts the confirmed package structure, stale contact
details, and claims that are supposed to be switched off. Run after any
content change:

    python3 tools/check_consistency.py
"""
import json
import os
import re
import sys
from html import unescape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
PRICING = json.load(open(os.path.join(SITE, "assets/data/pricing.json"), encoding="utf-8"))

# Confirmed business details — the single source for these checks.
PHONE_DISPLAY = "(587) 338-0069"
PHONE_HREF = "+15873380069"
EMAIL = "info@fastandperfect.ca"

failures = []
def fail(page, msg):
    failures.append(f"{page}: {msg}")


def visible_text(html):
    """Strip scripts/styles/tags so we test what a customer actually reads."""
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(html))


pages = sorted(f for f in os.listdir(SITE) if f.endswith(".html"))

# ---------------------------------------------------------------- 1. stale details
STALE = {
    "555-0142": "old placeholder phone number",
    "hello@fastandperfect": "old placeholder email",
    "780-555": "old placeholder phone number",
    "8am–7pm": "old business hours",
    "8:00 am – 7:00 pm": "old business hours",
    "9:00 am – 5:00 pm": "old Saturday hours",
    "By appointment": "old Sunday hours",
}

# ------------------------------------------------- 2. package-structure contradictions
# Things that must NEVER be described as included in a package, because the
# owner has confirmed they are paid add-ons on every package.
ALWAYS_PAID = ["fridge", "oven", "interior window"]
INCLUSION_WORDS = r"(include[sd]?|covers?|comes with|part of|bundled)"

# Work that belongs to deep cleaning only, so it must not be promised as
# something done on every visit.
DEEP_ONLY = ["baseboard", "door frame", "light switch"]
EVERY_VISIT = r"(every visit|every clean|each visit|always included|as standard)"

# Claims that are switched off until the owner confirms them.
DISABLED_CLAIMS = [
    (r"\binsured\b", "insurance claim"),
    (r"\bbonded\b", "bonding claim"),
    (r"\bWCB\b", "WCB claim"),
    (r"police[- ]check", "background-check claim"),
    (r"criminal[- ]record", "background-check claim"),
    (r"background[- ]check", "background-check claim"),
    (r"satisfaction guarantee", "guarantee claim"),
    (r"re-clean guarantee", "guarantee claim"),
]

for page in pages:
    html = open(os.path.join(SITE, page), encoding="utf-8").read()
    text = visible_text(html)
    low = text.lower()

    for needle, why in STALE.items():
        if needle.lower() in low:
            fail(page, f"{why} still present ({needle!r})")

    # an always-paid add-on described as included
    for item in ALWAYS_PAID:
        for m in re.finditer(item, low):
            window = low[max(0, m.start() - 90): m.start() + 60]
            if re.search(INCLUSION_WORDS, window) and "add-on" not in window \
               and "optional" not in window and "paid" not in window:
                fail(page, f"'{item}' appears near inclusion wording: "
                           f"...{window.strip()[-110:]}...")

    # deep-clean-only work promised on every visit
    for item in DEEP_ONLY:
        for m in re.finditer(item, low):
            window = low[max(0, m.start() - 110): m.start() + 110]
            if re.search(EVERY_VISIT, window):
                fail(page, f"'{item}' described as every-visit work: "
                           f"...{window.strip()[:130]}...")

    for pattern, why in DISABLED_CLAIMS:
        for m in re.finditer(pattern, text, re.I):
            window = text[max(0, m.start() - 60): m.start() + 60]
            # "not a guaranteed final price" is a disclaimer, not a claim
            if "guaranteed final price" in window.lower():
                continue
            fail(page, f"disabled {why} present: ...{window.strip()}...")

    # ------------------------------------------------ 3. contact details consistency
    if page not in ("404.html",):
        if "tel:" in html and PHONE_HREF not in html:
            fail(page, "has a tel: link that is not the confirmed number")
        if re.search(r"mailto:", html) and EMAIL not in html:
            fail(page, "has a mailto: link that is not the confirmed address")

# ---------------------------------------------------------- 4. prices trace to pricing.json
allowed = {0}
for t in PRICING["residential"]["tiers"]:
    for k in ("regular", "deep", "moveinout"):
        allowed.add(t[k])
for a in PRICING["residential"]["addons"]:
    allowed.add(a["price"])
for b in PRICING["commercial"]["bands"]:
    allowed.add(b["price"])
for v in PRICING["carpet"]["room_tiers"]:
    allowed.add(v)
for k in ("additional_room", "hallway", "stairs_base", "additional_step"):
    allowed.add(PRICING["carpet"][k])
for i in PRICING["items"]:
    allowed.add(i["price"])
for t in PRICING["treatments"]:
    allowed.add(t["min"]); allowed.add(t["max"])
allowed.add(PRICING["minimum_service_charge"])
allowed.add(PRICING["max_room_sqft"])

for page in pages:
    html = re.sub(r"<script.*?</script>", " ",
                  open(os.path.join(SITE, page), encoding="utf-8").read(), flags=re.S)
    found = {int(m.replace(",", "")) for m in re.findall(r"\$([0-9][0-9,]*)", html)}
    for extra in sorted(found - allowed):
        fail(page, f"price ${extra} does not appear in pricing.json")

# ------------------------------------------------- 5. commercial bands must be published
comm_html = open(os.path.join(SITE, "commercial-cleaning.html"), encoding="utf-8").read()
for band in PRICING["commercial"]["bands"]:
    if f"${band['price']:,}" not in comm_html and f"${band['price']}" not in comm_html:
        fail("commercial-cleaning.html", f"band {band['label']} (${band['price']}) not published")
if PRICING["commercial"]["over_band_label"] not in comm_html:
    fail("commercial-cleaning.html", "the 'over 5,000 sq ft' row is missing")
for t in PRICING["commercial"]["custom_types"]:
    if t not in comm_html:
        fail("commercial-cleaning.html", f"custom-quote type '{t}' not listed")

print("=" * 70)
if failures:
    print(f"CONSISTENCY: {len(failures)} problem(s)\n")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"CONSISTENCY: clean across {len(pages)} pages")
print("  no stale contact details")
print("  no always-paid add-on described as included")
print("  no deep-clean-only work promised on every visit")
print("  no disabled claims (insured / bonded / WCB / background checks / guarantee)")
print("  every published price traces to pricing.json")
print("  all commercial bands and custom-quote types published")
