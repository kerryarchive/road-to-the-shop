# Project Brief: Road to the Shop (RepairIQ)

**Purpose of this document:** a complete picture of our hackathon project as it exists today, so you can analyze it and help us narrow it down to exactly what we should build and demo. Everything below describes the real, current state of the code unless it says "idea" or "open question."

---

## 1. Context

- **Event:** Hacklanta, a 36-hour hackathon at Georgia State University in Atlanta.
- **Team:** three college students. Beginner-to-intermediate Python, intro-level web development. We need a simple architecture we can understand, explain and change ourselves.
- **Prize tracks we are targeting:**
  1. **Cox Automotive / Social Good** (primary): consumer protection and financial literacy for drivers.
  2. **AI/ML**
  3. **Creative**
  4. **Best Use of Gemini API**
- **Time remaining:** unknown or not yet decided; please factor it in as a question.

## 2. The problem we're solving

After a pothole, a fender-bender or a scraped mirror, most drivers walk into a repair shop with no idea what a fair repair costs. They can't tell an honest quote from a padded one, or a cheap fix from a dangerous one. The people who can least afford a $1,000 surprise are the most exposed to predatory markups.

## 3. What we built: "Road to the Shop"

A gamified web app (Python + Streamlit) where you take damage on an Atlanta road, get three competing repair quotes from an AI mechanic, pick one, and get graded on money vs. safety. The goal is to let people practice the shop visit before it happens for real.

### Stage 1: The Commute
- The player starts with **Car Health 100%** and **Wallet $1,500**.
- Location flavor text: "Downtown Connector, rush hour."
- **The "driving" is three buttons, not an actual driving game.** Each click applies one hazard:

| Hazard | Health lost | Damage | Illustrative fair repair range |
|---|---|---|---|
| Deep Atlanta Pothole | −25 | Blew the tire bead, bent the rim | $250–$700 |
| Construction Zone Traffic Cone | −15 | Cracked the front lower bumper lip | $150–$500 |
| Sideswiping a Tight Parked Car | −35 | Smashed side mirror, scratched door | $450–$1,300 |

- Hazards can be hit repeatedly; health stops at 0% ("Your car is undriveable. Call a tow.").
- The dashboard shows health, wallet, a progress bar and a damage log with severity badges.
- "Pull into Repair Shop" unlocks once there is any damage.

### Stage 2: The AI Body Shop
- The damage log is sent to an LLM (currently **Google Gemini, `gemini-3.8-flash`**), which plays a blunt Atlanta estimator.
- The AI returns strict JSON containing:
  - a 2-sentence **mechanic greeting**
  - three **quotes**, each with a cost and description:
    - **Dealership OEM Overhaul:** overpriced, padded with upsells
    - **Scrapyard Patch:** cheap but unsafe
    - **Certified Independent Repair:** fair market price
  - three **negotiation questions** to ask the shop
- The screen shows the reference fair range ("illustrative game data, not a real quote") so the player can judge each offer.
- The player can also go back to the road, retry the AI, or use the offline sample quote.

**Real example output** (pothole + sideswipe, reference range $700–$2,000):
- Greeting: "Those metal plates and craters on Moreland Avenue chewed your rim up, and that tight parking deck scrape didn't do you any favors either..."
- Dealer **$3,280** (inflated labor, unnecessary two-door repaint), Scrapyard **$490** (hammered rim, rattle-can paint), Fair **$1,380** (reconditioned OEM wheel, alignment, spot-blend paint)
- Tips like: "Can you break down the paint labor to show if you're charging for a full two-panel blend or just spot-refinishing the damaged door?"

### Stage 3: Scorecard
- Choosing a route deducts its cost from the wallet (the wallet can go negative, which shows a "repair loan" warning).
- Roadworthiness is fixed by the game, not the AI: **Dealer 100%, Scrapyard 45%, Fair 95%**.
- **Score = 50% Financial Health (wallet ÷ $1,500) + 50% Road Safety (roadworthiness)**, graded A (≥85), B (≥70), C (≥55), D (≥40), F.
- Verdict messages:
  - Fair: "Smart negotiator. You skipped $X of dealer padding."
  - Dealer: "Safe, but you got upsold. You paid $X more than a fair shop."
  - Scrapyard: "Cheap now, risky later. Your car is only 45% roadworthy."
- An expander lists what to take to a real shop. "Play Again" resets everything.

## 4. How the AI part works (AI/ML and Gemini tracks)

