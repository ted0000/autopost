# Python 표준 라이브러리
import json
import os
import re
import shutil
import tempfile

# 서드파티 라이브러리
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment, Tag
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from googleapiclient.discovery import build

# 로컬 모듈
from config.config import *
from core.text.WordpressAPI import WordpressAPI

class WebScrapper:
    def __init__(self, url):
        self.url = url
        self.temp_files = []
    
    def __del__(self):
        for f in self.temp_files:
            try:
                if os.path.isfile(f):  # 파일인 경우
                    LOG(f"파일 삭제: {f}")
                    os.unlink(f)
                elif os.path.isdir(f):  # 디렉터리인 경우
                    LOG(f"디렉토리 삭제: {f}")
                    shutil.rmtree(f)
                else:
                    LOG(f"Skipping unknown type: {f}")
            except Exception as e:
                ERROR(f"Error deleting {f}: {e}")
        self.temp_files.clear()  # temp_files 리스트도 정리
        LOG("All temporary files cleaned up.")

    def fetch_content(self):
        opt = webdriver.ChromeOptions()
        opt.add_argument('headless')

        driver = webdriver.Chrome(options=opt)
        driver.get(self.url)
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        page_source = driver.page_source
        driver.quit()

        return BeautifulSoup(page_source, 'html.parser')
    
    def save_image(self, url):
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # 이미지 확장자 추출
        _, ext = os.path.splitext(url)
        ext = ext.split('?')[0]  
        if not ext:
            ext = '.jpg'  # 기본 확장자

        # 임시 파일 생성
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)

        # 이미지 저장
        for chunk in response.iter_content(1024):
            temp_file.write(chunk)
        temp_file.close()

        self.temp_files.append(temp_file.name)
        return temp_file
        
    def search_images(self, query):
        image_url = self.search_image_bing(query)
        if not image_url:
            image_url = self.search_images_google(query)
        
        # LOG(f'이미지 검색 query: {query}')
        # LOG(f'이미지 검색 결과: {image_url}')
        return image_url
        
    def process_title_image(self, lang, title, image_url):
        """
        제목 이미지를 다운로드 후 WordPress에 업로드하고 featured_image_id를 반환합니다.
        """
        try:
            # LOG(f'Title Image 다운로드를 시작...\nLanguge: {lang}\nTitle: {title}\nImage URL: {image_url}')
            temp_file = self.save_image(image_url)
            # LOG(f'Title Image 다운로드 완료. temp file: {temp_file.name}')

            api = WordpressAPI()
            featured_image_id = api.media_upload(temp_file.name, title)

            return featured_image_id
        
        except requests.exceptions.RequestException as e:
            ERROR(f"{lang.upper()} - Title 이미지 다운로드 실패: {e}")
            return None
        
    def add_image_nodes_to_json(self, json_data):
        """
        URL과 JSON 데이터를 받아, JSON 내 subtitle 노드들에 이미지가 없을 경우
        Google/Bing 이미지 검색을 통해 이미지를 추가하고, title 이미지도 처리합니다.
        """
        def set_sub_image(node):
            for n in node.get('subtitles', []):
                if not n.get('image', None):
                    n['image'] = self.search_images(n['image_search_term'])

        def set_title_image(lang, node):
            node['image'] = self.process_title_image(lang, node['title'], node['image'])

        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        LOG('Title Image 처리를 시작합니다...')
        set_title_image('en', json_data)

        # subtitle 노드 중 이미지가 없는 경우 이미지 추가
        LOG('이미지가 없는 subtitle 노드에 이미지를 추가합니다 (Google/Bing 검색)')
        set_sub_image(json_data)

        return json_data
    
    def find_article(self):
        """
        기사 탐색 로직 개선 및 클린업:
        1. <article> 태그 우선 탐색
        2. 관련 div, section 태그 탐색 (article, post, story, article-body 등의 키워드)
        3. 필터링 후 최종 기사 후보 중 가장 길거나 평균 이상인 것 선택
        4. 최종 선택 요소에서 스크립트, 광고, 내비게이션 등을 제거하여 깔끔한 본문만 남김
        """

        def save_debug(soup, article):
            LOG('Debug: body, article 저장')
            root = os.path.join(os.getcwd(), 'dev')
            os.makedirs(root, exist_ok=True)
            
            body_text_path = os.path.join(root, 'body.txt')
            body_html_path = os.path.join(root, 'body.html')
            article_html_path = os.path.join(root, 'article.html')

            with open(body_text_path, 'w', encoding='utf-8') as f:
                f.write(soup.body.get_text(separator='\n', strip=True))
            with open(body_html_path, 'w', encoding='utf-8') as f:
                f.write(soup.body.prettify())

            if isinstance(article, list):
                merged_div = BeautifulSoup('<div></div>', 'html.parser').div
                for a in article:
                    merged_div.append(a)
                with open(article_html_path, 'w', encoding='utf-8') as f:
                    f.write(merged_div.prettify())
            else:
                with open(article_html_path, 'w', encoding='utf-8') as f:
                    f.write(article.prettify())

        def filter_articles_by_text_length(articles):
            LOG('텍스트 길이 평균 계산 후 필터링 중...')
            text_lengths = [len(a.get_text(strip=True)) for a in articles]
            if not text_lengths:
                LOG('기사 텍스트가 없습니다.')
                return []
            average_length = sum(text_lengths) / len(text_lengths)
            LOG(f'기사 후보 평균 길이: {average_length:.2f} chars')

            # 평균보다 긴 기사만 필터
            filtered = [a for a, length in zip(articles, text_lengths) if length > average_length]
            LOG(f'평균보다 긴 기사 수: {len(filtered)}개')

            return filtered, text_lengths

        def merge_articles(articles):
            LOG('필터링된 기사들을 하나로 합치는 중...')
            merged_div = BeautifulSoup('<div></div>', 'html.parser').div
            for article in articles:
                merged_div.append(article)
            LOG('기사 합치기 완료')
            return merged_div
        
        def remove_unwanted_elements(article_soup):
            # 스크립트, 스타일, iframe, 광고관련 div, 댓글, 공백 태그 제거
            for tag_name in ["script", "style", "iframe", "nav", "form"]:
                for t in article_soup.find_all(tag_name):
                    t.decompose()

            # 광고, 공유 버튼, SNS 링크로 추정되는 class나 id 정규식 제거
            # 특정한 패턴을 인식해서 제거할 수도 있음
            ad_keywords = re.compile(r'(ad-|adsbygoogle|google-auto-placed|taboola|sponsor|sns|share|social|comment|toolbar|quick-tool|footer|header|breadcrumbs)', re.IGNORECASE)
            for el in article_soup.find_all(
                lambda tag: (tag.get("id") and ad_keywords.search(tag.get("id"))) or
                            (tag.get("class") and any(ad_keywords.search(cls) for cls in tag.get("class"))) or
                            tag.name in ['aside','footer','header']
            ):
                el.decompose()

            # 주석 제거
            for comment in article_soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            # 빈 태그 제거 (글자수 없는 p, div 등)
            # for tag in article_soup.find_all():
            #     if tag.name not in ['br', 'img'] and not tag.get_text(strip=True):
            #         tag.decompose()

            return article_soup
        
        LOG(f'URL: {self.url} 페이지를 가져오는 중...')
        soup = self.fetch_content()
        LOG('페이지 분석 중...')

        candidates = set()

        # 1. <article> 태그
        articles = soup.find_all('article')
        candidates.update(articles)

        keywords_pattern = re.compile(r'(article|post|story)', re.IGNORECASE)

        def has_article_keyword(tag):
            # 혹시 모를 안전장치: tag가 Tag인지 확인
            if not isinstance(tag, Tag):
                return False
            for attr_value in tag.attrs.values():
                if isinstance(attr_value, str) and keywords_pattern.search(attr_value):
                    return True
                if isinstance(attr_value, list):
                    for v in attr_value:
                        if keywords_pattern.search(str(v)):
                            return True
            return False

        div_section_tags = soup.find_all(['div', 'section'])
        filtered_div_section = [t for t in div_section_tags if has_article_keyword(t)]
        candidates.update(filtered_div_section)

        candidates.update(soup.find_all(attrs={"itemprop": "articleBody"}))
        candidates.update(soup.find_all('main'))
        candidates.update(soup.find_all(attrs={"role": "main"}))

        if not candidates:
            ERROR('기사를 찾지 못했습니다.')
            return None

        candidates = list(candidates)

        filtered, lengths = filter_articles_by_text_length(candidates)
        if not filtered:
            LOG('평균보다 긴 기사가 없습니다. 가장 긴 기사 선택')
            max_len_idx = max(range(len(candidates)), key=lambda i: lengths[i])
            selected_article = candidates[max_len_idx]
        else:
            # 여러 개면 합치기
            selected_article = merge_articles(filtered)

        # 불필요한 요소 제거
        cleaned_article = remove_unwanted_elements(selected_article)

        # Debug 저장
        save_debug(soup, cleaned_article)
        
        # cleaned_article을 반환
        return cleaned_article
    
    def check_contents(self, data):
        if isinstance(data, str):
            data = json.loads(data)

        title = data.get('title', '')
        if 'Wrong Contents' in title:
            ERROR('콘텐츠가 카테고리와 맞지 않습니다.')
            return False
        
        category = data.get('category', '')
        if category not in CATEGORY:
            data['category'] = 'Uncategorized'
        
        LOG('콘텐츠 검사 완료')
        return True

    def search_image_bing(self, query):
        LOG(f'Bing 이미지 검색 시작: {query}')
        api_key = os.getenv('BING_SEARCH_API_KEY')
        endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}

        params = {
            'q': query,
            'count': 1,
            'imageType': 'Photo',
            'license': 'All',
            'safeSearch': 'Moderate',
            'mkt': 'ko-KR'
        }

        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        image_list = [v.get('contentUrl') for v in data.get('value', []) if v.get('contentUrl')]
        return image_list[0] if image_list else None
        
    def search_images_google(self, query):
        LOG(f'Google 이미지 검색 시작: {query}')
        api_key = os.getenv('GOOGLE_API_KEY')
        cse_id = os.getenv('GOOGLE_CUSTOM_ENGINE_ID')
        service = build("customsearch", "v1", developerKey=api_key)
        result = service.cse().list(
            q=query,
            cx=cse_id,
            searchType="image",
            num=10
        ).execute()
        images = [item['link'] for item in result.get('items', [])]

        # Instagram, Facebook URL 제외
        filtered_images = [
            url for url in images
            if not ("instagram.com" in url or "facebook.com" in url or "fbsbx" in url)
        ]

        return filtered_images[0] if filtered_images else None 
    