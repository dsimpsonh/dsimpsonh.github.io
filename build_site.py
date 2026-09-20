#!/usr/bin/env python3
"""
build_site.py — single source of truth for dianasimpsonhernandez.com

    python3 build_site.py            # regenerate every page + sitemap + robots + 404
    python3 build_site.py --og       # also re-render the 1200×630 OG cards (needs playwright)

Edit copy, fees, links or nav in the CONFIG / COPY blocks below, run, commit.
Every page is generated from the same head(), nav() and footer(), so SEO tags,
structured data and the analytics snippet cannot drift between pages.
"""
from __future__ import annotations
import json, os, sys, datetime, html as H

ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
SITE = {
    "domain":   "https://dianasimpsonhernandez.com",
    "name":     "Diana Simpson-Hernandez",
    "short":    "DSH",
    "email":    "dianasimpsonhernandez@gmail.com",
    "tagline":  "I design the decision layer.",
    "locale":   "en_GB",
    # Umami Cloud (free): one website covers both hosts. Paste the Website ID from cloud.umami.is → Settings → Websites.
    # Leave empty and NO analytics script is emitted — nothing ships half-configured.
    "umami_website_id": "a98055b4-17b2-4091-b09e-3b3b5b34b4ad",
    "umami_src": "https://cloud.umami.is/script.js",
}
LIB = "https://frameworks.dianasimpsonhernandez.com"

CONTRACT = {
    "availability": "Available now",
    "day_rate": "£650–850",
    "ir35": "Outside — via DiSH Creative Ltd",
    "pattern": "2–4 days a week · 2–6 months",
    "location": "London · remote-first",
    "right_to_work": "UK (no sponsorship needed)",
    "languages": "English · Spanish",
    "cv": "/assets/dsh-contract-cv.pdf",           # 2-page ATS-safe contract CV (DOCX beside it)
    "cv_docx": "/assets/dsh-contract-cv.docx",
    "cv_full": "/assets/diana_simpson-hernandez_CV.pdf",   # 8-page portfolio CV for bio + speaking
}

def utm(url: str, medium: str, campaign: str) -> str:
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=dsh-site&utm_medium={medium}&utm_campaign={campaign}"

CHANNELS = [
    # key, label, url, blurb, kind
    ("youtube",   "YouTube",   "https://www.youtube.com/@DianaSimpsonHernandez", "Teaching videos — one framework, one build, one lesson a week.", "video"),
    ("instagram", "Instagram", "https://www.instagram.com/diana.simpson.hernandez/", "Short-form: what I'm building, in public.", "social"),
    ("substack",  "Substack",  "https://substack.com/@dianasimpsonhernandez", "Long-form essays on decision intelligence, AI strategy and the creator economy.", "writing"),
    ("skool",     "Skool",     "https://www.skool.com/@diana-simpson-hernandez-4490", "REWIRED — the free community and the paid courses.", "community"),
    ("linkedin",  "LinkedIn",  "https://linkedin.com/in/dianasimpson", "Founder field notes and product breakdowns.", "social"),
    ("podcast",   "Stand Out", "https://standoutpodcast.com", "The podcast — innovation, creativity and the publishing path.", "audio"),
    ("github",    "GitHub",    "https://github.com/dsimpsonh", "Open frameworks and code in public.", "code"),
]
CH = {c[0]: c for c in CHANNELS}

# Paid ladder lives on Skool. Prices as published in the Distribution Stack — confirm they match Skool before pushing.
COURSES = [
    {"slug": "rewired-community", "name": "REWIRED — the community", "price": "Free", "price_num": 0, "cadence": "",
     "for": "Operators rewiring the defaults that stop them building AI-native businesses.",
     "what": "Weekly teaching video, the framework library, and the room where the builds get reviewed.",
     "url": CH["skool"][2], "cta": "Join free"},
    {"slug": "flywheel-masterclass", "name": "Flywheel Masterclass", "price": "£39", "price_num": 39, "cadence": "one-off",
     "for": "Founders who need to know which of the eight dimensions is dragging the business.",
     "what": "90 minutes on the FLYWHEEL canvas, scored live, with the Godmode coaching prompt built from your own evidence.",
     "url": CH["skool"][2], "cta": "Buy the masterclass"},
    {"slug": "build-room", "name": "Build Room", "price": "£39", "price_num": 39, "cadence": "/month",
     "for": "Non-engineers shipping real software with AI.",
     "what": "Monthly membership around the Vibecoding protocol — live build sessions, code review, and the 20-step checklist run every week.",
     "url": CH["skool"][2], "cta": "Join the Build Room"},
    {"slug": "ship-it-cohort", "name": "Ship It — the cohort", "price": "£997", "price_num": 997, "cadence": "per cohort",
     "for": "One idea, one cohort, one live URL at the end.",
     "what": "Four weeks: worthy problem → research → build → ship. You leave with a deployed product and a pitch.",
     "url": CH["skool"][2], "cta": "Apply for the next cohort"},
    {"slug": "founder-mentorship", "name": "Founder Mentorship", "price": "£3,500", "price_num": 3500, "cadence": "per quarter",
     "for": "Founders who want the decision layer of their business designed with them, not for them.",
     "what": "Fortnightly 1:1, async review between sessions, and the LEVER instruments applied to your own operation.",
     "url": CH["skool"][2], "cta": "Enquire"},
]

METHODS = [
    {"slug": "lever", "name": "LEVER", "unit": "The unit is a decision",
     "line": "Align the goal. Expose the friction. Sequence the fix.",
     "prop": "For operations businesses that have bought AI and can't prove it worked. LEVER prices the friction in every recurring decision, then builds the one tool that recovers it — in the one sequence that doesn't break something downstream.",
     "url": f"{LIB}/lever/", "fee": "Diagnostic £32,000 · Build from £45,000"},
    {"slug": "recall", "name": "RECALL", "unit": "The unit is a question",
     "line": "Ask first. Score the corpus. Earn the right to build.",
     "prop": "A retrieval system cannot be better than the corpus it retrieves from — and nobody measures the corpus before quoting the build. RECALL does, in four to five weeks, and will recommend against building if the numbers say so.",
     "url": f"{LIB}/recall/", "fee": "Diagnostic £34,000 · Build from £55,000"},
    {"slug": "stake", "name": "STAKE", "unit": "The unit is a revenue stream",
     "line": "I build it. I run it. You sell it.",
     "prop": "For a business that owns a vertical and needs a product it can't build. I build and run it on a royalty plus a service fee; you keep around 82% and sell to the market you already stand in.",
     "url": f"{LIB}/stake/", "fee": "Royalty 5–18% · Service fee 3–12%"},
]

