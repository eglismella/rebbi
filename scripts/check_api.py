"""Can the credentials in .env reach the model? Prints which way works, or why not; never a secret.

- ANTHROPIC_API_KEY: one Messages call with max_tokens=1. A refused call costs nothing.
- CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`): one one-word reply through the
  unmodified Claude Code binary, signed in with that token, as the agents will be.

    python scripts/check_api.py          # exit 0 and print the working --auth mode, else exit 1
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rebbi.fleet import INHERITED_PREFIXES  # noqa: E402
from rebbi.gateway import UPSTREAM  # noqa: E402


def check_api_key(key: str) -> str | None:
    """None if the key can make calls, else why not."""
    try:
        r = httpx.post(
            f"{UPSTREAM}/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            json={"model": "claude-haiku-5-5", "max_tokens": 1, "messages": [{"role": "user", "content": "ok"}]},
            timeout=30,
        )
    except httpx.HTTPError as e:
        return f"network: {e}"
    if r.status_code == 200:
        return None
    error = r.json().get("error", {}) if r.headers.get("content-type", "").startswith("application/json") else {}
    return f"{r.status_code} {error.get('type', '')}: {error.get('message', r.text[:200])}"


async def check_oauth_token(token: str) -> str | None:
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    for name in list(os.environ):
        if name.upper().startswith(INHERITED_PREFIXES):
            del os.environ[name]
    result = None
    # On Windows the CLI can still hold its config folder for a moment after it exits.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as config_dir:
        options = ClaudeAgentOptions(
            model="claude-haiku-5-5", tools=[], max_turns=1, setting_sources=[], cwd=config_dir,
            env={"CLAUDE_CODE_OAUTH_TOKEN": token, "CLAUDE_CONFIG_DIR": config_dir,
                 "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"},
        )
        # Read to the end rather than returning mid-stream, so the SDK shuts the CLI down cleanly.
        async for message in query(prompt="Reply with the single word ok.", options=options):
            if isinstance(message, ResultMessage):
                result = message
    if result is None:
        return "no result from the CLI"
    return None if not result.is_error else f"{result.api_error_status}: {result.result}"


def main() -> int:
    env = dotenv_values(ROOT / ".env")
    checks = []
    if key := env.get("ANTHROPIC_API_KEY"):
        checks.append(("api-key", lambda: check_api_key(key)))
    if token := env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        checks.append(("subscription", lambda: asyncio.run(check_oauth_token(token))))
    if not checks:
        print("no ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN in .env")
        return 1
    for mode, check in checks:
        problem = check()
        if problem is None:
            print(f"ok: --auth {mode}")
            return 0
        print(f"{mode} not usable: {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
