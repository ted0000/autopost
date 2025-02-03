# Python 표준 라이브러리
import os
import re

# 서드파티 라이브러리
import tiktoken
import yaml
from bs4 import BeautifulSoup

# 로컬 모듈
from config.config import *
from core.text.load_prompt import load_prompt
from core.text.WebScrapper import WebScrapper
from .BaseProcessor import BaseProcessor

class TextProcessor(BaseProcessor):
    def __init__(self, root_path, text):
        """
        TextProcessor 초기화.
        :param root_path: 프로젝트(또는 레포) 루트 경로
        :param text: 처리할 텍스트(스크래핑된 웹 텍스트 등)
        """
        super().__init__(root_path=root_path, url=None)
        self.text = text
        self.webscraper = WebScrapper(None)
        # originality가 0이면 contents를 재조정하는 prompt를 사용.
        # originality가 1이면 contents를 그대로 사용.
        self.originality = 1

    def generate_post(self):
        """
        language_model 인자에 따라 gpt 혹은 gemini 로직을 실행합니다.
        """
        if self.originality == 1:
            return self._generate_post_originality()
            
        if LANGUAGE_MODEL=='gpt':
            return self._generate_post_gpt()
        elif LANGUAGE_MODEL == 'gemini':
            return self._generate_post_gemini()

    def _generate_post_originality(self):
        """
        originality가 0이면 contents를 재조정하는 prompt를 사용.
        """
        text_content = self.text

        # 1) Prompt 준비
        prompt_file = 'article_gemini_ko_originality.txt'
        with open(os.path.join(self.root_path, 'prompt', prompt_file), 'r', encoding='utf-8') as f:
            user_prompt = f.read()
            user_prompt = user_prompt.format(web=text_content)
        if not user_prompt:
            ERROR("프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None

        # 2) Gemini API 호출
        LOG('--------------------Gemini API를 사용하여 Post Data를 생성합니다.....')
        response = self.client.generate_content(str(user_prompt))
        LOG('--------------------Gemini API Post Data 생성 완료..')

         # 3) 첫 번째 응답 처리
        data = response.text
        data = self._clean_json_str(data)

        # 6) Image 노드 추가
        LOG('Image Node 처리를 시작합니다...')
        updated_json = self.webscraper.add_image_nodes_to_json(data)

        return updated_json

    # ----------------------------------------------------------------------------
    # 내부 메서드: GPT용
    # ----------------------------------------------------------------------------
    def _generate_post_gpt(self):
        """
        GPT(OpenAI ChatCompletion) 로직을 사용해 포스트를 생성합니다.
        내부적으로 article_v3_o1mini4_only_en.yaml 프롬프트를 사용.
        """
        text_content = self.text

        # 1) Prompt 준비
        prompt_file = 'article_gpt_ko.yaml'
        user_prompt = self._prepare_prompt(prompt_file, text_content)
        if not user_prompt:
            ERROR("프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None

        # 2) Gemini API 호출
        LOG('--------------------OpenAI API를 사용하여 Post Data를 생성합니다.....')
        response = self.client.chat.completions.create(
            model=self.model['gpt'],
            messages=[{"role": "user", "content": user_prompt}]
        )
        LOG('--------------------OpenAI API Post Data 생성 완료..')

        output_text = response.choices[0].message.content.strip()

        # 5) Image 노드 추가
        LOG('Image Node 처리를 시작합니다...')
        updated_json = self.webscraper.add_image_nodes_to_json(output_text)
        
        return updated_json

    # ----------------------------------------------------------------------------
    # 내부 메서드: Gemini용
    # ----------------------------------------------------------------------------
    def _generate_post_gemini(self):
        """
        Gemini API 로직을 사용해 포스트를 생성합니다.
        내부적으로 article_v3_gemini.yaml, tune_gemini.yaml 프롬프트 등을 사용.
        """
        text_content = self.text

        # 1) Prompt 준비 (Gemini 전용 프롬프트)
        prompt_file = 'article_gemini_ko.yaml'
        user_prompt = self._prepare_prompt(prompt_file, text_content)
        if not user_prompt:
            ERROR("프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None

        # 2) Gemini API 호출
        LOG('--------------------Gemini API를 사용하여 Post Data를 생성합니다.....')
        response = self.client.generate_content(str(user_prompt))
        LOG('--------------------Gemini API Post Data 생성 완료..')

        # 3) 첫 번째 응답 처리
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

        # 5) WebScrapper로 콘텐츠 검증
        if not self.webscraper.check_contents(data):
            ERROR('Post 콘텐츠가 카테고리와 다른 내용입니다.')
            return None

        # 6) Image 노드 추가
        LOG('Image Node 처리를 시작합니다...')
        updated_json = self.webscraper.add_image_nodes_to_json(data)

        return updated_json

    # ----------------------------------------------------------------------------
    # 공통 헬퍼 메서드
    # ----------------------------------------------------------------------------
    def _prepare_prompt(self, prompt_file, text_content):
        """
        프롬프트 파일을 로드하고 user_prompt를 생성한 뒤,
        관련 정보를 로그로 출력합니다.
        """
        # LOG(f'Prompt 파일을 로드합니다: {prompt_file}')
        prompt_path = os.path.join(self.root_path, 'prompt', prompt_file)

        try:
            prompt_data = load_prompt(prompt_path)
        except Exception as e:
            ERROR(f'프롬프트 로드 에러: {e}')
            return None

        # YAML -> 스트링 변환 후 토큰 계산
        prompt_str = yaml.dump(prompt_data, allow_unicode=True)
        # LOG(f"Prompt 문자열 길이: {len(prompt_str)}")
        # LOG(f"Prompt 토큰 수: {count_tokens(prompt_str)}")

        # LOG(f"Text Contents 크기: {len(text_content)}")
        # LOG(f"Text Contents 토큰 수: {count_tokens(text_content)}")

        # user_prompt 생성
        # prompt_data 예: { 'user': "Hello {web}" } 형태라고 가정
        user_prompt = prompt_data['user'].format(web=text_content)
        LOG(f"User Prompt 크기: {len(user_prompt)}")
        LOG(f"User Prompt 토큰 수: {count_tokens(user_prompt)}")

        return user_prompt

    def _clean_json_str(self, data_str):
        """
        Gemini 등에서 받은 JSON 형태의 문자열을 정리(clean)합니다.
        """
        # 백틱/마크다운 포맷 ` ```json ... ``` ` 제거
        data_str = re.sub(r'```json|```', '', data_str)
        return data_str