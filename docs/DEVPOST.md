# Devpost submission: copy-paste kit

Everything below is ready to paste into Devpost. Replace anything in **[brackets]**.

## Submission checklist (deadline: 9:00 AM Sunday, aim for 8:00)

- [ ] Repo is **public**: GitHub → Settings → General → Danger Zone → Change visibility → Public (history checked: no keys or private info)
- [ ] Demo video (2–3 min) uploaded to YouTube or Google Drive and set to **Public**
- [ ] Video link added to the top of `README.md` and to Devpost
- [ ] Team names added to `README.md` and Devpost
- [ ] Devpost: title, tagline, write-up, "Built with", links, track, side challenges
- [ ] Main track: **Cox Social Good** (only one allowed)
- [ ] Side challenges (max 3): **MLH Best Use of Gemini API**, **Shock Tracker: Zero Data**
- [ ] **Google Form** submitted (link posted in Discord) with the Devpost link, project name, team details, track, and challenges
- [ ] Only **one** team member submits Devpost and the form
- [ ] Final check: open the repo and video links in a private/incognito window to confirm they work

---

## Project name

RepairIQ Academy

## Tagline (Devpost "elevator pitch", max 200 characters)

A 3D driving game that teaches drivers what repairs really cost, then makes them spot the padded and the unsafe quote, written live by Gemini, before a real shop does it to them.

## About the project (Devpost write-up)

### Inspiration

After a pothole or a fender-bender, most drivers walk into a repair shop with no idea what a fair price is. They can't tell an honest quote from a padded one, or a cheap fix from an unsafe one. The people hit hardest are the ones with the least room for error: students, first-time car owners, and families for whom a $1,000 surprise is a crisis.

We first planned a photo-based damage assessment tool. We realized that what people lack isn't another estimate. It's the experience to recognize a bad deal. So we built a way to practice that moment before it happens for real.

### What it does

RepairIQ Academy is a 3D driving game that runs in the browser on a laptop or phone.

1. **Drive.** Survive 15 seconds of Atlanta rush hour: traffic cars, construction cones, and potholes.
2. **Crash, and you're at the mechanic.** Decide what to inspect first, then whether to repair or replace, based on what the inspection finds.
3. **Pick a quote.** Three shops pitch you, shown only as Shop A, B, and C. Google Gemini writes each one live as that shop's own friendly sales pitch. The dealer slips in work your damage doesn't need. The budget shop promises speed and savings, but mentions shortcuts like skipping the alignment or offering no warranty. The fair shop names the parts, book labor, and a written warranty. After you pick, the game reveals which was which.
4. **Results.** A score out of 1,000, a grade, and three questions to ask before signing anything at a real shop.

### How we built it

- **3D game:** JavaScript and three.js, with keyboard, on-screen buttons, and swipe controls so it works on phones.
- **Server:** a small Flask server that serves the game and one API route for quotes. The Gemini API key stays on the server and never reaches the browser.
- **AI:** Google Gemini, called through its OpenAI-compatible endpoint. The prompt grounds the fair quote in a reference price range for the damage, requires dealer > fair > budget, and bans giveaway words like "overpriced" or "unsafe" so players have to read critically.
- **Guardrails in Python:** we parse the JSON reply, reject unbelievable prices, fill in missing tips, and check the price order. Shop titles, risk labels, and point values are fixed in code, never decided by the AI.
- **Reliability:** the server tries several Gemini models in order and moves on when one is busy or slow. It starts the request as soon as the mechanic challenge opens, so Gemini works while the player answers the first two questions. If every model fails, the game shows sample quotes clearly labeled "not AI-generated."
- **Testing:** 52 automated pytest tests with a fake AI client, plus full playthroughs in a headless browser at desktop and phone sizes.
- We started with a Streamlit prototype, then rebuilt the experience as a 3D game once we decided players should *feel* the crash before the shop.

### Challenges we ran into

- **Gemini overload.** During the night, some models were overloaded or timing out. We added an ordered model fallback with a time limit, and an honest offline mode so the demo never gets stuck.
- **The AI gave away the answer.** Early quotes called the budget option a "backyard cut-rate job." We rewrote the prompt so each quote reads like the shop's own sales pitch, with the red flags left for the player to find.
- **Honesty versus realism.** We wanted realistic prices without claiming to be a real estimator. We use clearly labeled illustrative ranges and say so in the game.

### Accomplishments that we're proud of

- A complete loop, from driving to the mechanic to the score, that works on a phone.
- Blind quotes that make players spot the padding and the shortcuts themselves.
- The game works with live AI, survives AI failures, and never presents sample data as AI output.

### What we learned

- Prompting an AI to sound convincing, not just correct, is what made the game educational.
- Keeping decisions that matter (scores, labels) in code and letting the AI write the words made the app reliable.
- Build the fallback first. It saved our demo more than once.

### What's next for RepairIQ Academy

- **Photo check:** upload a photo of real damage and have Gemini explain what it sees and what to ask the shop.
- More hazards and inspection scenarios, a Spanish version, and testing with real drivers to tune difficulty.

## Built with

`python` · `flask` · `javascript` · `three.js` · `html5` · `css3` · `google-gemini-api` · `openai-python-sdk` · `streamlit` · `pytest`

## Links

- GitHub: https://github.com/kerryarchive/road-to-the-shop
- Demo video: **[public YouTube/Drive link]**

## Track and side challenges

- **Main track:** Cox Social Good. Drivers with the least money and the least car knowledge are the easiest to overcharge. The game builds the one skill that protects them: recognizing a bad quote.
- **MLH Best Use of Gemini API:** Gemini writes three distinct shop personas per crash, grounded in a price range, as structured JSON that our code validates and scores.
- **Shock Tracker: Zero Data:** no accounts, logins, profiles, analytics, or cookies. The browser stores nothing, and the only data sent is the name of the obstacle you hit. To write the quotes, our server sends Google Gemini only a short description of the in-game damage, with no personal information, IP address, or identifier.

## Disclosure: what existed before Hacklanta

All project code was written during the hacking period (Oct 9–11, 2026). We used these existing tools: three.js r170 (MIT, bundled with its license), Flask, Streamlit, the openai Python SDK (as the client for Gemini's OpenAI-compatible endpoint), python-dotenv, pytest, and the Google Gemini API. We used AI coding assistants: Claude (Anthropic) for planning, code, and tests, and ChatGPT to critique our project brief. We looked at an existing open-source car-diagnostics app for ideas and used none of its code.

## Instructions for judges

No login or test credentials are needed. To run it: follow the README, then `python server.py` and open http://localhost:8000. Without an API key, the game works fully and the quote step uses sample quotes labeled "not AI-generated"; add a free `GEMINI_API_KEY` to `.env` to see live Gemini quotes. For the quickest path to the AI part, choose **Try Mechanic Challenge (sample scenario)** on the start screen.

## Team

**[Name 1, school, email]**
**[Name 2]**
**[Name 3]**
