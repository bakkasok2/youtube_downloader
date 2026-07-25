from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from core import available_resolutions, format_selector, validate_youtube_url


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

MAX_DOWNLOAD_MB = int(os.getenv("MAX_DOWNLOAD_MB", "500"))
YOUTUBE_PROXY_URL = os.getenv("YOUTUBE_PROXY_URL", "").strip()


def proxy_options() -> dict:
    if not YOUTUBE_PROXY_URL:
        if os.getenv("RENDER"):
            raise RuntimeError("Render 서버용 프록시가 설정되지 않았습니다.")
        return {}

    parsed = urlparse(YOUTUBE_PROXY_URL)
    if parsed.scheme not in {"http", "https", "socks4", "socks5", "socks5h"} or not parsed.hostname:
        raise RuntimeError("Render의 YOUTUBE_PROXY_URL 설정이 올바르지 않습니다.")
    return {"proxy": YOUTUBE_PROXY_URL}


def ffmpeg_options() -> dict:
    if os.name != "nt":
        return {}
    try:
        import imageio_ffmpeg

        return {"ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe()}
    except Exception:
        app.logger.warning("Bundled FFmpeg was not found")
        return {}


def base_ydl_options() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "skip_unavailable_fragments": False,
        **ffmpeg_options(),
        **proxy_options(),
    }


def friendly_error(output: str) -> str:
    lowered = output.lower()
    if "프록시가 설정되지" in output or "youtube_proxy_url" in lowered:
        return output
    if "proxy" in lowered or "tunnel connection failed" in lowered:
        return "YouTube 연결용 프록시에 접속하지 못했습니다. Render의 프록시 설정을 확인해 주세요."
    if "private video" in lowered:
        return "비공개 영상은 다운로드할 수 없습니다."
    if "video unavailable" in lowered:
        return "재생할 수 없는 영상입니다."
    if "sign in to confirm" in lowered or "not a bot" in lowered or "login_required" in lowered:
        return "현재 프록시 IP가 YouTube에서 제한되었습니다. 주거용 프록시의 새 IP가 필요합니다."
    if "requested format is not available" in lowered:
        return "선택한 해상도를 사용할 수 없습니다. 다른 해상도를 선택해 주세요."
    if "file is larger than max-filesize" in lowered:
        return f"영상 용량이 제한({MAX_DOWNLOAD_MB}MB)을 초과했습니다."
    return "YouTube 영상 처리에 실패했습니다. 공개 영상 주소와 프록시 상태를 확인해 주세요."


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "commit": os.getenv("RENDER_GIT_COMMIT", "local")[:12],
            "proxy_configured": bool(YOUTUBE_PROXY_URL),
        }
    )


@app.post("/api/formats")
def formats():
    payload = request.get_json(silent=True) or {}
    try:
        url = validate_youtube_url(payload.get("url", ""))
        options = {**base_ydl_options(), "skip_download": True}
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info or info.get("_type") == "playlist":
            raise ValueError("재생목록이 아닌 영상 한 개의 주소를 입력해 주세요.")

        resolutions = available_resolutions(info)
        if not resolutions:
            raise RuntimeError("YouTube가 현재 프록시 IP에 영상 해상도를 제공하지 않았습니다.")

        return jsonify(
            {
                "title": info.get("title") or "제목 없는 영상",
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "resolutions": resolutions,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except (DownloadError, RuntimeError) as exc:
        app.logger.warning("Format lookup failed: %s", type(exc).__name__)
        return jsonify({"error": friendly_error(str(exc))}), 422
    except Exception:
        app.logger.exception("Unexpected format lookup failure")
        return jsonify({"error": "영상 정보를 불러오지 못했습니다. 프록시 설정을 확인해 주세요."}), 500


@app.post("/api/download")
def download():
    payload = request.get_json(silent=True) or {}
    temp_dir: str | None = None

    try:
        url = validate_youtube_url(payload.get("url", ""))
        selector = format_selector(str(payload.get("height", "")))
        temp_dir = tempfile.mkdtemp(prefix="jini-ytdlp-")
        output_template = str(Path(temp_dir) / "%(title).160B [%(id)s].%(ext)s")

        options = {
            **base_ydl_options(),
            "format": selector,
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "max_filesize": MAX_DOWNLOAD_MB * 1024 * 1024,
        }
        with YoutubeDL(options) as ydl:
            ydl.extract_info(url, download=True)

        candidates = sorted(
            Path(temp_dir).glob("*.mp4"),
            key=lambda item: item.stat().st_mtime,
        )
        if not candidates:
            raise RuntimeError("yt-dlp completed without an MP4 output file")

        output_file = candidates[-1].resolve()
        if Path(temp_dir).resolve() not in output_file.parents:
            raise RuntimeError("Unexpected output path")

        response = send_file(
            output_file,
            as_attachment=True,
            download_name=output_file.name,
            mimetype="video/mp4",
            conditional=True,
        )
        response.call_on_close(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        temp_dir = None
        return response
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except (DownloadError, RuntimeError) as exc:
        app.logger.warning("Download failed: %s", type(exc).__name__)
        return jsonify({"error": friendly_error(str(exc))}), 422
    except Exception:
        app.logger.exception("Unexpected download failure")
        return jsonify({"error": "파일을 준비하지 못했습니다. 프록시 설정을 확인해 주세요."}), 500
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
