# Python 표준 라이브러리
import base64
import os
import re

# 서드파티 라이브러리
import requests
from colorama import Fore, Style, init
from openai import OpenAI
import google.generativeai as genai

# 로컬 모듈
from config.config import *
from core.text.load_prompt import load_prompt
from core.text.WordpressAPI import WordpressAPI

class BaseProcessor:
    def __init__(self, root_path, url):
        self.root_path = root_path
        self.url = url
        self.model = {
            # 'gpt': 'gpt-4o',
            # 'gpt': 'o1-mini',
            'gpt': 'gpt-4o-mini',
            'gemini': 'gemini-1.5-flash'
        }
        if LANGUAGE_MODEL=='gpt':
            self.mode = self.model['gpt']
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        elif LANGUAGE_MODEL=='gemini':
            self.mode = self.model['gemini']
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.client = genai.GenerativeModel(self.model['gemini'])
        
        self.used_tokens = {
            'input': 0,
            'output': 0
        }
        self.article = None

    def token(self, used_tokens):
        if LANGUAGE_MODEL=='gpt':
            self.used_tokens['input'] += used_tokens['input']
            self.used_tokens['output'] += used_tokens['output']

    def report_tokens(self):
        if LANGUAGE_MODEL=='gpt':
            print(f"{Fore.CYAN}사용된 입력 토큰: {Fore.GREEN}{self.used_tokens['input']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}사용된 출력 토큰: {Fore.GREEN}{self.used_tokens['output']}{Style.RESET_ALL}")

            if self.mode == 'gpt-4o':
                input_cost = (self.used_tokens['input'] * 2.50) / 1_000_000
                output_cost = (self.used_tokens['output'] * 10.00) / 1_000_000
                total_cost_usd = input_cost + output_cost
                total_cost_krw = total_cost_usd * 1400
            elif self.mode == 'gpt-4o-mini':
                input_cost = (self.used_tokens['input'] * 0.15) / 1_000_000
                output_cost = (self.used_tokens['output'] * 0.60) / 1_000_000
                total_cost_usd = input_cost + output_cost
                total_cost_krw = total_cost_usd * 1400
            elif self.mode == 'o1-mini':
                input_cost = (self.used_tokens['input'] * 3.00) / 1_000_000
                output_cost = (self.used_tokens['output'] * 12.00) / 1_000_000
                total_cost_usd = input_cost + output_cost
                total_cost_krw = total_cost_usd * 1400

            print(f"\n{Fore.YELLOW}--- 요금 예측 ---{Style.RESET_ALL}")
            print(f"{Fore.CYAN}예측 요금 (USD): {Fore.MAGENTA}${total_cost_usd:.6f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}예측 요금 (KRW): {Fore.MAGENTA}{total_cost_krw:.2f}원{Style.RESET_ALL}")
    
    def highlight_head(self, text):
        """강조된 텍스트를 HTML <span> 태그로 변환합니다."""
        return re.sub(r'\*\*(.*?)\*\*', r"<span style='font-family: \"Open Sans\", Arial, sans-serif; font-size: 20px; font-weight: bold;'>\1</span>", text)
    
    def highlight_contents(self, text):
        """강조된 텍스트를 HTML <span> 태그로 변환합니다."""
        return re.sub(r'\*\*(.*?)\*\*', r"<span style='color: #FF7F50; font-family: \"Open Sans\", Arial, sans-serif; font-size: 20px; font-weight: bold;'>\1</span>", text)
    
    def json_to_gutenberg_string(self, data, url):
        def remove_unnecessary_tags(text):
            return re.sub(r'\*+', '', text)

        gutenberg_blocks = []
        for subtitle in data['subtitles']:
            gutenberg_blocks.append(
                f'<!-- wp:heading {{"level":2}} -->\n'
                f'<h2 class="wp-block-heading">{self.highlight_head(subtitle["subtitle"])}</h2>\n'
                f'<!-- /wp:heading -->'
            )
            if subtitle.get('image'):
                gutenberg_blocks.append(
                    f'<!-- wp:image -->\n'
                    f'<figure class="wp-block-image"><img src="{subtitle["image"]}" alt="{remove_unnecessary_tags(subtitle["subtitle"])}" /></figure>\n'
                    f'<!-- /wp:image -->'
                )
            gutenberg_blocks.append(
                f'<!-- wp:paragraph -->\n'
                f'<p>{self.highlight_contents(subtitle["content"])}</p>\n'
                f'<!-- /wp:paragraph -->'
            )
            if subtitle.get('quote'):
                gutenberg_blocks.append(
                    f'<!-- wp:quote -->\n'
                    f'<blockquote class="wp-block-quote"><p>{subtitle["quote"]}</p></blockquote>\n'
                    f'<!-- /wp:quote -->'
                )
            if subtitle.get('code'):
                gutenberg_blocks.append(
                    f'<!-- wp:code -->\n'
                    f'<pre class="wp-block-code"><code>{subtitle["code"]}</code></pre>\n'
                    f'<!-- /wp:code -->'
                )
        # gutenberg_blocks.append(
        #     f'<!-- wp:heading {{"level":2}} -->\n'
        #     f'<h2 class="wp-block-heading">Wrap-Up</h2>\n'
        #     f'<!-- /wp:heading -->'
        # )
        gutenberg_blocks.append(
            f'<!-- wp:paragraph -->\n'
            f'<p>{self.highlight_head(data["conclusion"])}</p>\n'
            f'<!-- /wp:paragraph -->'
        )
        # if url is not none
        # if url:
        #     gutenberg_blocks.append(
        #         f'<!-- wp:paragraph -->\n'
        #         f'<p><strong>Source:</strong> <a href="{url}" target="_blank">{url}</a></p>\n'
        #         f'<!-- /wp:paragraph -->'
        #     )
        return "\n".join(gutenberg_blocks)
    
    def get_image_urls_with_openai(self, html, json_data):
        """
        OpenAI API를 사용하여 HTML과 JSON 데이터를 기반으로 이미지 URL을 생성합니다.
        """
        try:
            prompt_path = os.path.join(self.root_path, 'prompt', 'image_eng.yaml')
            prompt = load_prompt(prompt_path)

            system_prompt = prompt['system_contents']
            user_prompt = prompt['user_contents'].format(html=html[:10000], json=json_data)

            response = self.client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # 창의성 조절 (0.0은 매우 보수적, 1.0은 매우 창의적)
                max_tokens=10000   # 출력될 텍스트의 최대 토큰 수 (토큰 수에 따라 응답 길이 제한)
            )
            
            updated_json = response.choices[0].message.content.strip()
            return updated_json
        except Exception as e:
            raise Exception(f"Error using OpenAI API: {e}")

    # def post(self, title, category_id, post_content, featured_image_id):
    def post(self, lang, post_content, gutenberg_formmatted, featured_image_id):
        api = WordpressAPI()
        api.post(post_content, gutenberg_formmatted, featured_image_id)

    def post_(self, lang, post_content, gutenberg_formmatted, featured_image_id):
        # WordPress 인증 정보 설정
        LOG(f'{lang.upper()} - Post를 생성합니다.')
        auth_username = os.getenv('WORDPRESS_SITE_USERNAME')
        auth_password = os.getenv('WORDPRESS_SITE_PASSWORD')
        auth_string = f"{auth_username}:{auth_password}".encode('utf-8')
        auth_base64 = base64.b64encode(auth_string).decode('utf-8')
        site_url = os.getenv(f'WORDPRESS_SITE_URL_{lang.upper()}')
        LOG(f'Site URL : {site_url}에 Post를 전송합니다.')

        # 헤더 설정
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/json"
        }

        tags = post_content.get('tags', None)
        LOG(f'{lang.upper()} - 포스트 태그: {tags}')

        # 포스트 데이터 초기화
        post_data = {
            "title": post_content['title'],
            "content": gutenberg_formmatted,
            "status": "draft",
            "categories": CATEGORY[post_content['category']]
        }

        # 메타 데이터 추출 및 추가
        meta = post_content.get('meta', None)
        if meta:
            focus_kw = meta.get('_yoast_wpseo_focuskw', None)
            meta_desc = meta.get('_yoast_wpseo_metadesc', None)
            seo_title = meta.get('_yoast_wpseo_title', None)
            og_title = meta.get('og_title', None)
            og_desc = meta.get('og_description', None)
            og_image = meta.get('og_image', None)

            # 'meta'와 'yoast_head_json' 섹션 추가
            post_data["meta"] = {}
            if focus_kw:
                post_data["meta"]["_yoast_wpseo_focuskw"] = focus_kw
            if meta_desc:
                post_data["meta"]["_yoast_wpseo_metadesc"] = meta_desc
            if seo_title:
                post_data["meta"]["_yoast_wpseo_title"] = seo_title

            # Open Graph 메타 데이터 추가
            if og_title:
                post_data["meta"]["og_title"] = og_title
            if og_desc:
                post_data["meta"]["og_description"] = og_desc
            if og_image:
                post_data["meta"]["og_image"] = og_image

        # 특성이미지 설정
        if featured_image_id:
            post_data['featured_media'] = featured_image_id

        # 포스트 생성 API URL
        api_url = f"{site_url}/wp-json/wp/v2/posts"

        response = requests.post(api_url, json=post_data, headers=headers)
        if response.status_code == 201:
            LOG(f"{lang.upper()} - 포스트가 성공적으로 생성되었습니다.")
        else:
            LOG(f"{lang.upper()} - 포스트 생성에 실패했습니다. 상태 코드: {response.status_code}")
            # LOG(f"응답: {response.json()}")
