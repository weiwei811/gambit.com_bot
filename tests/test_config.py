from src.config import login_credentials


def test_login_credentials_use_environment(monkeypatch):
    monkeypatch.setenv("GAMBIT_USERNAME", "example-user")
    monkeypatch.setenv("GAMBIT_PASSWORD", "example-test-password")
    assert login_credentials() == ("example-user", "example-test-password")


def test_credentials_optional_for_existing_session(monkeypatch):
    monkeypatch.delenv("GAMBIT_USERNAME", raising=False)
    monkeypatch.delenv("GAMBIT_PASSWORD", raising=False)
    assert login_credentials() == ("", "")
