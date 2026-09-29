/* ==========================================================================
   Carpet & Upholstery estimate calculator — Fast and Perfect Ltd.

   Every number this file uses comes from assets/data/pricing.json.
   There are no prices hard-coded here: to change a price, edit that file
   (or use /admin-pricing.html) and re-upload it. Nothing here needs touching.
   ========================================================================== */
(function (global) {
  'use strict';

  /* ---------------------------------------------------------------- maths
     Kept as a pure function so it can be tested on its own and so the same
     logic drives the calculator, the summary and the quote hand-off.

     state = {
       rooms: int, hallways: int, steps: int,
       items: { chair: 2, sofa: 1, ... },
       treatments: ['heavy_stain', ...]
     }
     Returns { low, high, lines[], minimumApplied, hasFrom }
  */
  function estimate(state, pricing) {
    var lines = [];
    var subtotal = 0;
    var hasFrom = false;

    var rooms = Math.max(0, state.rooms | 0);
    var tiers = pricing.carpet.room_tiers || [];

    /* Carpeted rooms are TIERED, not per-unit: the published guide prices
       1–5 rooms individually, and only then charges per extra room. */
    if (rooms > 0) {
      var roomCost;
      if (rooms <= tiers.length) {
        roomCost = tiers[rooms - 1];
      } else {
        roomCost = tiers[tiers.length - 1] +
          (rooms - tiers.length) * pricing.carpet.additional_room;
      }
      subtotal += roomCost;
      lines.push({
        label: rooms + (rooms === 1 ? ' carpeted room' : ' carpeted rooms'),
        amount: roomCost
      });
    }

    var halls = Math.max(0, state.hallways | 0);
    if (halls > 0) {
      var hallCost = halls * pricing.carpet.hallway;
      subtotal += hallCost;
      lines.push({
        label: halls === 1 ? 'Hallway' : halls + ' hallways',
        amount: hallCost
      });
    }

    /* Stairs: a flat base covers the first N steps, then per-step after. */
    var steps = Math.max(0, state.steps | 0);
    if (steps > 0) {
      var inc = pricing.carpet.stairs_included_steps;
      var stairCost = pricing.carpet.stairs_base +
        Math.max(0, steps - inc) * pricing.carpet.additional_step;
      subtotal += stairCost;
      lines.push({
        label: 'Stairs (' + steps + (steps === 1 ? ' step' : ' steps') + ')',
        amount: stairCost
      });
    }

    (pricing.items || []).forEach(function (item) {
      var qty = Math.max(0, (state.items && state.items[item.key]) | 0);
      if (!qty) return;
      var cost = qty * item.price;
      subtotal += cost;
      if (item.from) hasFrom = true;
      lines.push({
        label: (qty > 1 ? qty + ' x ' : '') + item.label +
          (item.from ? ' (from)' : ''),
        amount: cost
      });
    });

    /* Treatments are quoted as a RANGE, so the whole estimate becomes one. */
    var extraLow = 0, extraHigh = 0;
    (pricing.treatments || []).forEach(function (t) {
      if (!state.treatments || state.treatments.indexOf(t.key) === -1) return;
      extraLow += t.min;
      extraHigh += t.max;
      lines.push({ label: t.label, amount: t.min, amountMax: t.max });
    });

    var low = subtotal + extraLow;
    var high = subtotal + extraHigh;

    /* The minimum service charge applies to every appointment. */
    var min = pricing.minimum_service_charge || 0;
    var minimumApplied = false;
    if (low < min) { low = min; minimumApplied = true; }
    if (high < min) { high = min; }

    return {
      low: low,
      high: high,
      subtotal: subtotal,
      lines: lines,
      minimumApplied: minimumApplied,
      hasFrom: hasFrom,
      empty: lines.length === 0
    };
  }

  function money(n, currency) {
    var s = '$' + Math.round(n).toLocaleString('en-CA');
    return currency ? s + ' ' + currency : s;
  }

  function formatRange(result) {
    if (result.low === result.high) return money(result.low);
    return money(result.low) + ' – ' + money(result.high);
  }

  global.FPCarpet = {
    estimate: estimate,
    money: money,
    formatRange: formatRange
  };
})(typeof window !== 'undefined' ? window : globalThis);


/* ======================================================================
   UI wiring — only runs if the calculator is present on the page.
   ====================================================================== */