FREE = [  # free resources — the library
    ("REWIRED", "Build the operator before you build the company. A 12-minute diagnostic and a protocol you'll run for life.", f"{LIB}/REWIRED/"),
    ("The Flywheel", "Score your business on eight dimensions in twenty minutes. See where the drag is.", f"{LIB}/flywheel/"),
    ("Vibecoding", "From a worthy problem to a live URL — the 20-step protocol non-engineers use to ship real software with AI.", f"{LIB}/vibecoding/"),
    ("The Rediscovery Canvas", "A five-layer canvas for finding your uniquely human edge after a transition.", f"{LIB}/rediscovery-canvas/"),
    ("TeamScale", "Build an AI-native team. Don't over-hire. Roles, benchmarks and the 12-month roadmap.", f"{LIB}/teamscale/"),
    ("The full library", "Every framework, method and case study, versioned and forkable.", f"{LIB}/"),
]

TESTIMONIAL = {
    "who": "Vanessa", "role": "Founder & CEO, Language Kids World", "where": "Houston, Texas",
    "org": "Language Kids World",
    "pull": "Months of my time back, and a product business I didn't know I had.",
    "quotes": [
        "I was the bottleneck for a sixty-person delivery team and didn't know it. Diana built the automations that took curriculum development from weeks to hours and gave me back months of my year. For the first time I'm working on the business instead of inside it.",
        "What I expected was time savings. What I got was time savings and two new revenue lines. While automating our operations Diana saw that the tools we needed were tools the whole industry needed — so we built them as products.",
        "She found a security problem in our systems that nobody had asked her to look for, and fixed it before it cost us.",
    ],
    "outcomes": [("92%", "less curriculum-development time"), ("10–15", "working weeks a year returned to the founder"), ("2", "new product revenue lines"), ("60", "people freed from one bottleneck")],
    "case_url": f"{LIB}/case-study-language-kids-world/",
}

# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS — Umami custom events. ev() returns data-attributes to drop inside any <a ...> tag.
# Events appear automatically in the Umami dashboard: cta_click, course_click, channel_click, framework_open, email_click
# ─────────────────────────────────────────────────────────────────────────────
def ev(name: str, **props) -> str:
    parts = [f'data-umami-event="{name}"']
    parts += [f'data-umami-event-{k}="{H.escape(str(v), quote=True)}"' for k, v in props.items()]
    return " ".join(parts)

def A(href, text, cls="", event=None, **props):
    """anchor with optional tracked event; external links open in a new tab."""
    ext = href.startswith("http")
    attrs = (f' class="{cls}"' if cls else "") + (" " + ev(event, **props) if event else "")
    if ext: attrs += ' target="_blank" rel="noopener"'
    return f'<a href="{href}"{attrs}>{text}</a>'

# ─────────────────────────────────────────────────────────────────────────────
# CSS — design system v2, "the site speaks" register
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
.grid{display:grid;gap:18px}.g2{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.g3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
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
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--rs);overflow:hidden}
.facts div{background:#fff;padding:18px}.facts .lab{margin-bottom:6px}.facts b{font-size:17px;color:var(--ink);font-weight:600}
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

# ─────────────────────────────────────────────────────────────────────────────
# SHARED CHROME
# ─────────────────────────────────────────────────────────────────────────────
NAV = [("/work-with-me/", "Work with me"), ("/learn/", "Learn"), (f"{LIB}/", "Frameworks"), ("/speaking/", "Speaking"), ("/#bio", "Bio")]

def analytics() -> str:
    wid = SITE.get("umami_website_id", "").strip()
    return f'<script defer src="{SITE["umami_src"]}" data-website-id="{wid}"></script>' if wid else "<!-- analytics: set SITE['umami_website_id'] in build_site.py -->"

def head(p: dict) -> str:
    url = SITE["domain"] + p["path"]
    og = SITE["domain"] + p.get("og", f"/assets/og/{p['slug']}.png")
    ld = json.dumps(p["jsonld"], ensure_ascii=False, indent=None) if p.get("jsonld") else ""
    robots = '<meta name="robots" content="noindex,follow">' if p.get("noindex") else '<meta name="robots" content="index,follow,max-image-preview:large">'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H.escape(p['title'])}</title>
<meta name="description" content="{H.escape(p['description'])}">
<link rel="canonical" href="{url}">
{robots}
<meta name="author" content="{SITE['name']}">
<meta name="theme-color" content="#1A1633">
<meta property="og:type" content="{p.get('og_type','website')}">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:locale" content="{SITE['locale']}">
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
{analytics()}
{('<script type="application/ld+json">'+ld+'</script>') if ld else ''}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""

def nav(active: str) -> str:
    CUR = ' aria-current="page"'
    items = "".join(f'<li><a href="{h}"{CUR if h == active else ""}>{t}</a></li>' for h, t in NAV)
    return f"""<header class="nav"><div class="wrap">
<a class="brand" href="/">Diana Simpson-Hernandez</a>
<ul>{items}</ul>
{A('mailto:'+SITE['email'], 'Contact', 'btn sm cta', 'email_click', position='nav')}
</div></header>
<main id="main">
"""

def channels_block(heading="Where to find me", lede="The site is the index. The work happens on the channels."):
    cards = "".join(
        f'<a href="{utm(u,"channels",k)}" target="_blank" rel="noopener" {ev("channel_click", channel=k)}><b>{l}</b><span>{b}</span></a>'
        for k, l, u, b, kind in CHANNELS)
    return f"""<section id="channels" class="tight"><div class="wrap">
<div class="sh"><span class="lab">Channels</span><h2>{heading}</h2><p class="lede">{lede}</p></div>
<div class="chan">{cards}</div></div></section>"""

