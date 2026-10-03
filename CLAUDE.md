# Bozo Parlay — Weekly NFL Pick Tool

A 6-person friend-group parlay pool: each week one person's pick becomes one leg of a shared 6-leg parlay. This is for fun. Never oversell confidence or imply the process has a proven edge against sportsbook lines — the books' prices already reflect most public information.

## Files
- `fetch_odds.py` — pulls current lines from the-odds-api.com (key in `.env` as `ODDS_API_KEY`). Stdlib only, Python 3.9+. Saves raw data to `odds_latest.json`.
- `picks_log.json` — JSON array of weekly picks (create as `[]` if missing).
- `.env` — secret. Never print, echo, or commit the key.

## Hard rules
- **Never use memory for current-week facts** (injuries, records, lines, stats, who's starting). Every fact in a pick must come from this session's `fetch_odds.py` output or a fresh web search.
- **Lines and odds come only from `fetch_odds.py`.** Don't scrape or fetch sportsbook sites. If a line isn't in the API output, don't quote it.
- **If reliable current info is thin, say so plainly.** Lower the confidence or say "no strong pick this week" rather than force a confident-sounding answer.
- Always state today's date and confirm the NFL week number via search before analyzing.

## Workflow: "generate this week's pick" (or similar)

1. **Lines:** Run `python3 fetch_odds.py`. If it errors, show the error and stop — don't substitute lines from search results. Note each game's event id.
2. **Research (fresh web searches):**
   - Injury reports: official team/NFL injury reports and beat reporters (practice participation, Out/Doubtful/Questionable designations). Note the date of each report.
   - Current-season team stats: efficiency (EPA/play, success rate, DVOA if available), turnover margin, home/away splits, relevant matchup stats.
   - Analyst picks from 2–3 outlets (e.g. ESPN, The Athletic, Action Network). Treat these as context, not evidence of an edge.
3. **Candidates:** Build 3–5 candidates spanning different bet types (spread, moneyline, total, and a player prop if one is well supported). Don't default to spreads.
   - For a prop candidate, fetch its line with `python3 fetch_odds.py --event <id> --markets <market>` (e.g. `player_pass_yds`, `player_rush_yds`, `player_reception_yds`, `player_anytime_td`). Each call costs extra API credits, so only fetch props you're seriously considering.
4. **Evaluate each candidate** on:
   - Evidence strength (how specific, current, and well-sourced the case is).
   - Market type: spreads/totals/moneylines are sharp, liquid markets (prices are efficient, hard to beat); player props are thinner and more volatile (one injury, game script, or usage change swings them). **These are not equivalent confidence levels** — say so explicitly when comparing.
   - The single biggest risk that breaks the pick.
   - Parlay context: a leg only helps the group if it hits — a heavy favorite moneyline (e.g. -300) is a legitimate option here even though it's poor standalone value.
5. **Choose ONE** recommendation and one runner-up.
6. **Log** by appending to `picks_log.json`:
   ```json
   {"week": 5, "date": "2026-10-03", "pick": "Team/Player + selection", "bet_type": "spread|moneyline|total|player prop", "line": "-3.5", "odds": "-110", "confidence": "High|Medium|Low", "reasoning": "1-2 sentence summary", "sources": ["url or outlet + title"], "result": null}
   ```
   If an entry for that week already exists, ask whether to replace it rather than adding a duplicate.
7. **Reply in exactly this format, about one screen total** (a decision with reasoning, not a research report):

   - **This Week's Pick:** [team/player, bet type, line, odds]
   - **Confidence:** [High/Medium/Low] — one line on what that means given the market type (e.g. "Medium for a sharp spread market = a reasonable lean, not an edge over the book")
   - **Why:**
     - 3–4 bullets, each citing a specific source or stat
   - **What breaks this pick:** the single most likely failure
   - **Runner-up:** one alternative, one sentence why
   - **Sources used:** short list

   Confidence guide: **High** is rare — strong, multi-source, current evidence in any market. Player props should almost never be High. **Low** whenever key injury news is unresolved (e.g. a Questionable QB) or sources conflict.

8. **Publish:** Overwrite `index.html` with this week's pick (same structure and CSS as the existing file: pick + line/odds, confidence badge + note, Why bullets, What breaks this pick, Runner-up, sources footer). Then commit `index.html` and `picks_log.json` and `git push`. GitHub Pages serves it at https://kylebusher67.github.io/nfl-picks/ (allow a minute or two to update).

## Workflow: "update results"

When given a game outcome (e.g. "week 5 won", "Bills covered"):
1. Find the matching entry in `picks_log.json` by week (if unclear which entry, ask).
2. Set `"result"` to `"win"`, `"loss"`, or `"push"`. If the user gives a final score instead, grade it against the logged line and show the math.
3. Report season record (W-L-P) and win % = wins / (wins + losses), pushes excluded.
4. Compare to the **~52.4% breakeven** needed at standard -110 odds (110/210). Note briefly when logged picks were at odds other than -110 (e.g. heavy favorites need a much higher hit rate), and keep it in perspective: small samples say very little about skill.
