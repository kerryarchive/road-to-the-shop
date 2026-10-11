"""
Tests for the game logic and AI parsing in app.py.

Run:  pytest

No test here calls a real AI service. fetch_ai_quotes() gets a fake client
through its client_factory argument, so the tests are free, fast, and work
without an API key or internet.
"""

import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def good_payload(dealer=2000, budget=300, fair=900):
    return {
        "mechanic_greeting": "Rough ride. Let's fix it.",
        "quote_dealer": {"title": "x", "cost": dealer, "description": "Padded.", "risk": "x"},
        "quote_budget": {"title": "x", "cost": budget, "description": "Cheap.", "risk": "x"},
        "quote_fair": {"title": "x", "cost": fair, "description": "Fair.", "risk": "x"},
        "negotiation_tips": ["Q1?", "Q2?", "Q3?"],
    }


def fake_response(text):
    message = SimpleNamespace(content=text)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    """Stands in for openai.OpenAI. Each create() call returns or raises the next item."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return fake_response(reply)


def factory_for(client):
    return lambda **kwargs: client


@pytest.fixture
def gemini_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")


@pytest.fixture
def one_pothole():
    _, log = app.apply_hazard(100, [], "pothole")
    return log


# ---------------------------------------------------------------------------
# Game logic
# ---------------------------------------------------------------------------

def test_apply_hazard_lowers_health_and_logs_it():
    health, log = app.apply_hazard(100, [], "pothole")
    assert health == 75
    assert len(log) == 1
    assert log[0]["key"] == "pothole"


def test_apply_hazard_does_not_change_the_original_log():
    log = []
    app.apply_hazard(100, log, "cone")
    assert log == []


def test_health_never_goes_below_zero():
    health, log = 100, []
    for _ in range(5):
        health, log = app.apply_hazard(health, log, "sideswipe")
    assert health == 0
    assert len(log) == 3  # the 4th hit takes health to 0; no hits are logged after that


def test_reference_range_adds_up_every_hit():
    _, log = app.apply_hazard(100, [], "pothole")
    _, log = app.apply_hazard(75, log, "pothole")
    assert app.reference_range(log) == (500, 1400)


def test_summarize_damage_groups_repeat_hits():
    health, log = app.apply_hazard(100, [], "cone")
    health, log = app.apply_hazard(health, log, "pothole")
    health, log = app.apply_hazard(health, log, "cone")
    summary = app.summarize_damage(log)
    assert [(s["key"], s["count"]) for s in summary] == [("cone", 2), ("pothole", 1)]


@pytest.mark.parametrize(
    "wallet, roadworthiness, grade",
    [
        (1500, 100, "A"),
        (1020, 95, "B"),
        (1200, 45, "C"),
        (0, 100, "D"),
        (300, 45, "F"),
    ],
)
def test_compute_score_grades(wallet, roadworthiness, grade):
    assert app.compute_score(wallet, roadworthiness)["grade"] == grade


def test_compute_score_clamps_negative_wallet():
    score = app.compute_score(-500, 95)
    assert score["financial"] == 0


# ---------------------------------------------------------------------------
# Reading the AI's reply
# ---------------------------------------------------------------------------

def test_extract_json_plain():
    assert app.extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_code_fence():
    assert app.extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_extra_text_around_it():
    assert app.extract_json('Sure! Here you go: {"a": 1} Hope that helps.') == {"a": 1}


def test_extract_json_rejects_non_json():
    with pytest.raises(app.QuoteError):
        app.extract_json("Sorry, I can't help with that.")


def test_validate_payload_uses_game_titles_not_ai_titles():
    result = app.validate_payload(good_payload())
    assert result["quotes"]["quote_fair"]["title"] == "Certified Independent Repair"
    assert result["quotes"]["quote_fair"]["cost"] == 900
    assert result["warnings"] == []


def test_validate_payload_reads_cost_strings():
    payload = good_payload()
    payload["quote_dealer"]["cost"] = "$2,450"
    assert app.validate_payload(payload)["quotes"]["quote_dealer"]["cost"] == 2450


@pytest.mark.parametrize("bad_cost", [0, -5, 999_999, "lots", None, True])
def test_validate_payload_rejects_bad_costs(bad_cost):
    payload = good_payload()
    payload["quote_fair"]["cost"] = bad_cost
    with pytest.raises(app.QuoteError):
        app.validate_payload(payload)


def test_validate_payload_rejects_missing_quote():
    payload = good_payload()
    del payload["quote_budget"]
    with pytest.raises(app.QuoteError):
        app.validate_payload(payload)


def test_validate_payload_fills_in_missing_tips():
    payload = good_payload()
    payload["negotiation_tips"] = ["Only one?"]
    tips = app.validate_payload(payload)["tips"]
    assert len(tips) == 3
    assert tips[0] == "Only one?"


def test_validate_payload_warns_when_prices_out_of_order():
    result = app.validate_payload(good_payload(dealer=500, budget=300, fair=900))
    assert result["warnings"]


# ---------------------------------------------------------------------------
# Calling the AI (with a fake client)
# ---------------------------------------------------------------------------

def test_fetch_ai_quotes_success(gemini_env, one_pothole):
    client = FakeClient([json.dumps(good_payload())])
    result = app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))
    assert result["is_ai"] is True
    assert "Gemini" in result["source"]
    assert client.calls[0]["response_format"] == {"type": "json_object"}


def test_fetch_ai_quotes_retries_after_bad_reply(gemini_env, one_pothole):
    client = FakeClient(["not json at all", json.dumps(good_payload())])
    result = app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))
    assert result["is_ai"] is True
    assert len(client.calls) == 2
    assert "response_format" not in client.calls[1]


def test_fetch_ai_quotes_gives_up_after_two_bad_replies(gemini_env, one_pothole):
    client = FakeClient(["nope", "still nope"])
    with pytest.raises(app.QuoteError):
        app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))


def test_fetch_ai_quotes_without_key(monkeypatch, one_pothole):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(app.MissingKeyError):
        app.fetch_ai_quotes(one_pothole, client_factory=factory_for(FakeClient([])))


def test_fetch_ai_quotes_bad_key_message(gemini_env, one_pothole, monkeypatch):
    class FakeAuthError(Exception):
        pass

    monkeypatch.setattr(app.openai, "AuthenticationError", FakeAuthError)
    client = FakeClient([FakeAuthError("401")])
    with pytest.raises(app.QuoteError, match="GEMINI_API_KEY"):
        app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))


def test_gemini_default_models(gemini_env):
    provider = app.resolve_provider()
    assert provider["model"] == "gemini-3.5-flash"
    assert len(provider["models"]) >= 2


def test_gemini_model_list_from_env(gemini_env, monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "model-a, model-b")
    assert app.resolve_provider()["models"] == ["model-a", "model-b"]


class FakeStatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class FakeRateError(Exception):
    pass


@pytest.fixture
def two_models(gemini_env, monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "busy-model, good-model")
    monkeypatch.setattr(app.openai, "APIStatusError", FakeStatusError)
    monkeypatch.setattr(app.openai, "RateLimitError", FakeRateError)


@pytest.mark.parametrize("failure", [FakeStatusError(503), FakeStatusError(404), FakeRateError("429")])
def test_busy_model_falls_through_to_next(two_models, one_pothole, failure):
    client = FakeClient([failure, json.dumps(good_payload())])
    result = app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))
    assert [c["model"] for c in client.calls] == ["busy-model", "good-model"]
    assert "good-model" in result["source"]


def test_all_models_busy_raises_friendly_error(two_models, one_pothole):
    client = FakeClient([FakeStatusError(503), FakeStatusError(503)])
    with pytest.raises(app.QuoteError, match="busy"):
        app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))


def test_other_client_errors_do_not_try_next_model(two_models, one_pothole):
    client = FakeClient([FakeStatusError(403)])
    with pytest.raises(app.QuoteError, match="403"):
        app.fetch_ai_quotes(one_pothole, client_factory=factory_for(client))
    assert len(client.calls) == 1


def test_ai_provider_setting_prefers_gemini(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("GEMINI_API_KEY", "m")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    assert app.resolve_provider()["name"] == "Gemini"


# ---------------------------------------------------------------------------
# Offline fallback
# ---------------------------------------------------------------------------

def test_offline_quotes_are_labeled_and_ordered(one_pothole):
    result = app.build_offline_quotes(one_pothole)
    assert result["is_ai"] is False
    assert "not AI-generated" in result["source"]
    q = result["quotes"]
    assert q["quote_budget"]["cost"] < q["quote_fair"]["cost"] < q["quote_dealer"]["cost"]
    low, high = app.reference_range(one_pothole)
    assert low <= q["quote_fair"]["cost"] <= high