def footer() -> str:
    ch = "".join(f'<li><a href="{utm(u,"footer",k)}" target="_blank" rel="noopener" {ev("channel_click", channel=k, position="footer")}>{l}</a></li>' for k, l, u, b, kind in CHANNELS)
    return f"""</main>
<footer><div class="wrap">
<div class="cols">
<div><p class="big">Designing the systems where <em class="grad">signal becomes decision</em>.</p>
<p style="font-size:14px;max-width:38ch">Founder &amp; CEO, Aletheai. Fractional Chief AI Officer. Educator. FRSA · AFHEA.</p></div>
<div><h4>Site</h4><ul><li><a href="/work-with-me/">Work with me</a></li><li><a href="/contract/">Contract</a></li><li><a href="/learn/">Learn</a></li><li><a href="/speaking/">Speaking</a></li><li><a href="/#bio">Bio</a></li></ul></div>
<div><h4>Ventures</h4><ul><li><a href="https://aletheai.ai" target="_blank" rel="noopener">Aletheai</a></li><li><a href="{LIB}/">Frameworks</a></li><li><a href="https://monogrampublishers.com" target="_blank" rel="noopener">Monogram Publishers</a></li><li><a href="https://standoutpodcast.com" target="_blank" rel="noopener">Stand Out</a></li></ul></div>
<div><h4>Channels</h4><ul>{ch}</ul></div>
</div>
<div class="base"><span>© {datetime.date.today().year} Diana Simpson-Hernandez · London · Texas</span>
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
    "jobTitle": "Founder & CEO, Aletheai · Fractional Chief AI Officer",
    "description": "Founder of Aletheai, a patent-pending behavioural decision-intelligence engine. Fractional Chief AI Officer, educator at IED Madrid and LCC (UAL), FRSA.",
    "email": "mailto:" + SITE["email"],
    "knowsLanguage": ["en", "es"],
    "knowsAbout": ["Decision intelligence", "AI strategy", "Behavioural prediction", "UX strategy", "Machine learning consulting", "AI-native operating models"],
    "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Royal College of Art"}, {"@type": "CollegeOrUniversity", "name": "Central Saint Martins"}],
    "memberOf": [{"@type": "Organization", "name": "Royal Society of Arts"}, {"@type": "Organization", "name": "Advance HE (Higher Education Academy)"}],
    "worksFor": {"@type": "Organization", "name": "Aletheai", "url": "https://aletheai.ai"},
    "sameAs": [u for k, l, u, b, kind in CHANNELS] + ["https://aletheai.ai", "https://monogrampublishers.com"],
}
WEBSITE = {"@type": "WebSite", "@id": SITE["domain"] + "/#website", "url": SITE["domain"] + "/", "name": "Diana Simpson-Hernandez", "publisher": {"@id": SITE["domain"] + "/#person"}, "inLanguage": "en-GB"}

def ld_graph(*items):
    return {"@context": "https://schema.org", "@graph": [PERSON, WEBSITE, *items]}

def ld_course(c):
    offer = {"@type": "Offer", "price": str(c["price_num"]), "priceCurrency": "GBP", "availability": "https://schema.org/InStock", "url": c["url"], "category": "Paid" if c["price_num"] else "Free"}
    return {"@type": "Course", "name": c["name"], "description": c["for"] + " " + c["what"], "url": c["url"],
            "provider": {"@type": "Person", "@id": SITE["domain"] + "/#person"},
            "offers": offer, "inLanguage": "en",
            "hasCourseInstance": [{"@type": "CourseInstance", "courseMode": "online", "courseWorkload": "PT2H" if c["price_num"] < 100 else "PT20H"}]}

LD_REVIEW = {
    "@type": "Service", "name": "AI automation and decision-intelligence consulting", "provider": {"@id": SITE["domain"] + "/#person"},
    "areaServed": ["GB", "ES", "US"],
    "review": {"@type": "Review", "author": {"@type": "Person", "name": TESTIMONIAL["who"]},
               "reviewBody": TESTIMONIAL["quotes"][0], "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"},
               "publisher": {"@type": "Organization", "name": TESTIMONIAL["org"]}},
}

def ld_breadcrumb(*crumbs):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE["domain"] + u} for i, (n, u) in enumerate(crumbs)]}

# ─────────────────────────────────────────────────────────────────────────────
# PAGE BODIES
# ─────────────────────────────────────────────────────────────────────────────
def methods_cards(compact=False):
    out = ""
    for m in METHODS:
        out += f"""<div class="card">
<span class="lab coral">{m['name']} · {m['unit']}</span>
<p class="line">{m['line']}</p>
<p>{m['prop']}</p>
<div class="foot"><span class="lab num">{m['fee']}</span>{A(m['url'], 'Read the method →', '', 'framework_open', framework=m['slug'])}</div>
</div>"""
    return out

def course_cards():
    out = ""
    for c in COURSES:
        price = f'<span class="price num">{c["price"]}{("<small> "+c["cadence"]+"</small>") if c["cadence"] else ""}</span>'
        out += f"""<div class="card{' tint' if c['price_num']==0 else ''}">
<span class="lab">{'Free' if c['price_num']==0 else 'Paid course'}</span>
<h3>{c['name']}</h3>
<p><strong>For:</strong> {c['for']}</p>
<p>{c['what']}</p>
<div class="foot">{price}{A(utm(c['url'],'courses',c['slug']), c['cta']+' →', 'btn sm'+('' if c['price_num'] else ' ghost'), 'course_click', course=c['slug'], price=c['price_num'])}</div>
</div>"""
    return out

def free_cards():
    return "".join(f"""<div class="card tint"><h3>{n}</h3><p>{d}</p><div class="foot">{A(u, 'Open →', '', 'framework_open', framework=n.lower().replace(' ','-'))}</div></div>""" for n, d, u in FREE)

def testimonial_block():
    t = TESTIMONIAL
    side = "".join(f"<p>{q}</p>" for q in t["quotes"][1:])
    outcomes = "".join(f'<div class="stat"><b class="num">{n}</b><span>{l}</span></div>' for n, l in t["outcomes"])
    return f"""<section id="proof"><div class="wrap">
<div class="sh"><span class="lab">Proof</span><h2>What it looks like when the <em>bottleneck moves</em>.</h2></div>
<div class="quote">
<div><blockquote>{t['quotes'][0]}</blockquote>
<div class="who"><b>{t['who']}</b>{t['role']} · {t['where']}</div></div>
<div class="side">{side}{A(t['case_url'], 'Read the case study →', '', 'framework_open', framework='case-study-language-kids-world')}</div>
</div>
<div class="stats" style="margin-top:18px">{outcomes}</div>
</div></section>"""

def body_home():
    doors = f"""<section class="tight" id="doors"><div class="wrap"><div class="doors">
{A('/work-with-me/', '<span class="lab">Buying a project</span><h3>Work with me</h3><p>Fixed-fee diagnostics and builds. LEVER, RECALL and STAKE — methods you can read before you hire me.</p><span class="go">See the methods and fees →</span>', 'door', 'cta_click', kind='work-with-me', position='doors')}
{A('/learn/', '<span class="lab">Learning to build</span><h3>Learn</h3><p>Free frameworks, the YouTube channel, and the paid courses on Skool — from a £39 masterclass to a shipped product.</p><span class="go">Courses and free resources →</span>', 'door', 'cta_click', kind='learn', position='doors')}
{A('/contract/', '<span class="lab">Hiring on contract</span><h3>Contract</h3><p>Day-rate work inside your company: AI adoption, strategy, governance, enablement. Facts first, then the fit.</p><span class="go">Availability and rate →</span>', 'door', 'cta_click', kind='contract', position='doors')}
</div></div></section>"""
    stats = """<div class="stats">
