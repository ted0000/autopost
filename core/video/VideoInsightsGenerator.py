import os
import base64
import mimetypes

import google.generativeai as genai
from openai import OpenAI

from config.config import *
from core.video.VideoDownloader import VideoDownloader
from core.video.FrameExtractor import FrameExtractor
from prompt.LoadPrompt import LoadPrompt

class VideoInsightsGenerator():
    def __init__(self):
        pass

    def generate_insights(self, url):
        # Download Video
        dloader = VideoDownloader()
        video_path = dloader.download_vertical_video(url)        
        if not video_path:
            return None
        
        LOG(f'Video Download 완료 : {video_path}')
        self.video_path = video_path
        
        # frame을 나누는 로직
        output_path = os.getenv('VIDEO_FRAME_DIR')
        frame_path = os.getenv('FRAME_FILE')
        fextrator = FrameExtractor(video_path, output_path=output_path, frame_count=9)
        image_path = fextrator.extract_frames(output_path=frame_path)        
        LOG(f'Frame 추출 완료.')
        self.frame_image = image_path

        # frame을 분석하는 로직
        # result = self.analyze_frames_openai(image_path=image_path)
        result = self.analyze_frames_gemini(image_path=image_path)
        LOG(f'Frame 분석 완료.')

        # 더 병맛으로 수정해주는 prompt 추가
        return result
    
    def analyze_frames_openai(self, image_path) -> str:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # 1) 이미지 파일을 base64로 변환
        with open(image_path, "rb") as f:
            image_data = f.read()

        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Prompt 불러오기
        prompt_loader = LoadPrompt("video_insight2.txt")
        prompt = prompt_loader.load()

        response = client.chat.completions.create(
                model="gpt-4o-mini",  # 적절한 모델 선택
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f'data:image/jpeg;base64,{image_base64}',
                                }
                            }
                        ]
                    }
                ]
            )
        result = response.choices[0].message.content.strip()
        return result
    
    def analyze_frames_gemini(self, image_path) -> str:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # 1) 이미지 파일을 base64로 변환
        with open(image_path, "rb") as f:
            image_data = f.read()

        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Gemini가 인식할 수 있도록 이미지 데이터를 dict 형태로 생성
        image_part = {
            "mime_type": mime_type,
            "data": image_base64
        }

        prompt_loader = LoadPrompt("video_insight2.txt")
        prompt = prompt_loader.load()

        # 3) Gemini에 이미지 데이터와 프롬프트 전달
        inputs_for_gemini = [image_part, prompt]

        try:
            response = model.generate_content(inputs_for_gemini)
            result = response.text
            # 코드 펜스 제거
            result = result.replace("```json", "").replace("```", "")
            return result
        except Exception as e:
            return ERROR(f"Error during Gemini call: {e}")
