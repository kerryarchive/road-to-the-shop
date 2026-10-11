# CLAUDE.md: Project context for Road to the Shop (RepairIQ)

This file carries over context from a planning and build conversation in the Claude app (Oct 10, 2026). Read it before making changes.

## Who we are and what this is for

- Three-person college team at **Hacklanta** (36-hour hackathon, Georgia State University, Atlanta).
- Beginner-to-intermediate Python, intro web dev. **Explain decisions in plain language.** Keep the architecture simple.
- Target prizes: **Cox Automotive / Social Good** (primary), **AI/ML**, **Creative**, and **Best Use of Gemini API**.

## Project history (how we got here)

1. **ClaimShield AI** (first idea): photo-based car damage assessment with Gemini, repair-cost ranges, deductible/insurance decision support, and repair-quote comparison. Core principle: be honest about uncertainty and never invent precise prices.
2. **RepairIQ** (teammate's plan): photo → damage analysis → repair estimate → replacement parts (eBay) → vehicle log (Supabase), plus Groupon deals. The teammate's audit found the candidate GitHub repos don't produce real damage results without custom weights.
3. **Merge:** RepairIQ became the core, with ClaimShield ideas as add-ons (deductible check, mechanic questions and adjuster summary, quote checker, language option). Proposed dropping Groupon and deferring Supabase.
4. **Game idea:** the team discussed adding a game. Options were a game mode inside RepairIQ, or a full pivot to an Atlanta hidden-gems explorer. Recommendation was not to mix two products.
5. **Current direction (what's built):** **"Road to the Shop"**, a gamified Streamlit app that combines a road-hazard simulation with an AI mechanic-quote simulator. This is what the code implements now.

A shared team doc with the merged plan exists on claude.ai ("RepairIQ — Team Catch-Up Report"). It predates the game build.

## What's in this folder

| File | Purpose |
|---|---|
| `app.py` | The whole app (~875 lines), single file, three stages |
| `requirements.txt` | `streamlit==1.65.0`, `openai==3.26.1`, `python-dotenv==1.2.3` |
| `requirements-dev.txt` | Adds `pytest` for the tests |
| `tests/test_app.py` | pytest suite (no API key or internet needed) |
| `.env.example` | Copy to `.env`; set `GROQ_API_KEY` or `GEMINI_API_KEY` |
| `README.md` | Hackathon docs: problem, solution, tracks, run steps |
| `.gitignore` | Keeps `.env` and `.venv/` out of Git |

Run: `streamlit run app.py` (inside an activated `.venv`).

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
- **AI provider:** uses the `openai` package for both providers. Groq is `https://api.groq.com/openai/v1` with `llama-3.1-8b-instant`. Gemini goes through its OpenAI-compatible endpoint (`GEMINI_MODEL` defaults to `gemini-3.8-flash`, which may need updating). `AI_PROVIDER=gemini` prefers Gemini when both keys are set.
- **The game controls the numbers that matter.** Titles, risk labels, and roadworthiness come from `QUOTE_META`, not the AI. The AI writes only prices, descriptions, the greeting, and tips.
- **Grounding:** each hazard has an illustrative `ref_low`/`ref_high` range. The fair quote is told to land inside it, and the shop shows the range so players can judge offers. These are game numbers, not real prices, and the UI says so.
- **Validation:** `extract_json()` handles code fences and stray text. `validate_payload()` coerces and checks costs ($1–$50,000), pads tips to 3, and warns if the prices aren't ordered budget < fair < dealer.
- **Error handling:** JSON mode first, then one retry without it. Friendly messages for a bad key, rate limit, no connection, or server error. Retry button.
- **Offline fallback:** with no key, or if the AI fails, `build_offline_quotes()` makes deterministic sample quotes, **clearly labeled as not AI-generated**.
- **Security:** all AI text is HTML-escaped with `esc()` before going into `unsafe_allow_html` markup.
- Uses `width="stretch"` (not the deprecated `use_container_width`).
- `main()` only runs under `if __name__ == "__main__"`, so the logic can be imported in tests.

## Testing status

- `tests/test_app.py`: 34 pytest tests covering game logic, scoring, JSON parsing and validation, `fetch_ai_quotes` (through a fake client, no network), and the offline fallback. Run `pytest` after `pip install -r requirements-dev.txt`.
- Verified Oct 11, 2026: the real Streamlit app runs end to end (commute, shop, scorecard), both offline and with live Gemini (`gemini-3.8-flash`). `gemini-2.5-flash` is retired for new keys.

## Principles to keep

- Honest labeling: never show sample or fallback data as live AI output.
- Don't claim accurate estimates, hidden-damage detection, fraud detection, or premium predictions. This is an educational game.
- Prefer small, understandable changes; explain them before making them; preserve working code.
- One finished product beats two half-finished ones.

## Open questions for the team

- Final name: "Road to the Shop", "RepairIQ", or both?
- Bring back any ClaimShield features (photo upload with Gemini vision, deductible check, quote checker) as a bonus mode?
- Hours left in the hackathon, and who owns which part of the code.
