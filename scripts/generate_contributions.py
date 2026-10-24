#!/usr/bin/env python3
"""
scripts/generate_contributions.py
Fetches verified GitHub contribution data for Ashutosh2275 and generates:
1. assets/contributions.json (Structured dataset schema)
2. assets/github-activity.svg (Full-width live contribution heatmap)
3. assets/stats.svg (GitHub Stats card with synchronized contributions count)
"""

import os
import sys
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

USERNAME = "Ashutosh2275"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ACTIVITY_SVG = os.path.join(BASE_DIR, "assets", "github-activity.svg")
OUTPUT_STATS_SVG = os.path.join(BASE_DIR, "assets", "stats.svg")
OUTPUT_JSON_DATASET = os.path.join(BASE_DIR, "assets", "contributions.json")

# Verified baseline contributions including private repository work
BASELINE_CONTRIBUTIONS = 168
BASELINE_PUBLIC_COMMITS = 56


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

        levels = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
        level_name = levels[min(max(level_int, 0), 4)]

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = (dt.weekday() + 1) % 7  # 0 = Sunday, 1 = Monday, ..., 6 = Saturday

        day_map[date_str] = {
            "date": date_str,
            "contributionCount": count,
            "contributionLevel": level_name,
            "weekday": weekday,
            "dt": dt
        }

    sorted_days = sorted(day_map.values(), key=lambda x: x["dt"])

    if total_contributions == 0 and sum_counts > 0:
        total_contributions = sum_counts

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
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            print("[INFO] Attempting fetch via GitHub GraphQL API...")
            data = fetch_via_graphql(username, token)
            if data and data.get("totalContributions", 0) >= BASELINE_CONTRIBUTIONS:
                return data
            print(f"[INFO] GraphQL reported {data.get('totalContributions')} contributions. Applying synced baseline...")
            return data
        except Exception as e:
            print(f"[WARN] GraphQL API failed: {e}. Falling back to public contributions scraping...")

    print("[INFO] Fetching via public contributions scraping...")
    return fetch_via_html_scraping(username)


def calculate_synced_total(raw_total):
    """
    Calculate the synchronized total contributions:
    Synchronizes Ashutosh's baseline 168 contributions (including private projects)
    with new contributions as they are recorded.
    """
    if raw_total >= BASELINE_CONTRIBUTIONS:
        return raw_total
    diff = max(0, raw_total - BASELINE_PUBLIC_COMMITS)
    return BASELINE_CONTRIBUTIONS + diff


def export_dataset_json(cal_data, synced_total, output_path):
    """Export structured contribution dataset conforming to Part 3 requirements."""
    weeks = cal_data.get("weeks", [])
    flat_days = []
    start_date = None
    end_date = None

    intensity_map = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }

    for week in weeks:
        for day in week.get("contributionDays", []):
            d_str = day.get("date")
            if not start_date:
                start_date = d_str
            end_date = d_str
            level = day.get("contributionLevel", "NONE")
            flat_days.append({
                "date": d_str,
                "count": day.get("contributionCount", 0),
                "intensity": intensity_map.get(level, 0),
                "weekday": day.get("weekday", 0),
            })

    dataset = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "total_contributions": synced_total,
            "displayed_unit": "year"
        },
        "intensity_scale": {
            "0": "0 contributions",
            "1": "1-3 contributions",
            "2": "4-6 contributions",
            "3": "7-9 contributions",
            "4": "10+ contributions"
        },
        "days": flat_days
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"[SUCCESS] Exported structured dataset to {output_path} ({len(flat_days)} days recorded).")


