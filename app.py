"""
Road to the Shop (RepairIQ)
===========================

A gamified Streamlit app in three stages:

1. The Commute   - drive an Atlanta road, hit hazards, take damage.
2. The Body Shop - an AI estimator gives three quotes (dealer, scrapyard, fair).
3. Scorecard     - pick a repair route and get graded on money vs. safety.

Run locally:  streamlit run app.py

AI provider (set ONE key in .env):
  GROQ_API_KEY    -> Groq Cloud, model llama-3.1-8b-instant (default)
  GEMINI_API_KEY  -> Google Gemini through its OpenAI-compatible endpoint
With no key, the shop offers a clearly labeled offline sample quote instead.
"""

from __future__ import annotations

import html
import json
import os
import re
from collections import Counter

import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Game constants
# ---------------------------------------------------------------------------

STARTING_HEALTH = 100
STARTING_WALLET = 1500

# ref_low / ref_high are ILLUSTRATIVE game ranges (parts + labor, USD) used to
# keep the AI grounded and to teach players what "fair" looks like. They are
# not real quotes; real costs vary by vehicle, shop, and region.
HAZARDS = {
    "pothole": {
        "name": "Deep Atlanta Pothole",
        "icon": "🕳️",
        "damage": 25,
        "event": "Blew the tire bead and bent the rim",
        "parts": "tire, alloy rim, wheel alignment check",
        "ref_low": 250,
        "ref_high": 700,
    },
    "cone": {
        "name": "Construction Zone Traffic Cone",
        "icon": "🚧",
        "damage": 15,
        "event": "Cracked the front lower bumper lip",
        "parts": "front lower bumper lip / valance, mounting clips",
        "ref_low": 150,
        "ref_high": 500,
    },
    "sideswipe": {
        "name": "Sideswiping a Tight Parked Car",
        "icon": "🚗",
        "damage": 35,
        "event": "Smashed the side mirror and scratched the door panel",
        "parts": "side mirror assembly, door panel refinish",
        "ref_low": 450,
        "ref_high": 1300,
    },
}

# Display order and fixed metadata for each repair route. Titles, risk labels,
# and roadworthiness are set by the game, not by the AI.
QUOTE_META = {
    "quote_dealer": {
        "route": "dealer",
        "title": "Dealership OEM Overhaul",
        "risk": "Overpriced / Predatory charges included",
        "roadworthiness": 100,
        "tone": "warn",
        "icon": "🏢",
    },
    "quote_budget": {
        "route": "budget",
        "title": "Scrapyard Patch",
        "risk": "Dangerous / Temporary fix",
        "roadworthiness": 45,
        "tone": "bad",
        "icon": "🪛",
    },
    "quote_fair": {
        "route": "fair",
        "title": "Certified Independent Repair",
        "risk": "Fair market parts & standard book labor",
        "roadworthiness": 95,
        "tone": "good",
        "icon": "✅",
    },
}

DEFAULT_TIPS = [
    "Can you give me an itemized breakdown of parts and labor hours, and which labor guide you used?",
    "Are these OEM, aftermarket, or used parts, and can I see the part numbers and the warranty?",
    "Which repairs are required for safety today, and which are optional add-ons I can decline?",
]

MAX_REASONABLE_COST = 50_000


class QuoteError(Exception):
    """A problem getting or reading quotes, with a message safe to show players."""


class MissingKeyError(QuoteError):
    """No AI API key is configured."""


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def default_state() -> dict:
    return {
        "stage": "commute",          # commute -> shop -> scorecard
        "health": STARTING_HEALTH,
        "wallet": STARTING_WALLET,
        "damage_log": [],            # list of {"key", "name", "icon", "damage", "event"}
        "quotes": None,              # validated quote payload once fetched
        "quote_error": None,         # user-facing error message
        "quote_attempted": False,
        "choice": None,              # key in QUOTE_META once chosen
        "cost_paid": 0,
    }


def init_state() -> None:
    for key, value in default_state().items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game() -> None:
    for key, value in default_state().items():
        st.session_state[key] = value


def clear_quotes() -> None:
    st.session_state.quotes = None
    st.session_state.quote_error = None
    st.session_state.quote_attempted = False


