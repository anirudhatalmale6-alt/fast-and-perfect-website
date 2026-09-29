/* Verifies the calculator against the price guide the owner supplied.
   Run: node tools/test_pricing.js                                        */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const P = JSON.parse(fs.readFileSync(
  path.join(ROOT, 'site/assets/data/pricing.json'), 'utf8'));

global.window = global;
require(path.join(ROOT, 'site/assets/js/pricing-engine.js'));
const { estimate, residential, commercial, estimateAll, formatRange } = global.FPCarpet;

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log(`  PASS  ${name.padEnd(58)}${detail || ''}`); }
  else { fail++; console.log(`  FAIL  ${name.padEnd(58)}${detail || ''}`); }
}
function eq(name, got, want) {
  ok(name, got === want, got === want ? String(got) : `got ${got}, expected ${want}`);
}

/* ===================================================== CARPET & UPHOLSTERY */
const S = (o) => Object.assign(
  { rooms: 0, hallways: 0, steps: 0, items: {}, treatments: [] }, o);
function range(name, state, lo, hi) {
  const r = estimate(state, P);
  ok(name, r.low === lo && r.high === hi,
    r.low === lo && r.high === hi ? formatRange(r) : `got ${r.low}-${r.high}, expected ${lo}-${hi}`);
}

console.log('\n=== CARPET: minimum service charge ($139) ===');
range('nothing selected', S({}), 139, 139);
range('1 room ($59) -> minimum', S({ rooms: 1 }), 139, 139);
range('3 rooms = exactly the minimum', S({ rooms: 3 }), 139, 139);
range('1 chair ($39) -> minimum', S({ items: { chair: 1 } }), 139, 139);

console.log('\n=== CARPET: tiers, hallways, stairs ===');
range('4 rooms', S({ rooms: 4 }), 169, 169);
range('5 rooms', S({ rooms: 5 }), 199, 199);
range('6 rooms = 199 + 35', S({ rooms: 6 }), 234, 234);
range('8 rooms = 199 + 3x35', S({ rooms: 8 }), 304, 304);
range('5 rooms + hallway', S({ rooms: 5, hallways: 1 }), 224, 224);
range('5 rooms + 13 steps (base only)', S({ rooms: 5, steps: 13 }), 254, 254);
range('5 rooms + 16 steps = 55 + 3x4', S({ rooms: 5, steps: 16 }), 266, 266);

console.log('\n=== CARPET: upholstery, mattresses, treatments ===');
range('sofa + loveseat', S({ items: { sofa: 1, loveseat: 1 } }), 208, 208);
range('sectional (from $159)', S({ items: { sectional: 1 } }), 159, 159);
range('queen + king', S({ items: { queen: 1, king: 1 } }), 218, 218);
range('4 rooms + heavy stain', S({ rooms: 4, treatments: ['heavy_stain'] }), 189, 209);
range('4 rooms + pet odour', S({ rooms: 4, treatments: ['pet_odour'] }), 199, 229);
range('4 rooms + both treatments',
  S({ rooms: 4, treatments: ['heavy_stain', 'pet_odour'] }), 219, 269);

console.log('\n=== CARPET MINIMUM: standalone only (owner rule, 29 Sep) ===');
range('carpet alone, 1 room -> minimum applies', S({ rooms: 1 }), 139, 139);
range('carpet + upholstery alone -> minimum applies',
  S({ rooms: 1, items: { chair: 1 } }), 139, 139);
{
  // With a house clean in the same visit the minimum is waived.
  const r = estimate(S({ rooms: 1, withOtherServices: true }), P);
  eq('1 carpeted room WITH a house clean -> charged at $59, no minimum', r.low, 59);
  ok('  minimum not flagged', r.minimumApplied === false);
}
{
  const r = estimate(S({ items: { chair: 1 }, withOtherServices: true }), P);
  eq('1 chair WITH a house clean -> charged at $39', r.low, 39);
}
{
  const all = estimateAll({
    package: true,
    residential: { package: 'regular', bedrooms: 3, bathrooms: 2 },
    carpetUph: true,
    carpetState: { rooms: 1, items: {}, treatments: [] }
  }, P);
  eq('house clean + 1 carpeted room = 249 + 59 (not 249 + 139)', all.low, 308);
}

/* ============================================================ RESIDENTIAL */
console.log('\n=== RESIDENTIAL: every tier against the guide ===');
const GUIDE_RES = [
  [0, 'studio',  149, 189, 239],
  [1, '1 bed',   169, 219, 269],
  [2, '2 bed',   199, 269, 339],
  [3, '3 bed',   249, 349, 429],
  [4, '4 bed',   319, 439, 539],
  [5, '5 bed',   399, 549, 669],
  [6, '6 bed',   499, 699, 829],
];
for (const [beds, label, reg, deep, mio] of GUIDE_RES) {
  for (const [pkg, want] of [['regular', reg], ['deep', deep], ['moveinout', mio]]) {
    const r = residential({ package: pkg, bedrooms: beds, bathrooms: 1 }, P);
    eq(`${label} ${pkg}`, r.custom ? 'CUSTOM' : r.base, want);
  }
}

