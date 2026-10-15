import assert from "node:assert/strict";
import test from "node:test";
import {
  THANKS,
  buildSubject,
  handleQuote,
  townForSubject,
} from "../lib/quote.mjs";

const PNG = Uint8Array.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
]);

function env(overrides = {}) {
  const sent = [];
  return {
    sent,
    EMAIL: {
      async send(message) {
        sent.push(message);
        return { messageId: "test-message" };
      },
    },
    TURNSTILE_SECRET: "secret-from-the-dashboard",
    TURNSTILE_HOSTNAMES:
      "phoenixrestoration.net,www.phoenixrestoration.net,phoenixrestoration-net.pages.dev",
    LEAD_FROM: "leads@quotes.phoenixrestoration.net",
    LEAD_TO: "eve-phoenix@mail.grokbot.com",
    ...overrides,
  };
}

function siteverifyOk(hostname = "phoenixrestoration.net") {
  return async () =>
    new Response(
      JSON.stringify({
        success: true,
        action: "quote",
        hostname,
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
}

function quoteForm(fields, file) {
  const form = new FormData();
  const values = {
    name: "Jane Smith",
    phone: "(334) 555-0100",
    email: "jane@example.com",
    address: "123 Oak St, Clanton, AL 35045",
    work_type: "kitchen",
    description: "Cabinets are falling apart and the counters need to go.",
    contact_time: "morning",
    "cf-turnstile-response": "token-from-widget",
    company_website: "",
    ...fields,
  };
  for (const [key, value] of Object.entries(values)) form.set(key, value);
  if (file) form.set("photo", file);
  return form;
}

function requestFor(form, host = "phoenixrestoration.net") {
  return new Request(`https://${host}/api/quote`, {
    method: "POST",
    body: form,
    headers: { origin: `https://${host}` },
  });
}

test("subject uses name, type, and town", () => {
  assert.equal(
    buildSubject("Jane Smith", "Kitchen", "Clanton"),
    "New quote request: Jane Smith - Kitchen - Clanton",
  );
  assert.equal(townForSubject("123 Oak St, Clanton, AL 35045"), "Clanton");
  assert.equal(townForSubject("Wetumpka, Alabama"), "Wetumpka");
  assert.equal(townForSubject("Elmore County"), "Elmore County");
  assert.equal(townForSubject("  12 Main\nStreet, Maplesville "), "Maplesville");
});

test("a valid quote emails only the intake inbox", async () => {
  const box = env();
  const response = await handleQuote(
    requestFor(quoteForm()),
    box,
    siteverifyOk(),
  );
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.message, THANKS);
  assert.equal(box.sent.length, 1);
  assert.equal(box.sent[0].to, "eve-phoenix@mail.grokbot.com");
  assert.equal(box.sent[0].from.email, "leads@quotes.phoenixrestoration.net");
  assert.equal(box.sent[0].replyTo, "jane@example.com");
  assert.equal(
    box.sent[0].subject,
    "New quote request: Jane Smith - Kitchen - Clanton",
  );
  assert.match(box.sent[0].text, /Cabinets are falling apart/);
  assert.match(box.sent[0].text, /Morning \(8 AM–noon\)/);
  assert.equal(box.sent[0].attachments, undefined);
});

test("honeypot submissions look successful and do not send", async () => {
  const box = env();
  const response = await handleQuote(
    requestFor(quoteForm({ company_website: "https://spam.example" })),
    box,
    siteverifyOk(),
  );
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.message, THANKS);
  assert.equal(box.sent.length, 0);
});

test("turnstile must succeed for the quote action and hostname", async () => {
  const box = env();
  const bad = await handleQuote(
    requestFor(quoteForm()),
    box,
    async () =>
      new Response(
        JSON.stringify({ success: true, action: "login", hostname: "phoenixrestoration.net" }),
        { status: 200 },
      ),
  );
  assert.equal(bad.status, 403);
  assert.equal(box.sent.length, 0);

  const replay = await handleQuote(
    requestFor(quoteForm()),
    box,
    async () =>
      new Response(JSON.stringify({ success: false, "error-codes": ["timeout-or-duplicate"] }), {
        status: 200,
      }),
  );
  assert.equal(replay.status, 403);
});

test("testing secrets are refused on the public site", async () => {
  const box = env({ TURNSTILE_SECRET: "1x0000000000000000000000000000000AA" });
  const response = await handleQuote(requestFor(quoteForm()), box, siteverifyOk());
  assert.equal(response.status, 503);
  assert.equal(box.sent.length, 0);
});

test("a small photo is attached and a large one is refused", async () => {
  const box = env();
  const file = new File([PNG], "job.png", { type: "image/png" });
  const response = await handleQuote(
    requestFor(quoteForm({}, file)),
    box,
    siteverifyOk(),
  );
  assert.equal(response.status, 200);
  assert.equal(box.sent[0].attachments.length, 1);
  assert.equal(box.sent[0].attachments[0].filename, "photo.png");
  assert.equal(box.sent[0].attachments[0].type, "image/png");

  const huge = new File([new Uint8Array(2 * 1024 * 1024 + 1)], "big.png", {
    type: "image/png",
  });
  const refused = await handleQuote(
    requestFor(quoteForm({}, huge)),
    box,
    siteverifyOk(),
  );
  assert.equal(refused.status, 400);
  assert.equal(box.sent.length, 1);
});

test("unknown work types and cross-site posts are refused", async () => {
  const box = env();
  const badType = await handleQuote(
    requestFor(quoteForm({ work_type: "handyman" })),
    box,
    siteverifyOk(),
  );
  assert.equal(badType.status, 400);

  const form = quoteForm();
  const cross = new Request("https://phoenixrestoration.net/api/quote", {
    method: "POST",
    body: form,
    headers: { origin: "https://evil.example" },
  });
  const blocked = await handleQuote(cross, box, siteverifyOk());
  assert.equal(blocked.status, 403);
  assert.equal(box.sent.length, 0);
});
