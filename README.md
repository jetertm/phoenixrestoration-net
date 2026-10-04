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
| `contact.html` | Phone, email, hours, county list, accessible form |
| `styles.css` | Shared styles |
| `site.js` | Menu toggle, footer year, mailto form |
| `assets/` | Logo files and project photos |

The contact form does **not** store submissions and does **not** use a Google email widget. Submit opens the visitor’s email app with a message to `info@phoenixrestoration.net`. With JavaScript off, the form still uses `mailto:`.

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
