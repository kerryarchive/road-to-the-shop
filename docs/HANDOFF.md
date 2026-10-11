# Handoff Report: RepairIQ Academy / Road to the Shop

**Date:** Oct 11, 2026 (Hacklanta, Georgia State University)
**Repo:** https://github.com/kerryarchive/road-to-the-shop (branch `main`)
**Purpose:** everything that was built and decided in Kerry's Claude Code session, so a teammate (and Claude) can pick it up and change it however they want.

---

## 1. Summary

We have a **working, tested 3D browser game called RepairIQ Academy**. You drive through Atlanta rush hour; if you crash, you go through a 3-step mechanic challenge where the third step uses **live Google Gemini** to write three competing repair quotes. You get a score out of 1,000.

The original **Streamlit version ("Road to the Shop")** still exists in the same repo and still works. Both versions share the same AI code.

Nothing here is final. The structure is simple on purpose, so it's easy to change.

---

## 2. What happened in this session (in order)

1. **Python setup on Kerry's laptop.** Python wasn't installed; installed Python 3.14, created `.venv`, installed requirements.
2. **Decided against Garaage.** We looked at https://github.com/immangat/Garaage as a possible base. It was rejected: it's a Flutter/Dart mobile app, needs an OBD2 car scanner, has no license, and using another team's 2024 project could break hackathon rules.
3. **Got the Streamlit app running.** Renamed `Hacklanta.py` to `app.py` so it matched the README.
4. **Connected Gemini.** `gemini-2.5-flash` is retired for new keys, so the model was updated.
5. **Added tests** (pytest) and made the first commit. Created the private GitHub repo and pushed.
6. **Wrote `docs/PROJECT_BRIEF.md`** for an outside AI (ChatGPT) to critique. ChatGPT suggested a 3D driving game with a scripted mechanic and no AI.
7. **Chose a "hybrid" plan instead:** a 3D driving game **plus** the live Gemini mechanic. That keeps all four prize tracks (Social Good, Creative, AI/ML, Best Use of Gemini).
8. **Built RepairIQ Academy** from scratch: three.js game, Flask server, mechanic challenge. Played it end to end in a headless browser at desktop and phone sizes.
9. **Fixed Gemini reliability.** `gemini-3.8-flash` was overloaded and timing out, so the app now tries a list of models in order.
10. **Rewrote the AI prompt** so each shop's quote reads like that shop's own sales pitch. Before, the AI's wording ("backyard cut-rate job") gave away the right answer.

---

## 3. How to run it

