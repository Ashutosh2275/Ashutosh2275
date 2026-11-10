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
            return data
        except Exception as e:
            print(f"[WARN] GraphQL API failed: {e}. Falling back to public contributions scraping...")

    print("[INFO] Fetching via public contributions scraping...")
    return fetch_via_html_scraping(username)


import math


def compute_stats(cal):
    weeks = cal.get("weeks", [])
    days = [d for w in weeks for d in w.get("contributionDays", [])]
    counts = [d.get("contributionCount", 0) for d in days]
    total, active = sum(counts), sum(1 for c in counts if c > 0)
    best = max(counts) if counts else 0
    best_date = days[counts.index(best)]["date"] if counts and best else None
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    i, current = len(counts) - 1, 0
    if i >= 0 and counts[i] == 0:
        i -= 1
    while i >= 0 and counts[i] > 0:
        current += 1
        i -= 1
    weekly = [sum(d.get("contributionCount", 0) for d in w.get("contributionDays", [])) for w in weeks]
    return {"total": total, "active_days": active, "best_day": best, "best_date": best_date,
            "longest_streak": longest, "current_streak": current,
            "avg_per_active_day": round(total / active, 1) if active else 0, "weekly": weekly}


def export_dataset_json(cal_data, stats, output_path):
    lvl = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    days = [{"date": d["date"], "count": d.get("contributionCount", 0),
             "intensity": lvl.get(d.get("contributionLevel", "NONE"), 0), "weekday": d.get("weekday", 0)}
            for w in cal_data.get("weeks", []) for d in w.get("contributionDays", [])]
    data = {"username": USERNAME, "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {"start_date": days[0]["date"] if days else None, "end_date": days[-1]["date"] if days else None,
                       "total_contributions": stats["total"]},
            "stats": stats, "days": days}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"[SUCCESS] Exported {len(days)} days to {output_path}")


