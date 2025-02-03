import argparse
from dotenv import load_dotenv
import os
import requests

from config.config import *

# .env 파일 로드
load_dotenv()

def bing_news_search(query, endpoint, api_key, num=10):
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    all_urls = []
    markets = ['en-US', 'ja-JP']

    for market in markets:
        params = {
            'q': query,
            'textDecorations': True,
            'textFormat': 'HTML',
            'category': 'Entertainment',
            'freshness': 'Week',
            'count': num,
            'sortBy': 'Relevance',
            'mkt': market
        }
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        all_urls.extend([d.get('url', '') for d in data.get('value', [])])

        # 중복 URL 제거
        all_urls = list(set(all_urls))
    
    return all_urls

def is_excluded_domain(url):
    return any(domain.lower() in url.lower() for domain in EXCLUDE_DOMAIN)

def main():
    endpoint = os.getenv('BING_NEWS_SEARCH_API_ENTPOINT')
    subscription_key = os.getenv('BING_SEARCH_API_KEY')

    query = '''
    kpop news, korean idol news, kpop star news
    '''

    urls = bing_news_search(query, endpoint, subscription_key)

    current = os.getcwd()
    file_path = os.path.join(current, "script", "urls.txt")
    print(file_path)

    with open(file_path, "w") as file:
        for url in urls:
            if is_excluded_domain(url):
                continue
            file.write(url + "\n")

if __name__ == "__main__":
    main()
    