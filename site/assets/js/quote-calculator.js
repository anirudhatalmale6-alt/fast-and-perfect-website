/* ==========================================================================
   Smart quote calculator — Fast and Perfect Ltd.

   ONE calculator for every service. The customer ticks the services they
   need and only the relevant questions appear. Several services can be
   combined into a single quote (e.g. carpet + upholstery).

   Pricing comes from assets/data/pricing.json via FPCarpet (pricing-engine.js).
   Carpet and upholstery have confirmed prices, so they produce a live
   estimate. Residential and commercial are listed as "quoted separately"
   until their prices are confirmed — see data-prices-general on the root.
   ========================================================================== */
(function () {
  'use strict';

  var root = document.getElementById('quote-calculator');
  if (!root) return;

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) {
    return Array.prototype.slice.call((c || document).querySelectorAll(s));
  };

  var PRICING = null;
  var GENERAL_PRICES_ON = root.getAttribute('data-prices-general') === 'on';

  /* Which panel each service needs. Treatments are shared by carpet and
     upholstery, so they appear once when either is selected. */
  var SERVICE_PANELS = {
    residential: ['home'],
    deep: ['home'],
    moveinout: ['home'],
    commercial: ['commercial'],
    carpet: ['carpet', 'treatments'],
    upholstery: ['upholstery', 'treatments']
  };
  var PRICED = { carpet: true, upholstery: true };

  function selectedServices() {
    return $$('input[name="service"]:checked', root)
      .map(function (i) { return i.value; });
  }

  function serviceLabel(value) {
    var input = $('input[name="service"][value="' + value + '"]', root);
    if (!input) return value;
    var lab = $('label[for="' + input.id + '"]', root);
    return lab ? lab.textContent.trim().replace(/\s+/g, ' ') : value;
  }

  /* ------------------------------------------------- show/hide the panels */
  function syncPanels() {
    var services = selectedServices();
    var needed = {};
    services.forEach(function (s) {
      (SERVICE_PANELS[s] || []).forEach(function (p) { needed[p] = true; });
    });
    $$('[data-panel]', root).forEach(function (panel) {
      var name = panel.getAttribute('data-panel');
      var show = !!needed[name];
      panel.hidden = !show;
      // never submit values from a panel the customer cannot see
      $$('input, select, textarea', panel).forEach(function (f) {
        f.disabled = !show;
      });
    });
    $$('.choice input[name="service"]', root).forEach(function (i) {
      var lab = $('label[for="' + i.id + '"]', root);
      if (lab) lab.classList.toggle('is-on', i.checked);
    });
  }

  /* --------------------------------------------------------- read values */
  function hiddenPanel(el) {
    var panel = el && el.closest('[data-panel]');
    return !!(panel && panel.hidden);
  }

  function qty(key) {
    var w = $('[data-qty="' + key + '"]', root);
    if (!w || hiddenPanel(w)) return 0;
    return parseInt($('input[type="hidden"]', w).value, 10) || 0;
  }

  function val(name) {
    var el = $('[name="' + name + '"]', root);
    if (!el || hiddenPanel(el)) return '';
    return el.value || '';
  }

  function checkedLabel(name) {
    var i = $('input[name="' + name + '"]:checked', root);
    if (!i || hiddenPanel(i)) return '';
    var lab = $('label[for="' + i.id + '"]', root);
    if (!lab) return i.value;
    var clone = lab.cloneNode(true);
    $$('.tag', clone).forEach(function (t) { t.remove(); });
    return clone.textContent.trim().replace(/\s+/g, ' ');
  }

  function readState() {
    var services = selectedServices();
    var wantsCarpet = services.indexOf('carpet') !== -1;
    var wantsUph = services.indexOf('upholstery') !== -1;

    var items = {};
    if (wantsUph && PRICING) {
      PRICING.items.forEach(function (it) { items[it.key] = qty(it.key); });
    }

    return {
      services: services,
      wantsCarpet: wantsCarpet,
      wantsUph: wantsUph,
      // home
      beds: qty('__beds'),
      baths: qty('__baths'),
      sqft: val('sqft'),
      frequency: checkedLabel('frequency'),
      extras: $$('input[name="extras"]:checked', root)
        .filter(function (i) { return !hiddenPanel(i); })
        .map(function (i) {
          var lab = $('label[for="' + i.id + '"]', root);
          return lab ? lab.textContent.trim() : i.value;
        }),
      // commercial
      commSqft: val('comm_sqft'),
      commType: val('comm_type'),
      commFreq: val('comm_frequency'),
      // carpet
      rooms: wantsCarpet ? qty('__rooms') : 0,
      hallways: wantsCarpet ? qty('__hallways') : 0,
      steps: wantsCarpet ? qty('__steps') : 0,
      items: items,
      treatments: (wantsCarpet || wantsUph)
        ? $$('input[name="treatment"]:checked', root)
          .filter(function (i) { return !hiddenPanel(i); })
          .map(function (i) { return i.value; })
        : []
    };
  }

  /* -------------------------------------------------------------- render */
  function render() {
    if (!PRICING) return;
    syncPanels();

    var s = readState();
    var priceEl = $('#quote-price', root);
    var linesEl = $('#quote-lines', root);
    var noteEl = $('#quote-note', root);
    var summaryEl = $('#quote-services', root);

    // which chosen services can be priced right now, and which cannot
    var pricedPicked = s.services.filter(function (x) { return PRICED[x]; });
    var unpricedPicked = s.services.filter(function (x) { return !PRICED[x]; });

    if (summaryEl) {
      summaryEl.innerHTML = s.services.length
        ? s.services.map(function (x) {
          return '<li><span>' + serviceLabel(x) + '</span><b>' +
            (PRICED[x] ? 'estimated below' : 'quoted separately') + '</b></li>';
        }).join('')
        : '';
    }

    var lines = [];
    var result = null;

    if (pricedPicked.length) {
      result = window.FPCarpet.estimate({
        rooms: s.rooms, hallways: s.hallways, steps: s.steps,
        items: s.items, treatments: s.treatments
      }, PRICING);
      lines = result.lines;
    }

    // headline figure
    if (priceEl) {
      if (!s.services.length) {
        priceEl.innerHTML = '&mdash;<small>Choose a service to start</small>';
      } else if (!pricedPicked.length) {
        priceEl.innerHTML = 'Quoted<small>in writing, free</small>';
      } else {
        priceEl.innerHTML = window.FPCarpet.formatRange(result) +
          '<small>Estimated price, ' + (PRICING.currency || 'CAD') + '</small>';
      }
    }

    // breakdown
    if (linesEl) {
      var html = lines.map(function (l) {
        var amt = l.amountMax !== undefined
          ? '+' + window.FPCarpet.money(l.amount) + ' – ' +
            window.FPCarpet.money(l.amountMax)
          : window.FPCarpet.money(l.amount);
        return '<li><span>' + l.label + '</span><b>' + amt + '</b></li>';
      });
      if (result && result.minimumApplied) {
        html.push('<li><span>Minimum service charge applied</span><b>' +
          window.FPCarpet.money(PRICING.minimum_service_charge) + '</b></li>');
      }
      // unpriced services are already listed in #quote-services — do not
      // repeat them here
      linesEl.innerHTML = html.join('');
    }

    // supporting note
    if (noteEl) {
      if (!s.services.length) {
        noteEl.textContent = 'Tick the services you need — the questions change ' +
          'to match, and you only see what is relevant to you.';
      } else if (!pricedPicked.length) {
        noteEl.textContent = 'Send these details through and we will come back ' +
          'with a written price. Free, and with no obligation.';
      } else if (result && result.minimumApplied) {
        noteEl.textContent = 'Your selection comes to less than the ' +
          window.FPCarpet.money(PRICING.minimum_service_charge) +
          ' minimum service charge, so the minimum applies.';
      } else if (unpricedPicked.length) {
        noteEl.textContent = 'The estimate above covers the carpet and ' +
          'upholstery work. The other services you picked are quoted separately ' +
          'and we will include them in your written quote.';
      } else if (result && result.hasFrom) {
        noteEl.textContent = 'Sectionals start at the price shown — larger ' +
          'sectionals are measured and quoted on site.';
      } else {
        noteEl.textContent = 'A minimum service charge of ' +
          window.FPCarpet.money(PRICING.minimum_service_charge) +
          ' applies to every carpet or upholstery appointment.';
      }
    }

    // the carpet disclaimer only makes sense when carpet/upholstery is picked
    var footEl = $('.est-foot', root);
    if (footEl) {
      footEl.textContent = pricedPicked.length
        ? PRICING.disclaimer
        : 'Your written quote is free and carries no obligation. We confirm ' +
          'the final price with you before any work is booked in.';
    }

    // hand everything to the quote form
    var field = $('#quote-detail-field');
    if (field) {
      var parts = [];
      if (s.services.length) parts.push('Services: ' + s.services.map(serviceLabel).join(', '));
      if (!$('[data-panel="home"]', root).hidden) {
        parts.push('Property: ' + s.beds + ' bed / ' + s.baths + ' bath' +
          (s.sqft ? ' / ' + s.sqft + ' sq ft' : ''));
        if (s.frequency) parts.push('Frequency: ' + s.frequency);
        if (s.extras.length) parts.push('Add-ons: ' + s.extras.join(', '));
      }
      if (!$('[data-panel="commercial"]', root).hidden) {
        if (s.commType) parts.push('Property type: ' + s.commType);
        if (s.commSqft) parts.push('Approx. size: ' + s.commSqft + ' sq ft');
        if (s.commFreq) parts.push('Frequency: ' + s.commFreq);
      }
      if (lines.length) {
        parts.push('Items: ' + lines.map(function (l) { return l.label; }).join(', '));
      }
      if (result) parts.push('Estimate: ' + window.FPCarpet.formatRange(result));
      field.value = parts.join(' | ');
    }
  }

  /* ------------------------------------------------------------ steppers */
  function wireSteppers() {
    $$('[data-qty]', root).forEach(function (wrap) {
      var out = $('output', wrap);
      var store = $('input[type="hidden"]', wrap);
      var min = parseInt(wrap.getAttribute('data-min') || '0', 10);
      var max = parseInt(wrap.getAttribute('data-max') || '30', 10);

      var write = function (v) {
        v = Math.min(max, Math.max(min, v));
        store.value = String(v);
        out.textContent = String(v);
        wrap.classList.toggle('is-active', v > 0);
        render();
      };
      $$('button', wrap).forEach(function (btn) {
        btn.addEventListener('click', function () {
          write((parseInt(store.value, 10) || 0) +
            (btn.getAttribute('data-step') === 'up' ? 1 : -1));
        });
      });
      write(parseInt(store.value, 10) || 0);
    });
  }

  /* ----------------------------------------------------- pricing labels  */
  function applyPricingLabels(p) {
    $$('[data-price-for]', document).forEach(function (el) {
      var key = el.getAttribute('data-price-for');
      var item = (p.items || []).filter(function (i) { return i.key === key; })[0];
      if (item) {
        el.textContent = (item.from ? 'from ' : '') + window.FPCarpet.money(item.price);
        return;
      }
      var t = (p.treatments || []).filter(function (i) { return i.key === key; })[0];
      if (t) {
        el.textContent = '+' + window.FPCarpet.money(t.min) + '–' +
          window.FPCarpet.money(t.max);
        return;
      }
      var map = {
        __hallways: '+' + window.FPCarpet.money(p.carpet.hallway) + ' each',
        __steps: window.FPCarpet.money(p.carpet.stairs_base) + ' up to ' +
          p.carpet.stairs_included_steps + ' steps, then +' +
          window.FPCarpet.money(p.carpet.additional_step) + '/step',
        __rooms: 'up to ' + p.max_room_sqft + ' sq ft each'
      };
      if (map[key]) el.textContent = map[key];
    });
    $$('[data-pricing-note]', document).forEach(function (el) {
      var k = el.getAttribute('data-pricing-note');
      if (k === 'max_room' && p.max_room_note) el.textContent = p.max_room_note;
      if (k === 'disclaimer' && p.disclaimer) el.textContent = p.disclaimer;
    });
  }

  /* ---------------------------------------------- published rate table   */
  function renderRateTable(p) {
    var body = document.getElementById('carpet-rate-body');
    if (!body) return;
    var rows = [];
    var push = function (a, b, c) {
      rows.push('<tr><td>' + a + '</td><td>' + b + '</td><td>' + c + '</td></tr>');
    };
    push('Minimum service charge', 'Applies to every appointment',
      window.FPCarpet.money(p.minimum_service_charge));
    p.carpet.room_tiers.forEach(function (price, i) {
      push((i + 1) + (i === 0 ? ' carpeted room' : ' carpeted rooms'),
        'Up to ' + p.max_room_sqft + ' sq ft per room',
        window.FPCarpet.money(price));
    });
    push('Each additional room', 'Up to ' + p.max_room_sqft + ' sq ft',
      '+' + window.FPCarpet.money(p.carpet.additional_room));
    push('Hallway', 'Per hallway', '+' + window.FPCarpet.money(p.carpet.hallway));
    push('Stairs', 'Up to approx. ' + p.carpet.stairs_included_steps + ' steps',
      '+' + window.FPCarpet.money(p.carpet.stairs_base));
    push('Each additional step', 'Beyond ' + p.carpet.stairs_included_steps + ' steps',
      '+' + window.FPCarpet.money(p.carpet.additional_step));
    (p.items || []).forEach(function (i) {
      push(i.label, i.group, (i.from ? 'from ' : '') + window.FPCarpet.money(i.price));
    });
    (p.treatments || []).forEach(function (t) {
      push(t.label, 'Depending on severity',
        '+' + window.FPCarpet.money(t.min) + '–' + window.FPCarpet.money(t.max));
    });
    body.innerHTML = rows.join('');
  }

  /* ---------------------------------------------------------------- init */
  function loadPricing() {
    var inline = document.getElementById('fp-pricing-inline');
    var fallback = null;
    if (inline) {
      try { fallback = JSON.parse(inline.textContent); } catch (e) { fallback = null; }
    }
    if (!window.fetch) return Promise.resolve(fallback);
    return fetch('assets/data/pricing.json', { cache: 'no-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .catch(function () { return fallback; });
  }

  /* ------------------------------------------------ carry state forward
     A customer who builds a detailed carpet quote on the carpet page and
     then clicks through to the quote form must not lose their selections.
     We serialise the whole calculator, stash it, and restore it on arrival. */
  var STORE_KEY = 'fp_quote_state';

  function serialize() {
    var qtys = {};
    $$('[data-qty]', root).forEach(function (w) {
      qtys[w.getAttribute('data-qty')] = $('input[type="hidden"]', w).value;
    });
    return {
      services: selectedServices(),
      qtys: qtys,
      sqft: (($('[name="sqft"]', root) || {}).value) || '',
      commType: (($('[name="comm_type"]', root) || {}).value) || '',
      commSqft: (($('[name="comm_sqft"]', root) || {}).value) || '',
      commFreq: (($('[name="comm_frequency"]', root) || {}).value) || '',
      commWash: (($('[name="comm_washrooms"]', root) || {}).value) || '',
      commNotes: (($('[name="comm_notes"]', root) || {}).value) || '',
      frequency: (($('input[name="frequency"]:checked', root) || {}).value) || '',
      extras: $$('input[name="extras"]:checked', root).map(function (i) { return i.value; }),
      treatments: $$('input[name="treatment"]:checked', root).map(function (i) { return i.value; })
    };
  }

  function restore(st) {
    if (!st) return;
    $$('input[name="service"]', root).forEach(function (i) {
      i.checked = st.services.indexOf(i.value) !== -1;
    });
    syncPanels();
    Object.keys(st.qtys || {}).forEach(function (k) {
      var w = $('[data-qty="' + k + '"]', root);
      if (!w) return;
      $('input[type="hidden"]', w).value = st.qtys[k];
      $('output', w).textContent = st.qtys[k];
      w.classList.toggle('is-active', parseInt(st.qtys[k], 10) > 0);
    });
    var setVal = function (sel, v) {
      var el = $(sel, root);
      if (el && v) el.value = v;
    };
    setVal('[name="sqft"]', st.sqft);
    setVal('[name="comm_type"]', st.commType);
    setVal('[name="comm_sqft"]', st.commSqft);
    setVal('[name="comm_frequency"]', st.commFreq);
    setVal('[name="comm_washrooms"]', st.commWash);
    setVal('[name="comm_notes"]', st.commNotes);
    if (st.frequency) {
      var f = $('input[name="frequency"][value="' + st.frequency + '"]', root);
      if (f) f.checked = true;
    }
    (st.extras || []).forEach(function (v) {
      var el = $('input[name="extras"][value="' + v + '"]', root);
      if (el) el.checked = true;
    });
    (st.treatments || []).forEach(function (v) {
      var el = $('input[name="treatment"][value="' + v + '"]', root);
      if (el) el.checked = true;
    });
  }

  function wireCta() {
    var cta = $('#quote-cta', root);
    if (!cta) return;
    cta.addEventListener('click', function (e) {
      try {
        sessionStorage.setItem(STORE_KEY, JSON.stringify(serialize()));
      } catch (err) { /* private mode — the quote form still works */ }

      // already on the page with the form? just scroll to it
      var form = document.getElementById('quote-form');
      if (form) {
        e.preventDefault();
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        var first = form.querySelector('input[name="name"]');
        if (first) setTimeout(function () { first.focus(); }, 550);
      }
    });
  }

  function restoreFromStore() {
    var raw = null;
    try { raw = sessionStorage.getItem(STORE_KEY); } catch (err) { return; }
    if (!raw) return;
    try { restore(JSON.parse(raw)); } catch (err) { return; }
    try { sessionStorage.removeItem(STORE_KEY); } catch (err) { /* ignore */ }
  }

  root.addEventListener('change', render);
  root.addEventListener('input', render);
  root.addEventListener('submit', function (e) { e.preventDefault(); });

  loadPricing().then(function (data) {
    if (!data) return;
    PRICING = data;
    applyPricingLabels(data);
    renderRateTable(data);
    wireSteppers();
    restoreFromStore();
    wireCta();
    render();
  });
})();
