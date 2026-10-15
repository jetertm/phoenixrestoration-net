import assert from "node:assert/strict";
import test from "node:test";
import {
  LEAD_FROM_INBOX,
  THANKS,
  buildSubject,
  handleQuote,
  townForSubject,
} from "../lib/quote.mjs";

const API_KEY = "am_test_key";
const INBOX = "phoenix-leads@agentmail.to";
const LEAD_TO = "eve-phoenix@mail.grokbot.com";
const SEND_URL = `https://api.agentmail.to/v0/inboxes/${encodeURIComponent(INBOX)}/messages/send`;

function env(overrides = {}) {
  return {
    AGENTMAIL_API_KEY: API_KEY,
    TURNSTILE_SECRET: "secret-from-the-dashboard",
    TURNSTILE_HOSTNAMES:
      "phoenixrestoration.net,www.phoenixrestoration.net,phoenixrestoration-net.pages.dev",
    LEAD_FROM_INBOX: INBOX,
    LEAD_TO,
    ...overrides,
  };
}

function siteverifyBody(hostname = "phoenixrestoration.net") {
  return {
    success: true,
    action: "quote",
    hostname,
  };
}

function quoteForm(fields) {
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
  return form;
}

function requestFor(form, host = "phoenixrestoration.net") {
  return new Request(`https://${host}/api/quote`, {
    method: "POST",
    body: form,
    headers: { origin: `https://${host}` },
  });
}

/**
 * Routes Cloudflare Siteverify and the AgentMail send through one fetch mock.
 * `siteverify` may be a function (url, init) => body object, or a body object.
 * `mailStatus` is the AgentMail HTTP status. `mailThrow` rejects the send.
 */
function mockFetch({ siteverify = siteverifyBody(), mailStatus = 200, mailThrow = false, calls }) {
  return async (url, init) => {
    const href = String(url);
    if (calls) calls.push({ url: href, init });
    if (href === "https://challenges.cloudflare.com/turnstile/v0/siteverify") {
      const body = typeof siteverify === "function" ? await siteverify(href, init) : siteverify;
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }
    if (href === SEND_URL) {
      if (mailThrow) throw new Error("network down");
      return new Response(JSON.stringify({ ok: mailStatus < 300 }), {
        status: mailStatus,
        headers: { "content-type": "application/json" },
      });
    }
    throw new Error(`unexpected fetch ${href}`);
  };
}

function mailCalls(calls) {
  return calls.filter((call) => call.url === SEND_URL);
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
  assert.equal(LEAD_FROM_INBOX, "phoenix-leads@agentmail.to");
});

test("a valid quote posts to AgentMail with the visitor as reply_to", async () => {
  const calls = [];
  const response = await handleQuote(
    requestFor(quoteForm()),
    env(),
    mockFetch({ calls }),
  );
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.message, THANKS);

  const sent = mailCalls(calls);
  assert.equal(sent.length, 1);
  assert.equal(sent[0].init.method, "POST");
  assert.equal(sent[0].init.headers.Authorization, `Bearer ${API_KEY}`);
  assert.equal(sent[0].init.headers["Content-Type"], "application/json");
  assert.equal(sent[0].url, SEND_URL);

  const payload = JSON.parse(sent[0].init.body);
  assert.deepEqual(Object.keys(payload).sort(), ["html", "reply_to", "subject", "text", "to"]);
  assert.equal(payload.to, LEAD_TO);
  assert.equal(payload.reply_to, "jane@example.com");
  assert.equal(payload.subject, "New quote request: Jane Smith - Kitchen - Clanton");
  assert.match(payload.text, /Cabinets are falling apart/);
  assert.match(payload.text, /Morning \(8 AM–noon\)/);
  assert.match(payload.html, /Jane Smith/);
  assert.equal(payload.attachments, undefined);
});