**One-time setup (Windows PowerShell):**
```powershell
git clone https://github.com/kerryarchive/road-to-the-shop.git
cd road-to-the-shop
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```
Then open `.env` and paste your own Gemini key after `GEMINI_API_KEY=` (free at https://aistudio.google.com/apikey). **Never commit `.env`.** It's already in `.gitignore`.

If `Activate.ps1` says "running scripts is disabled", run this once and try again:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Run:**

| What | Command | Opens at |
|---|---|---|
| 3D game (main demo) | `python server.py` | http://localhost:8000 |
| Streamlit version | `streamlit run app.py` | http://localhost:8501 |
| Tests (52, all passing) | `pytest` | n/a |

**Phone testing:** run `python server.py`, connect the phone to the same Wi-Fi, run `ipconfig` to find the laptop's IPv4 address, and open `http://THAT-IP:8000`. If Windows asks, allow Python through the firewall on private networks.

---

## 4. How RepairIQ Academy works

### Game flow (states in `web/game.js`)
`READY` → `DRIVING` → `MECHANIC` → `RESULTS`

### 1. Drive (up to 300 points)
- 15 seconds, 3 lanes, speed ramps up over time.
- Obstacles: **traffic cars, cones, potholes**. Each one maps to a damage type the AI knows:

| Obstacle | Hazard key | Damage story | Illustrative fair price |
|---|---|---|---|
| Traffic car | `sideswipe` | Smashed mirror, scratched door | $450–$1,300 |
| Cone | `cone` | Cracked front lower bumper lip | $150–$500 |
| Pothole | `pothole` | Blown tire bead, bent rim | $250–$700 |

- Controls: ← → or A/D, on-screen arrow buttons, or swipe.
- Points scale with time survived. A clean run gets 300 plus a maintenance tip.

### 2. Mechanic challenge (up to 700 points)
After a crash, or from the **"Try Mechanic Challenge (sample scenario)"** button, which is clearly labeled as a sample so it never pretends a crash happened.

| Step | Question | Points | Source |
|---|---|---|---|
| 1 | What should the mechanic inspect first? | 150 | Team-written scenario (`SCENARIOS` in `game.js`) |
| 2 | Repair or replace, given an inspection finding | 150 | Team-written scenario |
| 3 | Pick one of three quotes, shown as **Shop A / B / C** with no labels | Fair 400, dealer 150, budget 0 | **Live Gemini** through `server.py` |

- Every answer shows an explanation.
- After the player picks a quote, the game reveals which shop was which (Dealership OEM Overhaul / Scrapyard Patch / Certified Independent Repair).
- The AI request starts as soon as the challenge begins, so Gemini works while the player answers steps 1 and 2.

### 3. Results
Score out of 1,000, grade (A ≥ 850, B ≥ 700, C ≥ 550, D ≥ 400, F), a breakdown by section, and the AI's 3 "ask these before you sign anything" questions.

---

## 5. How the AI part works

- **The browser never sees the API key.** The game calls `POST /api/quotes` on our own Flask server (`server.py`), which calls Gemini.
- **The game controls what matters:** titles, risk labels, scoring and roadworthiness are fixed in code. The AI only writes prices, shop pitches, the mechanic greeting and tips.
- **Grounding:** the AI is told the fair quote must land inside the reference price range, the dealer quote must be higher, and the budget quote lower.
- **Shop pitches:** each quote is written as that shop's own friendly sales pitch. The dealer slips in add-ons the damage doesn't need; the budget shop mentions shortcuts like skipping the alignment or giving no warranty. The players have to spot the red flags themselves.
- **Validation in Python** (`app.py`): pulls JSON out of messy replies, rejects costs that aren't believable numbers, fills in missing tips, and warns if prices aren't in the order budget < fair < dealer.
- **Model fallback:** tries `gemini-3.5-flash`, then `gemini-3.1-flash-lite`, then `gemini-3.8-flash`, moving on when one is busy (503), rate-limited (429), retired (404) or slower than 20 seconds. You can override the list with `GEMINI_MODEL=model1, model2` in `.env`.
- **Offline fallback:** if there's no key or every model fails, the game shows sample quotes clearly labeled **"not AI-generated"**, plus a yellow note saying why. The demo never gets stuck.
- **Security:** all AI and server text is inserted with `textContent`, never as HTML.

---

## 6. Files

| File | What it is | Edit it to… |
|---|---|---|
| `web/game.js` | The whole 3D game (~900 lines): scene, driving, mechanic challenge, results | Change gameplay, scenarios, points, text |
| `web/style.css` | Look of the panels, buttons, HUD and touch controls | Change colors and layout |
| `web/index.html` | Page shell | Rarely needed |
| `web/vendor/` | three.js r170 (MIT license) | **Don't edit** |
| `server.py` | Flask server: serves `web/` and `/api/quotes` | Add API routes |
| `app.py` | Streamlit version **plus** shared data and AI code (`HAZARDS`, `SYSTEM_PROMPT`, `fetch_ai_quotes`, `build_offline_quotes`) | Change prices, the AI prompt, models |
| `tests/` | 52 pytest tests (fake AI, no internet needed) | Run `pytest` after changes |
| `CLAUDE.md` | Project context for Claude | Keep it updated |
| `docs/PROJECT_BRIEF.md` | The brief sent to ChatGPT (written **before** the 3D game) | Reference only |

### Quick "where do I change…" guide (all in `web/game.js` unless noted)

| Want to change | Look for |
|---|---|
| Round length | `ROUND_SECONDS` |
| Speed / difficulty | `START_SPEED`, `END_SPEED`, spawn gap in `update()` (`30 - 12 * progress`) |
| How often each obstacle appears | `weight` in `OBSTACLES` |
| Points | `DRIVE_POINTS_MAX`, `POINTS`, `QUOTE_POINTS`, `gradeFor()` |
| Mechanic questions and explanations | `SCENARIOS` |
| Maintenance tips | `MAINTENANCE_TIPS` |
| Disclaimer text | `DISCLOSURE` |
| Colors of cars and buildings | `trafficColors`, `buildingColors`, `makeCar(mat(0xd7263d))` for the player |
| Reference prices (`app.py`) | `HAZARDS` → `ref_low` / `ref_high` |
| What the AI is told (`app.py`) | `SYSTEM_PROMPT` |

**Rule:** if you add a new hazard, add it in **three places**: `HAZARDS` in `app.py`, `OBSTACLES` and `SCENARIOS` in `game.js`. A test fails if they don't match.

---

## 7. What's been verified

- 52 automated tests pass: game logic, scoring, AI parsing, model fallback, the server route, offline fallback.
- Full playthrough in headless Chrome at desktop (1280×800) and phone (390×844) sizes: no JavaScript errors, live Gemini quotes worked, and the offline fallback worked when Gemini was down.
- Live check of the new shop-pitch prompt on all 3 hazards: no giveaway words, prices in the right order, fair price inside the range.

**Not yet verified:**
- A real phone (touch controls on an actual device)
- Hosting online
- Real people playing it (difficulty, clarity)

---

## 8. Known issues and limitations

1. **Gemini can be slow or overloaded.** It took 5–16 seconds during testing. The fallback handles it, but step 3 may show "The estimator is writing up three quotes…" for a few seconds.
2. **Only one crash per round:** the first hit ends the drive. There's no multi-damage run like in the Streamlit version.
3. **Difficulty isn't tuned.** It may be too easy or too hard; needs real players.
4. **Prices are illustrative game data,** not a real pricing source. The UI says so.
5. **Graphics are simple blocks**, with no sound.
6. **Not hosted.** It needs the Python server, so a static host (GitHub Pages, Netlify) won't work. Options: Render.com free tier, or demo from a laptop.
7. **`docs/PROJECT_BRIEF.md` is out of date.** It describes the project before the 3D game.

---

## 9. Suggested next steps (pick what you like)

**Before the demo (high value):**
- [ ] Play it on a real phone and fix anything awkward
- [ ] Have 2–3 people play it; tune `ROUND_SECONDS`, speeds and spawn rate
- [ ] Decide on hosting (Render) vs. laptop demo
- [ ] Write and rehearse a 2-minute demo script: problem → drive → crash → mechanic → AI quotes → score
- [ ] Record a backup video of a full playthrough in case the Wi-Fi fails

**Nice to have:**
- [ ] Sound effects (crash, engine)
- [ ] A short "what you learned" summary on the results screen
- [ ] More hazards (e.g., road debris, curb strike), following the three-places rule above
- [ ] Leaderboard (needs storage; keep it simple)
- [ ] Spanish language option

---

## 10. Principles we agreed on

- **Honest labeling:** never present sample or offline data as AI output; team-written scenarios are labeled as such.
- **No overclaiming:** this is an educational game. No claims of accurate estimates, damage detection or fraud detection.
- **Keep it simple** enough for a beginner team to explain to judges.
- **One finished product** beats two half-finished ones.

---

## 11. Collaboration notes

- **Run `git pull` before you start, and push when you're done.** To avoid merge conflicts, try not to edit the same file at the same time as someone else.
- Each person uses **their own** Gemini key in their own `.env`.
- Commit messages so far end with a `Co-Authored-By: Claude` line because Claude Code made them. That's optional for your own commits.