console.log('\n=== RESIDENTIAL: outside the rules -> Custom Quote ===');
ok('7 bedrooms -> custom', residential({ package: 'regular', bedrooms: 7, bathrooms: 2 }, P).custom);
ok('3 bed / 4 bath (cap is 2) -> custom',
  residential({ package: 'regular', bedrooms: 3, bathrooms: 4 }, P).custom);
ok('3 bed / 2 bath (at the cap) -> priced',
  !residential({ package: 'regular', bedrooms: 3, bathrooms: 2 }, P).custom);
ok('5 bed / 5 bath (3+ allowed) -> priced',
  !residential({ package: 'regular', bedrooms: 5, bathrooms: 5 }, P).custom);

console.log('\n=== RESIDENTIAL: add-ons ===');
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    addons: { fridge: true, oven: true } }, P);
  eq('3 bed regular + fridge + oven = 249 + 59 + 59', r.low, 367);
}
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    addons: { laundry: 3 } }, P);
  eq('laundry x3 = 249 + 90', r.low, 339);
}

console.log('\n=== PACKAGE INCLUSIONS (owner rules, 29 Sep) ===');
{
  // Fridge, oven and interior windows are PAID on every package.
  const r = residential({ package: 'deep', bedrooms: 3, bathrooms: 2,
    addons: { fridge: true, oven: true } }, P);
  eq('deep + fridge + oven = 349 + 59 + 59 (both charged)', r.low, 467);
  eq('  nothing marked included', r.lines.filter((l) => l.included).length, 0);
}
{
  const r = residential({ package: 'moveinout', bedrooms: 3, bathrooms: 2,
    addons: { windows: true } }, P);
  eq('move-out + interior windows = 429 + 60 (charged)', r.low, 489);
}
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    addons: { fridge: true } }, P);
  eq('regular + fridge = 249 + 59', r.low, 308);
}
{
  // Only move-in/out covers inside cabinets (it cleans empty cabinets/drawers).
  const r = residential({ package: 'moveinout', bedrooms: 3, bathrooms: 2,
    addons: { cabinets: true } }, P);
  eq('move-out + inside cabinets stays at 429 (included)', r.low, 429);
  eq('  marked included', r.lines.filter((l) => l.included).length, 1);
}
{
  const r = residential({ package: 'deep', bedrooms: 3, bathrooms: 2,
    addons: { cabinets: true } }, P);
  eq('deep + inside cabinets = 349 + 75 (NOT included)', r.low, 424);
}
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    addons: { cabinets: true } }, P);
  eq('regular + inside cabinets = 249 + 75', r.low, 324);
}
ok('fridge is never auto-included on any package',
  Object.values(P.residential.included_in).every((v) => v.indexOf('fridge') === -1));
ok('oven is never auto-included on any package',
  Object.values(P.residential.included_in).every((v) => v.indexOf('oven') === -1));
ok('interior windows are never auto-included on any package',
  Object.values(P.residential.included_in).every((v) => v.indexOf('windows') === -1));

console.log('\n=== RESIDENTIAL: recurring discount, base only ===');
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    recurring: 'weekly' }, P);
  eq('3 bed weekly: first clean full price', r.firstTotal, 249);
  eq('3 bed weekly: after = 249 - 20%', r.afterTotal, 199);
}
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    recurring: 'biweekly' }, P);
  eq('3 bed bi-weekly after = 249 - 15%', r.afterTotal, 212);
}
{
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    recurring: 'monthly' }, P);
  eq('3 bed monthly after = 249 - 10%', r.afterTotal, 224);
}
{
  // discount must NOT touch the add-on
  const r = residential({ package: 'regular', bedrooms: 3, bathrooms: 2,
    recurring: 'weekly', addons: { oven: true } }, P);
  eq('weekly + $59 oven: first = 249 + 59', r.firstTotal, 308);
  eq('weekly + $59 oven: after = (249 x 0.8) + 59  [add-on undiscounted]',
    r.afterTotal, 258);
}

/* ============================================================= COMMERCIAL */
console.log('\n=== COMMERCIAL: square-footage bands ===');
const GUIDE_COMM = [
  [800, 149], [1000, 149], [1001, 199], [1500, 199],
  [1501, 249], [2500, 249], [2501, 349], [3500, 349],
  [3501, 449], [5000, 449],
];
for (const [sqft, want] of GUIDE_COMM) {
  const r = commercial({ propertyType: 'Office', sqft: sqft }, P);
  eq(`${sqft} sq ft office`, r.custom ? 'CUSTOM' : r.low, want);
}
ok('5001 sq ft -> custom quote',
  commercial({ propertyType: 'Office', sqft: 5001 }, P).custom);
ok('retail store is priced automatically',
  !commercial({ propertyType: 'Retail store', sqft: 1200 }, P).custom);

