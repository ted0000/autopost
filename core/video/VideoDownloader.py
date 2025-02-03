import tempfile
import os

from yt_dlp import YoutubeDL

from config.config import *

class VideoDownloader():
    def __init__(self, save_path=""):
        self.save_path = '/Users/1004507/my/autopost/dev/video'
        # self.save_path = save_path
        # self.save_path = self.create_tempDir()
        
    def create_tempDir(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        LOG(f"임시 디렉토리 생성: {self.temp_dir.name}")
        return self.temp_dir
    
    def clean_tempDir(self):
        self.temp_dir.cleanup()
        LOG(f"임시 디렉토리 삭제: {self.temp_dir.name}")

    
    def download_vertical_video(self, url):        
        # Temporary directory
        output_path = os.path.join(self.save_path, "temp_video.mp4")  # Fixed temp file name

        # yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[width<=720][height>=1280]+bestaudio/best',  # Select vertical format with 9:16 ratio
            'outtmpl': output_path,               # Output template
            'merge_output_format': 'mp4',         # Merge video and audio into mp4
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                LOG(f"Video downloaded successfully to: {output_path}")
                return output_path
        except Exception as e:
            ERROR(f"An error occurred while downloading the video: {e}")
            return None