# GitHub Profile Setup & Deployment Guide: `Ashutosh2275`

This guide explains how to install, configure, verify, and maintain the redesigned GitHub profile for **Ashutosh Mishra (`Ashutosh2275`)**.

---

## 1. Repository Architecture

GitHub displays a profile README when a public repository with the exact same name as your GitHub username exists: `https://github.com/Ashutosh2275/Ashutosh2275`.

```text
├── README.md                              # Main profile document (light minimal theme, 100% reference design)
├── INSTALL.md                             # Setup, configuration & troubleshooting guide
├── preview.html                           # Standalone local preview renderer
├── scripts/
│   └── generate_contributions.py          # Data pipeline generating live contribution heatmap
├── assets/
│   ├── banner.svg                         # High-resolution vector hero banner
│   ├── values.svg                         # Full-width core value cards (Learn, Build, Collaborate, Create)
│   ├── github-activity.svg                # Full-width contribution heatmap with wave accent
│   ├── skills.svg                         # Categorized technical skills icon matrix
│   ├── stats.svg                          # GitHub Stats card (Contributions, Repositories, Stars)
│   ├── languages.svg                      # Most Used Languages horizontal bar chart card
│   ├── learning-goals.svg                 # Learning Goals card
│   ├── quote-footer.svg                   # Signature footer banner with wave accent
│   └── projects/
│       ├── healthcare-rag.svg             # 3D Robot Card: Healthcare Document Intelligence & RAG
│       ├── resume-screener.svg            # 3D Robot Card: Intelligent Resume Screening & Job Matching
│       ├── student-analytics.svg          # 3D Robot Card: Smart Student Performance Analytics
│       └── fraud-detection.svg            # 3D Robot Card: Financial Intelligence & Fraud Detection
└── .github/
    └── workflows/
        ├── update-contributions.yml       # Daily contribution heatmap update workflow
        └── contribution-snake.yml         # Daily contribution snake animation workflow
```

---

## 2. Personalizing Links & Contact Destinations

All hyperlinks are verified against Ashutosh's live portfolio and resume:

| Item | Location in `README.md` | Verified Value |
| :--- | :--- | :--- |
| **LinkedIn** | Header & Contact | `https://www.linkedin.com/in/ashutoshmishra-tech/` |
| **Portfolio** | Header & Contact | `https://heyashutosh.netlify.app/` |
| **Email** | Header & Contact | `mailto:ashutoshmishra2275@gmail.com` |
| **Resume / CV** | Header | `https://drive.google.com/file/d/1RyirKSNDgrU9XfwkMZfwFgM8A7Jv8sfR/view?usp=sharing` |
| **GitHub** | Header & Contact | `https://github.com/Ashutosh2275` |
| **Healthcare RAG Code** | Featured Projects | `https://github.com/Ashutosh2275/Datacure` |
| **Resume Screener Code**| Featured Projects | `https://github.com/Ashutosh2275/Datacure` |
| **Student Analytics Code**| Featured Projects| `https://github.com/Ashutosh2275/DRAI-AI` |
| **Fraud Detection Code**| Featured Projects | `https://github.com/Ashutosh2275/ARTHSAVORA` |

---

## 3. GitHub Actions Automated Updates

The repository includes automated GitHub Actions workflows to keep your profile visual assets synchronized with your real GitHub contributions:
- `.github/workflows/update-contributions.yml`: Generates the custom full-width live heatmap card.
- `.github/workflows/contribution-snake.yml`: Generates the contribution snake grid.

### Workflow Permissions
Grant write permissions so GitHub Actions can commit freshly generated contribution assets back to `assets/`:
1. In your `Ashutosh2275/Ashutosh2275` repository, navigate to **Settings** ➔ **Actions** ➔ **General**.
2. Scroll down to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.
