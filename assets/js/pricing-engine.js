/* ==========================================================================
   Pricing engine — Fast and Perfect Ltd.

   Pure functions, no DOM. Every number comes from assets/data/pricing.json.
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