<div class="stat"><b class="num">4</b><span>ventures founded or co-founded across AI, publishing, clean-tech and design</span></div>
<div class="stat"><b class="num">2</b><span>patents — granted (US) and pending (UK)</span></div>
<div class="stat"><b class="num">2</b><span>London Design Award Golds</span></div>
<div class="stat"><b class="num">250K+</b><span>members on platforms I've led design for</span></div></div>"""
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<div class="eyebrow"><span class="lab">Vol. 02 / 2026</span><span class="lab">London · Texas</span><span class="lab">FRSA · AFHEA · CREATE Ambassador</span></div>
<h1>I design the <em>decision layer</em>.</h1>
<p class="sub">Founder &amp; CEO of Aletheai, a patent-pending behavioural decision-intelligence engine. I build AI systems, I consult on the decisions they should improve, and I teach operators to ship their own — in public, with methods you can check before you pay for them.</p>
<div class="row">{A('/work-with-me/', 'Work with me', 'btn', 'cta_click', kind='work-with-me', position='hero')}{A('/learn/', 'Learn to build', 'btn ghost', 'cta_click', kind='learn', position='hero')}{A(utm(CH['youtube'][2],'hero','youtube'), 'Watch on YouTube', 'btn ghost', 'channel_click', channel='youtube', position='hero')}</div>
</div></section>
{doors}
<section id="what"><div class="wrap">
<div class="sh"><span class="lab">What I do</span><h2>Three things, <em>one discipline</em>.</h2><p class="lede">Data has no value. Decisions have value. Everything below is about making a specific decision measurably better — in a product, in a company, or in the person building one.</p></div>
<div class="grid g3">
<div class="card"><span class="lab">Build</span><h3>Aletheai</h3><p>The UK's first multi-signal behavioural prediction engine for estate agents. Patent-pending. In pilot with Alto (Zoopla Group).</p><div class="foot">{A('https://aletheai.ai','aletheai.ai →','', 'cta_click', kind='aletheai')}</div></div>
<div class="card"><span class="lab">Consult</span><h3>Decision diagnostics</h3><p>Three published methods — LEVER, RECALL, STAKE — each with a paid diagnostic that can recommend against building. Fixed fees, engine-neutral, no day rate.</p><div class="foot">{A('/work-with-me/','Methods and fees →','', 'cta_click', kind='work-with-me', position='what')}</div></div>
<div class="card"><span class="lab">Teach</span><h3>Courses and community</h3><p>Lecturer at IED Madrid, mentor at LCC (UAL), and the REWIRED community on Skool — where non-engineers learn to ship real software with AI.</p><div class="foot">{A('/learn/','Learn →','', 'cta_click', kind='learn', position='what')}</div></div>
</div></div></section>
<section id="methods"><div class="wrap">
<div class="sh"><span class="lab">Methods</span><h2>Read the method <em>before</em> you hire me.</h2><p class="lede">Nobody sends a consultant's method ahead of the consultant. These are published in full — instruments, equations, gates and prices — so you can check the reasoning before the first call.</p></div>
<div class="grid g3">{methods_cards()}</div>
<p style="margin-top:18px;font-size:15px;color:var(--muted)">Routing question, asked in the first meeting: <em style="color:var(--ink)">“When this goes wrong, is it because someone chose badly, or because someone couldn't find out?”</em> Chose badly → LEVER. Couldn't find out → RECALL. Neither, but you own a vertical → STAKE.</p>
</div></section>
{testimonial_block()}
<section id="learn"><div class="wrap">
<div class="sh"><span class="lab">Learn</span><h2>From a <em>worthy problem</em> to a live URL.</h2><p class="lede">Free frameworks for everyone. Paid courses on Skool for people who want the build reviewed. The ladder starts at nothing and ends with a shipped product.</p></div>
<div class="grid g3">{course_cards()}</div>
<div class="sh" style="margin-top:56px"><span class="lab">Free resources</span><h3>The open library</h3></div>
<div class="grid g3">{free_cards()}</div>
</div></section>
{channels_block()}
<section id="work"><div class="wrap">
<div class="sh"><span class="lab">The work</span><h2>Ventures, bodies of work, <em>output</em>.</h2></div>
{stats}
<div class="grid g2" style="margin-top:18px">
<div class="card"><span class="lab">№ 01 · Shipping</span><h3>Aletheai</h3><p>Patent-pending decision intelligence for PropTech. Pilot with Alto (Zoopla Group). 10,000+ agent distribution pathway.</p><div class="foot"><a href="https://aletheai.com" target="_blank" rel="noopener">Visit aletheai.com →</a></div></div>
<div class="card"><span class="lab">№ 02 · Open</span><h3>Open Frameworks</h3><p>An open library of frameworks, methods and case studies distilled from fifteen years of building. Versioned. Forkable.</p><div class="foot"><a href="{LIB}/">Browse the library →</a></div></div>
<div class="card"><span class="lab">№ 03 · 2014 —</span><h3>Monogram Publishers</h3><p>Independent publishing for the creator-entrepreneur economy. Books, podcasts and digital content. Home of the Stand Out podcast.</p><div class="foot"><a href="https://monogrampublishers.com" target="_blank" rel="noopener">Visit Monogram →</a></div></div>
<div class="card"><span class="lab">№ 04 · 2022</span><h3>The Art of Getting Stuff Done</h3><p>Fifteen strategies to integrate into your life, accomplish your goals and achieve success. Amazon paperback, Monogram Publishers.</p><div class="foot"><a href="https://www.amazon.com/dp/B09Z6DVXQB" target="_blank" rel="noopener">Read on Amazon →</a></div></div>
</div></div></section>
<section id="teaching"><div class="wrap">
<div class="sh"><span class="lab">Teaching</span><h2>I also <em>teach</em>.</h2><p class="lede">Building the next generation of AI-native operators — in classrooms, workshops and accelerators across the UK and Europe.</p></div>
<ul class="clean roles">
<li><span><strong>Lecturer · IED Madrid</strong> — tech and AI in design education</span><span>2026 —</span></li>
<li><span><strong>Mentor · Venture &amp; Business Coach</strong> — London College of Communication (UAL)</span><span>2026 —</span></li>
<li><span><strong>Judge · LCC Accelerate 2026</strong> — early-stage venture panel, NatWest Accelerator</span><span>2026</span></li>
<li><span><strong>Education Ambassador · CREATE</strong> — creative, STEM and entrepreneurship education across the UK</span><span>Ongoing</span></li>
<li><span><strong>Senior Lecturer (former) · Nottingham Trent University</strong> — Product Design, curriculum lead BSc Year 1</span><span>2017–2019</span></li>
<li><span><strong>Guest Lecturer</strong> — European Commission · RCA · Central Saint Martins · UCL Academy · Hertfordshire · V&amp;A</span><span>2014 —</span></li>
</ul>
<p style="margin-top:22px">{A('/speaking/', 'Book a talk or a workshop →', 'btn ghost', 'cta_click', kind='speaking', position='teaching')}</p>
</div></section>
<section id="bio"><div class="wrap"><div class="two">
<div class="prose"><div class="sh"><span class="lab">Long bio</span><h2>15 years · 4 ventures · <em>2 patents</em>.</h2></div>
<p>I work at the seam where emerging technology meets commercial outcome — and where decisions become reality.</p>
<p>Today I'm Founder &amp; CEO of <strong>Aletheai</strong>, building the UK's first patent-pending, multi-signal behavioural prediction engine for estate agents. We've secured a strategic partnership and live pilot with Alto (Zoopla Group), unlocking distribution to 10,000+ agents.</p>
<p>Before Aletheai I built three other ventures — <strong>Monogram Publishers</strong> (independent publishing, founded 2014), <strong>Shake Your Power</strong> (clean-tech education, which I co-founded; US patent, two London Design Award Golds) and <strong>Glass Lab / Trash Surface Bureau</strong> (sustainable design, FRAME Magazine feature). I led design teams of 12+ at Slimming World's 250K-member platform, served as Senior Lecturer at Nottingham Trent University, and have lectured, judged, mentored and exhibited internationally — including at the V&amp;A, Royal College of Art, European Commission and London College of Communication.</p>
<p>I'm a Fellow of the Royal Society of Arts, Associate Fellow of the Higher Education Academy and Education Ambassador for CREATE. I write on Substack, teach on YouTube and Skool, and my playbook lives on Amazon.</p></div>
<div>
<h4 class="lab" style="margin:0 0 14px">Roles</h4>
<ul class="clean roles"><li><span>Founder &amp; CEO, Aletheai</span><span>2024 —</span></li><li><span>Founder &amp; CEO, Monogram</span><span>2014 —</span></li><li><span>Fractional Chief AI Officer</span><span>Available</span></li><li><span>Lecturer, IED Madrid</span><span>2026 —</span></li><li><span>Mentor, LCC (UAL)</span><span>2026 —</span></li></ul>
<h4 class="lab" style="margin:28px 0 14px">Memberships</h4>
<ul class="clean"><li>FRSA · Royal Society of Arts Fellow</li><li>AFHEA · Higher Education Academy Associate</li><li>ILM Level 3 Leadership</li><li>CREATE Ambassador</li></ul>
<h4 class="lab" style="margin:28px 0 14px">Resources</h4>
<ul class="clean"><li>{A(CONTRACT['cv_full'], 'Download CV (PDF) ↓', '', 'cta_click', kind='cv', position='bio')}</li><li><a href="https://linkedin.com/in/dianasimpson" target="_blank" rel="noopener">LinkedIn ↗</a></li><li><a href="https://github.com/dsimpsonh" target="_blank" rel="noopener">GitHub ↗</a></li></ul>
</div></div></div></section>
<section id="contact" class="tight"><div class="wrap"><div class="card dark" style="align-items:flex-start">
<span class="lab">Contact</span><h3 style="font-size:clamp(26px,3vw,38px)">Need a Fractional CAIO, a diagnostic, or a speaker?</h3>
<p>Aletheai pilots, AI advisory, board-level strategy, guest lectures — one email, and I'll tell you in a paragraph whether I'm the right person.</p>
<div class="foot" style="justify-content:flex-start">{A('mailto:'+SITE['email'], 'Email me →', 'btn coral', 'email_click', position='contact')}{A('https://linkedin.com/in/dianasimpson', 'LinkedIn →', 'btn ghost', 'channel_click', channel='linkedin', position='contact')}</div>
</div></div></section>
"""

def body_work():
    ladder = [
        ("Friction Teardown", "Free", "30-minute call. I tell you which method fits, or that neither does."),
        ("Product & Portfolio Review", "£750", "One product or portfolio, one written verdict, one call."),
        ("AI Working Session", "£1,950", "Half-day with your leadership team on one decision."),
        ("AI for Leaders", "£3,500", "One-day executive session: what to build, buy, or leave alone."),
        ("Build Without Permission", "£8,500", "Four sessions taking one operator from idea to shipped internal tool. £7,000 repeat."),
        ("The Scan", "£6,500", "Two-week pre-diagnostic. Credited in full against any diagnostic below."),
        ("LEVER Diagnostic", "£32,000", "Four weeks. Goal Ladder, Decision Blueprint, Friction Index, Leverage Equation, sequenced plan."),
        ("RECALL Diagnostic", "£34,000", "Four to five weeks. Question Ledger, Corpus Condition Index, gold set, Answerability Equation."),
        ("Programme Diagnostic", "£55,000", "Both methods across one operation, one plan."),
        ("Corpus Remediation", "from £28,000", "The RECALL finding turned into a purchase order rather than an apology."),
        ("LEVER Build", "from £45,000", "12–18% of L£. The one tool the diagnostic priced."),
        ("RECALL Build", "from £55,000", "16–24% of A£. Retrieval people can rely on."),
        ("Run retainer", "from £5,500 /mo", "Monitoring, drift, quarterly regression, published quality report."),
    ]
    rows = "".join(f"<tr><td><strong>{n}</strong></td><td class=\"num\">{p}</td><td>{d}</td></tr>" for n, p, d in ladder)
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">Work with me · buying a project</span>
<h1 style="margin-top:14px">Fixed fees. Published methods. <em>No day rate.</em></h1>
<p class="sub">Every engagement starts with a paid diagnostic that can recommend against building — which is exactly why clients say yes to it. The methods are public, so you can check the reasoning before the first call.</p>
<div class="row">{A('mailto:'+SITE['email']+'?subject=Friction%20Teardown', 'Book the free Friction Teardown', 'btn', 'email_click', position='work-hero')}{A('/contract/', 'Hiring on contract instead? →', 'btn ghost', 'cta_click', kind='contract', position='work-hero')}</div>
</div></section>
<section id="methods"><div class="wrap">
<div class="sh"><span class="lab">Three methods</span><h2>One routing question decides <em>which</em>.</h2><p class="lede">“When this goes wrong, is it because someone chose badly, or because someone couldn't find out?” Chose badly → LEVER. Couldn't find out → RECALL. Neither, but you own a vertical and need a product → STAKE.</p></div>
<div class="grid g3">{methods_cards()}</div>
</div></section>
<section id="fees"><div class="wrap">
<div class="sh"><span class="lab">Fees</span><h2>The <em>ladder</em>.</h2><p class="lede">Start anywhere. Everything above the Scan is credited against the diagnostic it leads to. Prices exclude VAT.</p></div>
<div class="tbl"><table><thead><tr><th>Engagement</th><th class="num">Fee</th><th>What you get</th></tr></thead><tbody>{rows}</tbody></table></div>
</div></section>
<section id="guards"><div class="wrap"><div class="two">
<div class="prose"><div class="sh"><span class="lab">Guarantees</span><h2>What every engagement <em>holds to</em>.</h2></div>
<ul class="clean">
<li><strong>Engine-neutral.</strong> Standard open-source tooling only. None of Aletheai's core, none of its behavioural primitives, in any client build.</li>
<li><strong>Honest gates.</strong> LQ &lt; 3, AQ &lt; 3, no gold set, no outcome labels — each one stops the build and says so in writing.</li>
<li><strong>Your data stays yours.</strong> Gold sets and ledgers are client data and never travel between engagements.</li>
<li><strong>Sequenced, not ranked.</strong> You get the shortest safe order of changes, not a list of ideas.</li>
<li><strong>Not property, not wealth.</strong> Those are Aletheai's verticals; I don't consult in them.</li>
</ul></div>
<div class="card dark"><span class="lab">Proof</span><h3>Language Kids World, Houston</h3><p>Ten full-time staff, fifty contract teachers, one founder as the single-threaded dependency. 92% less curriculum-development time, 10–15 working weeks a year returned, two product revenue lines created.</p><div class="foot" style="justify-content:flex-start">{A(TESTIMONIAL['case_url'], 'Read the case study →', '', 'framework_open', framework='case-study-language-kids-world')}</div></div>
</div></div></section>
<section id="contact" class="tight"><div class="wrap"><div class="card tint" style="align-items:flex-start">
<span class="lab">Start</span><h3>Thirty minutes, free, and I'll tell you which method fits — or that neither does.</h3>
<div class="foot" style="justify-content:flex-start">{A('mailto:'+SITE['email']+'?subject=Friction%20Teardown', 'Book the Friction Teardown →', 'btn', 'email_click', position='work-contact')}</div>
</div></div></section>
"""

