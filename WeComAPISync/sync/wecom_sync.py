#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from .browser_sync import sync_ip_with_browser
from .config import load_config
from .ip_provider import get_public_ip
from .state import append_log, read_text, write_text


def result(ok: bool, ip: str, status: str, message: str, verified: bool = False, screenshot: str = "") -> dict:
    return {
        "ok": ok,
        "ip": ip,
        "status": status,
        "message": message,
        "verified": verified,
        "screenshot": screenshot,
    }


def sync_once(force: bool = False) -> dict:
    config = load_config()
    ip = get_public_ip()
    last_ip = read_text(config.last_ip_path)

    if ip == last_ip and not force:
        message = f"IP {ip} unchanged and previously verified"
        append_log(config.log_path, message)
        return result(True, ip, "unchanged", message, verified=True)

    browser_result = sync_ip_with_browser(config, ip)
    if browser_result.ok and browser_result.verified:
        write_text(config.last_ip_path, ip)
        message = browser_result.message
        append_log(config.log_path, message)
        return result(True, ip, "verified", message, verified=True)

    message = browser_result.message
    append_log(config.log_path, message)
    return result(False, ip, "not_verified", message, verified=False, screenshot=browser_result.screenshot)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="run one sync attempt")
    parser.add_argument("--force", action="store_true", help="sync even when IP did not change")
    parser.add_argument("--ip", action="store_true", help="print public IP as JSON")
    args = parser.parse_args()

    try:
        if args.ip:
            ip = get_public_ip()
            print(json.dumps(result(True, ip, "ip", ip), ensure_ascii=False))
            return 0
        output = sync_once(force=args.force or args.once)
        print(json.dumps(output, ensure_ascii=False))
        return 0 if output["ok"] else 1
    except Exception as exc:
        print(json.dumps(result(False, "", "error", str(exc)), ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
