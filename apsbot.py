import feedparser
import requests
import time
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone


from dotenv import load_dotenv

from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configuration loads from .env
webhook_urls = os.environ.get("WEBHOOK_URLS").split(",")
llm_model = os.getenv("MODEL")
region = os.getenv("REGION")
project_id = os.getenv("PROJECT_ID")

date_file_path = os.getenv("DATE_FILE_PATH")  # Changed from HASH_FILE_PATH
rss_url = os.getenv("RSS_URL")

# Only run this block for Vertex AI API
client = genai.Client(
    vertexai=True, project=project_id, location=region
)

def get_latest_entry_date(rss_data):
    # print(rss_data)
    if not rss_data['entries']:
        print("No entries found in the RSS feed.")
        return None
    for entry in rss_data['entries']:
        # publication_date = entry.get('dc:date')  # Adjusting to fetch 'dc:date'
        publication_date = entry.get('prism_publicationdate', 'No publication date available')
        # print(entry)
        # print(publication_date)
        if publication_date:
            # Assuming the date is in ISO 8601 format
            return datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
    print("No valid publication date found in the entries.")
    return None

def save_latest_entry_date(pub_date):
    with open(date_file_path, 'w') as file:
        # ISO format with timezone
        file.write(pub_date.isoformat())


def read_latest_entry_date():
    if not os.path.exists(date_file_path):
        # Return a timezone-aware datetime object 8days before the current time
        return datetime.now(timezone.utc) - relativedelta(days=8)
    with open(date_file_path, 'r') as file:
        date_str = file.read().strip()  # Use .strip() to remove any leading/trailing whitespace
        # Ensure the datetime object is timezone-aware
        return datetime.fromisoformat(date_str)

def process_rss_feed(rss_data, last_processed_date):
    extracted_info = []
    for entry in rss_data['entries']:
        publication_date_str =  entry.get('prism_publicationdate', 'No publication date available')
        if publication_date_str:
            # Replace 'Z' with '+00:00' for compatibility and parse the ISO 8601 format
            try:
                publication_date = datetime.fromisoformat(publication_date_str.replace('Z', '+00:00'))
                # print(publication_date)
            except ValueError:
                print(f"Error parsing date: {publication_date_str}")
                continue
            
            
            if publication_date > last_processed_date:
                title = entry.get('title', 'No title available')
                author = entry.get('author', 'No author available')
                publication_date = entry.get('prism_publicationdate', 'No publication date available')
                doi = entry.get('prism_doi', 'No DOI available')
                link = entry.get('link', 'No link available')  # Link to the original article
                summary = entry.get('summary', 'No summary available').split('<br />')[0]
                content = entry.get('content', [{}])[0].get('value', 'No content available')

                extracted_info.append({
                    'title': title, 
                    'authors': author, 
                    'publication_date': publication_date, 
                    'doi': doi, 
                    'content': content, 
                    'summary': summary, 
                    'link': link
                })
    return extracted_info


def format_to_markdown(info, summary):
    # Format the extracted information into markdown
    markdown_format = (
        f"- **{info['title']}**\n"
        f" {info['authors']}\n"
        f" {info['publication_date']}\n"
        f" ```{summary}```\n"
        f" {info['link']}\n"
    )
    
    return markdown_format

def generate_and_send_messages(extracted_info, llm_model, webhook_urls):
    system_instruction = """あなたは高度な英語-日本語翻訳者です。提供された英語の論文要旨を学術的な聴衆に向けて日本語に要約してください。要約は100文字以内に抑え、論文の核心を簡潔に表現してください。文字数の制限は論文の内容の複雑さによって柔軟に調整可能です。要約が不可能な場合、または「Abstract not found.」と入力された場合は、「要約なし」と返してください。論文要旨が短い場合、直接的な日本語訳を提供してください。プロセスの結果として、要約または翻訳されたテキストのみを返すようにしてください。"""
    
    for info in reversed(extracted_info):
        content_message = f"Content: {info['content']}\nSuppl: {info['summary']}"
        # f"{info['summary']}"
        # print("debug: "+content_message)
        
        message = client.models.generate_content(
            model=llm_model,
            contents=content_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

        translated_summary = message.text.strip()
        print(translated_summary)
        markdown_message = format_to_markdown(info, translated_summary)
        
        # print(markdown_message)

        # ここでDiscordにメッセージをPOSTする
        payload = {"content": markdown_message}
        
        # 本番では以下のコメントアウトを外す
        for url in webhook_urls:
            response = requests.post(url, json=payload)
            if response.status_code in (200, 204):
                print(f"Successfully posted to Discord: {info['title']}")
            else:
                print(f"Failed to post to Discord: {info['title']} ({response.status_code})")

        time.sleep(1)  # 60回/分のレート制限に従う

# Main logic to check for updates in the RSS feed and process them
rss_feed_data = feedparser.parse(rss_url)
latest_entry_date = get_latest_entry_date(rss_feed_data)
last_processed_date = read_latest_entry_date()

if latest_entry_date and (not last_processed_date or latest_entry_date > last_processed_date):
    print("New entry found, processing...")
    extracted_info = process_rss_feed(rss_feed_data, last_processed_date)
    generate_and_send_messages(extracted_info, llm_model, webhook_urls)  # Assuming this function is defined elsewhere
    save_latest_entry_date(latest_entry_date)
else:
    print("No new entries, no action required.")
