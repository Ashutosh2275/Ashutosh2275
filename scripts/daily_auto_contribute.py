#!/usr/bin/env python3
"""
scripts/daily_auto_contribute.py
Automates daily GitHub portfolio contributions with realistic, organic pacing:
- Selects a daily target between 10 and 30 commits (heavily weighted towards 20-30).
- Generates a randomized daily schedule with realistic variable intervals (10 min, 50 min, 1 hour, 3 hours).
- NEVER makes bulk commits at once: at most ONE commit per execution when a scheduled window arrives.
- Commits as Ashutosh Mishra <ashutoshmishra2275@gmail.com>.
- Invokes generate_contributions.py to ensure real-time metrics and dynamic UTC timestamps with zero latency.
"""

import os
import sys
import json
import random
import subprocess
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTIVITY_FILE = os.path.join(BASE_DIR, "assets", "daily-activity.json")

AUTHOR_NAME = "Ashutosh Mishra"
AUTHOR_EMAIL = "ashutoshmishra2275@gmail.com"


def choose_daily_target():
    """
    Random target between 10 and 30, choosing the higher end (20-30) the majority of the time.
    10-14: ~4% weight
    15-19: ~8% weight
    20-24: ~32% weight
    25-30: ~56% weight
    Average: ~24.3 commits per day.
    """
    candidates = list(range(10, 31))
    weights = []
    for c in candidates:
        if c < 15:
            weights.append(1)
        elif c < 20:
            weights.append(2)
        elif c < 25:
            weights.append(8)
        else:
            weights.append(14)
    return random.choices(candidates, weights=weights)[0]


