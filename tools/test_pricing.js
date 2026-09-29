/* Verifies the calculator against the price guide the owner supplied.
   Run: node tools/test_pricing.js                                        */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const P = JSON.parse(fs.readFileSync(
  path.join(ROOT, 'site/assets/data/pricing.json'), 'utf8'));

// load the calculator the same way a browser would
global.window = global;
require(path.join(ROOT, 'site/assets/js/carpet-calculator.js'));
const { estimate, formatRange } = global.FPCarpet;

let pass = 0, fail = 0;
function check(name, state, expectLow, expectHigh) {
  const r = estimate(state, P);
  const ok = r.low === expectLow && r.high === expectHigh;
  if (ok) { pass++; console.log(`  PASS  ${name.padEnd(52)} ${formatRange(r)}`); }
  else {
    fail++;
    console.log(`  FAIL  ${name.padEnd(52)} got ${r.low}-${r.high}, expected ${expectLow}-${expectHigh}`);
  }
}
const S = (o) => Object.assign(
  { rooms: 0, hallways: 0, steps: 0, items: {}, treatments: [] }, o);

console.log('\n--- Minimum service charge ($139 on every appointment) ---');
check('nothing selected', S({}), 139, 139);
check('1 chair ($39) -> minimum applies', S({ items: { chair: 1 } }), 139, 139);
check('1 room ($59) -> minimum applies', S({ rooms: 1 }), 139, 139);
check('2 rooms ($99) -> minimum applies', S({ rooms: 2 }), 139, 139);
check('3 rooms ($139) -> exactly the minimum', S({ rooms: 3 }), 139, 139);

console.log('\n--- Carpeted rooms (tiered, per the guide) ---');
check('4 rooms', S({ rooms: 4 }), 169, 169);
check('5 rooms', S({ rooms: 5 }), 199, 199);
check('6 rooms = 199 + 35', S({ rooms: 6 }), 234, 234);
check('8 rooms = 199 + 3x35', S({ rooms: 8 }), 304, 304);

console.log('\n--- Hallways and stairs ---');
check('5 rooms + hallway', S({ rooms: 5, hallways: 1 }), 224, 224);
check('5 rooms + 2 hallways', S({ rooms: 5, hallways: 2 }), 249, 249);
check('5 rooms + 13 steps (base only)', S({ rooms: 5, steps: 13 }), 254, 254);
check('5 rooms + 10 steps (still base)', S({ rooms: 5, steps: 10 }), 254, 254);
check('5 rooms + 16 steps = 55 + 3x4', S({ rooms: 5, steps: 16 }), 266, 266);

console.log('\n--- Upholstery and mattresses ---');
check('sofa + loveseat = 119 + 89', S({ items: { sofa: 1, loveseat: 1 } }), 208, 208);
check('2 recliners = 138 -> minimum applies', S({ items: { recliner: 2 } }), 139, 139);
check('sectional (from $159)', S({ items: { sectional: 1 } }), 159, 159);
check('queen + king = 99 + 119', S({ items: { queen: 1, king: 1 } }), 218, 218);
check('3 chairs + ottoman = 117 + 35', S({ items: { chair: 3, ottoman: 1 } }), 152, 152);

console.log('\n--- Treatments produce a range ---');
check('4 rooms + heavy stain', S({ rooms: 4, treatments: ['heavy_stain'] }), 189, 209);
check('4 rooms + pet odour', S({ rooms: 4, treatments: ['pet_odour'] }), 199, 229);
check('4 rooms + both', S({ rooms: 4, treatments: ['heavy_stain', 'pet_odour'] }), 219, 269);
check('1 chair + both -> low hits minimum',
  S({ items: { chair: 1 }, treatments: ['heavy_stain', 'pet_odour'] }), 139, 139);

console.log('\n--- A realistic whole-house job ---');
check('5 rooms + hall + 14 steps + sofa + 2 chairs + queen + pet odour',
  S({ rooms: 5, hallways: 1, steps: 14, items: { sofa: 1, chair: 2, queen: 1 },
      treatments: ['pet_odour'] }),
  // 199 + 25 + (55+4) + 119 + 78 + 99 = 579 ; +30 / +60
  609, 639);

console.log('\n--- Every guide price appears in the config ---');
const guide = {
  'minimum service charge': [P.minimum_service_charge, 139],
  '1 room': [P.carpet.room_tiers[0], 59],
  '2 rooms': [P.carpet.room_tiers[1], 99],
  '3 rooms': [P.carpet.room_tiers[2], 139],
  '4 rooms': [P.carpet.room_tiers[3], 169],
  '5 rooms': [P.carpet.room_tiers[4], 199],
  'additional room': [P.carpet.additional_room, 35],
  hallway: [P.carpet.hallway, 25],
  stairs: [P.carpet.stairs_base, 55],
  'stairs included steps': [P.carpet.stairs_included_steps, 13],
  'additional step': [P.carpet.additional_step, 4],
};
const byKey = Object.fromEntries(P.items.map((i) => [i.key, i.price]));
Object.assign(guide, {
  chair: [byKey.chair, 39], recliner: [byKey.recliner, 69],
  loveseat: [byKey.loveseat, 89], sofa: [byKey.sofa, 119],
  sectional: [byKey.sectional, 159], ottoman: [byKey.ottoman, 35],
  twin: [byKey.twin, 69], queen: [byKey.queen, 99], king: [byKey.king, 119],
});
const tre = Object.fromEntries(P.treatments.map((t) => [t.key, [t.min, t.max]]));
for (const [name, [got, want]] of Object.entries(guide)) {
  if (got === want) { pass++; }
  else { fail++; console.log(`  FAIL  ${name}: config has ${got}, guide says ${want}`); }
}
const treChecks = [['heavy_stain', 20, 40], ['pet_odour', 30, 60]];
for (const [k, lo, hi] of treChecks) {
  if (tre[k][0] === lo && tre[k][1] === hi) pass++;
  else { fail++; console.log(`  FAIL  ${k}: config ${tre[k]}, guide ${lo}-${hi}`); }
}
console.log(`  ${treChecks.length + Object.keys(guide).length} guide prices cross-checked`);

console.log(`\n${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
