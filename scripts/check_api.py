"""Can the key in .env call the model? Prints `ok` or the API's error type and message, never the key.

One call with max_tokens=1 to the smallest model: a refused call costs nothing, an accepted one a few tokens.

    python scripts/check_api.py
"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rebbi.gateway import UPSTREAM, real_api_key  # noqa: E402

key = real_api_key(Path(__file__).resolve().parent.parent / ".env")
try:
    r = httpx.post(
        f"{UPSTREAM}/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        json={"model": "claude-haiku-5-5", "max_tokens": 1, "messages": [{"role": "user", "content": "ok"}]},
        timeout=30,
    )
except httpx.HTTPError as e:
    print(f"network: {e}")
    sys.exit(2)
if r.status_code == 200:
    print("ok")
    sys.exit(0)
error = r.json().get("error", {}) if r.headers.get("content-type", "").startswith("application/json") else {}
print(f"{r.status_code} {error.get('type', '')}: {error.get('message', r.text[:200])}")
sys.exit(1)
