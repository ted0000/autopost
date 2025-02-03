# Python 표준 라이브러리
import os

# 서드파티 라이브러리
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI

# 로컬 모듈
from config.config import *
from core.text.load_prompt import load_prompt

# .env 파일 로드
load_dotenv()

class GenImagePrompt():
    def __init__(self, root_path, url):
        self.root_path = root_path
        self.url = url
        self.model = {
            'gpt': 'gpt-4o',
            'gemini': 'gemini-pro'
        }
        self.mode = self.model['gemini']
        self.client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.client_gemini = genai.GenerativeModel(self.model['gemini'])
        
    def fetch_content(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text(separator='\n', strip=True)
            return text_content
        else:
            raise ValueError(f"Failed to retrieve content. Status code: {response.status_code}")
        
    def gen_prompt_gpt(self, text_content):
        # Object Prompt
        object_prompt_path = os.path.join(self.root_path, 'prompt', 'object.yaml')
        object_prompt = load_prompt(object_prompt_path)

        system_prompt = object_prompt['system_contents']
        user_prompt = object_prompt['user_contents'].format(contents=text_content)
        
        response = self.client_openai.chat.completions.create(
            model=self.model['gpt'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=10000
        )
        
        object_text = response.choices[0].message.content.strip()
        
        # create image generation prompt
        image_prompt_path = os.path.join(self.root_path, 'prompt', 'image_prompt.yaml')
        image_prompt = load_prompt(image_prompt_path)
        
        system_prompt = image_prompt['system_contents']
        user_prompt = image_prompt['user_contents'].format(object=object_text, contents=object_text)
        response = self.client_openai.chat.completions.create(
            model=self.model['gpt'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=10000
        )
        
        return response.choices[0].message.content.strip()        
    
    def gen_prompt_gemini(self, text_content):
        prompt_path = os.path.join(self.root_path, 'prompt', 'image_prompt_gemini.yaml')
        prompt = load_prompt(prompt_path)
        prompt = prompt['prompt'].format(contents=text_content)
        
        LOG(f"Prompt: {prompt}")
        
        response = self.client_gemini.generate_content(prompt)
        return response.text
        
    def generate_prompt(self):
        text_content = self.fetch_content()        
        # add try catch block
        try:
            if self.mode == self.model['gpt']:
                res = self.gen_prompt_gpt(text_content)
            elif self.mode == self.model['gemini']:
                res = self.gen_prompt_gemini(text_content)
                
            # save to file
            prompt_path = os.path.join(self.root_path, 'dev', 'image_gen_prompt.txt')
            with open(prompt_path, "w", encoding="utf-8") as file:
                file.write(res)
            
        except Exception as e:
            ERROR(f"generate_prompt Error: {e}")
            return None
