"""Shared head, header, footer, and JSON-LD built from the content file."""

from __future__ import annotations

import html
import json
from typing import Any

PHONE_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
    '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6 '
    '19.8 19.8 0 0 1-3.1-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.6a2 2 0 0 1-.5 2.1'
    'L8.1 9.9a16 16 0 0 0 6 6l1.5-1.1a2 2 0 0 1 2.1-.4c.8.3 1.7.5 2.6.6a2 2 0 0 1 1.7 2z"/>'
    "</svg>"
)

ICONS = {
    "bath": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M4 13h16v2a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4v-2z"/>'
        '<path d="M6 13V7a2 2 0 0 1 2-2h1"/><path d="M4 20l1.5-1.5M20 20l-1.5-1.5"/></svg>'
    ),
    "paint": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M4 5h12a2 2 0 0 1 2 2v3H8a2 2 0 0 0-2 2v0"/>'
        '<path d="M14 15h2.5a2.5 2.5 0 0 1 0 5H14a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1z"/><path d="M8 10v2"/></svg>'
    ),
    "deck": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M4 10h16v8H4z"/>'
        '<path d="M7 10V6h4v4M4 14h16M4 18h16"/></svg>'
    ),
    "kitchen": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M4 4h16v16H4z"/>'
        '<path d="M8 8h8v4H8zM8 16h3M14 16h2"/></svg>'
    ),
    "roof": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M3 12l9-8 9 8"/>'
        '<path d="M5 10.5V20h14v-9.5"/></svg>'
    ),
    "floor": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></svg>'
    ),
    "multi": (
        '<svg class="service-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true"><path d="M14.7 6.3a4 4 0 0 0-5.6 5.6L4 17l3 3 '
        '5.1-5.1a4 4 0 0 0 5.6-5.6l-2.2 2.2-2.8-2.8z"/></svg>'
    ),
}

NAV = [
    ("home", "index.html", "Home"),
    ("services", "services.html", "Services"),
    ("about", "about.html", "About"),
    ("team", "team.html", "Team"),
    ("area", "area.html", "Service area"),
    ("contact", "contact.html", "Contact"),
]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def county_inline(content: dict[str, Any]) -> str:
    shorts = [str(item["short"]) for item in content["service_area"]]
    if len(shorts) == 1:
        return shorts[0]
    return ", ".join(shorts[:-1]) + ", and " + shorts[-1]


def cta_text(content: dict[str, Any]) -> str:
    """The visible call-to-action sentence, with the payment line in place of cash-or-check."""
    phone = str(content.get("phone_display") or "").strip()
    email = str(content["email"]).strip()
    lead = str(content["cta"].get("lead") or "").strip()
    if lead:
        return lead
    contact = f"email {email}"
    if phone:
        contact = f"Call {phone} or {contact}"
    else:
        contact = contact[0].upper() + contact[1:]
    return f"{contact}. We pick up on weekdays, Central Time. {content['payment']}"


def prepare_context(content: dict[str, Any], page_id: str) -> dict[str, Any]:
    """Copy content and add derived fields. Does not mutate the file-backed dict."""
    ctx = json.loads(json.dumps(content))
    page = ctx['pages'][page_id]
    ctx['page'] = page
    ctx['page_id'] = page_id
    ctx['county_inline'] = county_inline(ctx)
    ctx['cta_text'] = cta_text(ctx)
    ctx['phone_display'] = str(ctx.get("phone_display") or "")
    ctx['phone_tel'] = str(ctx.get("phone_tel") or "")
    ctx['has_phone'] = bool(ctx['phone_display'] and ctx['phone_tel'])
    services = []
    for service in ctx['services']:
        item = dict(service)
        icon = ICONS.get(str(item.get("icon") or ""))
        if icon is None:
            raise SystemExit(f"Service {item.get('id')} has no known icon '{item.get('icon')}'.")
        item["icon_svg"] = icon
        services.append(item)
    ctx['services'] = services
    counties = []
    for county in ctx['service_area']:
        item = dict(county)
        item["badge_class"] = "badge" if item.get("home_base") else "badge badge-quiet"
        counties.append(item)
    ctx['service_area'] = counties
    ctx['counties'] = counties
    gallery = []
    for photo in ctx['gallery']:
        if photo.get("reviewed") is True:
            gallery.append(photo)
    ctx['gallery_public'] = gallery
    ctx['team_cards'] = [_team_card(ctx, member) for member in ctx.get("team", [])]
    ctx['phone_svg'] = PHONE_SVG
    ctx['footer_nav'] = _footer_nav()
    ctx['header_nav'] = _header_nav(page_id)
    return ctx


