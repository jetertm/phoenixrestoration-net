# phoenix-site

A small command-line tool for editing the Phoenix Restoration LLC website without hand-editing HTML. Eve changes the content file, builds, and checks. The pages keep the current layout.

Python 3.9 or newer. Works on Windows and Linux. The only dependency is Pillow, used when a photo is resized.

## Install

From the repository root:

```bash
pip install -r tools/phoenix-site/requirements.txt
```

Run it as:

```bash
python3 tools/phoenix-site/phoenix-site --help
```

On Windows, use `py` instead of `python3` if that is how Python is installed.

## Edit the words in one file

`tools/phoenix-site/content/site.json` is the copy Eve edits:

- business name
- services list
- service area
- contact email (`info@phoenixrestoration.net`)
- Facebook link
- call-to-action heading and button
- payment terms

The payment line is:

`Payment due within 7 days of invoice (Net 7). Accepted: card or ACH via Stripe pay link, ACH bank transfer, cash, check, or cashier's check.`

That sentence replaces the old "cash or check only" wording. The phone number already on the site, `(334) 327-7450`, stays. This tool does not add a new phone number.

Page templates live in `tools/phoenix-site/templates/`. A content edit is picked up on the next build.

## Commands

### build

```bash
python3 tools/phoenix-site/phoenix-site build
```

Writes the site to `dist/`. Static files (CSS, JavaScript, photos, the quote function) are copied with the rendered pages.

If a gallery photo is marked `"reviewed": false`, the build stops and does not publish. Jessy's rule: Eve looks at every public photo before it goes on the site.

Photos over 500 KB are published from `assets/optimized/` when a resized JPEG exists there, at the same path the page already uses. Originals stay in `assets/`.

### preview

```bash
python3 tools/phoenix-site/phoenix-site preview
python3 tools/phoenix-site/phoenix-site preview --port 8080
```

Builds, then serves `dist/` at `http://127.0.0.1:8080/`. It binds to this computer only.

### check

```bash
python3 tools/phoenix-site/phoenix-site check
```

Exits with an error if it finds:

- a broken local link
- an image with no alt text (the logo may use empty alt; it is decorative)
- an image over 500 KB
- a page missing a title, meta description, Open Graph tags, or a mobile viewport
- LocalBusiness JSON-LD that is not a home-renovation business serving Elmore County and Chilton County, Alabama
- a page over the size budget (HTML 100 KB, CSS 80 KB, JavaScript 80 KB, whole page 6 MB)

### optimize

```bash
python3 tools/phoenix-site/phoenix-site optimize
```

Also available as `phoenix-site check optimize`. Writes a resized JPEG and a WebP next to each oversized photo, under `assets/optimized/`. Originals are not deleted or overwritten.

### images

```bash
python3 tools/phoenix-site/phoenix-site images add path/to/photo.jpg
python3 tools/phoenix-site/phoenix-site images approve porch-evening
```

`images add` copies the photo into `assets/gallery/`, resizes it, and adds it to the gallery list with `"reviewed": false`. Put a real `alt` sentence in `site.json` before approving. `images approve` sets `reviewed` to true so the next build may include it.

### deploy

```bash
python3 tools/phoenix-site/phoenix-site deploy
python3 tools/phoenix-site/phoenix-site deploy --commit
```

Dry run is the default. It prints the plan and does not upload.

The Cloudflare Pages project `phoenixrestoration-net` is a direct upload. It is not connected to Git, and it has no build command, so a push does not publish the site. `--commit` builds, runs `check`, and then runs:

```bash
wrangler pages deploy dist --project-name phoenixrestoration-net
```

`CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` must be in the environment. The tool never prints them.

Do not run `--commit` until Jessy has asked for a deploy. This command does not change DNS.

If the project is later connected to Git, set the Pages build command to `python3 tools/phoenix-site/phoenix-site build` and the output directory to `dist`, and change `GIT_INTEGRATION` in `phoenix_site/deploy.py` so deploy pushes instead of uploading.

### dns-check

```bash
python3 tools/phoenix-site/phoenix-site dns-check
```

Reads A and CNAME records for `phoenixrestoration.net` and `www`, plus MX. It never creates or edits DNS.

Google Workspace mail is on this domain (`aspmx.l.google.com` and the alt MX hosts). The saved plan only describes a future website cutover for the apex and www names. If that plan were edited to change MX or nameservers, the command exits with an error and says, loudly, that Google Workspace mail would break. Leave the MX records as they are.

### uptime

```bash
python3 tools/phoenix-site/phoenix-site uptime
```

Fetches the live Pages URL and the custom-domain URLs. It prints HTTP status, response time, and TLS certificate expiry. The custom domain can fail this check while GoDaddy still serves the apex; the Pages URL is what decides the exit code.

## Tests

From `tools/phoenix-site`:

```bash
python3 -m pytest
```

That run does not use the network. Live DNS and uptime checks are marked `live`:

```bash
python3 -m pytest -m live
```

## What this tool will not do

It will not deploy unless you pass `--commit`. It will not merge a pull request. It will not change GoDaddy or Cloudflare DNS.
