/**
 * Quote-request validation and email payload for the Pages Function.
 * Pure helpers stay free of Cloudflare-only imports so Node tests can run them.
 */

export const LEAD_TO = "eve-phoenix@mail.grokbot.com";
export const LEAD_FROM_INBOX = "phoenix-leads@agentmail.to";
export const QUOTE_ACTION = "quote";
export const THANKS =
  "Thank you. We received your quote request and will reply within 1 business day.";

export const WORK_TYPES = {
  kitchen: "Kitchen",
  bath: "Bath",
  flooring: "Flooring",
  decking: "Decking",
  "full-rebuild": "Full rebuild",
  "insurance-storm": "Insurance / storm",
  other: "Other",
};

export const CONTACT_TIMES = {
  morning: "Morning (8 AM–noon)",
  afternoon: "Afternoon (noon–5 PM)",
  evening: "Evening (after 5 PM)",
  anytime: "Anytime",
};

const TEST_SECRETS = new Set([
  "1x0000000000000000000000000000000AA",
  "2x0000000000000000000000000000000AA",
  "3x0000000000000000000000000000000AA",
]);

export function isLocalHost(hostname) {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

export function allowedHostnames(env) {
  return new Set(
    String(env.TURNSTILE_HOSTNAMES || "")
      .split(",")
      .map((hostname) => hostname.trim().toLowerCase())
      .filter(Boolean),
  );
}

export function oneLine(value, max) {
  return String(value || "")
    .replace(/[\u0000-\u001F\u007F]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max);
}

export function townForSubject(raw) {
  const clean = oneLine(raw, 160);
  if (!clean) return "";
  const parts = clean
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  const drop = (part) =>
    /^(al|alabama)(\s+\d{5}(?:-\d{4})?)?$/i.test(part) ||
    /^\d{5}(?:-\d{4})?$/.test(part);
  while (parts.length > 1 && drop(parts[parts.length - 1])) parts.pop();
  return (parts[parts.length - 1] || clean).slice(0, 40);
}

export function buildSubject(name, typeLabel, town) {
  return `New quote request: ${oneLine(name, 80)} - ${oneLine(typeLabel, 40)} - ${oneLine(town, 40)}`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char];
  });
}

function json(status, message, extra) {
  return Response.json(
    { ok: status >= 200 && status < 300, message, ...extra },
    {
      status,
      headers: {
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
      },
    },
  );
}

function field(form, name) {
  const value = form.get(name);
  return typeof value === "string" ? value.trim() : "";
}

export function validateQuote(form) {
  const errors = [];
  const honeypot = field(form, "company_website");
  const name = oneLine(field(form, "name"), 80);
  const phone = oneLine(field(form, "phone"), 30);
  const email = oneLine(field(form, "email"), 120);
  const address = oneLine(field(form, "address"), 160);
  const workType = field(form, "work_type");
  const description = field(form, "description").replace(/\u0000/g, "").trim();
  const contactTime = field(form, "contact_time");

  if (honeypot) {
    return { ok: true, honeypot: true };
  }
  if (!name || name.length > 80) errors.push("Enter your name.");
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 10 || digits.length > 15) errors.push("Enter a phone number we can call.");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push("Enter an email address.");
  if (address.length < 2) errors.push("Enter the job address or town.");
  if (!WORK_TYPES[workType]) errors.push("Choose a type of work.");
  if (!description || description.length > 4000) errors.push("Describe the job.");
  if (!CONTACT_TIMES[contactTime]) errors.push("Choose a preferred contact time.");

  if (errors.length) return { ok: false, errors };
  return {
    ok: true,
    honeypot: false,
    lead: {
      name,
      phone,
      email,
      address,
      town: townForSubject(address),
      workType,
      typeLabel: WORK_TYPES[workType],
      description: description.slice(0, 4000),
      contactTime,
      contactLabel: CONTACT_TIMES[contactTime],
    },
  };
}

async function verifyTurnstile(token, request, env, fetchImpl) {
  const hostname = new URL(request.url).hostname.toLowerCase();
  const secret = String(env.TURNSTILE_SECRET || "").trim();
  const expected = allowedHostnames(env);
  if (!secret || expected.size === 0 || (TEST_SECRETS.has(secret) && !isLocalHost(hostname))) {
    return { ok: false, ready: false };
  }
  if (!expected.has(hostname)) return { ok: false, ready: true };
  if (typeof token !== "string" || token.length === 0 || token.length > 2048) {
    return { ok: false, ready: true };
  }

  const remoteip = request.headers.get("CF-Connecting-IP") || "";
  let result;
  try {
    const response = await fetchImpl("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      signal: AbortSignal.timeout(10_000),
      body: new URLSearchParams({
        secret,
        response: token,
        remoteip,
      }),
    });
    if (!response.ok) return { ok: false, ready: true };
    result = await response.json();
  } catch {
    return { ok: false, ready: true };
  }

  if (!result || result.success !== true) return { ok: false, ready: true };

  // Cloudflare's published testing keys succeed with hostname "example.com"
  // and omit action. They are already refused on every public hostname above.
  if (TEST_SECRETS.has(secret) && isLocalHost(hostname)) {
    return { ok: true, ready: true };
  }

  const seenHost = String(result.hostname || "").toLowerCase();
  if (result.action !== QUOTE_ACTION || seenHost !== hostname || !expected.has(seenHost)) {
    return { ok: false, ready: true };
  }
  return { ok: true, ready: true };
}

