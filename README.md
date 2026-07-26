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

## 무료 고정 주소로 실행하기 (Windows + zrok)

사용자의 Windows 컴퓨터에서 yt-dlp를 실행하고 zrok 무료 고정 주소로 접속합니다. YouTube 요청도 사용자 컴퓨터의 인터넷 회선을 사용하므로 Render 서버 IP 제한을 피할 수 있습니다.

### 처음 한 번

1. 이 저장소에서 **Code > Download ZIP**을 눌러 내려받고 압축을 풉니다.
2. `start_free_server.bat`를 더블클릭합니다.
3. 처음 실행 시 Python 패키지와 최신 공식 `zrok2`가 자동 설치됩니다.
4. 검은 창에서 요구하면 zrok 웹 화면의 **Account Token**을 복사해 붙여넣습니다.
5. 기본 주소 이름 `jini-youtube-downloader`이 이미 사용 중이면, 영문 소문자·숫자·하이픈으로 다른 이름을 한 번 입력합니다.

설정이 끝나면 검은 창에 아래 형식의 고정 주소가 표시됩니다.

```text
https://주소이름.shares.zrok.io
```

### 다음부터

`start_free_server.bat`만 더블클릭하면 같은 주소가 다시 열립니다. 프로그램 창과 컴퓨터가 켜져 있는 동안만 주소가 작동합니다.

## Render 배포

1. Render에서 **New > Blueprint**를 선택합니다.
2. 이 GitHub 저장소를 연결합니다.
3. `render.yaml`을 확인하고 배포합니다.

Docker 이미지에는 FFmpeg와 최신 yt-dlp가 자동 설치됩니다. 다만 Render의 공유 서버 IP는 YouTube에서 제한될 수 있으므로, 별도의 주거용 프록시가 없다면 위의 Windows + zrok 실행 방법을 사용하세요.

## 로컬 실행

```bash
docker build -t jini-youtube-downloader .
docker run --rm -p 10000:10000 jini-youtube-downloader
```

브라우저에서 `http://localhost:10000`을 엽니다.

## 이용 안내

본인이 소유하거나 다운로드 허가를 받은 콘텐츠에만 사용하세요. YouTube 이용약관과 저작권 관련 법규를 준수해야 합니다.
