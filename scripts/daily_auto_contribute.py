#!/usr/bin/env python3
"""
scripts/daily_auto_contribute.py
Automates daily GitHub portfolio contributions:
- Selects a daily target between 10 and 30 commits (heavily weighted towards 20-30).
- Paces commits across the 24-hour cycle so every day has active contributions.
- Records each deploy in assets/daily-activity.json.
- Commits as Ashutosh Mishra <ashutoshmishra2275@gmail.com>.
- Invokes generate_contributions.py to recalculate real-time metrics and update github-activity.svg.
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
    force_all = "--force-all" in sys.argv
    force_one = "--force-one" in sys.argv or os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour
    minute = now.minute

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
        state["date"] = today_str
        state["daily_target"] = target
        state["commits_today"] = 0
        print(f"[NEW DAY] {today_str}: Selected daily target = {target} commits (weighted 20-30)")
    else:
        target = state.get("daily_target", 25)

    commits_today = state.get("commits_today", 0)
    lifetime_deploys = state.get("lifetime_deploys", 0)

    # Calculate expected commits up to this point in the day
    elapsed_fraction = (hour + minute / 60.0) / 24.0
    if hour >= 23:
        expected = target
    else:
        expected = int(round(elapsed_fraction * target))
        expected = max(1, min(target, expected))

    if force_all:
        expected = target
    elif force_one:
        expected = max(expected, min(target, commits_today + 1))

    needed = max(0, expected - commits_today)
    # Batch up to 3 commits per normal run, or all needed if force_all
    batch_size = needed if force_all else min(3, needed)

    print(f"[STATUS] {today_str} {now.strftime('%H:%M')} UTC | Commits today: {commits_today}/{target} | Expected by now: {expected} | To make: {batch_size}")

    messages = [
        "portfolio contribution sync",
        "record automated deployment",
        "portfolio telemetry & metric refresh",
        "live activity heartbeat",
        "continuous portfolio deployment",
        "refresh daily contribution cadence",
        "automated profile update sync"
    ]

    commits_made = 0
    for i in range(batch_size):
        commits_today += 1
        lifetime_deploys += 1
        msg_type = messages[(commits_today - 1) % len(messages)]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
            commits_made += 1

    print(f"[DONE] Successfully generated {commits_made} new contribution commits.")

    # Always invoke generate_contributions.py to ensure SVGs and JSON are synchronized
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