def generate_day_schedule(target_count, date_str):
    """
    Generates target_count unique scheduled UTC timestamps distributed organically
    across the 24-hour day (1440 minutes).
    Random intervals range from 10 minutes up to 3+ hours (e.g. 10m, 50m, 1h, 3h).
    """
    slack = 1440 - (target_count * 10)
    if slack <= target_count:
        segs = [max(0, slack // target_count)] * target_count
    else:
        cuts = sorted(random.sample(range(slack), target_count - 1))
        segs = [cuts[0]] + [cuts[i] - cuts[i-1] for i in range(1, len(cuts))] + [slack - cuts[-1]]
        random.shuffle(segs)

    gaps = [10 + s for s in segs]
    schedule = []
    curr = random.randint(2, 12)
    for g in gaps:
        curr += g
        if curr >= 1440:
            curr = 1438
        h = curr // 60
        m = curr % 60
        schedule.append(f"{date_str}T{h:02d}:{m:02d}:00Z")
    return sorted(list(dict.fromkeys(schedule)))


def load_state():
    if os.path.exists(ACTIVITY_FILE):
        try:
            with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse {ACTIVITY_FILE}: {e}")
    return {
        "date": "",
        "daily_target": 25,
        "commits_today": 0,
        "lifetime_deploys": 0,
        "scheduled_times": [],
        "history": {},
        "recent_deploys": []
    }


def save_state(state):
    os.makedirs(os.path.dirname(ACTIVITY_FILE), exist_ok=True)
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def run_git(cmd):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    res = subprocess.run(cmd, cwd=BASE_DIR, env=env, capture_output=True, text=True)
    if res.returncode != 0 and "nothing to commit" not in (res.stdout + res.stderr):
        print(f"[GIT] {' '.join(cmd)} -> {res.stderr.strip() or res.stdout.strip()}")
    return res.returncode == 0


def main():
    force_one = "--force-one" in sys.argv or os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour

    state = load_state()

    # Rollover check for new UTC day
    if state.get("date") != today_str:
        prev_date = state.get("date")
        if prev_date:
            state.setdefault("history", {})[prev_date] = {
                "target": state.get("daily_target", 25),
                "completed": state.get("commits_today", 0)
            }
            # Keep history trimmed to last 60 days
            keys = sorted(state["history"].keys())
            if len(keys) > 60:
                for old_k in keys[:-60]:
                    del state["history"][old_k]

        target = choose_daily_target()
        schedule = generate_day_schedule(target, today_str)
        state["date"] = today_str
        state["daily_target"] = len(schedule)
        state["commits_today"] = 0
        state["scheduled_times"] = schedule
        print(f"[NEW DAY] {today_str}: Selected daily target = {len(schedule)} commits spaced with random intervals across 24h")
    else:
        # Ensure scheduled_times exists for current day
        if not state.get("scheduled_times"):
            target = state.get("daily_target", 25)
            state["scheduled_times"] = generate_day_schedule(target, today_str)
            state["daily_target"] = len(state["scheduled_times"])

    target = state.get("daily_target", len(state.get("scheduled_times", [])))
    commits_today = state.get("commits_today", 0)
    scheduled_times = state.get("scheduled_times", [])

    # Determine if a commit is due now
    # Rule: NEVER make bulk commits. At most 1 commit per execution.
    commit_due = False
    next_slot_time = None

    if commits_today < len(scheduled_times):
        next_slot_time = scheduled_times[commits_today]
        try:
            next_slot_dt = datetime.fromisoformat(next_slot_time.replace("Z", "+00:00"))
            if now >= next_slot_dt:
                commit_due = True
        except Exception:
            commit_due = True
    elif commits_today < target and hour >= 23:
        commit_due = True

    if force_one and commits_today < target:
        commit_due = True

    print(f"[STATUS] {today_str} {now.strftime('%H:%M')} UTC | Commits today: {commits_today}/{target}")

    if commit_due and commits_today < target:
        commits_today += 1
        lifetime_deploys = state.get("lifetime_deploys", 0) + 1

        messages = [
            "portfolio contribution sync",
            "record automated deployment",
            "portfolio telemetry & metric refresh",
            "live activity heartbeat",
            "continuous portfolio deployment",
            "refresh daily contribution cadence",
            "automated profile update sync"
        ]
        msg_type = messages[(commits_today - 1) % len(messages)]

        entry = {
            "timestamp": now.isoformat(),
            "deploy_index": commits_today,
            "target": target,
            "lifetime_total": lifetime_deploys,
            "type": msg_type
        }

        state["commits_today"] = commits_today
        state["lifetime_deploys"] = lifetime_deploys
        state["last_deploy_time"] = entry["timestamp"]
        recent = state.setdefault("recent_deploys", [])
        recent.append(entry)
        if len(recent) > 50:
            state["recent_deploys"] = recent[-50:]

        save_state(state)

        run_git(["git", "add", "assets/daily-activity.json"])
        commit_msg = f"chore(deploy): {msg_type} [#{commits_today}/{target}] [skip ci]"
        if run_git(["git", "commit", "-m", commit_msg]):
            print(f"[DEPLOY] Successfully executed scheduled commit #{commits_today} of {target} ({msg_type})")
    else:
        if commits_today >= target:
            print(f"[STATUS] Daily quota reached ({commits_today}/{target}). Waiting for midnight UTC rollover.")
        elif next_slot_time:
            next_slot_dt = datetime.fromisoformat(next_slot_time.replace("Z", "+00:00"))
            diff_mins = (next_slot_dt - now).total_seconds() / 60.0
            print(f"[PACING] Next commit scheduled at {next_slot_time} (in {diff_mins:.1f} mins). Interval-paced; no bulk commits.")

    # Always invoke generate_contributions.py to ensure SVGs and JSON are synchronized with live UTC timestamp
    gen_script = os.path.join(BASE_DIR, "scripts", "generate_contributions.py")
    print("[INFO] Invoking generate_contributions.py to synchronize SVG and JSON...")
    res = subprocess.run([sys.executable, gen_script], cwd=BASE_DIR, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("[WARN]", res.stderr.strip())

    # Commit updated SVG and JSON if modified
    run_git(["git", "add", "assets/github-activity.svg", "assets/contributions.json"])
    run_git(["git", "commit", "-m", "chore(activity): update live contribution orbit and metrics [skip ci]"])


if __name__ == "__main__":
    main()
