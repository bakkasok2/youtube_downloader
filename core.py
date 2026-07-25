from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def validate_youtube_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if not url or len(url) > 2048:
        raise ValueError("유튜브 영상 주소를 입력해 주세요.")

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or host not in ALLOWED_HOSTS:
        raise ValueError("youtube.com 또는 youtu.be 영상 주소만 사용할 수 있습니다.")
    if host == "youtu.be" and not parsed.path.strip("/"):
        raise ValueError("올바른 유튜브 영상 주소가 아닙니다.")

    params = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("list", "index", "start_radio", "pp"):
        params.pop(key, None)
    cleaned_query = urlencode({key: values[0] for key, values in params.items()})
    return urlunparse(parsed._replace(query=cleaned_query))


def available_resolutions(info: dict) -> list[dict]:
    best_by_height: dict[int, dict] = {}
    for item in info.get("formats") or []:
        height = item.get("height")
        if not isinstance(height, int) or item.get("vcodec") in {None, "none"}:
            continue

        candidate = {
            "height": height,
            "label": f"{height}p",
            "fps": item.get("fps"),
            "hdr": item.get("dynamic_range") not in {None, "SDR"},
            "tbr": item.get("tbr") or 0,
        }
        current = best_by_height.get(height)
        if current is None or candidate["tbr"] > current["tbr"]:
            best_by_height[height] = candidate

    choices = sorted(best_by_height.values(), key=lambda item: item["height"], reverse=True)
    for item in choices:
        item.pop("tbr", None)
    return choices


def format_selector(height: str) -> str:
    if height == "best":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

    if not re.fullmatch(r"\d{3,4}", height or ""):
        raise ValueError("올바른 해상도를 선택해 주세요.")

    numeric_height = int(height)
    if not 144 <= numeric_height <= 4320:
        raise ValueError("지원하지 않는 해상도입니다.")

    return (
        f"bestvideo[height<={numeric_height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={numeric_height}]+bestaudio/"
        f"best[height<={numeric_height}]"
    )
