#!/usr/bin/env python3
"""
build_site.py — single source of truth for dianasimpsonhernandez.com  (v5 · researcher, entrepreneur, lecturer profile)

    python3 build_site.py               # LIVE: regenerate every page + sitemap + robots + 404 into the repo root
    python3 build_site.py --hold        # HOLD: holding page at / and /404.html, other pages removed, sitemap = root only
    python3 build_site.py --preview     # PREVIEW: full site into ./_preview (git-ignored), repo root untouched
                                        #   then: python3 -m http.server 8000 -d _preview   →  http://localhost:8000
    python3 build_site.py --og          # also re-render the 1200×630 OG cards (needs playwright)

Content lives in data/*.json (writing, talks, teaching, methods, archive, aletheai).
To add an essay or a talk: add one entry to the JSON file, run, commit. No HTML editing.
Every page is generated from the same head(), nav() and footer(), so SEO tags,
structured data and the analytics snippet cannot drift between pages.

Location: London, remote-first. Madrid appears only as "IED Madrid" (an institution), never as where she lives.
Disclosure rules (do not relax without checking): as-filed patent wording only; "six patent applications filed";
no commercial figures (ARR, market size, per-agent savings, pilot claims); no codenames; DiSH Creative not named.
"""
from __future__ import annotations
import json, os, sys, shutil, datetime, html as H

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = ROOT                      # switched to ROOT/_preview by --preview
TODAY = datetime.date.today().isoformat()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
SITE = {
    "domain":   "https://dianasimpsonhernandez.com",
    "name":     "Diana Simpson-Hernandez",
    "short":    "DSH",
    "email":    "dianasimpsonhernandez@gmail.com",
    "tagline":  "Designer, researcher and founder. AI that keeps a record people can open.",
    "locale":   "en_GB",
    # Umami Cloud (free). Leave empty and NO analytics script is emitted.
    "umami_website_id": "a98055b4-17b2-4091-b09e-3b3b5b34b4ad",
    "umami_src": "https://cloud.umami.is/script.js",
}
LIB = "https://frameworks.dianasimpsonhernandez.com"

PROFILE = {
    "availability": "From 1 December 2026",
    "open_to": [
        "Fellowships, residencies and research collaborations in AI governance, assurance and safety",
        "Founding and leadership roles in AI product and AI governance",
        "Guest lectures, workshops and talks, in English or Spanish",
    ],
    "location": "London · remote-first",
    "cv": "/assets/dsh-cv.pdf",
    "linkedin": "https://linkedin.com/in/dianasimpson",
}

def utm(url: str, medium: str, campaign: str) -> str:
    if not url.startswith("http"): return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=dsh-site&utm_medium={medium}&utm_campaign={campaign}"

CHANNELS = [
    # key, label, url, blurb, kind   (v5: Skool and Instagram removed, no course funnel; YouTube off until it has content)
    ("substack",  "Substack",  "https://dianasimpsonhernandez.substack.com", "Essays on decision intelligence and AI that can be held to account.", "writing"),
    ("linkedin",  "LinkedIn",  PROFILE["linkedin"], "Field notes from building Aletheai.", "social"),
    ("github",    "GitHub",    "https://github.com/dsimpsonh", "Open frameworks and code.", "code"),
]
CH = {c[0]: c for c in CHANNELS}

# ─────────────────────────────────────────────────────────────────────────────
# DATA — data/*.json, validated on load so a bad edit fails the build, not the page
# ─────────────────────────────────────────────────────────────────────────────
def _load(name: str, required: dict) -> dict:
    path = os.path.join(ROOT, "data", f"{name}.json")
    with open(path, encoding="utf-8") as f: d = json.load(f)
    for key, fields in required.items():
        assert key in d, f"data/{name}.json: missing '{key}'"
        for i, item in enumerate(d[key] if isinstance(d[key], list) else [d[key]]):
            if isinstance(item, dict):
                missing = [k for k in fields if not item.get(k) and k != "url"]
                assert not missing, f"data/{name}.json → {key}[{i}] missing {missing}"
    return d

WRITING  = _load("writing",  {"essays": ["date", "title", "dek", "venue", "url"], "research": ["date", "title", "kind", "dek", "venue", "url"], "book": ["title", "url"], "audio": ["date", "title", "show", "url"]})
TALKS    = _load("talks",    {"talks": ["date", "when", "title", "venue", "era"]})["talks"]
TEACHING = _load("teaching", {"roles": ["years", "role", "org", "detail"]})["roles"]
METHODS  = _load("methods",  {"methods": ["name", "unit", "line", "text"], "tools": ["name", "text", "url"], "case": ["name", "text", "url"]})
ARCHIVE  = _load("archive",  {"projects": ["years", "name", "role", "text"], "exhibitions": [], "press": [], "awards": []})
ALETHEAI = _load("aletheai", {"patents": ["label", "title", "text"]})

NUMBER_WORDS = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}

def fmt_date(iso: str) -> str:
    return datetime.date.fromisoformat(iso).strftime("%-d %b %Y")

def esc(s: str) -> str:
    return H.escape(s, quote=False)

# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS — Umami custom events. ev() returns data-attributes to drop inside any <a ...> tag.
# Events: cta_click, channel_click, framework_open, email_click, writing_open, cv_download
# ─────────────────────────────────────────────────────────────────────────────
def ev(name: str, **props) -> str:
    parts = [f'data-umami-event="{name}"']
    parts += [f'data-umami-event-{k}="{H.escape(str(v), quote=True)}"' for k, v in props.items()]
    return " ".join(parts)

def A(href, text, cls="", event=None, **props):
    """anchor with optional tracked event; external links and PDFs open in a new tab."""
    ext = href.startswith("http") or href.endswith(".pdf")
    attrs = (f' class="{cls}"' if cls else "") + (" " + ev(event, **props) if event else "")
    if ext: attrs += ' target="_blank" rel="noopener"'
    return f'<a href="{href}"{attrs}>{text}</a>'

