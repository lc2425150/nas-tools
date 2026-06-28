from __future__ import annotations

import json
import urllib.parse
import urllib.request


ALLOW_TYPES = (3, 4, 1, 2)


def _post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def get_token(corp_id: str, corp_secret: str) -> str:
    query = urllib.parse.urlencode({"corpid": corp_id, "corpsecret": corp_secret})
    result = _get_json(f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?{query}")
    token = result.get("access_token")
    if not token:
        raise RuntimeError(result.get("errmsg") or str(result))
    return token


def try_set_allow_address(corp_id: str, corp_secret: str, ip: str) -> str:
    token = get_token(corp_id, corp_secret)
    last_error = ""
    for allow_type in ALLOW_TYPES:
        try:
            get_result = _post_json(
                f"https://qyapi.weixin.qq.com/cgi-bin/get_allow_address?access_token={token}",
                {"type": allow_type},
            )
            if get_result.get("errcode") != 0:
                last_error = f"type={allow_type} get: {get_result.get('errmsg')}"
                continue

            current = list(get_result.get("allow_address") or [])
            if ip not in current:
                current.append(ip)

            set_result = _post_json(
                f"https://qyapi.weixin.qq.com/cgi-bin/set_allow_address?access_token={token}",
                {"type": allow_type, "address_list": current},
            )
            if set_result.get("errcode") == 0:
                return f"api type={allow_type} accepted"
            last_error = f"type={allow_type} set: {set_result.get('errmsg')}"
        except Exception as exc:
            last_error = f"type={allow_type}: {exc}"
    raise RuntimeError(last_error or "all allow address API types failed")
