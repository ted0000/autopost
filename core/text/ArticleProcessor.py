# Python 표준 라이브러리
import os
import re

# 서드파티 라이브러리
import tiktoken
import yaml

# 로컬 모듈
from config.config import *
from core.text.load_prompt import load_prompt
from core.text.WebScrapper import WebScrapper
from .BaseProcessor import BaseProcessor

class ArticleProcessor(BaseProcessor):
    def __init__(self, root_path, url):
        """
        ArticleProcessor 초기화
        :param root_path: 루트 경로
        :param url: 스크래핑 대상 URL
        """
        super().__init__(root_path=root_path, url=url)
        self.webscraper = WebScrapper(self.url)

    # ----------------------------------------------------------------------------
    # Public Method (외부에서는 이 메서드만 호출)
    # ----------------------------------------------------------------------------
    def generate_post(self):
        """
        외부에서 단 한 번의 호출로, 원하는 language_model에 맞춰
        게시글 생성 로직을 실행합니다.

        :param language_model: 'o1mini', 'gemini', 'gpt4o' 등
        :return: 최종 JSON (이미지 노드 삽입 포함) 또는 None
        """
        # 1) 기사(articles) 스크래핑
        articles = self._get_article_content()
        if not articles:
            return None

        # 2) language_model 분기 처리
        if LANGUAGE_MODEL=='gpt':
            return self._generate_post_gpt(articles)
        elif LANGUAGE_MODEL == 'gemini':
            return self._generate_post_gemini(articles)

    # ----------------------------------------------------------------------------
    # Private Methods (내부에서만 호출)
    # ----------------------------------------------------------------------------

    def _generate_post_gpt(self, articles):
        """
        1) article_v3_o1mini4_only_en.yaml 프롬프트 로드
        2) GPT(OpenAI)로 콘텐츠 생성
        3) JSON + 이미지 노드 삽입
        """
        prompt_file = 'article_gpt.yaml'
        user_prompt = self._prepare_prompt(prompt_file, articles.prettify())
        if not user_prompt:
            return None

        # GPT 호출
        LOG('--------------------OpenAI API를 사용하여 Post Data를 생성합니다.....')
        response = self.client.chat.completions.create(
            model=self.model['gpt'],
            messages=[{"role": "user", "content": user_prompt}]
        )
        LOG('--------------------OpenAI API Post Data 생성 완료..')
        
        # 3) 토큰 계산
        output_text = response.choices[0].message.content.strip()
        output_tokens = len(tiktoken.encoding_for_model(self.model['gpt']).encode(output_text))
        self.token({'input': len(user_prompt), 'output': output_tokens})

        # # 4) SEO Tune 실행
        # prompt_file = 'tune_gpt.yaml'
        # user_prompt = self._prepare_prompt(prompt_file, output_text)
        # if not user_prompt:
        #     ERROR("프롬프트 준비 과정에서 오류가 발생했습니다.")
        #     return None
        
        # LOG('OpenAI API를 사용하여 SEO Tune을 실행합니다.....')
        # response = self.client.chat.completions.create(
        #     model=self.model['gpt'],
        #     messages=[{"role": "user", "content": user_prompt}]
        # )
        # LOG('SEO Tune완료')

        # 콘텐트 검증
        if not self.webscraper.check_contents(output_text):
            ERROR('Post 콘텐츠가 카테고리와 다른 내용입니다.')
            return None

        # 이미지 노드 삽입
        updated_json = self.webscraper.add_image_nodes_to_json(output_text)
        return updated_json

    def _generate_post_gemini(self, articles):
        """
        1) article_v3_o1mini4_only_en.yaml 프롬프트 로드
        2) Gemini API로 콘텐츠 생성
        3) JSON + 이미지 노드 삽입
        """
        prompt_file = 'article_gemini.yaml'
        user_prompt = self._prepare_prompt(prompt_file, articles.prettify())
        if not user_prompt:
            return None

        LOG('--------------------Gemini API를 사용하여 Post Data를 생성합니다.....')
        response = self.client.generate_content(str(user_prompt))
        LOG('--------------------Gemini API Data 생성 완료..')

        data = response.text
        data = self._clean_json_str(data)

        # 4) 두 번째 프롬프트(tune_gemini.yaml) 적용 (옵션)
        LOG('--------------------Gemini API를 사용하여 SEO Tune을 실행합니다.....')
        tune_prompt_file = 'tune_gemini.yaml'
        tune_prompt = self._prepare_prompt(tune_prompt_file, data)
        if tune_prompt:
            response_tuned = self.client.generate_content(str(tune_prompt))
            data = self._clean_json_str(response_tuned.text)
        LOG('--------------------SEO Tune완료')

        # 콘텐트 검증
        if not self.webscraper.check_contents(data):
            ERROR('Post 콘텐츠가 카테고리와 다른 내용입니다.')
            return None

        updated_json = self.webscraper.add_image_nodes_to_json(data)
        return updated_json

    # ----------------------------------------------------------------------------
    # 헬퍼 메서드
    # ----------------------------------------------------------------------------
    def _get_article_content(self):
        """
        WebScrapper로 기사 내용(articles)을 가져온 뒤 반환.
        찾지 못하면 None 반환
        """
        articles = self.webscraper.find_article()
        if not articles:
            ERROR("스크래핑할 기사가 없습니다.")
            return None
        return articles

    def _prepare_prompt(self, prompt_file, article_str):
        """
        단순 user prompt 구조의 YAML을 로드해 user_prompt를 생성.
        (예: prompt['user'].format(web=...))
        """
        LOG(f'Prompt 파일을 로드합니다. file : {prompt_file}')
        prompt_path = os.path.join(self.root_path, 'prompt', prompt_file)
        
        try:
            prompt_data = load_prompt(prompt_path)
        except Exception as e:
            ERROR(f"프롬프트 로드 에러: {e}")
            return None

        # Prompt 로깅
        prompt_str = yaml.dump(prompt_data, allow_unicode=True)
        # LOG(f"Prompt 문자열 길이: {len(prompt_str)}")
        # LOG(f"Prompt 토큰 수: {count_tokens(prompt_str)}")

        # LOG(f"WebContents 크기 : {len(article_str)}")
        # LOG(f"WebContents 토큰 수: {count_tokens(article_str)}")

        # user prompt 생성
        user_prompt = prompt_data['user'].format(web=article_str)
        LOG(f"User Prompt 크기 : {len(user_prompt)}")
        # LOG(f"User Prompt 토큰 수: {count_tokens(user_prompt)}")

        return user_prompt

    def _prepare_prompt_for_system(self, prompt_file, article_str):
        """
        system_prompt + user_prompt 구조의 YAML 로드
        (예: prompt['system_contents'], prompt['user_contents'] 사용)
        """
        LOG(f'Prompt 파일을 로드합니다. file : {prompt_file}')
        prompt_path = os.path.join(self.root_path, 'prompt', prompt_file)

        try:
            prompt_data = load_prompt(prompt_path)
        except Exception as e:
            ERROR(f"프롬프트 로드 에러: {e}")
            return None, None

        system_prompt = prompt_data.get('system_contents', '')
        user_prompt   = prompt_data.get('user_contents', '').format(web=article_str)

        # 로깅
        prompt_str = yaml.dump(prompt_data, allow_unicode=True)
        LOG(f"Prompt 문자열 길이: {len(prompt_str)}")
        LOG(f"Prompt 토큰 수: {count_tokens(prompt_str)}")

        LOG(f"WebContents 크기 : {len(article_str)}")
        LOG(f"WebContents 토큰 수: {count_tokens(article_str)}")

        LOG(f"System Prompt 크기 : {len(system_prompt)}")
        LOG(f"User Prompt 크기 : {len(user_prompt)}")

        return system_prompt, user_prompt

    def _call_openai_gpt(self, user_prompt, model_name):
        """
        OpenAI GPT API 호출 로직 (system prompt 없이 user만)
        호출 후 결과 문자열을 반환
        """
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": user_prompt}]
        )

        output_text = response.choices[0].message.content.strip()

        # 토큰 계산
        output_tokens = len(tiktoken.encoding_for_model(model_name).encode(output_text))
        self.token({'input': len(user_prompt), 'output': output_tokens})

        LOG('OpenAI API Data 생성 완료..')
        return output_text
    
    def _clean_json_str(self, data_str):
        """
        Gemini 등에서 받은 JSON 형태의 문자열을 정리(clean)합니다.
        """
        # 백틱/마크다운 포맷 ` ```json ... ``` ` 제거
        data_str = re.sub(r'```json|```', '', data_str)
        return data_str