# ─────────────────────────────────────────────────────────────────────────────
# CSS — design system v2, editorial register for v5
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
:root{--ink:#1A1633;--deep:#2A1B5E;--purple:#5B4BC4;--violet:#8A7BE8;--coral:#F96167;--coral-ink:#B3252B;
--pop:#D9D1FF;--lilac:#F2EFFB;--lilac-2:#EAE6FB;--line:#E3E0F0;--muted:#6E6A8A;--body-ink:#3A3560;--white:#fff;
--grad:linear-gradient(100deg,#5B4BC4 6%,#8A7BE8 46%,#F96167 94%);
--display:'Newsreader',Georgia,serif;--sans:'Archivo',system-ui,-apple-system,sans-serif;
--r:16px;--rs:10px;--max:1180px;--gutter:clamp(16px,4vw,48px)}
*{box-sizing:border-box}html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--white);color:var(--body-ink);font:16px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto}a{color:var(--purple);text-decoration:none}a:hover{text-decoration:underline}
h1,h2,h3{color:var(--ink);font-weight:300;font-family:var(--display);letter-spacing:-.01em;line-height:1.08;margin:0}
h1{font-size:clamp(40px,7vw,84px)}h2{font-size:clamp(30px,4.2vw,50px)}h3{font-size:clamp(22px,2.4vw,28px)}
h1 em,h2 em,h3 em,.grad{font-style:italic;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
p{margin:0 0 1em}strong{color:var(--ink);font-weight:600}
.wrap{max-width:var(--max);margin:0 auto;padding:0 var(--gutter)}
.lab{font:600 11px/1 var(--sans);letter-spacing:.19em;text-transform:uppercase;color:var(--muted)}
.lab.coral{color:var(--coral-ink)}
.num{font-variant-numeric:tabular-nums}
section{padding:clamp(56px,8vw,112px) 0;border-top:1px solid var(--line)}
section.tight{padding:clamp(40px,5vw,72px) 0}
.sh{display:flex;flex-direction:column;gap:14px;margin-bottom:clamp(28px,4vw,48px);max-width:820px}
.sh p.lede{font-size:clamp(17px,1.6vw,20px);color:var(--body-ink);margin:0}
/* nav */
.nav{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.92);backdrop-filter:saturate(1.4) blur(10px);border-bottom:1px solid var(--line)}
.nav .wrap{display:flex;align-items:center;gap:24px;min-height:64px}
.brand{font-family:var(--display);font-size:20px;color:var(--ink);white-space:nowrap}
.brand:hover{text-decoration:none}
.nav ul{display:flex;gap:22px;list-style:none;margin:0 0 0 auto;padding:0}
.nav li a{font-size:14px;font-weight:500;color:var(--body-ink)}
.nav li a[aria-current]{color:var(--purple)}
.nav .cta{margin-left:auto}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:999px;font-weight:600;font-size:14px;line-height:1;
background:var(--ink);color:#fff;border:1px solid var(--ink);white-space:nowrap}
.btn:hover{background:var(--deep);text-decoration:none}
.btn.ghost{background:transparent;color:var(--ink)}.btn.ghost:hover{background:var(--lilac)}
.btn.coral{background:var(--coral);border-color:var(--coral);color:#1A1633}.btn.coral:hover{background:#f74d54}
.btn.sm{padding:9px 14px;font-size:13px}
@media(max-width:760px){.nav ul{display:none}.nav .cta{margin-left:auto}}
/* hero */
.hero{padding:clamp(56px,9vw,128px) 0 clamp(40px,6vw,80px)}
.hero .eyebrow{display:flex;flex-wrap:wrap;gap:8px 20px;margin-bottom:28px}
.hero h1{max-width:12ch}
.hero .sub{font-size:clamp(18px,1.8vw,22px);max-width:56ch;margin:28px 0 36px;color:var(--body-ink)}
.hero .row{display:flex;flex-wrap:wrap;gap:12px}
/* doors */
.doors{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.door{display:block;padding:24px;border:1px solid var(--line);border-radius:var(--r);background:var(--lilac);color:var(--ink);transition:transform .15s,box-shadow .15s}
.door:hover{text-decoration:none;transform:translateY(-2px);box-shadow:0 12px 30px -18px rgba(42,27,94,.35)}
.door .lab{margin-bottom:10px}.door h3{margin-bottom:6px}.door p{margin:0;color:var(--body-ink);font-size:15px}
.door .go{display:block;margin-top:14px;font-weight:600;color:var(--purple)}
/* grids + cards */
.grid{display:grid;gap:18px}.g2{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.g3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}.g2x{grid-template-columns:1fr 1fr}@media(max-width:720px){.g2x{grid-template-columns:1fr}}
.card{border:1px solid var(--line);border-radius:var(--r);padding:26px;background:#fff;display:flex;flex-direction:column;gap:10px;min-width:0}
.card.tint{background:var(--lilac)}.card.dark{background:var(--deep);color:#DDD6F6;border-color:transparent}
.card.dark h3,.card.dark strong{color:#fff}.card.dark .lab{color:var(--pop)}.card.dark a{color:#fff}
.card h3{margin-bottom:2px}.card p{margin:0}.card .foot{margin-top:auto;padding-top:10px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.card .price{font-family:var(--display);font-size:28px;color:var(--ink)}.card .price small{font:500 13px var(--sans);color:var(--muted)}
.line{font-family:var(--display);font-style:italic;font-size:clamp(20px,2vw,24px);color:var(--ink);line-height:1.3}
/* stats */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}
.stat{padding:22px;border-radius:var(--rs);background:var(--lilac)}
.stat b{display:block;font:300 44px/1 var(--display);color:var(--ink);margin-bottom:8px}
.stat span{font-size:14px;color:var(--muted)}
/* testimonial */
.quote{background:var(--deep);color:#EDE9FB;border-radius:var(--r);padding:clamp(28px,4vw,56px);display:grid;gap:28px;grid-template-columns:1.2fr .8fr}
.quote blockquote{margin:0;font:italic 300 clamp(26px,3.2vw,40px)/1.2 var(--display);color:#fff}
.quote blockquote::before{content:'“';color:var(--coral)}
.quote .who{margin-top:22px;font-size:14px;color:#C9C0F0}.quote .who b{display:block;color:#fff;font-weight:600}
.quote .side{display:flex;flex-direction:column;gap:16px;font-size:15px}
.quote .side p{margin:0;padding-left:16px;border-left:2px solid var(--coral);color:#DDD6F6}
.quote .side a{color:#fff;font-weight:600}
@media(max-width:820px){.quote{grid-template-columns:1fr}}
/* tables + lists */
table{width:100%;border-collapse:collapse;font-size:15px}th,td{text-align:left;padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font:600 11px/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:var(--rs)}
.tbl table{min-width:560px}.tbl td,.tbl th{padding:12px 16px}
ul.clean{list-style:none;padding:0;margin:0;display:grid;gap:10px}ul.clean li{padding-left:18px;position:relative}
ul.clean li::before{content:'';position:absolute;left:0;top:.62em;width:8px;height:8px;border-radius:50%;background:var(--violet)}
.yes li::before{background:#2E8B57}.no li::before{background:var(--coral)}
.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--rs);overflow:hidden}
.facts div{background:#fff;padding:18px}.facts .lab{display:block;margin-bottom:6px}@media(max-width:860px){.facts{grid-template-columns:1fr 1fr}}@media(max-width:480px){.facts{grid-template-columns:1fr}}.facts b{font-size:17px;color:var(--ink);font-weight:600}
/* channels */
.chan{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.chan a{display:block;padding:18px 20px;border:1px solid var(--line);border-radius:var(--rs);color:var(--ink)}
.chan a:hover{background:var(--lilac);text-decoration:none}.chan b{display:block;font-weight:600;margin-bottom:4px}.chan span{font-size:14px;color:var(--muted)}
/* prose */
.prose{max-width:72ch}.prose p{font-size:17px}
.two{display:grid;grid-template-columns:1.1fr .9fr;gap:40px}@media(max-width:820px){.two{grid-template-columns:1fr}}
.roles li{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px solid var(--line);font-size:15px}
.roles li span:last-child{color:var(--muted);white-space:nowrap}
/* footer */
footer{background:var(--ink);color:#B9B3D6;padding:64px 0 32px;margin-top:40px}
footer .cols{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px}
footer h4{color:#fff;font:600 11px/1 var(--sans);letter-spacing:.19em;text-transform:uppercase;margin:0 0 14px}
footer ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}footer a{color:#DDD6F6}footer .big{font:italic 300 26px/1.2 var(--display);color:#fff;max-width:22ch;margin:0 0 12px}
footer .base{margin-top:48px;padding-top:20px;border-top:1px solid rgba(255,255,255,.12);font-size:13px;display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between}
@media(max-width:820px){footer .cols{grid-template-columns:1fr 1fr}}@media(max-width:480px){footer .cols{grid-template-columns:1fr}}
/* email toast */
.etoast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%) translateY(12px);z-index:60;display:flex;align-items:center;gap:10px;max-width:min(560px,calc(100vw - 32px));padding:12px 16px;border-radius:999px;background:#1A1633;color:#fff;font:500 14px/1.3 var(--sans);box-shadow:0 18px 40px -18px rgba(26,22,51,.6);opacity:0;pointer-events:none;transition:opacity .22s ease,transform .22s ease}
.etoast.on{opacity:1;transform:translateX(-50%) translateY(0)}
.etoast i{flex:0 0 auto;width:18px;height:18px;border-radius:50%;background:#F96167;display:inline-grid;place-items:center;font-style:normal;font-size:11px;color:#1A1633;font-weight:800}
.etoast b{font-weight:600;white-space:nowrap}
.etoast span{color:#C9C0F0}
@media(prefers-reduced-motion:reduce){.etoast{transition:none}}
@media(max-width:480px){.etoast{width:calc(100vw - 32px);border-radius:14px;align-items:flex-start;padding:12px 14px}.etoast i{margin-top:1px}.etoast b{white-space:normal;overflow-wrap:anywhere}}
.skip{position:absolute;left:-999px;top:0;background:#fff;padding:8px}.skip:focus{left:8px;z-index:99}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""


EXTRA_CSS = """
/* v5 · editorial profile */
.hero h1.name{max-width:16ch}
.entries{display:grid;border-top:1px solid var(--line)}
.entry{display:grid;grid-template-columns:150px minmax(0,1fr) auto;gap:6px 28px;padding:22px 0;border-bottom:1px solid var(--line);align-items:baseline}
.entry time,.entry .when{font:600 12px/1.4 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.entry h3{font-size:clamp(21px,2.1vw,26px)}.entry h3 a{color:var(--ink)}.entry h3 a:hover{color:var(--purple);text-decoration:none}
.entry .dek{margin:8px 0 0;color:var(--body-ink);max-width:68ch}
.entry .meta{font-size:13px;color:var(--muted);white-space:nowrap}
.entry.feature{padding:30px 0}.entry.feature h3{font-size:clamp(26px,3vw,36px)}
@media(max-width:720px){.entry{grid-template-columns:1fr}.entry .meta{white-space:normal}}
.rlist{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.rlist li{display:grid;grid-template-columns:190px minmax(0,1fr);gap:4px 28px;padding:18px 0;border-bottom:1px solid var(--line)}
.rlist .yrs{font:600 12px/1.6 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.rlist b{display:block;color:var(--ink);font-weight:600}.rlist .org{color:var(--purple);font-weight:500}.rlist p{margin:6px 0 0;font-size:15px;max-width:70ch}
@media(max-width:720px){.rlist li{grid-template-columns:1fr}}
.q{counter-increment:q}.q .lab::before{content:"Question 0" counter(q)}
.qgrid{counter-reset:q}
.side h4{margin:0 0 12px}.side ul+h4{margin-top:28px}
.side ul.clean{font-size:15px}
.lang{font:600 12px/1 var(--sans);letter-spacing:.12em;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:8px 10px}
.lang:hover{color:var(--purple);text-decoration:none;border-color:var(--violet)}
.nav .cta{margin-left:0}
@media(max-width:760px){.nav .lang{margin-left:auto}}
@media(max-width:440px){.nav .wrap{gap:10px}.brand{font-size:17px}.nav .btn.sm{padding:8px 11px}}
.status{display:flex;gap:12px;align-items:flex-start;padding:16px 18px;border-radius:var(--rs);background:var(--lilac);font-size:15px;color:var(--ink);max-width:820px}
.status b{flex:0 0 auto;width:10px;height:10px;margin-top:6px;border-radius:50%;background:#2E8B57}
.book{display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center}
.book .cover{width:120px;aspect-ratio:2/3;border-radius:6px;background:var(--grad);display:flex;align-items:flex-end;padding:12px;color:#fff;font:italic 300 17px/1.1 var(--display);box-shadow:0 18px 30px -18px rgba(42,27,94,.6)}
@media(max-width:520px){.book{grid-template-columns:1fr}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# SHARED CHROME
# ─────────────────────────────────────────────────────────────────────────────
NAV = [("/aletheai/", "Aletheai"), ("/writing/", "Writing"), ("/methods/", "Methods"), ("/teaching/", "Teaching"), ("/archive/", "Archive"), ("/contact/", "Contact")]

def analytics() -> str:
    wid = SITE.get("umami_website_id", "").strip()
    return f'<script defer src="{SITE["umami_src"]}" data-website-id="{wid}"></script>' if wid else "<!-- analytics: set SITE['umami_website_id'] in build_site.py -->"

def head(p: dict) -> str:
    url = SITE["domain"] + p["path"]
    og = SITE["domain"] + p.get("og", f"/assets/og/{p['slug']}.png")
    lang = p.get("lang", "en")
    ld = json.dumps(p["jsonld"], ensure_ascii=False, indent=None) if p.get("jsonld") else ""
    robots = '<meta name="robots" content="noindex,follow">' if p.get("noindex") else '<meta name="robots" content="index,follow,max-image-preview:large">'
    alt = ""
    if p["slug"] in ("home", "es"):
        alt = (f'<link rel="alternate" hreflang="en" href="{SITE["domain"]}/">\n'
               f'<link rel="alternate" hreflang="es" href="{SITE["domain"]}/es/">\n'
               f'<link rel="alternate" hreflang="x-default" href="{SITE["domain"]}/">')
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H.escape(p['title'])}</title>
<meta name="description" content="{H.escape(p['description'])}">
<link rel="canonical" href="{url}">
{alt}
{robots}
<meta name="author" content="{SITE['name']}">
<meta name="theme-color" content="#1A1633">
<meta property="og:type" content="{p.get('og_type','website')}">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:locale" content="{'es_ES' if lang == 'es' else SITE['locale']}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{H.escape(p.get('og_title', p['title']))}">
<meta property="og:description" content="{H.escape(p['description'])}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{H.escape(p.get('og_title', p['title']))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{H.escape(p.get('og_title', p['title']))}">
<meta name="twitter:description" content="{H.escape(p['description'])}">
<meta name="twitter:image" content="{og}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/assets/site.webmanifest">
<link rel="preload" href="/assets/fonts/Newsreader-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/Archivo-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<link rel="stylesheet" href="/styles/site.css">
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
<link rel="alternate" type="application/rss+xml" title="Diana Simpson-Hernandez on Substack" href="https://dianasimpsonhernandez.substack.com/feed">
{analytics()}
{('<script type="application/ld+json">'+ld+'</script>') if ld else ''}
</head>
<body>
<a class="skip" href="#main">{'Saltar al contenido' if lang == 'es' else 'Skip to content'}</a>
"""

def nav(active: str, lang: str = "en") -> str:
    CUR = ' aria-current="page"'
    items = "".join(f'<li><a href="{h}"{CUR if h == active else ""}>{t}</a></li>' for h, t in NAV)
    switch = '<a class="lang" href="/" hreflang="en" lang="en">EN</a>' if lang == "es" else '<a class="lang" href="/es/" hreflang="es" lang="es" title="En español">ES</a>'
    return f"""<header class="nav"><div class="wrap">
<a class="brand" href="/">Diana Simpson-Hernandez</a>
<ul>{items}</ul>
{switch}
{A('mailto:'+SITE['email'], 'Email' if lang == 'en' else 'Escribir', 'btn sm cta', 'email_click', position='nav')}
</div></header>
<main id="main">
"""

def channels_block(heading="Where to read and follow", lede="Essays go out on Substack first. LinkedIn carries the shorter notes."):
    cards = "".join(
        f'<a href="{utm(u,"channels",k)}" target="_blank" rel="noopener" {ev("channel_click", channel=k)}><b>{l}</b><span>{b}</span></a>'
        for k, l, u, b, kind in CHANNELS)
    return f"""<section id="channels" class="tight"><div class="wrap">
<div class="sh"><span class="lab">Channels</span><h2>{heading}</h2><p class="lede">{lede}</p></div>
<div class="chan">{cards}</div></div></section>"""

SITE_LINKS = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in [("/", "Home")] + NAV + [("/es/", "En español")])
HOLD_SITE_LINKS = '<li><a href="/">Home (rebuilding)</a></li><li><a href="mailto:' + SITE["email"] + '">Email me</a></li>'

def footer(site_links: str = SITE_LINKS, hold: bool = False) -> str:
    ch = "".join(f'<li><a href="{utm(u,"footer",k)}" target="_blank" rel="noopener" {ev("channel_click", channel=k, position="footer")}>{l}</a></li>' for k, l, u, b, kind in CHANNELS if not hold or k in ("substack", "linkedin"))
    return f"""</main>
<footer><div class="wrap">
<div class="cols">
<div><p class="big">AI that keeps a <em class="grad">record you can open</em>.</p>
<p style="font-size:14px;max-width:38ch">Designer, researcher and founder. Founder &amp; CEO, Aletheai. Lecturer, IED Madrid. FRSA · AFHEA.</p></div>
<div><h4>Site</h4><ul>{site_links}</ul></div>
<div><h4>Work</h4><ul><li><a href="https://aletheai.ai" target="_blank" rel="noopener">Aletheai</a></li>{'' if hold else f'<li><a href="{LIB}/">Framework library</a></li>'}</ul></div>
<div><h4>Channels</h4><ul>{ch}</ul></div>
</div>
<div class="base"><span>© {datetime.date.today().year} Diana Simpson-Hernandez · London</span>
{A('mailto:'+SITE['email'], SITE['email'], '', 'email_click', position='footer')}</div>
</div></footer>
<script>
(function(){{
  var toast;
  function say(addr,copied){{
    if(!toast){{toast=document.createElement('div');toast.className='etoast';toast.setAttribute('role','status');toast.setAttribute('aria-live','polite');document.body.appendChild(toast);}}
    toast.innerHTML='<i>✓</i><div><b>'+addr+'</b> <span>'+(copied?'copied — opening your email app':'— opening your email app')+'</span></div>';
    toast.classList.add('on'); clearTimeout(toast._t); toast._t=setTimeout(function(){{toast.classList.remove('on')}},3800);
  }}
  document.querySelectorAll('a[href^="mailto:"]').forEach(function(a){{
    a.addEventListener('click',function(){{
      var addr=a.getAttribute('href').slice(7).split('?')[0];
      var p=navigator.clipboard&&window.isSecureContext?navigator.clipboard.writeText(addr):Promise.reject();
      p.then(function(){{say(addr,true)}},function(){{say(addr,false)}});
    }});
  }});
}})();
</script>
</body></html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURED DATA
# ─────────────────────────────────────────────────────────────────────────────
PERSON = {
    "@type": "Person", "@id": SITE["domain"] + "/#person",
    "name": "Diana Simpson-Hernandez", "alternateName": "Diana Simpson Hernandez",
    "url": SITE["domain"] + "/", "image": SITE["domain"] + "/assets/dshlogo.png",
    "jobTitle": "Founder & CEO, Aletheai",
    "description": "Designer, researcher and founder. Founder and CEO of Aletheai (behavioural decision intelligence; six patent applications filed). Lecturer at IED Madrid; mentor at London College of Communication (UAL). FRSA, AFHEA.",
    "email": "mailto:" + SITE["email"],
    "knowsLanguage": ["en", "es"],
    "knowsAbout": ["Decision intelligence", "AI governance", "AI assurance", "Behavioural design", "Product design", "Speculative design", "AI-native product development"],
    "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Royal College of Art"}, {"@type": "CollegeOrUniversity", "name": "Central Saint Martins, University of the Arts London"}],
    "memberOf": [{"@type": "Organization", "name": "Royal Society of Arts"}, {"@type": "Organization", "name": "Advance HE (Higher Education Academy)"}],
    "worksFor": {"@type": "Organization", "name": "Aletheai", "url": "https://aletheai.ai"},
    "affiliation": [{"@type": "CollegeOrUniversity", "name": "IED Madrid"}, {"@type": "CollegeOrUniversity", "name": "London College of Communication, University of the Arts London"}],
    "sameAs": [u for k, l, u, b, kind in CHANNELS] + ["https://aletheai.ai", "https://substack.com/@dianasimpsonhernandez"],
}
WEBSITE = {"@type": "WebSite", "@id": SITE["domain"] + "/#website", "url": SITE["domain"] + "/", "name": "Diana Simpson-Hernandez", "publisher": {"@id": SITE["domain"] + "/#person"}, "inLanguage": ["en-GB", "es"]}
ME = {"@id": SITE["domain"] + "/#person"}

def ld_graph(*items):
    return {"@context": "https://schema.org", "@graph": [PERSON, WEBSITE, *items]}

def ld_breadcrumb(*crumbs):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE["domain"] + u} for i, (n, u) in enumerate(crumbs)]}

def abs_url(u: str) -> str:
    return u if u.startswith("http") else SITE["domain"] + u

def ld_writing():
    items = [{"@type": "BlogPosting", "headline": e["title"], "description": e["dek"], "datePublished": e["date"], "url": e["url"], "author": ME} for e in WRITING["essays"]]
    for r in WRITING["research"]:
        t = "Thesis" if "dissertation" in r["kind"].lower() else "Report"
        items.append({"@type": t, "name": r["title"], "description": r["dek"], "datePublished": r["date"], "url": abs_url(r["url"]), "author": ME,
                      **({"inSupportOf": "MA Design Products", "sourceOrganization": {"@type": "CollegeOrUniversity", "name": "Royal College of Art"}} if t == "Thesis" else {})})
    b = WRITING["book"]
    items.append({"@type": "Book", "name": b["title"], "alternativeHeadline": b.get("subtitle", ""), "datePublished": b["date"], "author": ME,
                  "publisher": {"@type": "Organization", "name": b["publisher"]}, "url": b["url"], "bookFormat": "https://schema.org/Paperback"})
    for a in WRITING["audio"]:
        items.append({"@type": "PodcastEpisode", "name": a["title"], "datePublished": a["date"], "url": a["url"], "partOfSeries": {"@type": "PodcastSeries", "name": a["show"]}, "actor": ME})
    return {"@type": "ItemList", "name": "Research and writing", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": it} for i, it in enumerate(items)]}

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────
def hero(lab: str, h1: str, sub: str, buttons: str = "", h1_cls: str = "") -> str:
    return f"""<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">{lab}</span>
<h1 class="{h1_cls}" style="margin-top:14px">{h1}</h1>
<p class="sub">{sub}</p>
{f'<div class="row">{buttons}</div>' if buttons else ''}
</div></section>"""

def section(id_: str, lab: str, h2: str, inner: str, lede: str = "", cls: str = "") -> str:
    return f"""<section id="{id_}"{f' class="{cls}"' if cls else ''}><div class="wrap">
<div class="sh"><span class="lab">{lab}</span><h2>{h2}</h2>{f'<p class="lede">{lede}</p>' if lede else ''}</div>
{inner}
</div></section>"""

def essay_entries(limit: int | None = None, feature_first: bool = False) -> str:
    out = ""
    for i, e in enumerate(sorted(WRITING["essays"], key=lambda x: x["date"], reverse=True)[:limit]):
        feat = " feature" if feature_first and i == 0 else ""
        out += f"""<article class="entry{feat}"><time datetime="{e['date']}">{fmt_date(e['date'])}</time>
<div><h3>{A(e['url'], esc(e['title']), '', 'writing_open', item=e['title'][:40])}</h3><p class="dek">{esc(e['dek'])}</p></div>
<span class="meta">{esc(e['venue'])}{(' · ' + esc(e['read'])) if e.get('read') else ''}</span></article>"""
    return f'<div class="entries">{out}</div>'

def research_entries() -> str:
    out = ""
    for r in sorted(WRITING["research"], key=lambda x: x["date"], reverse=True):
        out += f"""<article class="entry"><span class="when">{esc(r.get('date_label') or fmt_date(r['date']))}</span>
<div><span class="lab coral">{esc(r['kind'])}</span><h3 style="margin-top:8px">{A(r['url'], esc(r['title']), '', 'writing_open', item=r['title'][:40])}</h3><p class="dek">{esc(r['dek'])}</p></div>
<span class="meta">{esc(r['venue'])}{('<br>' + esc(r['meta'])) if r.get('meta') else ''}</span></article>"""
    return f'<div class="entries">{out}</div>'

def audio_entries() -> str:
    out = ""
    for a in sorted(WRITING["audio"], key=lambda x: x["date"], reverse=True):
        out += f"""<article class="entry"><time datetime="{a['date']}">{fmt_date(a['date'])}</time>
<div><h3>{A(a['url'], esc(a['title']), '', 'writing_open', item='podcast')}</h3><p class="dek">{esc(a['show'])}</p></div>
<span class="meta">{esc(a.get('role', ''))}</span></article>"""
    return f'<div class="entries">{out}</div>'

def talk_entries(era: str) -> str:
    rows = sorted((t for t in TALKS if t["era"] == era), key=lambda x: x["date"], reverse=True)
    out = "".join(f"""<article class="entry"><span class="when">{esc(t['when'])}</span>
<div><h3>{esc(t['title'])}</h3><p class="dek">{esc(t['venue'])}</p></div><span class="meta">{esc(t.get('kind', ''))}</span></article>""" for t in rows)
    return f'<div class="entries">{out}</div>'

def role_list(current: bool) -> str:
    li = "".join(f"""<li><span class="yrs">{esc(r['years'])}</span><div><b>{esc(r['role'])}</b><span class="org">{esc(r['org'])}</span><p>{esc(r['detail'])}</p></div></li>"""
                 for r in TEACHING if bool(r.get("current")) == current)
    return f'<ul class="rlist">{li}</ul>'

def question_cards() -> str:
    return '<div class="grid g3 qgrid">' + "".join(
        f'<div class="card q"><span class="lab"></span><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in ALETHEAI["questions"]) + "</div>"

def patent_cards() -> str:
    return '<div class="grid g2x">' + "".join(
        f'<div class="card"><span class="lab">{esc(p["label"])}</span><h3>{esc(p["title"])}</h3><p>{esc(p["text"])}</p></div>' for p in ALETHEAI["patents"]) + "</div>"

def contact_card(heading: str = "Fellowships, research, teaching and leadership roles.") -> str:
    li = "".join(f"<li>{esc(x)}</li>" for x in PROFILE["open_to"])
    return f"""<section id="contact" class="tight"><div class="wrap"><div class="card dark" style="align-items:flex-start">
<span class="lab">Contact · {esc(PROFILE['availability'].lower())}</span><h3 style="font-size:clamp(26px,3vw,38px);max-width:24ch">{heading}</h3>
<ul class="clean" style="margin:6px 0 4px">{li}</ul>
<div class="foot" style="justify-content:flex-start">{A('mailto:'+SITE['email'], 'Email Diana →', 'btn coral', 'email_click', position='contact')}{A(PROFILE['cv'], 'CV (PDF) ↓', 'btn ghost', 'cv_download', position='contact-card')}{A(PROFILE['linkedin'], 'LinkedIn →', 'btn ghost', 'channel_click', channel='linkedin', position='contact')}</div>
</div></div></section>"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE BODIES
# ─────────────────────────────────────────────────────────────────────────────
BIO = [
    "Diana Simpson-Hernandez works where design, behaviour and AI meet: on systems that help people make decisions they can defend afterwards.",
    "She trained in product design at Central Saint Martins and the Royal College of Art, where her MA dissertation, <em>Modern Mythopoeia</em> (2012), argued that the stories a culture tells itself decide which futures get built, and that designers can work on those stories on purpose. The speculative practice turned practical. Glass Lab made surface products from the commercial glass waste of London businesses, and at Shake Your Power she co-designed SPARK, the first energy-generating musical instrument, which was granted a US patent, won two London Design Award Golds and was piloted in schools in the UK, the US and India.",
    "She then spent a decade in product and service design and in teaching. She was Senior Lecturer in Product Design at Nottingham Trent University, and later led the digital design team and product strategy at Slimming World, one of the UK's largest behaviour-change platforms, where the work was keeping more than 250,000 members engaged with a health service week after week.",
    "In December 2024 she founded Aletheai to build the decision layer she kept finding missing: an engine that ranks who deserves attention by the evidence, explains each ranking in plain English, and declines to rank where the evidence runs out. She has filed six patent applications, on the engine and on the governance of AI agents' actions, and ran a feasibility study with the STFC Hartree Centre on real human-behaviour data.",
    "She teaches AI-native product building to MA students at IED Madrid every year, mentors founders at London College of Communication (UAL), and publishes her methods in the open. She is a Fellow of the Royal Society of Arts and an Associate Fellow of the Higher Education Academy, and works in English and Spanish.",
]

def body_home():
    facts = "".join(f'<div><span class="lab">{k}</span><b>{v}</b></div>' for k, v in [
        ("Now", "Founder &amp; CEO, Aletheai"), ("Teaching", "IED Madrid · LCC (UAL)"),
        ("Original work", "Six patent applications filed · one US patent granted"), ("Training", "MA RCA · BA CSM · FRSA · AFHEA")])
    doors = "".join(A(h, f'<span class="lab">{l}</span><h3>{t}</h3><p>{d}</p><span class="go">{g} →</span>', 'door', 'cta_click', kind=k, position='doors') for h, l, t, d, g, k in [
        ("/aletheai/", "Founder", "Aletheai", "Behavioural decision intelligence that states its evidence and its limits. Six patent applications filed.", "The company and the patents", "aletheai"),
        ("/methods/", "Published", "Methods", "LEVER, RECALL, FLYWHEEL, Vibecoding and more, written down in full so anyone can check the reasoning.", "The methods", "methods"),
        ("/teaching/", "Lecturer", "Teaching &amp; talks", "IED Madrid, LCC (UAL), Nottingham Trent; talks at the British Library and the European Commission.", "Teaching and talks", "teaching"),
        ("/archive/", "2012 – 2017", "Archive", "SPARK, Glass Lab, Monogram Publishers, exhibitions and press.", "Earlier work", "archive"),
    ])
    edu = "".join(f"<li>{x}</li>" for x in ["MA Design Products, Royal College of Art", "BA Product Design, Central Saint Martins (UAL)", "MIT xPRO, Designing and Building AI Products and Services", "IDEO U, Service Design · Oxford Saïd, FinTech"])
    mem = "".join(f"<li>{x}</li>" for x in ["FRSA, Royal Society of Arts", "AFHEA, Higher Education Academy", "Education Ambassador, CREATE", "Certified Scrum Master · ILM Level 3 Leadership"])
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<div class="eyebrow"><span class="lab">Diana Simpson-Hernandez</span><span class="lab">Designer · Researcher · Founder</span><span class="lab">London · remote-first</span></div>
<h1 class="name">AI that keeps a <em>record you can open</em>.</h1>
<p class="sub">Diana Simpson-Hernandez is the founder and CEO of Aletheai, a behavioural decision-intelligence company with six patent applications filed. She teaches AI-native product building to MA students at IED Madrid and mentors founders at London College of Communication (UAL).</p>
<div class="row">{A('/writing/', 'Read the writing', 'btn', 'cta_click', kind='writing', position='hero')}{A('/aletheai/', 'About Aletheai', 'btn ghost', 'cta_click', kind='aletheai', position='hero')}{A('#bio', 'Biography ↓', 'btn ghost', 'cta_click', kind='bio', position='hero')}</div>
</div></section>
<section class="tight" style="border-top:0;padding-top:0"><div class="wrap"><div class="facts">{facts}</div></div></section>
{section('research', 'Research', 'Three questions <em>run through the work</em>.', question_cards(), "How a machine should rank people, when it should decline, and what record it owes the people it ranks. The questions come out of building Aletheai; the answers are written up in the patents, the essays and the methods.")}
{section('latest', 'Latest writing', 'From <em>the essays</em>.', essay_entries(3, feature_first=True) + f'<p style="margin-top:22px">{A("/writing/", "All research and writing →", "btn ghost", "cta_click", kind="writing", position="latest")}</p>')}
<section id="doors" class="tight"><div class="wrap"><div class="doors">{doors}</div></div></section>
<section id="bio"><div class="wrap"><div class="two">
<div class="prose"><div class="sh"><span class="lab">Biography</span><h2>Design, behaviour <em>and AI</em>.</h2></div>
{''.join(f'<p>{p}</p>' for p in BIO)}</div>
<div class="side">
<h4 class="lab">Education</h4><ul class="clean">{edu}</ul>
<h4 class="lab">Fellowships and memberships</h4><ul class="clean">{mem}</ul>
<h4 class="lab">Resources</h4><ul class="clean"><li>{A(PROFILE['cv'], 'CV (PDF) ↓', '', 'cv_download', position='bio')}</li><li>{A(PROFILE['linkedin'], 'LinkedIn ↗')}</li><li>{A('https://github.com/dsimpsonh', 'GitHub ↗')}</li><li><a href="/es/" hreflang="es">Perfil en español →</a></li></ul>
</div></div></div></section>
{contact_card()}
"""

def body_aletheai():
    a = ALETHEAI
    partners = "".join(f"<tr><td><strong>{esc(n)}</strong></td><td>{esc(d)}</td></tr>" for n, d in a["partners"])
    btns = "".join(A(u, t + " →", 'btn' if i == 0 else 'btn ghost', 'cta_click', kind='aletheai-link', position='aletheai-hero') for i, (t, u) in enumerate(a["links"]))
    astra = next((e for e in WRITING["essays"] if e.get("featured")), WRITING["essays"][0])
    return f"""
{hero('Aletheai · founder and CEO since December 2024', 'Decisions with the <em>evidence attached</em>.', esc(a['summary']), btns)}
<section class="tight" style="border-top:0;padding-top:0"><div class="wrap"><p class="status"><b></b><span>{esc(a['status'])}</span></p></div></section>
{section('patents', 'Original work', 'Six patent applications. <em>One principle.</em>', patent_cards(), esc(a['patents_line']) + ' A machine decision is only worth the hours it redirects, and it is only followed if it is honest about where it cannot see.')}
{section('questions', 'Research questions', 'What the company <em>is trying to answer</em>.', question_cards())}
{section('partners', 'Research partners and recognition', 'Partners and <em>recognition</em>.', f'<div class="tbl"><table><tbody>{partners}</tbody></table></div>')}
<section class="tight"><div class="wrap"><div class="card tint" style="align-items:flex-start"><span class="lab">Read more</span>
<h3>{esc(astra['title'])}</h3><p style="max-width:70ch">{esc(astra['dek'])}</p>
<div class="foot" style="justify-content:flex-start">{A(astra['url'], 'Read the essay →', 'btn sm', 'writing_open', item='aletheai-page')}</div></div></div></section>
"""

def body_writing():
    b = WRITING["book"]
    book = f"""<div class="card"><div class="book"><div class="cover" aria-hidden="true">The Art of Getting Stuff Done</div>
<div><span class="lab">{esc(b['publisher'])} · {esc(b['format'])}</span><h3 style="margin-top:8px">{esc(b['title'])}</h3><p style="margin-top:6px">{esc(b.get('subtitle', ''))}</p>
<div class="foot" style="justify-content:flex-start">{A(b['url'], 'Find it on Amazon →', 'btn sm ghost', 'writing_open', item='book')}</div></div></div></div>"""
    sub = CH["substack"][2]
    return f"""
{hero('Research &amp; writing', 'Essays, research <em>and a book</em>.', 'Writing on decision intelligence, AI that can be held to account, and how the stories people tell decide what gets designed. New essays go out on Substack first.', A(utm(sub, 'writing-hero', 'substack'), 'Subscribe on Substack →', 'btn', 'channel_click', channel='substack', position='writing-hero'))}
{section('essays', 'Essays', 'On <em>Substack</em>.', essay_entries(feature_first=True))}
{section('research', 'Research and long-form', 'Papers and <em>research documents</em>.', research_entries(), 'From the 2012 MA dissertation on myth and design futures to the research statement behind Aletheai.')}
{section('book', 'Book', 'In <em>print</em>.', book)}
{section('audio', 'Podcasts and interviews', 'On <em>air</em>.', audio_entries())}
{channels_block()}
"""

def body_methods():
    cards = ""
    for m in METHODS["methods"]:
        link = A(LIB + m["url"], 'Read the method →', '', 'framework_open', framework=m['name'].lower()) if m.get("url") else '<span class="lab">In development</span>'
        cards += f"""<div class="card"><span class="lab coral">{esc(m['name'])} · {esc(m['unit'])}</span><p class="line">{esc(m['line'])}</p><p>{esc(m['text'])}</p><div class="foot">{link}</div></div>"""
    tools = "".join(f"""<div class="card tint"><h3>{esc(t['name'])}</h3><p>{esc(t['text'])}</p><div class="foot">{A(LIB + t['url'], 'Open →', '', 'framework_open', framework=t['name'].lower().replace(' ', '-'))}</div></div>""" for t in METHODS["tools"])
    c = METHODS["case"]
    case = f"""<div class="card dark"><span class="lab">Applied</span><h3>{esc(c['name'])}</h3><p>{esc(c['text'])}</p><div class="foot" style="justify-content:flex-start">{A(LIB + c['url'], 'Read the case study →', '', 'framework_open', framework='case-study-language-kids-world')}</div></div>"""
    return f"""
{hero('Methods', 'Methods, published <em>in full</em>.', 'Each method is written down with its instruments and its gates, so anyone can check the reasoning, use it, or argue with it. Several can recommend against building. They live in the open framework library.', A(LIB + '/', 'Open the framework library →', 'btn', 'framework_open', framework='library'))}
{section('methods', 'The methods', f'{NUMBER_WORDS[len(METHODS["methods"])]} methods, <em>one discipline</em>.', f'<div class="grid g2">{cards}</div>', 'Data has no value on its own. Decisions do. Each method starts from a specific decision, question, venture or team and makes it measurably better.')}
{section('tools', 'Tools and a worked example', 'Free tools and <em>a worked example</em>.', f'<div class="grid g2">{tools}{case}</div>')}
"""

def body_teaching():
    return f"""
{hero('Teaching &amp; talks', 'Teaching people to <em>build with AI</em>.', 'Diana has taught design and product for more than a decade, from Senior Lecturer in Product Design at Nottingham Trent University to AI-native product building for MA students at IED Madrid today. Guest lectures, workshops and talks in English or Spanish.', A('mailto:'+SITE['email']+'?subject=Lecture%20or%20talk', 'Invite a lecture or talk →', 'btn', 'email_click', position='teaching-hero'))}
{section('now', 'Current', 'Teaching and <em>mentoring</em>.', role_list(True))}
{section('before', 'Academic posts', 'Earlier <em>academic roles</em>.', role_list(False))}
{section('talks', 'Invited talks and lectures', 'Talks <em>since 2017</em>.', talk_entries('current') + '<p style="margin-top:18px;font-size:15px;color:var(--muted)">Earlier talks (2014–2016), including the European Commission and Central Saint Martins, are in the <a href="/archive/#talks">archive</a>.</p>')}
"""

def body_archive():
    ar = ARCHIVE
    projects = ""
    for p in ar["projects"]:
        links = "".join(A(u, esc(t) + " →", '', 'cta_click', kind='archive-link') for t, u in p.get("links", []))
        projects += f"""<div class="card"><span class="lab">{esc(p['years'])} · {esc(p['role'])}</span><h3>{esc(p['name'])}</h3><p>{esc(p['text'])}</p>{f'<div class="foot">{links}</div>' if links else ''}</div>"""
    def table(rows, cols):
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        head_ = "".join(f"<th>{c}</th>" for c in cols)
        return f'<div class="tbl"><table><thead><tr>{head_}</tr></thead><tbody>{body}</tbody></table></div>'
    awards = table([(esc(y), f"<strong>{esc(a)}</strong>", esc(f)) for y, a, f in ar["awards"]], ["Year", "Award", "For"])
    exh = table([(esc(y), f"<strong>{esc(t)}</strong>", esc(w)) for y, t, w in ar["exhibitions"]], ["Year", "Exhibition", "Where"])
    press = table([(esc(y), f"<strong>{esc(o)}</strong>", A(u, esc(t)) if u else esc(t)) for y, o, t, u in ar["press"]], ["Year", "Outlet", "Piece"])
    return f"""
{hero('Archive · 2012 – 2017', 'Earlier ventures, <em>objects and exhibitions</em>.', 'Before Aletheai: clean-tech education, publishing, recycled materials and speculative design. Different materials, the same question: what makes people change what they do.')}
{section('projects', 'Ventures and projects', 'What came <em>before</em>.', f'<div class="grid g2">{projects}</div>')}
{section('awards', 'Awards', '<em>Recognition</em>.', awards)}
{section('exhibitions', 'Exhibitions', 'Shown at the V&amp;A, Droog <em>and the Museu del Disseny</em>.', exh)}
{section('talks', 'Talks 2014 – 2016', 'Earlier <em>talks</em>.', talk_entries('archive'))}
{section('press', 'Press', 'Written <em>about the work</em>.', press)}
"""

def body_contact():
    facts = "".join(f'<div><span class="lab">{k}</span><b>{v}</b></div>' for k, v in [
        ("Availability", esc(PROFILE["availability"])), ("Location", esc(PROFILE["location"])), ("Languages", "English · Spanish"), ("Right to work", "UK, no sponsorship needed")])
    li = "".join(f"<li>{esc(x)}</li>" for x in PROFILE["open_to"])
    return f"""
{hero('Contact', 'Get in <em>touch</em>.', 'Email is the quickest way to reach Diana. For press, include your deadline; for a lecture or talk, the audience and the date.', A('mailto:'+SITE['email'], 'Email Diana →', 'btn', 'email_click', position='contact-hero') + A(PROFILE['cv'], 'CV (PDF) ↓', 'btn ghost', 'cv_download', position='contact-hero') + A(PROFILE['linkedin'], 'LinkedIn →', 'btn ghost', 'channel_click', channel='linkedin', position='contact-hero'))}
<section class="tight" style="border-top:0;padding-top:0"><div class="wrap"><div class="facts">{facts}</div></div></section>
{section('open', 'Open to', 'What Diana is <em>open to</em>.', f'<ul class="clean" style="font-size:17px;max-width:70ch">{li}</ul>')}
{channels_block('Elsewhere', 'Read the essays, follow the build, or look at the code.')}
"""

def body_es():
    sub = CH["substack"][2]
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<div class="eyebrow"><span class="lab">Diana Simpson-Hernandez</span><span class="lab">Diseñadora · Investigadora · Fundadora</span><span class="lab">Londres · en remoto</span></div>
<h1 class="name">IA que deja un <em>registro que se puede abrir</em>.</h1>
<p class="sub">Diana Simpson-Hernandez es fundadora y CEO de Aletheai, una empresa de inteligencia de decisiones basada en el comportamiento, con seis solicitudes de patente presentadas. Enseña a crear productos con IA a estudiantes de máster en el IED Madrid y es mentora de emprendedores en el London College of Communication (UAL).</p>
<div class="row">{A('mailto:'+SITE['email'], 'Escribir a Diana →', 'btn', 'email_click', position='es-hero')}{A('/aletheai/', 'Aletheai (en inglés)', 'btn ghost', 'cta_click', kind='aletheai', position='es-hero')}</div>
</div></section>
<section id="bio"><div class="wrap"><div class="two">
<div class="prose"><div class="sh"><span class="lab">Biografía</span><h2>Diseño, comportamiento <em>e IA</em>.</h2></div>
<p>Se formó en diseño de producto en Central Saint Martins y en el Royal College of Art de Londres. Su tesis de máster, <em>Modern Mythopoeia</em> (2012), estudia cómo los relatos de una cultura deciden qué futuros se diseñan.</p>
<p>Antes de Aletheai cofundó Shake Your Power, donde diseñó SPARK, el primer instrumento musical que genera energía (patente concedida en Estados Unidos y dos oros en los London Design Awards). Fue profesora titular de Diseño de Producto en la Nottingham Trent University y dirigió el equipo de diseño digital y la estrategia de producto de Slimming World, una de las mayores plataformas de cambio de hábitos del Reino Unido.</p>
<p>Su trabajo actual se centra en sistemas de IA que se pueden auditar: que priorizan con evidencia, explican cada decisión en lenguaje claro y se abstienen cuando la evidencia no alcanza.</p>
<p>Es Fellow de la Royal Society of Arts y Associate Fellow de la Higher Education Academy. Imparte clases, talleres y conferencias en español y en inglés.</p></div>
<div class="side">
<h4 class="lab">Ahora</h4><ul class="clean"><li>Fundadora y CEO, Aletheai</li><li>Profesora de máster, IED Madrid</li><li>Mentora, London College of Communication (UAL)</li></ul>
<h4 class="lab">Leer y contactar</h4><ul class="clean"><li>{A(utm(sub, 'es', 'substack'), 'Ensayos en Substack (en inglés) ↗', '', 'channel_click', channel='substack', position='es')}</li><li>{A(PROFILE['cv'], 'CV en PDF (en inglés) ↓', '', 'cv_download', position='es')}</li><li>{A(PROFILE['linkedin'], 'LinkedIn ↗')}</li><li><a href="/" hreflang="en">English version →</a></li></ul>
</div></div></div></section>
"""

def body_404():
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">404</span>
<h1 style="margin-top:14px">That page <em>moved</em>.</h1>
<p class="sub">The site was rebuilt in 2026 as a research and teaching profile. Pick where you were heading.</p>
<div class="doors" style="margin-top:20px">
<a class="door" href="/writing/"><span class="lab">Reading</span><h3>Research &amp; writing</h3><span class="go">Essays and papers →</span></a>
<a class="door" href="/aletheai/"><span class="lab">The company</span><h3>Aletheai</h3><span class="go">Patents and research →</span></a>
<a class="door" href="{LIB}/"><span class="lab">Looking for a framework</span><h3>The library</h3><span class="go">Every method →</span></a>
</div></div></section>
"""

HOLD_LINES = ["$ dsh rebuild site --v5", "reading the brief ......... ok", "design system ............. ok",
              "writing the pages ......... in progress", "checking every claim ...... in progress",
              "frameworks ................ polishing", "projects .................. upcoming", "publish ................... soon"]

def body_hold():
    chans = "".join(f'<a class="hchan" href="{u}" target="_blank" rel="noopener" {ev("cta_click", kind=k, position="hold")}><span class="lab">{H.escape(kind)}</span><b>{H.escape(label)}</b><span>{H.escape(blurb)}</span></a>'
                    for k, label, u, blurb, kind in CHANNELS if k in ("substack", "linkedin"))
    ribbon = "".join("<span>Rebuilding</span><i>✦</i><span>Upcoming</span><i>✦</i><span>Back soon</span><i>✦</i>" for _ in range(6))
    return f"""
<div class="hold-ribbon-clip" aria-hidden="true"><div class="hold-ribbon"><div class="hold-ribbon-track">{ribbon}</div></div></div>
<section class="hold"><div class="wrap hold-grid">
<div class="hold-copy">
<div class="hold-top"><img class="hold-mark" src="/assets/mark-ink.svg" alt="" width="46" height="46"><span class="hold-pill"><b></b>rebuilding</span></div>
<span class="lab">Diana Simpson-Hernandez · site v5</span>
<h1>I'm rebuilding <em>this site.</em></h1>
<p class="sub">New pages, same work: AI decision intelligence, designed in public with the limits stated. While the paint dries, I'm writing on Substack and LinkedIn.</p>
<div class="row">
{A('https://linkedin.com/in/dianasimpson', 'Find me on LinkedIn →', 'btn', 'cta_click', kind='linkedin', position='hold')}
{A('mailto:' + SITE['email'], 'Email me', 'btn ghost', 'email_click', position='hold')}
</div>
</div>
<div class="hold-term" aria-label="Build log, illustrative"><div class="hold-term-bar"><i></i><i></i><i></i><span>rebuild.log</span></div><pre id="hold-log" data-lines='{json.dumps(HOLD_LINES)}'></pre></div>
</div>
<div class="wrap hold-chans">{chans}</div>
<div class="hold-blob a" aria-hidden="true"></div><div class="hold-blob b" aria-hidden="true"></div>
</section>
<script>
(function(){{var el=document.getElementById('hold-log');if(!el)return;var lines=JSON.parse(el.dataset.lines),NL=String.fromCharCode(10);
if(matchMedia('(prefers-reduced-motion: reduce)').matches){{el.textContent=lines.join(NL);return;}}
var li=0,ci=0,out='';function tick(){{if(li>=lines.length){{el.innerHTML=out+'<span class="cur">▍</span>';return;}}
var L=lines[li];if(ci<=L.length){{el.innerHTML=out+L.slice(0,ci)+'<span class="cur">▍</span>';ci++;setTimeout(tick,L[ci-2]==='.'?12:28);}}
else{{out+=L+NL;li++;ci=0;setTimeout(tick,L.indexOf('$')===0?500:260);}}}}
setTimeout(tick,600);}})();
</script>
"""

HOLD_CSS = """
/* HOLD MODE */
.hold{position:relative;overflow:hidden;padding:clamp(56px,9vw,120px) 0 clamp(48px,7vw,96px);min-height:calc(100vh - 160px)}
.hold-grid{position:relative;z-index:2;display:grid;grid-template-columns:1.15fr .85fr;gap:clamp(28px,5vw,64px);align-items:center}
@media(max-width:860px){.hold-grid{grid-template-columns:1fr}}
.hold-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:26px}
.hold-mark{width:46px;height:46px;animation:hbob 4s ease-in-out infinite}
.hold-pill{font:600 11px/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:var(--coral-ink);border:1px solid #FFC9CB;background:#FFF0F0;border-radius:999px;padding:9px 14px;display:inline-flex;align-items:center;gap:8px}
.hold-pill b{width:8px;height:8px;border-radius:50%;background:var(--coral);animation:hpulse 1.6s ease-out infinite}
.hold-copy h1{max-width:11ch;margin-top:14px}
.hold-copy .sub{font-size:clamp(17px,1.7vw,21px);max-width:52ch;margin:24px 0 28px}
.hold-copy .row{display:flex;flex-wrap:wrap;gap:12px}
.hold-term{background:var(--ink);color:var(--pop);border-radius:var(--r);overflow:hidden;box-shadow:0 30px 60px -30px rgba(26,22,51,.5);transform:rotate(1deg)}
.hold-term-bar{display:flex;align-items:center;gap:7px;padding:12px 14px;background:var(--deep);font:600 11px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--pop)}
.hold-term-bar i{width:10px;height:10px;border-radius:50%;background:var(--coral)}.hold-term-bar i:nth-child(2){background:#F9C74F}.hold-term-bar i:nth-child(3){background:#7BE8A6}
.hold-term-bar span{margin-left:auto;opacity:.7}
.hold-term pre{margin:0;padding:18px 20px 20px;font:500 13px/1.8 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre;overflow-x:auto;min-height:14.4em}
.hold-term .cur{color:var(--coral);animation:hblink 1s steps(1) infinite}
.hold-chans{position:relative;z-index:2;display:grid;grid-template-columns:repeat(2,minmax(0,380px));gap:12px;margin-top:clamp(40px,6vw,72px)}
@media(max-width:560px){.hold-chans{grid-template-columns:1fr}}
.hchan{display:grid;gap:6px;padding:18px;border:1px solid var(--line);border-radius:var(--rs);background:rgba(255,255,255,.8);color:var(--body-ink);font-size:14px;transition:transform .25s,border-color .25s}
.hchan b{font-family:var(--display);font-weight:400;font-size:24px;color:var(--ink)}.hchan:hover{text-decoration:none;transform:translateY(-3px);border-color:var(--violet)}
.hold-ribbon-clip{overflow:hidden;position:relative;z-index:3}
.hold-ribbon{background:var(--coral);color:#fff;overflow:hidden;font:700 12px/1 var(--sans);letter-spacing:.22em;text-transform:uppercase;padding:11px 0;transform:rotate(-1.2deg) scale(1.04);position:relative;z-index:3}
.hold-ribbon-track{display:inline-flex;gap:28px;white-space:nowrap;animation:hmarquee 40s linear infinite;padding-left:28px}.hold-ribbon i{font-style:normal;color:var(--pop)}
.hold-blob{position:absolute;border-radius:50%;filter:blur(70px);opacity:.8;z-index:1;pointer-events:none}
.hold-blob.a{width:50vw;height:50vw;max-width:640px;max-height:640px;left:-14vw;top:-8vw;background:var(--pop);animation:hdrift 18s ease-in-out infinite alternate}
.hold-blob.b{width:40vw;height:40vw;max-width:520px;max-height:520px;right:-10vw;bottom:-10vw;background:#FFD9DA;animation:hdrift 22s ease-in-out infinite alternate-reverse}
@keyframes hmarquee{to{transform:translateX(-50%)}}@keyframes hbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px) rotate(-3deg)}}
@keyframes hpulse{0%{box-shadow:0 0 0 0 rgba(249,97,103,.55)}100%{box-shadow:0 0 0 12px rgba(249,97,103,0)}}@keyframes hblink{50%{opacity:0}}
@keyframes hdrift{to{transform:translate(6vw,4vw) scale(1.08)}}
@media(prefers-reduced-motion:reduce){.hold-ribbon-track,.hold-mark,.hold-pill b,.hold-blob,.hold-term .cur{animation:none}}
"""

HOLD_PAGE = {"slug": "hold", "path": "/", "file": "index.html", "nav": "/",
    "title": "Diana Simpson-Hernandez — rebuilding the site",
    "og_title": "I'm rebuilding this site.",
    "description": "Diana Simpson-Hernandez — designer, researcher and founder of Aletheai. The site is being rebuilt; Substack and LinkedIn are open.",
    "jsonld": None, "og": "/assets/og/home.png"}

def build_hold():
    write("styles/site.css", CSS.strip() + "\n" + EXTRA_CSS.strip() + "\n" + HOLD_CSS.strip() + "\n")
    html = head(HOLD_PAGE) + '<main id="main">\n' + body_hold() + footer(HOLD_SITE_LINKS, hold=True)
    write("index.html", html); print(f"  ✓ index.html (HOLD) {len(html)//1024} KB")
    nf = dict(HOLD_PAGE, path="/404.html", file="404.html", noindex=True, title="Page moved — Diana Simpson-Hernandez")
    write("404.html", head(nf) + '<main id="main">\n' + body_hold() + footer(HOLD_SITE_LINKS, hold=True)); print("  ✓ 404.html (HOLD)")
    for d in PAGE_DIRS + LEGACY_DIRS:
        if os.path.isdir(os.path.join(OUT, d)): shutil.rmtree(os.path.join(OUT, d)); print(f"  – removed {d}/")
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE["domain"]}/</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url></urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE['domain']}/sitemap.xml\nSitemap: {LIB}/sitemap.xml\n")
    print("  ✓ sitemap.xml (root only), robots.txt")

# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────
PAGES = [
    {"slug": "home", "path": "/", "file": "index.html", "nav": "/",
     "title": "Diana Simpson-Hernandez — designer, researcher and founder of Aletheai",
     "og_title": "AI that keeps a record you can open.",
     "description": "Diana Simpson-Hernandez is the founder and CEO of Aletheai (behavioural decision intelligence; six patent applications filed), a lecturer at IED Madrid and a mentor at LCC (UAL). Research, writing, methods and teaching.",
     "jsonld": ld_graph({"@type": "ProfilePage", "mainEntity": ME, "url": SITE["domain"] + "/"}),
     "body": body_home, "og_kicker": "Diana Simpson-Hernandez", "og_sub": "Designer · researcher · founder of Aletheai · lecturer, IED Madrid"},
    {"slug": "aletheai", "path": "/aletheai/", "file": "aletheai/index.html", "nav": "/aletheai/",
     "title": "Aletheai — behavioural decision intelligence | Diana Simpson-Hernandez",
     "og_title": "Decisions with the evidence attached.",
     "description": "Aletheai ranks who deserves attention by the evidence, explains every ranking in plain English, and declines to rank where the evidence runs out. Six patent applications filed. Founded by Diana Simpson-Hernandez.",
     "jsonld": ld_graph({"@type": "Organization", "name": "Aletheai", "url": "https://aletheai.ai", "founder": ME, "foundingDate": "2024-12"}, ld_breadcrumb(("Home", "/"), ("Aletheai", "/aletheai/"))),
     "body": body_aletheai, "og_kicker": "Aletheai", "og_sub": "Behavioural decision intelligence · six patent applications filed"},
    {"slug": "writing", "path": "/writing/", "file": "writing/index.html", "nav": "/writing/",
     "title": "Research & writing — essays, papers and a book | Diana Simpson-Hernandez",
     "og_title": "Essays, research and a book.",
     "description": "Essays on decision intelligence and accountable AI, the RCA dissertation Modern Mythopoeia (2012), the Aletheai research notice, The Art of Getting Stuff Done (2022) and podcast appearances.",
     "jsonld": ld_graph(ld_writing(), ld_breadcrumb(("Home", "/"), ("Writing", "/writing/"))),
     "body": body_writing, "og_kicker": "Research & writing", "og_sub": "Essays · papers · a book · podcasts"},
    {"slug": "methods", "path": "/methods/", "file": "methods/index.html", "nav": "/methods/",
     "title": "Methods — LEVER, RECALL, FLYWHEEL, Vibecoding | Diana Simpson-Hernandez",
     "og_title": "Methods, published in full.",
     "description": "Decision diagnostics, corpus readiness, venture diagnostics and AI-native building for non-engineers. Published in full in the open framework library, with a worked example.",
     "jsonld": ld_graph(ld_breadcrumb(("Home", "/"), ("Methods", "/methods/"))),
     "body": body_methods, "og_kicker": "Methods", "og_sub": "LEVER · RECALL · STAKE · FLYWHEEL · Vibecoding"},
    {"slug": "teaching", "path": "/teaching/", "file": "teaching/index.html", "nav": "/teaching/",
     "title": "Teaching & talks — IED Madrid, LCC (UAL) | Diana Simpson-Hernandez",
     "og_title": "Teaching people to build with AI.",
     "description": "Lecturer at IED Madrid (MA programmes), mentor at London College of Communication (UAL), former Senior Lecturer in Product Design at Nottingham Trent University. Invited talks and lectures in English and Spanish.",
     "jsonld": ld_graph(ld_breadcrumb(("Home", "/"), ("Teaching", "/teaching/"))),
     "body": body_teaching, "og_kicker": "Teaching & talks", "og_sub": "IED Madrid · LCC (UAL) · English and Spanish"},
    {"slug": "archive", "path": "/archive/", "file": "archive/index.html", "nav": "/archive/",
     "title": "Archive 2012–2017 — SPARK, Glass Lab, Monogram | Diana Simpson-Hernandez",
     "og_title": "Earlier ventures, objects and exhibitions.",
     "description": "Shake Your Power and SPARK (US patent, two London Design Award Golds), Glass Lab / Trash Surface Bureau, Monogram Publishers, RCA fictional objects, exhibitions, talks and press, 2012–2017.",
     "jsonld": ld_graph(ld_breadcrumb(("Home", "/"), ("Archive", "/archive/"))),
     "body": body_archive, "og_kicker": "Archive · 2012 – 2017", "og_sub": "SPARK · Glass Lab · Monogram · exhibitions and press"},
    {"slug": "contact", "path": "/contact/", "file": "contact/index.html", "nav": "/contact/",
     "title": "Contact | Diana Simpson-Hernandez",
     "og_title": "Get in touch.",
     "description": f"Fellowships, research collaborations, leadership roles, lectures and talks. {PROFILE['availability']}. London, remote-first. English and Spanish.",
     "jsonld": ld_graph({"@type": "ContactPage", "url": SITE["domain"] + "/contact/", "about": ME}, ld_breadcrumb(("Home", "/"), ("Contact", "/contact/"))),
     "body": body_contact, "og_kicker": "Contact", "og_sub": "Fellowships · research · teaching · leadership roles"},
    {"slug": "es", "path": "/es/", "file": "es/index.html", "nav": "", "lang": "es",
     "title": "Diana Simpson-Hernandez — diseñadora, investigadora y fundadora de Aletheai",
     "og_title": "IA que deja un registro que se puede abrir.",
     "description": "Diana Simpson-Hernandez es fundadora y CEO de Aletheai, profesora de máster en el IED Madrid y mentora en el London College of Communication (UAL).",
     "jsonld": ld_graph({"@type": "ProfilePage", "mainEntity": ME, "url": SITE["domain"] + "/es/", "inLanguage": "es"}),
     "body": body_es, "og_kicker": "Diana Simpson-Hernandez", "og_sub": "Diseñadora · investigadora · fundadora de Aletheai · IED Madrid"},
    {"slug": "404", "path": "/404.html", "file": "404.html", "nav": "", "noindex": True,
     "title": "Page not found | Diana Simpson-Hernandez", "og_title": "That page moved.",
     "description": "The page you were looking for has moved. Find the writing, Aletheai and the framework library.",
     "jsonld": None, "body": body_404, "og": "/assets/og/home.png"},
]
PAGE_DIRS = sorted({os.path.dirname(p["file"]) for p in PAGES if os.path.dirname(p["file"])})
LEGACY_DIRS = ["contract", "work-with-me", "learn", "speaking"]   # v4 pages; removed on every build

# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────
def write(rel: str, content: str):
    path = os.path.join(OUT, rel); os.makedirs(os.path.dirname(path) or OUT, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: f.write(content)
    os.replace(tmp, path)
    assert os.path.getsize(path) > 0, rel

def build_pages():
    for d in LEGACY_DIRS:
        if os.path.isdir(os.path.join(OUT, d)): shutil.rmtree(os.path.join(OUT, d)); print(f"  – removed legacy {d}/")
    for p in PAGES:
        html = head(p) + nav(p["nav"], p.get("lang", "en")) + p["body"]() + footer()
        write(p["file"], html); print(f"  ✓ {p['file']:26} {len(html)//1024} KB")

def build_sitemap():
    urls = "".join(f"<url><loc>{SITE['domain']}{p['path']}</loc><lastmod>{TODAY}</lastmod><changefreq>{'weekly' if p['slug'] in ('home', 'writing') else 'monthly'}</changefreq><priority>{'1.0' if p['slug']=='home' else '0.8'}</priority></url>"
                   for p in PAGES if not p.get("noindex"))
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE['domain']}/sitemap.xml\nSitemap: {LIB}/sitemap.xml\n")
    print("  ✓ sitemap.xml, robots.txt")

def build_css():
    write("styles/site.css", CSS.strip() + "\n" + EXTRA_CSS.strip() + "\n"); print("  ✓ styles/site.css")

def copy_static():
    """--preview only: mirror the static files the pages reference into _preview/."""
    for name in ("assets", "favicon.ico", "CNAME"):
        src = os.path.join(ROOT, name); dst = os.path.join(OUT, name)
        if os.path.isdir(src): shutil.copytree(src, dst, dirs_exist_ok=True)
        elif os.path.exists(src): shutil.copy2(src, dst)
    print("  ✓ static files copied")

def validate():
    """non-zero output + every internal href resolves to a generated file or a static asset."""
    import re
    for p in PAGES: assert os.path.getsize(os.path.join(OUT, p["file"])) > 4000, p["file"]
    bad = []
    for p in PAGES:
        html = open(os.path.join(OUT, p["file"]), encoding="utf-8").read()
        for href in re.findall(r'href="(/[^"#?]*)', html):
            target = os.path.join(OUT, href.lstrip("/"))
            if href.endswith("/"): target = os.path.join(target, "index.html")
            if not os.path.exists(target) and not os.path.exists(os.path.join(ROOT, href.lstrip("/"))): bad.append((p["file"], href))
    assert not bad, f"broken internal links: {bad}"
    print("  ✓ validation: sizes and internal links")

OG_TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Newsreader';font-style:normal;font-weight:300 500;src:url('data:font/woff2;base64,__NR__') format('woff2')}
@font-face{font-family:'Newsreader';font-style:italic;font-weight:300 500;src:url('data:font/woff2;base64,__NRI__') format('woff2')}
@font-face{font-family:'Archivo';font-style:normal;font-weight:400 700;src:url('data:font/woff2;base64,__AR__') format('woff2')}
body{margin:0;width:1200px;height:630px;background:#1A1633;color:#fff;font-family:'Archivo',sans-serif;position:relative;overflow:hidden}
.bar{position:absolute;left:0;top:0;width:1200px;height:14px;background:linear-gradient(100deg,#5B4BC4 6%,#8A7BE8 46%,#F96167 94%)}
.k{position:absolute;left:72px;top:72px;font:600 20px Archivo;letter-spacing:.2em;text-transform:uppercase;color:#D9D1FF}
.t{position:absolute;left:72px;top:150px;width:1000px;font:300 __SIZE__px/1.06 'Newsreader';letter-spacing:-.01em;color:#fff}
.t em{font-style:italic;background:linear-gradient(100deg,#8A7BE8 0%,#F96167 100%);-webkit-background-clip:text;color:transparent}
.s{position:absolute;left:72px;bottom:120px;width:980px;font:400 26px/1.35 Archivo;color:#C9C0F0}
.d{position:absolute;left:72px;bottom:56px;font:600 18px Archivo;letter-spacing:.14em;text-transform:uppercase;color:#fff}
.d span{color:#F96167}
</style></head><body><div class="bar"></div><div class="k">__KICKER__</div><div class="t">__TITLE__</div><div class="s">__SUB__</div><div class="d">dianasimpsonhernandez.com <span>·</span> Diana Simpson-Hernandez</div></body></html>"""

def build_og():
    from playwright.sync_api import sync_playwright
    import base64
    fonts = os.path.join(ROOT, "assets", "fonts"); out = os.path.join(ROOT, "assets", "og"); os.makedirs(out, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
        for p in PAGES:
            if p.get("og"): continue
            t = p["og_title"]
            # italicise the last two words for the gradient accent
            words = t.rstrip(".").split(" "); accent = " ".join(words[-2:]); lead = " ".join(words[:-2])
            title = f"{lead} <em>{accent}</em>." if lead else f"<em>{accent}</em>."
            size = 92 if len(t) < 34 else 72
            b64 = lambda n: base64.b64encode(open(os.path.join(fonts, n), "rb").read()).decode()
            html = (OG_TEMPLATE.replace("__NR__", b64("Newsreader-var.woff2")).replace("__NRI__", b64("Newsreader-var-italic.woff2")).replace("__AR__", b64("Archivo-var.woff2"))
                    .replace("__KICKER__", H.escape(p["og_kicker"]))
                    .replace("__TITLE__", title).replace("__SUB__", H.escape(p["og_sub"])).replace("__SIZE__", str(size)))
            pg.set_content(html, wait_until="load"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
            pg.screenshot(path=os.path.join(out, f"{p['slug']}.png"), type="png")
            print(f"  ✓ assets/og/{p['slug']}.png")
        b.close()

if __name__ == "__main__":
    if "--preview" in sys.argv:
        OUT = os.path.join(ROOT, "_preview"); os.makedirs(OUT, exist_ok=True)
        print(f"building dianasimpsonhernandez.com — PREVIEW into {OUT}")
        build_css(); build_pages(); build_sitemap(); copy_static(); validate()
        print("done — run:  python3 -m http.server 8000 -d _preview   then open http://localhost:8000"); sys.exit(0)
    if "--hold" in sys.argv:
        print("building dianasimpsonhernandez.com — HOLD MODE"); build_hold()
        assert os.path.getsize(os.path.join(ROOT, "index.html")) > 4000; print("done"); sys.exit(0)
    print("building dianasimpsonhernandez.com — LIVE")
    build_css(); build_pages(); build_sitemap()
    if "--og" in sys.argv: build_og()
    validate()
    print("done")