function emailBodies(lead) {
  const lines = [
    "New quote request from the Phoenix Restoration website.",
    "",
    `Name: ${lead.name}`,
    `Phone: ${lead.phone}`,
    `Email: ${lead.email}`,
    `Job address or town: ${lead.address}`,
    `Town: ${lead.town}`,
    `Type of work: ${lead.typeLabel}`,
    `Preferred contact time: ${lead.contactLabel}`,
    "",
    "Description:",
    lead.description,
    "",
    "Reply to the customer within 1 business day.",
  ];
  const text = lines.join("\n");
  const html = [
    "<p>New quote request from the Phoenix Restoration website.</p>",
    "<ul>",
    `<li><strong>Name:</strong> ${escapeHtml(lead.name)}</li>`,
    `<li><strong>Phone:</strong> ${escapeHtml(lead.phone)}</li>`,
    `<li><strong>Email:</strong> ${escapeHtml(lead.email)}</li>`,
    `<li><strong>Job address or town:</strong> ${escapeHtml(lead.address)}</li>`,
    `<li><strong>Town:</strong> ${escapeHtml(lead.town)}</li>`,
    `<li><strong>Type of work:</strong> ${escapeHtml(lead.typeLabel)}</li>`,
    `<li><strong>Preferred contact time:</strong> ${escapeHtml(lead.contactLabel)}</li>`,
    "</ul>",
    `<p><strong>Description</strong></p><p>${escapeHtml(lead.description).replace(/\n/g, "<br>")}</p>`,
    "<p>Reply to the customer within 1 business day.</p>",
  ].join("");
  return { text, html };
}

export async function handleQuote(request, env, fetchImpl = globalThis.fetch) {
  if (request.method !== "POST") {
    return json(405, "Use the quote form on the contact page.");
  }

  const url = new URL(request.url);
  const hostname = url.hostname.toLowerCase();
  const origin = request.headers.get("Origin");
  if (origin) {
    try {
      if (new URL(origin).hostname.toLowerCase() !== hostname) {
        return json(403, "The security check failed. Please try again.");
      }
    } catch {
      return json(403, "The security check failed. Please try again.");
    }
  }

  let form;
  try {
    form = await request.formData();
  } catch {
    return json(400, "We couldn't read that submission. Please try again.");
  }

  const parsed = validateQuote(form);
  if (parsed.honeypot) return json(200, THANKS);
  if (!parsed.ok) return json(400, parsed.errors[0]);

  const token = field(form, "cf-turnstile-response");
  const turnstile = await verifyTurnstile(token, request, env, fetchImpl);
  if (!turnstile.ready) {
    return json(503, "This form isn't ready yet. Please call (334) 327-7450.");
  }
  if (!turnstile.ok) {
    return json(403, "The security check failed. Please try again.");
  }

  const lead = parsed.lead;
  const apiKey = String(env.AGENTMAIL_API_KEY || "").trim();
  const inbox = oneLine(env.LEAD_FROM_INBOX || "", 200);
  const to = oneLine(env.LEAD_TO || "", 200);
  if (!apiKey || !inbox || !to) {
    return json(503, "This form isn't ready yet. Please call (334) 327-7450.");
  }

  const { text, html } = emailBodies(lead);
  const subject = buildSubject(lead.name, lead.typeLabel, lead.town);
  let mailResponse;
  try {
    mailResponse = await fetchImpl(
      `https://api.agentmail.to/v0/inboxes/${encodeURIComponent(inbox)}/messages/send`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          to,
          reply_to: lead.email,
          subject,
          text,
          html,
        }),
      },
    );
  } catch {
    console.log(JSON.stringify({ event: "quote_email_failed", status: 0 }));
    return json(502, "We couldn't send that just now. Please call (334) 327-7450.");
  }
  if (!mailResponse.ok) {
    console.log(JSON.stringify({ event: "quote_email_failed", status: mailResponse.status }));
    return json(502, "We couldn't send that just now. Please call (334) 327-7450.");
  }

  console.log(JSON.stringify({ event: "quote_email_sent", type: lead.workType }));
  return json(200, THANKS);
}
