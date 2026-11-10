"""Tiny client for FreeLLMAPI's Anthropic-compatible /v1/messages endpoint.

Standard library only. Reads settings from the environment or a .env file in the repo root.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path=ROOT / ".env"):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def complete(prompt, system=None, max_tokens=8000, temperature=0.7, timeout=600):
    """Send one prompt and return the reply text."""
    load_env()
    base = os.environ.get("FREELLMAPI_BASE_URL", "http://127.0.0.1:31415").rstrip("/")
    key = os.environ.get("FREELLMAPI_API_KEY", "")
    model = os.environ.get("FREELLMAPI_MODEL", "claude-sonnet-5-5")
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system
    req = urllib.request.Request(
        f"{base}/v1/messages",
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": key,
            "authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"FreeLLMAPI returned HTTP {e.code}: {e.read()[:300]!r}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Could not reach FreeLLMAPI at {base}. Is the app open? ({e})")
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
