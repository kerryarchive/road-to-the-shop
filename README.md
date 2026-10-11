# Road to the Shop (RepairIQ)

*Hacklanta 2026 · Georgia State University*

A gamified Streamlit app that teaches drivers what vehicle damage really costs, and how to avoid getting ripped off at the repair shop.

## The problem

After a pothole, a fender-bender, or a scraped mirror, most drivers walk into a shop with no idea what a fair repair costs. They can't tell an honest quote from a padded one, or a cheap fix from a dangerous one. The people who can least afford a $1,000 surprise are the most exposed to predatory markups.

## The solution

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
# open .env and paste a GROQ_API_KEY or GEMINI_API_KEY
streamlit run app.py
```

The app opens at http://localhost:8501. Without an API key it still runs; the shop offers an offline sample quote.

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests use a fake AI client, so they need no API key or internet.

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Use Groq Cloud (default provider) |
| `GEMINI_API_KEY` | Use Google Gemini via its OpenAI-compatible endpoint |
| `AI_PROVIDER` | Set to `gemini` to prefer Gemini when both keys exist |
| `GROQ_MODEL` / `GEMINI_MODEL` | Override the model name |

## Limitations

This is an educational game. Prices are illustrative and real repair costs vary by vehicle, shop, and region. It does not diagnose real vehicles and is not a substitute for a professional inspection.
