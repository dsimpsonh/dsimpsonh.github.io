# dsimpsonh.github.io
Diana Simpson Hernandez Public Website and Profile


# dianasimpsonhernandez.com

Personal hub for **Diana Simpson-Hernandez** — Founder & CEO of Aletheai, Fractional Chief AI Officer, educator at IED Madrid & LCC (UAL).

> **Deploys to:** `dianasimpsonhernandez.com` (apex domain)
> **Repo convention:** `dsimpsonh.github.io` (GitHub user-site pattern)

---

## 🏛️ The Brand Architecture

This repo is the **apex hub**. Every other body of work lives on its own subdomain, each backed by its own repo.

```
github.com/dsimpsonh/
│
├── dsimpsonh.github.io          ← THIS REPO (apex)
│                                  serves: dianasimpsonhernandez.com
│
├── frameworks                   ← serves: frameworks.dianasimpsonhernandez.com
├── aletheai-site                ← serves: aletheai.dianasimpsonhernandez.com
├── monogram                     ← serves: monogram.dianasimpsonhernandez.com
└── now                          ← serves: now.dianasimpsonhernandez.com
```

**Why this architecture:**
- Each subdomain = one focused experience = one repo
- Apex stays clean and editorial
- Adding a new venture is a 3-step pattern (new repo + DNS + Pages settings)
- Subdomains can be redesigned/replaced without touching the apex

---

## 🏗️ Repo Structure

```
/
├── index.html              ← apex landing page
├── styles/
│   └── main.css            ← shared design tokens
├── assets/
│   ├── og-image.png        ← (add) 1200×630 social preview
│   ├── favicon.ico         ← (add)
│   └── diana-simpson-hernandez-cv.pdf  ← (add)
├── CNAME                   ← contains: dianasimpsonhernandez.com
└── README.md
```

---

## 🚀 Deployment — Step by Step

### **STEP 1 — Create the apex repo**

```bash
# From your local machine
git init dsimpsonh.github.io
cd dsimpsonh.github.io
# Drop in all files from this bundle
git add .
git commit -m "Initial commit — apex landing page"
git remote add origin https://github.com/dsimpsonh/dsimpsonh.github.io.git
git push -u origin main
```

> **Important:** the repo MUST be named `dsimpsonh.github.io` (matching your GitHub username) for GitHub's "user site" auto-deploy to work.

### **STEP 2 — Enable GitHub Pages**

1. Go to repo → **Settings → Pages**
2. **Source:** `Deploy from a branch` → `main` → `/ (root)`
3. **Custom domain:** `dianasimpsonhernandez.com`
4. Tick **Enforce HTTPS** (becomes available after DNS propagates)

### **STEP 3 — Configure DNS for the apex**

In your DNS provider (where you bought `dianasimpsonhernandez.com`):

**Remove any existing A or CNAME records** for `@` (the root) first.

Then add:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| `A` | `@` | `185.199.108.153` | 3600 |
| `A` | `@` | `185.199.109.153` | 3600 |
| `A` | `@` | `185.199.110.153` | 3600 |
| `A` | `@` | `185.199.111.153` | 3600 |
| `CNAME` | `www` | `dsimpsonh.github.io` | 3600 |

DNS propagates in 5–60 minutes. Verify with:
```bash
dig dianasimpsonhernandez.com +short
# Should return the four IPs above
```

### **STEP 4 — Re-point the existing `frameworks` repo to the subdomain**

In your existing `frameworks` repo:

**Update `CNAME`** to:
```
frameworks.dianasimpsonhernandez.com
```

In DNS, add:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| `CNAME` | `frameworks` | `dsimpsonh.github.io` | 3600 |

In the `frameworks` repo → **Settings → Pages → Custom domain:**
`frameworks.dianasimpsonhernandez.com`

---

## ➕ How to Add a New Subdomain (future)

Pattern for any new venture (e.g. `monogram.dianasimpsonhernandez.com`):

**1. Create the new repo** on GitHub:
```bash
git init monogram
# build the site
git remote add origin https://github.com/dsimpsonh/monogram.git
git push -u origin main
```

**2. Add a `CNAME` file** to that repo containing:
```
monogram.dianasimpsonhernandez.com
```

**3. Add DNS record:**

| Type | Name | Value |
|------|------|-------|
| `CNAME` | `monogram` | `dsimpsonh.github.io` |

**4. In repo Settings → Pages → Custom domain:**
`monogram.dianasimpsonhernandez.com`

✅ Live in 5–10 minutes.

---

## 🎨 Design System

All tokens in `styles/main.css` under `:root`:

| Token | Value | Use |
|-------|-------|-----|
| `--paper` | `#f6f4ef` | Background |
| `--paper-warm` | `#efece4` | Card backgrounds |
| `--ink` | `#1a1a1a` | Primary text |
| `--accent` | `#c8462c` | Signal red — links, italic emphasis |
| `--font-display` | Fraunces | Headings, italic emphasis |
| `--font-body` | Inter Tight | Body text, UI |
| `--font-mono` | JetBrains Mono | Eyebrows, metadata |

**To rebrand any subdomain consistently:** copy `/styles/main.css` to that repo. Same tokens = same brand.

---

## ✅ Pre-Launch Checklist

### Content
- [ ] Verify all venture URLs (Aletheai, Monogram, Stand Out podcast)
- [ ] Confirm Substack handle (`@dianasimpsonhernandez`)
- [ ] Confirm LinkedIn handle (currently `linkedin.com/in/dianasimpson` — verify)
- [ ] Add `assets/diana-simpson-hernandez-cv.pdf` to repo
- [ ] Add `assets/og-image.png` (1200×630)
- [ ] Add `assets/favicon.ico`

### DNS
- [ ] Apex A records pointing to GitHub IPs
- [ ] `www` CNAME → `dsimpsonh.github.io`
- [ ] `frameworks` CNAME → `dsimpsonh.github.io`
- [ ] `dig dianasimpsonhernandez.com` returns GitHub IPs

### GitHub
- [ ] Repo named `dsimpsonh.github.io`
- [ ] Pages source set to `main` branch
- [ ] Custom domain `dianasimpsonhernandez.com` saved
- [ ] HTTPS enforced
- [ ] CNAME file in repo matches custom domain

### Optional v1.1
- [ ] Add Plausible / Fathom analytics snippet
- [ ] Add Substack inline embed for newsletter sign-up
- [ ] Add CV PDF generation pipeline (so docx → pdf is automated)

---

## 🗺️ Roadmap

| Version | What |
|---------|------|
| **v1.0** | This — apex landing page + frameworks subdomain |
| v1.1 | Add `now.dianasimpsonhernandez.com` (live status page) |
| v1.2 | Add `monogram.dianasimpsonhernandez.com` |
| v1.3 | Auto-generated OG image per page |
| v2.0 | Optional migration to Astro for SSG with shared components across all subdomains |

---

## 📞 Operating Notes

- **Typo fix:** the CV uses "Diana Simpson-Hernandez" (with hyphen) and "@dianasimpsonhernandez" (no hyphen) on Substack. The site uses both consistently per source.
- **Patent status:** "patent-pending" (Aletheai, UK) and "granted" (SPARK, US). Don't conflate.
- **Memberships:** FRSA, AFHEA, ILM L3, CREATE Ambassador.
- **Locations:** London (primary), Madrid, Texas — in that order on the site.

Built v1.0 — May 2026.
