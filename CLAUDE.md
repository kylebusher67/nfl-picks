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

Risk level is optional: "generate this week's pick — safe" / "balanced" / "aggressive". **With no level, generate all three tiers.** **Each tier gets 3 picks**, ranked #1–#3 within the tier, so a full run is 9 picks.

| Tier | What it is |
|---|---|
| **Safe** | Sharp, liquid markets (spread, total, heavy-favorite moneyline) with the strongest evidence. Lower payout, likeliest to hit. |
| **Balanced** | Solid evidence at moderate odds (roughly -150 to +130). A sensible parlay leg without being reckless. |
| **Aggressive** | Higher odds (underdog moneylines, player props, close calls). Real upside, but it **trades win probability for payout**. |

Tier rules:
- Every pick in every tier gets the same depth: 3–4 sourced Why bullets and a specific "what breaks this". #1 is the strongest-evidence pick in the tier; #2 and #3 must still be real picks that hold up on their own, not filler.
- **Never present aggressive as the better or "smart money" pick.** It stands on its own with the higher risk stated. Don't rank tiers against each other; the group chooses based on how much risk it wants.
- **No duplicates:** all 9 picks are different bets. Avoid giving the same game and side in two tiers (e.g. Packers -3.5 as Safe and Packers ML as Balanced); if you do, say why.
- **Spread picks across games:** within a tier, prefer 3 different games. If two picks are correlated (same game, or the same thing breaks both of them), say so, because the group may only use one of them.
- **Don't force it:** if fewer than 3 candidates honestly fit a tier (common for Safe in a week with no clear favorites, or for player props without posted lines), give fewer picks and say so plainly rather than pad the tier.

1. **Lines:** Run `python3 fetch_odds.py`. If it errors, show the error and stop — don't substitute lines from search results. Note each game's event id.
2. **Research (fresh web searches):**
   - Injury reports: official team/NFL injury reports and beat reporters (practice participation, Out/Doubtful/Questionable designations). Note the date of each report.
   - Current-season team stats: efficiency (EPA/play, success rate, DVOA if available), turnover margin, home/away splits, relevant matchup stats.
   - Analyst picks from 2–3 outlets (e.g. ESPN, The Athletic, Action Network). Treat these as context, not evidence of an edge.
   - **Recent player usage (last 3–4 games)** for every player relevant to a candidate: anyone in a prop, plus the starting QB, RB1 and top WRs/TE whose role drives a team-level pick. Use ESPN, Pro Football Reference or similar stat sites, and check snap count %, target share, carries and red-zone touches before raw yards or TDs. Then check the opposing defense's **recent** performance against that role (e.g. yards and targets allowed to slot WRs or RBs over the last few games, and who's covering), not just its season-long rank. See "Player trend rules" below.
   - Line movement: whether a line has moved since it opened (from line-move reporting in news coverage, with the source cited) and how much books disagree, using the `[books range ...]` in `fetch_odds.py` output.
   - **Historical ATS situational trends** (supporting context only; see "ATS trend rules" below). Search for trends that actually apply to this week's matchups, for example:
     - ATS record after a specific start (e.g. teams starting 0-3)
     - ATS record as a home/road favorite or underdog of a similar size to this week's line
     - ATS record off a bye or on short rest (only if one of the teams is in that spot this week)
     - Any other well-established situational trend that genuinely fits a specific matchup
     If nothing relevant applies, use no trend. Don't search until something turns up just to have one.
3. **Candidates:** Build about 5–6 candidates per requested tier (they can overlap across tiers), spanning different bet types (spread, moneyline, total, and a player prop if one is well supported). Don't default to spreads.
   - For a prop candidate, fetch its line with `python3 fetch_odds.py --event <id> --markets <market>` (e.g. `player_pass_yds`, `player_rush_yds`, `player_reception_yds`, `player_anytime_td`). Each call costs extra API credits, so only fetch props you're seriously considering. If no line is posted, drop the candidate.
4. **Evaluate each candidate** on:
   - Evidence strength (how specific, current, and well-sourced the case is).
   - Market type: spreads/totals/moneylines are sharp, liquid markets (prices are efficient, hard to beat); player props are thinner and more volatile (one injury, game script, or usage change swings them). **These are not equivalent confidence levels** — say so explicitly when comparing.
   - The single biggest risk that breaks the pick.
   - Parlay context: a leg only helps the group if it hits.
   - **Evidence weighting, strongest to weakest:** (1) this week's injury reports, (2) current-season efficiency stats and role-driven player usage trends, (3) line movement and market agreement, (4) analyst picks, historical ATS trends, and production spikes without a usage change. A trend can support a pick or add a caution, but **never make a trend the main reason for a pick**, and never let one override what the injury report or efficiency data says.
### ATS trend rules
- **Every trend needs a source and a sample size**, stated together: e.g. "13-4 ATS since 2021 (17 games), per [source]". If either one is missing, don't use the trend.
- **Sample size caveat:** if a trend covers fewer than ~20 games, label it **"small sample — directional only, not a strong signal."** Even 20–50 games is noisy, so present those as context too, not proof.
- **Assume the line already prices it in.** Well-known situational trends (bye weeks, rest, big favorites, 0-3 teams) are public, and the books and sharp bettors know them. Say explicitly why the trend may already be reflected in the line, and never present it as a hidden edge. A trend that runs against what the current-season data says is usually noise.
- Be wary of trends that were cherry-picked: odd cutoffs (e.g. "since 2019 on Sundays in October"), stacked conditions, or a source selling picks. The more specific the filter, the less it means.
- Use the most relevant trend per pick at most, not a list.