console.log('\n=== COMMERCIAL: specialised property types -> Custom Quote ===');
for (const t of P.commercial.custom_types) {
  ok(`${t} -> custom`, commercial({ propertyType: t, sqft: 1200 }, P).custom);
}
ok('no square footage yet -> custom + prompt',
  commercial({ propertyType: 'Office', sqft: 0 }, P).needsSqft === true);

console.log('\n=== COMMERCIAL: recurring is captured, never auto-discounted ===');
{
  const one = commercial({ propertyType: 'Office', sqft: 1200, frequency: 'One-time' }, P);
  const wk = commercial({ propertyType: 'Office', sqft: 1200, frequency: 'Weekly' }, P);
  eq('weekly costs the same per visit as one-time (no auto discount)',
    wk.low, one.low);
  ok('weekly is flagged as a recurring enquiry', wk.recurring === true);
}

/* =============================================================== COMBINED */
console.log('\n=== COMBINED quotes ===');
{
  const r = estimateAll({
    package: true,
    residential: { package: 'regular', bedrooms: 3, bathrooms: 2 },
    carpetUph: true,
    carpetState: { rooms: 4, items: {}, treatments: [] }
  }, P);
  eq('3 bed regular ($249) + 4 carpeted rooms ($169)', r.low, 418);
  ok('  both sections present', r.sections.length === 2);
}
{
  const r = estimateAll({
    carpetUph: true,
    carpetState: { rooms: 4, items: { sofa: 1 }, treatments: ['pet_odour'] }
  }, P);
  ok('carpet + upholstery + treatment is one range',
    r.low === 318 && r.high === 348, `${r.low}-${r.high}`);
}
{
  const r = estimateAll({
    package: true,
    residential: { package: 'regular', bedrooms: 9, bathrooms: 4 },
    carpetUph: true,
    carpetState: { rooms: 4, items: {}, treatments: [] }
  }, P);
  ok('oversized home + carpet: custom flagged, carpet still priced',
    r.anyCustom && r.low === 169, `custom=${r.anyCustom} low=${r.low}`);
}

/* ====================================================== GUIDE CROSS-CHECK */
console.log('\n=== Every published number cross-checked against the guide ===');
const checks = [
  ['minimum service charge', P.minimum_service_charge, 139],
  ['max room sq ft', P.max_room_sqft, 250],
  ['carpet 1 room', P.carpet.room_tiers[0], 59],
  ['carpet 2 rooms', P.carpet.room_tiers[1], 99],
  ['carpet 3 rooms', P.carpet.room_tiers[2], 139],
  ['carpet 4 rooms', P.carpet.room_tiers[3], 169],
  ['carpet 5 rooms', P.carpet.room_tiers[4], 199],
  ['additional room', P.carpet.additional_room, 35],
  ['hallway', P.carpet.hallway, 25],
  ['stairs base', P.carpet.stairs_base, 55],
  ['stairs included steps', P.carpet.stairs_included_steps, 13],
  ['additional step', P.carpet.additional_step, 4],
];
const byKey = Object.fromEntries(P.items.map((i) => [i.key, i.price]));
[['chair', 39], ['recliner', 69], ['loveseat', 89], ['sofa', 119],
 ['sectional', 159], ['ottoman', 35], ['twin', 69], ['queen', 99], ['king', 119]]
  .forEach(([k, v]) => checks.push([`item ${k}`, byKey[k], v]));
const addon = Object.fromEntries(P.residential.addons.map((a) => [a.key, a.price]));
[['fridge', 59], ['oven', 59], ['cabinets', 75], ['windows', 60],
 ['laundry', 30], ['garage', 30], ['basement_fin', 65], ['basement_unfin', 25],
 ['pet_hair', 20], ['wall_washing', 120]]
  .forEach(([k, v]) => checks.push([`add-on ${k}`, addon[k], v]));
const disc = Object.fromEntries(P.residential.recurring.map((r) => [r.key, r.discount]));
[['weekly', 20], ['biweekly', 15], ['monthly', 10], ['onetime', 0]]
  .forEach(([k, v]) => checks.push([`discount ${k}`, disc[k], v]));
P.commercial.bands.forEach((b, i) => {
  checks.push([`commercial band ${b.label}`, b.price, [149, 199, 249, 349, 449][i]]);
});
const tre = Object.fromEntries(P.treatments.map((t) => [t.key, [t.min, t.max]]));
checks.push(['heavy stain min', tre.heavy_stain[0], 20]);
checks.push(['heavy stain max', tre.heavy_stain[1], 40]);
checks.push(['pet odour min', tre.pet_odour[0], 30]);
checks.push(['pet odour max', tre.pet_odour[1], 60]);

let silent = 0;
for (const [name, got, want] of checks) {
  if (got === want) { pass++; silent++; }
  else { fail++; console.log(`  FAIL  ${name}: config has ${got}, guide says ${want}`); }
}
console.log(`  ${silent}/${checks.length} published prices match the guide`);

console.log(`\n${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
