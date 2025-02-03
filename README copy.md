# AutoPost

AutoPost is a Python-based tool that automatically generates and publishes blog posts from various sources such as web pages, YouTube videos, and text files. It integrates with OpenAI and Gemini clients to process content and categorize it. The generated content is formatted according to the Gutenberg editor format used by WordPress before being posted.

## Blog URL (WordPress based)
[https://klutz91.kr](https://klutz91.kr)

## Features

### Article Process (Web Page Processing)
1. Provide a web page URL as an argument.
2. Analyze the web page to generate a blog post.
3. Reformat the content into Gutenberg format.
4. Publish the post on the blog.

### YouTube Process (YouTube Video Processing)
1. Provide a YouTube URL as an argument.
2. Download subtitles from YouTube and generate a blog post based on them.
3. Reformat the content into Gutenberg format.
4. Publish the post on the blog.

### Text Process (New Feature – Text File Processing)
1. Provide a `.txt` file containing the content to be posted as an argument.
2. Read the file’s content to generate a blog post and categorize it.
3. Reformat the content into Gutenberg format.
4. Publish the post on the blog.

## Installation and Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ted0000/autopost.git
   cd autopost
   ```
2.	**Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```
3.	**Configure Environment Variables**:
Create a .env file in the project’s root directory and add your API keys and configuration details.

## Usage
The script can process blog posts by accepting URL, file, or text file arguments.

### Example Commands
- To process a single URL:
```bash
python main.py --url "https://example.com"
```
- To process a YouTube video:
```bash
python main.py --url "https://youtube.com/watch?v=example"
```
- To process a list of URLs:
```bash
python main.py --file urls.txt
```
- To process content from a text file:
```bash
python main.py --txt content.txt
```

## File Structure
- main.py: The main execution file that processes URL or file arguments.
- ArticleProcessor.py: A class that handles processing of web page URLs.
- YoutubeProcessor.py: A class that handles processing of YouTube URLs.
- TextProcessor.py: A class that handles processing of text files.

This project enables you to automatically convert and manage blog posts from various sources.