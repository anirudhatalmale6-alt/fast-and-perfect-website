/* ==========================================================================
   /api/enquiry — the site's own form endpoint (Cloudflare Pages Function)

   WHY THIS EXISTS
   ---------------
   The forms used to post straight to a third-party form service. Two
   separate things went wrong with that, and both were invisible to us:

     1. Posting by fetch() is an XHR, so CORS applies. The service sits
        behind bot protection that answers without an
        Access-Control-Allow-Origin header, so the browser refused to read
        the reply and every send failed.
     2. Posting natively fixed the CORS problem, but then the service
        itself started returning HTTP 500 from its own servers — so the
        customer was navigated away from fastandperfect.ca and dumped on a
        stranger's blue error page.

   Neither is acceptable on a page that asks a customer for their phone
   number. So the form now posts here instead: same origin, same domain,
   our own code.

   That buys three things that matter:
     - No CORS, ever. Same origin.
     - The customer never leaves fastandperfect.ca, and never sees a third
       party's error page. If delivery fails they get OUR message and the
       "email this to us instead" button.
     - We only ever tell a customer their request was received when the
       mail provider actually confirmed it. A failure is reported as a
       failure.

   CONFIGURING DELIVERY
   --------------------
   Set ONE of these in the Cloudflare dashboard:
     Workers & Pages -> fast-and-perfect-website -> Settings ->
     Environment variables -> Production (and Preview) -> Add

     WEB3FORMS_KEY   free key from web3forms.com, no card, no subscription
     BREVO_API_KEY   free Brevo account, 300 emails/day
     RESEND_API_KEY  free Resend account (needs domain verification)

   With none of them set it falls back to FormSubmit, which needs no
   account but is the service that was failing — hence the fallback rather
   than the default.

   TO_EMAIL overrides where enquiries are delivered. Defaults to
   info@fastandperfect.ca.
   ========================================================================== */

const DEFAULT_TO = 'info@fastandperfect.ca';
const SITE = 'https://fastandperfect.ca';

/* Field order for the email body. Anything not listed still gets included,
   after these, so adding a field to a form can never silently drop it. */
const FIELD_ORDER = [
  'name', 'phone', 'email', 'address', 'city', 'area',
  'service_interest', 'timing', 'service', 'services',
  'package', 'bedrooms', 'bathrooms', 'sqft', 'frequency', 'property_type',
  'date', 'window', 'quote_details', 'detail', 'estimate', 'message', 'consent'
];

const LABELS = {
  name: 'Name', phone: 'Phone', email: 'Email', address: 'Address',
  area: 'Service area', city: 'City', service: 'Service', services: 'Services',
  package: 'Package', bedrooms: 'Bedrooms', bathrooms: 'Bathrooms',
  sqft: 'Square footage', frequency: 'Frequency',
  property_type: 'Property type', date: 'Preferred date',
  window: 'Arrival window', detail: 'Selection detail',
  // These three are what the live contact and quote forms actually post.
  // Without labels they arrive in the email under their raw field names,
  // which is readable but ugly. Checked against the rendered form, not
  // against what the form was assumed to send.
  service_interest: 'Service needed', timing: 'Preferred timing',
  quote_details: 'Quote selection',
  estimate: 'On-site estimate shown', message: 'Message',
  consent: 'Consented to be contacted'
};

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

/* Collect the real fields, dropping our own control fields (_next, _subject,
   the honeypots) and anything empty. */
function collect(fd) {
  const out = [];
  const seen = new Set();
  const push = (k) => {
    if (seen.has(k) || k.startsWith('_')) return;
    const vals = fd.getAll(k).map(v => String(v).trim()).filter(Boolean);
    if (!vals.length) return;
    seen.add(k);
    out.push([LABELS[k] || k, vals.join(', ')]);
  };
  FIELD_ORDER.forEach(push);
  for (const k of fd.keys()) push(k);
  return out;
}

function textBody(rows) {
  return rows.map(([k, v]) => `${k}: ${v}`).join('\n');
}

function htmlBody(rows, subject) {
  const trs = rows.map(([k, v]) =>
    `<tr><th align="left" style="padding:6px 14px 6px 0;vertical-align:top;` +
    `white-space:nowrap;color:#64758a;font-weight:600">${esc(k)}</th>` +
    `<td style="padding:6px 0;vertical-align:top">${esc(v).replace(/\n/g, '<br>')}</td></tr>`
  ).join('');
  return `<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;` +
    `font-size:15px;color:#0b1b2b"><h2 style="margin:0 0 14px;font-size:18px">` +
    `${esc(subject)}</h2><table cellpadding="0" cellspacing="0">${trs}</table>` +
    `<p style="margin:18px 0 0;font-size:13px;color:#64758a">` +
    `Sent from the contact form at fastandperfect.ca</p></div>`;
}

/* ---------------------------------------------------------------- senders
   Each returns { ok } or { ok:false, error }. They never throw — a provider
   being down must produce an honest "not delivered", not a crash. */

async function sendWeb3Forms(env, { to, subject, rows, replyTo }) {
  const r = await fetch('https://api.web3forms.com/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(Object.assign(
      {
        access_key: env.WEB3FORMS_KEY,
        subject,
        from_name: 'Fast and Perfect website',
        replyto: replyTo || undefined
      },
      Object.fromEntries(rows)
    ))
  });
  let body = {};
  try { body = await r.json(); } catch (_) { /* non-JSON = not a success */ }
  return r.ok && body.success
    ? { ok: true, via: 'web3forms' }
    : { ok: false, error: `web3forms ${r.status} ${body.message || ''}`.trim() };
}

