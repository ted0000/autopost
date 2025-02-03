# Python 표준 라이브러리
import argparse
import json
import os

# 서드파티 라이브러리
from dotenv import load_dotenv

# 프로젝트 로컬 모듈
from config.config import *
from core.text.ArticleProcessor import ArticleProcessor
from core.text.YoutubeProcessor import YoutubeProcessor
from core.text.TextProcessor import TextProcessor


# .env 파일 로드
load_dotenv(override=True)

def setup_processor(url, processor_type, text=None):
    """
    Processor 인스턴스를 초기화하는 함수입니다.
    processor_type에 따라 ArticleProcessor 또는 YoutubeProcessor를 반환합니다.
    """

    root_path = os.path.dirname(os.path.abspath(__file__))
    
    if processor_type == "article":
        return ArticleProcessor(root_path, url)
    elif processor_type == "youtube":
        return YoutubeProcessor(root_path, url)
    elif processor_type == "text":
        return TextProcessor(root_path, text)
    else:
        raise ValueError("Invalid processor type. Must be 'article' or 'youtube'.")
    return


def process_content(processor, url, text, output_filename):
    """
    공통 처리 작업을 수행하는 함수입니다. Processor를 사용하여 포스트 내용을 생성하고,
    카테고리 분류, 파일 저장, 포스팅, 토큰 보고를 처리합니다.
    """
    try:
        # Generate post content
        # 전체 작업 단계 정의
        LOG("")
        LOG("====================================================")
        LOG(f'Autopost 작업을 시작합니다.')
        LOG("====================================================")
        LOG("")

        post_content = processor.generate_post()
        
        # Save post content to json
        with open(f"dev/{output_filename}", "w", encoding="utf-8") as file:
            json.dump(post_content, file, ensure_ascii=False, indent=4)
        
        if type(post_content) is str:
            post_content = json.loads(post_content)

        if post_content.get('en', None):
            # multi language
            for key, value in post_content.items():
                reformat_contents = processor.json_to_gutenberg_string(value, url)
                with open(f"dev/output_gutenberg_{output_filename}_{key}", "w", encoding="utf-8") as file:
                    file.write(reformat_contents)
                
                featured_image_id = value.get('image', None)

                processor.post(key, value,
                            reformat_contents, 
                            featured_image_id)
        else:
            # only english
            reformat_contents = processor.json_to_gutenberg_string(post_content, url)
            with open(f"dev/output_gutenberg_{output_filename}_en", "w", encoding="utf-8") as file:
                file.write(reformat_contents)
            
            featured_image_id = post_content.get('image', None)

            processor.post('en', post_content,
                        reformat_contents, 
                        featured_image_id)
            
        # Report token usage
        processor.report_tokens()
    except Exception as e:
        ERROR(f"처리 중 오류 발생: {e}")
        # 상세 오류 정보 출력 (선택 사항)
        import traceback
        traceback.print_exc()
        raise  # 예외를 다시 발생시켜 상위 호출자에게 전달
    return

def is_excluded_domain(url):
    return any(domain.lower() in url.lower() for domain in EXCLUDE_DOMAIN)

def process_pages_url(url):
    """
    웹 페이지 URL을 처리하는 함수. ArticleProcessor를 사용하여 처리.
    """
    if is_excluded_domain(url):
        ERROR(f"URL '{url}'의 콘텐츠는 처리할 수 없습니다.")
        return
    
    processor = setup_processor(url, processor_type="article")
    process_content(processor=processor, 
                    url=url, 
                    text=None,
                    output_filename = "output_web.json")
    return


def process_youtube_url(url):
    """
    유튜브 URL을 처리하는 함수. YoutubeProcessor를 사용하여 처리.
    """
    processor = setup_processor(url, processor_type="youtube")
    process_content(processor=processor, 
                    url=url, 
                    text=None,
                    output_filename = "output_youtube.txt")
    return
    
def process_text(textfile):
    try:
        with open(textfile, "r", encoding="utf-8") as f:
            # read file and save contents
            text = f.read()
        processor = setup_processor(url=None, processor_type='text', text=text)
        process_content(processor=processor, url=None, text=text, output_filename='output_text.txt')
        return
        
    except FileNotFoundError:
        ERROR(f"The file '{textfile}' was not found.")
        return None

def main_url(url):
    if "youtube.com/watch" in url or "youtu.be/" in url:
        process_youtube_url(url)
    else:
        process_pages_url(url)


def process_urls_from_file(file):
    """
    파일에서 URL 목록을 읽어 각각의 URL을 처리합니다.
    모든 URL이 처리된 후 파일의 내용을 삭제합니다.
    """
    with open(file, "r") as f:
        urls = [url.strip() for url in f.readlines()]
    
    for url in urls:
        main_url(url)
    
    # 파일 내용 초기화
    with open(file, "w") as f:
        f.write("")       


def process_single_url(url):
    """
    단일 URL을 처리합니다.
    """
    main_url(url)


def main(args):
    """
    입력된 파일이나 URL을 기반으로 작업을 수행합니다.
    """
    if args.file:
        process_urls_from_file(args.file)
    elif args.url:
        process_single_url(args.url)
    elif args.txt:
        process_text(args.txt)
    else:
        print("No URL provided. Please provide a valid URL using --url.")
        # URL이 없는 경우 추가 처리 로직을 여기에 추가할 수 있습니다.


if __name__ == "__main__":
    # ArgumentParser를 사용하여 커맨드라인 인자 받아오기
    parser = argparse.ArgumentParser(description="Process a URL or a file with URLs.")
    parser.add_argument("--url", required=False, help="The URL to process")
    parser.add_argument("--file", required=False, help="File containing a list of URLs to process")
    parser.add_argument("--txt", required=False, help="contents file")
        
    args = parser.parse_args()
    
    # main 함수 호출
    main(args)
    