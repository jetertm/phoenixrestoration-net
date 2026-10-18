"""Load and save the site content file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import CONTENT_PATH

PAYMENT_LINE = (
    "Payment due within 7 days of invoice (Net 7). Accepted: card or ACH via "
    "Stripe pay link, ACH bank transfer, cash, check, or cashier's check."
)


class ContentError(Exception):
    pass


def load_content(path: Path | None = None) -> dict[str, Any]:
    content_path = Path(path) if path else CONTENT_PATH
    try:
        data = json.loads(content_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContentError(f"Content file not found: {content_path}") from exc
    except json.JSONDecodeError as exc:
        raise ContentError(f"Content file is not valid JSON: {content_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContentError("Content file must be a JSON object.")
    _require(data)
    return data


def save_content(data: dict[str, Any], path: Path | None = None) -> Path:
    content_path = Path(path) if path else CONTENT_PATH
    content_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    content_path.write_text(text, encoding="utf-8")
    return content_path


def _require(data: dict[str, Any]) -> None:
    for key in ("business_name", "email", "facebook", "payment", "cta", "services", "service_area", "gallery"):
        if key not in data:
            raise ContentError(f"Content file is missing {key}.")
    if not isinstance(data["services"], list) or not data["services"]:
        raise ContentError("services must be a non-empty list.")
    if not isinstance(data["service_area"], list) or not data["service_area"]:
        raise ContentError("service_area must be a non-empty list.")
    if not isinstance(data["gallery"], list):
        raise ContentError("gallery must be a list.")
    if not str(data["email"]).strip():
        raise ContentError("email is empty.")
    if not str(data["payment"]).strip():
        raise ContentError("payment is empty.")


def unreviewed_images(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Gallery entries Eve has not approved. Missing reviewed counts as not approved."""
    pending = []
    for item in content.get("gallery", []):
        if not isinstance(item, dict):
            continue
        if item.get("reviewed") is not True:
            pending.append(item)
    return pending


def image_name(item: dict[str, Any]) -> str:
    if item.get("name"):
        return str(item["name"])
    src = str(item.get("src") or "")
    return Path(src).stem or "(unnamed)"
