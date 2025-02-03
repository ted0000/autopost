import os
import cv2
import math

from PIL import Image

from config.config import *

class FrameExtractor:
    def __init__(self, video_path, output_path, frame_count=5):
        self.video_path = video_path
        self.output_path = output_path
        self.frame_count = frame_count

        self.clean_output()

    def clean_output(self):
        if os.path.exists(self.output_path):
            for file in os.listdir(self.output_path):
                os.remove(os.path.join(self.output_path, file))

    def extract_frames(self, output_path='combined_image.jpg', frame_count=9):
        frames = self._extract_frames(frame_count=frame_count)
        self.combine_images(frames, output_path)
        return output_path
        
    def _extract_frames(self, frame_count=9):
        os.makedirs(self.output_path, exist_ok=True)

        video = cv2.VideoCapture(self.video_path)

        # Get total frames and FPS
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)  # Frames per second
        duration = total_frames / fps  # Total duration in seconds

        frame_count = int(min(frame_count, duration))

        # Calculate the intervals at which frames should be extracted
        interval = duration / (self.frame_count + 1)  # Spread frames evenly

        extracted_frames = []
        for i in range(1, self.frame_count + 1):
            target_time = int(i * interval)  # Target time in seconds
            target_frame = int(target_time * fps)  # Convert time to frame index

            # Set the video to the target frame
            video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            success, frame = video.read()
            if success:
                frame_path = os.path.join(self.output_path, f"frame_{target_time}.jpg")
                cv2.imwrite(frame_path, frame)
                extracted_frames.append(frame_path)

        video.release()
        return sorted(extracted_frames)
    
    def combine_images(self, frames, output_path='combined_image.jpg'):
        # 이미지 열기
        images = [Image.open(frame) for frame in frames]

        # 각 이미지의 크기 가져오기 (모든 이미지가 동일한 크기라고 가정)
        img_width, img_height = images[0].size

        # 이미지 개수에 따른 그리드 크기 계산
        num_images = len(images)
        grid_cols = math.ceil(math.sqrt(num_images))
        grid_rows = math.ceil(num_images / grid_cols)

        # 출력 이미지의 크기 계산
        combined_width = grid_cols * img_width
        combined_height = grid_rows * img_height

        # 빈 출력 이미지 생성
        combined_image = Image.new('RGB', (combined_width, combined_height), (255, 255, 255))

        # 이미지들을 그리드에 배치
        for index, image in enumerate(images):
            row = index // grid_cols
            col = index % grid_cols
            x = col * img_width
            y = row * img_height
            combined_image.paste(image, (x, y))

        # 결과 이미지 저장
        combined_image.save(output_path)
        # LOG(f'이미지가 성공적으로 저장되었습니다: {output_path}')
