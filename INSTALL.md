# GitHub Profile Setup & Deployment Guide: `Ashutosh2275`

This guide explains how to install, configure, verify, and maintain the redesigned GitHub profile for **Ashutosh Mishra (`Ashutosh2275`)**.

---

## 1. Repository Architecture

GitHub displays a profile README when a public repository with the exact same name as your GitHub username exists: `https://github.com/Ashutosh2275/Ashutosh2275`.

```text
├── README.md                              # Main profile document (light minimal theme)
├── INSTALL.md                             # Setup, configuration & troubleshooting guide
├── assets/
│   ├── banner.svg                         # High-resolution vector hero banner
│   ├── values.svg                         # Core value cards (Learn, Build, Collaborate, Create)
│   ├── skills.svg                         # Categorized technical skills icon matrix
│   ├── learning-goals.svg                 # Engineering goals card
│   ├── quote-footer.svg                   # Signature footer banner with wave accent
│   ├── github-contribution-grid-snake.svg # Contribution snake grid animation (bundled default)
│   └── projects/
│       ├── healthcare-rag.svg             # Custom vector art: Healthcare RAG Assistant
│       ├── resume-screener.svg            # Custom vector art: Resume Screening & Job Matching
│       ├── student-analytics.svg          # Custom vector art: Student Performance Analytics
│       └── fraud-detection.svg            # Custom vector art: Financial Intelligence & Fraud
└── .github/
    └── workflows/
        └── contribution-snake.yml         # Daily automation workflow for contribution snake
```

---

## 2. Step-by-Step Initial Setup

### Step 2.1: Create the Special Profile Repository on GitHub
1. Log into your GitHub account: [https://github.com/Ashutosh2275](https://github.com/Ashutosh2275).
2. Go to **New repository** ([https://github.com/new](https://github.com/new)).
3. In **Repository name**, enter exactly: `Ashutosh2275`.
4. Set visibility to **Public** (required for GitHub profile READMEs).
5. **Do not** initialize with a README, .gitignore, or license (we already have clean files prepared).
6. Click **Create repository**.

### Step 2.2: Push Local Files to GitHub
Open your terminal in the workspace directory and run:

```bash
# Verify git status
git status

# Stage all files
git add .

# Create initial commit
git commit -m "feat: implement professional minimal light GitHub profile redesign"

# Connect remote (replace with SSH if preferred)
git remote add origin https://github.com/Ashutosh2275/Ashutosh2275.git

# Set branch to main and push
git branch -M main
git push -u origin main
```

---

## 3. Configuring the Contribution Snake Workflow

The repository includes `.github/workflows/contribution-snake.yml` to automatically animate your contribution grid every 24 hours.

### Step 3.1: Enable Workflow Permissions
By default, GitHub Actions may have read-only permissions. Grant write permissions so the workflow can commit the updated snake animation back to `assets/`:

1. In your `Ashutosh2275/Ashutosh2275` repository, navigate to **Settings** ➔ **Actions** ➔ **General**.
2. Scroll to the bottom to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Check **Allow GitHub Actions to create and approve pull requests** (optional, recommended).
5. Click **Save**.

### Step 3.2: Trigger the Workflow Manually
To test the workflow immediately:
1. Go to the **Actions** tab in your repository.
2. Under "Workflows" on the left, click **Generate Contribution Snake**.
3. Click the **Run workflow** dropdown on the right and select the `main` branch.
4. Click **Run workflow**.
5. Once completed (typically ~30 seconds), the workflow updates `assets/github-contribution-grid-snake.svg` with your actual contribution graph.

---

## 4. Personalizing Links & Contact Destinations

The profile includes working placeholders based on your known profiles. You can verify and adjust them in `README.md`:

| Item | Current Location in `README.md` | Verification / Value |
| :--- | :--- | :--- |
| **LinkedIn** | Lines 14, 275 | `https://linkedin.com/in/ashutosh2275` |
| **Email** | Lines 22, 279 | `ashutoshmishra2275@gmail.com` |
| **Portfolio** | Line 18 | `https://suraksha-weekly.vercel.app` (or your personal domain) |
| **Resume** | Line 26 | Links to `https://github.com/Ashutosh2275?tab=repositories` or replace with a direct PDF URL |
| **Datacure Repo** | Line 96 | `https://github.com/Ashutosh2275/Datacure` |
| **EduVista Repo** | Line 140 | `https://github.com/Ashutosh2275/EduVista` |
| **Suraksha Repo** | Line 162 | `https://github.com/Ashutosh2275/suraksha-weekly` |
| **Live Demo** | Line 177 | `https://suraksha-weekly.vercel.app` |

---

## 5. Troubleshooting & FAQ

### Q: Why does GitHub display my previous README or nothing at all?
- Ensure the repository is strictly named `Ashutosh2275` and is set to **Public**.
- Confirm `README.md` is in the root directory, not inside a subfolder.

### Q: What if external statistics cards (github-readme-stats) load slowly?
- `github-readme-stats.vercel.app` caches requests on Vercel's edge network for 4 hours.
- If external rate-limiting ever occurs, GitHub's image proxy (`camo.githubusercontent.com`) automatically serves the last successfully cached version.
- You can tune parameters directly in the URL in `README.md`, such as adding `&cache_seconds=86400`.

### Q: How can I update my resume button with a direct PDF download?
Upload your PDF file as a release asset or to Google Drive, and update line 26 in `README.md`:
```markdown
<a href="https://your-domain.com/ashutosh-mishra-resume.pdf" target="_blank">
  <img src="https://img.shields.io/badge/Resume-7C3AED?style=for-the-badge&logo=googledocs&logoColor=white" alt="Resume / CV" />
</a>
```

### Q: How do relative asset paths work on GitHub?
All images use relative paths (`assets/banner.svg`, `assets/projects/*.svg`), meaning GitHub resolves them directly from the repository tree without requiring absolute raw URLs or third-party image hosts.

---

## 6. Pre-Flight Verification Checklist

- [x] `README.md` contains zero markdown/syntax errors.
- [x] All 8 SVGs in `assets/` validated as well-formed, standards-compliant XML.
- [x] Workflow `.github/workflows/contribution-snake.yml` validated as valid YAML with minimal permissions (`contents: write`).
- [x] Color scheme verified against user design direction (pure light theme, pale blue `#F0F7FF`, navy `#0F172A`).
- [x] Layout confirmed responsive across mobile and desktop.
- [x] No fabricated achievements or fake stats.
