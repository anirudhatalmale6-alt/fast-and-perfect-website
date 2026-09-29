/* ==========================================================================
   Price editor — Fast and Perfect Ltd.

   Loads assets/data/pricing.json, renders every price as an editable field,
   previews the result live, and hands back an updated pricing.json to upload.

   Nothing is saved to a server (this is a static site) — the workflow is:
   edit here -> Download pricing.json -> upload it over the old one.
   ========================================================================== */
(function () {
  'use strict';

  var root = document.getElementById('price-editor');
  if (!root) return;

  var DATA = null;
  var ORIGINAL = null;

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) {
    return Array.prototype.slice.call((c || document).querySelectorAll(s));
  };

  function money(n) { return '$' + Math.round(n).toLocaleString('en-CA'); }

  /* ------------------------------------------------------------- fields */
  function numField(label, value, path, hint, step) {
    return '<div class="field">' +
      '<label>' + label + '</label>' +
      '<input type="number" min="0" step="' + (step || 1) + '" value="' + value +
      '" data-path="' + path + '">' +
      (hint ? '<span class="field-hint">' + hint + '</span>' : '') +
      '</div>';
  }

  function textField(label, value, path, hint) {
    return '<div class="field field--full">' +
      '<label>' + label + '</label>' +
      '<textarea data-path="' + path + '" rows="3">' + value + '</textarea>' +
      (hint ? '<span class="field-hint">' + hint + '</span>' : '') +
      '</div>';
  }

  function section(title, inner, note) {
    return '<section class="admin-block">' +
      '<h2 class="h-sm">' + title + '</h2>' +
      (note ? '<p class="field-hint mt-1">' + note + '</p>' : '') +
      '<div class="field-grid mt-2">' + inner + '</div></section>';
  }

  function render() {
    var p = DATA;
    var html = '';

    // ---- residential -------------------------------------------------
    var resTiers = p.residential.tiers.map(function (t, i) {
      return numField(t.label + ' — regular ($)', t.regular, 'residential.tiers.' + i + '.regular') +
        numField(t.label + ' — deep ($)', t.deep, 'residential.tiers.' + i + '.deep') +
        numField(t.label + ' — move in/out ($)', t.moveinout, 'residential.tiers.' + i + '.moveinout') +
        numField(t.label + ' — max bathrooms', t.max_bathrooms, 'residential.tiers.' + i + '.max_bathrooms',
          'Above this, the customer sees Custom Quote.');
    }).join('');
    html += section('Residential packages', resTiers,
      'Three prices per home size. Anything outside these tiers shows as a ' +
      'Custom Quote rather than guessing.');

    var resAddons = p.residential.addons.map(function (a, i) {
      return numField(a.label + ' ($)', a.price, 'residential.addons.' + i + '.price',
        a.qty ? 'Charged per unit.' : (a.from ? 'Shown as \u201cfrom\u201d.' : ''));
    }).join('');
    html += section('Residential add-ons', resAddons);

    var resRec = p.residential.recurring.map(function (r, i) {
      if (!r.discount && r.key === 'onetime') return '';
      return numField(r.label + ' — discount (%)', r.discount,
        'residential.recurring.' + i + '.discount');
    }).join('');
    html += section('Recurring discounts', resRec,
      'Applied to the cleaning package only, from the second visit onwards. ' +
      'Never applied to add-ons, carpet, upholstery or commercial.');

    // ---- commercial ----------------------------------------------------
    var commBands = p.commercial.bands.map(function (b, i) {
      return numField(b.label + ' ($)', b.price, 'commercial.bands.' + i + '.price');
    }).join('');
    html += section('Commercial — starting price per visit', commBands,
      'Standard offices and retail only. Every other property type, and ' +
      'anything over the top band, shows as a Custom Quote.');

    html += section('Minimum &amp; room size',
      numField('Minimum appointment total ($)', p.minimum_service_charge,
        'minimum_service_charge',
        'A floor for standalone bookings, never an added fee. Does not apply ' +
        'when a cleaning package is booked.') +
      numField('Maximum room size (sq ft)', p.max_room_sqft, 'max_room_sqft',
        'Anything larger is quoted separately.', 10));

    var tiers = p.carpet.room_tiers.map(function (v, i) {
      return numField((i + 1) + ' carpeted room' + (i ? 's' : '') + ' ($)', v,
        'carpet.room_tiers.' + i);
    }).join('');
    html += section('Carpet cleaning',
      tiers +
      numField('Each additional room ($)', p.carpet.additional_room,
        'carpet.additional_room') +
      numField('Hallway ($)', p.carpet.hallway, 'carpet.hallway') +
      numField('Stairs — per individual step ($)', p.carpet.per_step,
        'carpet.per_step', 'Charged as price x number of steps.'));

    ['Upholstery', 'Mattresses'].forEach(function (group) {
      var inner = p.items.map(function (item, i) {
        if (item.group !== group) return '';
        return numField(item.label + ' ($)', item.price, 'items.' + i + '.price',
          item.from ? 'Shown as “from”.' : '');
      }).join('');
      html += section(group, inner);
    });

    var tre = p.treatments.map(function (t, i) {
      return numField(t.label + ' — from ($)', t.min, 'treatments.' + i + '.min') +
        numField(t.label + ' — to ($)', t.max, 'treatments.' + i + '.max');
    }).join('');
    html += section('Additional treatments', tre,
      'These are quoted as a range, so the customer sees an estimate range.');

    html += section('Wording',
      textField('Room-size note', p.max_room_note, 'max_room_note') +
      textField('Estimate disclaimer', p.disclaimer, 'disclaimer'));

    $('#editor-fields', root).innerHTML = html;
    preview();
  }

  /* --------------------------------------------------------- read/write */
  function setPath(obj, path, value) {
    var parts = path.split('.');
    var cur = obj;
    for (var i = 0; i < parts.length - 1; i++) {
      var k = parts[i];
      cur = cur[/^\d+$/.test(k) ? Number(k) : k];
    }
    var last = parts[parts.length - 1];
    cur[/^\d+$/.test(last) ? Number(last) : last] = value;
  }

  root.addEventListener('input', function (e) {
    var el = e.target;
    var path = el.getAttribute('data-path');
    if (!path) return;
    var val = el.type === 'number' ? parseFloat(el.value) : el.value;
    if (el.type === 'number' && (isNaN(val) || val < 0)) return;
    setPath(DATA, path, val);
    preview();
    markDirty();
  });

  function markDirty() {
    var changed = JSON.stringify(DATA) !== JSON.stringify(ORIGINAL);
    $('#editor-status', root).textContent = changed
      ? 'Unsaved changes — download the file and upload it to publish them.'
      : 'No changes yet.';
    $('#editor-status', root).className =
      'form-status ' + (changed ? 'is-ok' : '');
    $('#editor-status', root).style.display = 'block';
  }

  /* ------------------------------------------------------------ preview */
  var RES_SAMPLES = [
    { title: '3 bed / 2 bath — regular', state: { package: 'regular', bedrooms: 3, bathrooms: 2 } },
    { title: '3 bed / 2 bath — deep', state: { package: 'deep', bedrooms: 3, bathrooms: 2 } },
    { title: '3 bed / 2 bath — move out', state: { package: 'moveinout', bedrooms: 3, bathrooms: 2 } },
    { title: '3 bed weekly (2nd visit on)', state: { package: 'regular', bedrooms: 3, bathrooms: 2, recurring: 'weekly' }, showAfter: true },
    { title: '3 bed / 5 bath (over the cap)', state: { package: 'regular', bedrooms: 3, bathrooms: 5 } }
  ];

  var COMM_SAMPLES = [
    { title: 'Office, 900 sq ft', state: { propertyType: 'Office', sqft: 900 } },
    { title: 'Office, 2,000 sq ft', state: { propertyType: 'Office', sqft: 2000 } },
    { title: 'Office, 4,000 sq ft', state: { propertyType: 'Office', sqft: 4000 } },
    { title: 'Clinic, 2,000 sq ft', state: { propertyType: 'Medical or dental clinic', sqft: 2000 } }
  ];

  var SAMPLES = [
    { title: 'Nothing selected', state: {} },
    { title: '1 carpeted room only', state: { rooms: 1 } },
    { title: '3 rooms + hallway + stairs (13 steps)',
      state: { rooms: 3, hallways: 1, steps: 13 } },
    { title: '5 rooms + 3-seat sofa + pet odour',
      state: { rooms: 5, items: { sofa: 1 }, treatments: ['pet_odour'] } },
    { title: 'Sofa + loveseat + queen mattress',
      state: { items: { sofa: 1, loveseat: 1, queen: 1 } } }
  ];

  function preview() {
    if (!window.FPCarpet) return;
    var CUSTOM = DATA.custom_quote_label || 'Custom Quote';
    var rows = [];

    rows.push('<tr><td colspan="2"><b>Residential</b></td></tr>');
    RES_SAMPLES.forEach(function (s) {
      var r = window.FPCarpet.residential(s.state, DATA);
      var val = r.custom ? CUSTOM
        : (s.showAfter
          ? window.FPCarpet.money(r.firstTotal) + ' then ' + window.FPCarpet.money(r.afterTotal)
          : window.FPCarpet.money(r.low));
      rows.push('<tr><td>' + s.title + '</td><td>' + val + '</td></tr>');
    });

    rows.push('<tr><td colspan="2"><b>Commercial</b></td></tr>');
    COMM_SAMPLES.forEach(function (s) {
      var r = window.FPCarpet.commercial(s.state, DATA);
      rows.push('<tr><td>' + s.title + '</td><td>' +
        (r.custom ? CUSTOM : 'from ' + window.FPCarpet.money(r.low)) + '</td></tr>');
    });

    rows.push('<tr><td colspan="2"><b>Carpet &amp; upholstery</b></td></tr>');
    SAMPLES.forEach(function (s) {
      var state = Object.assign(
        { rooms: 0, hallways: 0, steps: 0, items: {}, treatments: [] }, s.state);
      var r = window.FPCarpet.estimate(state, DATA);
      rows.push('<tr><td>' + s.title + '</td><td>' +
        window.FPCarpet.formatRange(r) +
        (r.minimumApplied ? ' <span class="field-hint">(minimum)</span>' : '') +
        '</td></tr>');
    });

    $('#preview-body', root).innerHTML = rows.join('');
  }

  /* ------------------------------------------------------------ actions */
  function cleanForExport(d) {
    // keep the README block at the top of the exported file
    return JSON.stringify(d, null, 2) + '\n';
  }

  function wireActions() {
    $('#btn-download', root).addEventListener('click', function () {
      var blob = new Blob([cleanForExport(DATA)], { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'pricing.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
    });

    $('#btn-copy', root).addEventListener('click', function () {
      var text = cleanForExport(DATA);
      var done = function (ok) {
        var b = $('#btn-copy', root);
        var orig = b.textContent;
        b.textContent = ok ? 'Copied' : 'Copy failed';
        setTimeout(function () { b.textContent = orig; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); },
          function () { done(false); });
      } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
        document.body.removeChild(ta);
        done(ok);
      }
    });

    $('#btn-reset', root).addEventListener('click', function () {
      DATA = JSON.parse(JSON.stringify(ORIGINAL));
      render();
      markDirty();
    });
  }

  /* --------------------------------------------------------------- init */
  fetch('assets/data/pricing.json', { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (data) {
      DATA = data;
      ORIGINAL = JSON.parse(JSON.stringify(data));
      render();
      wireActions();
    })
    .catch(function (err) {
      $('#editor-fields', root).innerHTML =
        '<div class="form-status is-err" style="display:block">Could not load ' +
        'assets/data/pricing.json (' + err.message + '). This page needs to be ' +
        'opened over http:// or https:// — not by double-clicking the file.</div>';
    });
})();
