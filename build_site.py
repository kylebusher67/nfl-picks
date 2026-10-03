#!/usr/bin/env python3
"""Build the static site from picks_log.json.

Usage:
    python3 build_site.py           # regenerate index.html + week-N.html
    python3 build_site.py --push    # regenerate, then git commit + push (GitHub Pages redeploys)

Every page is generated from picks_log.json -- never hand-edit the HTML files.
Uses only the Python standard library.
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from html import escape
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
LOG_PATH = HERE / "picks_log.json"
SITE_TITLE = "Bozo Parlay Picks"
TIER_ORDER = ["safe", "balanced", "aggressive"]
TIER_BLURBS = {
    "safe": "Sharp market, strongest evidence, likeliest to hit. Lower payout.",
    "balanced": "Solid evidence at moderate odds. A reasonable parlay leg.",
    "aggressive": "Bigger payout, lower win probability. Higher volatility, not a smarter pick.",
}
DISCLAIMER = "For fun among friends. Not betting advice, and no proven edge against sportsbook lines."


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_picks():
    if not LOG_PATH.exists():
        return []
    try:
        picks = json.loads(LOG_PATH.read_text())
    except json.JSONDecodeError as e:
        fail(f"picks_log.json is not valid JSON: {e}")
    if not isinstance(picks, list):
        fail("picks_log.json must be a JSON array")
    for i, p in enumerate(picks):
        missing = [k for k in ("week", "pick", "bet_type", "odds", "confidence") if k not in p]
        if missing:
            fail(f"picks_log.json entry #{i} is missing {', '.join(missing)}")
    return picks


def tier_of(pick):
    return (pick.get("risk_tier") or "balanced").lower()


def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
{body}
<footer>{DISCLAIMER}</footer>
</main>
</body>
</html>
"""


def source_link(source):
    text = str(source)
    if text.startswith(("http://", "https://")):
        host = urlparse(text).netloc.removeprefix("www.")
        return f'<a href="{escape(text)}">{escape(host)}</a>'
    return escape(text)


def result_badge(pick):
    result = pick.get("result")
    if not result:
        return ""
    return f' <span class="result result-{escape(result.lower())}">{escape(result.upper())}</span>'


def render_pick_card(pick):
    tier = tier_of(pick)
    line = pick.get("line", "")
    price = f"{line} · {pick['odds']}" if line and line.upper() != "ML" else pick["odds"]
    why = pick.get("why") or []
    why_html = "".join(f"<li>{escape(w)}</li>" for w in why) or f"<li>{escape(pick.get('reasoning', ''))}</li>"
    conf = pick["confidence"]
    conf_note = pick.get("confidence_note", "")

    parts = [
        f'<section class="card tier-{escape(tier)}">',
        f'<div class="tier-head"><span class="tier-label">{escape(tier.title())}</span>'
        f'<span class="tier-blurb">{escape(TIER_BLURBS.get(tier, ""))}</span></div>',
        f'<p class="pick">{escape(pick["pick"])}{result_badge(pick)}</p>',
        f'<p class="meta">{escape(pick["bet_type"].title())} · {escape(price)}</p>',
        '<h3>Confidence</h3>',
        f'<p><span class="badge conf-{escape(conf.lower())}">{escape(conf)}</span>{escape(conf_note)}</p>',
        f'<h3>Why</h3><ul>{why_html}</ul>',
    ]
    if pick.get("breaks"):
        parts.append(f'<div class="risk"><h3>What breaks this pick</h3><p>{escape(pick["breaks"])}</p></div>')
    if pick.get("runner_up"):
        parts.append(f'<h3>Runner-up</h3><p>{escape(pick["runner_up"])}</p>')
    if pick.get("sources"):
        parts.append('<p class="sources">Sources: ' + ", ".join(source_link(s) for s in pick["sources"]) + "</p>")
    parts.append("</section>")
    return "\n".join(parts)


