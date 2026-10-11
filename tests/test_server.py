"""
Tests for server.py, the API behind the 3D game.

Run:  pytest

fetch_ai_quotes is replaced with fakes, so nothing here calls a real AI.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as game  # noqa: E402
import server  # noqa: E402


@pytest.fixture
def client():
    server.server.config["TESTING"] = True
    return server.server.test_client()


def fake_ai_result(log):
    result = game.validate_payload({
        "mechanic_greeting": "Rough ride.",
        "quote_dealer": {"cost": 900, "description": "Padded."},
        "quote_budget": {"cost": 150, "description": "Cheap."},
        "quote_fair": {"cost": 450, "description": "Fair."},
        "negotiation_tips": ["Q1?", "Q2?", "Q3?"],
    })
    result["is_ai"] = True
    result["source"] = "AI estimate · Fake"
    return result


def test_home_page_serves_the_game(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"game.js" in res.data


def test_game_files_are_served(client):
    assert client.get("/game.js").status_code == 200
    assert client.get("/vendor/three.module.min.js").status_code == 200


def test_quotes_with_ai(client, monkeypatch):
    monkeypatch.setattr(game, "fetch_ai_quotes", fake_ai_result)
    res = client.post("/api/quotes", json={"hazards": ["pothole"]})
    data = res.get_json()
    assert res.status_code == 200
    assert data["is_ai"] is True
    assert data["quotes"]["quote_fair"]["cost"] == 450
    assert data["reference_range"] == [250, 700]
    assert "notice" not in data


def test_quotes_fall_back_when_ai_fails(client, monkeypatch):
    def broken(log):
        raise game.QuoteError("Gemini rate limit reached.")

    monkeypatch.setattr(game, "fetch_ai_quotes", broken)
    data = client.post("/api/quotes", json={"hazards": ["cone"]}).get_json()
    assert data["is_ai"] is False
    assert "not AI-generated" in data["source"]
    assert data["notice"] == "Gemini rate limit reached."


def test_quotes_fall_back_on_unexpected_error(client, monkeypatch):
    def crashes(log):
        raise RuntimeError("boom")

    monkeypatch.setattr(game, "fetch_ai_quotes", crashes)
    data = client.post("/api/quotes", json={"hazards": ["sideswipe"]}).get_json()
    assert data["is_ai"] is False
    assert "RuntimeError" in data["notice"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"hazards": []},
        {"hazards": "pothole"},
        {"hazards": ["meteor"]},
        {"hazards": [1]},
        {"hazards": ["pothole"] * 6},
    ],
)
def test_quotes_reject_bad_requests(client, monkeypatch, body):
    monkeypatch.setattr(game, "fetch_ai_quotes", fake_ai_result)
    assert client.post("/api/quotes", json=body).status_code == 400


def test_every_game_obstacle_is_a_known_hazard():
    """The obstacles in web/game.js must match HAZARDS in app.py."""
    with open(os.path.join(server.WEB_DIR, "game.js"), encoding="utf-8") as f:
        js = f.read()
    for key in game.HAZARDS:
        assert f'hazard: "{key}"' in js
        assert f"  {key}: {{" in js  # a SCENARIOS entry for the mechanic challenge
