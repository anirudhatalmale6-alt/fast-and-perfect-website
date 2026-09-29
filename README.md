# Fast and Perfect Ltd. — Website

Marketing site for a cleaning company in Edmonton, Alberta.
Plain static HTML, CSS and JavaScript. No framework, no build step required to
host it, no database. Any web host that serves files will run it.

**Live preview:** https://anirudhatalmale6-alt.github.io/fast-and-perfect-website/

---

## ⚠️ Placeholders to replace before launch

These are stand-in values. Everything else is production-ready.

| What | Current value | Where to change it |
|---|---|---|
| Phone number | `(780) 555-0142` | `tools/build.py` → `BUSINESS` |
| Email | `hello@fastandperfect.ca` | `tools/build.py` → `BUSINESS` |
| Domain | `https://fastandperfect.ca` | `tools/build.py` → `BUSINESS` |
| Social links | `#` | `tools/build.py` → `BUSINESS["social"]` |
| Hours | Mon–Fri 8–7, Sat 9–5 | `tools/build.py` → `BUSINESS["hours"]` |
| Service areas | Edmonton + 19 secondary | `tools/build.py` → `BUSINESS["primary_area"]` / `secondary_areas` |
| Photos | Generated illustrations | `site/assets/img/` |
| Reviews | **Removed** — none published | `tools/build.py` → `TESTIMONIALS` |
| Residential / commercial prices | **Removed** — not confirmed | `tools/build.py` → `CLAIMS["show_prices"]` |
| Carpet & upholstery prices | **Live** — owner-confirmed | `site/assets/data/pricing.json` |
| Insurance / bonding / guarantees | **Removed** — none published | `tools/build.py` → `CLAIMS` |
| Form delivery | Demo mode | `site/assets/js/main.js` → `CONFIG.FORM_ENDPOINT` |

### The claims gate

`tools/build.py` has a `CLAIMS` dict. Everything in it is currently `False`
or `None`, and while a value is off, the site publishes nothing about it —
no star ratings, no review quotes, no insurance or bonding statements, no
guarantees, no staff-screening claims, and no prices (including the prices
that would otherwise appear in the Google structured data).

```python
CLAIMS = {
    "insured": False,
    "bonded": False,
    "wcb_covered": False,
    "police_checks": False,
    "guarantee_hours": None,
    "rating": None,
    "review_count": None,
    "eco_products": False,
    "same_crew": False,
    "supplies_included": False,
    "years_in_business": None,
    "show_prices": False,         # residential + commercial (NOT confirmed)
    "show_prices_carpet": True,   # confirmed in writing
}
```

Set a value to the real, confirmed figure and rebuild to switch that claim
back on. **Do not enable anything the owner has not confirmed in writing.**
Invented reviews and unverifiable business claims breach Google and Meta
advertising policy and are grounds for a listing suspension.

---

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — hero, services, quote form, before/after, FAQ |
| `residential-cleaning.html` | Residential service + room-by-room checklist |
| `commercial-cleaning.html` | Commercial service + sectors + onboarding |
| `carpet-cleaning.html` | Carpet & upholstery + method + estimate calculator + rate table |
| `admin-pricing.html` | **Private** price editor (noindex, robots-disallowed) |
| `quote.html` | Quote builder + free quote form |
| `book.html` | Online booking — service, date, arrival window, live summary |
| `gallery.html` | Before/after sliders + job grid |
| `service-areas.html` | Edmonton (primary) + 19 secondary communities (local SEO) |
| `about.html` | Who we are, how we work, what to expect |
| `contact.html` | Contact form, phone, hours |
| `privacy.html` | PIPEDA / Alberta PIPA privacy policy |
| `404.html` | Not-found page |

Plus `sitemap.xml` and `robots.txt`.

---

## Features

- **Quote builder** — service, bedrooms, bathrooms, square footage, frequency
  and add-ons, summarised live and carried into the quote form. The pricing
  engine is written and tested but stays switched off until `CLAIMS`
  `show_prices` is enabled with the owner's confirmed rates.
