/* Tests for the /api/enquiry Pages Function.
   Runs the real handler with a stubbed global fetch, so provider failures,
   honeypots and the "never confirm an unconfirmed send" rule are all
   exercised without touching the network.

   node tools/test_enquiry.mjs
*/
import { onRequestPost, onRequestGet } from '../functions/api/enquiry.js';

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; }
  else { fail++; console.log('  FAIL:', name, extra === undefined ? '' : extra); }
}

const URL_ = 'https://fastandperfect.ca/api/enquiry';

function req(fields, { json = true } = {}) {
  const fd = new FormData();
  Object.entries(fields).forEach(([k, v]) => fd.append(k, v));
  return new Request(URL_, {
    method: 'POST',
    body: fd,
    headers: json ? { Accept: 'application/json' } : { Accept: 'text/html' }
  });
}

const GOOD = { name: 'John Lambert', phone: '5873380069', email: 'j@example.com',
               area: 'Mill Woods', message: 'Need a deep clean' };

/* Stub global fetch. `impl` sees (url, init) and returns a Response. */
let calls = [];
function stub(impl) {
  calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return impl(String(url), init);
  };
}
const jsonRes = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json' } });

console.log('\n/api/enquiry');

/* ---- 1. happy path, Web3Forms --------------------------------------- */
stub(() => jsonRes({ success: true }));
let r = await onRequestPost({ request: req(GOOD), env: { WEB3FORMS_KEY: 'k' } });
let b = await r.json();
ok('web3forms success -> 200 ok:true', r.status === 200 && b.ok === true, b);
ok('web3forms was the provider called', calls[0].url.includes('web3forms.com'), calls[0] && calls[0].url);
let sent = JSON.parse(calls[0].init.body);
ok('payload carries the access key', sent.access_key === 'k');
ok('payload carries the labelled fields', sent.Name === 'John Lambert' && sent.Phone === '5873380069', sent);
ok('reply-to is the customer', sent.replyto === 'j@example.com');
ok('honeypots are not forwarded', !('_gotcha' in sent) && !('_honey' in sent));

/* ---- 2. provider fails -> honest failure, never a false success ------ */
stub(() => jsonRes({ success: false, message: 'nope' }, 200));
r = await onRequestPost({ request: req(GOOD), env: { WEB3FORMS_KEY: 'k' } });
b = await r.json();
ok('provider 200 + success:false -> NOT reported as sent', b.ok === false, b);
ok('failure is a 5xx, not a 200', r.status >= 500);
ok('failure message points at the fallback', /email this to us instead/i.test(b.message), b.message);

stub(() => new Response('<html>500</html>', { status: 500 }));
r = await onRequestPost({ request: req(GOOD), env: { WEB3FORMS_KEY: 'k' } });
ok('provider HTTP 500 -> not reported as sent', (await r.json()).ok === false);

stub(() => { throw new Error('network down'); });
r = await onRequestPost({ request: req(GOOD), env: { WEB3FORMS_KEY: 'k' } });
ok('provider throwing -> handled, not a crash', (await r.json()).ok === false);

/* ---- 3. the FormSubmit trap that caused the original bug ------------- */
stub(() => jsonRes({ success: 'false', message: 'not activated' }, 200));
r = await onRequestPost({ request: req(GOOD), env: {} });
ok('formsubmit 200 + success:"false" -> NOT a delivery', (await r.json()).ok === false);
ok('formsubmit is only the fallback', calls[0].url.includes('formsubmit.co'));

stub(() => jsonRes({ success: 'true', message: 'sent' }, 200));
r = await onRequestPost({ request: req(GOOD), env: {} });
ok('formsubmit success:"true" -> delivered', (await r.json()).ok === true);

/* ---- 4. provider precedence ------------------------------------------ */
stub(() => jsonRes({ success: true }));
await onRequestPost({ request: req(GOOD), env: { WEB3FORMS_KEY: 'k', BREVO_API_KEY: 'b' } });
ok('web3forms wins over brevo', calls[0].url.includes('web3forms'));
stub(() => new Response('', { status: 201 }));
await onRequestPost({ request: req(GOOD), env: { BREVO_API_KEY: 'b' } });
ok('brevo used when it is the only key', calls[0].url.includes('brevo'));
ok('brevo gets its api-key header', calls[0].init.headers['api-key'] === 'b');
stub(() => new Response('{}', { status: 200 }));
await onRequestPost({ request: req(GOOD), env: { RESEND_API_KEY: 'r' } });
ok('resend used when it is the only key', calls[0].url.includes('resend'));

/* ---- 5. honeypots ---------------------------------------------------- */
stub(() => jsonRes({ success: true }));
r = await onRequestPost({ request: req({ ...GOOD, _gotcha: 'spam' }), env: { WEB3FORMS_KEY: 'k' } });
ok('honeypot _gotcha -> nothing sent', calls.length === 0);
ok('honeypot still answers normally (bots learn nothing)', (await r.json()).ok === true);
r = await onRequestPost({ request: req({ ...GOOD, _honey: 'spam' }), env: { WEB3FORMS_KEY: 'k' } });
ok('honeypot _honey -> nothing sent', calls.length === 0);

/* ---- 6. validation --------------------------------------------------- */
stub(() => jsonRes({ success: true }));
r = await onRequestPost({ request: req({ message: 'hi' }), env: { WEB3FORMS_KEY: 'k' } });
ok('no name -> rejected, nothing sent', (await r.json()).ok === false && calls.length === 0);
r = await onRequestPost({ request: req({ name: 'A' }), env: { WEB3FORMS_KEY: 'k' } });
ok('no phone and no email -> rejected', (await r.json()).ok === false && calls.length === 0);
r = await onRequestPost({ request: req({ name: 'A', phone: '5873380069' }), env: { WEB3FORMS_KEY: 'k' } });
ok('phone only -> accepted', (await r.json()).ok === true);
r = await onRequestPost({ request: req({ name: 'A', email: 'a@b.ca' }), env: { WEB3FORMS_KEY: 'k' } });
ok('email only -> accepted', (await r.json()).ok === true);

/* ---- 7. no-JS path redirects instead of returning JSON --------------- */
stub(() => jsonRes({ success: true }));
r = await onRequestPost({ request: req(GOOD, { json: false }), env: { WEB3FORMS_KEY: 'k' } });
ok('no-JS success -> redirect to thank-you',
   r.status === 303 && r.headers.get('location') === 'https://fastandperfect.ca/thank-you.html',
   r.status + ' ' + r.headers.get('location'));
stub(() => jsonRes({ success: false }, 500));
r = await onRequestPost({ request: req(GOOD, { json: false }), env: { WEB3FORMS_KEY: 'k' } });
ok('no-JS failure -> redirect back, flagged, NOT to thank-you',
   r.status === 303 && /send=failed/.test(r.headers.get('location')),
   r.headers.get('location'));

/* ---- 8. field coverage ----------------------------------------------- */
stub(() => jsonRes({ success: true }));
await onRequestPost({
  request: req({ ...GOOD, detail: 'Carpet: 3 rooms', estimate: '$199', newfield: 'kept' }),
  env: { WEB3FORMS_KEY: 'k' }
});
sent = JSON.parse(calls[0].init.body);
ok('known fields get readable labels', sent['Selection detail'] === 'Carpet: 3 rooms');
ok('an unlisted field is still forwarded, never dropped', sent.newfield === 'kept', sent);

/* ---- 9. GET is not a submission -------------------------------------- */
r = await onRequestGet();
ok('GET -> 405', r.status === 405);

console.log(`\n${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
