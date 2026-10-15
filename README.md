# Phoenix Restoration LLC — static website

Multi-page marketing site for **Phoenix Restoration LLC**, a disabled veteran-owned residential remodeler based in Verbena, Alabama (Chilton County). The service area is ten counties, including Chilton and Autauga. Home base is Verbena only.

Domain: **https://phoenixrestoration.net/** — do not change DNS or register anything from this folder.

## Preview

No build step. Open `index.html` in a browser, or:

```bash
cd /workspace/phoenix-web/site
python3 -m http.server 8080
```

Then open http://127.0.0.1:8080/

Click through **Home → Services → About → Team → Service area → Contact**.

## Pages

| File | What it is |
|------|------------|
| `index.html` | Home: hero, services, real project photos, 10-county teaser, how a job starts |
| `services.html` | Full bathroom remodels, paint and trim, decks and fencing, full kitchen renovations, roofs, floors, multi-trade work |
| `about.html` | Disabled veteran-owned, owner Jessy Jeter, how we work, cash or check |
| `team.html` | Meet the team: Jessy Jeter and Eve Harper. Card grid so more people can be added later |
| `area.html` | All 10 counties, with example towns — not a list of offices. Based in Verbena |
| `contact.html` | Phone, email, hours, county list, quote form |
| `styles.css` | Shared styles |
| `site.js` | Menu, footer year, quote form, recent-work gallery |
| `functions/api/quote.js` | Pages Function that emails a quote request |
| `assets/recent-work/jobs.json` | Before/after jobs for the home page |
| `assets/` | Logo files and project photos |

The contact page has a **Request a quote** form. It posts to the Pages Function at `/api/quote`, which emails `eve-phoenix@mail.grokbot.com`. The public address `info@phoenixrestoration.net` stays on the page for people who want to write directly. With JavaScript off, the form cannot send; the page tells the visitor to call or email.

## What changed from the one-pager

- Split into separate HTML pages with a shared header, footer, and current-page nav.
- Header uses the circular Phoenix seal (`assets/logo-512.jpg`, made from the brand PNG), not the old inline SVG mark.
- The visible project photography uses the full-size Facebook originals in `assets/from-facebook/full/`: kitchen, bathroom, interior, porch, door/roof framing, and fireplace work. The home gallery mixes those photos with the two Chuck deck photos from Drive. The hero is the finished kitchen (`assets/from-facebook/full/kitchen-1.jpg`). Each service block has a matching project photo and a short caption. Thumbnail-only Facebook batch imports remain out of visible galleries; there are no stock photos or invented reviews.
- Service area is the locked list of 10 counties: Chilton, Autauga, Elmore, Shelby, Bibb, Coosa, Dallas, Perry, Lowndes, Montgomery.
- Each page has its own title, description, canonical URL, and Open Graph tags.
- Favicon is the seal (`assets/apple-touch.png`).

`assets/from-facebook/logo-1.jpg` and `cover.jpg` are the same wide Facebook cover. They say “Construction Service” and sit on a template jobsite that is not our work, so they are not used as the header logo or as a project photo. The round brand seal is the logo on the site.

## Facts used on the pages

- Phone: (334) 327-7450
- Public email: info@phoenixrestoration.net
- Payment: cash or check only; checks payable to Phoenix Restoration LLC
- Hours: Monday–Friday 8:00 AM–5:00 PM Central; weekends by appointment
- Facebook: https://www.facebook.com/people/Phoenix-Restoration/61559147480515/

## Publish

A zip of the site files (no preview screenshots) is at:

`/workspace/phoenix-web/phoenix-site-preview.zip` (site files for Desktop review; old preview screenshots left out so they do not show the removed deck) and `/workspace/phoenix-web/publish/phoenix-site.zip` (deploy package without preview screenshots).

Upload the publish zip’s contents as the web root when Jessy is ready. Do not point DNS until then.

## Quote form setup

The form does not send until the Cloudflare project `phoenixrestoration-net` has the binding, variables, and Turnstile secret below. This repo does not change DNS. Google Workspace mail on `phoenixrestoration.net` stays in place only if the apex MX records are left alone.

### Do not do this

- Do not click **Onboard Domain** for Email Routing on `phoenixrestoration.net`. That replaces the apex MX records (`aspmx.l.google.com` and the `alt` records) and takes incoming mail away from Google Workspace.
- Do not replace the apex SPF record Google Workspace uses.
- Do not replace an existing `_dmarc` TXT record. If Email Sending offers a new `_dmarc` policy of `p=reject`, refuse it. A new DMARC record, if you need one at all, should start as `v=DMARC1; p=none`.
- Do not add `localhost` or `127.0.0.1` to the production Turnstile hostname list.

### 1. Free email path (verified destination)

Sends to a verified destination address are free on Workers Free, including when only Email Routing is configured. Arbitrary-recipient Email Sending is a Workers Paid feature and is not required here.

