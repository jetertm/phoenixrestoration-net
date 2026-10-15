const TEST_SITEKEYS = new Set([
  "1x00000000000000000000AA",
  "2x00000000000000000000AB",
  "3x00000000000000000000FF",
]);

export function onRequestGet(context) {
  const host = new URL(context.request.url).hostname;
  const local = host === "localhost" || host === "127.0.0.1";
  const key = String(context.env.TURNSTILE_SITE_KEY || "").trim();
  const usable = Boolean(key) && (local || !TEST_SITEKEYS.has(key));
  return Response.json(
    { sitekey: usable ? key : null },
    {
      headers: {
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
      },
    },
  );
}