def _team_card(ctx: dict[str, Any], member: dict[str, Any]) -> dict[str, Any]:
    bits = []
    if member.get("show_phone") and ctx['has_phone']:
        bits.append(f'<a href="tel:{esc(ctx['phone_tel'])}">{esc(ctx['phone_display'])}</a>')
    email = str(member.get("email") or "").strip()
    if email:
        bits.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
    return {
        "initials": member.get("initials") or "",
        "name": member.get("name") or "",
        "role": member.get("role") or "",
        "bio": member.get("bio") or "",
        "contact_html": "<br>".join(bits),
    }


def _header_nav(page_id: str) -> str:
    items = []
    for pid, href, label in NAV:
        current = ' aria-current="page"' if pid == page_id else ""
        items.append(f'<li><a href="{esc(href)}"{current}>{esc(label)}</a></li>')
    return "\n          ".join(items)


def _footer_nav() -> str:
    items = [f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for _pid, href, label in NAV]
    return "\n            ".join(items)


def render_head(ctx: dict[str, Any]) -> str:
    page = ctx['page']
    title = page["title"]
    description = page["description"]
    canonical = page["canonical"]
    image = ctx['og_image']
    image_alt = ctx['og_image_alt']
    return f"""  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="{esc(ctx['theme_color'])}">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:locale" content="en_US">
  <meta property="og:image" content="{esc(image)}">
  <meta property="og:image:alt" content="{esc(image_alt)}">
  <meta name="twitter:card" content="summary">
  <link rel="icon" href="assets/apple-touch.png" type="image/png">
  <link rel="apple-touch-icon" href="assets/apple-touch.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500..700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">"""


def render_jsonld(ctx: dict[str, Any]) -> str:
    page = ctx['page']
    area = [
        {"@type": "AdministrativeArea", "name": f"{county['name']}, Alabama"}
        for county in ctx['service_area']
    ]
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "name": ctx['business_name'],
        "description": page["schema_description"],
        "url": ctx['site_url'],
        "email": ctx['email'],
        "image": ctx['og_image'],
        "paymentAccepted": ctx['payment'],
        "currenciesAccepted": "USD",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": ctx['locality'],
            "addressRegion": "AL",
            "addressCountry": "US",
        },
        "areaServed": area,
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "opens": "08:00",
            "closes": "17:00",
        },
        "sameAs": [ctx['facebook']],
    }
    if ctx['has_phone']:
        data["telephone"] = ctx['phone_schema']
    if page.get("offer_catalog"):
        data["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": "Residential renovation and rebuilds",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": name}}
                for name in ctx['schema_services']
            ],
        }
    # Keep telephone next to the historical position: name, description, url, telephone, email.
    ordered = {
        "@context": data["@context"],
        "@type": data["@type"],
        "name": data["name"],
        "description": data["description"],
        "url": data["url"],
    }
    if "telephone" in data:
        ordered["telephone"] = data["telephone"]
    ordered["email"] = data["email"]
    ordered["image"] = data["image"]
    ordered["paymentAccepted"] = data["paymentAccepted"]
    ordered["currenciesAccepted"] = data["currenciesAccepted"]
    ordered["address"] = data["address"]
    if "hasOfferCatalog" in data:
        ordered["hasOfferCatalog"] = data["hasOfferCatalog"]
    ordered["areaServed"] = data["areaServed"]
    ordered["openingHoursSpecification"] = data["openingHoursSpecification"]
    ordered["sameAs"] = data["sameAs"]
    body = json.dumps(ordered, indent=2, ensure_ascii=False)
    comment = ""
    if page.get("schema_comment"):
        comment = f"<!-- {page['schema_comment']} -->\n"
    return f"{comment}<script type=\"application/ld+json\">\n{body}\n</script>"


