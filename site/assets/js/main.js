/* ==========================================================================
   Fast and Perfect Ltd. — site behaviour
   Plain ES2017, no dependencies, no build step.
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------
     CONFIG — the only block you normally need to touch.
     FORM_ENDPOINT: paste the URL from your form provider (Web3Forms,
     Formspree, Netlify Forms, etc). While it is empty the forms run in
     demo mode: they validate and show the success screen, but nothing
     is actually delivered.
     ------------------------------------------------------------------ */
  var CONFIG = {
    FORM_ENDPOINT: '',
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

  /* ==================================================================
     QUOTE ESTIMATOR
     Rates are placeholders — confirm them with the owner before launch.
     ================================================================== */
  var RATES = {
    // service -> [base, perBedroom, perBathroom, perSqftHundred]
    residential: { base: 95, bed: 22, bath: 30, sqft100: 3.5 },
    deep:        { base: 165, bed: 34, bath: 46, sqft100: 5.5 },
    moveinout:   { base: 195, bed: 40, bath: 55, sqft100: 6.5 },
    carpet:      { base: 89, bed: 42, bath: 0, sqft100: 4.0 },
    commercial:  { base: 130, bed: 0, bath: 28, sqft100: 4.5 }
  };
  var FREQ = {
    onetime: { mult: 1, label: 'One-time', off: 0 },
    monthly: { mult: 0.9, label: 'Monthly', off: 10 },
    biweekly: { mult: 0.85, label: 'Every 2 weeks', off: 15 },
    weekly: { mult: 0.8, label: 'Weekly', off: 20 }
  };
  var EXTRA_PRICE = {
    fridge: 35, oven: 35, windows: 55, laundry: 25, garage: 45, basement: 40
  };
  var EXTRA_LABEL = {
    fridge: 'Inside fridge', oven: 'Inside oven', windows: 'Interior windows',
    laundry: 'Laundry', garage: 'Garage', basement: 'Finished basement'
  };

  var money = function (n) {
    return '$' + Math.round(n).toLocaleString('en-CA');
  };

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

  function readEstimator(form) {
    var service = (form.querySelector('input[name="service"]:checked') || {}).value || 'residential';
    var freq = (form.querySelector('input[name="frequency"]:checked') || {}).value || 'onetime';
    var beds = parseInt((form.querySelector('input[name="bedrooms"]') || {}).value || '0', 10);
    var baths = parseInt((form.querySelector('input[name="bathrooms"]') || {}).value || '0', 10);
    var sqft = parseInt((form.querySelector('[name="sqft"]') || {}).value || '0', 10);
    var extras = $$('input[name="extras"]:checked', form).map(function (i) { return i.value; });
    return { service: service, freq: freq, beds: beds, baths: baths, sqft: sqft, extras: extras };
  }

  function priceEstimate(s) {
    var r = RATES[s.service] || RATES.residential;
    var subtotal = r.base + r.bed * s.beds + r.bath * s.baths;
    if (s.sqft > 0) subtotal += (s.sqft / 100) * r.sqft100;

    var extrasTotal = s.extras.reduce(function (sum, key) {
      return sum + (EXTRA_PRICE[key] || 0);
    }, 0);
    subtotal += extrasTotal;

    var f = FREQ[s.freq] || FREQ.onetime;
    var total = subtotal * f.mult;

    return {
      subtotal: subtotal,
      extrasTotal: extrasTotal,
      discountPct: f.off,
      discountAmt: subtotal - total,
      total: total,
      low: total * 0.9,
      high: total * 1.15,
      freqLabel: f.label
    };
  }

  var estForm = $('#estimator-form');
  if (estForm) {
    var priceEl = $('#est-price');
    var breakEl = $('#est-breakdown');
    var subEl = $('#est-sub');

    // While the owner's rates are unconfirmed the calculator collects the job
    // details but publishes no dollar figure anywhere.
    var pricesOff = estForm.getAttribute('data-prices') === 'off';

    var renderEstimate = function () {
      var state = readEstimator(estForm);

      if (pricesOff) {
        if (breakEl) {
          var rows2 = [
            ['Service', labelOf(estForm, 'service')],
            ['Frequency', labelOf(estForm, 'frequency')],
            ['Property', state.beds + ' bed · ' + state.baths + ' bath' +
              (state.sqft ? ' · ' + state.sqft + ' sq ft' : '')]
          ];
          if (state.extras.length) {
            rows2.push(['Add-ons', state.extras.map(function (k) {
              return EXTRA_LABEL[k] || k;
            }).join(', ')]);
          }
          breakEl.innerHTML = rows2.map(function (r) {
            return '<li><span>' + r[0] + '</span><b>' + r[1] + '</b></li>';
          }).join('');
        }
        return;
      }

      var p = priceEstimate(state);

      if (priceEl) {
        priceEl.innerHTML = money(p.low) + '&thinsp;&ndash;&thinsp;' + money(p.high) +
          '<small>' + CONFIG.CURRENCY + '</small>';
      }
      if (subEl) {
        subEl.textContent = p.discountPct > 0
          ? p.freqLabel + ' service — ' + p.discountPct + '% recurring discount already applied.'
          : 'One-time visit. Switch to a recurring plan to save up to 20%.';
      }
      if (breakEl) {
        // only itemise when there is actually something to itemise — a
        // "Base clean $221 / Estimated total $221" pair just reads as a bug
        var rows = [];
        if (p.extrasTotal > 0 || p.discountAmt > 0.5) {
          rows.push(['Base clean', money(p.subtotal - p.extrasTotal)]);
        }
        if (p.extrasTotal > 0) rows.push(['Add-ons (' + state.extras.length + ')', money(p.extrasTotal)]);
        if (p.discountAmt > 0.5) rows.push([p.freqLabel + ' discount', '&minus;' + money(p.discountAmt)]);
        rows.push(['Estimated total', money(p.total)]);
        breakEl.innerHTML = rows.map(function (r) {
          return '<li><span>' + r[0] + '</span><b>' + r[1] + '</b></li>';
        }).join('');
      }

      // carry the estimate into the quote form if both are on the page
      var carry = $('#quote-estimate');
      if (carry) carry.value = money(p.low) + '–' + money(p.high) + ' (' + p.freqLabel + ')';
    };

    /* Carpet & upholstery is priced by room, staircase and furniture item —
       not by bedroom count — so it has its own calculator. Surface the link
       only when someone actually picks carpet. */
    var carpetHint = $('#carpet-redirect');
    if (carpetHint) {
      var toggleCarpetHint = function () {
        var picked = estForm.querySelector('input[name="service"]:checked');
        carpetHint.hidden = !picked || picked.value !== 'carpet';
      };
      estForm.addEventListener('change', toggleCarpetHint);
      toggleCarpetHint();
    }

    estForm.addEventListener('change', renderEstimate);
    estForm.addEventListener('input', renderEstimate);
    estForm.addEventListener('stepper:change', renderEstimate);
    estForm.addEventListener('submit', function (e) { e.preventDefault(); });
    renderEstimate();

    // "Send me this quote" — copy the live estimate into the quote form
    var jumpBtn = $('#est-continue');
    if (jumpBtn) {
      jumpBtn.addEventListener('click', function () {
        var state = readEstimator(estForm);
        var target = $('#quote-form');
        if (!target) return;
        var set = function (name, val) {
          var f = target.querySelector('[name="' + name + '"]');
          if (f) f.value = val;
        };
        set('service_interest', state.service);
        set('frequency', state.freq);
        if (!pricesOff) {
          var p = priceEstimate(state);
          set('estimate', money(p.low) + '-' + money(p.high) + ' ' + CONFIG.CURRENCY);
        }
        set('property', state.beds + ' bed / ' + state.baths + ' bath' +
          (state.sqft ? ' / ' + state.sqft + ' sq ft' : ''));
        if (state.extras.length) {
          set('extras', state.extras.map(function (k) { return EXTRA_LABEL[k] || k; }).join(', '));
        }
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        var first = target.querySelector('input[name="name"]');
        if (first) setTimeout(function () { first.focus(); }, 550);
      });
    }
  }

  /* ================= Booking summary ================= */
  var bookForm = $('#booking-form');
  if (bookForm) {
    var sumList = $('#booking-summary');
    var sumTotal = $('#booking-total');
    var bookPricesOff = bookForm.getAttribute('data-prices') === 'off';

    var labelFor = function (name) { return labelOf(bookForm, name); };

    var renderBooking = function () {
      var state = readEstimator(bookForm);
      var p = priceEstimate(state);
      var date = (bookForm.querySelector('[name="date"]') || {}).value || '';
      var slot = labelFor('slot');

      var rows = [
        ['Service', labelFor('service') || '—'],
        ['Frequency', bookPricesOff ? labelFor('frequency') : p.freqLabel],
        ['Property', state.beds + ' bed · ' + state.baths + ' bath' + (state.sqft ? ' · ' + state.sqft + ' sq ft' : '')]
      ];
      if (state.extras.length) {
        rows.push(['Add-ons', state.extras.map(function (k) { return EXTRA_LABEL[k] || k; }).join(', ')]);
      }
      if (date) {
        var d = new Date(date + 'T12:00:00');
        rows.push(['Date', isNaN(d) ? date : d.toLocaleDateString('en-CA', {
          weekday: 'short', month: 'short', day: 'numeric'
        })]);
      }
      if (slot) rows.push(['Arrival window', slot]);

      if (sumList) {
        sumList.innerHTML = rows.map(function (r) {
          return '<li><span>' + r[0] + '</span><b>' + r[1] + '</b></li>';
        }).join('');
      }
      if (sumTotal && !bookPricesOff) {
        sumTotal.innerHTML = money(p.low) + '&thinsp;&ndash;&thinsp;' + money(p.high);
      }
      var hidden = bookForm.querySelector('[name="estimate"]');
      if (hidden && !bookPricesOff) {
        hidden.value = money(p.low) + '–' + money(p.high) + ' ' + CONFIG.CURRENCY;
      }
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

  /* ================= Forms ================= */
  $$('form[data-form]').forEach(function (form) {
    var status = $('.form-status', form);
    var submit = form.querySelector('[type="submit"]');

    var say = function (msg, ok) {
      if (!status) return;
      status.className = 'form-status ' + (ok ? 'is-ok' : 'is-err');
      status.textContent = msg;
      status.setAttribute('role', 'status');
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // honeypot — bots fill hidden fields, people never see them
      var hp = form.querySelector('input[name="_gotcha"]');
      if (hp && hp.value) return;

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      var original = submit ? submit.innerHTML : '';
      if (submit) {
        submit.disabled = true;
        submit.innerHTML = 'Sending…';
      }

      var done = function (ok, msg) {
        if (submit) { submit.disabled = false; submit.innerHTML = original; }
        say(msg, ok);
        if (ok) {
          form.reset();
          $$('[data-stepper]').forEach(function (w) {
            var o = $('output', w), h = $('input[type="hidden"]', w);
            if (o && h) { h.value = h.defaultValue || '1'; o.textContent = h.value; }
          });
          form.dispatchEvent(new Event('change'));
        }
      };

      if (!CONFIG.FORM_ENDPOINT) {
        // Demo mode — nothing is transmitted.
        setTimeout(function () {
          done(true, 'Thanks! Your request has been received — we\'ll be in touch shortly. (Demo mode: connect your form endpoint in assets/js/main.js to start receiving these.)');
        }, 700);
        return;
      }

      var data = new FormData(form);
      fetch(CONFIG.FORM_ENDPOINT, {
        method: 'POST',
        body: data,
        headers: { Accept: 'application/json' }
      })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          done(true, 'Thanks! Your request has been received — we\'ll be in touch shortly.');
        })
        .catch(function () {
          done(false, 'Sorry, something went wrong sending that. Please call us directly and we\'ll take care of it.');
        });
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