1. In the Cloudflare dashboard, go to **Compute → Email Service → Email Routing → Destination addresses**. Add `eve-phoenix@mail.grokbot.com` and click the verification link Cloudflare sends to that inbox.
2. Open the zone `phoenixrestoration.net` under Email Routing. Do not onboard the apex. Open **Settings → Subdomains** and add `quotes`. Cloudflare adds MX records only on `quotes.phoenixrestoration.net` (its own `route1`, `route2`, and `route3.mx.cloudflare.net` records). Leave the apex MX records on Google. If that Subdomains control is unavailable unless you onboard the apex, stop and use the Email Sending fallback below. Do not onboard Email Routing on the apex.
3. Confirm the Pages binding can send only to that destination. `wrangler.toml` already contains:

```toml
[[send_email]]
name = "EMAIL"
destination_address = "eve-phoenix@mail.grokbot.com"
```

The function sends **from** `leads@quotes.phoenixrestoration.net` (variable `LEAD_FROM`) **to** `eve-phoenix@mail.grokbot.com`, with the visitor’s email as Reply-To. The subject line is `New quote request: <name> - <type> - <town>`.

If a send fails with the sender domain not verified, use Email **Sending** (not Email Routing) for `phoenixrestoration.net` instead of the subdomain. Email Sending adds records on the `cf-bounce` subdomain only:

| Type | Name | Purpose |
| --- | --- | --- |
| MX | `cf-bounce` | Bounce handling. Not the apex. |
| TXT | `cf-bounce` | SPF: `v=spf1 include:_spf.mx.cloudflare.net ~all` |
| TXT | `cf-bounce._domainkey` | DKIM. Cloudflare shows the value. |

Then set `LEAD_FROM` to `leads@phoenixrestoration.net`. Still do not change the apex MX or the Google SPF record.

### 2. Pages binding, variables, and secret

Project: **phoenixrestoration-net**. Set these for Production and Preview. After a Git deploy, confirm the binding is listed on the project. If the deploy did not apply `wrangler.toml`, add the binding in **Workers & Pages → phoenixrestoration-net → Settings → Bindings**.

| Kind | Name | Value |
| --- | --- | --- |
| Send Email binding | `EMAIL` | Destination address `eve-phoenix@mail.grokbot.com` only |
| Plain variable | `LEAD_FROM` | `leads@quotes.phoenixrestoration.net` |
| Plain variable | `LEAD_TO` | `eve-phoenix@mail.grokbot.com` |
| Plain variable | `TURNSTILE_HOSTNAMES` | `phoenixrestoration.net,www.phoenixrestoration.net,phoenixrestoration-net.pages.dev` |
| Plain variable | `TURNSTILE_SITE_KEY` | Public Turnstile sitekey from step 3 |
| Secret (encrypt) | `TURNSTILE_SECRET` | Turnstile secret key. Never commit it. |

`TURNSTILE_SITE_KEY` is public. Add it to `wrangler.toml` under `[vars]` when you have it, because a deploy that applies this file can replace dashboard variables. Leave `TURNSTILE_SECRET` out of the file. For local `wrangler pages dev`, copy `.dev.vars.example` to `.dev.vars`.

The handler rejects Cloudflare’s public testing secret on every hostname except `localhost` and `127.0.0.1`.

### 3. Turnstile widget

1. Dashboard → **Turnstile → Add widget**.
2. Name: `Phoenix quote form`. Mode: **Managed**.
3. Hostnames: `phoenixrestoration.net`, `www.phoenixrestoration.net`, `phoenixrestoration-net.pages.dev`.
4. Put the sitekey in `TURNSTILE_SITE_KEY` and the secret in `TURNSTILE_SECRET`.

The widget action is `quote`. The function calls `https://challenges.cloudflare.com/turnstile/v0/siteverify` and accepts the token only when `success` is true, `action` is `quote`, and `hostname` is both the request host and one of `TURNSTILE_HOSTNAMES`. There is also a honeypot field named `company_website`.

### 4. Recent work photos

`assets/recent-work/jobs.json` drives the home page section. To add a job, drop files in a new folder:

```text
assets/recent-work/my-job/before.jpg
assets/recent-work/my-job/after.jpg
assets/recent-work/my-job/job.json
```

`job.json` may set `title`, `trade`, `town`, `beforeAlt`, and `afterAlt`. Leave `town` empty until you know it. Then run:

```bash
node scripts/index-recent-work.mjs
```

JPG, JPEG, PNG, and WebP work. Pair only photos of the same job. The two jobs already listed point at photos that were already in the repo.

### Facts left unpublished

Street address, postal code, map coordinates, contractor license number, and reviews are not on the site. Do not invent them. The visible business facts are the phone `(334) 327-7450`, `info@phoenixrestoration.net`, Verbena in Chilton County, weekday hours 8–5 Central, and the ten counties already listed on the service-area page.
