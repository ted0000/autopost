import yaml
import os
import sys

# 루트 디렉토리 경로를 가져옴
root_path = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(root_path, 'prompt')

# 경로 추가
sys.path.append(root_path)
sys.path.append(prompt_path)

# load prompt function 작성
def load_prompt(prompt_file):
    # YAML 파일 읽기
    with open(prompt_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # prompt 내용 반환
    return data