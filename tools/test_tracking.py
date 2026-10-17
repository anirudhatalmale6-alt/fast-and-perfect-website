"""Consent, analytics and conversion tracking: browser tests.

    python3 tools/test_tracking.py

Builds a throwaway copy of the site with dummy GA4 and Pixel IDs, serves it
with a stub /api/enquiry whose success/failure can be switched, intercepts
every request to Google and Meta, and checks:

  - nothing loads, and no request or cookie is made, before Accept
  - Decline is remembered and sends nothing, even after a successful send
  - the forms' own "I agree" checkbox is untouched by the banner styles
  - Accept loads both tags with the right IDs and consent mode
  - each form reports its own conversion ONLY on confirmed delivery
  - no name, phone, email or address ever reaches Google or Meta
  - phone and text taps, including the mobile sticky bar
  - the banner sits above the call bar on a phone
  - Cookie settings reopens it; Decline after Accept revokes and deletes cookies
  - blocked storage (private browsing) does not crash it

The real site is not touched: the dummy IDs exist only in the temp copy.
Requires Playwright with Chromium.
"""
import os, re, shutil, socketserver, tempfile, threading, http.server, json as _json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TMP = tempfile.mkdtemp(prefix="fp-tracking-")
for d in ("tools", "site", "functions"):
    shutil.copytree(os.path.join(ROOT, d), os.path.join(TMP, d))
_bp = os.path.join(TMP, "tools", "build.py")
_s = open(_bp, encoding="utf-8").read()
_s = re.sub(r'"ga4": "[^"]*"', '"ga4": "G-TEST123456"', _s, count=1)
_s = re.sub(r'"meta_pixel": "[^"]*"', '"meta_pixel": "123456789012345"', _s, count=1)
open(_bp, "w", encoding="utf-8").write(_s)
assert os.system(f'python3 "{_bp}" > /dev/null') == 0, "test build failed"

SITE_DIR = os.path.join(TMP, "site")
MODE = {"v": "ok"}

class _H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=SITE_DIR, **k)
    def log_message(s, *a): pass
    def do_GET(s):
        if s.path.startswith("/__mode/"):
            MODE["v"] = s.path.rsplit("/", 1)[1]
            s.send_response(200); s.end_headers(); s.wfile.write(b"ok"); return
        return super().do_GET()
    def do_POST(s):
        s.rfile.read(int(s.headers.get("content-length", 0)))
        ok = MODE["v"] == "ok"
        b = _json.dumps({"ok": ok, "message": None if ok else "fail"}).encode()
        s.send_response(200 if ok else 502)
        s.send_header("content-type", "application/json")
        s.send_header("content-length", str(len(b))); s.end_headers(); s.wfile.write(b)

socketserver.TCPServer.allow_reuse_address = True
_srv = socketserver.TCPServer(("127.0.0.1", 0), _H)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
PORT = _srv.server_address[1]

import json, urllib.request, datetime, re
from playwright.sync_api import sync_playwright
B=f"http://127.0.0.1:{PORT}/"
TRK=re.compile(r"googletagmanager\.com|google-analytics\.com|connect\.facebook\.net|facebook\.com/tr")
def mode(m): urllib.request.urlopen(B+"__mode/"+m).read()
PII=["Zelda Quokka","zelda.quokka@example.com","7805550199","123 Secret Lane"]
res=[]; 
def check(name, cond, detail=""):
    res.append(cond); print(("  PASS " if cond else "  FAIL ")+name+(f"  [{detail}]" if detail else ""))

def ga(pg):  return pg.evaluate("() => (window.dataLayer||[]).map(a => Array.from(a).map(x => x instanceof Date ? 'DATE' : x))")
def fb(pg):  return pg.evaluate("() => (window.fbq && window.fbq.queue) ? window.fbq.queue.map(a => Array.from(a)) : null")
def ga_events(pg): return [e for e in ga(pg) if len(e)>=2 and e[0]=="event"]
def fb_tracks(pg): return [e for e in (fb(pg) or []) if len(e)>=2 and e[0]=="track"]

