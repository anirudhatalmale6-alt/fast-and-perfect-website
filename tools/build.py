#!/usr/bin/env python3
"""
Static site builder for Fast and Perfect Ltd.

Everything the owner is likely to change lives in the BUSINESS dict below.
Change it once, run `python3 tools/build.py`, and every page updates:
phone number, email, hours, service areas, social links, domain.

Output is plain HTML in site/ — no server, no database, no framework.
Any host that serves files will run it.
"""
import html
import json
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")

# ============================================================================
#  BUSINESS DETAILS  — edit these, rebuild, done.
#  Values marked PLACEHOLDER must be replaced before the site goes live.
# ============================================================================
BUSINESS = {
    "name": "Fast and Perfect",
    "legal_name": "Fast and Perfect Ltd.",
    "tagline": "Cleaning Services",
    "phone_display": "(780) 555-0142",          # PLACEHOLDER
    "phone_href": "+17805550142",               # PLACEHOLDER
    "email": "hello@fastandperfect.ca",         # PLACEHOLDER (needs the domain first)
    "domain": "https://fastandperfect.ca",      # PLACEHOLDER (pending registration)
    "city": "Edmonton",
    "region": "AB",
    "region_full": "Alberta",
    "country": "CA",
    "postal_hint": "T5J",
    "lat": "53.5461",
    "lng": "-113.4938",
    "hours": [
        ("Monday – Friday", "8:00 am – 7:00 pm"),
        ("Saturday", "9:00 am – 5:00 pm"),
        ("Sunday", "By appointment"),
    ],
    "hours_schema": [
        (["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "08:00", "19:00"),
        (["Saturday"], "09:00", "17:00"),
    ],
    # Edmonton is the primary market — it leads every page, carries the
    # keyword weight, and is the geographic target for Google Ads and SEO.
    # The rest are secondary service areas.
    "primary_area": "Edmonton",
    "secondary_areas": [
        "St. Albert", "Sherwood Park", "Spruce Grove", "Stony Plain", "Leduc",
        "Beaumont", "Fort Saskatchewan", "Nisku", "Devon", "Acheson",
        "Morinville", "Ardrossan", "Gibbons", "Legal", "Bon Accord", "Calmar",
        "Thorsby", "Millet", "New Sarepta",
    ],
    "neighbourhoods": [
        "Downtown", "Oliver", "Windermere", "Terwillegar", "Summerside",
        "Griesbach", "Glenora", "Strathcona", "Mill Woods", "The Hamptons",
        "Riverbend", "Castle Downs",
    ],
    "social": {
        "facebook": "#",     # PLACEHOLDER — paste the page URL once created
        "instagram": "#",    # PLACEHOLDER
        "tiktok": "#",       # PLACEHOLDER
        "google": "#",       # PLACEHOLDER — Google Business Profile
    },
}

BUSINESS["areas"] = [BUSINESS["primary_area"]] + BUSINESS["secondary_areas"]

# ============================================================================
#  UNVERIFIED CLAIMS GATE
#
#  The owner has not yet confirmed any of the following, so NONE of it appears
#  on the site. Every block below is suppressed at build time while the value
#  is False/None — no ratings, no review quotes, no insurance or bonding
#  claims, no guarantees, no staff-screening claims, no pricing.
#
#  To switch one back on: set it to the real, confirmed value and rebuild.
#  Do not enable anything the owner has not explicitly confirmed in writing.
# ============================================================================
CLAIMS = {
    "insured": False,          # set True only once a policy is confirmed
    "bonded": False,
    "wcb_covered": False,
    "police_checks": False,    # staff criminal-record checks
    "guarantee_hours": None,   # e.g. 24 — the re-clean guarantee window
    "rating": None,            # e.g. "4.9" — only from a real review profile
    "review_count": None,      # e.g. 87
    "eco_products": False,     # pet/child-safe product claim
    "same_crew": False,        # "same cleaners every visit"
    "supplies_included": False,
    "years_in_business": None,

    # Pricing is gated per service, because the owner has confirmed his
    # carpet & upholstery rates but not his residential/commercial ones.
    "show_prices": False,         # residential + commercial (NOT confirmed)
    "show_prices_carpet": True,   # confirmed in writing, see pricing.json
}

# Carpet & upholstery prices live in one JSON file so the owner can change
# them without touching any HTML or rebuilding. Both the calculator and the
# published rate table read from it.
PRICING_PATH = os.path.join(ROOT, "site", "assets", "data", "pricing.json")
with open(PRICING_PATH, encoding="utf-8") as _fh:
    PRICING = json.load(_fh)

# Real customer reviews only. Leave empty until the owner supplies them —
# invented reviews breach Google and Meta policy and are grounds for a
# listing suspension.
TESTIMONIALS = []

B = BUSINESS
TEL = B["phone_href"]
PHONE = B["phone_display"]


def claim(key):
    """True when the owner has confirmed this claim and it may be published."""
    return bool(CLAIMS.get(key))


# Recurring-discount percentages are a pricing claim, so they only appear
# on the frequency chips once pricing is confirmed.
DISCOUNT_TAG = (
    ['<span class="tag">-10%</span>', '<span class="tag">-15%</span>',
     '<span class="tag">-20%</span>']
    if CLAIMS.get("show_prices") else ["", "", ""]
)


# ---------------------------------------------------------------- icons
def icon(name, size=18, stroke=2):
    p = {
        "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
        "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
        "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
        "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
        "check": '<path d="M20 6 9 17l-5-5"/>',
        "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
        "star": '<path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor" stroke="none"/>',
        "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
        "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
        "sparkle": '<path d="M12 3c.6 4.2 2.8 6.4 7 7-4.2.6-6.4 2.8-7 7-.6-4.2-2.8-6.4-7-7 4.2-.6 6.4-2.8 7-7z"/>',
        "leaf": '<path d="M11 20A7 7 0 0 1 4 13c0-6 7-10 16-10 0 9-4 16-9 17z"/><path d="M8 16c2-4 5-6 9-7"/>',
        "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "wallet": '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5"/><circle cx="17" cy="13" r="1.4" fill="currentColor" stroke="none"/>',
        "repeat": '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
        "chevrons": '<path d="m9 7-5 5 5 5"/><path d="m15 7 5 5-5 5"/>',
        "caret": '<path d="m6 9 6 6 6-6"/>',
        "facebook": '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
        "instagram": '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/>',
        "tiktok": '<path d="M16 3v10.5a4.5 4.5 0 1 1-4-4.47"/><path d="M16 3c.4 2.6 2 4.2 5 4.5"/>',
        "google": '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
    }[name]
    fill = "none"
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{p}</svg>'
    )


# ---------------------------------------------------------------- nav data
SERVICES = [
    ("residential-cleaning.html", "Residential Cleaning"),
    ("commercial-cleaning.html", "Commercial Cleaning"),
    ("carpet-cleaning.html", "Carpet &amp; Upholstery"),
]

NAV = [
    ("index.html", "Home"),
    (None, "Services"),
    ("gallery.html", "Our Work"),
    ("service-areas.html", "Areas Served"),
    ("about.html", "About"),
    ("contact.html", "Contact"),
]


def nav_html(current):
    out = []
    for href, label in NAV:
        if href is None:
            sub = "".join(
                f'<a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{t}</a>'
                for h, t in SERVICES
            )
            active = ' aria-current="page"' if current in [h for h, _ in SERVICES] else ""
            out.append(
                f'<div class="nav__group"><a href="residential-cleaning.html"{active}>'
                f"{label} {icon('caret', 14, 2.4)}</a>"
                f'<div class="nav__panel">{sub}</div></div>'
            )
        else:
            cur = ' aria-current="page"' if href == current else ""
            out.append(f'<a href="{href}"{cur}>{label}</a>')
    return "".join(out)


def drawer_html(current):
    out = []
    for href, label in NAV:
        if href is None:
            out.append(f"<a href=\"residential-cleaning.html\">{label}</a>")
            for h, t in SERVICES:
                out.append(f'<a class="sub" href="{h}">{t}</a>')
        else:
            out.append(f'<a href="{href}">{label}</a>')
    return "".join(out)


BRAND = (
    '<a class="brand" href="index.html" aria-label="{legal} home">'
    '<img class="brand__mark" src="assets/img/logo-mark.svg" alt="" width="40" height="40">'
    '<span class="brand__text"><span class="brand__name">{name}</span>'
    '<span class="brand__tag">{tag}</span></span></a>'
).format(legal=B["legal_name"], name=B["name"], tag=B["tagline"] + " · " + B["city"])


def header(current):
    return f"""
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="shell shell--wide header-inner">
    {BRAND}
    <nav class="nav" aria-label="Primary">{nav_html(current)}</nav>
    <div class="header-cta">
      <a class="header-phone" href="tel:{TEL}">{icon('phone', 16)} {PHONE}</a>
      <a class="btn btn--gold" href="quote.html">Free Quote</a>
      <button class="burger" type="button" aria-expanded="false" aria-controls="drawer" aria-label="Open menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer">
  {drawer_html(current)}
  <div class="drawer__actions">
    <a class="btn btn--gold btn--block" href="quote.html">Get a free quote</a>
    <a class="btn btn--ghost btn--block" href="tel:{TEL}">{icon('phone', 16)} Call {PHONE}</a>
  </div>
</div>
"""


def footer():
    area_links = "".join(
        f"<li><a href=\"service-areas.html\">{a}</a></li>" for a in B["areas"][:8]
    )
    svc_links = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in SERVICES)
    soc = B["social"]
    return f"""
<footer class="site-footer">
  <div class="shell shell--wide">
    <div class="footer-grid">
      <div>
        {BRAND}
        <p class="footer-about">Locally owned cleaning company serving {B['city']} as our
        primary service area, plus {len(B['secondary_areas'])} surrounding communities
        across the Edmonton region. Residential, commercial and carpet cleaning.</p>
        <div class="socials">
          <a href="{soc['facebook']}" aria-label="Facebook">{icon('facebook', 18)}</a>
          <a href="{soc['instagram']}" aria-label="Instagram">{icon('instagram', 18)}</a>
          <a href="{soc['tiktok']}" aria-label="TikTok">{icon('tiktok', 18)}</a>
          <a href="{soc['google']}" aria-label="Google Business Profile">{icon('google', 18)}</a>
        </div>
      </div>
      <div>
        <div class="footer-h">Services</div>
        <ul class="footer-list">{svc_links}
          <li><a href="quote.html">Free Quote</a></li>
          <li><a href="book.html">Book Online</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-h">Areas Served</div>
        <ul class="footer-list">{area_links}</ul>
      </div>
      <div>
        <div class="footer-h">Get in Touch</div>
        <div class="footer-contact">
          <a href="tel:{TEL}">{icon('phone', 15)} {PHONE}</a>
          <a href="mailto:{B['email']}">{icon('mail', 15)} {B['email']}</a>
          <div>{icon('pin', 15)} Serving {B['city']}, {B['region']} &amp; area</div>
          <div>{icon('clock', 15)} Mon–Fri 8am–7pm · Sat 9am–5pm</div>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <div>&copy; <span data-year>2026</span> {B['legal_name']}. All rights reserved.</div>
      <nav aria-label="Footer">
        <a href="privacy.html">Privacy Policy</a>
        <a href="contact.html">Contact</a>
        <a href="book.html">Book Online</a>
      </nav>
    </div>
  </div>
</footer>
<div class="callbar">
  <a href="tel:{TEL}">{icon('phone', 17)} Call Now</a>
  <a href="quote.html">{icon('sparkle', 17)} Free Quote</a>
</div>
"""


# ---------------------------------------------------------------- schema
def local_business_schema():
    hours = [
        {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": days,
            "opens": o,
            "closes": c,
        }
        for days, o, c in B["hours_schema"]
    ]
    return {
        "@context": "https://schema.org",
        "@type": "HouseCleaningService",
        "@id": B["domain"] + "/#business",
        "name": B["legal_name"],
        "alternateName": B["name"],
        "url": B["domain"] + "/",
        "telephone": "+1-780-555-0142",
        "email": B["email"],
        "image": B["domain"] + "/assets/img/og-cover.svg",
        "logo": B["domain"] + "/assets/img/logo-mark.svg",
        # priceRange and paymentAccepted are business claims — Google reads and
        # displays them, so they stay out until the owner confirms both.
        **({"priceRange": "$$",
            "currenciesAccepted": "CAD",
            "paymentAccepted": "Cash, Debit, Credit Card, e-Transfer"}
           if claim("show_prices") else {}),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": B["city"],
            "addressRegion": B["region"],
            "addressCountry": B["country"],
        },
        "geo": {"@type": "GeoCoordinates", "latitude": B["lat"], "longitude": B["lng"]},
        "areaServed": [{"@type": "City", "name": a} for a in B["areas"]],
        "openingHoursSpecification": hours,
        "sameAs": [v for v in B["social"].values() if v != "#"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Cleaning Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {"@type": "Service", "name": n},
                }
                for n in [
                    "Residential House Cleaning",
                    "Deep Cleaning",
                    "Move-In / Move-Out Cleaning",
                    "Commercial & Office Cleaning",
                    "Carpet & Upholstery Cleaning",
                ]
            ],
        },
    }