async function sendBrevo(env, { to, subject, rows, replyTo }) {
  const r = await fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: {
      'api-key': env.BREVO_API_KEY,
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify({
      sender: { name: 'Fast and Perfect website', email: env.FROM_EMAIL || to },
      to: [{ email: to }],
      replyTo: replyTo ? { email: replyTo } : undefined,
      subject,
      htmlContent: htmlBody(rows, subject),
      textContent: textBody(rows)
    })
  });
  if (r.ok) return { ok: true, via: 'brevo' };
  return { ok: false, error: `brevo ${r.status} ${(await r.text()).slice(0, 160)}` };
}

async function sendResend(env, { to, subject, rows, replyTo }) {
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: env.FROM_EMAIL || 'Fast and Perfect <onboarding@resend.dev>',
      to: [to],
      reply_to: replyTo || undefined,
      subject,
      html: htmlBody(rows, subject),
      text: textBody(rows)
    })
  });
  if (r.ok) return { ok: true, via: 'resend' };
  return { ok: false, error: `resend ${r.status} ${(await r.text()).slice(0, 160)}` };
}

/* No account needed, but this is the service that was returning 500 — so it
   is the last resort, not the default. */
async function sendFormSubmit(env, { to, subject, rows }) {
  const body = new URLSearchParams();
  rows.forEach(([k, v]) => body.append(k, v));
  body.append('_subject', subject);
  body.append('_captcha', 'false');
  body.append('_template', 'table');
  const r = await fetch(`https://formsubmit.co/ajax/${to}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Accept: 'application/json'
    },
    body
  });
  let j = {};
  try { j = await r.json(); } catch (_) { /* an HTML error page, not a send */ }
  /* This service answers 200 with success:"false" while an address is
     unconfirmed. Treating r.ok as delivery would report a send that never
     happened, which is the exact bug we are here to remove. */
  const delivered = r.ok && String(j.success) === 'true';
  return delivered
    ? { ok: true, via: 'formsubmit' }
    : { ok: false, error: `formsubmit ${r.status} ${j.message || 'not confirmed'}` };
}

function pickSender(env) {
  if (env.WEB3FORMS_KEY) return sendWeb3Forms;
  if (env.BREVO_API_KEY) return sendBrevo;
  if (env.RESEND_API_KEY) return sendResend;
  return sendFormSubmit;
}

export async function onRequestPost({ request, env }) {
  const to = env.TO_EMAIL || DEFAULT_TO;
  const url = new URL(request.url);
  const origin = url.origin;

  let fd;
  try {
    const ct = request.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      fd = new FormData();
      const j = await request.json();
      Object.entries(j || {}).forEach(([k, v]) => fd.append(k, v));
    } else {
      fd = await request.formData();
    }
  } catch (_) {
    return respond(request, origin, false, 'We could not read that submission.');
  }

  /* Honeypots. A bot fills fields a person never sees. Answer with a normal
     success so it does not learn to work around the trap — but send nothing. */
  if ((fd.get('_gotcha') || '').trim() || (fd.get('_honey') || '').trim()) {
    return respond(request, origin, true, null);
  }

  const rows = collect(fd);
  const name = (fd.get('name') || '').toString().trim();
  const email = (fd.get('email') || '').toString().trim();
  const phone = (fd.get('phone') || '').toString().trim();

  if (!name || (!email && !phone)) {
    return respond(request, origin, false,
      'Please include your name and either a phone number or an email address.');
  }

  const subject = (fd.get('_subject') || '').toString().trim() ||
    `New enquiry from fastandperfect.ca — ${name}`;

  const send = pickSender(env);
  let result;
  try {
    result = await send(env, { to, subject, rows, replyTo: email });
  } catch (err) {
    result = { ok: false, error: String(err && err.message || err).slice(0, 160) };
  }

  if (!result.ok) {
    /* Goes to the Cloudflare Pages function log, never to the customer. */
    console.error('enquiry delivery failed:', result.error);
    return respond(request, origin, false,
      'We could not send that just now. Please use the "email this to us ' +
      'instead" link just above the button, or call (587) 338-0069. We do ' +
      'not want to lose your request.');
  }

  return respond(request, origin, true, null);
}

/* A browser with JavaScript gets JSON and stays on the page. A browser
   without it gets a redirect, so the form still works with JS disabled. */
function respond(request, origin, ok, message) {
  const accept = request.headers.get('accept') || '';
  const wantsJson = accept.includes('application/json');

  if (wantsJson) {
    return new Response(JSON.stringify({ ok, message }), {
      status: ok ? 200 : 502,
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
    });
  }
  const dest = ok
    ? `${origin}/thank-you.html`
    : `${origin}/contact.html?send=failed`;
  return Response.redirect(dest, 303);
}

/* A GET here is someone poking at the URL, not a customer. */
export async function onRequestGet() {
  return new Response('This endpoint accepts form submissions only.', {
    status: 405,
    headers: { Allow: 'POST', 'Content-Type': 'text/plain' }
  });
}
