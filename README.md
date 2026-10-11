# RepairIQ Academy / Road to the Shop

*Hacklanta 2026 · Georgia State University*

Games that teach drivers what vehicle damage really costs, and how to avoid getting ripped off at the repair shop.

This repo has two front ends that share the same AI code (`app.py`):

| | What it is | Run |
|---|---|---|
| **RepairIQ Academy** (main demo) | A 3D driving game in the browser. Survive 15 seconds of Atlanta rush hour; crash and you face a 3-step mechanic challenge with live Gemini quotes. Score out of 1,000. Works on desktop and phone. | `python server.py` → http://localhost:8000 |
| **Road to the Shop** | The original Streamlit version: pick hazards, get three AI quotes, get graded on money vs. safety. | `streamlit run app.py` → http://localhost:8501 |

## RepairIQ Academy: how a round works

1. **Drive (up to 300 pts).** Three lanes of traffic, cones and potholes. Steer with ← → / A D, the on-screen arrows, or a swipe.
2. **Mechanic challenge (up to 700 pts),** after a crash, or from the "Try Mechanic Challenge" button as a clearly labeled sample scenario:
   - **Inspect (150):** what should the mechanic check first?
   - **Repair or replace (150):** decide based on an inspection finding.
   - **Pick a quote (400):** three AI-written quotes shown as Shop A/B/C with no labels. Fair = 400, dealer = 150, scrapyard = 0. The shops are revealed after you choose.
3. **Results:** score, grade, and the AI's questions to ask before signing anything.

Steps 1 and 2 are training scenarios written by the team. Step 3 uses live Gemini through `server.py`, which keeps the API key on the server. If the AI is unavailable, the game shows offline sample quotes labeled as not AI-generated.

## The problem

After a pothole, a fender-bender, or a scraped mirror, most drivers walk into a shop with no idea what a fair repair costs. They can't tell an honest quote from a padded one, or a cheap fix from a dangerous one. The people who can least afford a $1,000 surprise are the most exposed to predatory markups.

## The original Streamlit version

**Road to the Shop** turns that moment into a game you can practice before it happens for real:

1. **The Commute.** Drive an Atlanta road with $1,500 and a healthy car. Hit real-world hazards (a deep pothole, a construction cone, a tight parked car) and watch your Car Health drop.
2. **The AI Body Shop.** An LLM plays a gritty Atlanta estimator and returns three quotes as structured JSON: a padded **Dealership OEM Overhaul**, a dangerous **Scrapyard Patch**, and a **Certified Independent Repair** at fair market price. Each is shown against a reference fair range, along with three questions to ask so you don't get scammed.
3. **The Decision.** Pick a route. The game deducts the cost, sets your car's roadworthiness, and grades you on **Financial Health vs. Road Safety**.

## Hackathon tracks

- **Cox Automotive / Social Good:** consumer protection and financial literacy for drivers facing repair decisions, especially those with the least room for error.
- **Creative:** an urban road-hazard game paired with a negotiation simulator, instead of another form-based estimator.
- **AI/ML:** an LLM role-playing a domain expert with strict JSON output, validated in Python, grounded by a reference price range, with a deterministic fallback.

## How it works

| Part | Handled by |
|---|---|
| Hazards, damage, wallet, roadworthiness, grading | Python (deterministic) |
| Mechanic greeting, quote descriptions, prices, negotiation tips | LLM (Groq `llama-3.1-8b-instant` or Gemini) |
| JSON parsing, cost checks, price-order sanity check | Python validation |
| No key / API down | Offline sample quotes, clearly labeled as not AI-generated |

All AI text is HTML-escaped before display. Reference prices are illustrative game data, not real quotes.

## Run it locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
# open .env and paste a GEMINI_API_KEY (or GROQ_API_KEY)
python server.py                 # 3D game:  http://localhost:8000
streamlit run app.py             # Streamlit version: http://localhost:8501
```

Without an API key both still run, with offline sample quotes. To test on a phone, run `python server.py`, connect the phone to the same Wi-Fi, and open `http://<your computer's IP>:8000` (allow Python through the Windows firewall on private networks).

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests use a fake AI client, so they need no API key or internet.

## Credits

3D rendering uses [three.js](https://threejs.org) r170 (MIT license, bundled in `web/vendor/` with its license file). All game code was written during the hackathon.

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Use Groq Cloud (default provider) |
| `GEMINI_API_KEY` | Use Google Gemini via its OpenAI-compatible endpoint |
| `AI_PROVIDER` | Set to `gemini` to prefer Gemini when both keys exist |
| `GROQ_MODEL` / `GEMINI_MODEL` | Override the model; `GEMINI_MODEL` can be a comma-separated list tried in order |

## Limitations

This is an educational game. Inspection scenarios in the 3D game are written by the team, not AI analysis. Prices are illustrative and real repair costs vary by vehicle, shop, and region. It does not diagnose real vehicles and is not a substitute for a professional inspection.