def breadcrumbs(items):
    """items: [(name, url_or_None)] — last item is the current page."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                **({"item": B["domain"] + "/" + url} if url else {}),
            }
            for i, (name, url) in enumerate(items)
        ],
    }


def faq_schema(pairs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)},
            }
            for q, a in pairs
        ],
    }


def service_schema(name, desc, low, high, unit="visit", enabled=None):
    schema = {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": name,
        "provider": {"@id": B["domain"] + "/#business"},
        "areaServed": [{"@type": "City", "name": a} for a in B["areas"]],
        "description": desc,
    }
    # A price in structured data is still a published price — Google surfaces
    # it in search results. Gated per service.
    if enabled is None:
        enabled = claim("show_prices")
    if enabled:
        schema["offers"] = {
            "@type": "AggregateOffer",
            "priceCurrency": "CAD",
            "lowPrice": str(low),
        }
        # Only claim an upper bound when there genuinely is one.
        if high is not None:
            schema["offers"]["highPrice"] = str(high)
    return schema


# ---------------------------------------------------------------- shell
def page(slug, title, description, body, schemas=None, current=None, keywords=None,
         extra_js=None, noindex=False, bare=False):
    current = current or slug
    schemas = schemas or []
    extra = "".join(f'<script src="{s}" defer></script>' for s in (extra_js or []))
    blocks = "".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>'
        for s in schemas
    )
    canonical = B["domain"] + "/" + ("" if slug == "index.html" else slug)
    robots = ("noindex, nofollow" if noindex
              else "index, follow, max-image-preview:large")
    kw = f'<meta name="keywords" content="{keywords}">' if keywords else ""
    doc = f"""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
{kw}
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#1c4b3a">
<meta name="geo.region" content="CA-AB">
<meta name="geo.placename" content="{B['city']}">
<meta name="geo.position" content="{B['lat']};{B['lng']}">
<meta name="ICBM" content="{B['lat']}, {B['lng']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{B['legal_name']}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="en_CA">
<meta property="og:image" content="{B['domain']}/assets/img/og-cover.svg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{B['domain']}/assets/img/og-cover.svg">
<link rel="icon" href="assets/img/logo-mark.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/img/logo-mark.svg">
<link rel="preload" href="assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/karla-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/main.css">
{blocks}
</head>
<body>
{header(current)}
<main id="main">
{body}
</main>
{footer()}
<script src="assets/js/main.js" defer></script>{extra}
</body>
</html>
"""
    with open(os.path.join(SITE, slug), "w", encoding="utf-8") as fh:
        fh.write(doc)
    return slug


# ---------------------------------------------------------------- partials
def page_head(eyebrow, h1, lede, crumbs_items):
    crumbs = "".join(
        f'<li><a href="{u}">{n}</a></li>' if u else f"<li>{n}</li>"
        for n, u in crumbs_items
    )
    return f"""
<section class="page-head">
  <div class="shell">
    <ul class="crumbs">{crumbs}</ul>
    <span class="eyebrow">{eyebrow}</span>
    <h1 class="h-lg">{h1}</h1>
    <p class="lede">{lede}</p>
  </div>
</section>
"""


def hero_float_cards():
    """The rating card only exists if there is a real rating; the price card
    only exists if prices are confirmed. Otherwise both are replaced with
    statements of fact about the service itself."""
    cards = []
    if CLAIMS.get("rating"):
        sub = (f"from {CLAIMS['review_count']} reviews"
               if CLAIMS.get("review_count") else "from local reviews")
        cards.append(f"""
      <div class="float-card float-card--rating">
        <span class="stars" aria-hidden="true">{''.join(icon('star', 14) for _ in range(5))}</span>
        <span><span class="rating-num">{CLAIMS['rating']}</span>
        <span class="rating-sub">{sub}</span></span>
      </div>""")
    else:
        cards.append(f"""
      <div class="float-card float-card--rating">
        <span class="stars" aria-hidden="true" style="color:var(--pine)">{icon('sparkle', 20)}</span>
        <span><span class="rating-num">3</span>
        <span class="rating-sub">services, one local team</span></span>
      </div>""")

    if claim("show_prices"):
        cards.append("""
      <div class="float-card float-card--quote">
        <span class="fc-label">3 bed / 2 bath</span>
        <div class="fc-price">$165</div>
        <p class="fc-note">Typical recurring clean in Edmonton — quoted in writing.</p>
      </div>""")
    else:
        cards.append(f"""
      <div class="float-card float-card--quote">
        <span class="fc-label">Free quote</span>
        <div class="fc-price">1 call</div>
        <p class="fc-note">Tell us about your space and we'll come back with a price
        in writing. No obligation.</p>
      </div>""")
    return "".join(cards)


def cta_band(title=None, text=None):
    title = title or 'Ready for a place that <span class="tilt--gold">actually</span> feels clean?'
    text = text or (
        "Tell us about your space and we'll send a firm, itemised quote — "
        "as quickly as we can. No pressure, no obligation."
    )
    return f"""
<section class="section band cta-band">
  <div class="shell">
    <span class="eyebrow eyebrow--light eyebrow--center">Get started</span>
    <h2 class="h-lg">{title}</h2>
    <p class="lede">{text}</p>
    <div class="cta-band__actions">
      <a class="btn btn--gold btn--lg" href="quote.html">{icon('sparkle', 17)} Get my free quote</a>
      <a class="btn btn--outline-light btn--lg" href="tel:{TEL}">{icon('phone', 17)} {PHONE}</a>
    </div>
  </div>
</section>
"""


def trust_strip():
    """Only claims the owner has confirmed. Facts about how we operate —
    not credentials — are safe to state; everything else is gated."""
    items = [
        ("pin", f"{B['primary_area']} &amp; surrounding areas"),
        ("clock", "Free quotes, no obligation"),
        ("users", "Locally owned and operated"),
    ]
    if claim("insured") and claim("bonded"):
        items.insert(0, ("shield", "Insured &amp; bonded"))
    elif claim("insured"):
        items.insert(0, ("shield", "Fully insured"))
    if claim("police_checks"):
        items.append(("check", "Police-checked cleaners"))
    if claim("eco_products"):
        items.append(("leaf", "Pet &amp; child-safe products"))
    if CLAIMS.get("guarantee_hours"):
        items.append(("repeat", f"{CLAIMS['guarantee_hours']}-hour re-clean guarantee"))
    lis = "".join(f"<li>{icon(i, 17)} {t}</li>" for i, t in items[:4])
    return f'<ul class="trust-row">{lis}</ul>'


def estimator_block(form_id="estimator-form", with_cta=True):
    services = [
        ("residential", "Regular house clean", ""),
        ("deep", "Deep clean", ""),
        ("moveinout", "Move in / move out", ""),
        ("carpet", "Carpet cleaning", ""),
        ("commercial", "Commercial / office", ""),
    ]
    svc = "".join(
        f'<input type="radio" name="service" id="svc-{v}" value="{v}"'
        f'{" checked" if i == 0 else ""}><label for="svc-{v}">{l}{t}</label>'
        for i, (v, l, t) in enumerate(services)
    )
    freqs = [
        ("onetime", "One-time", ""),
        ("monthly", "Monthly", DISCOUNT_TAG[0]),
        ("biweekly", "Every 2 weeks", DISCOUNT_TAG[1]),
        ("weekly", "Weekly", DISCOUNT_TAG[2]),
    ]
    frq = "".join(
        f'<input type="radio" name="frequency" id="frq-{v}" value="{v}"'
        f'{" checked" if i == 0 else ""}><label for="frq-{v}">{l}{t}</label>'
        for i, (v, l, t) in enumerate(freqs)
    )
    extras = [
        ("fridge", "Inside fridge", 35), ("oven", "Inside oven", 35),
        ("windows", "Interior windows", 55), ("laundry", "Laundry", 25),
        ("garage", "Garage", 45), ("basement", "Finished basement", 40),
    ]
    ext = "".join(
        f'<input type="checkbox" name="extras" id="ex-{v}" value="{v}">'
        f'<label for="ex-{v}">{l}'
        + (f' <span class="tag">+${p}</span>' if claim("show_prices") else "")
        + "</label>"
        for v, l, p in extras
    )
    cta = (
        f'<button class="btn btn--gold btn--block" type="button" id="est-continue">'
        f"Send me this quote {icon('arrow', 16)}</button>"
        if with_cta else
        f'<a class="btn btn--gold btn--block" href="quote.html">Send me this quote {icon("arrow", 16)}</a>'
    )

    # Until the owner confirms his rates, the calculator collects the job
    # details but publishes no dollar figure.
    if claim("show_prices"):
        result_body = f"""
    <span class="est-result__label">Your estimated price</span>
    <div class="est-price" id="est-price">$0</div>
    <p class="est-sub" id="est-sub"></p>
    <ul class="est-break" id="est-breakdown"></ul>
    {cta}
    <p class="est-foot">Instant estimate only. We confirm the final price in writing
    before any work starts.</p>"""
    else:
        result_body = f"""
    <span class="est-result__label">Your quote</span>
    <div class="est-price" id="est-price-static">Priced<small>per job</small></div>
    <p class="est-sub">Every space is different, so we price yours properly rather
    than guessing. Send these details through and we'll come back with a written
    quote.</p>
    <ul class="est-break" id="est-breakdown"></ul>
    {cta}
    <p class="est-foot">No obligation, and no charge for the quote.</p>"""

    prices_attr = "" if claim("show_prices") else ' data-prices="off"'
    # Carpet & upholstery has its own calculator with confirmed prices, so
    # point people at it rather than pricing carpets by bedroom count here.
    carpet_hint = (
        f"""
    <div class="form-note mt-2" id="carpet-redirect" hidden>{icon('sparkle', 17)}
      <span>Carpets and upholstery have their own calculator, priced by room,
      staircase and furniture item — with live estimates.
      <a href="carpet-cleaning.html#calculator"><b>Open the carpet &amp;
      upholstery calculator</b></a>.</span></div>"""
        if claim("show_prices_carpet") else ""
    )
    return f"""
<div class="estimator">
  <form class="est-panel" id="{form_id}"{prices_attr} novalidate>
    <div class="field field--full">
      <span class="field-label">What do you need cleaned?</span>
      <div class="choice">{svc}</div>{carpet_hint}
    </div>
    <div class="field-grid mt-2">
      <div class="field">
        <span class="field-label">Bedrooms</span>
        <div class="stepper" data-stepper data-min="0" data-max="10">
          <button type="button" data-step="down" aria-label="Fewer bedrooms">&minus;</button>
          <output>3</output>
          <input type="hidden" name="bedrooms" value="3">
          <button type="button" data-step="up" aria-label="More bedrooms">+</button>
        </div>
      </div>
      <div class="field">
        <span class="field-label">Bathrooms</span>
        <div class="stepper" data-stepper data-min="0" data-max="10">
          <button type="button" data-step="down" aria-label="Fewer bathrooms">&minus;</button>
          <output>2</output>
          <input type="hidden" name="bathrooms" value="2">
          <button type="button" data-step="up" aria-label="More bathrooms">+</button>
        </div>
      </div>
      <div class="field field--full">
        <label for="sqft-{form_id}">Approximate size (sq ft) <span class="field-hint">— optional</span></label>
        <input type="number" id="sqft-{form_id}" name="sqft" min="0" max="20000" step="50" placeholder="e.g. 1600" inputmode="numeric">
      </div>
    </div>
    <div class="field field--full mt-2">
      <span class="field-label">How often?</span>
      <div class="choice">{frq}</div>
    </div>
    <div class="field field--full mt-2">
      <span class="field-label">Add-ons</span>
      <div class="choice">{ext}</div>
    </div>
  </form>

  <aside class="est-result">{result_body}
  </aside>
</div>
"""


def quote_form(form_id="quote-form", heading=True):
    head = (
        '<span class="eyebrow">Request a quote</span>'
        '<h2 class="h-md">Tell us about your space</h2>'
        '<p class="lede mt-1">Tell us what you need and we\'ll get back to you with a price.</p>'
        if heading else ""
    )
    return f"""