# ---------------------------------------------------------------------------
# Pure game logic (no Streamlit calls; easy to unit test)
# ---------------------------------------------------------------------------

def apply_hazard(health: int, log: list, key: str) -> tuple[int, list]:
    """Return the new health and damage log after hitting a hazard."""
    hazard = HAZARDS[key]
    if health <= 0:
        return health, log
    new_log = log + [{
        "key": key,
        "name": hazard["name"],
        "icon": hazard["icon"],
        "damage": hazard["damage"],
        "event": hazard["event"],
    }]
    return max(0, health - hazard["damage"]), new_log


def summarize_damage(log: list) -> list[dict]:
    """Group the log by hazard: [{"key", "hazard", "count"}] in first-hit order."""
    counts = Counter(entry["key"] for entry in log)
    seen, summary = set(), []
    for entry in log:
        key = entry["key"]
        if key not in seen:
            seen.add(key)
            summary.append({"key": key, "hazard": HAZARDS[key], "count": counts[key]})
    return summary


def reference_range(log: list) -> tuple[int, int]:
    """Illustrative fair-price range for everything in the log."""
    low = sum(HAZARDS[e["key"]]["ref_low"] for e in log)
    high = sum(HAZARDS[e["key"]]["ref_high"] for e in log)
    return low, high


def round_to(value: float, step: int = 10) -> int:
    return int(round(value / step) * step)


def compute_score(wallet: int, roadworthiness: int) -> dict:
    """Grade the decision on Financial Health and Road Safety, 50/50."""
    financial = max(0, min(100, round(wallet / STARTING_WALLET * 100)))
    safety = max(0, min(100, roadworthiness))
    overall = round(0.5 * financial + 0.5 * safety)
    if overall >= 85:
        grade = "A"
    elif overall >= 70:
        grade = "B"
    elif overall >= 55:
        grade = "C"
    elif overall >= 40:
        grade = "D"
    else:
        grade = "F"
    return {"financial": financial, "safety": safety, "overall": overall, "grade": grade}


# ---------------------------------------------------------------------------
# AI estimator
# ---------------------------------------------------------------------------

# Gemini models to try in order. If one is overloaded, rate-limited, or slow,
# fetch_ai_quotes moves on to the next. Override with a comma-separated
# GEMINI_MODEL in .env.
DEFAULT_GEMINI_MODELS = "gemini-3.5-flash, gemini-3.1-flash-lite, gemini-3.8-flash"


def _model_list(value: str) -> list[str]:
    return [m.strip() for m in value.split(",") if m.strip()]


def resolve_provider() -> dict | None:
    """Pick the AI provider from environment variables, or None if no key."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    preferred = os.getenv("AI_PROVIDER", "").strip().lower()

    groq_models = _model_list(os.getenv("GROQ_MODEL", "") or "llama-3.1-8b-instant")
    groq = {
        "name": "Groq",
        "env_var": "GROQ_API_KEY",
        "api_key": groq_key,
        "base_url": "https://api.groq.com/openai/v1",
        "model": groq_models[0],
        "models": groq_models,
    } if groq_key else None

    gemini_models = _model_list(os.getenv("GEMINI_MODEL", "") or DEFAULT_GEMINI_MODELS)
    gemini = {
        "name": "Gemini",
        "env_var": "GEMINI_API_KEY",
        "api_key": gemini_key,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": gemini_models[0],
        "models": gemini_models,
    } if gemini_key else None

    if preferred == "gemini" and gemini:
        return gemini
    if preferred == "groq" and groq:
        return groq
    return groq or gemini


SYSTEM_PROMPT = """You are a blunt, experienced auto body-shop estimator in Atlanta, Georgia.
A driver has pulled in with damage. Write three competing repair quotes for a typical mid-size sedan.

Return ONLY a JSON object with exactly these keys:
{
  "mechanic_greeting": "Exactly 2 sentences: a gritty, realistic assessment of the car.",
  "quote_dealer": {"title": "Dealership OEM Overhaul", "cost": 0, "description": "...", "risk": "Overpriced / Predatory charges included"},
  "quote_budget": {"title": "Scrapyard Patch", "cost": 0, "description": "...", "risk": "Dangerous / Temporary fix"},
  "quote_fair": {"title": "Certified Independent Repair", "cost": 0, "description": "...", "risk": "Fair market parts & standard book labor"},
  "negotiation_tips": ["question 1", "question 2", "question 3"]
}

