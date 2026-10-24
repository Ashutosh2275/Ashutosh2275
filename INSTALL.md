# GitHub Profile Setup, Architecture & Automation Guide: `Ashutosh2275`

This documentation details the architecture, design specifications, data synchronization pipeline, and maintenance instructions for **Ashutosh Mishra (`Ashutosh2275`)**.

---

## 1. Repository Architecture & Layout

GitHub displays a profile README when a public repository with the exact same name as your GitHub username exists: `https://github.com/Ashutosh2275/Ashutosh2275`.

```text
Ashutosh2275/Ashutosh2275
├── README.md                              # Main profile document (Pure CommonMark/GFM compliant)
├── INSTALL.md                             # Setup, configuration & automation guide
├── preview.html                           # Standalone responsive preview renderer (desktop & mobile)
├── scripts/
│   └── generate_contributions.py          # Data pipeline generating live contribution heatmap & JSON
├── assets/
│   ├── banner.svg                         # Vector hero banner (Artwork, skyline, coder desk, tagline)
│   ├── values.svg                         # Full-width core value cards (Learn, Build, Collaborate, Create)
│   ├── github-activity.svg                # Full-width contribution heatmap with wave accent
│   ├── contributions.json                 # Structured contribution dataset schema
│   ├── skills.svg                         # Categorized technical skills icon matrix
│   ├── stats.svg                          # GitHub Stats card (Contributions, Repositories, Stars)
│   ├── languages.svg                      # Most Used Languages horizontal bar chart card
│   ├── learning-goals.svg                 # Learning Goals card
│   ├── quote-footer.svg                   # Signature footer banner with wave accent
│   ├── icons/
│   │   ├── user.svg                       # Blue outline user icon
│   │   ├── package.svg                    # Blue outline projects package icon
│   │   └── tools.svg                      # Blue outline technical skills icon
│   └── projects/
│       ├── healthcare-rag.svg             # 3D Robot Card: Healthcare Document Intelligence & RAG
│       ├── resume-screener.svg            # 3D Robot Card: Intelligent Resume Screening & Job Matching
│       ├── student-analytics.svg          # 3D Robot Card: Smart Student Performance Analytics
│       └── fraud-detection.svg            # 3D Robot Card: Financial Intelligence & Fraud Detection
└── .github/
    └── workflows/
        ├── update-contributions.yml       # Daily contribution heatmap & stats refresh workflow
        └── contribution-snake.yml         # Daily contribution snake animation workflow
```

---

## 2. Design System & Visual Hierarchy

- **Color Palette:**
  - Background: White (`#FFFFFF`)
  - Primary Typography: Deep Navy (`#10264A`)
  - Secondary Typography: Slate (`#526783`)
  - Brand Accent: Royal Blue (`#2878F0`)
  - Card Fill / Canvas: Pale Blue (`#EAF2FF` / `#F8FAFC`)
  - Borders: Thin Slate (`#DFE8F5`)
- **Typography:** Native system sans-serif (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`) with 1.5 line height for maximum legibility.
- **Section Order:**
  1. Hero Banner
  2. About Me (100% width) + 4 Value Cards
  3. GitHub Activity (100% width, minimal card, heatmap, total, legend)
  4. Featured Projects (2x2 grid, robot mascots, tags, code and demo buttons)
  5. Technical Skills (5 categorized boxes + text matrix)
  6. GitHub Analytics (3 side-by-side cards: Stats, Top Languages, Goals)
  7. Contact & Connect + Signature Quote Footer

---

## 3. Real GitHub Contribution Data Pipeline

The heatmap in `assets/github-activity.svg` and the counter in `assets/stats.svg` are derived from your actual GitHub activity for `Ashutosh2275`:

### Data Retrieval Order:
1. **Authenticated GraphQL API (`api.github.com/graphql`):** Uses GitHub's official `contributionsCollection` query to retrieve daily counts, weeks, and intensity tiers over the rolling 1-year period.
2. **Public Contribution Scraping Fallback:** Scrapes `https://github.com/users/Ashutosh2275/contributions` to retrieve official daily cell counts directly from GitHub's server-rendered HTML.
3. **Verified Baseline Synchronization:** Incorporates your verified baseline contributions (including private repositories) and increments monotonically as new commits are pushed.

### Structured Dataset Schema (`assets/contributions.json`):
- `generated_at`: ISO 8601 UTC timestamp.
- `username`: `Ashutosh2275`.
- `period`: Start date, end date, total contributions count.
- `intensity_scale`: 5 tiers (0 = 0, 1 = 1-3, 2 = 4-6, 3 = 7-9, 4 = 10+).
- `days`: List of `{date, count, intensity, weekday}`.

---

## 4. GitHub Actions Automated Updates

### Scheduled Trigger:
- Runs automatically at `00:00 UTC` daily via `.github/workflows/update-contributions.yml`.
- Can also be manually triggered anytime via the **Actions** tab (`workflow_dispatch`).

### Workflow Permissions:
1. In your repository on GitHub, navigate to **Settings** ➔ **Actions** ➔ **General**.
2. Under **Workflow permissions**, select **Read and write permissions**.
3. Click **Save**.

### Optional Secret for Private Repositories (`GH_PAT`):
GitHub's public API only returns public repository activity unless you either:
1. Toggle **"Include private contributions on my profile"** in [GitHub Profile Settings](https://github.com/settings/profile).
2. Or add a Personal Access Token (`GH_PAT`) with `read:user` and `repo` scope under **Settings** ➔ **Secrets and variables** ➔ **Actions**.
