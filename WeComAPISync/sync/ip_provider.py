from __future__ import annotations

import json
import urllib.request


IP_SOURCES = (
    "https://ip.sb/api/ip",
    "https://api.ipify.org",
    "https://myip.ipip.net/json",
)


def _read_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore").strip()


def get_public_ip() -> str:
    errors: list[str] = []
    for url in IP_SOURCES:
        try:
            body = _read_url(url)
            if body.startswith("{"):
                parsed = json.loads(body)
                body = parsed.get("data", {}).get("ip", body)
            body = body.strip()
            if body and ("." in body or ":" in body):
                return body
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("; ".join(errors) or "unable to resolve public IP")
