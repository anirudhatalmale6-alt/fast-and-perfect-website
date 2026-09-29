/* ==========================================================================
   Pricing engine — Fast and Perfect Ltd.

   Pure functions, no DOM. Every number comes from assets/data/pricing.json.
   There are no prices hard-coded here: to change a price, edit that file
   (or use /admin-pricing.html) and re-upload it.

   Three families of pricing, each with its own rules:

   RESIDENTIAL  tiered by bedroom count, with a bathroom cap per tier.
                Outside the tiers (too many bedrooms/bathrooms) -> Custom Quote.
                Recurring discount applies to the BASE package only, never to
                add-ons, and never to the first clean.
   COMMERCIAL   banded by square footage, standard office/retail only.
                Any other property type, or over the top band -> Custom Quote.
                Recurring schedules are captured but never auto-discounted.
   CARPET/UPH   tiered rooms + per-item furniture, with a minimum service
                charge and treatments quoted as ranges.
   ========================================================================== */
(function (global) {
  'use strict';

  function round(n) { return Math.round(n); }

  function money(n, currency) {
    var s = '$' + Math.round(n).toLocaleString('en-CA');
    return currency ? s + ' ' + currency : s;
  }

  /* ------------------------------------------------------- carpet & uph. */
  function estimate(state, pricing) {
    var lines = [];
    var subtotal = 0;
    var hasFrom = false;

    var rooms = Math.max(0, state.rooms | 0);
    var tiers = (pricing.carpet && pricing.carpet.room_tiers) || [];

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

    /* The minimum service charge applies to carpet/upholstery appointments.
       Whether it still applies when a house or commercial clean is booked in
       the same visit is a business decision, so it is configurable. */
    var min = pricing.minimum_service_charge || 0;
    var applyMin = true;
    if (state.withOtherServices &&
        pricing.minimum_applies_with_other_services === false) {
      applyMin = false;
    }
    var minimumApplied = false;
    if (applyMin) {
      if (low < min) { low = min; minimumApplied = true; }
      if (high < min) { high = min; }
    }

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

  /* ----------------------------------------------------------- residential
     state: { package: 'regular'|'deep'|'moveinout', bedrooms, bathrooms,
              addons: {key: qty|true}, recurring: 'weekly'|... }               */
  function residential(state, pricing) {
    var cfg = pricing.residential;
    if (!cfg) return null;

    var pkg = state.package || 'regular';
    var beds = Math.max(0, state.bedrooms | 0);
    var baths = Math.max(0, state.bathrooms | 0);

    var tier = null;
    for (var i = 0; i < cfg.tiers.length; i++) {
      if (cfg.tiers[i].bedrooms === beds) { tier = cfg.tiers[i]; break; }
    }

    var custom = false;
    var reason = '';
    if (!tier) {
      custom = true;
      reason = beds > cfg.max_bedrooms
        ? 'Homes larger than ' + cfg.max_bedrooms + ' bedrooms are quoted individually.'
        : 'This home size is quoted individually.';
    } else if (baths > tier.max_bathrooms) {
      custom = true;
      reason = tier.label + ' is priced for up to ' + tier.max_bathrooms +
        ' bathroom' + (tier.max_bathrooms === 1 ? '' : 's') +
        '. With ' + baths + ', we quote it individually.';
    }

    var lines = [];
    var base = 0;
    if (!custom) {
      base = tier[pkg];
      if (typeof base !== 'number') { custom = true; reason = 'Quoted individually.'; }
    }

    /* Add-ons. Anything already covered by the chosen package is shown as
       included and costs nothing — never charged twice. */
    var included = (cfg.included_in && cfg.included_in[pkg]) || [];
    var addonTotal = 0;
    var addonHasFrom = false;
    (cfg.addons || []).forEach(function (a) {
      var picked = state.addons && state.addons[a.key];
      if (!picked) return;
      if (included.indexOf(a.key) !== -1) {
        lines.push({ label: a.label, included: true, amount: 0 });
        return;
      }
      var qty = a.qty ? Math.max(1, picked | 0) : 1;
      var cost = qty * a.price;
      addonTotal += cost;
      if (a.from) addonHasFrom = true;
      lines.push({
        label: (qty > 1 ? qty + ' x ' : '') + a.label + (a.from ? ' (from)' : ''),
        amount: cost
      });
    });

    if (custom) {
      return {
        custom: true, reason: reason, lines: lines,
        low: addonTotal, high: addonTotal, addonTotal: addonTotal,
        hasFrom: addonHasFrom
      };
    }

    /* Recurring discount: base only, and never on the first clean. */
    var rec = null;
    (cfg.recurring || []).forEach(function (r) {
      if (r.key === (state.recurring || 'onetime')) rec = r;
    });
    var discountPct = rec ? rec.discount : 0;
    var baseAfter = base * (1 - discountPct / 100);

    lines.unshift({
      label: tier.label + ' — ' + packageLabel(pkg, pricing),
      amount: base
    });

    var firstTotal = base + addonTotal;
    var afterTotal = baseAfter + addonTotal;

    return {
      custom: false,
      tier: tier,
      package: pkg,
      base: base,
      baseAfter: round(baseAfter),
      addonTotal: addonTotal,
      discountPct: discountPct,
      recurringLabel: rec ? rec.label : '',
      lines: lines,
      low: round(firstTotal),
      high: round(firstTotal),
      firstTotal: round(firstTotal),
      afterTotal: round(afterTotal),
      hasFrom: addonHasFrom
    };
  }

  function packageLabel(key, pricing) {
    return {
      regular: 'regular clean',
      deep: 'deep clean',
      moveinout: 'move in / move out'
    }[key] || key;
  }

  /* ------------------------------------------------------------ commercial
     state: { propertyType, sqft, frequency }                                 */
  function commercial(state, pricing) {
    var cfg = pricing.commercial;
    if (!cfg) return null;

    var type = state.propertyType || '';
    var sqft = Math.max(0, parseInt(state.sqft, 10) || 0);

    // Only standard office / retail gets an automatic number.
    var isStandard = (cfg.standard_types || []).indexOf(type) !== -1;
    if (type && !isStandard) {
      return {
        custom: true,
        reason: type + ' is a specialised property, so we price it after a ' +
          'site visit rather than from a form.',
        lines: [], low: 0, high: 0
      };
    }
    if (!sqft) {
      return { custom: true, needsSqft: true,
        reason: 'Add the approximate square footage for a starting estimate.',
        lines: [], low: 0, high: 0 };
    }

    var band = null;
    for (var i = 0; i < cfg.bands.length; i++) {
      if (sqft <= cfg.bands[i].max) { band = cfg.bands[i]; break; }
    }
    if (!band) {
      return {
        custom: true,
        reason: 'Premises ' +
          (cfg.over_band_label || 'over the largest band').toLowerCase() +
          ' are measured and quoted individually.',
        lines: [], low: 0, high: 0
      };
    }

    return {
      custom: false,
      band: band,
      startingAt: true,
      frequency: state.frequency || '',
      recurring: !!(state.frequency && state.frequency !== 'One-time'),
      lines: [{ label: band.label + ' — starting at', amount: band.price }],
      low: band.price,
      high: band.price
    };
  }

  /* ------------------------------------------------------------- combined */
  function estimateAll(state, pricing) {
    var sections = [];
    var totalLow = 0, totalHigh = 0;
    var anyCustom = false, anyPriced = false;
    var reasons = [];

    var wantsHome = !!state.package;
    var wantsComm = !!state.commercial;
    var wantsCarpetOrUph = !!state.carpetUph;

    if (wantsHome) {
      var r = residential(state.residential || {}, pricing);
      if (r) {
        sections.push({ key: 'residential', title: 'Home cleaning', result: r });
        totalLow += r.low; totalHigh += r.high;
        if (r.custom) { anyCustom = true; reasons.push(r.reason); }
        else anyPriced = true;
        if (r.addonTotal) anyPriced = true;
      }
    }

    if (wantsComm) {
      var c = commercial(state.commercialState || {}, pricing);
      if (c) {
        sections.push({ key: 'commercial', title: 'Commercial cleaning', result: c });
        totalLow += c.low; totalHigh += c.high;
        if (c.custom) { anyCustom = true; reasons.push(c.reason); }
        else anyPriced = true;
      }
    }

    if (wantsCarpetOrUph) {
      var cu = estimate(
        Object.assign({}, state.carpetState || {},
          { withOtherServices: wantsHome || wantsComm }),
        pricing);
      sections.push({ key: 'carpet', title: 'Carpet & upholstery', result: cu });
      totalLow += cu.low; totalHigh += cu.high;
      anyPriced = true;
    }

    return {
      sections: sections,
      low: totalLow,
      high: totalHigh,
      anyCustom: anyCustom,
      anyPriced: anyPriced,
      reasons: reasons
    };
  }

  function formatRange(result) {
    if (result.low === result.high) return money(result.low);
    return money(result.low) + ' – ' + money(result.high);
  }

  global.FPCarpet = {
    estimate: estimate,
    residential: residential,
    commercial: commercial,
    estimateAll: estimateAll,
    money: money,
    formatRange: formatRange
  };
})(typeof window !== 'undefined' ? window : globalThis);
