# Bozo Parlay — Weekly NFL Pick Tool

A 6-person friend-group parlay pool: each week one person's pick becomes one leg of a shared 6-leg parlay. This is for fun. Never oversell confidence or imply the process has a proven edge against sportsbook lines — the books' prices already reflect most public information.

## Files
- `fetch_odds.py` — pulls current lines from the-odds-api.com (key in `.env` as `ODDS_API_KEY`). Stdlib only, Python 3.9+. Saves raw data to `odds_latest.json`.
- `picks_log.json` — JSON array of picks, one entry per (week, risk tier). **Source of truth for the website.**
- `build_site.py` — generates `index.html` (homepage listing every week) and `week-N.html` (one page per week, all tiers) from `picks_log.json`. `--push` also commits and pushes. **Never hand-edit the HTML files**; edit the log and rebuild.
- `style.css` — shared styling for all pages.
- `.env` — secret. Never print, echo, or commit the key.

The site is static (GitHub Pages, https://kylebusher67.github.io/nfl-picks/). Never add anything to the site that calls the Odds API or exposes the key; generation only happens locally.

## Hard rules
- **Never use memory for current-week facts** (injuries, records, lines, stats, who's starting). Every fact in a pick must come from this session's `fetch_odds.py` output or a fresh web search.
- **Lines and odds come only from `fetch_odds.py`.** Don't scrape or fetch sportsbook sites. If a line isn't in the API output, don't quote it.
- **If reliable current info is thin, say so plainly.** Lower the confidence or say "no strong pick this week" rather than force a confident-sounding answer.
- Always state today's date and confirm the NFL week number via search before analyzing.

## Workflow: "generate this week's pick" (optionally with a risk level)

Risk level is optional: "generate this week's pick — safe" / "balanced" / "aggressive". **With no level, generate all three tiers.**

| Tier | What it is |
|---|---|
| **Safe** | Sharp, liquid markets (spread, total, heavy-favorite moneyline) with the strongest evidence. Lower payout, likeliest to hit. |
| **Balanced** | Solid evidence at moderate odds (roughly -150 to +130). A sensible parlay leg without being reckless. |
| **Aggressive** | Higher odds (underdog moneylines, player props, close calls). Real upside, but it **trades win probability for payout**. |

Tier rules:
- Every tier gets the same depth: 3–4 sourced Why bullets, a specific "what breaks this", and its own runner-up.
- **Never present aggressive as the better or "smart money" pick.** It stands on its own with the higher risk stated. Don't rank tiers against each other; the group chooses based on how much risk it wants.
- Each tier must be a different bet. If no candidate honestly fits a tier (e.g. no well-supported aggressive play), say so and skip that tier rather than force one.

1. **Lines:** Run `python3 fetch_odds.py`. If it errors, show the error and stop — don't substitute lines from search results. Note each game's event id.
2. **Research (fresh web searches):**
   - Injury reports: official team/NFL injury reports and beat reporters (practice participation, Out/Doubtful/Questionable designations). Note the date of each report.
   - Current-season team stats: efficiency (EPA/play, success rate, DVOA if available), turnover margin, home/away splits, relevant matchup stats.
   - Analyst picks from 2–3 outlets (e.g. ESPN, The Athletic, Action Network). Treat these as context, not evidence of an edge.
   - Line movement: whether a line has moved since it opened (from line-move reporting in news coverage, with the source cited) and how much books disagree, using the `[books range ...]` in `fetch_odds.py` output.
   - **Historical ATS situational trends** (supporting context only; see "ATS trend rules" below). Search for trends that actually apply to this week's matchups, for example:
     - ATS record after a specific start (e.g. teams starting 0-3)
     - ATS record as a home/road favorite or underdog of a similar size to this week's line
     - ATS record off a bye or on short rest (only if one of the teams is in that spot this week)
     - Any other well-established situational trend that genuinely fits a specific matchup
     If nothing relevant applies, use no trend. Don't search until something turns up just to have one.
3. **Candidates:** Build 3–5 candidates per requested tier (they can overlap across tiers), spanning different bet types (spread, moneyline, total, and a player prop if one is well supported). Don't default to spreads.
   - For a prop candidate, fetch its line with `python3 fetch_odds.py --event <id> --markets <market>` (e.g. `player_pass_yds`, `player_rush_yds`, `player_reception_yds`, `player_anytime_td`). Each call costs extra API credits, so only fetch props you're seriously considering. If no line is posted, drop the candidate.
4. **Evaluate each candidate** on:
   - Evidence strength (how specific, current, and well-sourced the case is).
   - Market type: spreads/totals/moneylines are sharp, liquid markets (prices are efficient, hard to beat); player props are thinner and more volatile (one injury, game script, or usage change swings them). **These are not equivalent confidence levels** — say so explicitly when comparing.
   - The single biggest risk that breaks the pick.
   - Parlay context: a leg only helps the group if it hits.
   - **Evidence weighting, strongest to weakest:** (1) this week's injury reports, (2) current-season efficiency stats, (3) line movement and market agreement, (4) analyst picks and historical ATS trends. A trend can support a pick or add a caution, but **never make a trend the main reason for a pick**, and never let one override what the injury report or efficiency data says.
### ATS trend rules
- **Every trend needs a source and a sample size**, stated together: e.g. "13-4 ATS since 2021 (17 games), per [source]". If either one is missing, don't use the trend.
- **Sample size caveat:** if a trend covers fewer than ~20 games, label it **"small sample — directional only, not a strong signal."** Even 20–50 games is noisy, so present those as context too, not proof.
- **Assume the line already prices it in.** Well-known situational trends (bye weeks, rest, big favorites, 0-3 teams) are public, and the books and sharp bettors know them. Say explicitly why the trend may already be reflected in the line, and never present it as a hidden edge. A trend that runs against what the current-season data says is usually noise.
- Be wary of trends that were cherry-picked: odd cutoffs (e.g. "since 2019 on Sundays in October"), stacked conditions, or a source selling picks. The more specific the filter, the less it means.
- Use the most relevant trend per pick at most, not a list.

5. **Choose ONE pick per requested tier**, plus a runner-up for each.
6. **Log** each tier as its own entry in `picks_log.json`:
   ```json
   {"week": 5, "risk_tier": "safe|balanced|aggressive", "date": "2026-10-10",
    "pick": "Team/Player + selection", "bet_type": "spread|moneyline|total|player prop",
    "line": "-3.5 (or ML)", "odds": "-110", "confidence": "High|Medium|Low",
    "confidence_note": "one line on what the confidence means for this market type",
    "reasoning": "1-2 sentence summary",
    "why": ["3-4 bullets, each citing a source or stat"],
    "breaks": "the single most likely failure",
    "runner_up": "alternative + one sentence why",
    "trend": "OPTIONAL — omit the key entirely if no relevant trend. Trend + sample size + source + small-sample caveat + why it may be priced in",
    "sources": ["https://... or outlet + title"], "result": null}
   ```
   If an entry already exists for that week **and tier**, ask whether to replace it. Other tiers for the week stay untouched.
7. **Publish:** `python3 build_site.py --push`. That rebuilds the homepage and the week page and commits and pushes everything. Report whether the push worked; if it fails, show the error.
8. **Reply**, about one screen per tier, in this format for each tier generated (Safe → Balanced → Aggressive):

   **[Tier]: [team/player, bet type, line, odds]**
   - **Confidence:** [High/Medium/Low] — what that means given the market type
   - **Why:** 3–4 bullets, each citing a specific source or stat
   - **What breaks this pick:** the single most likely failure
   - **Relevant historical trend:** [trend + source + sample size + "small sample — directional only, not a strong signal" if under ~20 games + one clause on why it's likely priced in]. **Only include this line if a genuinely relevant trend was found;** otherwise leave the line out entirely (don't write "none").
   - **Runner-up:** one alternative, one sentence why

   Then one combined **Sources used** list and the week page link (`https://kylebusher67.github.io/nfl-picks/week-N.html`).

   Confidence guide: **High** is rare — strong, multi-source, current evidence in any market. Player props should almost never be High. **Low** whenever key injury news is unresolved (e.g. a Questionable QB) or sources conflict. Confidence is about evidence quality, not the tier: an aggressive pick can be Medium, and a safe pick can be Low.

## Workflow: "update results"

When given a game outcome (e.g. "week 5 safe won", "Bills covered"):
1. Find the matching entry in `picks_log.json` by week **and tier** (match the team/player named; if it's unclear which entry, ask).
2. Set `"result"` to `"win"`, `"loss"`, or `"push"`. If the user gives a final score instead, grade it against the logged line and show the math. Grade every tier that game affects.
3. Run `python3 build_site.py --push` so the result badges show on the site.
4. Report the season record (W-L-P) and win % = wins / (wins + losses), pushes excluded, **overall and per tier**.
5. Compare to the **~52.4% breakeven** needed at standard -110 odds (110/210). Since tiers use very different odds, also give each tier's breakeven from its logged odds (favorite -X: X/(X+100); underdog +X: 100/(X+100)). For example, a -700 pick needs 87.5% to break even. Keep it in perspective: small samples say very little about skill.