<form class="est-panel" id="{form_id}" data-form novalidate>
  {head}
  <div class="field-grid mt-2">
    <div class="field">
      <label for="q-name">Your name *</label>
      <input type="text" id="q-name" name="name" required autocomplete="name" placeholder="Jane Doe">
    </div>
    <div class="field">
      <label for="q-phone">Phone *</label>
      <input type="tel" id="q-phone" name="phone" required autocomplete="tel" placeholder="(780) 000-0000">
    </div>
    <div class="field">
      <label for="q-email">Email *</label>
      <input type="email" id="q-email" name="email" required autocomplete="email" placeholder="you@example.com">
    </div>
    <div class="field">
      <label for="q-area">Area / city *</label>
      <input type="text" id="q-area" name="area" required placeholder="Edmonton, Windermere" autocomplete="address-level2">
    </div>
    <div class="field">
      <label for="q-service">Service needed</label>
      <select id="q-service" name="service_interest">
        <option value="residential">Regular house cleaning</option>
        <option value="deep">Deep cleaning</option>
        <option value="moveinout">Move in / move out</option>
        <option value="carpet">Carpet &amp; upholstery</option>
        <option value="commercial">Commercial / office</option>
        <option value="other">Something else</option>
      </select>
    </div>
    <div class="field">
      <label for="q-when">Preferred timing</label>
      <select id="q-when" name="timing">
        <option>As soon as possible</option>
        <option>Within a week</option>
        <option>Within a month</option>
        <option>Just getting prices</option>
      </select>
    </div>
    <div class="field field--full">
      <label for="q-msg">Anything we should know?</label>
      <textarea id="q-msg" name="message" placeholder="3 bed / 2 bath bungalow, two cats, need the oven done too…"></textarea>
    </div>
    <input type="hidden" name="estimate" id="quote-estimate" value="">
    <input type="hidden" name="frequency" value="">
    <input type="hidden" name="property" value="">
    <input type="hidden" name="extras" value="">
    <input type="hidden" name="_subject" value="New quote request — fastandperfect.ca">
    <div class="hp" aria-hidden="true">
      <label for="q-gotcha">Leave this blank</label>
      <input type="text" id="q-gotcha" name="_gotcha" tabindex="-1" autocomplete="off">
    </div>
    <div class="field field--full">
      <label class="consent">
        <input type="checkbox" name="consent" required>
        <span>I agree to be contacted by {B['legal_name']} about this request.
        We never sell or share your details. See our
        <a href="privacy.html">privacy policy</a>.</span>
      </label>
    </div>
    <div class="field field--full">
      <button class="btn btn--gold btn--lg btn--block" type="submit">
        {icon('sparkle', 17)} Send my free quote request
      </button>
      <p class="field-hint mt-1" style="text-align:center">
        Or call {PHONE} if you would rather talk it through.
      </p>
    </div>
  </div>
  <div class="form-status" aria-live="polite"></div>
</form>
"""


# ---------------------------------------------------------------- content
def testimonial_cards(n=3, start=0):
    """Renders nothing at all while TESTIMONIALS is empty."""
    cards = []
    for name, where, text in TESTIMONIALS[start:start + n]:
        initials = "".join(p[0] for p in name.split()[:2]).upper()
        cards.append(f"""
<figure class="quote-card reveal">
  <blockquote>{text}</blockquote>
  <figcaption>
    <span class="avatar" aria-hidden="true">{initials}</span>
    <span><span class="who">{name}</span><span class="where">{where}</span></span>
  </figcaption>
</figure>""")
    return "".join(cards)


def reviews_section(n=3, start=0, heading="What our customers say"):
    """The whole section disappears until real reviews exist."""
    if not TESTIMONIALS:
        return ""
    return f"""
<section class="section">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Reviews</span>
      <h2 class="h-lg">{heading}</h2>
    </div>
    <div class="grid grid--3">{testimonial_cards(n, start)}</div>
  </div>
</section>
"""


HOME_FAQ = [
    ("Do I need to be home during the cleaning?",
     "Whatever suits you. You're welcome to be there, or you can arrange access with "
     "us in advance — plenty of clients prefer to come home to a finished house."),
    ("What areas do you cover?",
     f"{B['primary_area']} is our main service area. We also cover "
     + ", ".join(B["secondary_areas"][:-1])
     + f" and {B['secondary_areas'][-1]}. Depending on the size and type of job we can "
     "travel further — call and ask."),
    ("How much does a cleaning cost?",
     "It depends on the size of the space, the type of clean and how often you want "
     "us. Tell us the details through the quote form or over the phone and we'll come "
     "back with a written price. The quote is free and there's no obligation."),
    ("What's the difference between a regular clean and a deep clean?",
     "A regular clean maintains a space that's already in reasonable shape. A deep "
     "clean covers the things that only need doing occasionally — inside the oven and "
     "fridge, behind appliances, window tracks, light fixtures, baseboards scrubbed "
     "rather than wiped. Many people start with a deep clean and then move to a "
     "regular schedule."),
    ("How far ahead do I need to book?",
     "Get in touch and we'll tell you honestly what's available. If you need something "
     "urgently, call rather than using the form — it's faster."),
    ("Do you clean commercial premises as well as homes?",
     "Yes. Offices, clinics, retail units, salons and common areas, scheduled around "
     "your opening hours so your staff and customers aren't working around us."),
]


def qty_row(key, label, price_key, min_v=0, max_v=30):
    """One line item: label, its price, and a quantity stepper."""
    return f"""
<div class="qty" data-qty="{key}" data-min="{min_v}" data-max="{max_v}">
  <span class="qty__label">{label}
    <span class="qty__price" data-price-for="{price_key}"></span></span>
  <span class="stepper stepper--sm">
    <button type="button" data-step="down" aria-label="Fewer: {label}">&minus;</button>
    <output>0</output>
    <input type="hidden" value="0">
    <button type="button" data-step="up" aria-label="More: {label}">+</button>
  </span>
</div>"""


def carpet_calculator():
    """Carpet & upholstery estimate calculator.

    Deliberately has no bedrooms/bathrooms — it is built around what is
    actually cleaned: carpeted rooms, hallways, stairs, fabric furniture
    and mattresses.
    """
    if not claim("show_prices_carpet"):
        return ""

    p = PRICING
    uph = [i for i in p["items"] if i["group"] == "Upholstery"]
    mat = [i for i in p["items"] if i["group"] == "Mattresses"]

    carpet_rows = (
        qty_row("__rooms", "Carpeted rooms", "__rooms_price", 0, 20)
        .replace('<span class="qty__price" data-price-for="__rooms_price"></span>',
                 f'<span class="qty__price">up to {p["max_room_sqft"]} sq ft each</span>')
        + qty_row("__hallways", "Hallways", "__hallways", 0, 10)
        + qty_row("__steps", "Stairs — number of steps", "__steps", 0, 60)
    )
    uph_rows = "".join(qty_row(i["key"], i["label"], i["key"], 0, 15) for i in uph)
    mat_rows = "".join(qty_row(i["key"], i["label"], i["key"], 0, 15) for i in mat)
    treat_rows = "".join(
        f'<label class="treat"><input type="checkbox" name="treatment" value="{t["key"]}">'
        f'<span>{t["label"]}<span class="qty__price" data-price-for="{t["key"]}"></span></span>'
        f"</label>"
        for t in p["treatments"]
    )

    # A copy of the pricing travels with the page so the calculator still
    # works if the JSON file cannot be fetched for any reason.
    inline = json.dumps(p, ensure_ascii=False)

    return f"""
<div class="estimator" id="carpet-calculator">
  <script type="application/json" id="fp-pricing-inline">{inline}</script>
  <form class="est-panel" novalidate>
    <span class="eyebrow">Carpet cleaning</span>
    <div class="qty-group">{carpet_rows}</div>

    <span class="eyebrow mt-3">Upholstery</span>
    <div class="qty-group">{uph_rows}</div>

    <span class="eyebrow mt-3">Mattresses</span>
    <div class="qty-group">{mat_rows}</div>

    <span class="eyebrow mt-3">Additional treatments</span>
    <div class="treat-group">{treat_rows}</div>

    <div class="form-note mt-2">{icon('pin', 17)}
      <span data-pricing-note="max_room">{p['max_room_note']}</span></div>
  </form>

  <aside class="est-result">
    <span class="est-result__label">Estimated price</span>
    <div class="est-price" id="carpet-price">&mdash;<small>Select what needs cleaning</small></div>
    <p class="est-sub" id="carpet-min-note"></p>
    <ul class="est-break" id="carpet-lines"></ul>
    <a class="btn btn--gold btn--block" href="quote.html">
      Request this quote {icon('arrow', 16)}</a>
    <p class="est-foot" data-pricing-note="disclaimer">{p['disclaimer']}</p>
  </aside>
</div>
"""


def carpet_rate_table():
    """Published rate table. Rendered here at build time so it is in the HTML
    source for search engines, and re-rendered by the calculator script from
    the same JSON so the two can never drift apart."""
    if not claim("show_prices_carpet"):
        return ""
    p = PRICING

    def m(n):
        return f"${n:,.0f}"

    rows = [("Minimum service charge", "Applies to every appointment",
             m(p["minimum_service_charge"]))]
    for i, price in enumerate(p["carpet"]["room_tiers"]):
        rows.append((f"{i + 1} carpeted room" + ("" if i == 0 else "s"),
                     f"Up to {p['max_room_sqft']} sq ft per room", m(price)))
    rows += [
        ("Each additional room", f"Up to {p['max_room_sqft']} sq ft",
         "+" + m(p["carpet"]["additional_room"])),
        ("Hallway", "Per hallway", "+" + m(p["carpet"]["hallway"])),
        ("Stairs", f"Up to approx. {p['carpet']['stairs_included_steps']} steps",
         "+" + m(p["carpet"]["stairs_base"])),
        ("Each additional step", f"Beyond {p['carpet']['stairs_included_steps']} steps",
         "+" + m(p["carpet"]["additional_step"])),
    ]
    for i in p["items"]:
        rows.append((i["label"], i["group"],
                     ("from " if i.get("from") else "") + m(i["price"])))
    for t in p["treatments"]:
        rows.append((t["label"], "Depending on severity",
                     "+" + m(t["min"]) + "–" + m(t["max"])))

    body = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    return f"""
<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Price guide</span>
      <h2 class="h-lg">Carpet &amp; upholstery rates.</h2>
      <p class="lede">Starting prices, published so you know roughly where you
      stand before you call. Every job is confirmed with a written quote.</p>
    </div>
    <div class="table-wrap reveal">
      <table class="rate-table">
        <thead><tr><th>Service</th><th>Detail</th><th>Estimated price</th></tr></thead>
        <tbody id="carpet-rate-body">{body}</tbody>
      </table>
    </div>
    <p class="field-hint mt-2" data-pricing-note="disclaimer">{p['disclaimer']}</p>
    <p class="field-hint mt-1" data-pricing-note="max_room">{p['max_room_note']}</p>
  </div>
</section>
"""


def rate_table_section(c1, c2, c3, rows, title, lede, footnote):
    """A published rate table is a pricing claim — it disappears entirely
    until the owner confirms his numbers."""
    if not claim("show_prices"):
        return ""
    return f"""
<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Pricing</span>
      <h2 class="h-lg">{title}</h2>
      <p class="lede">{lede}</p>
    </div>
    <div class="table-wrap reveal">
      <table class="rate-table">
        <thead><tr><th>{c1}</th><th>{c2}</th><th>{c3}</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <p class="field-hint mt-2">{footnote}</p>
  </div>
</section>
"""


def faq_block(pairs, title="Questions people ask before booking"):
    items = "".join(
        f"<details{' open' if i == 0 else ''}><summary>{q}</summary>"
        f'<div class="faq__body">{a}</div></details>'
        for i, (q, a) in enumerate(pairs)
    )
    return f"""
<section class="section">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">FAQ</span>
      <h2 class="h-lg">{title}</h2>
    </div>
    <div class="faq reveal">{items}</div>
  </div>
</section>
"""


# ================================================================== PAGES
def build_home():
    services = [
        ("service-residential.svg", "Residential Cleaning", "residential-cleaning.html",
         "Weekly, bi-weekly, monthly or one-time. Kitchens, bathrooms, floors "
         "and dusting, worked through to a written checklist.",
         ["Regular &amp; recurring cleans", "Deep cleans", "Move in / move out", "Post-renovation"],
         "$135", "show_prices"),
        ("service-commercial.svg", "Commercial Cleaning", "commercial-cleaning.html",
         "Offices, clinics, salons, retail and small warehouses across Edmonton. "
         "Scheduled around your opening hours.",
         ["Offices &amp; clinics", "Retail &amp; salons", "Common areas", "Nightly or weekly schedules"],
         "$160", "show_prices"),
        ("service-carpet.svg", "Carpet &amp; Upholstery", "carpet-cleaning.html",
         "Hot-water extraction for carpets, area rugs, sofas and mattresses — "
         "traffic lanes, spills and pet accidents.",
         ["Carpets &amp; area rugs", "Sofas &amp; mattresses", "Pet odour treatment", "Stain protection"],
         f"${PRICING['minimum_service_charge']}", "show_prices_carpet"),
    ]
    cards = ""
    for i, (img, title, href, desc, bullets, price, gate) in enumerate(services):
        lis = "".join(f"<li>{b}</li>" for b in bullets)
        price_line = (f'<div class="price-from">from <b>{price}</b></div>'
                      if claim(gate) else "")
        cards += f"""
<article class="card reveal" data-delay="{i * 90}">
  <div class="card__media">
    <span class="card__index">{i + 1:02d}</span>
    <img src="assets/img/{img}" alt="{re.sub('&amp;', 'and', title)} in Edmonton" loading="lazy" width="1200" height="900">
  </div>
  <div class="card__body">
    <h3 class="h-sm">{title}</h3>
    <p>{desc}</p>
    <ul class="card__list">{lis}</ul>
    <div class="card__foot">
      {price_line}
      <a class="card-link mt-1" href="{href}">See what's included {icon('arrow', 15)}</a>
    </div>
  </div>
