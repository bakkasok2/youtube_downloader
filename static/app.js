const form = document.querySelector("#lookup-form");
const urlInput = document.querySelector("#video-url");
const lookupButton = document.querySelector("#lookup-button");
const panel = document.querySelector("#video-panel");
const thumbnail = document.querySelector("#thumbnail");
const title = document.querySelector("#video-title");
const duration = document.querySelector("#video-duration");
const quality = document.querySelector("#quality");
const downloadButton = document.querySelector("#download-button");
const statusBox = document.querySelector("#status");

function setStatus(message = "", type = "") {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`.trim();
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return "";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remaining = Math.floor(seconds % 60);
  return [hours, minutes, remaining]
    .filter((_, index) => hours > 0 || index > 0)
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
}

async function readError(response) {
  try {
    const data = await response.json();
    return data.error || "요청을 처리하지 못했습니다.";
  } catch {
    return "서버 응답을 확인하지 못했습니다.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  panel.hidden = true;
  lookupButton.disabled = true;
  setStatus("영상 정보와 해상도를 확인하고 있습니다…");

  try {
    const response = await fetch("/api/formats", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlInput.value }),
    });
    if (!response.ok) throw new Error(await readError(response));

    const data = await response.json();
    title.textContent = data.title;
    thumbnail.src = data.thumbnail || "";
    thumbnail.alt = `${data.title} 미리보기`;
    duration.textContent = formatDuration(data.duration);
    quality.replaceChildren();

    const best = new Option("최고 화질", "best");
    quality.add(best);
    data.resolutions.forEach((item) => {
      const details = [
        item.label,
        item.fps ? `${Math.round(item.fps)}fps` : "",
        item.hdr ? "HDR" : "",
      ].filter(Boolean);
      quality.add(new Option(details.join(" · "), String(item.height)));
    });

    panel.hidden = false;
    setStatus("다운로드할 해상도를 선택해 주세요.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    lookupButton.disabled = false;
  }
});

downloadButton.addEventListener("click", async () => {
  downloadButton.disabled = true;
  setStatus("서버에서 MP4 파일을 준비하고 있습니다. 창을 닫지 마세요…");

  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: urlInput.value,
        height: quality.value,
      }),
    });
    if (!response.ok) throw new Error(await readError(response));

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const disposition = response.headers.get("Content-Disposition") || "";
    const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i);
    const plainName = disposition.match(/filename="?([^";]+)"?/i);
    let filename = "Jini_video.mp4";

    if (encodedName) {
      filename = decodeURIComponent(encodedName[1]);
    } else if (plainName) {
      filename = plainName[1];
    }

    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 30_000);
    setStatus("MP4 다운로드를 시작했습니다.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    downloadButton.disabled = false;
  }
});