### Player trend rules
- **Role beats results.** Usage (snap %, target share, carries, red-zone touches) reflects role and predicts better than yards or TDs, which swing on a few plays.
- **Label every player trend as role-driven or variance-driven.** It's role-driven when usage changed for a reason you can name: a new starter, a teammate's injury, a return from injury, a scheme change. It's variance-driven when production jumped but usage stayed flat (e.g. two long TD runs inflating a rushing average, or a TD streak on the same red-zone share). **Call a variance-driven hot streak noise, say so plainly, and give it low weight**, never present it as a trend.
- **Check the matchup.** A rising role means less against a defense that has recently shut down that role (a shutdown corner shadowing the WR, a front that's stopped the run lately). Use the defense's recent games against that position, not just its season rank.
- **For props, check whether the line already moved.** The Odds API only gives current lines, so compare the current prop line with the player's recent production and with any earlier line cited in news or analyst coverage (cite it). If the line has already climbed to match the hot streak, **say the trend is priced in and isn't an edge**. Never recommend a prop as if the market hadn't noticed the trend.
- **Cite it fully.** When a player trend supports a pick, the Why bullet must state the specific metric, the sample (number of recent games), role-driven vs variance-driven, and whether the current line already reflects it. Example: "Target share up from 18% to 27% over the last 3 games since the WR2 went on IR (role-driven, ESPN); his receiving line rose from 48.5 to 61.5, so most of it is priced in."
- **Don't force it.** Use a player trend only when it's genuinely among the strongest evidence for a pick. If recent player data neither supports nor contradicts the line, say so in one clause or leave it out. Don't build a weak angle to fill space.

5. **Choose 3 picks per requested tier**, ranked #1–#3. The picks ranked #2 and #3 take the place of a runner-up.
6. **Log** each tier as its own entry in `picks_log.json`:
   ```json
   {"week": 5, "risk_tier": "safe|balanced|aggressive", "rank": 1, "date": "2026-10-10",
    "pick": "Team/Player + selection", "bet_type": "spread|moneyline|total|player prop",
    "line": "-3.5 (or ML)", "odds": "-110", "confidence": "High|Medium|Low",
    "confidence_note": "one line on what the confidence means for this market type",
    "reasoning": "1-2 sentence summary",
    "why": ["3-4 bullets, each citing a source or stat"],
    "breaks": "the single most likely failure",
    "trend": "OPTIONAL — omit the key entirely if no relevant trend. Trend + sample size + source + small-sample caveat + why it may be priced in",
    "sources": ["https://... or outlet + title"], "result": null}
   ```
   One entry per (week, tier, rank), with `rank` 1–3. If entries already exist for that week **and tier**, ask whether to replace the whole tier (all of its ranks). Other tiers for the week stay untouched.
7. **Publish:** `python3 build_site.py --push`. That rebuilds the homepage and the week page and commits and pushes everything. Report whether the push worked; if it fails, show the error.
8. **Reply**, about one screen per tier, grouped by tier (Safe → Balanced → Aggressive). The chat version is condensed because 9 full write-ups is too long; the week page has the full 3–4 Why bullets for every pick. Condense every tier the same way. For each pick:

   **[Tier] #[rank]: [team/player, bet type, line, odds]**
   - **Confidence:** [High/Medium/Low] — what that means given the market type
   - **Why:** the 2 strongest bullets, each citing a specific source or stat
   - **What breaks this pick:** the single most likely failure
   - **Relevant historical trend:** [trend + source + sample size + "small sample — directional only, not a strong signal" if under ~20 games + one clause on why it's likely priced in]. **Only include this line if a genuinely relevant trend was found;** otherwise leave the line out entirely (don't write "none").

   Flag any correlated picks (same game, or the same thing breaks both) right after the tier they're in.

   Then one combined **Sources used** list and the week page link (`https://kylebusher67.github.io/nfl-picks/week-N.html`).

   Confidence guide: **High** is rare — strong, multi-source, current evidence in any market. Player props should almost never be High. **Low** whenever key injury news is unresolved (e.g. a Questionable QB) or sources conflict. Confidence is about evidence quality, not the tier: an aggressive pick can be Medium, and a safe pick can be Low.

## Workflow: "update results"

When given a game outcome (e.g. "week 5 safe won", "Bills covered"):
1. Find the matching entries in `picks_log.json` by week and the team/player/game named. One game can settle several picks across tiers, so grade all of them. If it's unclear which entry is meant, ask.
2. Set `"result"` to `"win"`, `"loss"`, or `"push"`. If the user gives a final score instead, grade it against the logged line and show the math. Grade every tier that game affects.
3. Run `python3 build_site.py --push` so the result badges show on the site.
4. Report the season record (W-L-P) and win % = wins / (wins + losses), pushes excluded, **overall and per tier** (all ranks), and also for #1 picks only, since those are the ones most likely to go into the parlay.
5. Compare to the **~52.4% breakeven** needed at standard -110 odds (110/210). Since tiers use very different odds, also give each tier's breakeven from its logged odds (favorite -X: X/(X+100); underdog +X: 100/(X+100)). For example, a -700 pick needs 87.5% to break even. Keep it in perspective: small samples say very little about skill.