def body_contract():
    c = CONTRACT
    facts = "".join(f'<div><span class="lab">{k}</span><b>{v}</b></div>' for k, v in [
        ("Availability", c["availability"]), ("Day rate", c["day_rate"]), ("IR35", c["ir35"]), ("Pattern", c["pattern"]),
        ("Location", c["location"]), ("Right to work", c["right_to_work"]), ("Delivery languages", c["languages"]), ("Company", "DiSH Creative Ltd (UK)")])
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">Contract · hiring inside your company</span>
<h1 style="margin-top:14px">The answers to your <em>first message</em>, first.</h1>
<p class="sub">Day-rate work inside other people's companies. Below is what a recruiter or hiring manager asks in the first email, answered before you send it.</p>
</div></section>
<section class="tight" style="border-top:0"><div class="wrap"><div class="facts">{facts}</div>
<p style="margin-top:14px;font-size:14px;color:var(--muted)">Prices are for contract roles only. Project work is priced as fixed-fee diagnostics on {A('/work-with-me/','the work-with-me page')} and never as a day rate.</p></div></section>
<section id="roles"><div class="wrap">
<div class="sh"><span class="lab">Role shapes</span><h2>Four shapes I take. <em>One I don't.</em></h2></div>
<div class="grid g2">
<div class="card"><span class="lab">01</span><h3>AI adoption &amp; change</h3><p>Taking a team from “we bought the licence” to “we can show the board which decision got better, and by how much”.</p></div>
<div class="card"><span class="lab">02</span><h3>AI strategy</h3><p>Fractional Chief AI Officer. What to build, buy or leave alone — with the Leverage Equation applied to your own backlog.</p></div>
<div class="card"><span class="lab">03</span><h3>Governance &amp; assurance</h3><p>Decision ledgers, gold sets, trust discounts. The evidence trail that lets an AI system survive an audit.</p></div>
<div class="card"><span class="lab">04</span><h3>Literacy &amp; enablement</h3><p>Teaching operators to ship their own tools. Curriculum, workshops, and the Vibecoding protocol inside your company.</p></div>
</div>
<div class="grid g2" style="margin-top:18px">
<div class="card tint"><span class="lab">A brief is a fit if</span><ul class="clean yes"><li>The outcome is a decision that gets measurably better</li><li>There is data with recorded outcomes, or a corpus someone needs answers from</li><li>A named sponsor owns the result</li><li>2–4 days a week, 2–6 months, outside IR35</li></ul></div>
<div class="card tint"><span class="lab">It is not a fit if</span><ul class="clean no"><li>The role is pure ML engineering with no decision owner</li><li>The deliverable is a slide deck about AI, with nothing to ship</li><li>It's inside IR35, five days a week, or open-ended</li><li>It's in property or wealth management</li></ul></div>
</div></div></section>
<section id="thirty"><div class="wrap"><div class="two">
<div class="prose"><div class="sh"><span class="lab">First thirty days</span><h2>The method, <em>applied in-house</em>.</h2></div>
<p><strong>Week 1 — Goal Ladder.</strong> One goal, in the board's words, with its number attached. Signed before anything is mapped.</p>
<p><strong>Weeks 2–3 — Blueprint and Ledger.</strong> Every recurring decision, who owns it, what's recorded, and a Friction Index scored from observation, not interviews.</p>
<p><strong>Week 4 — Sequenced plan.</strong> The shortest safe order of changes, priced with the Leverage Equation, with the things I'd leave alone named as clearly as the things I'd build.</p>
<p>It's {A(f'{LIB}/lever/','LEVER','', 'framework_open', framework='lever')} and {A(f'{LIB}/recall/','RECALL','', 'framework_open', framework='recall')}, run from the inside. Read them first; that's what they're for.</p></div>
<div>
<div class="card dark"><span class="lab">Recent delivery</span><h3>Language Kids World, Houston</h3><p>AI automations across a 60-person delivery organisation. 92% less curriculum-development time; 10–15 working weeks a year returned to the founder; a security breach found unprompted; two product revenue lines created.</p><div class="foot" style="justify-content:flex-start">{A(TESTIMONIAL['case_url'],'Case study →','', 'framework_open', framework='case-study-language-kids-world')}</div></div>
<div class="card" style="margin-top:14px"><span class="lab">Engagement routes</span><ul class="clean"><li><strong>Associate bench</strong> — via your consultancy, on your paper</li><li><strong>Agency PSL</strong> — through your preferred supplier list</li><li><strong>Direct SOW</strong> — statement of work with DiSH Creative Ltd</li></ul></div>
</div></div></div></section>
<section id="contact" class="tight"><div class="wrap"><div class="card tint" style="align-items:flex-start">
<span class="lab">Next step</span><h3>Send the brief. I reply within one working day with a yes, a no, or the question that decides it.</h3>
<div class="foot" style="justify-content:flex-start">{A('mailto:'+SITE['email']+'?subject=Contract%20brief', 'Send a brief →', 'btn', 'email_click', position='contract')}{A(c['cv'], 'Contract CV (PDF) ↓', 'btn ghost', 'cta_click', kind='cv', position='contract')}{A(c['cv_docx'], 'Word version ↓', 'btn ghost', 'cta_click', kind='cv-docx', position='contract')}{A('https://linkedin.com/in/dianasimpson', 'LinkedIn →', 'btn ghost', 'channel_click', channel='linkedin', position='contract')}</div>
</div></div></section>
"""

def body_learn():
    yt = CH["youtube"]; ig = CH["instagram"]; sub = CH["substack"]
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">Learn · courses and free resources</span>
<h1 style="margin-top:14px">Learn to build the <em>decision layer</em> yourself.</h1>
<p class="sub">Everything here runs on one idea: skip a step and the next one gets harder. The free frameworks give you the steps. The courses give you the room where the work gets reviewed.</p>
<div class="row">{A(utm(CH['skool'][2],'learn-hero','skool'), 'Join REWIRED free', 'btn', 'course_click', course='rewired-community', price=0)}{A(utm(yt[2],'learn-hero','youtube'), 'Watch on YouTube', 'btn ghost', 'channel_click', channel='youtube', position='learn-hero')}</div>
</div></section>
<section id="courses"><div class="wrap">
<div class="sh"><span class="lab">Courses · on Skool</span><h2>The <em>ladder</em>.</h2><p class="lede">Start free. Pay only when you want your build in front of me. Every paid tier includes the one below it.</p></div>
<div class="grid g3">{course_cards()}</div>
</div></section>
<section id="free"><div class="wrap">
<div class="sh"><span class="lab">Free resources</span><h2>The <em>open library</em>.</h2><p class="lede">Interactive frameworks, methods and case studies. No sign-up, no paywall. Read them, run them, fork them.</p></div>
<div class="grid g3">{free_cards()}</div>
</div></section>
<section id="weekly"><div class="wrap">
<div class="sh"><span class="lab">Every week</span><h2>One video. One essay. <em>One build.</em></h2></div>
<div class="grid g3">
<div class="card"><span class="lab">YouTube</span><h3>The teaching channel</h3><p>One framework taught properly, one build shown end to end, every week. If a course is the room, this is the window.</p><div class="foot">{A(utm(yt[2],'learn','youtube'), 'Subscribe →', 'btn sm', 'channel_click', channel='youtube', position='learn-weekly')}</div></div>
<div class="card"><span class="lab">Substack</span><h3>The essays</h3><p>Long-form on decision intelligence, AI strategy and the creator economy. The thinking behind the frameworks, before it becomes one.</p><div class="foot">{A(utm(sub[2],'learn','substack'), 'Read and subscribe →', 'btn sm ghost', 'channel_click', channel='substack', position='learn-weekly')}</div></div>
<div class="card"><span class="lab">Instagram</span><h3>Building in public</h3><p>Short-form: what shipped this week, what broke, what the fix was.</p><div class="foot">{A(utm(ig[2],'learn','instagram'), 'Follow →', 'btn sm ghost', 'channel_click', channel='instagram', position='learn-weekly')}</div></div>
</div></div></section>
"""