def render_header(ctx: dict[str, Any]) -> str:
    phone = ""
    if ctx['has_phone']:
        phone = f"""        <a class="header-phone" href="tel:{esc(ctx['phone_tel'])}" aria-label="Call {esc(ctx['phone_display'])}">
          {PHONE_SVG}
          <span class="header-phone-label">{esc(ctx['phone_display'])}</span>
        </a>"""
    quote = ctx['cta']['button']
    return f"""  <header class="site-header">
    <div class="wrap header-inner">
      <a class="logo" href="index.html" aria-label="{esc(ctx['business_name'])} — home">
        <img class="logo-img" src="assets/logo-512.jpg" width="48" height="48" alt="">
        <span class="logo-text">
          <span class="logo-name">{esc(ctx['short_name'])}</span>
          <span class="logo-tag">{esc(ctx['logo_tag'])}</span>
        </span>
      </a>
      <nav class="site-nav" id="site-nav" aria-label="Primary">
        <ul>
          {ctx['header_nav']}
        </ul>
      </nav>
      <div class="header-actions">
        <a class="header-quote" href="contact.html#quote"><span class="hq-long">{esc(quote)}</span><span class="hq-short">Quote</span></a>
{phone}
      </div>
      <button type="button" class="nav-toggle" id="nav-toggle" aria-controls="site-nav" aria-expanded="false" aria-label="Open menu">
        <svg class="icon-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
        <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
    </div>
  </header>"""


def render_cta(ctx: dict[str, Any]) -> str:
    page = ctx['page']
    cta_id = page["cta_id"]
    href = page["cta_href"]
    phone_btn = ""
    if ctx['has_phone']:
        phone_btn = (
            f'<a class="btn btn-primary" href="tel:{esc(ctx['phone_tel'])}">{PHONE_SVG}'
            f'Call {esc(ctx['phone_display'])}</a>\n        '
        )
    return f"""  <section class="cta-band" aria-labelledby="{esc(cta_id)}">
    <div class="wrap cta-band-inner">
      <div>
        <h2 id="{esc(cta_id)}">{esc(ctx['cta']['heading'])}</h2>
        <p>{esc(ctx['cta_text'])}</p>
      </div>
      <div class="cta-row">
        {phone_btn}<a class="btn btn-on-dark" href="{esc(href)}">{esc(ctx['cta']['button'])}</a>
      </div>
    </div>
  </section>"""


def render_footer(ctx: dict[str, Any]) -> str:
    phone = ""
    if ctx['has_phone']:
        phone = f'<a href="tel:{esc(ctx['phone_tel'])}">{esc(ctx['phone_display'])}</a><br>\n            '
    return f"""  <footer class="site-footer">
    <div class="wrap">
      <div class="footer-grid">
        <div>
          <div class="footer-brand-row">
            <img class="footer-logo" src="assets/logo-512.jpg" width="48" height="48" alt="">
            <div>
              <p class="footer-brand">{esc(ctx['business_name'])}</p>
              <p class="footer-tagline">{esc(ctx['tagline'])}</p>
              <p class="footer-vet">{esc(ctx['veteran_line'])}</p>
            </div>
          </div>
          <p class="footer-tag">{esc(ctx['footer_tag'])}</p>
          <p class="footer-meta">
            {phone}<a href="mailto:{esc(ctx['email'])}">{esc(ctx['email'])}</a><br>
            <a href="{esc(ctx['facebook'])}" rel="noopener noreferrer">Facebook</a>
          </p>
          <p class="footer-pay">{esc(ctx['payment'])}</p>
        </div>
        <nav aria-label="Footer">
          <p class="footer-heading">Pages</p>
          <ul class="footer-nav">
            {ctx['footer_nav']}
          </ul>
        </nav>
        <div>
          <p class="footer-heading">Service area</p>
          <p class="footer-tag">County-wide in {esc(ctx['county_inline'])}.</p>
        </div>
      </div>
      <p class="footer-bottom">
        &copy; <span id="year">2026</span> {esc(ctx['business_name'])}.
      </p>
    </div>
  </footer>"""
