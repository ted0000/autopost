# AutoPost

AutoPost 프로젝트는 웹 페이지, YouTube 영상, 텍스트 파일 등 다양한 소스로부터 블로그 게시물을 자동으로 생성하고 게시하는 Python 기반의 도구입니다. OpenAI와 Gemini 클라이언트를 연동하여 콘텐츠를 처리하고 카테고리를 분류합니다. 생성된 콘텐츠는 WordPress의 Gutenberg 에디터 형식에 맞게 포맷팅된 후 게시됩니다.

## Blog URL (Wordpress based)
https://klutz91.kr

## 제약사항
1. wordpress.com에서 hosting하는 블로그를 대상으로 한다.
2. 비지니스 요금제이상을 사용해야 api를 사용가능하다.

## Language model 설정
root/config/config.py의 LANGUAGE_MODEL 설정.

## 기능

### Article Process (웹 페이지 처리)
1. 웹 페이지 URL을 인자로 전달합니다.
2. 웹 페이지를 분석하여 블로그 게시물을 생성합니다.
3. Gutenberg 포맷으로 내용을 재구성합니다.
4. 블로그에 게시합니다.

### YouTube Process (유튜브 처리)
1. YouTube URL을 인자로 전달합니다.
2. YouTube에서 자막을 다운로드하고 이를 바탕으로 블로그 게시물을 생성합니다.
3. Gutenberg 포맷으로 내용을 재구성합니다.
4. 블로그에 게시합니다.

### Text Process (신규 기능 - 텍스트 파일 처리)
1. 게시할 내용을 포함한 `.txt` 파일을 인자로 전달합니다.
2. 파일 내용을 읽어 블로그 게시물을 생성하고 카테고리를 분류합니다.
3. Gutenberg 포맷으로 내용을 재구성합니다.
4. 블로그에 게시합니다.

## 설치 및 설정

1. **저장소 클론**:
   ```bash
   git clone https://github.com/ted0000/autopost.git
   cd autopost
   ```
2. 필수 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```
3. 환경 변수 설정:
   프로젝트 루트 디렉토리에 .env 파일을 생성하고, API 키 및 설정 정보를 추가합니다.

## 사용법
스크립트는 URL, 파일, 텍스트 파일 인자를 통해 블로그 게시물을 처리할 수 있습니다.

### 예제 명령어
- 단일 URL 처리:
 ```bash
 python main.py --url "https://example.com"
 ```
- Youtube 처리
```bash
python main.py --url "https://youtube.com/watch?v=example"
```
- URL 목록 처리
```bash
python main.py --file urls.txt
```
- URL 목록 처리
```bash
python main.py --txt content.txt
```

## 파일 구조
- main.py: 주요 실행 파일로, URL 또는 파일을 인자로 받아 처리합니다.
- ArticleProcessor.py: 웹 페이지 URL을 처리하는 클래스.
- YoutubeProcessor.py: YouTube URL을 처리하는 클래스.
- TextProcessor.py: 텍스트 파일을 처리하는 클래스.

이 프로젝트를 통해 다양한 소스를 자동으로 블로그 게시물로 변환하고 관리할 수 있습니다.