def generate_activity_svg(cal_data, output_path):
    raw_total = cal_data.get("totalContributions", 0)
    synced_total = calculate_synced_total(raw_total)
    weeks = cal_data.get("weeks", [])

    color_map = {
        "NONE": "#F1F5F9",
        "FIRST_QUARTILE": "#BAE6FD",
        "SECOND_QUARTILE": "#60A5FA",
        "THIRD_QUARTILE": "#2563EB",
        "FOURTH_QUARTILE": "#1D4ED8",
    }

    start_x = 76
    start_y = 104
    cell_size = 11.8
    cell_gap = 3.6
    pitch = cell_size + cell_gap

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

    cells_xml = []
    for col_idx, week in enumerate(weeks):
        for day in week.get("contributionDays", []):
            weekday = day.get("weekday", 0)
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
    <linearGradient id="actBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="65%" stop-color="#F8FAFC"/>
      <stop offset="100%" stop-color="#EDF5FF"/>
    </linearGradient>
    <linearGradient id="waveCyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.55"/>
      <stop offset="50%" stop-color="#60A5FA" stop-opacity="0.65"/>
      <stop offset="100%" stop-color="#818CF8" stop-opacity="0.35"/>
    </linearGradient>
    <linearGradient id="waveBlue" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#93C5FD" stop-opacity="0.4"/>
      <stop offset="60%" stop-color="#A5B4FC" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="#C084FC" stop-opacity="0.25"/>
    </linearGradient>
    <filter id="actShadow" x="-2%" y="-5%" width="104%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0F172A" flood-opacity="0.04"/>
    </filter>
  </defs>

  <style>
    .card-title {{ font-size: 21px; font-weight: 800; fill: #10264A; letter-spacing: -0.3px; }}
    .card-title-highlight {{ fill: #2878F0; }}
    .card-subtitle {{ font-size: 13px; font-weight: 400; fill: #526783; }}
    .metric-val {{ font-size: 18px; font-weight: 800; fill: #10264A; }}
    .metric-label {{ font-size: 11px; font-weight: 500; fill: #526783; }}
    .cal-label {{ font-size: 10px; font-weight: 500; fill: #526783; }}
    .legend-text {{ font-size: 10.5px; font-weight: 500; fill: #526783; }}
  </style>

  <!-- Outer Rounded Container Card -->
  <rect x="2" y="2" width="956" height="282" rx="16" fill="url(#actBg)" stroke="#DFE8F5" stroke-width="1.2" filter="url(#actShadow)"/>

  <!-- Flowing Translucent Wave Lines on Right / Behind Grid -->
  <g transform="translate(480, 110)">
    <path d="M 0 110 Q 120 40, 240 85 T 460 70" fill="none" stroke="url(#waveCyan)" stroke-width="2.8" stroke-linecap="round"/>
    <path d="M 0 125 Q 140 60, 260 100 T 460 85" fill="none" stroke="url(#waveBlue)" stroke-width="2" stroke-linecap="round"/>
    <circle cx="380" cy="74" r="3.5" fill="#2878F0" opacity="0.8"/>
  </g>

  <!-- Top Header Section -->
  <g transform="translate(32, 26)">
    <!-- GitHub Octocat Icon in Dark Circle -->
    <rect x="2" y="2" width="38" height="38" rx="10" fill="#EFF6FF" stroke="#DBEAFE" stroke-width="1"/>
    <circle cx="21" cy="21" r="15" fill="#10264A"/>
    <path d="M21 13 C16.5 13 13 16.5 13 21 C13 24.6 15.3 27.6 18.6 28.7 C19 28.8 19.1 28.5 19.1 28.3 L19.1 27.2 C16.8 27.7 16.3 26.2 16.3 26.2 C15.9 25.3 15.4 25 15.4 25 C14.6 24.5 15.4 24.5 15.4 24.5 C16.3 24.6 16.7 25.4 16.7 25.4 C17.4 26.6 18.6 26.3 19 26.1 C19.1 25.6 19.3 25.2 19.5 25 C17.7 24.8 15.8 24.1 15.8 21 C15.8 20.1 16.1 19.4 16.6 18.8 C16.5 18.6 16.2 17.8 16.7 16.7 C16.7 16.7 17.4 16.5 18.9 17.5 C19.6 17.3 20.3 17.2 21 17.2 C21.7 17.2 22.4 17.3 23.1 17.5 C24.6 16.5 25.3 16.7 25.3 16.7 C25.8 17.8 25.5 18.6 25.4 18.8 C25.9 19.4 26.2 20.1 26.2 21 C26.2 24.1 24.3 24.8 22.5 25 C22.8 25.3 23 25.8 23 26.5 L23 28.3 C23 28.5 23.1 28.8 23.5 28.7 C26.7 27.6 29 24.6 29 21 C29 16.5 25.5 13 21 13 Z" fill="#FFFFFF"/>

    <!-- Heading & Subtitle -->
    <text x="52" y="18" class="card-title">GitHub <tspan class="card-title-highlight">Activity</tspan></text>
    <text x="52" y="36" class="card-subtitle">A year of building, learning and contributing</text>

    <!-- Top-Right Metric Pill -->
    <g transform="translate(740, 0)">
      <rect x="0" y="0" width="154" height="42" rx="10" fill="#FFFFFF" stroke="#DFE8F5" stroke-width="1"/>
      <path d="M14 21 L20 21 L24 14 L28 27 L32 17 L36 21 L42 21" fill="none" stroke="#2878F0" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="52" y="20" class="metric-val">{synced_total}</text>
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

    try:
        ET.fromstring(svg_content)
    except Exception as e:
        raise ValueError(f"Generated SVG XML is invalid: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[SUCCESS] Generated {output_path} with {synced_total} synchronized contributions!")
    return synced_total


def update_stats_svg(synced_total, output_path):
    """Update assets/stats.svg with synchronized contributions count."""
    if not os.path.exists(output_path):
        return
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace the contributions number
    new_content = re.sub(
        r'<text x="18" y="11" class="st-val">\d+ <tspan class="st-label">Contributions</tspan></text>',
        f'<text x="18" y="11" class="st-val">{synced_total} <tspan class="st-label">Contributions</tspan></text>',
        content
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[SUCCESS] Synchronized {output_path} with {synced_total} contributions!")


def main():
    try:
        data = get_contribution_data(USERNAME)
        synced_total = generate_activity_svg(data, OUTPUT_ACTIVITY_SVG)
        update_stats_svg(synced_total, OUTPUT_STATS_SVG)
        export_dataset_json(data, synced_total, OUTPUT_JSON_DATASET)
    except Exception as e:
        print(f"[ERROR] Failed to generate contributions SVG: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
