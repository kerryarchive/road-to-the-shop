"""
RepairIQ Academy server
=======================

Serves the 3D driving game in web/ and gives it one API route for repair
quotes. The quotes come from the same Gemini/Groq code the Streamlit app uses
(app.py), so the API key stays on the server and never reaches the browser.

Run locally:  python server.py   ->  http://localhost:8000
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

import app as game

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
MAX_HAZARDS = 5

server = Flask(__name__, static_folder=WEB_DIR, static_url_path="")


@server.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@server.post("/api/quotes")
def quotes():
    """Three repair quotes for the damage the player took.

    Body: {"hazards": ["pothole", ...]} using keys from game.HAZARDS.
    Always answers with quotes: live AI when it works, otherwise the
    offline sample (is_ai = false, with a "notice" saying why).
    """
    data = request.get_json(silent=True) or {}
    keys = data.get("hazards")
    if (
        not isinstance(keys, list)
        or not 1 <= len(keys) <= MAX_HAZARDS
        or any(not isinstance(k, str) or k not in game.HAZARDS for k in keys)
    ):
        return jsonify(error=f"'hazards' must be a list of 1-{MAX_HAZARDS} known hazard keys."), 400

    health, log = game.STARTING_HEALTH, []
    for key in keys:
        health, log = game.apply_hazard(health, log, key)

    try:
        result = game.fetch_ai_quotes(log)
    except game.QuoteError as exc:
        result = game.build_offline_quotes(log)
        result["notice"] = str(exc)
    except Exception as exc:  # never leave the player stuck in the shop
        result = game.build_offline_quotes(log)
        result["notice"] = f"Unexpected error talking to the AI: {type(exc).__name__}."

    result["reference_range"] = list(game.reference_range(log))
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    # 0.0.0.0 lets a phone on the same Wi-Fi open the game for testing.
    print(f"\n  RepairIQ Academy: http://localhost:{port}\n")
    server.run(host="0.0.0.0", port=port, debug=False)