(function () {
  'use strict';
  if (typeof document === 'undefined') return;

  var root = document.getElementById('carpet-calculator');
  if (!root) return;

  var PRICING = null;

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) {
    return Array.prototype.slice.call((c || document).querySelectorAll(s));
  };

  /* Prefer the live JSON file so the owner can change prices by re-uploading
     it alone. Fall back to the copy embedded at build time if the fetch
     fails (offline, file://, or a host that will not serve .json). */
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

  function readState() {
    var items = {};
    $$('[data-qty]', root).forEach(function (w) {
      items[w.getAttribute('data-qty')] =
        parseInt($('input[type="hidden"]', w).value, 10) || 0;
    });
    return {
      rooms: items.__rooms || 0,
      hallways: items.__hallways || 0,
      steps: items.__steps || 0,
      items: items,
      treatments: $$('input[name="treatment"]:checked', root)
        .map(function (i) { return i.value; })
    };
  }

  function render() {
    if (!PRICING) return;
    var state = readState();
    var r = window.FPCarpet.estimate(state, PRICING);

    var priceEl = $('#carpet-price', root);
    var linesEl = $('#carpet-lines', root);
    var noteEl = $('#carpet-min-note', root);

    if (priceEl) {
      priceEl.innerHTML = r.empty
        ? '&mdash;<small>Select what needs cleaning</small>'
        : window.FPCarpet.formatRange(r) + '<small>Estimated price, ' +
          (PRICING.currency || 'CAD') + '</small>';
    }

    if (linesEl) {
      if (r.empty) {
        linesEl.innerHTML = '';
      } else {
        var html = r.lines.map(function (l) {
          var amt = l.amountMax !== undefined
            ? '+' + window.FPCarpet.money(l.amount) + ' – ' +
              window.FPCarpet.money(l.amountMax)
            : window.FPCarpet.money(l.amount);
          return '<li><span>' + l.label + '</span><b>' + amt + '</b></li>';
        }).join('');
        if (r.minimumApplied) {
          html += '<li><span>Minimum service charge applied</span><b>' +
            window.FPCarpet.money(PRICING.minimum_service_charge) + '</b></li>';
        }
        linesEl.innerHTML = html;
      }
    }

    if (noteEl) {
      if (r.empty) {
        noteEl.textContent = 'A minimum service charge of ' +
          window.FPCarpet.money(PRICING.minimum_service_charge) +
          ' applies to every appointment.';
      } else if (r.minimumApplied) {
        noteEl.textContent = 'Your selection comes to less than the ' +
          window.FPCarpet.money(PRICING.minimum_service_charge) +
          ' minimum service charge, so the minimum applies.';
      } else if (r.hasFrom) {
        noteEl.textContent = 'Sectionals start at the price shown — larger ' +
          'sectionals are measured and quoted on site.';
      } else {
        noteEl.textContent = 'A minimum service charge of ' +
          window.FPCarpet.money(PRICING.minimum_service_charge) +
          ' applies to every appointment.';
      }
    }

    // carry the selection into the quote form if it is on this page
    var carry = $('#carpet-estimate-field');
    if (carry) {
      carry.value = r.empty ? '' :
        window.FPCarpet.formatRange(r) + ' — ' +
        r.lines.map(function (l) { return l.label; }).join(', ');
    }
  }

  /* quantity steppers (same pattern as the rest of the site) */
  function wireSteppers() {
    $$('[data-qty]', root).forEach(function (wrap) {
      var out = $('output', wrap);
      var store = $('input[type="hidden"]', wrap);
      var min = parseInt(wrap.getAttribute('data-min') || '0', 10);
      var max = parseInt(wrap.getAttribute('data-max') || '30', 10);
      var stepBy = parseInt(wrap.getAttribute('data-step-by') || '1', 10);

      var write = function (v) {
        v = Math.min(max, Math.max(min, v));
        store.value = String(v);
        out.textContent = String(v);
        wrap.classList.toggle('is-active', v > 0);
        render();
      };
      $$('button', wrap).forEach(function (btn) {
        btn.addEventListener('click', function () {
          var cur = parseInt(store.value, 10) || 0;
          write(cur + (btn.getAttribute('data-step') === 'up' ? stepBy : -stepBy));
        });
      });
      write(parseInt(store.value, 10) || 0);
    });
  }

  root.addEventListener('change', render);
  root.addEventListener('submit', function (e) { e.preventDefault(); });

  loadPricing().then(function (data) {
    if (!data) return;
    PRICING = data;
    renderRateTable(data);
    applyPricingLabels(data);
    wireSteppers();
    render();
  });

  /* Price labels beside each line item come from the same file. */
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
        __minimum: window.FPCarpet.money(p.minimum_service_charge),
        __maxroom: p.max_room_sqft + ' sq ft'
      };
      if (map[key]) el.textContent = map[key];
    });

    $$('[data-pricing-note]', document).forEach(function (el) {
      var k = el.getAttribute('data-pricing-note');
      if (k === 'max_room' && p.max_room_note) el.textContent = p.max_room_note;
      if (k === 'disclaimer' && p.disclaimer) el.textContent = p.disclaimer;
    });
  }

  /* The published rate table is generated from the same numbers, so it can
     never drift out of sync with the calculator. */
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
})();
