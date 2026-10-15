import { handleQuote } from "../../lib/quote.mjs";

export async function onRequestPost(context) {
  return handleQuote(context.request, context.env);
}

export async function onRequest(context) {
  if (context.request.method === "POST") return onRequestPost(context);
  return Response.json(
    { ok: false, message: "Use the quote form on the contact page." },
    { status: 405, headers: { "cache-control": "no-store" } },
  );
}
