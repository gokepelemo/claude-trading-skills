"""Unit tests for check_alpaca_connection.py (no network access required)."""

# Import as a module (not `from ... import test_*`) so pytest does not try to
# collect the script's own `test_account_info` / `test_positions` helpers.
import check_alpaca_connection as cac
import pytest


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


def _patch_get(monkeypatch, response=None, exc=None):
    """Replace requests.get with a stub returning `response` or raising `exc`."""
    calls = []

    def fake_get(url, headers=None, **kwargs):
        calls.append({"url": url, "headers": headers})
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(cac.requests, "get", fake_get)
    return calls


# --- get_base_url -----------------------------------------------------------


def test_get_base_url_paper():
    assert cac.get_base_url(True) == "https://paper-api.alpaca.markets"


def test_get_base_url_live():
    assert cac.get_base_url(False) == "https://api.alpaca.markets"


# --- load_credentials -------------------------------------------------------


def test_load_credentials_missing_exits(monkeypatch, capsys):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        cac.load_credentials()

    assert exc_info.value.code == 1
    assert "ALPACA_API_KEY" in capsys.readouterr().out


def test_load_credentials_defaults_to_paper(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "key123")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret456")
    monkeypatch.delenv("ALPACA_PAPER", raising=False)

    assert cac.load_credentials() == ("key123", "secret456", True)


def test_load_credentials_live_flag(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "key123")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret456")
    monkeypatch.setenv("ALPACA_PAPER", "FALSE")

    assert cac.load_credentials()[2] is False


# --- test_account_info ------------------------------------------------------


def test_account_info_success(monkeypatch, capsys):
    payload = {
        "status": "ACTIVE",
        "account_number": "PA123",
        "equity": "10000.50",
        "cash": "2500",
        "buying_power": "5000",
        "portfolio_value": "10000.50",
    }
    calls = _patch_get(monkeypatch, FakeResponse(200, payload))

    assert cac.test_account_info("k", "s", "https://paper-api.alpaca.markets") is True

    assert calls[0]["url"] == "https://paper-api.alpaca.markets/v2/account"
    assert calls[0]["headers"] == {"APCA-API-KEY-ID": "k", "APCA-API-SECRET-KEY": "s"}
    out = capsys.readouterr().out
    assert "Equity: $10,000.50" in out
    assert "WARNING" not in out


def test_account_info_warns_when_blocked(monkeypatch, capsys):
    payload = {"status": "ACTIVE", "trading_blocked": True}
    _patch_get(monkeypatch, FakeResponse(200, payload))

    assert cac.test_account_info("k", "s", "https://x") is True
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "Trading is blocked" in out


@pytest.mark.parametrize("status", [401, 403, 500])
def test_account_info_http_error(monkeypatch, status):
    _patch_get(monkeypatch, FakeResponse(status, text="err"))
    assert cac.test_account_info("k", "s", "https://x") is False


def test_account_info_network_error(monkeypatch, capsys):
    _patch_get(monkeypatch, exc=cac.requests.exceptions.RequestException("boom"))

    assert cac.test_account_info("k", "s", "https://x") is False
    assert "Network error" in capsys.readouterr().out


# --- test_positions ---------------------------------------------------------


def test_positions_empty(monkeypatch, capsys):
    _patch_get(monkeypatch, FakeResponse(200, []))

    assert cac.test_positions("k", "s", "https://x") is True
    assert "Portfolio is empty" in capsys.readouterr().out


def test_positions_totals(monkeypatch, capsys):
    positions = [
        {
            "symbol": "AAPL",
            "qty": "10",
            "avg_entry_price": "150",
            "current_price": "160",
            "market_value": "1600",
            "unrealized_pl": "100",
            "unrealized_plpc": "0.0667",
        },
        {
            "symbol": "MSFT",
            "qty": "5",
            "avg_entry_price": "400",
            "current_price": "380",
            "market_value": "1900",
            "unrealized_pl": "-100",
            "unrealized_plpc": "-0.05",
        },
    ]
    calls = _patch_get(monkeypatch, FakeResponse(200, positions))

    assert cac.test_positions("k", "s", "https://x") is True

    assert calls[0]["url"] == "https://x/v2/positions"
    out = capsys.readouterr().out
    assert "Found 2 position(s)" in out
    assert "Total Portfolio Value: $3,500.00" in out
    assert "Total Unrealized P/L: $0.00" in out
    assert "+$100.00 (+6.67%)" in out
    assert "-$100.00 (-5.00%)" in out


def test_positions_http_error(monkeypatch):
    _patch_get(monkeypatch, FakeResponse(500, text="server error"))
    assert cac.test_positions("k", "s", "https://x") is False


def test_positions_network_error(monkeypatch):
    _patch_get(monkeypatch, exc=cac.requests.exceptions.RequestException("down"))
    assert cac.test_positions("k", "s", "https://x") is False


# --- test_market_data (optional, never raises) ------------------------------


def test_market_data_paid_tier_message(monkeypatch, capsys):
    _patch_get(monkeypatch, FakeResponse(402))
    cac.test_market_data("k", "s")
    assert "paid subscription" in capsys.readouterr().out


def test_market_data_swallows_exceptions(monkeypatch, capsys):
    _patch_get(monkeypatch, exc=RuntimeError("unexpected"))
    cac.test_market_data("k", "s")  # must not raise
    assert "Could not test market data API" in capsys.readouterr().out


# --- main -------------------------------------------------------------------


def test_main_success_exit_code(monkeypatch, capsys):
    monkeypatch.setenv("ALPACA_API_KEY", "abcdefgh1234")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("ALPACA_PAPER", "true")
    monkeypatch.setattr(cac, "test_account_info", lambda *a: True)
    monkeypatch.setattr(cac, "test_positions", lambda *a: True)
    monkeypatch.setattr(cac, "test_market_data", lambda *a: None)

    assert cac.main() == 0
    out = capsys.readouterr().out
    assert "Mode: PAPER TRADING" in out
    assert "All tests passed" in out


def test_main_failure_skips_positions(monkeypatch, capsys):
    monkeypatch.setenv("ALPACA_API_KEY", "abcdefgh1234")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("ALPACA_PAPER", "false")
    called = {"positions": False}

    def fake_positions(*a):
        called["positions"] = True
        return True

    monkeypatch.setattr(cac, "test_account_info", lambda *a: False)
    monkeypatch.setattr(cac, "test_positions", fake_positions)
    monkeypatch.setattr(cac, "test_market_data", lambda *a: None)

    assert cac.main() == 1
    assert called["positions"] is False
    out = capsys.readouterr().out
    assert "Mode: LIVE TRADING" in out
    assert "Some tests failed" in out