</article>"""

    areas = "".join(f'<a href="service-areas.html">{a}</a>' for a in B["areas"])
    marquee_items = "".join(
        f"<span>{a}</span>" for a in (B["areas"] + B["areas"])
    )

    body = f"""
<section class="hero">
  <div class="hero__arc" aria-hidden="true"></div>
  <div class="shell shell--wide hero__grid">
    <div>
      <span class="eyebrow anim">{B['city']} · {B['region_full']}</span>
      <h1 class="anim">A cleaner home,<br><span class="tilt">without</span> the chasing.</h1>
      <p class="lede anim">Residential, commercial and carpet cleaning across
      {B['city']} and {len(B['secondary_areas'])} surrounding communities. Tell us what
      you need and we'll come back with a clear price in writing — free, and with no
      obligation.</p>
      <div class="hero__actions anim">
        <a class="btn btn--gold btn--lg" href="quote.html">{icon('sparkle', 17)} Get a free quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{TEL}">{icon('phone', 17)} {PHONE}</a>
      </div>
      <div class="anim">{trust_strip()}</div>
    </div>
    <div class="collage">
      <div class="collage__main">
        <img src="assets/img/hero-living-room.svg" alt="Freshly cleaned living room in an Edmonton home" width="1200" height="900" fetchpriority="high">
      </div>
      {hero_float_cards()}
    </div>
  </div>
</section>

<div class="marquee" aria-hidden="true">
  <div class="marquee__track">{marquee_items}</div>
</div>

<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">What we do</span>
      <h2 class="h-lg">Three services, done <span class="tilt">properly</span>.</h2>
      <p class="lede">No franchise scripts, no rotating strangers. A small local crew
      that turns up when we said we would and cleans the things people actually notice.</p>
    </div>
    <div class="grid grid--3">{cards}</div>
  </div>
</section>

<section class="section band">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow eyebrow--light">How we work</span>
      <h2 class="h-lg">Straightforward, <span class="tilt--gold">local</span><br>and easy to reach.</h2>
    </div>
    <div class="stat-grid">
      <div class="stat reveal"><div class="stat__num">3</div>
        <div class="stat__label">Services — residential, commercial and carpet</div></div>
      <div class="stat reveal" data-delay="80"><div class="stat__num">{len(B['areas'])}</div>
        <div class="stat__label">Communities served across the Edmonton region</div></div>
      <div class="stat reveal" data-delay="160"><div class="stat__num">{icon('wallet', 42, 1.6)}</div>
        <div class="stat__label">Free quotes, in writing, with no obligation</div></div>
      <div class="stat reveal" data-delay="240"><div class="stat__num">{icon('users', 42, 1.6)}</div>
        <div class="stat__label">Locally owned and operated in {B['region_full']}</div></div>
    </div>
  </div>
</section>

<section class="section" id="estimate">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Free quote</span>
      <h2 class="h-lg">Tell us what you <span class="tilt">need</span>.</h2>
      <p class="lede">Set the details below and send them through. We'll come back with a
      written price — no walkthrough needed for most homes, and no obligation.</p>
    </div>
    {estimator_block()}
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">How it works</span>
      <h2 class="h-lg">Three steps, no <span class="tilt">runaround</span>.</h2>
    </div>
    <div class="steps steps--3">
      <div class="step reveal">
        <h3 class="h-sm">Tell us about your place</h3>
        <p>Use the form above or call us. Takes about ninety seconds — rooms,
        how often, and anything unusual we should know about.</p>
      </div>
      <div class="step reveal" data-delay="90">
        <h3 class="h-sm">Get a written quote</h3>
        <p>We put the price and the task list in writing so you know exactly what
        you're getting and what it costs before you commit to anything.</p>
      </div>
      <div class="step reveal" data-delay="180">
        <h3 class="h-sm">We book you in and clean</h3>
        <p>We agree a date and an arrival window that works around you, then work
        through the checklist we quoted on.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="shell">
    <div class="split">
      <div class="split__media reveal">
        <img src="assets/img/gallery-kitchen.svg" alt="Detailed kitchen cleaning including backsplash and counters" loading="lazy" width="1200" height="900">
      </div>
      <div>
        <span class="eyebrow">Our standard</span>
        <h2 class="h-lg">We clean the bits<br>other crews <span class="tilt">skip</span>.</h2>
        <p class="lede mt-2">Anyone can wipe a counter. The difference shows up in the
        places you only notice when they're wrong.</p>
        <ul class="check-list">
          <li>{icon('check', 18)}<span><b>Baseboards, switch plates and door frames</b> — every visit, not just deep cleans.</span></li>
          <li>{icon('check', 18)}<span><b>Under and behind</b> the toaster, the couch cushions, the toilet base.</span></li>
          <li>{icon('check', 18)}<span><b>Fresh microfibre per room</b> so bathroom cloths never touch a kitchen counter.</span></li>
          <li>{icon('check', 18)}<span><b>A written checklist</b> agreed before we start, so you know exactly what's covered.</span></li>
        </ul>
        <a class="btn btn--ghost mt-3" href="residential-cleaning.html">See the full checklist {icon('arrow', 16)}</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-sage">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Before &amp; after</span>
      <h2 class="h-lg">Drag the handle.</h2>
      <p class="lede">Real difference, same room. Grab the slider and pull it across.</p>
    </div>
    <div class="grid grid--2">
      <div class="reveal">
        <div class="ba">
          <img class="ba__before" src="assets/img/before-carpet.svg" alt="Carpet before cleaning" loading="lazy" width="1200" height="900">
          <img class="ba__after" src="assets/img/after-carpet.svg" alt="Carpet after professional hot-water extraction" loading="lazy" width="1200" height="900">
          <span class="ba__tag ba__tag--before">Before</span>
          <span class="ba__tag ba__tag--after">After</span>
          <span class="ba__handle"></span>
          <span class="ba__knob">{icon('chevrons', 18)}</span>
        </div>
        <p class="field-hint mt-1">Carpet extraction — Mill Woods, Edmonton</p>
      </div>
      <div class="reveal" data-delay="110">
        <div class="ba">
          <img class="ba__before" src="assets/img/before-living-room.svg" alt="Living room before cleaning" loading="lazy" width="1200" height="900">
          <img class="ba__after" src="assets/img/after-living-room.svg" alt="Living room after a full deep clean" loading="lazy" width="1200" height="900">
          <span class="ba__tag ba__tag--before">Before</span>
          <span class="ba__tag ba__tag--after">After</span>
          <span class="ba__handle"></span>
          <span class="ba__knob">{icon('chevrons', 18)}</span>
        </div>
        <p class="field-hint mt-1">Move-out deep clean — Terwillegar, Edmonton</p>
      </div>
    </div>
    <div class="center mt-4">
      <a class="btn btn--ghost" href="gallery.html">See more of our work {icon('arrow', 16)}</a>
    </div>
  </div>
</section>

{reviews_section(3, heading="What Edmonton says.")}

<section class="section section--tight bg-paper">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Coverage</span>
      <h2 class="h-md">Serving Edmonton and the surrounding communities</h2>
    </div>
    <div class="area-cloud reveal" style="justify-content:center">{areas}</div>
  </div>
</section>

{faq_block(HOME_FAQ)}

{cta_band()}
"""
    page(
        "index.html",
        f"Cleaning Services in {B['city']}, AB | {B['legal_name']}",
        "Residential, commercial and carpet cleaning in Edmonton and "
        f"{len(B['secondary_areas'])} surrounding communities. Locally owned, with a "
        "free written quote and no obligation.",
        body,
        schemas=[local_business_schema(), faq_schema(HOME_FAQ)],
        keywords="cleaning services Edmonton, house cleaning Edmonton, commercial "
                 "cleaning Edmonton, carpet cleaning Edmonton, maid service Edmonton",
    )


def build_residential():
    checklist = {
        "Kitchen": [
            "Counters, backsplash and sink scrubbed and polished",
            "Exterior of all appliances, cupboards and handles",
            "Stovetop degreased, range hood wiped",
            "Microwave cleaned inside and out",
            "Floors vacuumed and washed, edges included",
            "Garbage emptied, liner replaced",
        ],
        "Bathrooms": [
            "Toilet cleaned and disinfected — base, hinges and behind",
            "Tub, shower and tiles scrubbed, glass de-scaled",
            "Mirrors and chrome polished streak-free",
            "Vanity, sink and cabinet fronts wiped",
            "Floors washed, corners and behind the door included",
        ],
        "Bedrooms & living areas": [
            "All reachable surfaces dusted, including sills and ledges",
            "Beds made or linens changed if left out",
            "Mirrors and glass polished",
            "Under furniture vacuumed where accessible",
            "Carpets vacuumed, hard floors washed",
        ],
        "Everywhere": [
            "Baseboards, switch plates, door handles and frames",
            "Cobwebs removed from ceilings and corners",
            "Interior glass on doors",
            "Final walkthrough against the written checklist",
        ],
    }
    blocks = ""
    for i, (room, items) in enumerate(checklist.items()):
        lis = "".join(f"<li>{it}</li>" for it in items)
        blocks += f"""
<article class="card reveal" data-delay="{i * 70}">
  <div class="card__body">
    <span class="card__index" style="position:static;margin-bottom:.9rem">{i + 1:02d}</span>
    <h3 class="h-sm">{room}</h3>
    <ul class="card__list">{lis}</ul>
  </div>
</article>"""

    rates = [
        ("1 bed / 1 bath condo", "2 – 2.5 hrs", "$120 – $150"),
        ("2 bed / 1 bath", "2.5 – 3 hrs", "$140 – $175"),
        ("3 bed / 2 bath", "3 – 4 hrs", "$165 – $210"),
        ("4 bed / 3 bath", "4 – 5.5 hrs", "$220 – $290"),
        ("Deep clean (add-on)", "+1.5 – 3 hrs", "+$80 – $160"),
        ("Move in / move out", "4 – 7 hrs", "$260 – $450"),
    ]
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rates)

    faqs = [
        ("How long does a house cleaning take?",
         "It depends on the size of the home and whether it's a regular clean or a "
         "deep clean. We'll give you a realistic time along with your quote rather "
         "than a number that sounds good and then runs over."),
        ("What's the difference between a regular clean and a deep clean?",
         "A regular clean maintains a home that's already in decent shape. A deep clean "
         "adds the things that only need doing a few times a year — inside the oven and "
         "fridge, behind appliances, window tracks, light fixtures, baseboards scrubbed "
         "rather than wiped. Many people start with one deep clean, then go recurring."),
        ("Do you do laundry or dishes?",
         "Dishes in the sink can be washed or loaded as part of a kitchen clean. "
         "Laundry is available as an add-on — just tick it on the quote form and we'll "
         "include it in your price."),
        ("What about pets?",
         "Not a problem. Just let us know in advance so we know to watch the doors, and "
         "tell us if an animal is nervous around strangers so we can work around a "
         "closed door."),
        ("Can you work around my schedule?",
         "Yes — tell us the days and times that suit you when you request your quote "
         "and we'll tell you honestly what we can fit."),
    ]

    body = page_head(
        "Residential",
        'House Cleaning in Edmonton<br>to a <span class="tilt">written</span> checklist.',
        "Weekly, bi-weekly, monthly or one-off cleans for homes, condos and townhouses "
        "across Edmonton and the surrounding communities.",
        [("Home", "index.html"), ("Services", "residential-cleaning.html"), ("Residential Cleaning", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="split">
      <div>
        <span class="eyebrow">What's included</span>
        <h2 class="h-lg">Every clean follows<br>the same <span class="tilt">checklist</span>.</h2>
        <p class="lede mt-2">Not a vague "general tidy". A written list, agreed with you
        before we start, so you can see exactly what's covered and tell us if something
        should be added or dropped.</p>
        <ul class="check-list">
          <li>{icon('check', 18)}<span><b>Regular or one-off</b> — weekly, every two weeks, monthly, or a single visit.</span></li>
          <li>{icon('check', 18)}<span><b>Flexible entry</b> — be home, leave a key, or arrange a door code.</span></li>
          <li>{icon('check', 18)}<span><b>Tell us your priorities</b> and we'll weight the time where it matters to you.</span></li>
          <li>{icon('check', 18)}<span><b>A written quote</b> before anything is booked in.</span></li>
        </ul>
        <div class="hero__actions mt-3">
          <a class="btn btn--gold" href="quote.html">Get my quote</a>
          <a class="btn btn--ghost" href="book.html">{icon('calendar', 16)} Book online</a>
        </div>
      </div>
      <div class="split__media reveal">
        <img src="assets/img/service-residential.svg" alt="Clean, bright living room after a residential cleaning in Edmonton" loading="lazy" width="1200" height="900">
      </div>
    </div>
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Room by room</span>
      <h2 class="h-lg">The full standard clean.</h2>
    </div>
    <div class="grid grid--2">{blocks}</div>
  </div>
</section>

{rate_table_section("Home size", "Typical duration", "Price range", rows,
                    "Typical Edmonton prices.",
                    "Recurring plans are priced lower than one-off visits. Your written "
                    "quote is the price you pay.",
                    "Prices in CAD, GST-exclusive.")}

<section class="section bg-sage">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Free quote</span>
      <h2 class="h-lg">Price your home.</h2>
    </div>
    {estimator_block("estimator-form", with_cta=False)}
  </div>
</section>

{reviews_section(3, 0, heading="From homes like yours.")}

{faq_block(faqs, "Residential cleaning questions")}
{cta_band()}
"""
    page(
        "residential-cleaning.html",
        f"House Cleaning {B['city']} | Weekly, Deep & Move-Out | {B['name']}",
        "House cleaning in Edmonton — weekly, bi-weekly, deep and move-out cleans "
        "for homes, condos and townhouses across the Edmonton region. Free written "
        "quote, no obligation.",
        body,
        schemas=[
            service_schema(
                "Residential House Cleaning",
                "Recurring and one-time house cleaning for homes, condos and "
                "townhouses in Edmonton and surrounding communities.",
                120, 450,
            ),
            breadcrumbs([("Home", "index.html"), ("Residential Cleaning", None)]),
            faq_schema(faqs),
        ],
        keywords="house cleaning Edmonton, maid service Edmonton, deep cleaning "
                 "Edmonton, move out cleaning Edmonton, residential cleaners Edmonton",
    )


