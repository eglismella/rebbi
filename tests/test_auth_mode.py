import pytest

from rebbi.fleet import detect_auth


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def env_file(tmp_path, text):
    path = tmp_path / ".env"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_token_alone_means_subscription(tmp_path):
    assert detect_auth(env_file(tmp_path, "CLAUDE_CODE_OAUTH_TOKEN=tok\n")) == "subscription"


def test_an_api_key_goes_through_the_gateway_by_default(tmp_path):
    path = env_file(tmp_path, "ANTHROPIC_API_KEY=sk\nCLAUDE_CODE_OAUTH_TOKEN=tok\n")
    assert detect_auth(path) == "api-key"
    assert detect_auth(path, "subscription") == "subscription"


def test_asking_for_a_mode_without_its_credential_fails_clearly(tmp_path):
    with pytest.raises(SystemExit, match="CLAUDE_CODE_OAUTH_TOKEN"):
        detect_auth(env_file(tmp_path, "ANTHROPIC_API_KEY=sk\n"), "subscription")
    with pytest.raises(SystemExit, match="claude setup-token"):
        detect_auth(env_file(tmp_path, ""))
