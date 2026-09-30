/* ==========================================================================
   Fast and Perfect Ltd. — site behaviour
   Plain ES2017, no dependencies, no build step.
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------
     CONFIG — the only block you normally need to touch.
     ------------------------------------------------------------------ */
  var CONFIG = {
    /* Delivery is configured on the <form action> itself (a native POST),
       not here — see the comment above the form handler for why. */
    FALLBACK_EMAIL: 'info@fastandperfect.ca',
    FALLBACK_PHONE: '(587) 338-0069',
    CURRENCY: 'CAD'
  };

  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) {
    return Array.prototype.slice.call((ctx || document).querySelectorAll(sel));
  };

  /* ================= Header: shadow on scroll ================= */
  var header = $('.site-header');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-stuck', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ================= Mobile drawer ================= */
  var burger = $('.burger');
  var drawer = $('.drawer');
  if (burger && drawer) {
    var setDrawer = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      drawer.classList.toggle('is-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    burger.addEventListener('click', function () {
      setDrawer(burger.getAttribute('aria-expanded') !== 'true');
    });
    $$('a', drawer).forEach(function (a) {
      a.addEventListener('click', function () { setDrawer(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setDrawer(false);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 960) setDrawer(false);
    });
  }

  /* ================= Scroll reveal ================= */
  var reveals = $$('.reveal');
  if (reveals.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var delay = parseInt(el.getAttribute('data-delay') || '0', 10);
          setTimeout(function () { el.classList.add('is-in'); }, delay);
          io.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    }
  }

  /* ================= Year stamp ================= */
  $$('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ================= Number steppers ================= */
  $$('[data-stepper]').forEach(function (wrap) {
    var out = $('output', wrap);
    var store = $('input[type="hidden"]', wrap);
    var min = parseInt(wrap.getAttribute('data-min') || '0', 10);
    var max = parseInt(wrap.getAttribute('data-max') || '20', 10);

    var read = function () { return parseInt(store.value || out.textContent, 10) || min; };
    var write = function (v) {
      v = Math.min(max, Math.max(min, v));
      store.value = String(v);
      out.textContent = String(v);
      wrap.dispatchEvent(new CustomEvent('stepper:change', { bubbles: true }));
    };

    $$('button', wrap).forEach(function (btn) {
      btn.addEventListener('click', function () {
        write(read() + (btn.getAttribute('data-step') === 'up' ? 1 : -1));
      });
    });
    write(read());
  });

  /* Pricing lives in pricing-engine.js + assets/data/pricing.json.
     There is deliberately no second copy of the rates in this file — a
     duplicate set silently drifted out of date once already. */

  /* Visible text of the checked radio in `name`, read from its own <label>
     so the summary always matches what the customer actually sees. */
  function labelOf(form, name) {
    var input = form.querySelector('input[name="' + name + '"]:checked');
    if (!input) return '—';
    var lab = form.querySelector('label[for="' + input.id + '"]');
    if (!lab) return input.value;
    var clone = lab.cloneNode(true);
    Array.prototype.forEach.call(clone.querySelectorAll('.tag'), function (t) {
      t.remove();
    });
    return clone.textContent.trim().replace(/\s+/g, ' ');
  }

  /* ================= Booking summary ================= */
  var bookForm = $('#booking-form');
  if (bookForm) {
    var sumList = $('#booking-summary');

    var labelFor = function (name) { return labelOf(bookForm, name); };

    var renderBooking = function () {
      var date = (bookForm.querySelector('[name="date"]') || {}).value || '';
      var beds = parseInt((bookForm.querySelector('input[name="bedrooms"]') || {}).value || '0', 10);
      var baths = parseInt((bookForm.querySelector('input[name="bathrooms"]') || {}).value || '0', 10);
      var sqft = (bookForm.querySelector('[name="sqft"]') || {}).value || '';
      var extras = $$('input[name="extras"]:checked', bookForm).map(function (i) {
        var lab = bookForm.querySelector('label[for="' + i.id + '"]');
        return lab ? lab.textContent.trim().replace(/\s+/g, ' ') : i.value;
      });

      var rows = [
        ['Service', labelFor('service')],
        ['Frequency', labelFor('frequency')],
        ['Property', beds + ' bed · ' + baths + ' bath' + (sqft ? ' · ' + sqft + ' sq ft' : '')]
      ];
      if (extras.length) rows.push(['Add-ons', extras.join(', ')]);
      if (date) {
        var d = new Date(date + 'T12:00:00');
        rows.push(['Date', isNaN(d) ? date : d.toLocaleDateString('en-CA', {
          weekday: 'short', month: 'short', day: 'numeric'
        })]);
      }
      var slot = labelFor('slot');
      if (slot && slot !== '—') rows.push(['Arrival window', slot]);

      if (sumList) {
        sumList.innerHTML = rows.map(function (r) {
          return '<li><span>' + r[0] + '</span><b>' + r[1] + '</b></li>';
        }).join('');
      }

      var hidden = bookForm.querySelector('[name="estimate"]');
      if (hidden) hidden.value = '';
    };

    bookForm.addEventListener('change', renderBooking);
    bookForm.addEventListener('input', renderBooking);
    bookForm.addEventListener('stepper:change', renderBooking);

    // no dates in the past; default to two days out
    var dateInput = bookForm.querySelector('[name="date"]');
    if (dateInput) {
      var today = new Date();
      var pad = function (n) { return String(n).padStart(2, '0'); };
      var iso = function (d) {
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
      };
      dateInput.min = iso(today);
      var soon = new Date(today.getTime());
      soon.setDate(soon.getDate() + 2);
      if (!dateInput.value) dateInput.value = iso(soon);
    }

    renderBooking();
  }

  /* ================= Before / after sliders ================= */
  $$('.ba').forEach(function (ba) {
    var after = $('.ba__after', ba);
    var handle = $('.ba__handle', ba);
    var knob = $('.ba__knob', ba);
    if (!after || !handle) return;

    var set = function (pct) {
      pct = Math.min(98, Math.max(2, pct));
      after.style.clipPath = 'inset(0 0 0 ' + pct + '%)';
      handle.style.left = pct + '%';
      if (knob) knob.style.left = pct + '%';
      ba.setAttribute('aria-valuenow', String(Math.round(pct)));
    };

    var fromEvent = function (e) {
      var rect = ba.getBoundingClientRect();
      var x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
      set((x / rect.width) * 100);
    };

    var dragging = false;
    ba.addEventListener('mousedown', function (e) { dragging = true; fromEvent(e); e.preventDefault(); });
    window.addEventListener('mousemove', function (e) { if (dragging) fromEvent(e); });
    window.addEventListener('mouseup', function () { dragging = false; });
    ba.addEventListener('touchstart', function (e) { dragging = true; fromEvent(e); }, { passive: true });
    ba.addEventListener('touchmove', function (e) { if (dragging) fromEvent(e); }, { passive: true });
    ba.addEventListener('touchend', function () { dragging = false; });

    // keyboard
    ba.setAttribute('tabindex', '0');
    ba.setAttribute('role', 'slider');
    ba.setAttribute('aria-label', 'Drag to compare before and after');
    ba.setAttribute('aria-valuemin', '0');
    ba.setAttribute('aria-valuemax', '100');
    ba.addEventListener('keydown', function (e) {
      var cur = parseFloat(ba.getAttribute('aria-valuenow') || '50');
      if (e.key === 'ArrowLeft') { set(cur - 4); e.preventDefault(); }
      if (e.key === 'ArrowRight') { set(cur + 4); e.preventDefault(); }
      if (e.key === 'Home') { set(2); e.preventDefault(); }
      if (e.key === 'End') { set(98); e.preventDefault(); }
    });

    set(50);
  });

  /* Builds a mailto: containing everything the customer typed, used as a
     recovery path if the submission endpoint is unreachable. */
  function mailtoFor(form) {
    var skip = /^_|^consent$/;
    var lines = [];
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || skip.test(el.name) || el.disabled) return;
      if ((el.type === 'checkbox' || el.type === 'radio') && !el.checked) return;
      var v = (el.value || '').trim();
      if (!v) return;
      var label = form.querySelector('label[for="' + el.id + '"]');
      var key = label ? label.textContent.replace(/\*/g, '').trim() : el.name;
      lines.push(key + ': ' + v);
    });
    var subjEl = form.querySelector('[name="_subject"]');
    var subject = subjEl ? subjEl.value : 'Website enquiry';
    return 'mailto:' + CONFIG.FALLBACK_EMAIL +
      '?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(lines.join('\n'));
  }

  /* ================= Forms =================
     The forms POST natively to the delivery endpoint rather than through
     fetch(). A fetch is an XHR and is therefore subject to CORS: the
     provider sits behind bot protection that answers without an
     Access-Control-Allow-Origin header, so the browser refuses to read the
     reply and the send fails even when the request is legitimate.

     A plain form POST is a navigation, not an XHR. No CORS applies, it
     works with JavaScript disabled, and if the provider ever does show a
     challenge the visitor sees it and can complete it — instead of the
     request failing silently behind the scenes.

     JS here only validates and guards spam; it never blocks the submit.
     ========================================================================= */
  $$('form[data-form]').forEach(function (form) {
    var status = $('.form-status', form);
    var submit = form.querySelector('[type="submit"]');

    // Keep the "email it instead" escape hatch visible and always working.
    var alt = $('[data-mailto-fallback]', form);
    if (alt) {
      var refreshAlt = function () { alt.href = mailtoFor(form); };
      form.addEventListener('input', refreshAlt);
      form.addEventListener('change', refreshAlt);
      refreshAlt();
    }

    form.addEventListener('submit', function (e) {
      // bots fill hidden fields; people never see them
      var hp = form.querySelector('input[name="_gotcha"]');
      var hp2 = form.querySelector('input[name="_honey"]');
      if ((hp && hp.value) || (hp2 && hp2.value)) {
        e.preventDefault();
        return;
      }

      if (!form.checkValidity()) {
        e.preventDefault();
        form.reportValidity();
        return;
      }

      // Let the native POST proceed. Show progress; the browser navigates.
      if (submit) {
        submit.disabled = true;
        submit.innerHTML = 'Sending…';
        // If the navigation is blocked or slow, give the button back so the
        // visitor is never stuck staring at a dead form.
        setTimeout(function () {
          submit.disabled = false;
          submit.innerHTML = submit.getAttribute('data-label') || 'Send';
          if (status) {
            status.className = 'form-status is-err';
            status.style.display = 'block';
            status.textContent = 'Still sending. If nothing happens, use the ' +
              '"email this instead" link below, or call ' + CONFIG.FALLBACK_PHONE + '.';
          }
        }, 12000);
      }
    });
  });

  /* ================= Smooth in-page anchors ================= */
  $$('a[href^="#"]:not([href="#"])').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var target = document.getElementById(a.getAttribute('href').slice(1));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      history.replaceState(null, '', a.getAttribute('href'));
    });
  });
})();