COLORS = ["#E8EDFB", "#BFDBFE", "#60A5FA", "#6366F1", "#7C3AED"]
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def generate_activity_svg(cal, stats, output_path):
    weeks = cal.get("weeks", [])
    n = max(len(weeks), 1)
    cx, cy, r_in, pitch, th = 250, 240, 64, 20, 17
    step = 2 * math.pi / n

    def pt(r, a):
        return f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}"

    cells, labels, last = [], [], None
    for wi, w in enumerate(weeks):
        a0, a1 = -math.pi / 2 + wi * step + 0.012, -math.pi / 2 + (wi + 1) * step - 0.012
        for d in w.get("contributionDays", []):
            lv = LEVELS.get(d.get("contributionLevel", "NONE"), 0)
            r0 = r_in + d.get("weekday", 0) * pitch
            r1 = r0 + th
            path = f"M{pt(r1,a0)}A{r1},{r1} 0 0 1 {pt(r1,a1)}L{pt(r0,a1)}A{r0},{r0} 0 0 0 {pt(r0,a0)}Z"
            hi = lv >= 3
            dl = f"{wi*0.03:.2f}s" + (f",{1.6 + (wi % 6) * 0.35:.1f}s" if hi else "")
            cells.append(f'<path class="c{" h" if hi else ""}" style="animation-delay:{dl}" d="{path}" fill="{COLORS[lv]}"/>')
        first = w.get("contributionDays", [{}])[0].get("date")
        if first:
            dt = datetime.strptime(first, "%Y-%m-%d")
            if dt.month != last and dt.day <= 14:
                last = dt.month
                if wi == 0:
                    continue
                ang = -math.pi / 2 + (wi + 0.5) * step
                R = r_in + 7 * pitch + 14
                lx, ly = cx + R * math.cos(ang), cy + R * math.sin(ang) + 4
                anc = "start" if math.cos(ang) > 0.25 else "end" if math.cos(ang) < -0.25 else "middle"
                labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anc}" class="lbl">{MON[dt.month-1]}</text>')

    def tile(i, val, label):
        x, y = 520 + (i % 2) * 212, 52 + (i // 2) * 86
        return (f'<g transform="translate({x},{y})"><rect width="196" height="70" rx="14" fill="#fff" stroke="#E2E8F7"/>'
                f'<rect x="0" y="16" width="3" height="38" rx="1.5" fill="url(#accv)"/>'
                f'<text x="22" y="38" class="val">{val}</text><text x="22" y="57" class="lbl">{label}</text></g>')

    bd = ""
    if stats["best_date"]:
        dt = datetime.strptime(stats["best_date"], "%Y-%m-%d")
        bd = f" / {MON[dt.month-1]} {dt.day}"
    tiles = "".join(tile(i, v, l) for i, (v, l) in enumerate([
        (stats["total"], "Contributions"), (stats["active_days"], "Active days"),
        (f'{stats["current_streak"]} days', "Current streak"), (f'{stats["longest_streak"]} days', "Longest streak"),
        (stats["best_day"], "Best day" + bd), (stats["avg_per_active_day"], "Avg per active day")]))
    wk = stats["weekly"]
    mx = max(wk) if wk and max(wk) else 1
    bw = 408 / max(len(wk), 1)
    bars = "".join(f'<rect class="b" style="animation-delay:{i*0.025:.2f}s" x="{520+i*bw:.1f}" y="{404-max(3, 66*v/mx):.1f}" width="{bw-2:.1f}" height="{max(3, 66*v/mx):.1f}" rx="2" fill="{COLORS[min(4, 1 + int(3*v/mx))] if v else COLORS[0]}"/>' for i, v in enumerate(wk))
    leg = "".join(f'<rect x="{520+30+i*15}" y="422" width="11" height="11" rx="3" fill="{c}"/>' for i, c in enumerate(COLORS))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 470" width="960" height="470" style="font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,Roboto,Helvetica,Arial,sans-serif">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#F1F4FF"/></linearGradient>
<linearGradient id="accv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3B82F6"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient>
<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6366F1" stop-opacity="0"/><stop offset="1" stop-color="#6366F1" stop-opacity=".22"/></linearGradient></defs>
<style>.val{{font-size:24px;font-weight:800;fill:#0F172A}}.lbl{{font-size:10.5px;font-weight:600;fill:#64748B}}.mono{{font-family:'SF Mono',Consolas,monospace;letter-spacing:3px;font-size:11px;font-weight:600;fill:#6366F1}}
.c{{opacity:0;animation:pop .5s ease forwards}}.h{{animation:pop .5s ease forwards,pl 2.8s ease-in-out infinite}}.b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:gr .7s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes pop{{to{{opacity:1}}}}@keyframes pl{{50%{{fill-opacity:.55}}}}@keyframes gr{{to{{transform:scaleY(1)}}}}</style>
<rect x=".5" y=".5" width="959" height="469" rx="22" fill="url(#bg)" stroke="#E2E8F7"/>
<text x="520" y="34" class="mono">CONTRIBUTION ORBIT</text>
{''.join(cells)}{''.join(labels)}
<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="14s" repeatCount="indefinite"/>
<path d="M{cx},{cy}L{cx},{cy-r_in-7*pitch}A{r_in+7*pitch},{r_in+7*pitch} 0 0 1 {cx+(r_in+7*pitch)*math.sin(0.5):.1f},{cy-(r_in+7*pitch)*math.cos(0.5):.1f}Z" fill="url(#sweep)"/>
<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-r_in-7*pitch}" stroke="#6366F1" stroke-opacity=".5" stroke-width="1.4"/></g>
<circle cx="{cx}" cy="{cy}" r="52" fill="#fff" stroke="#E2E8F7"/><circle cx="{cx}" cy="{cy}" r="52" fill="none" stroke="url(#accv)" stroke-width="2" stroke-dasharray="60 270"><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="-360 {cx} {cy}" dur="8s" repeatCount="indefinite"/></circle>
<text x="{cx}" y="{cy+6}" text-anchor="middle" style="font-size:30px;font-weight:800" fill="#0F172A">{stats["total"]}</text><text x="{cx}" y="{cy+24}" text-anchor="middle" class="lbl">last 12 months</text>
{tiles}<text x="520" y="326" class="mono">WEEKLY RHYTHM</text>{bars}<text x="520" y="432" class="lbl">Less</text>{leg}<text x="{520+30+5*15+4}" y="432" class="lbl">More</text>
</svg>"""
    ET.fromstring(svg)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[SUCCESS] Generated {output_path}")


def main():
    cal = get_contribution_data(USERNAME)
    stats = compute_stats(cal)
    generate_activity_svg(cal, stats, OUTPUT_ACTIVITY_SVG)
    export_dataset_json(cal, stats, OUTPUT_JSON_DATASET)
    print(f"[DONE] {stats['total']} contributions, {stats['active_days']} active days")


if __name__ == "__main__":
    main()