def fill(pg, form_sel):
    pg.evaluate("""([sel, pii]) => {
      const f=document.querySelector(sel);
      f.querySelectorAll('input,select,textarea').forEach(el=>{
        if(el.disabled||el.type==='hidden'||/^_/.test(el.name||'')) return;
        if(el.type==='checkbox'){ if(el.required) el.checked=true; return; }
        if(el.type==='radio'){ if(el.required && !f.querySelector('input[name="'+el.name+'"]:checked')) el.checked=true; return; }
        if(el.tagName==='SELECT'){ if(el.required && el.options.length>1) el.selectedIndex=1; return; }
        if(el.type==='email') el.value=pii[1];
        else if(el.type==='tel') el.value=pii[2];
        else if(el.type==='date'){ const d=new Date(Date.now()+7*864e5); el.value=d.toISOString().slice(0,10); }
        else if(el.type==='number') el.value='1200';
        else if(/address/i.test(el.name)) el.value=pii[3];
        else if(/name/i.test(el.name)) el.value=pii[0];
        else if(el.tagName==='TEXTAREA') el.value='Please call '+pii[0]+' at '+pii[2];
        else el.value='Edmonton';
      });
    }""", [form_sel, PII])

with sync_playwright() as p:
    br=p.chromium.launch(args=["--no-proxy-server"])
    def ctx_page():
        ctx=br.new_context(viewport={"width":1280,"height":900})
        hits=[]
        # Record EVERY request to a tracking host, routed or not. The first
        # run used "**/googletagmanager.com/**", which never matches
        # www.googletagmanager.com, so gtag slipped through unrecorded and
        # "zero requests" passed falsely.
        ctx.on("request", lambda r: hits.append(r.url) if TRK.search(r.url) else None)
        ctx.route(TRK, lambda route: route.fulfill(status=200, content_type="application/javascript", body="/* stub */"))
        pg=ctx.new_page(); errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        return ctx, pg, hits, errs

    print("1. BEFORE ANY CHOICE")
    ctx,pg,hits,errs=ctx_page(); pg.goto(B+"index.html", wait_until="networkidle"); pg.wait_for_timeout(600)
    check("banner shown on first visit", pg.is_visible("#consent-banner"))
    check("zero requests to Google or Meta", hits==[], hits)
    check("gtag not defined, fbq not defined", pg.evaluate("typeof window.gtag==='undefined' && typeof window.fbq==='undefined'"))
    check("no tracking cookies", "_ga" not in pg.evaluate("document.cookie") and "_fbp" not in pg.evaluate("document.cookie"))
    pg.click("a[href^='tel:']", force=True); pg.wait_for_timeout(200)
    check("phone tap before consent sends nothing", hits==[] and ga(pg)==[] , hits)
    ctx.close()

    print("2. DECLINE")
    ctx,pg,hits,errs=ctx_page(); pg.goto(B+"index.html", wait_until="networkidle")
    pg.click("[data-consent='decline']"); pg.wait_for_timeout(500)
    check("banner closes", not pg.is_visible("#consent-banner"))
    check("still zero requests", hits==[], hits)
    pg.goto(B+"contact.html", wait_until="networkidle"); pg.wait_for_timeout(500)
    check("choice remembered: no banner on next page", not pg.is_visible("#consent-banner"))
    mode("ok"); fill(pg,"#contact-form"); pg.click("#contact-form button[type=submit]"); pg.wait_for_timeout(1500)
    check("successful send after decline: still nothing sent", hits==[] and ga(pg)==[], hits)
    ctx.close()

    print("2b. THE FORMS' OWN CONSENT CHECKBOX IS UNTOUCHED")
    ctx,pg,hits,errs=ctx_page(); pg.goto(B+"contact.html", wait_until="networkidle"); pg.wait_for_timeout(400)
    pos=pg.evaluate("getComputedStyle(document.querySelector('#contact-form label.consent')).position")
    check("form 'I agree' label is not position:fixed", pos=="static", pos)
    bpos=pg.evaluate("getComputedStyle(document.getElementById('consent-banner')).position")
    check("cookie banner IS position:fixed", bpos=="fixed", bpos)
    ctx.close()

    print("3. ACCEPT")
    ctx,pg,hits,errs=ctx_page(); pg.goto(B+"index.html", wait_until="networkidle")
    pg.click("[data-consent='accept']"); pg.wait_for_timeout(800)
    check("gtag.js requested with the GA4 ID", any("gtag/js?id=G-TEST123456" in h for h in hits), hits)
    check("fbevents.js requested", any("fbevents.js" in h for h in hits))
    g=ga(pg)
    check("GA4 configured with the ID", ["config","G-TEST123456"] in g)
    check("consent mode update = granted", any(len(e)>=3 and e[0]=="consent" and e[1]=="update" and e[2].get("analytics_storage")=="granted" for e in g))
    q=fb(pg)
    check("Pixel init with the ID + PageView", ["init","123456789012345"] in q and ["track","PageView"] in q, q)
    ctx.close()

    def accepted(page_url):
        ctx,pg,hits,errs=ctx_page(); pg.goto(B+"index.html", wait_until="networkidle")
        pg.click("[data-consent='accept']"); pg.wait_for_timeout(400)
        pg.goto(B+page_url, wait_until="networkidle"); pg.wait_for_timeout(700)
        return ctx,pg,hits,errs

    print("4. CONVERSIONS: one per form, only on confirmed delivery")
    for page_url, fid, ga_name, meta_name in [("quote.html","#quote-form","quote_request","Lead"),
                                               ("contact.html","#contact-form","contact_request","Lead"),
                                               ("book.html","#booking-form","booking_request","Schedule")]:
        ctx,pg,hits,errs=accepted(page_url)
        check(f"{page_url}: consent carried across pages", not pg.is_visible("#consent-banner") and pg.evaluate("typeof window.gtag==='function'"))
        mode("fail"); fill(pg,fid); pg.click(fid+" button[type=submit]"); pg.wait_for_timeout(1500)
        check(f"{page_url}: FAILED send -> no conversion", not any(e[1]==ga_name for e in ga_events(pg)) and not any(e[1]==meta_name and e[1]!="PageView" for e in fb_tracks(pg)),
              [e[1] for e in ga_events(pg)])
        mode("ok"); fill(pg,fid); pg.click(fid+" button[type=submit]"); pg.wait_for_timeout(1500)
        evs=[e for e in ga_events(pg) if e[1]==ga_name]
        check(f"{page_url}: confirmed send -> GA4 '{ga_name}' once", len(evs)==1, evs)
        check(f"{page_url}: confirmed send -> Meta '{meta_name}'", any(e[1]==meta_name for e in fb_tracks(pg)), fb_tracks(pg))
        if evs: check(f"{page_url}: form_id param = {fid[1:]}", evs[0][2].get("form_id")==fid[1:], evs[0][2])
        blob=json.dumps(ga(pg))+json.dumps(fb(pg))
        check(f"{page_url}: NO personal data in anything sent", not any(x in blob for x in PII), [x for x in PII if x in blob])
        check(f"{page_url}: no JS errors", errs==[], errs)
        ctx.close()

    print("5. PHONE AND TEXT TAPS")
    ctx,pg,hits,errs=accepted("contact.html")
    pg.evaluate("document.addEventListener('click', e => { if (e.target.closest('a[href^=\"tel:\"],a[href^=\"sms:\"]')) e.preventDefault(); }, true)")
    pg.click("main a[href^='tel:']"); pg.wait_for_timeout(200)
    pg.click("main a[href^='sms:']"); pg.wait_for_timeout(200)
    pg.click(".site-footer a[href^='tel:']"); pg.wait_for_timeout(200)
    ev=ga_events(pg)
    pc=[e for e in ev if e[1]=="phone_click"]; tc=[e for e in ev if e[1]=="text_click"]
    check("phone tap -> phone_click", len(pc)==2, pc)
    check("text tap -> text_click", len(tc)==1, tc)
    check("location recorded (page + footer)", sorted(e[2].get("link_location") for e in pc)==["footer","page"], [e[2] for e in pc])
    check("Meta 'Contact' for taps", sum(1 for e in fb_tracks(pg) if e[1]=="Contact")==3, fb_tracks(pg))
    ctx.close()

    print("6. MOBILE: sticky bar tap, banner clear of the bar")
    ctx=br.new_context(viewport={"width":390,"height":800}, is_mobile=True, has_touch=True)
    hits=[]; ctx.on("request", lambda r: hits.append(r.url) if TRK.search(r.url) else None)
    ctx.route(TRK, lambda r: r.fulfill(status=200, body=""))
    pg=ctx.new_page(); pg.goto(B+"index.html", wait_until="networkidle"); pg.wait_for_timeout(500)
    bb=pg.query_selector("#consent-banner").bounding_box(); cb=pg.query_selector(".callbar").bounding_box()
    check("banner sits above the call bar, not over it", bb["y"]+bb["height"] <= cb["y"], f"banner bottom {bb['y']+bb['height']:.0f}, bar top {cb['y']:.0f}")
    check("banner within the screen width", bb["x"]>=0 and bb["x"]+bb["width"]<=390, bb)
    pg.click("[data-consent='accept']"); pg.wait_for_timeout(400)
    pg.evaluate("document.addEventListener('click', e => { if (e.target.closest('a[href^=\"tel:\"]')) e.preventDefault(); }, true)")
    pg.click(".callbar a[href^='tel:']"); pg.wait_for_timeout(200)
    ev=[e for e in ga_events(pg) if e[1]=="phone_click"]
    check("sticky bar Call -> phone_click, location mobile_bar", len(ev)==1 and ev[0][2].get("link_location")=="mobile_bar", ev)
    ctx.close()

    print("7. CHANGING YOUR MIND")
    ctx,pg,hits,errs=accepted("index.html")
    pg.evaluate("document.cookie='_ga=GA1.1.123; path=/'; document.cookie='_fbp=fb.1.1; path=/'")
    pg.click("[data-cookie-settings]"); pg.wait_for_timeout(300)
    check("Cookie settings reopens the banner", pg.is_visible("#consent-banner"))
    pg.click("[data-consent='decline']"); pg.wait_for_timeout(400)
    g=ga(pg)
    check("GA4 told consent is now denied", any(len(e)>=3 and e[0]=="consent" and e[1]=="update" and e[2].get("analytics_storage")=="denied" for e in g))
    check("Meta told consent revoked", ["consent","revoke"] in (fb(pg) or []))
    ck=pg.evaluate("document.cookie")
    check("tracking cookies deleted", "_ga=" not in ck and "_fbp=" not in ck, ck)
    n_before=len(ga_events(pg))
    pg.evaluate("document.addEventListener('click', e => { if (e.target.closest('a[href^=\"tel:\"]')) e.preventDefault(); }, true)")
    pg.click("main a[href^='tel:']", force=True); pg.wait_for_timeout(200)
    check("taps after withdrawing send nothing", len(ga_events(pg))==n_before)
    ctx.close()

    print("8. STORAGE BLOCKED (private browsing)")
    ctx=br.new_context(viewport={"width":1280,"height":900})
    ctx.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    pg=ctx.new_page(); errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(B+"index.html", wait_until="networkidle"); pg.wait_for_timeout(500)
    check("banner still shows, no crash", pg.is_visible("#consent-banner") and errs==[], errs)
    ctx.close(); br.close()

print(f"\n{sum(res)} passed, {len(res)-sum(res)} failed")
_srv.shutdown()
shutil.rmtree(TMP, ignore_errors=True)
raise SystemExit(0 if all(res) else 1)
