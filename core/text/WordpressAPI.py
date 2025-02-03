# Python 표준 라이브러리
import os

# 서드파티 라이브러리
import requests

# 로컬 모듈
from config.config import *

class WordpressAPI():
    def __init__(self):
        self.token = self.getToken()
        self.site_id = os.getenv('WORDPRESS_SITE_ID')

    def getToken(self):
        client_id = os.getenv('WORDPRESS_OAUTH_CLIENT_ID')
        client_secret = os.getenv('WORDPRESS_OAUTH_CLIENT_SECRET')
        username = os.getenv('WORDPRESS_OAUTH_USERNAME')
        app_password = os.getenv('WORDPRESS_OAUTH_APP_PASSWORD')
        oauth_endpoint = os.getenv('WORDPRESS_OAUTH_ENDPOINT')

        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': username,
            'password': app_password
        }
        response = requests.post(oauth_endpoint, data=payload)
        response.raise_for_status()
    
        # 응답 JSON 파싱
        auth = response.json()
        access_token = auth.get('access_token', None)
        if not access_token:
            ERROR('액세스 토큰을 찾을 수 없습니다.')
            ERROR('응답 내용:', auth)
        return access_token
    
    def media_upload(self, file_path, alt_text):
        endpoint = f'https://public-api.wordpress.com/rest/v1.1/sites/{self.site_id}/media/new'

        if not self.token:
            ERROR('액세스 토큰이 없습니다.')
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            files = {'media': open(file_path, 'rb')}
            
            response = requests.post(endpoint, headers=headers, files=files)
            response.raise_for_status()
            result = response.json()
            media = result.get('media', None)
            if media:
                LOG(f'미디어 업로드 완료')
                media_id = media[0].get('ID', None)
            else:
                ERROR(f'미디어 업로드 실패: {result}')
                return None
            
            edit_url = f'https://public-api.wordpress.com/rest/v1.1/sites/{self.site_id}/media/{media_id}/edit'
            edit_data = {
                'alt': alt_text,
                'caption': alt_text,
                'description': alt_text
            }
            edit_header = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            edit_response = requests.post(edit_url, headers=edit_header, json=edit_data)
            edit_response.raise_for_status()
            LOG(f'미디어 속성 수정')
            return media_id

        except requests.exceptions.RequestException as e:
            ERROR(f'미디어 업로드 중 오류 발생: {e}')
            return None
        
    def post(self, post_content, gutenberg_formmatted, featured_image_id):
        LOG(f'Post를 생성합니다.')
        endpoint = f'https://public-api.wordpress.com/rest/v1.1/sites/{self.site_id}/posts/new'

        if not self.token:
            ERROR('액세스 토큰이 없습니다.')
            return None

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        tags = post_content.get('tags', None)
        LOG('====================================================')
        LOG(f'포스트 태그')
        LOG(tags)
        LOG('====================================================')

        # 포스트 데이터 초기화
        post_data = {
            "title": post_content['title'],
            "content": gutenberg_formmatted,
            "status": "draft",
            "categories": CATEGORY[post_content['category']]
        }

        meta = post_content.get('meta', None)
        if meta:
            focus_kw = meta.get('_yoast_wpseo_focuskw', None)
            meta_desc = meta.get('_yoast_wpseo_metadesc', None)
            seo_title = meta.get('_yoast_wpseo_title', None)
            # og_title = meta.get('og_title', None)
            # og_desc = meta.get('og_description', None)
            # og_image = meta.get('og_image', None)
            LOG('')
            LOG(f"Focus KW : {focus_kw}")
            LOG(f"SEO Title : {seo_title}")
            LOG(f"SEO 요약글 : {meta_desc}")
            LOG('')
            # LOG(f"SEO og_title : {og_title}")
            # LOG(f"SEO og_desc : {og_desc}")

            # 'meta'와 'yoast_head_json' 섹션 추가
            # post_data["metadata"] = {}
            # if focus_kw:
            #     post_data["metadata"]["_yoast_wpseo_focuskw"] = focus_kw
            # if seo_title:
            #     post_data["metadata"]["_yoast_wpseo_title"] = seo_title
            # if meta_desc:
            #     post_data["metadata"]["_yoast_wpseo_metadesc"] = meta_desc
            #     # post_data["metadata"]["_jetpack_post_excerpt"] = meta_desc

            # # Open Graph 메타 데이터 추가
            # if og_title:
            #     post_data["metadata"]["_yoast_wpseo_opengraph-title"] = og_title
            # if og_desc:
            #     post_data["metadata"]["_yoast_wpseo_opengraph-description"] = og_desc
            # if og_image:
            #     post_data["metadata"]["_yoast_wpseo_opengraph-image"] = og_image

        # 특성이미지 설정
        if featured_image_id:
            post_data['featured_media'] = featured_image_id
            post_data['featured_image'] = featured_image_id
            
        response = requests.post(endpoint, json=post_data, headers=headers)
        if response.status_code == 200:
            LOG(f"포스트가 성공적으로 생성되었습니다.")
        else:
            LOG(f"포스트 생성에 실패했습니다. 상태 코드: {response.status_code}")
