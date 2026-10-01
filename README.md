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
| Phone number | **(587) 338-0069** — confirmed | `tools/build.py` → `BUSINESS` |
| Email | **info@fastandperfect.ca** — confirmed | `tools/build.py` → `BUSINESS` |
| Domain | `https://fastandperfect.ca` | `tools/build.py` → `BUSINESS` |
| Social links | `#` | `tools/build.py` → `BUSINESS["social"]` |
| Hours | **Mon–Fri 8–8, Sat 9–6, Sun 10–4** — confirmed | `tools/build.py` → `BUSINESS["hours"]` |
| Service areas | Edmonton + 19 secondary | `tools/build.py` → `BUSINESS["primary_area"]` / `secondary_areas` |
| Photos | Generated illustrations | `site/assets/img/` |
| Reviews | **Removed** — none published | `tools/build.py` → `TESTIMONIALS` |
| All pricing | **Live** — owner-confirmed | `site/assets/data/pricing.json` |
| Insurance / bonding / guarantees | **Removed** — none published | `tools/build.py` → `CLAIMS` |
| Form delivery | Own endpoint `/api/enquiry` | `functions/api/enquiry.js` |

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
| `quote.html` | Smart calculator + free quote form |
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

- **One smart quote calculator** for every service. The customer ticks the
  services they need (several at once is fine) and only the relevant
  questions appear:
  - *Regular / deep / move-in-out* → bedrooms, bathrooms, sq ft, frequency, add-ons
  - *Commercial* → property type, sq ft, frequency, washrooms, access notes
  - *Carpet* → carpeted rooms, hallways, stairs by step
  - *Upholstery* → chairs, recliners, loveseats, sofas, sectionals, ottomans, mattresses
  - *Treatments* (heavy stain, pet odour) shown once when carpet or upholstery is picked

  Carpet and upholstery produce a live estimate from `pricing.json`. Services
  without confirmed prices are listed as "quoted separately" rather than
  guessed at. Selections survive navigation to the quote form via
  sessionStorage, and fields in hidden panels are disabled so they can never
  leak into a submission.
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

## Changing prices

**Every price on the site lives in one file**: `site/assets/data/pricing.json` —
residential packages and add-ons, recurring discounts, commercial bands, carpet,
upholstery, mattresses and treatments. The calculator, all three published rate
tables and the booking page read from it, so they cannot disagree.

Two ways to change a price:

1. **The price editor** (no code): open `/admin-pricing.html`, change the
   numbers, watch the live preview, click **Download pricing.json**, then
   upload that file over `site/assets/data/pricing.json`. No rebuild needed.
2. **Edit the JSON directly** and re-upload it.

The pricing rules encoded there:

**Residential** — tiered by bedroom count, each tier with a bathroom cap.
Exceed the cap (or the largest tier) and the customer sees **Custom Quote**
rather than a guess. Add-ons already covered by a deep or move-out clean are
shown as *included* and never charged twice. The recurring discount applies to
the base package only, from the second visit — never to add-ons, and never to
the first clean.

**Commercial** — banded by square footage, for standard offices and retail
only. Specialised premises (clinics, restaurants, warehouses, gyms, common
areas) and anything over the top band are **Custom Quote**. Recurring schedules
are captured in the enquiry but never auto-discounted.

**Carpet & upholstery** — a minimum service charge on every appointment;
carpeted rooms tiered 1–5 then per extra room; stairs a base covering the first
N steps then per step; treatments quoted as a **range**, which makes the whole
estimate a range; a maximum room size, above which rooms, large basements and
open-plan areas are quoted separately.

Run both checks after any change:

```bash
node tools/test_pricing.js        # 148 assertions on the pricing rules
python3 tools/check_consistency.py # site-wide copy + contact-detail consistency
```

`check_consistency.py` fails the build if any page contradicts the confirmed
package structure — an always-paid add-on (fridge, oven, interior windows)
described as included, deep-clean-only work (baseboards, door frames, light
switches) promised on every visit, a stale phone number or email, a disabled
claim reappearing, a price that is not in `pricing.json`, or a missing
commercial band.

---

## How the forms deliver

The quote, contact and booking forms post to **`/api/enquiry`** — the site's
own endpoint, running as a Cloudflare Pages Function on this same domain
(`functions/api/enquiry.js`).

### Why not post straight to a form service

That was the original design, and it failed twice, both times invisibly:

1. **Posting by `fetch()` is an XHR, so CORS applies.** The service answered
   from behind bot protection without an `Access-Control-Allow-Origin`
   header, so the browser refused to read the reply and every send died.
   Reproduced on the live domain.
2. **Posting natively fixed CORS**, but the service then began returning
   HTTP 500 from its own servers — which navigated the customer off
   fastandperfect.ca and onto a stranger's error page. Confirmed on both the
   custom domain and the `pages.dev` URL, so it was not a DNS or domain issue.

Posting to our own origin removes both. There is no CORS on a same-origin
request, so the page can read the reply and say truthfully whether the
enquiry was delivered; and the visitor never leaves the site.

### The rules it enforces

- **A success message only ever follows a confirmed delivery.** A provider
  answering `200` with `success: false` — which is exactly what happens while
  an address is unactivated — counts as a failure, not a send.
- **A failure says so**, and points at the always-visible *"email this to us
  instead"* link (which carries everything the customer typed) and the phone
  number. Their typing is never cleared on failure.
- **It works with JavaScript off.** The form has a real `method`/`action`;
  the endpoint redirects to `thank-you.html` on success, or back to
  `contact.html?send=failed` on failure, which the page then reports.
- **Honeypots are checked server-side too**, and answer normally so bots
  learn nothing.

### Choosing a mail provider

Set **one** of these in the Cloudflare dashboard → *Workers & Pages →
fast-and-perfect-website → Settings → Environment variables* (add it to both
Production and Preview):

| Variable | Provider | Notes |
|---|---|---|
| `WEB3FORMS_KEY` | Web3Forms | free key, no card, no subscription |
| `BREVO_API_KEY` | Brevo | free tier, 300 emails/day |
| `RESEND_API_KEY` | Resend | free tier, needs domain verification |

`TO_EMAIL` overrides the destination (default `info@fastandperfect.ca`).

With none set it falls back to FormSubmit, which needs no account but is the
service that was failing — hence a fallback rather than the default.

Adding a provider is one function in `enquiry.js` plus one line in
`pickSender()`. Run the tests after any change:

```bash
node tools/test_enquiry.mjs    # 30 assertions on delivery, honeypots, no-JS
```

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
  assets/js/pricing-engine.js     ← pure pricing maths (unit-tested)
  assets/js/quote-calculator.js   ← the smart calculator UI
  assets/js/admin-pricing.js      ← the price editor
  assets/js/main.js
  assets/data/pricing.json        ← every carpet/upholstery price
  assets/fonts/          ← Fraunces + Karla, self-hosted (SIL Open Font License)
  assets/img/            ← SVG artwork
functions/
  api/enquiry.js         ← the form endpoint (Cloudflare Pages Function)
tools/
  build.py               ← generates the HTML pages
  make_placeholders.py   ← generates the SVG artwork
  test_pricing.js        ← pricing rule assertions
  test_enquiry.mjs       ← form-delivery assertions
  check_consistency.py   ← site-wide copy + contact-detail consistency
```

---

## Credits

Typefaces: [Fraunces](https://fonts.google.com/specimen/Fraunces) and
[Karla](https://fonts.google.com/specimen/Karla), both under the SIL Open Font
License, self-hosted so the site makes no third-party requests.
