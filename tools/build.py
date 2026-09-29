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
    "areas": [
        "Edmonton", "St. Albert", "Sherwood Park", "Spruce Grove", "Leduc",
        "Beaumont", "Stony Plain", "Fort Saskatchewan", "Devon", "Nisku",
        "Morinville", "Ardrossan",
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

B = BUSINESS
TEL = B["phone_href"]
PHONE = B["phone_display"]


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
        <p class="footer-about">Locally owned cleaning company serving {B['city']} and
        surrounding communities. Insured, bonded and backed by a 24-hour
        satisfaction guarantee.</p>
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
        "priceRange": "$$",
        "currenciesAccepted": "CAD",
        "paymentAccepted": "Cash, Debit, Credit Card, e-Transfer",
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


def service_schema(name, desc, low, high, unit="visit"):
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": name,
        "provider": {"@id": B["domain"] + "/#business"},
        "areaServed": [{"@type": "City", "name": a} for a in B["areas"]],
        "description": desc,
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "CAD",
            "lowPrice": str(low),
            "highPrice": str(high),
            "offerCount": "5",
        },
    }


# ---------------------------------------------------------------- shell
def page(slug, title, description, body, schemas=None, current=None, keywords=None):
    current = current or slug
    schemas = schemas or []
    blocks = "".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>'
        for s in schemas
    )
    canonical = B["domain"] + "/" + ("" if slug == "index.html" else slug)
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
<meta name="robots" content="index, follow, max-image-preview:large">
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
<script src="assets/js/main.js" defer></script>
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


def cta_band(title=None, text=None):
    title = title or 'Ready for a place that <span class="tilt--gold">actually</span> feels clean?'
    text = text or (
        "Tell us about your space and we'll send a firm, itemised quote — "
        "usually within one business hour. No pressure, no obligation."
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
    items = [
        ("shield", "Insured &amp; bonded"),
        ("check", "Police-checked cleaners"),
        ("leaf", "Pet &amp; child-safe products"),
        ("repeat", "24-hour re-clean guarantee"),
    ]
    lis = "".join(f"<li>{icon(i, 17)} {t}</li>" for i, t in items)
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
        ("monthly", "Monthly", '<span class="tag">-10%</span>'),
        ("biweekly", "Every 2 weeks", '<span class="tag">-15%</span>'),
        ("weekly", "Weekly", '<span class="tag">-20%</span>'),
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
        f'<label for="ex-{v}">{l} <span class="tag">+${p}</span></label>'
        for v, l, p in extras
    )
    cta = (
        f'<button class="btn btn--gold btn--block" type="button" id="est-continue">'
        f"Send me this quote {icon('arrow', 16)}</button>"
        if with_cta else
        f'<a class="btn btn--gold btn--block" href="quote.html">Send me this quote {icon("arrow", 16)}</a>'
    )
    return f"""
<div class="estimator">
  <form class="est-panel" id="{form_id}" novalidate>
    <div class="field field--full">
      <span class="field-label">What do you need cleaned?</span>
      <div class="choice">{svc}</div>
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

  <aside class="est-result">
    <span class="est-result__label">Your estimated price</span>
    <div class="est-price" id="est-price">$0</div>
    <p class="est-sub" id="est-sub"></p>
    <ul class="est-break" id="est-breakdown"></ul>
    {cta}
    <p class="est-foot">Instant estimate only. We confirm the final price in writing
    before any work starts — and we never charge more than the quote.</p>
  </aside>
</div>
"""