- **Online booking** with date, arrival window and a live-updating summary card.
- **Before/after sliders** — drag, touch or arrow-key driven.
- **Click-to-call** everywhere, plus a sticky call bar on mobile.
- **Spam protection** — honeypot field on every form.
- **SEO** — per-page titles, meta descriptions, canonicals, Open Graph,
  `HouseCleaningService` / `Service` / `FAQPage` / `BreadcrumbList` structured
  data, geo meta tags, sitemap and robots.
- **Accessibility** — skip link, keyboard-operable sliders and menus, visible
  focus rings, `aria-live` form status, `prefers-reduced-motion` support.
- **Performance** — self-hosted fonts (no third-party requests), SVG artwork,
  lazy-loaded images, ~40 KB CSS + ~12 KB JS, zero dependencies.

---

## Editing the site

### Option A — edit the HTML directly
The files in `site/` are plain HTML. Open one, change the text, save, upload.
Nothing else required.

### Option B — rebuild from the generator (recommended for global changes)
Changing the phone number in one place and having all 12 pages update
(the same applies to service areas, hours and every gated claim):

```bash
python3 tools/build.py            # regenerates every page in site/
python3 tools/make_placeholders.py # regenerates the SVG artwork
```

Requires Python 3 only — no packages to install.

---

## Changing carpet & upholstery prices

Every carpet, upholstery, mattress and treatment price lives in **one file**:
`site/assets/data/pricing.json`. The estimate calculator *and* the published
rate table both read from it, so they can never disagree.

Two ways to change a price:

1. **The price editor** (no code): open `/admin-pricing.html`, change the
   numbers, watch the live preview, click **Download pricing.json**, then
   upload that file over `site/assets/data/pricing.json`. No rebuild needed.
2. **Edit the JSON directly** and re-upload it.

The pricing rules encoded there:

- A minimum service charge applies to **every** appointment.
- Carpeted rooms are **tiered** (1–5 rooms priced individually), then a flat
  rate per additional room.
- Stairs are a base price covering the first N steps, then per step after.
- Treatments are quoted as a **range**, which makes the whole estimate a range.
- A "room" has a maximum square footage; larger rooms, basements and open-plan
  areas are quoted separately.

Run `node tools/test_pricing.js` after changing prices — it re-checks the
calculator against every published price and the worked examples.

---

## Connecting the forms

The quote, contact and booking forms currently run in **demo mode**: they
validate and show the success message, but nothing is delivered.

To make them live, sign up with a form provider (Web3Forms and Formspree both
have free tiers), then put the endpoint URL here:

```js
// site/assets/js/main.js
var CONFIG = {
  FORM_ENDPOINT: 'https://api.web3forms.com/submit',  // <- paste yours
  CURRENCY: 'CAD'
};
```

Submissions then arrive by email. No server-side code needed.

---

## Swapping in real photos

Every image in `site/assets/img/` is a generated illustration standing in for a
real photo. To replace one:

1. Save the photo as a `.jpg` (1200×900 or larger, under ~300 KB).
2. Drop it in `site/assets/img/`.
3. Update the `src` in the HTML, or in `tools/build.py` and rebuild.

For the before/after sliders, shoot both frames **from the same spot** — same
angle, same height, same lighting. That is what makes the slider convincing.

---

## Hosting

Static files — it will run on anything. In rough order of cost:

- **Netlify / Cloudflare Pages / GitHub Pages** — free tier, HTTPS included.
- **Any shared cPanel host** — upload the contents of `site/` to `public_html`.

Upload the **contents** of `site/`, not the folder itself, so that `index.html`
sits at the web root.

---

## Repository layout

```
site/                    ← the website (this is what gets uploaded)
  *.html
  sitemap.xml, robots.txt
  assets/css/main.css
  assets/js/main.js
  assets/fonts/          ← Fraunces + Karla, self-hosted (SIL Open Font License)
  assets/img/            ← SVG artwork
tools/
  build.py               ← generates the HTML pages
  make_placeholders.py   ← generates the SVG artwork
```

---

## Credits

Typefaces: [Fraunces](https://fonts.google.com/specimen/Fraunces) and
[Karla](https://fonts.google.com/specimen/Karla), both under the SIL Open Font
License, self-hosted so the site makes no third-party requests.
