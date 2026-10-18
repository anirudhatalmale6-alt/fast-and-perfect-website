/* ==========================================================================
   Fast and Perfect Ltd. — analytics and ad measurement, behind consent

   Google Analytics 4 and the Meta Pixel. Neither loads, sets a cookie or
   sends a single request until the visitor clicks Accept. That is opt-in
   consent: it satisfies Quebec's Law 25 and the GDPR as well as Alberta PIPA
   and PIPEDA, so the site does not need to know where a visitor is from.

   The IDs come from a JSON block the build writes into each page
   (#fp-tracking-config). With no IDs configured that block is absent and
   this file is not even included, so nothing changes until the owner
   supplies them.

   Conversions are sent through window.fpTrack(), which main.js calls only
   once the form endpoint has CONFIRMED the enquiry was delivered. A send
   that failed must never be counted as a lead.

   No personal information is ever passed to Google or Meta: no names,
   phone numbers, emails or addresses. Google's terms forbid it, and it would
   break the promise in the privacy policy.
   ========================================================================== */
(function () {
  'use strict';

  var cfgEl = document.getElementById('fp-tracking-config');
  if (!cfgEl) return;
  var cfg;
  try { cfg = JSON.parse(cfgEl.textContent); } catch (e) { return; }
  if (!cfg || (!cfg.ga4 && !cfg.pixel)) return;

  var KEY = 'fp_consent_v1';
  var loaded = false;

  /* Storage can be blocked (private windows, strict settings). Without it
     the choice simply is not remembered, and the banner asks again. */
  function getChoice() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function setChoice(v) {
    try { window.localStorage.setItem(KEY, v); } catch (e) { /* not remembered */ }
  }

  /* ------------------------------------------------------------ loaders */
  function addScript(src) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    document.head.appendChild(s);
  }

  function loadGA4() {
    if (!cfg.ga4) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    /* Consent mode signals, so Google Ads and GA4 know the basis on which
       the data was collected. Only ever reached after Accept. */
    window.gtag('consent', 'default', {
      ad_storage: 'denied', analytics_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied'
    });
    window.gtag('consent', 'update', {
      ad_storage: 'granted', analytics_storage: 'granted',
      ad_user_data: 'granted', ad_personalization: 'granted'
    });
    window.gtag('js', new Date());
    window.gtag('config', cfg.ga4);
    addScript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(cfg.ga4));
  }

  function loadPixel() {
    if (!cfg.pixel) return;
    /* Meta's standard base code, unchanged apart from formatting. */
    /* eslint-disable */
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0';
      n.queue = []; t = b.createElement(e); t.async = !0; t.src = v;
      s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    /* eslint-enable */
    window.fbq('consent', 'grant');
    /* Turn off Meta's automatic configuration BEFORE init. Left on, the
       Pixel scans the page and can log its own Lead and Contact events from
       form submissions and phone-link taps, which would double-count the
       ones sent below. Every conversion here is sent deliberately, once. */
    window.fbq('set', 'autoConfig', false, cfg.pixel);
    window.fbq('init', cfg.pixel);
    window.fbq('track', 'PageView');
  }

  function grant() {
    setChoice('granted');
    if (loaded) {
      if (window.gtag) window.gtag('consent', 'update', {
        ad_storage: 'granted', analytics_storage: 'granted',
        ad_user_data: 'granted', ad_personalization: 'granted'
      });
      if (window.fbq) window.fbq('consent', 'grant');
      return;
    }
    loaded = true;
    loadGA4();
    loadPixel();
  }

  /* Withdrawing consent has to actually stop the tracking, not just hide
     the banner: tell both tags, and remove the cookies they already set. */
  function revoke() {
    setChoice('denied');
    if (window.gtag) window.gtag('consent', 'update', {
      ad_storage: 'denied', analytics_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied'
    });
    if (window.fbq) window.fbq('consent', 'revoke');
    clearTrackingCookies();
  }

  function clearTrackingCookies() {
    var host = location.hostname;
    var bare = host.replace(/^www\./, '');
    var domains = ['', host, '.' + host, bare, '.' + bare];
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (!/^(_ga|_gid|_gat|_fbp|_fbc)/.test(name)) return;
      domains.forEach(function (d) {
        document.cookie = name + '=; Max-Age=0; path=/' + (d ? '; domain=' + d : '');
      });
    });
  }

  /* ------------------------------------------------------------- events
     One name per conversion, so each can be marked as a key event in GA4
     separately. Meta gets its matching standard event, which its ad system
     recognises without extra setup. */
  var EVENTS = {
    quote_request:   { meta: 'Lead',     label: 'Quote request' },
    contact_request: { meta: 'Lead',     label: 'Contact form' },
    booking_request: { meta: 'Schedule', label: 'Booking request' },
    phone_click:     { meta: 'Contact',  label: 'Phone call' },
    text_click:      { meta: 'Contact',  label: 'Text message' }
  };
  /* The only parameters ever forwarded. Anything else is dropped, so a
     future caller cannot leak a name or phone number by accident. */
  var ALLOWED = { form_id: 1, link_location: 1, value: 1, currency: 1 };

  window.fpTrack = function (name, params) {
    if (getChoice() !== 'granted' || !loaded) return;
    var ev = EVENTS[name];
    if (!ev) return;
    var p = {};
    Object.keys(params || {}).forEach(function (k) {
      if (ALLOWED[k] && params[k] !== undefined && params[k] !== null && params[k] !== '') p[k] = params[k];
    });
    if (p.value !== undefined) p.currency = 'CAD';
    if (window.gtag && cfg.ga4) window.gtag('event', name, p);
    if (window.fbq && cfg.pixel) {
      var m = { content_name: ev.label };
      if (p.value !== undefined) { m.value = p.value; m.currency = 'CAD'; }
      window.fbq('track', ev.meta, m);
    }
  };

  /* Phone and text taps: every tel: and sms: link on every page, including
     the sticky bar on mobile, without touching each one. */
  function where(el) {
    if (el.closest('.callbar')) return 'mobile_bar';
    if (el.closest('.site-header, .drawer')) return 'header';
    if (el.closest('.site-footer')) return 'footer';
    return 'page';
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="sms:"]');
    if (!a) return;
    var isText = a.getAttribute('href').indexOf('sms:') === 0;
    window.fpTrack(isText ? 'text_click' : 'phone_click', { link_location: where(a) });
  });

  /* ------------------------------------------------------------- banner */
  var banner = document.getElementById('consent-banner');
  function show() { if (banner) banner.hidden = false; }
  function hide() { if (banner) banner.hidden = true; }

  if (banner) {
    banner.addEventListener('click', function (e) {
      var b = e.target.closest('[data-consent]');
      if (!b) return;
      if (b.getAttribute('data-consent') === 'accept') grant(); else revoke();
      hide();
    });
  }
  /* "Cookie settings" in the footer reopens the choice at any time.
     Withdrawing consent must be as easy as giving it. */
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-cookie-settings]');
    if (!t) return;
    e.preventDefault();
    show();
  });

  var choice = getChoice();
  if (choice === 'granted') grant();
  else if (choice !== 'denied') show();
})();
