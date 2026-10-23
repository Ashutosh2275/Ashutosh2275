#!/usr/bin/env python3
"""
scripts/generate_contributions.py
Fetches verified GitHub contribution data for Ashutosh2275 and generates
a custom light-theme GitHub Activity SVG card matching the reference design.
"""

import os
import sys
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

USERNAME = "Ashutosh2275"
OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "github-activity.svg")


def fetch_via_graphql(username, token):
    """Fetch contribution calendar using GitHub's authenticated GraphQL API."""
    url = "https://api.github.com/graphql"
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
                weekday
              }
            }
            months {
              name
              year
              firstDay
              totalWeeks
            }
          }
        }
      }
    }
    """
    req_body = json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_body,
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": "GitHub-Contribution-Generator",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if "errors" in data:
            raise RuntimeError(f"GraphQL returned errors: {data['errors']}")
        cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        return cal


def fetch_via_html_scraping(username):
    """Fallback fetcher scraping the public contributions calendar."""
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8")

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Extract total contributions
    h2 = soup.find("h2")
    total_str = h2.get_text(strip=True) if h2 else ""
    total_match = re.search(r"([\d,]+)\s+contributions", total_str)
    total_contributions = int(total_match.group(1).replace(",", "")) if total_match else 0

    # Extract tooltip details to get exact counts
    tooltips = {}
    for tt in soup.find_all("tool-tip"):
        for_id = tt.get("for")
        text = tt.get_text(strip=True)
        if for_id and text:
            tooltips[for_id] = text

    # Map table rows / cells into columns of weeks
    tds = soup.find_all("td", attrs={"data-date": True})
    
    # Organize days into weeks (53 columns x 7 rows)
    day_map = {}
    sum_counts = 0
    for td in tds:
        date_str = td.get("data-date")
        level_str = td.get("data-level", "0")
        try:
            level_int = int(level_str)
        except ValueError:
            level_int = 0

        day_id = td.get("id", "")
        tt_text = tooltips.get(day_id, "")
        count = 0
        m = re.search(r"(\d+)\s+contribution", tt_text)
        if m:
            count = int(m.group(1))

        sum_counts += count

        # Level mapping to GraphQL equivalent
        levels = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
        level_name = levels[min(max(level_int, 0), 4)]

        # Day of week from date
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = (dt.weekday() + 1) % 7  # 0 = Sunday, 1 = Monday, ... 6 = Saturday

        # Extract week index from id or placement
        # id is like contribution-day-component-ROW-COL
        col = None
        if day_id and "contribution-day-component-" in day_id:
            parts = day_id.split("-")
            if len(parts) >= 5:
                try:
                    col = int(parts[4])
                except ValueError:
                    pass

        day_map[date_str] = {
            "date": date_str,
            "contributionCount": count,
            "contributionLevel": level_name,
            "weekday": weekday,
            "col": col,
            "dt": dt
        }

    # Sort days chronologically
    sorted_days = sorted(day_map.values(), key=lambda x: x["dt"])

    # If total_contributions was not parsed from h2, use sum of counts
    if total_contributions == 0 and sum_counts > 0:
        total_contributions = sum_counts

    # Reconstruct weeks
    weeks = []
    current_week = []
    for d in sorted_days:
        if d["weekday"] == 0 and current_week:
            weeks.append({"contributionDays": current_week})
            current_week = []
        current_week.append(d)
    if current_week:
        weeks.append({"contributionDays": current_week})

    return {
        "totalContributions": total_contributions,
        "weeks": weeks
    }


def get_contribution_data(username):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            print("[INFO] Attempting fetch via GitHub GraphQL API...")
            return fetch_via_graphql(username, token)
        except Exception as e:
            print(f"[WARN] GraphQL API failed: {e}. Falling back to public contributions scraping...")

    print("[INFO] Fetching via public contributions scraping...")
    return fetch_via_html_scraping(username)


def generate_activity_svg(cal_data, output_path):
    total = cal_data.get("totalContributions", 0)
    weeks = cal_data.get("weeks", [])

    # Color palette matching the reference image (Clean white card, navy text, soft royal blue levels)
    # Level 0 (None): Pale light ice blue/gray
    # Level 1 (Light): Soft sky blue
    # Level 2 (Medium): Clear azure
    # Level 3 (High): Vibrant royal blue
    # Level 4 (Highest): Deep navy blue
    color_map = {
        "NONE": "#F1F5F9",
        "FIRST_QUARTILE": "#BAE6FD",
        "SECOND_QUARTILE": "#60A5FA",
        "THIRD_QUARTILE": "#2563EB",
        "FOURTH_QUARTILE": "#1D4ED8",
    }

    # Grid dimensions
    start_x = 76
    start_y = 104
    cell_size = 11.8
    cell_gap = 3.6
    pitch = cell_size + cell_gap

    # Build month labels
    # We find where each month starts across the weeks
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_labels = []
    last_month = None

    for col_idx, week in enumerate(weeks):
        for day in week.get("contributionDays", []):
            dt = datetime.strptime(day["date"], "%Y-%m-%d")
            if dt.month != last_month and dt.day <= 14:
                month_labels.append((month_names[dt.month - 1], start_x + col_idx * pitch))
                last_month = dt.month
                break

    # Build SVG cells
    cells_xml = []
    for col_idx, week in enumerate(weeks):
        for day in week.get("contributionDays", []):
            weekday = day.get("weekday", 0)  # 0 = Sunday, 1 = Monday, ..., 6 = Saturday
            # We display row 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
            x = start_x + col_idx * pitch
            y = start_y + weekday * pitch
            level = day.get("contributionLevel", "NONE")
            fill_color = color_map.get(level, "#F1F5F9")
            stroke_attr = ' stroke="#E2E8F0" stroke-width="0.8"' if level == "NONE" else ""
            cells_xml.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{fill_color}"{stroke_attr}/>'
            )

    months_xml = []
    for m_name, m_x in month_labels:
        months_xml.append(f'<text x="{m_x:.1f}" y="{start_y - 10}" class="cal-label">{m_name}</text>')

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 286" width="100%" height="auto" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <!-- Background Card Gradient -->
    <linearGradient id="actBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="65%" stop-color="#F8FAFC"/>
      <stop offset="100%" stop-color="#EDF5FF"/>
    </linearGradient>

    <!-- Translucent Wave Gradients -->
    <linearGradient id="waveCyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.5"/>
      <stop offset="50%" stop-color="#60A5FA" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#818CF8" stop-opacity="0.3"/>
    </linearGradient>
    <linearGradient id="waveBlue" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#93C5FD" stop-opacity="0.35"/>
      <stop offset="60%" stop-color="#A5B4FC" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#C084FC" stop-opacity="0.2"/>
    </linearGradient>

    <filter id="actShadow" x="-2%" y="-5%" width="104%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0F172A" flood-opacity="0.04"/>
    </filter>
  </defs>

  <style>
    .card-title {{ font-size: 21px; font-weight: 800; fill: #0F172A; letter-spacing: -0.3px; }}
    .card-title-highlight {{ fill: #2563EB; }}
    .card-subtitle {{ font-size: 13px; font-weight: 400; fill: #64748B; }}
    .metric-val {{ font-size: 18px; font-weight: 800; fill: #0F172A; }}
    .metric-label {{ font-size: 11px; font-weight: 500; fill: #64748B; }}
    .cal-label {{ font-size: 10px; font-weight: 500; fill: #64748B; }}
    .legend-text {{ font-size: 10.5px; font-weight: 500; fill: #64748B; }}
  </style>

  <!-- Outer Rounded Container Card -->
  <rect x="2" y="2" width="956" height="282" rx="16" fill="url(#actBg)" stroke="#E2E8F0" stroke-width="1.2" filter="url(#actShadow)"/>

  <!-- Flowing Translucent Wave Lines on Right / Behind Grid -->
  <g transform="translate(480, 110)">
    <path d="M 0 110 Q 120 40, 240 85 T 460 70" fill="none" stroke="url(#waveCyan)" stroke-width="2.8" stroke-linecap="round"/>
    <path d="M 0 125 Q 140 60, 260 100 T 460 85" fill="none" stroke="url(#waveBlue)" stroke-width="2" stroke-linecap="round"/>
  </g>

  <!-- Top Header Section -->
  <g transform="translate(32, 26)">
    <!-- GitHub Octocat Icon in Dark Circle -->
    <circle cx="20" cy="20" r="18" fill="#0F172A"/>
    <!-- Octocat Inverted Path -->
    <path d="M20 10.5 C15.03 10.5 11 14.53 11 19.5 C11 23.48 13.58 26.85 17.16 28.04 C17.61 28.12 17.77 27.84 17.77 27.6 C17.77 27.39 17.76 26.66 17.76 25.79 C15.26 26.33 14.73 24.72 14.73 24.72 C14.32 23.68 13.73 23.4 13.73 23.4 C12.91 22.84 13.79 22.85 13.79 22.85 C14.7 22.91 15.17 23.78 15.17 23.78 C15.98 25.16 17.29 24.76 17.81 24.53 C17.89 23.94 18.13 23.54 18.39 23.31 C16.39 23.08 14.29 22.31 14.29 18.88 C14.29 17.9 14.64 17.1 15.22 16.48 C15.13 16.25 14.82 15.34 15.31 14.12 C15.31 14.12 16.06 13.88 17.77 15.04 C18.48 14.84 19.24 14.74 20 14.74 C20.76 14.74 21.52 14.84 22.23 15.04 C23.94 13.88 24.69 14.12 24.69 14.12 C25.18 15.34 24.87 16.25 24.78 16.48 C25.36 17.1 25.71 17.9 25.71 18.88 C25.71 22.32 23.6 23.08 21.6 23.3 C21.92 23.58 22.21 24.13 22.21 24.97 C22.21 26.17 22.2 27.14 22.2 27.44 C22.2 27.68 22.36 27.97 22.82 27.88 C26.4 26.68 28.98 23.33 28.98 19.34 C28.98 14.37 24.95 10.5 20 10.5 Z" fill="#FFFFFF"/>

    <!-- Heading & Subtitle -->
    <text x="48" y="16" class="card-title">GitHub <tspan class="card-title-highlight">Activity</tspan></text>
    <text x="48" y="34" class="card-subtitle">A year of building, learning and contributing</text>

    <!-- Top-Right Metric Pill -->
    <g transform="translate(740, 0)">
      <rect x="0" y="0" width="154" height="42" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1"/>
      <!-- Sparkline Activity Icon -->
      <path d="M14 21 L20 21 L24 14 L28 27 L32 17 L36 21 L42 21" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="52" y="20" class="metric-val">{total}</text>
      <text x="52" y="34" class="metric-label">Contributions</text>
    </g>
  </g>

  <!-- Month Labels -->
  {' '.join(months_xml)}

  <!-- Weekday Labels on Left -->
  <g class="cal-label">
    <text x="46" y="{start_y + 1 * pitch + 9}">Mon</text>
    <text x="46" y="{start_y + 3 * pitch + 9}">Wed</text>
    <text x="46" y="{start_y + 5 * pitch + 9}">Fri</text>
  </g>

  <!-- Contribution Heatmap Grid -->
  <g>
    {' '.join(cells_xml)}
  </g>

  <!-- Bottom Legend -->
  <g transform="translate({start_x}, {start_y + 7 * pitch + 24})">
    <text x="0" y="9.5" class="legend-text">Less activity</text>
    <g transform="translate(68, 0)">
      <rect x="0" y="0" width="10" height="10" rx="2" fill="#F1F5F9" stroke="#E2E8F0" stroke-width="0.8"/>
      <rect x="14" y="0" width="10" height="10" rx="2" fill="#BAE6FD"/>
      <rect x="28" y="0" width="10" height="10" rx="2" fill="#60A5FA"/>
      <rect x="42" y="0" width="10" height="10" rx="2" fill="#2563EB"/>
      <rect x="56" y="0" width="10" height="10" rx="2" fill="#1D4ED8"/>
    </g>
    <text x="144" y="9.5" class="legend-text">More activity</text>
  </g>
</svg>"""

    # Validate XML syntax before writing
    try:
        ET.fromstring(svg_content)
    except Exception as e:
        raise ValueError(f"Generated SVG XML is invalid: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[SUCCESS] Generated {output_path} with {total} verified contributions!")


def main():
    try:
        data = get_contribution_data(USERNAME)
        generate_activity_svg(data, OUTPUT_SVG)
    except Exception as e:
        print(f"[ERROR] Failed to generate contributions SVG: {e}")
        # If output already exists, keep it intact (graceful preservation)
        if os.path.exists(OUTPUT_SVG):
            print("[INFO] Preserving existing known-good SVG asset.")
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