- **The game controls the numbers that matter.** Titles, risk labels, roadworthiness and grading are fixed in Python. The AI writes only prices, descriptions, the greeting and the tips.
- **Grounding:** each hazard has a reference price range. The AI is told the fair quote must land inside the combined range, the dealer must be higher and the scrapyard lower.
- **Validation in Python:** extracts JSON even if wrapped in code fences or extra text; rejects costs that aren't numbers or are outside $1–$50,000; fills in missing tips; warns if prices aren't in the order scrapyard < fair < dealer.
- **Retry:** first attempt uses JSON mode; if that fails, one retry without it.
- **Friendly errors** for a bad key, rate limit, no internet or server error.
- **Offline fallback:** with no key or if the AI fails, deterministic sample quotes built from the reference table, **clearly labeled "not AI-generated."**
- **Security:** all AI text is HTML-escaped before display.
- **Providers:** Gemini (current) or Groq (`llama-3.1-8b-instant`), both called through the `openai` Python package's compatible endpoints. Set by `GEMINI_API_KEY` / `GROQ_API_KEY` in a `.env` file.

## 5. Tech and code

| Item | Detail |
|---|---|
| Language / framework | Python 3.14, Streamlit 1.65 |
| Packages | `streamlit`, `openai`, `python-dotenv`; `pytest` for tests |
| Code size | One file, `app.py`, about 875 lines |
| Tests | `tests/test_app.py`, 34 pytest tests, all passing (game logic, scoring, AI parsing, error handling, offline fallback; uses a fake AI, no internet needed) |
| Run | `streamlit run app.py` → opens at http://localhost:8501 |
| Repo | Private GitHub repository |
| Verified | Runs end to end in a real browser session, both offline and with live Gemini |

## 6. Honest weaknesses and gaps

1. **The "game" is thin.** The commute is three buttons. There's no movement, timing, map, randomness or skill. Judges for "Creative" may see it as a form with emojis.
2. **The optimal choice is obvious.** The Fair route almost always wins, and the labels basically tell you so ("Overpriced / Predatory", "Dangerous"). There's little real decision-making or learning by discovery.
3. **One car only.** Quotes assume "a typical mid-size sedan." No make, model or year.
4. **Prices are illustrative, not real data.** The reference ranges are made up for the game. There's no real pricing source (e.g., Cox Automotive / KBB / RepairPal-style data).
5. **No negotiation.** The tips are shown, but the player can't actually use them to haggle with the mechanic.
6. **Only text AI.** We don't yet use Gemini's vision (photos) or multi-turn chat, which may matter for "Best Use of Gemini."
7. **Nothing carries over.** No accounts, history, leaderboard or multiple days of driving.
8. **No real-world use.** A driver with an actual damaged car can't use this to check a real quote.

## 7. Ideas we considered (not built)

- **ClaimShield AI** (our first idea): upload a photo of car damage → Gemini assesses it → repair-cost range, insurance deductible check (is it worth claiming?), quote comparison. Principle: be honest about uncertainty and never invent precise prices.
- **RepairIQ** (a teammate's plan): photo → damage analysis → estimate → replacement parts (eBay) → vehicle log (Supabase) → Groupon deals. An audit found open-source damage-detection repos don't work without custom-trained models.
- **Add-on ideas from those plans:** deductible checker, "questions for your mechanic" and adjuster summary, real-quote checker (paste a quote, get a fairness verdict), language option (e.g., Spanish).
- **Garaage** (an existing GitHub project, Flutter mobile app from a 2024 Gemini competition): OBD2 check-engine code explanations, Gemini chatbot with photos, AR part identification. **We decided not to use it or its ideas.** It's a different language, needs hardware we don't have, has no license, and could violate hackathon rules about building during the event.
- **Atlanta hidden-gems explorer game:** a full pivot, rejected so we don't mix two products.

## 8. Principles we want to keep

- Honest labeling: never present sample or fallback data as live AI output.
- Don't claim accurate estimates, hidden-damage detection, fraud detection or insurance predictions. It's an educational game.
- Keep the architecture simple enough for beginners to explain to judges.
- One finished, polished product beats two half-finished ones.

## 9. Open questions for the team

- Final name: "Road to the Shop", "RepairIQ", or both?
- How many hours are left, and who owns which part?
- Should we bring back a ClaimShield feature (photo upload, deductible check, real-quote checker) as a bonus mode, or keep it pure game?

## 10. What we want from you

Please analyze this and give us:

1. **The single clearest version of this product** in one or two sentences: who it's for, what it does, why it matters.
2. **Which prize track(s) to really go after,** and what judges in each will look for that we're missing.
3. **A ranked list of changes** that would most improve the demo (especially for weaknesses 1, 2, 5 and 6), each with rough effort (small / medium / large) for a beginner Python team using Streamlit.
4. **What to cut or not build,** so we stay focused.
5. **A 2-minute demo script** for the final version.
6. **Any risks** (technical, honesty or hackathon-rule) we haven't thought of.
