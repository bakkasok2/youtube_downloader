# Jini YouTube Downloader

유튜브 영상 주소를 입력하고 해상도를 선택해 MP4 파일로 내려받는 서버형 웹 프로그램입니다.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/bakkasok2/youtube_downloader)

## 주요 기능

- YouTube URL 검증
- 영상 제목, 썸네일, 재생시간, 지원 해상도 조회
- 선택한 최대 해상도로 영상과 오디오 병합
- MP4 형식으로 브라우저 다운로드
- 최신 `yt-dlp` GitHub `master` 브랜치 사용
- FFmpeg 포함 Docker 및 Render Blueprint 제공

## Render 배포

1. Render에서 **New > Blueprint**를 선택합니다.
2. 이 GitHub 저장소를 연결합니다.
3. `render.yaml`을 확인하고 배포합니다.

Docker 이미지에는 FFmpeg와 최신 yt-dlp가 자동 설치됩니다.

## 로컬 실행

```bash
docker build -t jini-youtube-downloader .
docker run --rm -p 10000:10000 jini-youtube-downloader
```

브라우저에서 `http://localhost:10000`을 엽니다.

## 이용 안내

본인이 소유하거나 다운로드 허가를 받은 콘텐츠에만 사용하세요. YouTube 이용약관과 저작권 관련 법규를 준수해야 합니다.


## 무료 실행 방법

첨부 데스크톱 프로그램과 동일하게 사용자의 Windows 컴퓨터에서 yt-dlp를 실행하고, Cloudflare Quick Tunnel로 임시 웹 주소를 만듭니다.

1. 이 저장소를 ZIP으로 다운로드하고 압축을 풉니다.
2. `start_free_server.bat`를 더블클릭합니다.
3. 처음 실행 시 Python 패키지와 공식 cloudflared 실행 파일이 자동으로 설치됩니다.
4. 검은 창에 표시되는 `https://...trycloudflare.com` 주소를 브라우저에서 엽니다.
5. 창을 닫으면 서버와 주소가 종료됩니다.

컴퓨터가 켜져 있고 실행 창이 열려 있는 동안만 사용할 수 있습니다. Quick Tunnel 주소는 실행할 때마다 달라질 수 있습니다.