def quote_form(form_id="quote-form", heading=True):
    head = (
        '<span class="eyebrow">Request a quote</span>'
        '<h2 class="h-md">Tell us about your space</h2>'
        '<p class="lede mt-1">We reply within one business hour, Monday to Saturday.</p>'
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
        Or call {PHONE} — we usually pick up on the first ring.
      </p>
    </div>
  </div>
  <div class="form-status" aria-live="polite"></div>
</form>
"""


# ---------------------------------------------------------------- content
TESTIMONIALS = [
    ("Priya M.", "Windermere, Edmonton",
     "Booked a deep clean before my in-laws arrived and honestly the kitchen "
     "looked better than the day we moved in. The team showed up on time, "
     "worked around my toddler napping, and the price was exactly what was quoted."),
    ("Dan R.", "Sherwood Park",
     "We use them every two weeks for the house. Same two cleaners each time, "
     "which matters — they know where everything goes now. Easiest recurring "
     "bill I pay."),
    ("Chelsea O.", "Downtown Edmonton",
     "Move-out clean on a condo I was sure I'd lose the deposit on. Got every "
     "dollar back. The landlord actually asked who I'd used."),
    ("Marcus T.", "Leduc",
     "Our office had carpet stains from years of coffee runs. They lifted 90% "
     "of it and the place stopped smelling like an office. Booked them quarterly."),
    ("Amrit S.", "Terwillegar",
     "Three cats, long-haired, you can imagine. No complaints, no upcharges, "
     "and they use products that don't set off my asthma. Worth every penny."),
    ("Joanne K.", "St. Albert",
     "I've tried four cleaning companies in this city. This is the first one "
     "that sent the same crew twice and answered the phone when I called."),
]


def testimonial_cards(n=3, start=0):
    cards = []
    for name, where, text in TESTIMONIALS[start:start + n]:
        initials = "".join(p[0] for p in name.split()[:2]).upper()
        stars = "".join(icon("star", 14) for _ in range(5))
        cards.append(f"""
<figure class="quote-card reveal">
  <div class="stars" aria-label="5 out of 5 stars">{stars}</div>
  <blockquote>{text}</blockquote>
  <figcaption>
    <span class="avatar" aria-hidden="true">{initials}</span>
    <span><span class="who">{name}</span><span class="where">{where}</span></span>
  </figcaption>
</figure>""")
    return "".join(cards)


HOME_FAQ = [
    ("Do I need to be home during the cleaning?",
     "Not at all. Most of our recurring clients give us a door code or a key we keep "
     "logged and secured. You're welcome to be home too — whatever you're comfortable with."),
    ("Are you insured and bonded?",
     "Yes. We carry full liability insurance and every cleaner is bonded and "
     "criminal-record checked before their first shift. We can send you a copy of "
     "our certificate of insurance on request."),
    ("What if I'm not happy with the clean?",
     "Call us within 24 hours and we come back and re-do whatever missed the mark, "
     "free. No arguing, no invoice. That guarantee is why most of our work comes "
     "from referrals."),
    ("Do you bring your own supplies and equipment?",
     "Yes — everything, including vacuums, microfibre and eco-friendly products that "
     "are safe around pets and kids. If you'd rather we use your products because of "
     "allergies or a specific surface, just leave them out and tell us."),
    ("How much does a cleaning cost in Edmonton?",
     "Most regular 3-bed / 2-bath homes in Edmonton land between $150 and $210 per "
     "visit, and recurring plans come down from there. Use the instant estimator on "
     "this page for a number specific to your home, then we confirm it in writing."),
    ("Which areas do you cover?",
     "Edmonton and the surrounding communities — St. Albert, Sherwood Park, Spruce "
     "Grove, Leduc, Beaumont, Stony Plain, Fort Saskatchewan, Devon, Nisku, "
     "Morinville and Ardrossan. If you're just outside that, call and ask."),
]


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
         "Weekly, bi-weekly, monthly or one-time. Kitchens, bathrooms, floors, "
         "dusting — done properly, by the same crew each visit.",
         ["Regular &amp; recurring cleans", "Deep cleans", "Move in / move out", "Post-renovation"],
         "$135"),
        ("service-commercial.svg", "Commercial Cleaning", "commercial-cleaning.html",
         "Offices, clinics, salons, retail and small warehouses across Edmonton. "
         "After-hours scheduling so your staff never trip over a mop.",
         ["Offices &amp; clinics", "Retail &amp; salons", "Common areas", "Nightly or weekly contracts"],
         "$160"),
        ("service-carpet.svg", "Carpet &amp; Upholstery", "carpet-cleaning.html",
         "Hot-water extraction that lifts ground-in traffic lanes, pet accidents "
         "and years of spilled coffee. Dry in 4–6 hours.",
         ["Carpets &amp; area rugs", "Sofas &amp; mattresses", "Pet odour treatment", "Stain protection"],
         "$89"),
    ]
    cards = ""
    for i, (img, title, href, desc, bullets, price) in enumerate(services):
        lis = "".join(f"<li>{b}</li>" for b in bullets)
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
      <div class="price-from">from <b>{price}</b></div>
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
      <p class="lede anim">Reliable residential, commercial and carpet cleaning across
      {B['city']} and the surrounding communities. Same crew every visit, a firm price
      before we start, and a 24-hour guarantee if anything's missed.</p>
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
      <div class="float-card float-card--rating">
        <span class="stars" aria-hidden="true">{''.join(icon('star', 14) for _ in range(5))}</span>
        <span><span class="rating-num">4.9</span>
        <span class="rating-sub">from local reviews</span></span>
      </div>
      <div class="float-card float-card--quote">
        <span class="fc-label">3 bed / 2 bath</span>
        <div class="fc-price">$165</div>
        <p class="fc-note">Typical recurring clean in Edmonton — quoted in writing, never exceeded.</p>
      </div>
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
      <span class="eyebrow eyebrow--light">Why {B['city']} keeps calling us back</span>
      <h2 class="h-lg">The boring things<br>done <span class="tilt--gold">reliably</span>.</h2>
    </div>
    <div class="stat-grid">
      <div class="stat reveal"><div class="stat__num">24hr</div>
        <div class="stat__label">Re-clean guarantee — we come back free</div></div>
      <div class="stat reveal" data-delay="80"><div class="stat__num">4.9&#8239;★</div>
        <div class="stat__label">Average rating from local customers</div></div>
      <div class="stat reveal" data-delay="160"><div class="stat__num">12</div>
        <div class="stat__label">Communities served around Edmonton</div></div>
      <div class="stat reveal" data-delay="240"><div class="stat__num">$0</div>
        <div class="stat__label">Surprise charges. The quote is the price.</div></div>
    </div>
  </div>
</section>

<section class="section" id="estimate">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Instant estimate</span>
      <h2 class="h-lg">Know the price <span class="tilt">before</span> you call.</h2>
      <p class="lede">Most cleaning companies make you book a walkthrough just to hear a
      number. Move the sliders and see yours right now — then we confirm it in writing.</p>
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
        <p>Use the estimator above or call us. Takes about ninety seconds — bedrooms,
        bathrooms, how often, anything unusual.</p>
      </div>
      <div class="step reveal" data-delay="90">
        <h3 class="h-sm">Get a firm written quote</h3>
        <p>We confirm the price and the checklist in writing, usually within one
        business hour. If we can't do it for that, we say so upfront.</p>
      </div>
      <div class="step reveal" data-delay="180">
        <h3 class="h-sm">We show up and clean</h3>
        <p>Same crew, same day each visit, all supplies included. Not happy with
        something? Call within 24 hours and we re-do it free.</p>
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
          <li>{icon('check', 18)}<span><b>A written checklist</b> you get after every clean, so you know exactly what was done.</span></li>
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

<section class="section">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Reviews</span>
      <h2 class="h-lg">What Edmonton says.</h2>
    </div>
    <div class="grid grid--3">{testimonial_cards(3)}</div>
  </div>
</section>

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
        "Trusted residential, commercial and carpet cleaning in Edmonton and area. "
        "Insured and bonded, firm written quotes, 24-hour satisfaction guarantee. "
        "Get a free quote in one business hour.",
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
         "A typical 3-bed / 2-bath home takes three to four hours with two cleaners. "
         "First-time and deep cleans run longer because there's more built-up work to do."),
        ("What's the difference between a regular clean and a deep clean?",
         "A regular clean maintains a home that's already in decent shape. A deep clean "
         "adds the things that only need doing a few times a year — inside the oven and "
         "fridge, behind appliances, window tracks, light fixtures, baseboards scrubbed "
         "rather than wiped. Most people start with one deep clean, then go recurring."),
        ("Can I get the same cleaners every time?",
         "Yes, and that's our default for recurring clients. The same crew learns your "
         "home — where the spare vacuum bag lives, which door sticks, that the guest room "
         "gets skipped in winter."),
        ("Do you do laundry or dishes?",
         "Dishes in the sink get washed or loaded as part of a standard kitchen clean. "
         "Laundry is a $25 add-on — we'll run and fold one load while we work."),
        ("What about pets?",
         "No problem at all, and no pet surcharge. Just let us know so we watch the doors. "
         "Our products are pet-safe. If an animal is anxious around strangers, tell us and "
         "we'll work around a closed door."),
    ]

    body = page_head(
        "Residential",
        'House Cleaning in Edmonton<br>done <span class="tilt">the same way</span> every time.',
        "Weekly, bi-weekly, monthly or one-off cleans for homes, condos and townhouses "
        "across Edmonton and area. Same crew, written checklist, firm price.",
        [("Home", "index.html"), ("Services", "residential-cleaning.html"), ("Residential Cleaning", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="split">
      <div>
        <span class="eyebrow">What's included</span>
        <h2 class="h-lg">Every clean follows<br>the same <span class="tilt">checklist</span>.</h2>
        <p class="lede mt-2">Not a vague "general tidy". A written list, the same one
        every visit, that you get a copy of when we're done — so you can see exactly
        what was covered and tell us if something should be added.</p>
        <ul class="check-list">
          <li>{icon('check', 18)}<span><b>All supplies and equipment included</b> — nothing for you to buy or store.</span></li>
          <li>{icon('check', 18)}<span><b>Eco-friendly, pet and child-safe products</b> as standard, or we'll use yours.</span></li>
          <li>{icon('check', 18)}<span><b>Flexible entry</b> — be home, leave a key, or give us a door code.</span></li>
          <li>{icon('check', 18)}<span><b>24-hour re-clean guarantee</b> on everything we touch.</span></li>
        </ul>
        <div class="hero__actions mt-3">
          <a class="btn btn--gold" href="quote.html">Get my price</a>
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

<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Pricing</span>
      <h2 class="h-lg">Typical Edmonton prices.</h2>
      <p class="lede">Real ranges, not "call for pricing". Recurring plans take 10–20%
      off these numbers. Your written quote is the price you pay.</p>
    </div>
    <div class="table-wrap reveal">
      <table class="rate-table">
        <thead><tr><th>Home size</th><th>Typical duration</th><th>Price range</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <p class="field-hint mt-2">Prices in CAD, including all supplies and GST-exclusive.
    Heavier first-time cleans are quoted individually after a quick photo or video walkthrough.</p>
  </div>
</section>

<section class="section bg-sage">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Instant estimate</span>
      <h2 class="h-lg">Price your home now.</h2>
    </div>
    {estimator_block("estimator-form", with_cta=False)}
  </div>
</section>

<section class="section">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Reviews</span>
      <h2 class="h-lg">From homes like yours.</h2>
    </div>
    <div class="grid grid--3">{testimonial_cards(3, 0)}</div>
  </div>
</section>

{faq_block(faqs, "Residential cleaning questions")}
{cta_band()}
"""
    page(
        "residential-cleaning.html",
        f"House Cleaning {B['city']} | Weekly, Deep & Move-Out | {B['name']}",
        "Professional house cleaning in Edmonton — weekly, bi-weekly, deep and "
        "move-out cleans. Same crew every visit, all supplies included, from $120. "
        "Insured and bonded. Free quote in one business hour.",
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
         "That's how most of our commercial contracts run — evenings, early mornings or "
         "weekends. We'll work to whatever window keeps your team and customers "
         "undisturbed."),
        ("Are your staff insured and screened for commercial sites?",
         "Yes. Full liability coverage, WCB, and every cleaner is bonded and "
         "criminal-record checked. We'll provide certificates for your records or your "
         "property manager's."),
        ("Can we start with a trial before signing a contract?",
         "Absolutely, and we'd encourage it. Most clients start with a one-off clean or a "
         "two-week trial. No lock-in, no cancellation penalty on our monthly agreements."),
        ("Do you supply consumables — paper, soap, liners?",
         "We can. Most clients find it simpler to have us manage and restock washroom "
         "supplies, billed at cost plus a small handling fee. Or keep supplying your own; "
         "we'll just flag when stock runs low."),
        ("How do you handle keys, alarm codes and access?",
         "Keys and fobs are logged, numbered and never labelled with your address. Alarm "
         "codes are stored separately and only issued to the assigned crew. We can also "
         "work with your existing access system or a lockbox."),
    ]

    body = page_head(
        "Commercial",
        'Commercial Cleaning<br>that keeps your doors <span class="tilt">open</span>.',
        "Offices, clinics, retail, salons and common areas across Edmonton. "
        "After-hours scheduling, screened and insured crews, flexible monthly "
        "agreements with no lock-in.",
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
        <p class="lede mt-2">The complaint we hear most about other commercial cleaners
        isn't the cleaning — it's not knowing whether anyone showed up. We fix that.</p>
        <ul class="check-list">
          <li>{icon('check', 18)}<span><b>Named account contact</b> who answers the phone, not a call centre.</span></li>
          <li>{icon('check', 18)}<span><b>Digital sign-off after every visit</b> — you get a timestamped record of what was done.</span></li>
          <li>{icon('check', 18)}<span><b>Monthly agreements, 30 days' notice</b> — no three-year contracts.</span></li>
          <li>{icon('check', 18)}<span><b>WCB covered, fully insured</b>, certificates provided for your files.</span></li>
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
      <h2 class="h-lg">From call to first clean<br>in about a <span class="tilt--gold">week</span>.</h2>
    </div>
    <div class="steps steps--3">
      <div class="step reveal">
        <h3 class="h-sm">Walkthrough</h3>
        <p>We visit the site, measure, and agree the scope room by room. Takes about
        twenty minutes and costs nothing.</p>
      </div>
      <div class="step reveal" data-delay="90">
        <h3 class="h-sm">Written scope &amp; price</h3>
        <p>You get a per-visit price, a frequency, and a written task list. Change it
        any time — the price moves with the scope, transparently.</p>
      </div>
      <div class="step reveal" data-delay="180">
        <h3 class="h-sm">Crew assigned</h3>
        <p>A named crew, a fixed schedule, and a first-month check-in to adjust anything
        that isn't landing right.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Reviews</span>
      <h2 class="h-lg">From local businesses.</h2>
    </div>
    <div class="grid grid--3">{testimonial_cards(3, 3)}</div>
  </div>
</section>

{faq_block(faqs, "Commercial cleaning questions")}
{cta_band(
    'Get a <span class="tilt--gold">site-specific</span> quote.',
    "Tell us the square footage and how often you need us. We'll book a twenty-minute "
    "walkthrough and come back with a written scope and a fixed per-visit price."
)}
"""
    page(
        "commercial-cleaning.html",
        f"Commercial & Office Cleaning {B['city']} | {B['name']}",
        "Commercial cleaning in Edmonton for offices, clinics, retail and common "
        "areas. After-hours schedules, insured and WCB-covered crews, monthly "
        "agreements with no lock-in. Free site walkthrough.",
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
         "backing rising to the surface. If it reappears within 48 hours, call us and we "
         "re-treat that spot free."),
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
        "Edmonton. Traffic lanes, pet accidents and years of spills — dry in four "
        "to six hours.",
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
          <li>{icon('check', 18)}<span><b>Groomed and speed-dried</b>, so you're back on it in four to six hours.</span></li>
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

<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Pricing</span>
      <h2 class="h-lg">Carpet &amp; upholstery rates.</h2>
      <p class="lede">Flat rates, published. Minimum charge $139 — we'd rather tell you
      that now than after we've parked outside.</p>
    </div>
    <div class="table-wrap reveal">
      <table class="rate-table">
        <thead><tr><th>Service</th><th>Detail</th><th>Price</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <p class="field-hint mt-2">Prices in CAD, GST-exclusive. A "room" is up to 250 sq ft;
    larger open-plan spaces count as two. Combined house-clean and carpet bookings get
    10% off the carpet portion.</p>
  </div>
</section>

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
        <p>Both sides, with an anti-allergen treatment for dust mites.</p></div></article>
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
    "Combine a house clean with carpet extraction and we take 10% off the carpet work. "
    "One visit, one invoice, one crew."
)}
"""
    page(
        "carpet-cleaning.html",
        f"Carpet Cleaning {B['city']} | Steam Extraction from $139 | {B['name']}",
        "Carpet and upholstery cleaning in Edmonton using hot-water extraction. "
        "Traffic lanes, pet odours and stains lifted, dry in 4–6 hours. Flat "
        "published rates from $139. Free quote.",
        body,
        schemas=[
            service_schema(
                "Carpet and Upholstery Cleaning",
                "Hot-water extraction carpet cleaning, upholstery and mattress "
                "cleaning across Edmonton and surrounding communities.",
                45, 600,
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

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Reviews</span>
      <h2 class="h-lg">What people said afterwards.</h2>
    </div>
    <div class="grid grid--3">{testimonial_cards(6)}</div>
  </div>
</section>

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
        'A small local crew,<br>not a <span class="tilt">franchise</span>.',
        f"{B['legal_name']} is an Edmonton-owned cleaning company. We're deliberately "
        "small, which is why you get the same faces and someone who answers the phone.",
        [("Home", "index.html"), ("About", None)],
    ) + f"""
<section class="section">
  <div class="shell">
    <div class="split">
      <div class="split__media reveal">
        <img src="assets/img/about-crew.svg" alt="The Fast and Perfect cleaning crew" loading="lazy" width="1200" height="900">
      </div>
      <div class="prose">
        <span class="eyebrow">Our story</span>
        <h2 class="h-lg">Built on the jobs<br>nobody else <span class="tilt">finished</span>.</h2>
        <p class="lede mt-2">Fast and Perfect started because of a recurring complaint we
        kept hearing from Edmonton homeowners: the first clean was great, and every one
        after that got a little thinner.</p>
        <p class="mt-2">So we built the company around the opposite. A written checklist
        that doesn't shrink. The same crew assigned to your address so standards don't
        reset with every new face. And a guarantee with an actual deadline attached —
        call within 24 hours and we come back, free, no debate.</p>
        <p>We're not the cheapest cleaners in the city and we don't pretend to be. We're
        the ones who still turn up in February when it's minus thirty and the last company
        stopped answering.</p>
      </div>
    </div>
  </div>
</section>

<section class="section band">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow eyebrow--light">What we promise</span>
      <h2 class="h-lg">Four things, <span class="tilt--gold">every time</span>.</h2>
    </div>
    <div class="stat-grid">
      <div class="stat reveal"><div class="stat__num">{icon('shield', 42, 1.6)}</div>
        <div class="stat__label">Insured, bonded and WCB covered. Certificates on request.</div></div>
      <div class="stat reveal" data-delay="80"><div class="stat__num">{icon('users', 42, 1.6)}</div>
        <div class="stat__label">The same crew at your address, not a rotating roster.</div></div>
      <div class="stat reveal" data-delay="160"><div class="stat__num">{icon('wallet', 42, 1.6)}</div>
        <div class="stat__label">The written quote is the invoice. No day-of surprises.</div></div>
      <div class="stat reveal" data-delay="240"><div class="stat__num">{icon('repeat', 42, 1.6)}</div>
        <div class="stat__label">24 hours to tell us it's wrong. We re-do it free.</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">How we hire</span>
      <h2 class="h-lg">Who's in your home.</h2>
    </div>
    <div class="steps steps--3">
      <div class="step reveal">
        <h3 class="h-sm">Screened before day one</h3>
        <p>Criminal-record check, reference checks and proof of work eligibility before
        anyone is assigned to a client address.</p>
      </div>
      <div class="step reveal" data-delay="90">
        <h3 class="h-sm">Trained on our checklist</h3>
        <p>Two weeks paired with a senior cleaner. Nobody works a property alone until
        they've been signed off room by room.</p>
      </div>
      <div class="step reveal" data-delay="180">
        <h3 class="h-sm">Paid properly, kept long</h3>
        <p>We pay above the going rate for this industry because turnover is what
        destroys quality. The crew that starts with you tends to stay with you.</p>
      </div>
    </div>
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head section-head--center">
      <span class="eyebrow eyebrow--center">Reviews</span>
      <h2 class="h-lg">In their words.</h2>
    </div>
    <div class="grid grid--3">{testimonial_cards(3, 3)}</div>
  </div>
</section>

{cta_band()}
"""
    page(
        "about.html",
        f"About {B['legal_name']} | Edmonton Cleaning Company",
        f"{B['legal_name']} is a locally owned Edmonton cleaning company. Screened "
        "and bonded crews, written checklists, and a 24-hour satisfaction "
        "guarantee on every clean.",
        body,
        schemas=[
            local_business_schema(),
            breadcrumbs([("Home", "index.html"), ("About", None)]),
        ],
    )


def build_areas():
    cards = ""
    blurbs = {
        "Edmonton": "Our home base. Full coverage from Castle Downs to Summerside, "
                    "including downtown condos and the river valley communities.",
        "St. Albert": "Weekly and bi-weekly residential routes, plus commercial "
                      "contracts along St. Albert Trail.",
        "Sherwood Park": "Residential cleaning across Strathcona County, with "
                         "after-hours commercial work in the business park.",
        "Spruce Grove": "Homes, acreages and small commercial sites — no travel "
                        "surcharge inside the town limits.",
        "Leduc": "Residential and commercial, including short-turnaround move-out "
                 "cleans near the airport.",
        "Beaumont": "Family homes and new builds. Popular for post-construction "
                    "and first-occupancy cleans.",
        "Stony Plain": "Regular residential routes on Tuesdays and Fridays.",
        "Fort Saskatchewan": "Residential plus industrial office and lunchroom "
                             "contracts.",
        "Devon": "Residential cleaning and carpet extraction, scheduled around "
                 "our Leduc route.",
        "Nisku": "Commercial and industrial offices, shops and lunchrooms.",
        "Morinville": "Residential cleaning on a bi-weekly and monthly rotation.",
        "Ardrossan": "Acreages and family homes east of Sherwood Park.",
    }
    for i, a in enumerate(B["areas"]):
        cards += f"""
<article class="card reveal" data-delay="{i * 40}">
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
        "We cover Edmonton and eleven surrounding communities. If you're just outside "
        "the list, call and ask — we'll tell you honestly whether we can serve you well.",
        [("Home", "index.html"), ("Areas Served", None)],
    ) + f"""
<section class="section">
  <div class="shell shell--wide">
    <div class="grid grid--3">{cards}</div>
  </div>
</section>

<section class="section bg-paper">
  <div class="shell">
    <div class="section-head">
      <span class="eyebrow">Edmonton neighbourhoods</span>
      <h2 class="h-lg">Where we work most.</h2>
      <p class="lede">These come up most often on our routes — but we serve the whole
      city, not just these.</p>
    </div>
    <div class="area-cloud reveal">{hoods}</div>
  </div>
</section>

<section class="section band">
  <div class="shell">
    <div class="split">
      <div>
        <span class="eyebrow eyebrow--light">Travel &amp; scheduling</span>
        <h2 class="h-lg">No hidden <span class="tilt--gold">travel fees</span>.</h2>
        <p class="lede mt-2">Every community on this page is inside our standard service
        area. The price you're quoted covers getting there.</p>
        <ul class="check-list" style="--ink-soft:rgba(246,242,234,.78)">
          <li>{icon('check', 18)}<span style="color:rgba(246,242,234,.82)"><b style="color:#fffdf8">Same-week availability</b> for most residential bookings.</span></li>
          <li>{icon('check', 18)}<span style="color:rgba(246,242,234,.82)"><b style="color:#fffdf8">Fixed weekday routes</b> per community, so recurring clients get a consistent slot.</span></li>
          <li>{icon('check', 18)}<span style="color:rgba(246,242,234,.82)"><b style="color:#fffdf8">Emergency and same-day</b> cleans subject to crew availability — call and ask.</span></li>
        </ul>
        <a class="btn btn--gold mt-3" href="book.html">{icon('calendar', 16)} Check availability</a>
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
        "Fast and Perfect cleans homes and businesses across Edmonton, St. Albert, "
        "Sherwood Park, Spruce Grove, Leduc, Beaumont and nine more communities. "
        "No travel surcharges.",
        body,
        schemas=[breadcrumbs([("Home", "index.html"), ("Areas Served", None)])],
        keywords="cleaning services St Albert, cleaners Sherwood Park, house "
                 "cleaning Spruce Grove, cleaning company Leduc, Beaumont cleaners",
    )


def build_quote():
    body = page_head(
        "Free quote",
        'Get your price<br>in <span class="tilt">one hour</span>.',
        "Price it yourself with the estimator, then send it over. We reply within one "
        "business hour with a firm written quote — no walkthrough needed for most homes.",
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
              <span class="v">Within 1 business hour<span>Mon–Sat</span></span></span></li>
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
              <p>In writing, itemised, with the checklist attached. Valid 30 days.</p>
            </div>
            <div class="step" style="padding-top:2.4rem">
              <h3 class="h-sm">You decide</h3>
              <p>No follow-up pestering. One reply, and we leave it with you.</p>
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
        "Get an instant cleaning estimate for your Edmonton home or business, then a "
        "firm written quote within one business hour. No walkthrough needed for most homes.",
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
    freqs = [("onetime", "One-time", ""), ("monthly", "Monthly", '<span class="tag">-10%</span>'),
             ("biweekly", "Every 2 weeks", '<span class="tag">-15%</span>'),
             ("weekly", "Weekly", '<span class="tag">-20%</span>')]
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
        f'<label for="bex-{v}">{l} <span class="tag">+${p}</span></label>'
        for v, l, p in extras
    )

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
      <form class="est-panel" id="booking-form" data-form novalidate>
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
          <ul class="summary-list" id="booking-summary"></ul>
          <div class="summary-total">
            <span class="k">Estimated</span>
            <span class="v" id="booking-total">$0</span>
          </div>
          <p class="field-hint mt-2">Estimate only — confirmed in writing before we start.
          Recurring discounts are already included above.</p>
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
        "your date and arrival window — we confirm within one business hour. Free "
        "cancellation up to 24 hours before.",
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
        f"{PHONE}, email us, or send the form — we reply within one business hour.",
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
        "Allow: /\n\n"
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