Rules:
- "cost" is a whole number of US dollars covering parts AND labor for ALL listed damage.
- quote_fair must land inside the combined reference range you are given.
- quote_dealer must be clearly higher than quote_fair. quote_budget must be clearly lower than quote_fair.
- Each "description" is that shop's OWN sales pitch to the driver: 2-3 sentences, first person ("we"), confident and friendly. The driver should have to spot the red flags themselves, so never call a shop bad. Do not use words like padded, unnecessary, inflated, upsell, overpriced, predatory, scam, cut-rate, backyard, junk, shoddy, cheap, dangerous, unsafe, or risky.
- quote_dealer's pitch sounds premium and thorough, but slips in 1-2 specific add-ons or extra labor the listed damage does not need (for example, replacing undamaged parts or repainting extra panels), presented as "while we're in there" or "for peace of mind".
- quote_budget's pitch sounds like a great deal and promises speed, but mentions 1-2 specific shortcuts as savings (for example, used or unbranded parts, skipping the alignment check, touch-up paint with no clear coat, or no warranty).
- quote_fair's pitch names the specific parts, standard book labor, a written warranty, and repairs only what was damaged.
- negotiation_tips: exactly 3 specific questions the driver should ask the shop to avoid being scammed.
- No markdown and no text outside the JSON object."""


def build_user_prompt(log: list) -> str:
    lines = []
    for item in summarize_damage(log):
        h, n = item["hazard"], item["count"]
        lines.append(
            f"- {h['name']} (hit {n}x): {h['event']}. Affected parts: {h['parts']}. "
            f"Reference fair range: ${h['ref_low'] * n}-${h['ref_high'] * n}."
        )
    low, high = reference_range(log)
    return (
        "Damage report:\n" + "\n".join(lines)
        + f"\nCombined reference fair range: ${low}-${high}.\n"
        + "Write the three quotes now."
    )


def extract_json(text: str) -> dict:
    """Parse a JSON object from a model reply, tolerating code fences or stray text."""
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    raise QuoteError("The estimator's reply wasn't valid JSON.")


def _to_cost(value) -> int:
    if isinstance(value, bool):
        raise QuoteError("A quote cost wasn't a number.")
    if isinstance(value, (int, float)):
        cost = int(round(value))
    elif isinstance(value, str):
        digits = re.sub(r"[^\d.]", "", value)
        try:
            cost = int(round(float(digits)))
        except ValueError as exc:
            raise QuoteError("A quote cost wasn't a number.") from exc
    else:
        raise QuoteError("A quote cost wasn't a number.")
    if cost <= 0 or cost > MAX_REASONABLE_COST:
        raise QuoteError(f"A quote cost (${cost:,}) was outside a believable range.")
    return cost


def validate_payload(data) -> dict:
    """Check the model's JSON and normalize it into the game's quote format."""
    if not isinstance(data, dict):
        raise QuoteError("The estimator's reply wasn't a JSON object.")

    greeting = str(data.get("mechanic_greeting") or "").strip()
    if not greeting:
        greeting = "Took a look under the lights. Let's talk about your options."

    quotes = {}
    for key, meta in QUOTE_META.items():
        raw = data.get(key)
        if not isinstance(raw, dict):
            raise QuoteError(f"The estimator left out the {meta['title']} quote.")
        description = str(raw.get("description") or "").strip()
        if not description:
            raise QuoteError(f"The {meta['title']} quote had no description.")
        quotes[key] = {
            "title": meta["title"],
            "risk": meta["risk"],
            "cost": _to_cost(raw.get("cost")),
            "description": description,
        }

    raw_tips = data.get("negotiation_tips")
    tips = [str(t).strip() for t in raw_tips if str(t).strip()] if isinstance(raw_tips, list) else []
    tips = (tips + [t for t in DEFAULT_TIPS if t not in tips])[:3]

    warnings = []
    dealer = quotes["quote_dealer"]["cost"]
    budget = quotes["quote_budget"]["cost"]
    fair = quotes["quote_fair"]["cost"]
    if not budget < fair < dealer:
        warnings.append(
            "The AI's prices aren't in the usual order (scrapyard < fair < dealer). "
            "Judge each one against the reference range below."
        )

    return {"greeting": greeting, "quotes": quotes, "tips": tips, "warnings": warnings}


def _api_error(name: str):
    """Look up an openai exception class by name, tolerating SDK changes."""
    return getattr(openai, name, None) or Exception


def fetch_ai_quotes(log: list, client_factory=None) -> dict:
    """Ask the configured LLM for quotes. Raises QuoteError with a friendly message."""
    provider = resolve_provider()
    if provider is None:
        raise MissingKeyError("No AI API key found.")

    factory = client_factory or openai.OpenAI
    client = factory(
        api_key=provider["api_key"],
        base_url=provider["base_url"],
        timeout=20.0,
        max_retries=0,  # instead of retrying a busy model, we move on to the next one
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(log)},
    ]

    auth_error = _api_error("AuthenticationError")
    rate_error = _api_error("RateLimitError")
    conn_error = _api_error("APIConnectionError")  # includes timeouts
    bad_request = _api_error("BadRequestError")
    status_error = _api_error("APIStatusError")

    unavailable: QuoteError | None = None
    for model in provider.get("models") or [provider["model"]]:
        last_error: QuoteError | None = None
        # Attempt 1 uses JSON mode; attempt 2 retries without it in case the
        # provider or model rejects response_format, or the reply was malformed.
        for use_json_mode in (True, False):
            kwargs = {"model": model, "messages": messages, "temperature": 0.7}
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                response = client.chat.completions.create(**kwargs)
            except auth_error as exc:
                raise QuoteError(
                    f"{provider['name']} rejected the API key. Check {provider['env_var']} in your .env file."
                ) from exc
            except rate_error:
                unavailable = QuoteError(f"{provider['name']} rate limit reached. Wait a minute and retry.")
                break
            except conn_error:
                unavailable = QuoteError(
                    f"Couldn't reach {provider['name']} or it was too slow. Check your internet connection."
                )
                break
            except bad_request as exc:
                detail = getattr(exc, "message", "") or str(exc)
                last_error = QuoteError(f"{provider['name']} rejected the request: {detail[:200]}")
                continue
            except status_error as exc:
                code = getattr(exc, "status_code", "unknown")
                if code == 404 or (isinstance(code, int) and code >= 500):
                    # Model retired or overloaded: try the next model.
                    unavailable = QuoteError(f"{provider['name']} is busy (status {code}). Try again.")
                    break
                raise QuoteError(f"{provider['name']} returned an error (status {code}). Try again.") from exc

            choices = getattr(response, "choices", None) or []
            content = choices[0].message.content if choices else ""
            try:
                result = validate_payload(extract_json(content))
            except QuoteError as exc:
                last_error = exc
                continue
            result["is_ai"] = True
            result["source"] = f"AI estimate · {provider['name']} ({model})"
            return result
        else:
            # Both attempts reached the model but its replies were unusable.
            raise last_error or QuoteError("The estimator didn't return usable quotes.")

    raise unavailable or QuoteError("The estimator didn't return usable quotes.")


def build_offline_quotes(log: list) -> dict:
    """Deterministic sample quotes from the reference table. Clearly labeled, not AI."""
    low, high = reference_range(log)
    fair = round_to((low + high) / 2)
    damage_list = ", ".join(
        f"{item['hazard']['event'].lower()}" + (f" (x{item['count']})" if item["count"] > 1 else "")
        for item in summarize_damage(log)
    )
    return {
        "is_ai": False,
        "source": "Offline sample quote · not AI-generated (built from the game's reference table)",
        "greeting": (
            "Offline mode: no AI estimator is connected, so these are sample quotes. "
            f"Here's what we're looking at: {damage_list}."
        ),
        "quotes": {
            "quote_dealer": {
                "title": QUOTE_META["quote_dealer"]["title"],
                "risk": QUOTE_META["quote_dealer"]["risk"],
                "cost": round_to(fair * 1.85),
                "description": (
                    "New OEM parts at full list price, a full four-wheel alignment you may not need, "
                    "a 'protective coating' package, and labor billed well above book hours."
                ),
            },
            "quote_budget": {
                "title": QUOTE_META["quote_budget"]["title"],
                "risk": QUOTE_META["quote_budget"]["risk"],
                "cost": round_to(fair * 0.4),
                "description": (
                    "Used junkyard parts, zip ties and filler instead of proper mounts, "
                    "and no alignment or safety check. It may hold for a while, but it may not."
                ),
            },
            "quote_fair": {
                "title": QUOTE_META["quote_fair"]["title"],
                "risk": QUOTE_META["quote_fair"]["risk"],
                "cost": fair,
                "description": (
                    "Quality aftermarket or OEM-equivalent parts, standard book labor hours, "
                    "and a written warranty on the work."
                ),
            },
        },
        "tips": list(DEFAULT_TIPS),
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1180px;}
.rts-hero {border-radius: 16px; padding: 18px 24px; margin-bottom: 1rem;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #7c2d12 140%); color: #f8fafc;}
.rts-hero h1 {margin: 0; font-size: 1.9rem; color: #f8fafc; letter-spacing: -0.02em;}
.rts-hero p {margin: .3rem 0 0; color: #cbd5e1;}
.rts-stage {display: inline-block; margin-top: .6rem; padding: 2px 10px; border-radius: 999px;
  background: rgba(250, 204, 21, .18); color: #fde68a; font-size: .8rem; font-weight: 700;}
.rts-road {position: relative; height: 96px; border-radius: 14px; overflow: hidden; margin: .4rem 0 1rem;
  background: #334155; border-top: 6px solid #94a3b8; border-bottom: 6px solid #94a3b8;}
.rts-road .lane {position: absolute; top: 42px; left: 0; right: 0; height: 4px;
  background: repeating-linear-gradient(90deg, #facc15 0 36px, transparent 36px 72px);}
.rts-road .car {position: absolute; top: 20px; font-size: 42px; transform: scaleX(-1);}
.rts-road .shop {position: absolute; right: 14px; top: 22px; font-size: 38px;}
.rts-road .miles {position: absolute; left: 12px; bottom: 4px; font-size: .75rem; color: #cbd5e1;}
.rts-badge {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem;
  font-weight: 700; margin-left: 6px; white-space: nowrap;}
.rts-badge.minor {background: rgba(234, 179, 8, .18); color: #a16207;}
.rts-badge.moderate {background: rgba(234, 88, 12, .18); color: #c2410c;}
.rts-badge.severe {background: rgba(220, 38, 38, .18); color: #b91c1c;}
.rts-log {padding: 8px 12px; border-radius: 10px; margin-bottom: 6px;
  background: rgba(128, 128, 128, .08); border: 1px solid rgba(128, 128, 128, .18);}
.rts-log small {opacity: .75;}
.rts-card {border: 1px solid rgba(128, 128, 128, .3); border-radius: 14px; padding: 18px;
  min-height: 330px; background: rgba(128, 128, 128, .05); margin-bottom: .6rem;}
.rts-card.good {border: 2px solid rgba(22, 163, 74, .65);}
.rts-card.warn {border: 2px solid rgba(234, 88, 12, .55);}
.rts-card.bad {border: 2px solid rgba(220, 38, 38, .55);}
.rts-card h3 {margin: 0 0 .2rem; font-size: 1.1rem;}
.rts-cost {font-size: 2.1rem; font-weight: 800; margin: .2rem 0 .4rem; letter-spacing: -0.02em;}
.rts-risk {display: inline-block; font-weight: 700; font-size: .8rem; padding: 4px 10px; border-radius: 8px;}
.rts-risk.good {background: rgba(22, 163, 74, .15); color: #15803d;}
.rts-risk.warn {background: rgba(234, 88, 12, .15); color: #c2410c;}
.rts-risk.bad {background: rgba(220, 38, 38, .15); color: #b91c1c;}
.rts-meta {font-size: .85rem; opacity: .8; margin-top: .6rem;}
.rts-over {color: #dc2626; font-weight: 700;}
.rts-grade {font-size: 4.5rem; font-weight: 900; line-height: 1; text-align: center;}
.rts-grade-label {text-align: center; opacity: .75; font-size: .9rem;}
</style>
"""


