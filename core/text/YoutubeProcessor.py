# Python 표준 라이브러리
import os
import re
import tempfile

# 서드파티 라이브러리
import tiktoken
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

# 로컬 모듈
from config.config import *
from core.text.load_prompt import load_prompt
from .BaseProcessor import BaseProcessor

class YoutubeProcessor(BaseProcessor):
    def get_video_default_language(self, video_id):
        """
        주어진 YouTube 비디오의 기본 언어를 반환합니다.

        Parameters:
        - api_key (str): YouTube API 키
        - video_id (str): YouTube 비디오 ID

        Returns:
        - str: 비디오의 기본 언어 (예: "en", "ko"), 또는 정보가 없을 경우 "정보 없음"
        """
        # YouTube API 클라이언트 설정
        youtube = build("youtube", "v3", developerKey=os.getenv('YOUTUBE_API_KEY'))
        
        # 비디오 정보 가져오기
        response = youtube.videos().list(part="snippet", id=video_id).execute()
        video_info = response['items'][0]['snippet']
        
        # 기본 언어 가져오기
        return video_info.get("defaultAudioLanguage", "ko")
    
    def fetch_youtube_transcript(self):
        def get_video_id(youtube_url):
            # 정규식을 사용하여 유튜브 URL에서 비디오 ID 추출
            pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
            match = re.search(pattern, youtube_url)
            return match.group(1) if match else None
        
        video_id = get_video_id(self.url)
        if not video_id:
            ERROR("Invalid YouTube URL.")
            return None
        
        try:
            # 자막 가져오기 (기본 언어: 'ko')
            lang = self.get_video_default_language(video_id)
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            
            # 임시 파일 생성 및 자막 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_file:
                for entry in transcript:
                    temp_file.write(f"{entry['start']:.2f}s: {entry['text']}\n")
            
            LOG(f"Transcript saved to {temp_file.name}")
            return temp_file.name  # 임시 파일 경로 반환
        
        except Exception as e:
            ERROR("Error downloading transcript:", str(e))
            return None

    def generate_post(self):
        transcript_file = self.fetch_youtube_transcript()
        if not transcript_file:
            ERROR("Transcript 파일 없음.")
            return
        with open(transcript_file, 'r', encoding='utf-8') as temp_file:
            transcript_content = temp_file.read()
        os.remove(transcript_file)

        # 요약하는것은 o1_mini에 query할것
        
        prompt_path = os.path.join(self.root_path, 'prompt', 'article_v2_eng.yaml')
        prompt = load_prompt(prompt_path)
        system_prompt = prompt['system_contents']
        user_prompt = prompt['user_contents'].format(web=transcript_content)
        
        response = self.client.chat.completions.create(
            model=self.model['gpt'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=10000
        )
        # token 계산
        output_tokens = len(tiktoken.encoding_for_model(self.model['gpt']).encode(response.choices[0].message.content.strip()))
        self.token({'input': len(system_prompt + user_prompt), 'output': output_tokens})
        
        return response.choices[0].message.content.strip()