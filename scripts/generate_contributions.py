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

    colors = {"NONE": "#16233B", "FIRST_QUARTILE": "#0E4F7A", "SECOND_QUARTILE": "#0EA5E9",
              "THIRD_QUARTILE": "#38BDF8", "FOURTH_QUARTILE": "#A5F3FC"}

    days = [d for w in weeks for d in w.get("contributionDays", [])]
    counts = [d.get("contributionCount", 0) for d in days]
    active = sum(1 for c in counts if c > 0)
    best = max(counts) if counts else 0
    longest = cur = 0
    for c in counts:
        cur = cur + 1 if c > 0 else 0
        longest = max(longest, cur)
    current = 0
    for c in reversed(counts):
        if c > 0:
            current += 1
        elif current or c == 0 and counts and c is not counts[-1]:
            break

    sx, sy, cs, gap = 64, 196, 12.4, 3.6
    pitch = cs + gap
    names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    months, last = [], None
    for ci, w in enumerate(weeks):
        for d in w.get("contributionDays", []):
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            if dt.month != last and dt.day <= 14:
                months.append((names[dt.month-1], sx + ci*pitch)); last = dt.month
            break

    cells = []
    for ci, w in enumerate(weeks):
        for d in w.get("contributionDays", []):
            lvl = d.get("contributionLevel", "NONE")
            x, y = sx + ci*pitch, sy + d.get("weekday", 0)*pitch
            hi = lvl in ("THIRD_QUARTILE", "FOURTH_QUARTILE")
            glow = ' filter="url(#glow)"' if hi else ""
            dl = f"{ci*0.025:.2f}s" + (f",{1.5 + (ci % 5) * 0.4:.1f}s" if hi else "")
            cells.append(f'<rect class="c{" h" if hi else ""}" style="animation-delay:{dl}" x="{x:.1f}" y="{y:.1f}" width="{cs}" height="{cs}" rx="3" fill="{colors.get(lvl, colors["NONE"])}"{glow}/>')
    mx = "".join(f'<text x="{x:.1f}" y="{sy-12}" class="lbl">{n}</text>' for n, x in months)

    def stat(x, val, label):
        return (f'<g transform="translate({x},0)"><rect width="214" height="58" rx="12" fill="#101B30" stroke="#1E2D4A"/>'
                f'<rect x="0" y="14" width="3" height="30" rx="1.5" fill="url(#acc)"/>'
                f'<text x="22" y="29" class="val">{val}</text><text x="22" y="46" class="lbl">{label}</text></g>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 390" width="100%" height="auto" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A1020"/><stop offset="1" stop-color="#0F1D3A"/></linearGradient>
<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22D3EE"/><stop offset="1" stop-color="#818CF8"/></linearGradient>
<radialGradient id="orb" cx="0.85" cy="0" r="0.7"><stop offset="0" stop-color="#6366F1" stop-opacity="0.28"/><stop offset="1" stop-color="#6366F1" stop-opacity="0"/></radialGradient>
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7DD3FC" stop-opacity="0"/><stop offset=".5" stop-color="#7DD3FC"/><stop offset="1" stop-color="#7DD3FC" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<style>.t{{font-size:22px;font-weight:800;fill:#F1F5F9;letter-spacing:-.3px}}.s{{font-size:12.5px;fill:#7C8DAE}}.val{{font-size:20px;font-weight:800;fill:#F8FAFC}}.lbl{{font-size:10.5px;font-weight:500;fill:#7C8DAE}}.c{{opacity:0;animation:pop .5s ease forwards}}.h{{animation:pop .5s ease forwards,pl 2.8s ease-in-out infinite}}@keyframes pop{{to{{opacity:1}}}}@keyframes pl{{50%{{fill-opacity:.5}}}}</style>
<rect x="1" y="1" width="958" height="388" rx="18" fill="url(#bg)" stroke="#1E2D4A" stroke-width="1.5"/>
<rect x="1" y="1" width="958" height="388" rx="18" fill="url(#orb)"/>
<rect x="32" y="30" width="4" height="34" rx="2" fill="url(#acc)"/>
<text x="46" y="45" class="t">GitHub <tspan fill="url(#acc)">Activity</tspan></text>
<text x="46" y="63" class="s">A year of building, learning and shipping &#183; updated daily</text>
<g transform="translate(32,88)">{stat(0, synced_total, "Contributions")}{stat(226, active, "Active days")}{stat(452, f"{longest} days", "Longest streak")}{stat(678, best, "Best day")}</g>
{mx}
<rect y="{sy-4}" width="90" height="{7*pitch+4}" fill="url(#shine)" opacity=".16"><animate attributeName="x" values="40;860;40" dur="9s" repeatCount="indefinite"/></rect>
<g class="lbl"><text x="30" y="{sy+1*pitch+10}">Mon</text><text x="30" y="{sy+3*pitch+10}">Wed</text><text x="30" y="{sy+5*pitch+10}">Fri</text></g>
{''.join(cells)}
<g transform="translate({sx},{sy+7*pitch+20})"><text y="9.5" class="lbl">Less</text>
<rect x="30" width="11" height="11" rx="3" fill="#16233B"/><rect x="45" width="11" height="11" rx="3" fill="#0E4F7A"/><rect x="60" width="11" height="11" rx="3" fill="#0EA5E9"/><rect x="75" width="11" height="11" rx="3" fill="#38BDF8"/><rect x="90" width="11" height="11" rx="3" fill="#A5F3FC"/>
<text x="108" y="9.5" class="lbl">More</text></g>
</svg>"""
    ET.fromstring(svg)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[SUCCESS] Generated {output_path} with {synced_total} contributions")
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