def body_speaking():
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">Speaking · talks, workshops, lectures</span>
<h1 style="margin-top:14px">Talks that leave a <em>method</em> behind.</h1>
<p class="sub">Every talk ships with the framework it teaches — the audience leaves with something they can run on Monday, not a set of slides about the future.</p>
<div class="row">{A('mailto:'+SITE['email']+'?subject=Speaking%20enquiry', 'Book a talk', 'btn', 'email_click', position='speaking-hero')}</div>
</div></section>
<section id="talks"><div class="wrap">
<div class="sh"><span class="lab">Talks</span><h2>Four <em>I give often</em>.</h2></div>
<div class="grid g2">
<div class="card"><span class="lab">Keynote · 30–45 min</span><h3>Data has no value. Decisions do.</h3><p>Why 91% of the mid-market has deployed AI and 38% can prove it worked — and the one instrument that closes the gap.</p></div>
<div class="card"><span class="lab">Workshop · half day</span><h3>The Flywheel</h3><p>Every founder scores their business live on eight dimensions, finds the drag, and leaves with a coaching prompt built from their own evidence. Run at LCC.</p></div>
<div class="card"><span class="lab">Workshop · full day</span><h3>Vibecoding: from worthy problem to live URL</h3><p>Non-engineers ship a real product in a day. Twenty steps, fifteen prompts, no excuses.</p></div>
<div class="card"><span class="lab">Lecture · 60 min</span><h3>Build the operator before the company</h3><p>REWIRED for students and early founders: identity is plastic, state is callable, beliefs are rewireable.</p></div>
</div></div></section>
<section id="where"><div class="wrap"><div class="two">
<div class="prose"><div class="sh"><span class="lab">Where</span><h2>Rooms I've <em>spoken in</em>.</h2></div>
<p>V&amp;A · Royal College of Art · European Commission · Central Saint Martins · London College of Communication (UAL) · UCL Academy · Nottingham Trent University · Hertfordshire University · IED Madrid · Women's AI Breakfast, London AI Hub · LCC NatWest Accelerator Pitch Day.</p>
<p>Delivered in English or Spanish. London in person; anywhere on video.</p></div>
<div class="card tint"><span class="lab">Fees</span><h3>Two bands</h3><p><strong>Corporate and conference</strong> — quoted per event.</p><p><strong>Education and non-profit</strong> — a separate, published rate. Universities and accelerators, ask; the answer is usually yes.</p><div class="foot" style="justify-content:flex-start">{A('mailto:'+SITE['email']+'?subject=Speaking%20enquiry', 'Enquire →', 'btn sm', 'email_click', position='speaking-fees')}{A(CONTRACT['cv_full'], 'Speaker CV (PDF) ↓', 'btn sm ghost', 'cta_click', kind='cv', position='speaking')}</div></div>
</div></div></section>
"""

def body_404():
    return f"""
