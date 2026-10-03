#!/usr/bin/env python3
"""Fetch current NFL lines from the-odds-api.com.

Usage:
    python3 fetch_odds.py                 # game lines (moneyline, spread, total) for the next 7 days
    python3 fetch_odds.py --days 4        # narrow the window
    python3 fetch_odds.py --json          # print raw API JSON instead of the summary
    python3 fetch_odds.py --event EVENT_ID --markets player_pass_yds,player_anytime_td
                                          # player props for one game (costs extra API credits)

Reads ODDS_API_KEY from .env in this folder (or the environment).
Every successful run also saves the raw response to odds_latest.json.
Uses only the Python standard library -- no pip installs needed.
"""

import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_URL = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
GAME_MARKETS = "h2h,spreads,totals"
MARKET_LABELS = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}


def fail(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def load_api_key():
    env_path = HERE / ".env"
    if env_path.exists():
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name.startswith("export "):
                name = name[len("export "):].strip()
            if name == "ODDS_API_KEY":
                value = value.strip().strip('"').strip("'")
                if value:
                    return value
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if key:
        return key
    fail(
        "ODDS_API_KEY not found. Add a line like\n"
        "    ODDS_API_KEY=your_key_here\n"
        f"to {env_path} (no spaces around '=', no quotes needed)."
    )


def call_api(url, params):
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full_url, headers={"User-Agent": "bozo-parlay-picks/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            headers = response.headers
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        hints = {
            401: "API key was rejected -- check ODDS_API_KEY in .env, or your monthly quota may be used up.",
            404: "Endpoint or event not found -- check the event ID.",
            422: "Request parameters were rejected (bad market name or event ID?).",
            429: "Rate limited / out of credits -- wait a bit or check your usage at the-odds-api.com.",
        }
        fail(f"Odds API returned HTTP {e.code}. {hints.get(e.code, '')}\nResponse: {detail}")
    except urllib.error.URLError as e:
        fail(f"Could not reach the Odds API ({e.reason}). Check your internet connection.")
    except TimeoutError:
        fail("Odds API request timed out after 20s. Try again.")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        fail(f"Odds API returned something that isn't JSON:\n{body[:300]}")

    used = headers.get("x-requests-used", "?")
    remaining = headers.get("x-requests-remaining", "?")
    return data, f"API credits used: {used}, remaining: {remaining}"


def fmt_odds(price):
    return f"+{price}" if price > 0 else str(price)


def fmt_point(point, signed):
    if point is None:
        return ""
    text = f"{point:g}"
    return f"+{text}" if signed and point > 0 else text


def summarize_outcomes(event, market_key):
    """Per outcome: consensus line (most common point), median price at that line, and best price/book."""
    rows = {}
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") != market_key:
                continue
            for o in market.get("outcomes", []):
                rows.setdefault(o["name"], []).append((o.get("point"), o["price"], book["title"]))

    lines = []
    for name, quotes in rows.items():
        consensus_point = Counter(q[0] for q in quotes).most_common(1)[0][0]
        at_consensus = [q for q in quotes if q[0] == consensus_point]
        median_price = int(statistics.median(q[1] for q in at_consensus))
        best = max(at_consensus, key=lambda q: q[1])
        point_range = sorted({q[0] for q in quotes if q[0] is not None})
        spread_note = ""
        if len(point_range) > 1:
            signed = market_key == "spreads"
            spread_note = f"  [books range {fmt_point(point_range[0], signed)} to {fmt_point(point_range[-1], signed)}]"
        label = f"{name} {fmt_point(consensus_point, market_key == 'spreads')}".strip()
        lines.append(
            f"    {label:<32} median {fmt_odds(median_price):>5}   best {fmt_odds(best[1]):>5} ({best[2]})"
            f"  across {len(quotes)} books{spread_note}"
        )
    return lines


def print_summary(events, markets):
    if not events:
        print("No NFL games with posted odds in this window.")
        return
    for event in sorted(events, key=lambda e: e["commence_time"]):
        kickoff = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
        print(f"\n{event['away_team']} @ {event['home_team']}  --  {kickoff:%a %b %d, %H:%M} UTC  (event id: {event['id']})")
        if not event.get("bookmakers"):
            print("    (no bookmaker odds posted yet)")
            continue
        for market_key in markets:
            out = summarize_outcomes(event, market_key)
            if out:
                print(f"  {MARKET_LABELS.get(market_key, market_key)}:")
                print("\n".join(out))


def main():
    parser = argparse.ArgumentParser(description="Fetch current NFL odds from the-odds-api.com")
    parser.add_argument("--days", type=int, default=7, help="only games kicking off within this many days (default 7)")
    parser.add_argument("--json", action="store_true", help="print raw JSON instead of the readable summary")
    parser.add_argument("--event", help="event id for a single game (use with --markets for player props)")
    parser.add_argument("--markets", help="comma-separated markets for --event, e.g. player_pass_yds,player_anytime_td")
    parser.add_argument("--regions", default="us", help="bookmaker region(s) (default us)")
    args = parser.parse_args()

    api_key = load_api_key()
    params = {"apiKey": api_key, "regions": args.regions, "oddsFormat": "american"}

    if args.event:
        markets = args.markets or GAME_MARKETS
        params["markets"] = markets
        data, quota = call_api(f"{BASE_URL}/events/{args.event}/odds", params)
        events = [data]
    else:
        markets = GAME_MARKETS
        now = datetime.now(timezone.utc).replace(microsecond=0)
        params.update({
            "markets": markets,
            "commenceTimeFrom": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "commenceTimeTo": (now + timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        data, quota = call_api(f"{BASE_URL}/odds", params)
        if not isinstance(data, list):
            fail(f"Unexpected response shape from the Odds API:\n{json.dumps(data)[:300]}")
        events = data

    (HERE / "odds_latest.json").write_text(json.dumps(data, indent=2))

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"Fetched {datetime.now():%Y-%m-%d %H:%M} local -- {len(events)} game(s). {quota}")
        print_summary(events, markets.split(","))
    print(f"\n{quota}. Raw data saved to odds_latest.json", file=sys.stderr)


if __name__ == "__main__":
    main()
