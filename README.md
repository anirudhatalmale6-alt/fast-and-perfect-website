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
| Service areas | 12 communities | `tools/build.py` → `BUSINESS["areas"]` |
| Photos | Generated illustrations | `site/assets/img/` |
| Reviews | Written examples | `tools/build.py` → `TESTIMONIALS` |
| Prices | Edmonton market estimates | `tools/build.py` + `site/assets/js/main.js` → `RATES` |
| Form delivery | Demo mode | `site/assets/js/main.js` → `CONFIG.FORM_ENDPOINT` |

The review quotes are illustrative examples written to show the layout — they
must be replaced with real customer reviews before the site goes live.

---

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — hero, services, instant estimator, before/after, reviews, FAQ |
| `residential-cleaning.html` | Residential service + room-by-room checklist + price table |
| `commercial-cleaning.html` | Commercial service + sectors + onboarding |
| `carpet-cleaning.html` | Carpet & upholstery + method + published rates |
| `quote.html` | Instant estimator + free quote form |
| `book.html` | Online booking — service, date, arrival window, live summary |
| `gallery.html` | Before/after sliders + job grid |
| `service-areas.html` | 12 communities + Edmonton neighbourhoods (local SEO) |
| `about.html` | Company story, promises, hiring standards |
| `contact.html` | Contact form, phone, hours |
| `privacy.html` | PIPEDA / Alberta PIPA privacy policy |
| `404.html` | Not-found page |

Plus `sitemap.xml` and `robots.txt`.

---

## Features

- **Instant quote estimator** — service, bedrooms, bathrooms, square footage,
  frequency and add-ons produce a live price range with a visible breakdown.
  Recurring discounts (10/15/20%) are applied automatically.
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
Changing the phone number in one place and having all 12 pages update:

```bash
python3 tools/build.py            # regenerates every page in site/
python3 tools/make_placeholders.py # regenerates the SVG artwork
```

Requires Python 3 only — no packages to install.

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
