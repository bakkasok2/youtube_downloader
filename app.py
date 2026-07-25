from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from core import available_resolutions, format_selector, validate_youtube_url


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

MAX_DOWNLOAD_MB = int(os.getenv("MAX_DOWNLOAD_MB", "500"))
DOWNLOAD_TIMEOUT_SECONDS = int(os.getenv("DOWNLOAD_TIMEOUT_SECONDS", "900"))
YOUTUBE_COOKIES_FILE = os.getenv("YOUTUBE_COOKIES_FILE", "/etc/secrets/youtube_cookies.txt")


def youtube_cookie_options() -> dict:
    """Copy Render's read-only secret cookie file to a writable runtime path."""
    secret_path = Path(YOUTUBE_COOKIES_FILE)
    if not secret_path.is_file() or secret_path.stat().st_size == 0:
        return {}

    runtime_path = Path(tempfile.gettempdir()) / f"jini-youtube-cookies-{os.getpid()}.txt"
    try:
        if (
            not runtime_path.is_file()
            or runtime_path.stat().st_size != secret_path.stat().st_size
        ):
            shutil.copyfile(secret_path, runtime_path)
            runtime_path.chmod(0o600)
    except OSError:
        app.logger.exception("Failed to prepare YouTube cookie file")
        return {}

    return {"cookiefile": str(runtime_path)}


def friendly_download_error(output: str) -> str:
    lowered = output.lower()
    if "private video" in lowered:
        return "비공개 영상은 다운로드할 수 없습니다."
    if "video unavailable" in lowered:
        return "재생할 수 없는 영상입니다."
    if "sign in to confirm" in lowered or "not a bot" in lowered or "login_required" in lowered:
        if not youtube_cookie_options():
            return "서버 인증이 필요합니다. 관리자가 Render에 YouTube 쿠키 비밀 파일을 등록해야 합니다."
        return "YouTube 인증 쿠키가 만료되었거나 서버 IP가 제한되었습니다. 관리자에게 쿠키 갱신을 요청해 주세요."
    if "requested format is not available" in lowered:
        return "선택한 해상도를 사용할 수 없습니다. 다른 해상도를 선택해 주세요."
    if "file is larger than max-filesize" in lowered:
        return f"영상 용량이 제한({MAX_DOWNLOAD_MB}MB)을 초과했습니다."
    return "영상을 내려받는 중 오류가 발생했습니다. 주소와 공개 상태를 확인해 주세요."


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "commit": os.getenv("RENDER_GIT_COMMIT", "local")[:12]})


@app.post("/api/formats")
def formats():
    payload = request.get_json(silent=True) or {}
    try:
        url = validate_youtube_url(payload.get("url", ""))
        base_options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "ignore_no_formats_error": True,
            "socket_timeout": 20,
            "retries": 2,
        }
        provider_args = {
            "youtubepot-bgutilscript": {
                "server_home": ["/root/bgutil-ytdlp-pot-provider/server"]
            }
        }
        attempts = [
            {
                **base_options,
                "extractor_args": {
                    "youtube": {"player_client": ["android_vr", "web_safari"]},
                    **provider_args,
                },
            },
            {
                **base_options,
                "extractor_args": {
                    "youtube": {"player_client": ["mweb"]},
                    **provider_args,
                },
                **youtube_cookie_options(),
            },
        ]

        last_info = None
        last_error = None
        for options in attempts:
            try:
                with YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=False)
            except DownloadError as exc:
                last_error = exc
                continue

            if not info or info.get("_type") == "playlist":
                continue

            last_info = info
            resolutions = available_resolutions(info)
            if resolutions:
                return jsonify(
                    {
                        "title": info.get("title") or "제목 없는 영상",
                        "thumbnail": info.get("thumbnail"),
                        "duration": info.get("duration"),
                        "resolutions": resolutions,
                    }
                )

        if last_info:
            raw_formats = last_info.get("formats") or []
            video_formats = [
                item for item in raw_formats
                if item.get("vcodec") not in {None, "none"}
            ]
            url_formats = [item for item in video_formats if item.get("url")]
            app.logger.warning(
                "No downloadable resolutions after fallbacks: total=%d video=%d url=%d",
                len(raw_formats),
                len(video_formats),
                len(url_formats),
            )
            raise ValueError(
                "YouTube가 이 서버에 영상 형식을 제공하지 않았습니다. "
                f"(진단: 전체 {len(raw_formats)}, 영상 {len(video_formats)}, "
                f"주소 {len(url_formats)})"
            )

        if last_error:
            raise last_error
        raise ValueError("영상 정보를 확인하지 못했습니다.")

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except DownloadError as exc:
        return jsonify({"error": friendly_download_error(str(exc))}), 422
    except Exception:
        app.logger.exception("Format lookup failed")
        return jsonify({"error": "영상 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."}), 500


@app.post("/api/download")
def download():
    payload = request.get_json(silent=True) or {}
    temp_dir: str | None = None

    try:
        url = validate_youtube_url(payload.get("url", ""))
        selector = format_selector(str(payload.get("height", "")))
        temp_dir = tempfile.mkdtemp(prefix="jini-ytdlp-")
        output_template = str(Path(temp_dir) / "%(title).160B [%(id)s].%(ext)s")

        command = [
            "yt-dlp",
            "--no-playlist",
            "--restrict-filenames",
            "--no-warnings",
            "--extractor-args",
            "youtube:player_client=web_safari,mweb",
            "--extractor-args",
            "youtubepot-bgutilscript:server_home=/root/bgutil-ytdlp-pot-provider/server",
            "--format",
            selector,
            "--merge-output-format",
            "mp4",
            "--remux-video",
            "mp4",
            "--max-filesize",
            f"{MAX_DOWNLOAD_MB}M",
            "--socket-timeout",
            "20",
            "--retries",
            "3",
            "--fragment-retries",
            "3",
            "--output",
            output_template,
            "--print",
            "after_move:filepath",
        ]
        cookie_options = youtube_cookie_options()
        if cookie_options:
            command.extend(["--cookies", cookie_options["cookiefile"]])
        command.append(url)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)

        candidates = [
            Path(line.strip())
            for line in result.stdout.splitlines()
            if line.strip() and Path(line.strip()).is_file()
        ]
        if not candidates:
            candidates = list(Path(temp_dir).glob("*.mp4"))
        if not candidates:
            raise RuntimeError("yt-dlp completed without an output file")

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
    except subprocess.TimeoutExpired:
        return jsonify({"error": "다운로드 제한 시간을 초과했습니다. 더 짧은 영상을 선택해 주세요."}), 504
    except RuntimeError as exc:
        app.logger.warning("yt-dlp failed: %s", str(exc)[-1200:])
        return jsonify({"error": friendly_download_error(str(exc))}), 422
    except Exception:
        app.logger.exception("Download failed")
        return jsonify({"error": "파일을 준비하지 못했습니다. 잠시 후 다시 시도해 주세요."}), 500
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
