# Open AI API
For information on the OpenAI API, please refer to [OpenAI API](https://openai.com/index/openai-api/).  
Reference: [How to Get and Test OpenAI API Key](https://velog.io/@ji1kang/OpenAI%EC%9D%98-API-Key-%EB%B0%9C%EA%B8%89-%EB%B0%9B%EA%B3%A0-%ED%85%8E%EC%8A%A4%ED%8A%B8-%ED%95%98%EA%B8%B0)

# Gemini AI API
For details on the Gemini API, please visit: [Gemini API Documentation](https://ai.google.dev/gemini-api/docs/api-key?hl=ko).

# WordPress (Business Plan or Higher)
1. **WORDPRESS_SITE_URL_EN**:  
   This refers to the URL of your WordPress site (e.g., `https://klutz91.com`).  
   Note: The current code in this project is configured to target a blog hosted on wordpress.com.  
   If you are using standard WordPress hosting, you can log in without using OAuth.

2. **WORDPRESS_SITE_USERNAME**:  
   This is your WordPress.com username, typically the same as your login name on wordpress.com.

3. **WORDPRESS_OAUTH_ENDPOINT**:  
   This is the endpoint that must be accessed for OAuth authentication with the WordPress.com API using a Python client.

4. **WORDPRESS_OAUTH_CLIENT_ID**

5. **WORDPRESS_OAUTH_CLIENT_SECRET**:  
   To obtain these credentials, go to the [WordPress Developer Apps Page](https://wordpress.com/log-in?redirect_to=https%3A%2F%2Fdeveloper.wordpress.com%2Fapps%2F).  
   After logging in, click on "Create New Application" to generate your Client ID and Client Secret.

6. **WORDPRESS_OAUTH_USERNAME**

7. **WORDPRESS_OAUTH_APP_PASSWORD**:  
   For more details, please refer to the [WordPress Developers page](https://developer.wordpress.com/docs/oauth2/).

8. **WORDPRESS_SITE_ID**:  
   To retrieve your site ID, execute the following command:
```shell
curl https://public-api.wordpress.com/rest/v1.1/sites/klutz91.com
```
response will be
```json
{
    "ID":238103852,
    "name":"Klutz Kulture",
    "description":"Where K-Culture Comes Alive",
    ...
```

# Search Engine
1. GOOGLE_CUSTOM_ENGINE_ID:
For information, visit Programmable Search Engine.
2. YOUTUBE_API_KEY:
This API key is used to download subtitles from YouTube videos for generating blog content.
You can obtain it from the library section in the Google Cloud Console.
3. BING_SEARCH_API_ENDPOINT:
Since Azure’s search engine tends to produce better results than Google Custom Engine, this endpoint is included as an alternative.