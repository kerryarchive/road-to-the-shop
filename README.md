# RepairIQ Academy

*Hacklanta 2026 · Georgia State University · Main track: Cox Social Good · Side challenges: MLH Best Use of Gemini API, Shock Tracker: Zero Data*

**A 3D driving game that teaches drivers what repairs really cost, and how to spot a bad quote before they sign it.**

You drive through Atlanta rush hour. Hit a pothole, a cone, or another car, and you're at the mechanic. You decide what to inspect, whether to repair or replace, and then pick one of three repair quotes written live by Google Gemini. The quotes are unlabeled, so you have to spot the padding and the shortcuts yourself.

**▶ Demo video:** [watch the 2-minute playthrough](#) <!-- replace # with your public YouTube/Drive link -->

## The problem, and who it's for

After a pothole or a fender-bender, most drivers walk into a repair shop with no idea what a fair price is. They can't tell an honest quote from a padded one, or a cheap fix from an unsafe one. The people hit hardest are the ones with the least room for error: students, first-time car owners, and families for whom a $1,000 surprise is a crisis.

RepairIQ Academy lets people practice that moment before it happens for real, in a few minutes, on a phone or laptop, with no account.

## How a round works

1. **Drive (up to 300 points).** 15 seconds, 3 lanes, traffic cars, cones, and potholes. Steer with ← → or A/D, the on-screen arrows, or a swipe.
2. **Mechanic challenge (up to 700 points).** After a crash, or from the clearly labeled "Try Mechanic Challenge (sample scenario)" button.
   - **Inspect (150):** what should the mechanic check first?
   - **Repair or replace (150):** decide from an inspection finding.
   - **Pick a quote (400):** three Gemini-written quotes shown as Shop A, B, and C. Each reads like that shop's own sales pitch. The dealer slips in add-ons the damage doesn't need; the budget shop mentions shortcuts like skipping the alignment or offering no warranty. Fair = 400, dealer = 150, budget = 0. The shops are revealed after you choose.
3. **Results.** Score out of 1,000, a grade, a breakdown, and three questions to ask before signing anything at a real shop.

## How the AI works

| Part | Handled by |
|---|---|
| Driving, obstacles, scoring, grades | Game code (`web/game.js`) |
| Inspection and repair-or-replace scenarios | Written by our team (`SCENARIOS` in `web/game.js`) |
| Quote prices, shop pitches, mechanic greeting, negotiation tips | **Google Gemini**, live, through `server.py` |
| Shop titles, risk labels, point values | Fixed in code, never decided by the AI |
| Checking the AI's reply | Python (`app.py`): pulls JSON out of messy replies, rejects unbelievable prices, fills missing tips, warns if prices aren't in the order budget < fair < dealer |

- **Grounding.** Gemini is told the fair quote must fall inside a reference price range for that damage, the dealer must be higher, and the budget lower. The ranges are illustrative game data, and the game says so.
- **No giveaways.** The prompt bans words like "overpriced" or "unsafe," so players have to read the pitches critically.
- **Reliability.** The server tries a list of Gemini models in order and moves on when one is busy, rate-limited, retired, or slower than 20 seconds. The request starts as soon as the challenge begins, so Gemini works while the player answers steps 1 and 2.
- **Honest fallback.** If there's no key or every model fails, the game shows sample quotes labeled **"not AI-generated"** with a note saying why. The demo never gets stuck.
- **Security.** The API key stays on the server and never reaches the browser. All AI text is inserted as plain text, never as HTML.

## Zero Data

RepairIQ Academy has no accounts, no logins, no profiles, no analytics, and no cookies. The browser stores nothing. The only data the game sends is the name of the obstacle you hit (for example `"pothole"`), to our own server, to get quotes. To write the quotes, the server sends Google Gemini only a short description of the in-game damage (for example, "blew the tire bead and bent the rim"). Nothing about the player is included: no personal information, IP address, or identifier. The server has no database and writes no files; while it runs, its terminal shows the standard request lines and nothing is saved. Everything resets when you close the tab.

## Run it locally

Requires Python 3.10 or newer.

```bash
git clone https://github.com/kerryarchive/road-to-the-shop.git
cd road-to-the-shop
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# optional: open .env and paste a GEMINI_API_KEY (free at https://aistudio.google.com/apikey)
python server.py
```

Open http://localhost:8000. To play on a phone, connect it to the same Wi-Fi and open `http://<your computer's IP>:8000`.

### Notes for judges

- **No API key needed to try it.** Without a key, the game runs fully and step 3 uses sample quotes clearly labeled "not AI-generated." Add a free `GEMINI_API_KEY` to `.env` to see live Gemini quotes.
- **Quick path to the AI part:** on the start screen, choose **Try Mechanic Challenge (sample scenario)**.
- There are no test accounts or credentials; nothing requires a login.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

52 automated tests cover game logic, AI reply parsing, model fallback, the server route, and the offline fallback. They use a fake AI client, so they need no key or internet.

## What existed before Hacklanta (disclosure)

All project code was written during the Hacklanta hacking period (Oct 9–11, 2026). We built on these existing tools:

- **[three.js](https://threejs.org) r170** for 3D rendering (MIT license, bundled in `web/vendor/` with its license file)
- **Flask** (web server), **Streamlit** (early prototype UI), **openai** Python SDK (used as the client for Gemini's OpenAI-compatible endpoint), **python-dotenv**, **pytest**
- **Google Gemini API** for the live quotes
- **AI coding assistants:** we used Claude (Anthropic) for planning, code, and tests, and ChatGPT to critique our project brief. Every design decision was made by our team.

We looked at an existing open-source car-diagnostics app for ideas, and used none of its code.

## The earlier Streamlit version

`app.py` also contains our first prototype, **Road to the Shop**: pick road hazards, get three AI quotes, and get graded on money left versus road safety. It shares the same AI code as the 3D game. Run it with `streamlit run app.py` (opens at http://localhost:8501).

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Live Gemini quotes (used in our demo) |
| `GEMINI_MODEL` | Optional: a comma-separated list of Gemini models to try in order |
| `GROQ_API_KEY` / `GROQ_MODEL` | Optional alternative provider. If both keys are set, set `AI_PROVIDER=gemini` to use Gemini |

## Limitations

RepairIQ Academy is an educational game. Inspection scenarios are written by our team, not AI analysis. Prices are illustrative; real repair costs vary by vehicle, shop, and region. It does not diagnose real vehicles and is not a substitute for a professional inspection.

## What's next

- **Photo check:** upload a photo of real damage and have Gemini explain what it sees and what to ask the shop.
- More hazards and scenarios, a Spanish option, and testing with real drivers to tune difficulty.

## Team

<!-- Replace with your names -->
- Kerry, ...
- ...
- ...