def esc(text) -> str:
    """Escape any text (including AI output) before putting it inside HTML."""
    return html.escape(str(text))


def severity_badge(damage: int) -> str:
    if damage >= 30:
        return '<span class="rts-badge severe">SEVERE</span>'
    if damage >= 20:
        return '<span class="rts-badge moderate">MODERATE</span>'
    return '<span class="rts-badge minor">MINOR</span>'


def render_header(stage_label: str) -> None:
    st.markdown(
        f"""<div class="rts-hero">
        <h1>🛣️ Road to the Shop</h1>
        <p>Survive an Atlanta commute, then survive the repair shop. Learn what repairs really cost.</p>
        <span class="rts-stage">{esc(stage_label)}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.header("How to play")
        st.markdown(
            "1. **Drive.** Hit road hazards and watch your Car Health drop.\n"
            "2. **Pull into the shop.** An AI estimator gives you three quotes.\n"
            "3. **Choose wisely.** You're graded on money left *and* road safety."
        )
        st.divider()
        provider = resolve_provider()
        if provider:
            st.success(f"AI estimator: {provider['name']} · `{provider['model']}`")
        else:
            st.warning(
                "No AI key found. Add `GROQ_API_KEY` or `GEMINI_API_KEY` to a `.env` file "
                "and restart. You can still play with offline sample quotes."
            )
        st.divider()
        if st.button("🔄 Restart game", width="stretch"):
            reset_game()
            st.rerun()
        st.caption(
            "Educational game. Prices are illustrative; real repair costs vary by vehicle, "
            "shop, and region. This is not a substitute for a professional inspection."
        )


# ---------------------------------------------------------------------------
# Stage 1: The Commute
# ---------------------------------------------------------------------------

def on_hazard(key: str) -> None:
    health, log = apply_hazard(st.session_state.health, st.session_state.damage_log, key)
    st.session_state.health = health
    st.session_state.damage_log = log
    clear_quotes()


def go_to_shop() -> None:
    clear_quotes()
    st.session_state.stage = "shop"


def render_commute() -> None:
    render_header("Stage 1 · The Commute")
    health = st.session_state.health
    log = st.session_state.damage_log
    totaled = health <= 0

    road_col, dash_col = st.columns([3, 2], gap="large")

    with road_col:
        st.subheader("Downtown Connector, rush hour")
        car_left = min(78, 4 + len(log) * 12)
        st.markdown(
            f"""<div class="rts-road">
            <div class="lane"></div>
            <div class="car" style="left:{car_left}%">🚙</div>
            <div class="shop">🔧</div>
            <div class="miles">Hazards hit: {len(log)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if totaled:
            st.error("Your car is undriveable. Call a tow and head to the shop.")
        else:
            st.write("Traffic is brutal. Something's coming up. **What do you hit?**")

        cols = st.columns(3)
        for col, (key, hazard) in zip(cols, HAZARDS.items()):
            with col:
                st.button(
                    f"{hazard['icon']} {hazard['name']}",
                    key=f"hazard_{key}",
                    on_click=on_hazard,
                    args=(key,),
                    disabled=totaled,
                    width="stretch",
                )
                st.caption(f"−{hazard['damage']} health · {hazard['event']}")

    with dash_col:
        st.subheader("Dashboard")
        m1, m2 = st.columns(2)
        m1.metric("Car Health", f"{health}%", delta=f"{health - STARTING_HEALTH}%" if log else None)
        m2.metric("Wallet", f"${st.session_state.wallet:,}")
        st.progress(health / 100)

        st.markdown("**Damage log**")
        if not log:
            st.caption("No damage yet. Enjoy it while it lasts.")
        for i, entry in enumerate(log, start=1):
            st.markdown(
                f"""<div class="rts-log">{esc(entry['icon'])} <b>{esc(entry['name'])}</b>
                {severity_badge(entry['damage'])}<br>
                <small>#{i} · {esc(entry['event'])} · −{entry['damage']} health</small></div>""",
                unsafe_allow_html=True,
            )

        st.button(
            "🔧 Pull into Repair Shop",
            type="primary",
            on_click=go_to_shop,
            disabled=not log,
            width="stretch",
        )
        if not log:
            st.caption("Take some damage first; the shop only opens for broken cars.")


# ---------------------------------------------------------------------------
# Stage 2 + 3: The Body Shop and the decision
# ---------------------------------------------------------------------------

def load_ai_quotes() -> None:
    st.session_state.quote_attempted = True
    try:
        st.session_state.quotes = fetch_ai_quotes(st.session_state.damage_log)
        st.session_state.quote_error = None
    except MissingKeyError:
        st.session_state.quote_error = "missing_key"
    except QuoteError as exc:
        st.session_state.quote_error = str(exc)
    except Exception as exc:  # last-resort guard so the demo never crashes
        st.session_state.quote_error = f"Unexpected error talking to the AI: {type(exc).__name__}."


def use_offline_quotes() -> None:
    st.session_state.quotes = build_offline_quotes(st.session_state.damage_log)
    st.session_state.quote_error = None
    st.session_state.quote_attempted = True


def retry_quotes() -> None:
    clear_quotes()


def back_to_road() -> None:
    clear_quotes()
    st.session_state.stage = "commute"


def choose_route(key: str) -> None:
    if st.session_state.choice is not None or st.session_state.quotes is None:
        return
    quote = st.session_state.quotes["quotes"][key]
    st.session_state.choice = key
    st.session_state.cost_paid = quote["cost"]
    st.session_state.wallet -= quote["cost"]
    st.session_state.health = QUOTE_META[key]["roadworthiness"]
    st.session_state.stage = "scorecard"


def render_quote_card(key: str, quote: dict, wallet: int) -> None:
    meta = QUOTE_META[key]
    over = quote["cost"] > wallet
    after = wallet - quote["cost"]
    over_html = '<div class="rts-over">⚠️ Over your budget, this puts you in debt</div>' if over else ""
    st.markdown(
        f"""<div class="rts-card {meta['tone']}">
        <h3>{meta['icon']} {esc(quote['title'])}</h3>
        <div class="rts-cost">${quote['cost']:,}</div>
        <span class="rts-risk {meta['tone']}">{esc(quote['risk'])}</span>
        <p style="margin-top:.8rem">{esc(quote['description'])}</p>
        <div class="rts-meta">Roadworthiness after repair: <b>{meta['roadworthiness']}%</b><br>
        Wallet after: <b>${after:,}</b></div>
        {over_html}
        </div>""",
        unsafe_allow_html=True,
    )
    st.button(
        f"Choose {meta['route'].capitalize()} route",
        key=f"choose_{key}",
        on_click=choose_route,
        args=(key,),
        type="primary" if meta["route"] == "fair" else "secondary",
        width="stretch",
    )


def render_shop() -> None:
    render_header("Stage 2 · The AI Body Shop")
    log = st.session_state.damage_log

    if st.session_state.quotes is None and not st.session_state.quote_attempted:
        with st.spinner("The estimator is crawling under your car..."):
            load_ai_quotes()

    payload = st.session_state.quotes
    if payload is None:
        error = st.session_state.quote_error
        if error == "missing_key":
            st.warning(
                "**No AI estimator connected.** Add `GROQ_API_KEY` (or `GEMINI_API_KEY`) to a `.env` "
                "file next to `app.py`, then restart `streamlit run app.py`. "
                "Or keep playing with an offline sample quote."
            )
        else:
            st.error(f"**The estimator couldn't produce quotes.** {error}")
        c1, c2, c3 = st.columns(3)
        c1.button("🔁 Retry AI estimate", on_click=retry_quotes, width="stretch",
                  disabled=error == "missing_key")
        c2.button("📋 Use offline sample quote", on_click=use_offline_quotes, type="primary",
                  width="stretch")
        c3.button("⬅️ Back to the road", on_click=back_to_road, width="stretch")
        return

    with st.chat_message("assistant", avatar="🧰"):
        st.markdown(f"**Estimator:** {payload['greeting']}")
    st.caption(payload["source"])
    for warning in payload.get("warnings", []):
        st.warning(warning)

    low, high = reference_range(log)
    st.info(
        f"**Reference fair range for your damage: ${low:,} – ${high:,}** "
        "(illustrative game data, not a real quote). Use it to judge each offer.",
        icon="📏",
    )

    wallet = st.session_state.wallet
    st.subheader(f"Pick your repair · Wallet: ${wallet:,}")
    cols = st.columns(3, gap="medium")
    for col, key in zip(cols, QUOTE_META):
        with col:
            render_quote_card(key, payload["quotes"][key], wallet)

    st.subheader("🛡️ Ask these before you sign anything")
    for i, tip in enumerate(payload["tips"], start=1):
        st.markdown(f"{i}. {tip}")

    st.button("⬅️ Leave the shop and keep driving", on_click=back_to_road)


# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------

def verdict(choice: str, quotes: dict) -> tuple[str, str]:
    """Return (streamlit status kind, message) for the chosen route."""
    fair = quotes["quote_fair"]["cost"]
    dealer = quotes["quote_dealer"]["cost"]
    budget = quotes["quote_budget"]["cost"]
    if choice == "quote_fair":
        saved = max(0, dealer - fair)
        return "success", (
            f"**Smart negotiator.** You got a safe, warrantied repair and skipped "
            f"**${saved:,}** of dealer padding."
        )
    if choice == "quote_dealer":
        extra = max(0, dealer - fair)
        return "warning", (
            f"**Safe, but you got upsold.** You paid **${extra:,}** more than a fair independent "
            "shop would have charged. Always ask for an itemized estimate."
        )
    saved = max(0, fair - budget)
    return "error", (
        f"**Cheap now, risky later.** You saved **${saved:,}**, but your car is only 45% "
        "roadworthy. A bent rim or loose mirror can fail at highway speed."
    )


def render_scorecard() -> None:
    render_header("Stage 3 · Scorecard")
    choice = st.session_state.choice
    payload = st.session_state.quotes
    if choice is None or payload is None:
        st.info("No decision recorded yet.")
        st.button("Back to the road", on_click=back_to_road)
        return

    quote = payload["quotes"][choice]
    wallet = st.session_state.wallet
    score = compute_score(wallet, QUOTE_META[choice]["roadworthiness"])

    grade_col, stats_col = st.columns([1, 3], gap="large")
    with grade_col:
        st.markdown(f'<div class="rts-grade">{score["grade"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rts-grade-label">Overall {score["overall"]}/100</div>',
                    unsafe_allow_html=True)
    with stats_col:
        st.markdown(f"You chose **{esc(quote['title'])}** for **${quote['cost']:,}**.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Wallet left", f"${wallet:,}", delta=f"-${st.session_state.cost_paid:,}")
        m2.metric("Financial Health", f"{score['financial']}%")
        m3.metric("Road Safety", f"{score['safety']}%")
        st.markdown("**Financial Health**")
        st.progress(score["financial"] / 100)
        st.markdown("**Road Safety**")
        st.progress(score["safety"] / 100)

    kind, message = verdict(choice, payload["quotes"])
    getattr(st, kind)(message)
    if wallet < 0:
        st.error(f"You're **${-wallet:,} in debt**. In real life that often means a high-interest repair loan.")

    with st.expander("What you should take to a real shop"):
        for i, tip in enumerate(payload["tips"], start=1):
            st.markdown(f"{i}. {tip}")
        low, high = reference_range(st.session_state.damage_log)
        st.markdown(f"Reference fair range for this damage in the game: **${low:,} – ${high:,}**.")

    st.button("🔄 Play Again", type="primary", on_click=reset_game, width="stretch")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Road to the Shop · RepairIQ", page_icon="🛣️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    render_sidebar()

    stage = st.session_state.stage
    if stage == "shop":
        render_shop()
    elif stage == "scorecard":
        render_scorecard()
    else:
        render_commute()


if __name__ == "__main__":
    main()
