# Pitch, demo video, and Q&A prep

Judging: **3 minutes pitch + 2 minutes Q&A**, 2 judges per table, 9:30–11:30 AM in the State Ballroom. Judges score: track fit, polish of the demo, presentation, and how clear and compelling the use case is.

## Before you walk up

- Laptop charged, game already running (`python server.py`), browser open on the start screen, sound off
- `.env` has a working `GEMINI_API_KEY`; do one test run in the line so Gemini is warm
- Phone with the game open on the same Wi-Fi, to hand to a judge (optional, but memorable)
- Backup: the demo video ready to play offline, in case the Wi-Fi fails

## 3-minute pitch

Roles: **Speaker** talks; **Driver** plays. Practice the hand-offs.

**0:00–0:25 · The problem** (Speaker)
> "Raise your hand if you've ever hit a pothole on the Downtown Connector. After that, most people walk into a repair shop with no idea what a fair price is. They can't tell an honest quote from a padded one, or a cheap fix from an unsafe one. The people who get hurt most are the ones with the least room for error: students, first-time owners, families living paycheck to paycheck."

**0:25–0:40 · The idea** (Speaker)
> "Nobody practices this moment before it happens. So we built RepairIQ Academy, a game that lets you crash safely and practice dealing with the shop."

**0:40–1:00 · Drive** (Driver plays; Speaker narrates)
> "You're driving Atlanta rush hour. Cones, potholes, traffic." *(Crash into something.)* "And now, like most of us, you're at the mechanic."

**1:00–1:30 · Inspect and decide** (Driver answers steps 1 and 2)
> "First: what should the mechanic check? Then: repair or replace? Each answer comes with a short explanation, so even a wrong answer teaches something."

**1:30–2:15 · The quotes: the heart of it** (Driver reads one pitch aloud)
> "Now three shops pitch you. Google Gemini writes these live, every time, as each shop's own sales pitch. No labels, no hints. One sounds premium but adds work your car doesn't need. One sounds like a great deal but quietly skips the alignment and the warranty. Your job is to spot it." *(Pick, show the reveal.)* "That's exactly the skill that protects you at a real counter."

**2:15–2:35 · Results** (Driver)
> "You get a score, and three questions to ask before signing anything at a real shop."

**2:35–3:00 · Why it matters + close** (Speaker)
> "It works on any phone, with no account and no data collected. Gemini creates fresh shops every time, and our code keeps the scoring honest and labels sample data as sample data. Next, we want drivers to upload a photo of their own damage. RepairIQ Academy: crash here, so you don't get crashed at the shop. Thank you."

## Likely questions (2 minutes)

**"How do you know the prices are right?"**
They're illustrative ranges for the game, and the game says so. Gemini is told the fair quote must land inside the range, the dealer above it, the budget below it, and our Python code checks the order. We're teaching people to spot patterns, not quoting real prices.

**"What does the AI actually do versus your code?"**
Gemini writes the prices, the three shop pitches, the mechanic greeting, and the tips. Our code controls everything that's scored: shop labels, point values, and validation. The inspection questions are written by our team.

**"What if Gemini is down?"**
The server tries several Gemini models in order. If all fail, the game uses sample quotes labeled "not AI-generated," so it never gets stuck and never pretends.

**"Couldn't the AI make the bad shop obvious?"**
It did at first. Early quotes called the budget shop "backyard." We rewrote the prompt to ban giveaway words and make each quote a sales pitch, so players have to read critically.

**"Who is this for, really?"**
Drivers with the least money and the least car knowledge, who are the easiest to overcharge. It's free, runs on a phone, and needs no account.

**"Did you build all this here?"**
Yes, all the code was written during Hacklanta. We used three.js for 3D, Flask, and the Gemini API, and we used AI coding assistants, which we disclosed on Devpost. Our Git history shows the build.

**"What's next?"**
Photo upload so drivers can check their own damage with Gemini, more scenarios, and a Spanish version.

## Demo video (2–3 minutes, upload as Public)

Record your screen with **Xbox Game Bar** (Windows: Win + Alt + R) or OBS, and talk over it. One take is fine.

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Start screen | The problem (first line of the pitch) |
| 0:20–0:45 | Drive and crash | "Drive Atlanta rush hour... and now you're at the shop." |
| 0:45–1:15 | Steps 1 and 2 | What to inspect, repair or replace, explanations |
| 1:15–2:00 | Step 3: read one pitch on screen, pick, reveal | Gemini writes three shop pitches live; spot the red flags |
| 2:00–2:20 | Results screen | Score and the three questions to ask |
| 2:20–2:45 | Quick shot of the code or README | Gemini + guardrails, honest fallback, no data collected, what's next |

Upload to YouTube or Google Drive and set it to **Public**, as the rules require. Paste the link into the README and Devpost, then open it in an incognito window to confirm it plays.
