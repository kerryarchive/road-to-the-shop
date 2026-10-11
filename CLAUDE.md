# CLAUDE.md: Project context for RepairIQ Academy (formerly Road to the Shop)

This file carries over context from planning and build sessions in the Claude app and Claude Code (Oct 10–11, 2026). Read it before making changes.

## Who we are and what this is for

- Three-person college team at **Hacklanta** (36-hour hackathon, Georgia State University, Atlanta).
- Beginner-to-intermediate Python, intro web dev. **Explain decisions in plain language.** Keep the architecture simple.

## Deadlines, tracks, and submission (Hacklanta 2026)

- **Hacking ends 9:00 AM Sunday, Oct 11, 2026. Our target is to submit by 8:00 AM.** After that, don't start new features; only fix bugs and finish the submission.
- **Main track (only one allowed): Cox Social Good.**
- **Side challenges:** MLH Best Use of Gemini API, and Shock Tracker: Zero Data.
- **To submit:**
  1. Public GitHub repo: https://github.com/kerryarchive/road-to-the-shop (confirmed public)
  2. Public 2–3 minute demo video (YouTube or Google Drive), linked in `README.md` and Devpost
  3. Devpost write-up, drafted in `docs/DEVPOST.md` (includes the full checklist)
  4. The Google Form posted in Discord
  Only one team member submits Devpost and the form.
- **Judging:** 9:30–11:30 AM in the State Ballroom, 3-minute pitch + 2-minute Q&A, 2 judges per table. Judges score track fit, demo polish, presentation, and how clear and compelling the use case is. Pitch script, Q&A prep, and video plan are in `docs/PITCH.md`.
- **Zero Data claim** (README, Devpost): no accounts, logins, analytics, cookies, or browser storage; the server has no database and writes no files. Keep it that way: don't add tracking, storage, or logging of player data.

## Project history (how we got here)