<section class="hero" style="border-top:0"><div class="wrap">
<span class="lab">404</span>
<h1 style="margin-top:14px">That page <em>moved</em>.</h1>
<p class="sub">The site was rebuilt in September 2026. Pick the door you came for.</p>
<div class="doors" style="margin-top:20px">
<a class="door" href="/work-with-me/"><span class="lab">Buying a project</span><h3>Work with me</h3><span class="go">Methods and fees →</span></a>
<a class="door" href="/learn/"><span class="lab">Learning</span><h3>Learn</h3><span class="go">Courses and free resources →</span></a>
<a class="door" href="{LIB}/"><span class="lab">Looking for a framework</span><h3>The library</h3><span class="go">Every framework →</span></a>
</div></div></section>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────
PAGES = [
    {"slug": "home", "path": "/", "file": "index.html", "nav": "/",
     "title": "Diana Simpson-Hernandez — AI decision intelligence",
     "og_title": "I design the decision layer.",
     "description": "Founder of Aletheai. Fixed-fee AI diagnostics (LEVER, RECALL, STAKE), courses for non-engineers who ship software with AI, and an open framework library.",
     "jsonld": ld_graph(LD_REVIEW, {"@type": "ItemList", "name": "Courses", "itemListElement": [ld_course(c) for c in COURSES]}),
     "body": body_home, "og_kicker": "Diana Simpson-Hernandez", "og_sub": "Founder & CEO, Aletheai · Fractional Chief AI Officer · Educator"},
    {"slug": "work-with-me", "path": "/work-with-me/", "file": "work-with-me/index.html", "nav": "/work-with-me/",
     "title": "Work with me — fixed-fee AI diagnostics | DSH",
     "og_title": "Fixed fees. Published methods. No day rate.",
     "description": "AI decision diagnostics for mid-market operations businesses. LEVER, RECALL and STAKE: published methods, fixed fees from £750 to £55,000, engine-neutral.",
     "jsonld": ld_graph(LD_REVIEW, ld_breadcrumb(("Home", "/"), ("Work with me", "/work-with-me/"))),
     "body": body_work, "og_kicker": "Work with me", "og_sub": "LEVER · RECALL · STAKE — read the method before you hire me"},
    {"slug": "contract", "path": "/contract/", "file": "contract/index.html", "nav": "/contract/",
     "title": "Contract — AI strategy & adoption, outside IR35 | DSH",
     "og_title": "The answers to your first message, first.",
     "description": f"Contract AI strategist and fractional Chief AI Officer. Day rate {CONTRACT['day_rate']}, outside IR35, {CONTRACT['pattern'].lower()}. London or remote.",
     "jsonld": ld_graph(ld_breadcrumb(("Home", "/"), ("Contract", "/contract/"))),
     "body": body_contract, "og_kicker": "Contract", "og_sub": f"Day rate {CONTRACT['day_rate']} · outside IR35 · {CONTRACT['availability'].lower()}"},
    {"slug": "learn", "path": "/learn/", "file": "learn/index.html", "nav": "/learn/",
     "title": "Learn — AI courses for non-engineers & free frameworks",
     "og_title": "Learn to build the decision layer yourself.",
     "description": "Courses on Skool from a free community to a £997 ship-it cohort: Vibecoding, the Flywheel, REWIRED. Free interactive frameworks, weekly YouTube video, Substack essays.",
     "jsonld": ld_graph({"@type": "ItemList", "name": "Courses", "itemListElement": [ld_course(c) for c in COURSES]}, ld_breadcrumb(("Home", "/"), ("Learn", "/learn/"))),
     "body": body_learn, "og_kicker": "Learn", "og_sub": "Free frameworks · YouTube · courses on Skool from £39"},
    {"slug": "speaking", "path": "/speaking/", "file": "speaking/index.html", "nav": "/speaking/",
     "title": "Speaking — keynotes & workshops on AI decisions | DSH",
     "og_title": "Talks that leave a method behind.",
     "description": "Keynotes, workshops and lectures on AI decision intelligence, the Flywheel, Vibecoding and REWIRED. English and Spanish. London, or on video. Education rate.",
     "jsonld": ld_graph(ld_breadcrumb(("Home", "/"), ("Speaking", "/speaking/"))),
     "body": body_speaking, "og_kicker": "Speaking", "og_sub": "Keynotes · workshops · lectures — EN / ES"},
    {"slug": "404", "path": "/404.html", "file": "404.html", "nav": "", "noindex": True,
     "title": "Page not found | Diana Simpson-Hernandez", "og_title": "That page moved.",
     "description": "The page you were looking for has moved. Find work-with-me, learn, and the framework library.",
     "jsonld": None, "body": body_404, "og": "/assets/og/home.png"},
]

# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────
def write(rel: str, content: str):
    path = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(path) or ROOT, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: f.write(content)
    os.replace(tmp, path)
    assert os.path.getsize(path) > 0, rel

def build_pages():
    for p in PAGES:
        html = head(p) + nav(p["nav"]) + p["body"]() + footer()
        write(p["file"], html); print(f"  ✓ {p['file']:26} {len(html)//1024} KB")

def build_sitemap():
    urls = "".join(f"<url><loc>{SITE['domain']}{p['path']}</loc><lastmod>{TODAY}</lastmod><changefreq>{'weekly' if p['slug']=='home' else 'monthly'}</changefreq><priority>{'1.0' if p['slug']=='home' else '0.8'}</priority></url>"
                   for p in PAGES if not p.get("noindex"))
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE['domain']}/sitemap.xml\nSitemap: {LIB}/sitemap.xml\n")
    print("  ✓ sitemap.xml, robots.txt")

def build_css():
    write("styles/site.css", CSS.strip() + "\n"); print("  ✓ styles/site.css")

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
    print("building dianasimpsonhernandez.com")
    build_css(); build_pages(); build_sitemap()
    if "--og" in sys.argv: build_og()
    # non-zero validation
    for p in PAGES: assert os.path.getsize(os.path.join(ROOT, p["file"])) > 4000, p["file"]
    print("done")
