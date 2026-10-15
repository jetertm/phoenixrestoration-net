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

The contact page has a **Request a quote** form. It posts to the Pages Function at `/api/quote`, which sends the lead through AgentMail to `eve-phoenix@mail.grokbot.com`. The public address `info@phoenixrestoration.net` stays on the page for people who want to write directly. With JavaScript off, the form cannot send; the page tells the visitor to call or email.

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

The form sends through AgentMail. It does not use Cloudflare Email Sending, so GoDaddy DNS does not need to change. Do not add or edit MX, SPF, DKIM, or any other DNS record for this form.

Project: **phoenixrestoration-net**. Set these for Production and Preview. `LEAD_FROM_INBOX` and `LEAD_TO` are already in `wrangler.toml`. Secrets stay out of the file. For local `wrangler pages dev`, copy `.dev.vars.example` to `.dev.vars`.

| Kind | Name | Value |
| --- | --- | --- |
| Secret (encrypt) | `AGENTMAIL_API_KEY` | AgentMail API key for the leads inbox |
| Plain variable | `LEAD_FROM_INBOX` | `phoenix-leads@agentmail.to` |
| Plain variable | `LEAD_TO` | `eve-phoenix@mail.grokbot.com` |
| Plain variable | `TURNSTILE_HOSTNAMES` | `phoenixrestoration.net,www.phoenixrestoration.net,phoenixrestoration-net.pages.dev` |
| Plain variable | `TURNSTILE_SITE_KEY` | Public Turnstile sitekey from the widget step |
| Secret (encrypt) | `TURNSTILE_SECRET` | Turnstile secret key. Never commit it. |

The function POSTs to `https://api.agentmail.to/v0/inboxes/phoenix-leads@agentmail.to/messages/send` with `Authorization: Bearer` and JSON `to`, `reply_to`, `subject`, `text`, and `html`. `reply_to` is the visitor's email. The subject is `New quote request: <name> - <type> - <town>`. A non-2xx response is treated as a failure and the visitor is asked to call.

`TURNSTILE_SITE_KEY` is public. Add it under `[vars]` in `wrangler.toml` when you have it, because a deploy that applies this file can replace dashboard variables. Do not add `localhost` or `127.0.0.1` to the production Turnstile hostname list.

The handler rejects Cloudflare’s public testing secret on every hostname except `localhost` and `127.0.0.1`. On those two hosts, the documented testing keys are accepted even though Siteverify reports hostname `example.com` and omits the action. A real widget still has to match action `quote` and the request hostname.

### Turnstile widget

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
