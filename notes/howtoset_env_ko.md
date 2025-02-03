# Open AI API
openai의 api는 https://openai.com/index/openai-api/ 를 참고하기 바란다.
Ref : https://velog.io/@ji1kang/OpenAI%EC%9D%98-API-Key-%EB%B0%9C%EA%B8%89-%EB%B0%9B%EA%B3%A0-%ED%85%8C%EC%8A%A4%ED%8A%B8-%ED%95%98%EA%B8%B0

# Gemini AI API
https://ai.google.dev/gemini-api/docs/api-key?hl=ko

# Wordpress (비지니스 요금제 이상)
1. WORDPRESS_SITE_URL_EN : Wordpress 사이트의 url을 말함. ex) https://klutz91.com
현재 이 프로젝트의 모든 코드는 wordpress.com에서 Hosting하는 블로그를 대상으로 설정되었음.
일반 wordpress hosting을 사용하는 경우에는 oauth를 사용하지 않고 login이 가능하다.
2. WORDPRESS_SITE_USERNAME
사용자의 wordpress.com의 username을 말함. 일반적으로 wordpress.com의 login name을 말함.
3. WORDPRESS_OAUTH_ENDPOINT
python client로 wordpress.com의 api에 접근하기 위해 먼저 oauth 처리를 해야함. 이때 접근해야할 endpoint임.
4. WORDPRESS_OAUTH_CLIENT_ID
5. WORDPRESS_OAUTH_CLIENT_SECRET
[Wordpress Developer Apps Page](https://wordpress.com/log-in?redirect_to=https%3A%2F%2Fdeveloper.wordpress.com%2Fapps%2F)로 이동한다.
여기서 login을 한후 페이지에 들어가면 Create New Application이 있다.
여기서 Application을 만들면 Client ID, Secret이 나온다.
6. WORDPRESS_OAUTH_USERNAME
7. WORDPRESS_OAUTH_APP_PASSWORD
[Wordpress Developers page](https://developer.wordpress.com/docs/oauth2/) 참고
8. WORDPRESS_SITE_ID
```shell
curl https://public-api.wordpress.com/rest/v1.1/sites/klutz91.com
```
이에 대한 응답은 다음과 같다.
```json
{
    "ID":238103852,
    "name":"Klutz Kulture",
    "description":"Where K-Culture Comes Alive",
    ...
```
# Search Engine
1. GOOGLE_CUSTOM_ENGINE_ID : https://programmablesearchengine.google.com/about/ 
2. YOUTUBE_API_KEY : Youtube 영상에서 블로그 내용을 만들기위해 자막 다운로드 할때 사용함.
https://console.cloud.google.com/apis 에서 라이브러리에서 찾을수 있다.
3. BING_SEARCH_API_ENDPOINT : google custom engine 보다 azure engine을 쓰는게 더 결과가 잘나와서 추가.