def render_week(week, picks):
    picks = sorted(picks, key=lambda p: TIER_ORDER.index(tier_of(p)) if tier_of(p) in TIER_ORDER else 99)
    dates = sorted({p.get("date", "") for p in picks if p.get("date")})
    generated = f"Generated {dates[-1]}" if dates else ""
    nav = "".join(
        f'<a href="#tier-{escape(tier_of(p))}">{escape(tier_of(p).title())}</a>' for p in picks
    ) if len(picks) > 1 else ""
    cards = "\n".join(
        render_pick_card(p).replace('<section class="card', f'<section id="tier-{escape(tier_of(p))}" class="card', 1)
        for p in picks
    )
    body = f"""<header>
<p class="crumbs"><a href="index.html">&larr; All weeks</a></p>
<p class="eyebrow">NFL Week {week} · {escape(generated)}</p>
<h1>Week {week} Picks</h1>
{f'<nav class="tiers">{nav}</nav>' if nav else ''}
</header>
{cards}"""
    return page(f"Week {week} Picks · {SITE_TITLE}", body)


def render_home(weeks):
    if weeks:
        items = []
        for week in sorted(weeks, reverse=True):
            picks = weeks[week]
            tiers = sorted({tier_of(p) for p in picks}, key=lambda t: TIER_ORDER.index(t) if t in TIER_ORDER else 99)
            chips = "".join(f'<span class="chip tier-{escape(t)}">{escape(t.title())}</span>' for t in tiers)
            items.append(
                f'<a class="week-card" href="week-{week}.html"><span class="week-title">Week {week} Picks</span>'
                f'<span class="chips">{chips}</span></a>'
            )
        listing = '<div class="weeks">' + "\n".join(items) + "</div>"
    else:
        listing = "<p>No picks generated yet.</p>"
    body = f"""<header>
<p class="eyebrow">6 friends · 6 legs · 1 parlay</p>
<h1>{SITE_TITLE}</h1>
<p class="lede">Each week one of us adds a leg to the group parlay. These are the researched picks for each week,
in up to three risk tiers: safe, balanced and aggressive.</p>
</header>
{listing}"""
    return page(SITE_TITLE, body)


def build():
    weeks = defaultdict(list)
    for p in load_picks():
        weeks[int(p["week"])].append(p)

    written = [HERE / "index.html"]
    (HERE / "index.html").write_text(render_home(weeks))
    for week, picks in weeks.items():
        path = HERE / f"week-{week}.html"
        path.write_text(render_week(week, picks))
        written.append(path)

    # Remove pages for weeks no longer in the log
    for stale in HERE.glob("week-*.html"):
        if stale not in written:
            stale.unlink()
            print(f"Removed stale page {stale.name}")

    print(f"Built {len(written)} page(s): " + ", ".join(p.name for p in written))
    return sorted(weeks)


def push(weeks):
    def git(*args):
        return subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True)

    # .gitignore keeps .env, odds_latest.json and local settings out of the commit
    added = git("add", "-A")
    if added.returncode != 0:
        fail(f"git add failed:\n{added.stderr}")
    if git("diff", "--cached", "--quiet").returncode == 0:
        print("Nothing changed; no commit made.")
        return
    latest = weeks[-1] if weeks else "?"
    commit = git("commit", "-m", f"Update picks site (through week {latest})\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    if commit.returncode != 0:
        fail(f"git commit failed:\n{commit.stderr or commit.stdout}")
    pushed = git("push")
    if pushed.returncode != 0:
        fail(f"git push failed:\n{pushed.stderr}")
    print("Pushed. Site updates at https://kylebusher67.github.io/nfl-picks/ in a minute or two.")


def main():
    parser = argparse.ArgumentParser(description="Build the static picks site from picks_log.json")
    parser.add_argument("--push", action="store_true", help="git commit and push the site after building")
    args = parser.parse_args()
    weeks = build()
    if args.push:
        push(weeks)


if __name__ == "__main__":
    main()