test("a non-2xx AgentMail response is an error and does not thank the visitor", async () => {
  const calls = [];
  const response = await handleQuote(
    requestFor(quoteForm()),
    env(),
    mockFetch({ calls, mailStatus: 500 }),
  );
  const body = await response.json();
  assert.equal(response.status, 502);
  assert.equal(body.ok, false);
  assert.match(body.message, /couldn't send/i);
  assert.equal(mailCalls(calls).length, 1);
});

test("a network failure talking to AgentMail is an error", async () => {
  const response = await handleQuote(
    requestFor(quoteForm()),
    env(),
    mockFetch({ mailThrow: true }),
  );
  assert.equal(response.status, 502);
});

test("missing AgentMail settings fail closed and do not send", async () => {
  for (const overrides of [
    { AGENTMAIL_API_KEY: "" },
    { LEAD_FROM_INBOX: "" },
    { LEAD_TO: "" },
  ]) {
    const calls = [];
    const response = await handleQuote(
      requestFor(quoteForm()),
      env(overrides),
      mockFetch({ calls }),
    );
    assert.equal(response.status, 503);
    assert.equal(mailCalls(calls).length, 0);
  }
});

test("honeypot submissions look successful and do not send", async () => {
  const calls = [];
  const response = await handleQuote(
    requestFor(quoteForm({ company_website: "https://spam.example" })),
    env(),
    mockFetch({ calls }),
  );
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.message, THANKS);
  assert.equal(calls.length, 0);
});

test("turnstile must succeed for the quote action and hostname", async () => {
  const calls = [];
  const bad = await handleQuote(
    requestFor(quoteForm()),
    env(),
    mockFetch({
      calls,
      siteverify: { success: true, action: "login", hostname: "phoenixrestoration.net" },
    }),
  );
  assert.equal(bad.status, 403);
  assert.equal(mailCalls(calls).length, 0);

  const replay = await handleQuote(
    requestFor(quoteForm()),
    env(),
    mockFetch({
      calls,
      siteverify: { success: false, "error-codes": ["timeout-or-duplicate"] },
    }),
  );
  assert.equal(replay.status, 403);
  assert.equal(mailCalls(calls).length, 0);
});

test("localhost accepts Cloudflare's testing-key response", async () => {
  const calls = [];
  const response = await handleQuote(
    requestFor(quoteForm(), "127.0.0.1"),
    env({
      TURNSTILE_SECRET: "1x0000000000000000000000000000000AA",
      TURNSTILE_HOSTNAMES: "127.0.0.1",
    }),
    mockFetch({
      calls,
      siteverify: {
        success: true,
        hostname: "example.com",
        "error-codes": [],
        metadata: { result_with_testing_key: true },
      },
    }),
  );
  assert.equal(response.status, 200);
  const payload = JSON.parse(mailCalls(calls)[0].init.body);
  assert.equal(payload.subject, "New quote request: Jane Smith - Kitchen - Clanton");
  assert.equal(payload.reply_to, "jane@example.com");
});

test("testing secrets are refused on the public site", async () => {
  const calls = [];
  const response = await handleQuote(
    requestFor(quoteForm()),
    env({ TURNSTILE_SECRET: "1x0000000000000000000000000000000AA" }),
    mockFetch({ calls }),
  );
  assert.equal(response.status, 503);
  assert.equal(calls.length, 0);
});

test("unknown work types and cross-site posts are refused", async () => {
  const calls = [];
  const badType = await handleQuote(
    requestFor(quoteForm({ work_type: "handyman" })),
    env(),
    mockFetch({ calls }),
  );
  assert.equal(badType.status, 400);
  assert.equal(calls.length, 0);

  const cross = new Request("https://phoenixrestoration.net/api/quote", {
    method: "POST",
    body: quoteForm(),
    headers: { origin: "https://evil.example" },
  });
  const blocked = await handleQuote(cross, env(), mockFetch({ calls }));
  assert.equal(blocked.status, 403);
  assert.equal(mailCalls(calls).length, 0);
});
