# Jini YouTube Downloader

유튜브 영상 주소를 입력하고 해상도를 선택해 MP4 파일로 내려받는 서버형 웹 프로그램입니다.

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