def build_commercial():
    sectors = [
        ("Offices &amp; coworking", "Desks, meeting rooms, kitchens and washrooms cleaned "
         "after hours so nobody works around a wet floor sign."),
        ("Clinics &amp; dental", "Disinfection protocols for treatment rooms, waiting areas "
         "and high-touch surfaces, with logged sign-off sheets."),
        ("Retail &amp; salons", "Front-of-house glass, floors, change rooms and washrooms "
         "reset nightly so you open to a clean store."),
        ("Warehouses &amp; shops", "Lunchrooms, offices, washrooms and walkways on a schedule "
         "that fits around shift changes."),
        ("Property &amp; common areas", "Lobbies, corridors, elevators, stairwells and gym "
         "areas for condo boards and property managers."),
        ("Post-construction", "Fine dust removal, sticker and adhesive cleanup, and a final "
         "detail before handover or tenant move-in."),
    ]
    cards = ""
    for i, (t, d) in enumerate(sectors):
        cards += f"""
<article class="card reveal" data-delay="{i * 60}">
  <div class="card__body">
    <h3 class="h-sm">{t}</h3>
    <p>{d}</p>
  </div>
</article>"""

    faqs = [
        ("Do you clean outside business hours?",
         "Yes — evenings, early mornings or weekends. Tell us the window that keeps "
         "your team and customers undisturbed and we'll work to it."),
        ("Can we start with a trial before committing to a schedule?",
         "Of course, and we'd encourage it. Starting with a one-off clean or a short "
         "trial period is the sensible way to find out whether we're a fit before "
         "anyone signs anything."),
        ("Do you supply consumables — paper, soap, liners?",
         "We can manage and restock washroom supplies for you, or you can keep "
         "supplying your own and we'll flag when stock is running low. Tell us which "
         "you'd prefer and we'll price it accordingly."),
        ("How do you handle keys, alarm codes and access?",
         "Keys and fobs are numbered and stored securely, never labelled with your "
         "address, and alarm codes are recorded separately from them. We can also work "
         "with an existing access system or a lockbox if you have one."),
        ("What documentation can you provide for our records?",
         "Tell us what your business or property manager requires and we'll confirm "
         "exactly what we can supply before you commit to anything."),
    ]

    body = page_head(
        "Commercial",
        'Commercial Cleaning<br>that keeps your doors <span class="tilt">open</span>.',
        "Offices, clinics, retail, salons and common areas across Edmonton and the "
        "surrounding communities, scheduled around your opening hours.",
        [("Home", "index.html"), ("Services", "commercial-cleaning.html"), ("Commercial Cleaning", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="split split--flip">
      <div class="split__media reveal">
        <img src="assets/img/service-commercial.svg" alt="Clean Edmonton office after a commercial cleaning service" loading="lazy" width="1200" height="900">
      </div>
      <div>
        <span class="eyebrow">How we work</span>
        <h2 class="h-lg">A schedule you can<br>actually <span class="tilt">plan around</span>.</h2>
        <p class="lede mt-2">You're dealing with a local business, not a call centre —
        so the person who quotes your site is the person you ring when something needs
        changing.</p>
        <ul class="check-list">
          <li>{icon('check', 18)}<span><b>Scheduled around your hours</b> — evenings, early mornings or weekends.</span></li>
          <li>{icon('check', 18)}<span><b>A written scope of work</b>, agreed task by task before we start.</span></li>
          <li>{icon('check', 18)}<span><b>Change the scope whenever you need</b> — the price moves with it, transparently.</span></li>
          <li>{icon('check', 18)}<span><b>Start with a trial</b> rather than a long commitment.</span></li>
        </ul>
        <div class="hero__actions mt-3">
          <a class="btn btn--gold" href="quote.html">Request a site quote</a>
          <a class="btn btn--ghost" href="tel:{TEL}">{icon('phone', 16)} {PHONE}</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Sectors</span>
      <h2 class="h-lg">Who we clean for.</h2>
    </div>
    <div class="grid grid--3">{cards}</div>
  </div>
</section>

<section class="section band">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow eyebrow--light">Getting started</span>
      <h2 class="h-lg">Three steps to a<br>working <span class="tilt--gold">schedule</span>.</h2>
    </div>
    <div class="steps steps--3">
      <div class="step reveal">
        <h3 class="h-sm">Walkthrough</h3>
        <p>We visit the site, look at what's actually involved, and agree the scope
        area by area. It costs nothing.</p>
      </div>
      <div class="step reveal" data-delay="90">
        <h3 class="h-sm">Written scope &amp; price</h3>
        <p>You get a per-visit price, a frequency, and a written task list. Change it
        any time — the price moves with the scope, transparently.</p>
      </div>
      <div class="step reveal" data-delay="180">
        <h3 class="h-sm">Schedule agreed</h3>
        <p>We settle on the days and times that keep your staff and customers
        undisturbed, then check in early on to adjust anything that isn't working.</p>
      </div>
    </div>
  </div>
</section>

{reviews_section(3, 3, heading="From local businesses.")}

{faq_block(faqs, "Commercial cleaning questions")}
{cta_band(
    'Get a <span class="tilt--gold">site-specific</span> quote.',
    "Tell us the square footage and how often you need us. We'll arrange a walkthrough "
    "and come back with a written scope and a per-visit price."
)}
"""
    page(
        "commercial-cleaning.html",
        f"Commercial & Office Cleaning {B['city']} | {B['name']}",
        "Commercial cleaning in Edmonton for offices, clinics, retail and common "
        "areas across the Edmonton region. Scheduled around your opening hours. "
        "Free site walkthrough and written quote.",
        body,
        schemas=[
            service_schema(
                "Commercial Cleaning",
                "Office, clinic, retail and common-area cleaning across Edmonton "
                "and surrounding communities, scheduled outside business hours.",
                160, 2500,
            ),
            breadcrumbs([("Home", "index.html"), ("Commercial Cleaning", None)]),
            faq_schema(faqs),
        ],
        keywords="commercial cleaning Edmonton, office cleaning Edmonton, janitorial "
                 "services Edmonton, retail cleaning Edmonton",
    )


def build_carpet():
    faqs = [
        ("How long does carpet take to dry?",
         "Four to six hours in a normally ventilated room. We extract as much moisture as "
         "the machine will pull, so you're not walking on a swamp. Open a window or run "
         "the furnace fan and it's quicker."),
        ("Will the stains come back?",
         "Sometimes a stain 'wicks' back as the carpet dries — that's residue deep in the "
         "backing rising to the surface as moisture leaves. If that happens, get in touch "
         "and we'll talk through re-treating the spot."),
        ("Can you get rid of pet smells?",
         "Usually, yes. Surface cleaning won't do it — urine soaks into the backing and "
         "underlay. We use an enzyme treatment that breaks down the source rather than "
         "masking it. Severe, repeated accidents may need the underlay replaced, and "
         "we'll tell you honestly if that's the case."),
        ("Do you move the furniture?",
         "We move what two people can safely lift — sofas, chairs, coffee tables. "
         "Bookcases, pianos, aquariums and anything on fragile legs stay put and we clean "
         "around them."),
        ("What method do you use?",
         "Hot-water extraction, which most people call steam cleaning. It's what almost "
         "every carpet manufacturer specifies for warranty purposes, and it's the only "
         "method that reliably flushes soil out of the pile rather than moving it around."),
    ]
    rates = [
        ("Up to 3 rooms", "Standard extraction", "$139"),
        ("Each additional room", "Standard extraction", "+$35"),
        ("Hallway or staircase", "Up to 14 steps", "$45"),
        ("Area rug (per sq ft)", "On-site", "$0.55"),
        ("Sofa (3-seat)", "Upholstery extraction", "$95"),
        ("Mattress (queen)", "Both sides", "$75"),
        ("Pet odour enzyme treatment", "Per affected area", "+$45"),
        ("Stain protection", "Per room", "+$25"),
    ]
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rates)

    body = page_head(
        "Carpet &amp; Upholstery",
        'Carpet Cleaning that lifts<br>what a vacuum <span class="tilt">can\'t</span>.',
        "Hot-water extraction for carpets, area rugs, sofas and mattresses across "
        "Edmonton and the surrounding communities — traffic lanes, pet accidents "
        "and years of spills.",
        [("Home", "index.html"), ("Services", "carpet-cleaning.html"), ("Carpet Cleaning", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="split">
      <div>
        <span class="eyebrow">The method</span>
        <h2 class="h-lg">Hot-water extraction,<br>done <span class="tilt">thoroughly</span>.</h2>
        <p class="lede mt-2">Most of what makes a carpet look tired isn't a stain — it's
        soil ground into the base of the pile that shampooing just redistributes.
        Extraction flushes it out and pulls it back up.</p>
        <ul class="check-list">
          <li>{icon('check', 18)}<span><b>Pre-vacuum and pre-spray</b> so the solution has time to break the soil down.</span></li>
          <li>{icon('check', 18)}<span><b>Agitation on traffic lanes</b> — the doorways and hallways that always go first.</span></li>
          <li>{icon('check', 18)}<span><b>Hot extraction rinse</b> that leaves no sticky detergent residue behind to re-attract dirt.</span></li>
          <li>{icon('check', 18)}<span><b>Groomed and dried</b> before we leave, and we'll tell you how long to stay off it.</span></li>
        </ul>
        <div class="hero__actions mt-3">
          <a class="btn btn--gold" href="quote.html">Get a carpet quote</a>
          <a class="btn btn--ghost" href="book.html">{icon('calendar', 16)} Book online</a>
        </div>
      </div>
      <div class="split__media reveal">
        <img src="assets/img/service-carpet.svg" alt="Carpet cleaned by hot-water extraction showing fresh vacuum tracks" loading="lazy" width="1200" height="900">
      </div>
    </div>
  </div>
</section>

<section class="section bg-sage">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">See the difference</span>
      <h2 class="h-lg">Drag to compare.</h2>
    </div>
    <div class="reveal" style="max-width:860px;margin-inline:auto">
      <div class="ba">
        <img class="ba__before" src="assets/img/before-carpet.svg" alt="Carpet before hot-water extraction" loading="lazy" width="1200" height="900">
        <img class="ba__after" src="assets/img/after-carpet.svg" alt="Carpet after hot-water extraction" loading="lazy" width="1200" height="900">
        <span class="ba__tag ba__tag--before">Before</span>
        <span class="ba__tag ba__tag--after">After</span>
        <span class="ba__handle"></span>
        <span class="ba__knob">{icon('chevrons', 18)}</span>
      </div>
    </div>
  </div>
</section>

<section class="section" id="calculator">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Estimate calculator</span>
      <h2 class="h-lg">Price your <span class="tilt">carpets</span> and furniture.</h2>
      <p class="lede">Choose what needs cleaning and see an estimate straight away.
      No bedrooms or bathrooms here — just what actually gets cleaned.</p>
    </div>
    {carpet_calculator()}
  </div>
</section>

{carpet_rate_table()}

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Also cleaned</span>
      <h2 class="h-lg">Not just carpet.</h2>
    </div>
    <div class="grid grid--4">
      <article class="card reveal"><div class="card__body"><h3 class="h-sm">Sofas &amp; armchairs</h3>
        <p>Fabric upholstery extracted and deodorised. We test colourfastness first.</p></div></article>
      <article class="card reveal" data-delay="70"><div class="card__body"><h3 class="h-sm">Mattresses</h3>
        <p>Both sides, extracted and deodorised.</p></div></article>
      <article class="card reveal" data-delay="140"><div class="card__body"><h3 class="h-sm">Area rugs</h3>
        <p>Cleaned on-site where suitable, priced by the square foot.</p></div></article>
      <article class="card reveal" data-delay="210"><div class="card__body"><h3 class="h-sm">Vehicle interiors</h3>
        <p>Seats, mats and headliners for cars, vans and RVs. Quoted per vehicle.</p></div></article>
    </div>
  </div>
</section>

{faq_block(faqs, "Carpet cleaning questions")}
{cta_band(
    'Book the carpets and the house <span class="tilt--gold">together</span>.',
    "Combining a house clean with carpet extraction means one visit and one invoice. "
    "Ask for both on your quote and we'll price them as a single job."
)}
"""
    page(
        "carpet-cleaning.html",
        f"Carpet Cleaning {B['city']} | Hot-Water Extraction | {B['name']}",
        "Carpet and upholstery cleaning in Edmonton using hot-water extraction. "
        "Traffic lanes, pet odours and stains, plus sofas, mattresses and area "
        "rugs. Free written quote.",
        body,
        extra_js=["assets/js/carpet-calculator.js"],
        schemas=[
            service_schema(
                "Carpet and Upholstery Cleaning",
                "Hot-water extraction carpet cleaning, upholstery and mattress "
                "cleaning across Edmonton and surrounding communities.",
                PRICING["minimum_service_charge"], None,
                enabled=claim("show_prices_carpet"),
            ),
            breadcrumbs([("Home", "index.html"), ("Carpet Cleaning", None)]),
            faq_schema(faqs),
        ],
        keywords="carpet cleaning Edmonton, steam cleaning Edmonton, upholstery "
                 "cleaning Edmonton, pet odour removal Edmonton, rug cleaning Edmonton",
    )


def build_gallery():
    tiles = [
        ("gallery-kitchen.svg", "Kitchen deep clean — Glenora"),
        ("gallery-bathroom.svg", "Bathroom detail — Oliver"),
        ("gallery-office.svg", "Office after-hours clean — Downtown"),
        ("gallery-carpet.svg", "Carpet extraction — Mill Woods"),
        ("gallery-window.svg", "Interior windows — Windermere"),
        ("gallery-hallway.svg", "Common area — St. Albert"),
        ("gallery-living.svg", "Move-out clean — Terwillegar"),
        ("service-commercial.svg", "Clinic disinfection — Sherwood Park"),
    ]
    grid = "".join(
        f'<figure class="tile reveal" data-delay="{i * 50}">'
        f'<img src="assets/img/{f}" alt="{c}" loading="lazy" width="1200" height="900">'
        f'<figcaption class="tile__cap">{c}</figcaption></figure>'
        for i, (f, c) in enumerate(tiles)
    )
    body = page_head(
        "Our work",
        'Rooms we\'ve <span class="tilt">reset</span>.',
        "A look at recent jobs across Edmonton and area — homes, offices, carpets "
        "and move-outs.",
        [("Home", "index.html"), ("Our Work", None)],
    ) + f"""
<section class="section">
  <div class="shell shell--wide">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Before &amp; after</span>
      <h2 class="h-lg">Drag the handle to compare.</h2>
    </div>
    <div class="grid grid--2">
      <div class="reveal">
        <div class="ba">
          <img class="ba__before" src="assets/img/before-carpet.svg" alt="Carpet before cleaning" loading="lazy" width="1200" height="900">
          <img class="ba__after" src="assets/img/after-carpet.svg" alt="Carpet after cleaning" loading="lazy" width="1200" height="900">
          <span class="ba__tag ba__tag--before">Before</span>
          <span class="ba__tag ba__tag--after">After</span>
          <span class="ba__handle"></span><span class="ba__knob">{icon('chevrons', 18)}</span>
        </div>
        <p class="field-hint mt-1">Living room carpet, five years no professional clean — Mill Woods</p>
      </div>
      <div class="reveal" data-delay="110">
        <div class="ba">
          <img class="ba__before" src="assets/img/before-living-room.svg" alt="Living room before cleaning" loading="lazy" width="1200" height="900">
          <img class="ba__after" src="assets/img/after-living-room.svg" alt="Living room after cleaning" loading="lazy" width="1200" height="900">
          <span class="ba__tag ba__tag--before">Before</span>
          <span class="ba__tag ba__tag--after">After</span>
          <span class="ba__handle"></span><span class="ba__knob">{icon('chevrons', 18)}</span>
        </div>
        <p class="field-hint mt-1">Move-out deep clean, tenant handover — Terwillegar</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="shell shell--wide">
    <div class="section-head">
      <span class="eyebrow">Recent jobs</span>
      <h2 class="h-lg">Around the city.</h2>
    </div>
    <div class="gallery-grid">{grid}</div>
  </div>
</section>

{reviews_section(6, heading="What people said afterwards.")}

{cta_band()}
"""
    page(
        "gallery.html",
        f"Our Work — Cleaning Gallery {B['city']} | {B['name']}",
        "Before-and-after photos from recent residential, commercial and carpet "
        "cleaning jobs across Edmonton, St. Albert, Sherwood Park and area.",
        body,
        schemas=[breadcrumbs([("Home", "index.html"), ("Our Work", None)])],
    )


def build_about():
    body = page_head(
        "About us",
        'A local company,<br>not a <span class="tilt">franchise</span>.',
        f"{B['legal_name']} is a locally owned cleaning company based in "
        f"{B['city']}, {B['region_full']}.",
        [("Home", "index.html"), ("About", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="split">
      <div class="split__media reveal">
        <img src="assets/img/about-crew.svg" alt="The Fast and Perfect cleaning team" loading="lazy" width="1200" height="900">
      </div>
      <div class="prose">
        <span class="eyebrow">Who we are</span>
        <h2 class="h-lg">Cleaning, done<br><span class="tilt">properly</span>.</h2>
        <p class="lede mt-2">{B['legal_name']} provides residential, commercial and
        carpet cleaning across {B['city']} and {len(B['secondary_areas'])} surrounding
        communities.</p>
        <p class="mt-2">We're a local business, which means you're dealing with the
        people actually doing the work — not a call centre in another province. When you
        ring, someone here answers.</p>
        <p>Every job starts with a written quote and an agreed task list, so there's no
        ambiguity about what's included or what it costs. If something isn't right, tell
        us and we'll put it right.</p>
      </div>
    </div>
  </div>
</section>

<section class="section band">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow eyebrow--light">How we work</span>
      <h2 class="h-lg">Four things, <span class="tilt--gold">every time</span>.</h2>
    </div>
    <div class="stat-grid">
      <div class="stat reveal"><div class="stat__num">{icon('wallet', 42, 1.6)}</div>
        <div class="stat__label">A written quote before anything is booked in.</div></div>
      <div class="stat reveal" data-delay="80"><div class="stat__num">{icon('check', 42, 1.6)}</div>
        <div class="stat__label">An agreed task list, so you know what's covered.</div></div>
      <div class="stat reveal" data-delay="160"><div class="stat__num">{icon('phone', 42, 1.6)}</div>
        <div class="stat__label">A local number, answered by the people doing the work.</div></div>
      <div class="stat reveal" data-delay="240"><div class="stat__num">{icon('pin', 42, 1.6)}</div>
        <div class="stat__label">{len(B['areas'])} communities across the Edmonton region.</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">What to expect</span>
      <h2 class="h-lg">From first call to finished job.</h2>
    </div>
    <div class="steps steps--3">
      <div class="step reveal">
        <h3 class="h-sm">A straight answer</h3>
        <p>Tell us what you need and we'll tell you honestly whether we're the right
        fit, what it involves and what it will cost.</p>
      </div>
      <div class="step reveal" data-delay="90">
        <h3 class="h-sm">An agreed checklist</h3>
        <p>We put the scope in writing before we start, so nothing is assumed and
        nothing gets quietly dropped.</p>
      </div>
      <div class="step reveal" data-delay="180">
        <h3 class="h-sm">Work you can check</h3>
        <p>Walk through it with us or tell us afterwards. If something's been missed,
        we want to hear about it.</p>
      </div>
    </div>
  </div>
</section>

{reviews_section(3, 3, heading="In their words.")}

{cta_band()}
"""
    page(
        "about.html",
        f"About {B['legal_name']} | Edmonton Cleaning Company",
        f"{B['legal_name']} is a locally owned cleaning company serving Edmonton "
        f"and {len(B['secondary_areas'])} surrounding communities — residential, "
        "commercial and carpet cleaning to an agreed written checklist.",
        body,
        schemas=[
            local_business_schema(),
            breadcrumbs([("Home", "index.html"), ("About", None)]),
        ],
    )


def build_areas():
    blurbs = {
        "St. Albert": "Residential and commercial cleaning throughout St. Albert.",
        "Sherwood Park": "Homes and businesses across Strathcona County.",
        "Spruce Grove": "Homes, acreages and small commercial premises.",
        "Stony Plain": "Residential and commercial cleaning across the town.",
        "Leduc": "Residential and commercial, including move-in and move-out cleans.",
        "Beaumont": "Family homes and new builds, including post-construction cleans.",
        "Fort Saskatchewan": "Residential cleaning plus office and lunchroom work.",
        "Nisku": "Commercial and industrial offices, shops and lunchrooms.",
        "Devon": "Residential cleaning and carpet extraction.",
        "Acheson": "Industrial and commercial premises across the business park.",
        "Morinville": "Residential cleaning on a regular or one-off basis.",
        "Ardrossan": "Acreages and family homes east of Sherwood Park.",
        "Gibbons": "Residential cleaning for homes and acreages.",
        "Legal": "Residential and small commercial cleaning.",
        "Bon Accord": "Residential cleaning for homes and acreages.",
        "Calmar": "Residential and small commercial cleaning.",
        "Thorsby": "Residential cleaning for homes and acreages.",
        "Millet": "Residential and small commercial cleaning.",
        "New Sarepta": "Residential cleaning for homes and acreages.",
    }

    # Edmonton leads on its own — it's the primary market for both SEO and ads.
    primary_card = f"""
<article class="card reveal" style="border-color:var(--sage-deep)">
  <div class="card__body">
    <span class="eyebrow">Primary service area</span>
    <h3 class="h-md">{icon('pin', 20)} {B['primary_area']}</h3>
    <p>Our main service area — full coverage across the city, from Castle Downs to
    Summerside, including downtown condos and the river valley communities.
    Residential, commercial and carpet cleaning.</p>
    <ul class="card__list">
      <li>Residential — regular, deep, move in / move out</li>
      <li>Commercial — offices, clinics, retail, common areas</li>
      <li>Carpet &amp; upholstery — hot-water extraction</li>
    </ul>
    <div class="card__foot">
      <a class="btn btn--gold" href="quote.html">Get an {B['primary_area']} quote {icon('arrow', 15)}</a>
    </div>
  </div>
</article>"""

    cards = ""
    for i, a in enumerate(B["secondary_areas"]):
        cards += f"""
<article class="card reveal" data-delay="{min(i, 8) * 40}">
  <div class="card__body">
    <h3 class="h-sm">{icon('pin', 17)} {a}</h3>
    <p>{blurbs.get(a, 'Residential and commercial cleaning available.')}</p>
    <div class="card__foot"><a class="card-link" href="quote.html">Get a quote for {a} {icon('arrow', 15)}</a></div>
  </div>
</article>"""

    hoods = "".join(f"<span>{n}</span>" for n in B["neighbourhoods"])

    body = page_head(
        "Coverage",
        f'Cleaning across {B["city"]}<br>and <span class="tilt">the region</span>.',
        f"{B['primary_area']} is our primary service area. We also serve "
        f"{len(B['secondary_areas'])} surrounding communities — and depending on the "
        "size and type of job, we can travel further. If you're outside the list, "
        "call and ask.",
        [("Home", "index.html"), ("Areas Served", None)],
    ) + f"""
<section class="section">
  <div class="shell shell--wide">
    <div class="split" style="align-items:stretch">
      {primary_card}
      <div class="split__media reveal">
        <img src="assets/img/gallery-living.svg" alt="Cleaning services in {B['primary_area']}, Alberta" loading="lazy" width="1200" height="900">
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="shell shell--wide">
    <div class="section-head">
      <span class="eyebrow">Secondary service areas</span>
      <h2 class="h-lg">{len(B['secondary_areas'])} surrounding communities.</h2>
      <p class="lede">All within our standard service area, covering residential,
      commercial and carpet cleaning.</p>
    </div>
    <div class="grid grid--3">{cards}</div>
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">{B['primary_area']} neighbourhoods</span>
      <h2 class="h-lg">Across the whole city.</h2>
      <p class="lede">A few of the areas we're asked about most — but we cover all of
      {B['primary_area']}, not just these.</p>
    </div>
    <div class="area-cloud reveal">{hoods}</div>
  </div>
</section>

<section class="section band">
  <div class="shell">
    <div class="split">
      <div>
        <span class="eyebrow eyebrow--light">Travel &amp; scheduling</span>
        <h2 class="h-lg">Outside the list? <span class="tilt--gold">Ask.</span></h2>
        <p class="lede mt-2">Every community on this page is inside our standard service
        area. We also take on work further out depending on the size and type of job.</p>
        <ul class="check-list" style="--ink-soft:rgba(246,242,234,.78)">
          <li>{icon('check', 18)}<span style="color:rgba(246,242,234,.82)"><b style="color:#fffdf8">{B['primary_area']} first</b> — it's our primary market and where most of our work is.</span></li>
          <li>{icon('check', 18)}<span style="color:rgba(246,242,234,.82)"><b style="color:#fffdf8">Surrounding communities</b> covered for residential, commercial and carpet work.</span></li>
          <li>{icon('check', 18)}<span style="color:rgba(246,242,234,.82)"><b style="color:#fffdf8">Larger jobs further out</b> — tell us where you are and what's involved and we'll give you a straight answer.</span></li>
        </ul>
        <a class="btn btn--gold mt-3" href="quote.html">{icon('sparkle', 16)} Request a quote</a>
      </div>
      <div class="split__media reveal">
        <img src="assets/img/gallery-hallway.svg" alt="Cleaned common area hallway in an Edmonton building" loading="lazy" width="1200" height="900">
      </div>
    </div>
  </div>
</section>

{cta_band()}
"""
    page(
        "service-areas.html",
        f"Areas Served — Cleaning in {B['city']}, St. Albert & Sherwood Park",
        "Fast and Perfect cleans homes and businesses across Edmonton — our primary "
        "service area — plus St. Albert, Sherwood Park, Spruce Grove, Stony Plain, "
        f"Leduc, Beaumont and {len(B['secondary_areas']) - 6} more communities.",
        body,
        schemas=[breadcrumbs([("Home", "index.html"), ("Areas Served", None)])],
        keywords=", ".join(
            [f"cleaning services {B['primary_area']}", f"house cleaning {B['primary_area']}"]
            + [f"cleaners {a}" for a in B["secondary_areas"][:8]]
        ),
    )


def build_quote():
    body = page_head(
        "Free quote",
        'Get your <span class="tilt">free</span> quote.',
        "Fill in the details below and send them over. We'll come back with a written "
        "quote — no walkthrough needed for most homes, and no obligation.",
        [("Home", "index.html"), ("Free Quote", None)],
    ) + f"""
<section class="section section--tight">
  <div class="shell">
    {estimator_block()}
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="contact-grid">
      <div>{quote_form()}</div>
      <div>
        <div class="info-card">
          <h3 class="h-sm">Rather just talk?</h3>
          <p class="mt-1" style="color:var(--ink-soft);font-size:.96rem">Call and we'll
          quote you over the phone in about three minutes.</p>
          <ul class="info-list mt-2">
            <li><span class="ico">{icon('phone', 18)}</span>
              <span><span class="k">Phone</span>
              <span class="v"><a href="tel:{TEL}">{PHONE}</a></span></span></li>
            <li><span class="ico">{icon('mail', 18)}</span>
              <span><span class="k">Email</span>
              <span class="v"><a href="mailto:{B['email']}">{B['email']}</a></span></span></li>
            <li><span class="ico">{icon('clock', 18)}</span>
              <span><span class="k">Reply time</span>
              <span class="v">A written quote<span>No obligation, no charge</span></span></span></li>
          </ul>
        </div>
        <div class="info-card">
          <h3 class="h-sm">What happens next</h3>
          <div class="steps mt-2">
            <div class="step" style="padding-top:2.4rem">
              <h3 class="h-sm">We read it properly</h3>
              <p>A person, not an autoresponder. If something's unclear we'll call you.</p>
            </div>
            <div class="step" style="padding-top:2.4rem">
              <h3 class="h-sm">You get a firm price</h3>
              <p>In writing, itemised, with the task list attached — so you can compare it properly.</p>
            </div>
            <div class="step" style="padding-top:2.4rem">
              <h3 class="h-sm">You decide</h3>
              <p>Take your time. We send the quote and leave the decision with you.</p>
            </div>
          </div>
        </div>
        <div class="info-card">
          <div class="form-note">{icon('shield', 17)}
          <span>Your details are used only to prepare and send this quote. We don't
          sell or share them, ever. <a href="privacy.html">Privacy policy</a>.</span></div>
        </div>
      </div>
    </div>
  </div>
</section>

{faq_block(HOME_FAQ[:4], "Before you send it")}
"""
    page(
        "quote.html",
        f"Free Cleaning Quote {B['city']} | Instant Estimate | {B['name']}",
        "Request a free cleaning quote for your Edmonton home or business. Tell us the "
        "details and we send back a written price — no walkthrough needed for most homes.",
        body,
        schemas=[breadcrumbs([("Home", "index.html"), ("Free Quote", None)])],
        keywords="cleaning quote Edmonton, house cleaning prices Edmonton, free "
                 "cleaning estimate Edmonton",
    )


def build_book():
    slots = [
        ("8:00 – 10:00 am", "s1"), ("10:00 – 12:00 pm", "s2"),
        ("12:00 – 2:00 pm", "s3"), ("2:00 – 4:00 pm", "s4"),
        ("4:00 – 6:00 pm", "s5"), ("Flexible — any time", "s6"),
    ]
    slot_html = "".join(
        f'<input type="radio" name="slot" id="{sid}" value="{lab}"'
        f'{" checked" if i == 0 else ""}><label for="{sid}">{lab}</label>'
        for i, (lab, sid) in enumerate(slots)
    )
    services = [
        ("residential", "Regular house clean"), ("deep", "Deep clean"),
        ("moveinout", "Move in / move out"), ("carpet", "Carpet cleaning"),
        ("commercial", "Commercial / office"),
    ]
    svc = "".join(
        f'<input type="radio" name="service" id="bsvc-{v}" value="{v}"'
        f'{" checked" if i == 0 else ""}><label for="bsvc-{v}">{l}</label>'
        for i, (v, l) in enumerate(services)
    )
    freqs = [("onetime", "One-time", ""), ("monthly", "Monthly", DISCOUNT_TAG[0]),
             ("biweekly", "Every 2 weeks", DISCOUNT_TAG[1]),
             ("weekly", "Weekly", DISCOUNT_TAG[2])]
    frq = "".join(
        f'<input type="radio" name="frequency" id="bfrq-{v}" value="{v}"'
        f'{" checked" if i == 0 else ""}><label for="bfrq-{v}">{l}{t}</label>'
        for i, (v, l, t) in enumerate(freqs)
    )
    extras = [("fridge", "Inside fridge", 35), ("oven", "Inside oven", 35),
              ("windows", "Interior windows", 55), ("laundry", "Laundry", 25),
              ("garage", "Garage", 45), ("basement", "Finished basement", 40)]
    ext = "".join(
        f'<input type="checkbox" name="extras" id="bex-{v}" value="{v}">'
        f'<label for="bex-{v}">{l}'
        + (f' <span class="tag">+${p}</span>' if claim("show_prices") else "")
        + "</label>"
        for v, l, p in extras
    )
    book_prices_attr = "" if claim("show_prices") else ' data-prices="off"'
    if claim("show_prices"):
        summary_total = f"""
          <div class="summary-total">
            <span class="k">Estimated</span>
            <span class="v" id="booking-total">$0</span>
          </div>
          <p class="field-hint mt-2">Estimate only — confirmed in writing before we start.</p>"""
    else:
        summary_total = """
          <div class="summary-total">
            <span class="k">Price</span>
            <span class="v" style="font-size:1.1rem">Quoted in writing</span>
          </div>
          <p class="field-hint mt-2">We confirm the slot and the price with you before
          anything is booked in. Nothing is charged online.</p>"""

    body = page_head(
        "Book online",
        'Pick a day.<br>We\'ll <span class="tilt">confirm</span> within the hour.',
        "Choose your service, date and arrival window. Nothing is charged online — we "
        "confirm the slot and the price by phone or email first.",
        [("Home", "index.html"), ("Book Online", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="contact-grid">
      <form class="est-panel" id="booking-form"{book_prices_attr} data-form novalidate>
        <span class="eyebrow">Step 1 — the job</span>
        <div class="field field--full mt-1">
          <span class="field-label">Service</span>
          <div class="choice">{svc}</div>
        </div>
        <div class="field-grid mt-2">
          <div class="field">
            <span class="field-label">Bedrooms</span>
            <div class="stepper" data-stepper data-min="0" data-max="10">
              <button type="button" data-step="down" aria-label="Fewer bedrooms">&minus;</button>
              <output>3</output><input type="hidden" name="bedrooms" value="3">
              <button type="button" data-step="up" aria-label="More bedrooms">+</button>
            </div>
          </div>
          <div class="field">
            <span class="field-label">Bathrooms</span>
            <div class="stepper" data-stepper data-min="0" data-max="10">
              <button type="button" data-step="down" aria-label="Fewer bathrooms">&minus;</button>
              <output>2</output><input type="hidden" name="bathrooms" value="2">
              <button type="button" data-step="up" aria-label="More bathrooms">+</button>
            </div>
          </div>
          <div class="field field--full">
            <label for="b-sqft">Approximate size (sq ft) <span class="field-hint">— optional</span></label>
            <input type="number" id="b-sqft" name="sqft" min="0" max="20000" step="50" placeholder="e.g. 1600" inputmode="numeric">
          </div>
        </div>
        <div class="field field--full mt-2">
          <span class="field-label">How often</span>
          <div class="choice">{frq}</div>
        </div>
        <div class="field field--full mt-2">
          <span class="field-label">Add-ons</span>
          <div class="choice">{ext}</div>
        </div>

        <hr style="border:0;border-top:1px solid var(--line-soft);margin:2rem 0">

        <span class="eyebrow">Step 2 — when</span>
        <div class="field-grid mt-1">
          <div class="field">
            <label for="b-date">Preferred date *</label>
            <input type="date" id="b-date" name="date" required>
          </div>
          <div class="field field--full">
            <span class="field-label">Arrival window</span>
            <div class="slots">{slot_html}</div>
          </div>
        </div>

        <hr style="border:0;border-top:1px solid var(--line-soft);margin:2rem 0">

        <span class="eyebrow">Step 3 — you</span>
        <div class="field-grid mt-1">
          <div class="field">
            <label for="b-name">Name *</label>
            <input type="text" id="b-name" name="name" required autocomplete="name">
          </div>
          <div class="field">
            <label for="b-phone">Phone *</label>
            <input type="tel" id="b-phone" name="phone" required autocomplete="tel" placeholder="(780) 000-0000">
          </div>
          <div class="field">
            <label for="b-email">Email *</label>
            <input type="email" id="b-email" name="email" required autocomplete="email">
          </div>
          <div class="field">
            <label for="b-city">City *</label>
            <input type="text" id="b-city" name="city" required placeholder="Edmonton" autocomplete="address-level2">
          </div>
          <div class="field field--full">
            <label for="b-address">Address</label>
            <input type="text" id="b-address" name="address" autocomplete="street-address" placeholder="Street address — optional until we confirm">
          </div>
          <div class="field field--full">
            <label for="b-notes">Access notes, pets, parking, anything unusual</label>
            <textarea id="b-notes" name="notes" placeholder="Back door code is 1234, two friendly dogs, parking on the street…"></textarea>
          </div>
          <input type="hidden" name="estimate" value="">
          <input type="hidden" name="_subject" value="New online booking — fastandperfect.ca">
          <div class="hp" aria-hidden="true">
            <label for="b-gotcha">Leave this blank</label>
            <input type="text" id="b-gotcha" name="_gotcha" tabindex="-1" autocomplete="off">
          </div>
          <div class="field field--full">
            <label class="consent">
              <input type="checkbox" name="consent" required>
              <span>I agree to be contacted by {B['legal_name']} to confirm this booking.
              <a href="privacy.html">Privacy policy</a>.</span>
            </label>
          </div>
          <div class="field field--full">
            <div class="form-note">{icon('shield', 17)}
            <span>Nothing is charged now. We confirm the slot and the final price with
            you first — you can change or cancel free up to 24 hours before.</span></div>
          </div>
          <div class="field field--full">
            <button class="btn btn--gold btn--lg btn--block" type="submit">
              {icon('calendar', 17)} Request this booking
            </button>
          </div>
        </div>
        <div class="form-status" aria-live="polite"></div>
      </form>

      <aside>
        <div class="summary-card">
          <span class="eyebrow">Your booking</span>
          <h3 class="h-sm">Summary</h3>
          <ul class="summary-list" id="booking-summary"></ul>{summary_total}
          <a class="btn btn--ghost btn--block mt-2" href="tel:{TEL}">{icon('phone', 16)} Prefer to call?</a>
        </div>
      </aside>
    </div>
  </div>
</section>

{cta_band(
    'Not sure which service you <span class="tilt--gold">need</span>?',
    "Call us and describe the place in thirty seconds. We'll tell you what it needs — "
    "and if a cheaper option would do the job, we'll say so."
)}
"""
    page(
        "book.html",
        f"Book a Cleaning Online — {B['city']} | {B['name']}",
        "Book residential, commercial or carpet cleaning in Edmonton online. Pick "
        "your date and arrival window and we will confirm it with you. Nothing is "
        "charged online.",
        body,
        schemas=[breadcrumbs([("Home", "index.html"), ("Book Online", None)])],
    )


def build_contact():
    hours = "".join(f"<li><span>{d}</span><b>{t}</b></li>" for d, t in B["hours"])
    body = page_head(
        "Contact",
        'Talk to an actual <span class="tilt">person</span>.',
        "Call, email or send the form. Whichever you pick, someone local answers — "
        "usually within the hour, Monday to Saturday.",
        [("Home", "index.html"), ("Contact", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="contact-grid">
      <div>{quote_form("contact-form")}</div>
      <div>
        <div class="info-card">
          <h3 class="h-sm">Reach us directly</h3>
          <ul class="info-list mt-2">
            <li><span class="ico">{icon('phone', 18)}</span>
              <span><span class="k">Phone</span>
              <span class="v"><a href="tel:{TEL}">{PHONE}</a><span>Fastest way to reach us</span></span></span></li>
            <li><span class="ico">{icon('mail', 18)}</span>
              <span><span class="k">Email</span>
              <span class="v"><a href="mailto:{B['email']}">{B['email']}</a></span></span></li>
            <li><span class="ico">{icon('pin', 18)}</span>
              <span><span class="k">Service area</span>
              <span class="v">{B['city']}, {B['region']}<span>Plus 11 surrounding communities —
              <a href="service-areas.html">see the list</a></span></span></span></li>
          </ul>
        </div>
        <div class="info-card">
          <h3 class="h-sm">{icon('clock', 17)} Hours</h3>
          <ul class="hours-list mt-2">{hours}</ul>
          <p class="field-hint mt-2">Commercial contracts are cleaned outside these hours
          by arrangement — evenings, early mornings and weekends.</p>
        </div>
        <div class="info-card">
          <h3 class="h-sm">Follow along</h3>
          <p class="mt-1" style="color:var(--ink-soft);font-size:.95rem">Before-and-afters,
          seasonal offers and the occasional satisfying carpet video.</p>
          <div class="socials mt-2" style="--sage-deep:var(--pine)">
            <a href="{B['social']['facebook']}" aria-label="Facebook" style="border-color:var(--line)">{icon('facebook', 18)}</a>
            <a href="{B['social']['instagram']}" aria-label="Instagram" style="border-color:var(--line)">{icon('instagram', 18)}</a>
            <a href="{B['social']['tiktok']}" aria-label="TikTok" style="border-color:var(--line)">{icon('tiktok', 18)}</a>
            <a href="{B['social']['google']}" aria-label="Google Business Profile" style="border-color:var(--line)">{icon('google', 18)}</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

{cta_band(
    'Or skip ahead and <span class="tilt--gold">book a slot</span>.',
    "If you already know what you need, pick a date and we'll confirm it within the hour."
)}
"""
    page(
        "contact.html",
        f"Contact {B['legal_name']} | Cleaning Services {B['city']}",
        f"Contact Fast and Perfect Ltd. for cleaning in Edmonton and area. Call "
        f"{PHONE}, email us, or send the form and we will get back to you.",
        body,
        schemas=[
            local_business_schema(),
            breadcrumbs([("Home", "index.html"), ("Contact", None)]),
        ],
    )


def build_privacy():
    body = page_head(
        "Legal",
        "Privacy Policy",
        f"How {B['legal_name']} collects, uses and protects the information you give us.",
        [("Home", "index.html"), ("Privacy Policy", None)],
    ) + f"""
<section class="section">
  <div class="shell" style="max-width:820px">
    <div class="prose">
      <p class="field-hint">Last updated: <span data-year>2026</span></p>

      <p class="lede mt-2">{B['legal_name']} ("we", "us") operates this website and provides
      cleaning services in {B['city']}, {B['region_full']}. This policy explains what
      personal information we collect and what we do with it, in line with Canada's
      Personal Information Protection and Electronic Documents Act (PIPEDA) and
      Alberta's Personal Information Protection Act (PIPA).</p>

      <h2 class="h-md">What we collect</h2>
      <ul>
        <li><b>Information you give us</b> — your name, phone number, email address,
        service address and any details you include in a quote request, booking or
        message.</li>
        <li><b>Service records</b> — the work performed at your property, access
        instructions you've provided, and payment records.</li>
        <li><b>Website analytics</b> — if analytics is enabled, aggregated data about
        pages visited and how visitors arrived. This does not identify you personally.</li>
        <li><b>Advertising measurement</b> — if advertising tags are installed, our ad
        platforms may record that a visit or enquiry came from one of our ads.</li>
      </ul>

      <h2 class="h-md">Why we collect it</h2>
      <ul>
        <li>To prepare and send the quote you asked for.</li>
        <li>To schedule, perform and invoice cleaning services.</li>
        <li>To contact you about a booking, including confirmations and reminders.</li>
        <li>To improve the website and understand which services people look for.</li>
      </ul>
      <p>We only use your information for the purpose you gave it to us for. If we ever
      want to use it for something else, we'll ask first.</p>

      <h2 class="h-md">What we never do</h2>
      <ul>
        <li>We do not sell, rent or trade your personal information to anyone.</li>
        <li>We do not add you to a marketing list without your consent.</li>
        <li>We do not share your address or access details with anyone outside the crew
        assigned to your property.</li>
      </ul>

      <h2 class="h-md">Who we share it with</h2>
      <p>Only where it's necessary to deliver the service: our own cleaning staff, our
      payment processor, and service providers that host this website or deliver our
      form submissions. Each is bound to protect your information. We may also disclose
      information where required by law.</p>

      <h2 class="h-md">How long we keep it</h2>
      <p>Quote requests that don't become bookings are deleted within 12 months. Client
      service and invoicing records are kept for seven years as required by the Canada
      Revenue Agency, then destroyed.</p>

      <h2 class="h-md">Keys, codes and access</h2>
      <p>Keys and fobs are numbered and stored in a locked cabinet, never labelled with
      your address. Alarm codes are recorded separately and issued only to the crew
      assigned to your property. You can ask us to return or destroy them at any time.</p>

      <h2 class="h-md">Cookies</h2>
      <p>This site uses only the cookies required for it to work, plus any analytics or
      advertising cookies noted above. You can block cookies in your browser settings;
      the site will still function.</p>

      <h2 class="h-md">Your rights</h2>
      <p>You can ask us what personal information we hold about you, ask for it to be
      corrected, or ask us to delete it. Contact us and we'll respond within 30 days.
      If you're not satisfied with our answer, you may contact the Office of the
      Information and Privacy Commissioner of Alberta.</p>

      <h2 class="h-md">Contact</h2>
      <p>{B['legal_name']}<br>
      {B['city']}, {B['region_full']}, Canada<br>
      Phone: <a href="tel:{TEL}">{PHONE}</a><br>
      Email: <a href="mailto:{B['email']}">{B['email']}</a></p>
    </div>
  </div>
</section>
"""
    page(
        "privacy.html",
        f"Privacy Policy | {B['legal_name']}",
        "How Fast and Perfect Ltd. collects, uses and protects your personal "
        "information, under PIPEDA and Alberta's PIPA.",
        body,
        schemas=[breadcrumbs([("Home", "index.html"), ("Privacy Policy", None)])],
    )


# ---------------------------------------------------------------- extras
PAGES_FOR_SITEMAP = [
    ("index.html", "1.0", "weekly"),
    ("residential-cleaning.html", "0.9", "monthly"),
    ("commercial-cleaning.html", "0.9", "monthly"),
    ("carpet-cleaning.html", "0.9", "monthly"),
    ("quote.html", "0.9", "monthly"),
    ("book.html", "0.8", "monthly"),
    ("service-areas.html", "0.8", "monthly"),
    ("gallery.html", "0.7", "monthly"),
    ("about.html", "0.6", "yearly"),
    ("contact.html", "0.7", "yearly"),
    ("privacy.html", "0.3", "yearly"),
]


def build_admin_pricing():
    """Private price editor. Not linked from the site, noindex, and blocked
    in robots.txt. It contains no customer data — only the prices, which are
    published on the carpet page anyway."""
    body = page_head(
        "Owner tools",
        'Price <span class="tilt">editor</span>.',
        "Change any carpet or upholstery price here, check the preview, then "
        "download the updated file and upload it to the site. No code involved.",
        [("Home", "index.html"), ("Price editor", None)],
    ) + f"""
<section class="section section--tight">
  <div class="shell" id="price-editor">
    <div class="contact-grid">
      <div>
        <div id="editor-fields"></div>
      </div>
      <aside>
        <div class="summary-card">
          <span class="eyebrow">Live preview</span>
          <h3 class="h-sm">What customers would see</h3>
          <div class="table-wrap mt-2">
            <table class="rate-table">
              <thead><tr><th>Example job</th><th>Estimate</th></tr></thead>
              <tbody id="preview-body"></tbody>
            </table>
          </div>
          <div class="form-status" id="editor-status"></div>
          <div class="drawer__actions">
            <button class="btn btn--gold btn--block" type="button" id="btn-download">
              Download pricing.json</button>
            <button class="btn btn--ghost btn--block" type="button" id="btn-copy">
              Copy to clipboard</button>
            <button class="btn btn--ghost btn--block" type="button" id="btn-reset">
              Undo all changes</button>
          </div>
          <div class="form-note mt-2">{icon('shield', 17)}
            <span>Downloading does not publish anything. To go live, upload the
            file to <code>assets/data/pricing.json</code>, replacing the old one.
            The calculator and the rate table both update immediately.</span></div>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="section section--tight bg-paper">
  <div class="shell" style="max-width:820px">
    <div class="prose">
      <h2 class="h-md">How this works</h2>
      <ol style="color:var(--ink-soft);padding-left:1.2rem">
        <li>Change any price above. The preview on the right updates as you type.</li>
        <li>Click <b>Download pricing.json</b>.</li>
        <li>Upload that file to your web host, into the
        <code>assets/data/</code> folder, replacing the existing
        <code>pricing.json</code>.</li>
        <li>Refresh the carpet page — the calculator and the published rate
        table both use the new prices straight away.</li>
      </ol>
      <p class="mt-2">Nothing else needs editing. The prices exist in exactly one
      file, so the calculator and the rate table can never disagree.</p>
      <p><b>Note:</b> this page is hidden from Google and not linked anywhere on
      the site, but it is not password protected — a static site has no login.
      It only shows prices, which are public on the carpet page anyway. If you
      want it behind a password later, that needs hosting that supports it and
      I can set that up.</p>
    </div>
  </div>
</section>
"""
    page(
        "admin-pricing.html",
        f"Price editor — {B['legal_name']} (private)",
        "Private price editor for Fast and Perfect Ltd.",
        body,
        schemas=[],
        noindex=True,
        extra_js=["assets/js/carpet-calculator.js", "assets/js/admin-pricing.js"],
    )


def build_sitemap():
    urls = "".join(
        f"<url><loc>{B['domain']}/{'' if s == 'index.html' else s}</loc>"
        f"<changefreq>{cf}</changefreq><priority>{p}</priority></url>"
        for s, p, cf in PAGES_FOR_SITEMAP
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)

    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin-pricing.html\n\n"
        f"Sitemap: {B['domain']}/sitemap.xml\n"
    )
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(robots)


def build_404():
    body = f"""
<section class="section" style="text-align:center;padding-block:clamp(5rem,12vw,9rem)">
  <div class="shell" style="max-width:640px">
    <span class="eyebrow eyebrow--center">404</span>
    <h1 class="h-xl">That page took<br>the <span class="tilt">day off</span>.</h1>
    <p class="lede mt-2" style="margin-inline:auto">The link's broken or the page moved.
    Here's the way back.</p>
    <div class="cta-band__actions">
      <a class="btn btn--gold btn--lg" href="index.html">Back to home</a>
      <a class="btn btn--ghost btn--lg" href="quote.html">Get a free quote</a>
    </div>
  </div>
</section>
"""
    page("404.html", f"Page not found | {B['legal_name']}",
         "That page couldn't be found.", body,
         schemas=[])
    # 404 shouldn't be indexed
    p = os.path.join(SITE, "404.html")
    with open(p, encoding="utf-8") as fh:
        c = fh.read()
    c = c.replace('content="index, follow, max-image-preview:large"', 'content="noindex, follow"')
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(c)


def main():
    os.makedirs(SITE, exist_ok=True)
    build_home()
    build_residential()
    build_commercial()
    build_carpet()
    build_gallery()
    build_about()
    build_areas()
    build_quote()
    build_book()
    build_contact()
    build_privacy()
    build_404()
    build_admin_pricing()
    build_sitemap()

    files = sorted(f for f in os.listdir(SITE) if f.endswith((".html", ".xml", ".txt")))
    total = 0
    for f in files:
        size = os.path.getsize(os.path.join(SITE, f))
        total += size
        print(f"  {f:32s} {size:>8,} bytes")
    print(f"\n  {len(files)} files, {total:,} bytes of HTML/XML")


if __name__ == "__main__":
    main()