1. **ClaimShield AI** (first idea): photo-based car damage assessment with Gemini, repair-cost ranges, deductible/insurance decision support, and repair-quote comparison. Core principle: be honest about uncertainty and never invent precise prices.
2. **RepairIQ** (teammate's plan): photo → damage analysis → repair estimate → replacement parts (eBay) → vehicle log (Supabase), plus Groupon deals. The teammate's audit found the candidate GitHub repos don't produce real damage results without custom weights.
3. **Merge:** RepairIQ became the core, with ClaimShield ideas as add-ons (deductible check, mechanic questions and adjuster summary, quote checker, language option). Proposed dropping Groupon and deferring Supabase.
4. **Game idea:** the team discussed adding a game. Options were a game mode inside RepairIQ, or a full pivot to an Atlanta hidden-gems explorer. Recommendation was not to mix two products.
5. **First build:** **"Road to the Shop"**, a gamified Streamlit app that combines a road-hazard simulation with an AI mechanic-quote simulator. It still works (`streamlit run app.py`).
6. **Current direction (main demo):** **RepairIQ Academy**, a 3D driving game (`web/` + `server.py`) with the live Gemini mechanic. See the section below. Judge-facing docs: `README.md`, `docs/DEVPOST.md`, `docs/PITCH.md`; teammate handoff: `docs/HANDOFF.md`.

A shared team doc with the merged plan exists on claude.ai ("RepairIQ — Team Catch-Up Report"). It predates the game build.

## What's in this folder

| File | Purpose |
|---|---|
| `app.py` | Streamlit version (single file, three stages) **and** the shared game data + AI code (`HAZARDS`, `fetch_ai_quotes`, `build_offline_quotes`) |
| `server.py` | Flask server for the 3D game: serves `web/` and `POST /api/quotes` (keeps the API key off the browser) |
| `web/` | **RepairIQ Academy**, the 3D game: `index.html`, `style.css`, `game.js`, and `vendor/` (three.js r170, MIT) |
| `requirements.txt` | `streamlit==1.65.0`, `openai==3.26.1`, `python-dotenv==1.2.3`, `flask==3.1.2` |
| `requirements-dev.txt` | Adds `pytest` for the tests |
| `tests/` | pytest suites for `app.py` and `server.py` (no API key or internet needed) |
| `docs/DEVPOST.md` | Devpost copy-paste kit and submission checklist |
| `docs/PITCH.md` | 3-minute pitch script, Q&A prep, demo video plan |
| `docs/HANDOFF.md` | Full handoff report: what was built, how to run and change it |
| `docs/PROJECT_BRIEF.md` | Brief written for an outside AI to analyze the project (predates the 3D game) |
| `.env.example` | Copy to `.env`; set `GROQ_API_KEY` or `GEMINI_API_KEY` |
| `README.md` | Hackathon docs: problem, solution, tracks, run steps |
| `.gitignore` | Keeps `.env` and `.venv/` out of Git |

Run (inside an activated `.venv`): `python server.py` for the 3D game (http://localhost:8000), or `streamlit run app.py` for the Streamlit version.

## RepairIQ Academy (the 3D game, main demo since Oct 11)

Built after the team chose a "hybrid" plan: a 3D driving game (instead of the Streamlit button "commute") plus the existing live Gemini mechanic. The game code was written from scratch during the hackathon; only three.js is third-party.

- **States in `game.js`:** `READY` → `DRIVING` → `MECHANIC` → `RESULTS`.
- **Drive:** 15 s, 3 lanes, speed ramps up. Obstacles map to `HAZARDS` keys: traffic car → `sideswipe`, cone → `cone`, pothole → `pothole`. Up to 300 points by time survived. Keyboard, on-screen arrows, or swipe.
- **Mechanic challenge (700):** step 1 what to inspect (150) and step 2 repair vs. replace (150) use team-written `SCENARIOS` in `game.js`; step 3 shows the AI quotes as unlabeled Shop A/B/C (fair 400, dealer 150, budget 0) and reveals them after the pick. Quotes are requested as soon as the mechanic starts, so the AI works while the player answers steps 1–2.
- **"Try Mechanic Challenge"** loads a sample scenario that is labeled as such (no fake crash).
- All server/AI text is inserted with `textContent`, never `innerHTML`.
- A test checks that every `HAZARDS` key has an obstacle and a scenario in `game.js`. Keep them in sync when adding hazards.

## How `app.py` works

**Stages** (stored in `st.session_state.stage`): `commute` → `shop` → `scorecard`.

1. **Commute.** Start with Car Health 100% and Wallet $1,500. Three hazards in `HAZARDS`:
   - Deep Atlanta Pothole: −25, blows tire bead and bends rim
   - Construction Zone Traffic Cone: −15, cracks the front lower bumper lip
   - Sideswiping a Tight Parked Car: −35, smashes the mirror and scratches the door
   
   The dashboard shows metrics, a progress bar, and a damage log with severity badges. The "Pull into Repair Shop" button is enabled once there's any damage.
2. **AI Body Shop.** `fetch_ai_quotes()` sends the damage log to the LLM, which must return JSON with `mechanic_greeting`, `quote_dealer`, `quote_budget`, `quote_fair` (each with `title`, `cost`, `description`, `risk`), and `negotiation_tips` (3). The quotes appear as three cards via `st.columns(3)`.
3. **Scorecard.** Choosing a route deducts its cost and sets roadworthiness (Dealer 100, Budget 45, Fair 95). `compute_score()` grades 50% Financial Health and 50% Road Safety (A–F). There's a "Play Again" reset.

**Key design decisions:**
- **AI provider:** uses the `openai` package for both providers. Groq is `https://api.groq.com/openai/v1` with `llama-3.1-8b-instant`. Gemini goes through its OpenAI-compatible endpoint. `GEMINI_MODEL` is a comma-separated list tried in order (default `DEFAULT_GEMINI_MODELS`: `gemini-3.5-flash, gemini-3.1-flash-lite, gemini-3.8-flash`); on a timeout, 429, 404 or 5xx the next model is tried. On Oct 11 `gemini-3.8-flash` was often overloaded or timing out, which is why it's last. `AI_PROVIDER=gemini` prefers Gemini when both keys are set.
- **The game controls the numbers that matter.** Titles, risk labels, and roadworthiness come from `QUOTE_META`, not the AI. The AI writes only prices, descriptions, the greeting, and tips.
- **Grounding:** each hazard has an illustrative `ref_low`/`ref_high` range. The fair quote is told to land inside it, and the shop shows the range so players can judge offers. These are game numbers, not real prices, and the UI says so.
- **Validation:** `extract_json()` handles code fences and stray text. `validate_payload()` coerces and checks costs ($1–$50,000), pads tips to 3, and warns if the prices aren't ordered budget < fair < dealer.
- **Error handling:** JSON mode first, then one retry without it. Friendly messages for a bad key, rate limit, no connection, or server error. Retry button.
- **Offline fallback:** with no key, or if the AI fails, `build_offline_quotes()` makes deterministic sample quotes, **clearly labeled as not AI-generated**.
- **Security:** all AI text is HTML-escaped with `esc()` before going into `unsafe_allow_html` markup.
- Uses `width="stretch"` (not the deprecated `use_container_width`).
- `main()` only runs under `if __name__ == "__main__"`, so the logic can be imported in tests.

## Testing status

- 52 pytest tests in `tests/` covering game logic, scoring, JSON parsing and validation, `fetch_ai_quotes` incl. model fallback (fake client, no network), the offline fallback, and the `/api/quotes` route. Run `pytest` after `pip install -r requirements-dev.txt`.
- Verified Oct 11, 2026: the Streamlit app runs end to end, offline and with live Gemini. The 3D game was played end to end in headless Chrome at desktop (1280×800) and phone (390×844) sizes with no JS errors, with both live Gemini quotes and the offline fallback. `gemini-2.5-flash` is retired for new keys.
- **Not yet done:** a test on a real phone, and hosting it online.

## Principles to keep

- Honest labeling: never show sample or fallback data as live AI output.
- Don't claim accurate estimates, hidden-damage detection, fraud detection, or premium predictions. This is an educational game.
- Prefer small, understandable changes; explain them before making them; preserve working code.
- One finished product beats two half-finished ones.

## Open questions for the team

- Resolved: the name is **RepairIQ Academy**. Photo upload with Gemini vision is listed as "what's next", not built.
- Still open: demo video link and team names (placeholders in `README.md` and `docs/DEVPOST.md`).
