import feedparser
import requests
import time
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone


from dotenv import load_dotenv
from anthropic import AnthropicVertex

# Load environment variables
load_dotenv()

# Configuration loads from .env
webhook_url = os.getenv("WEBHOOK_URL")
model = os.getenv("MODEL")
region = os.getenv("REGION")
project_id = os.getenv("PROJECT_ID")
date_file_path = os.getenv("DATE_FILE_PATH")  # Changed from HASH_FILE_PATH
rss_url = os.getenv("RSS_URL")

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
        # Return a timezone-aware datetime object one month before the current time
        return datetime.now(timezone.utc) - relativedelta(months=1)
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


def generate_and_send_messages(extracted_info, model, region, project_id, webhook_url):
    client = AnthropicVertex(region=region, project_id=project_id)
    
    for info in extracted_info:
        content_message = f"Title: {info['title']}\nAuthors: {info['authors']}\nPublication Date: {info['publication_date']}\nDOI: {info['doi']}\nContent: {info['content']}\nSummary: {info['summary']}\nLink: {info['link']}\n"
        
        message = client.messages.create(
            max_tokens=1024,
            system="""あなたは英日翻訳の優秀な専門家です。以下の情報を翻訳し、整形してください。titleとauthorsは英語のままにして、summaryは日本語に訳してください。最後にurlをつけてください。また、フォーマットはマークダウン形式に従い、以下のように成型してください:
- **Title**: [ここにタイトルを挿入]
- **Authors**: [ここに著者を挿入。複数いる場合はコンマで区切ってください]
- **Publication Date**:[ここに出版日を挿入。]
- **Summary**: [ここに翻訳した要約を日本語で挿入]
- **Link**: [ここにlinkを挿入]
""",
            messages=[
                {
                    "role": "user",
                    "content": content_message,
                }
            ],
            model=model,
        )

        # ここでDiscordにメッセージをPOSTする
        payload = {"content": message.content[0].text}
        response = requests.post(webhook_url, json=payload)
        if response.status_code in (200, 204):
            print(f"Successfully posted to Discord: {info['title']}")
        else:
            print(f"Failed to post to Discord: {info['title']} ({response.status_code})")

        time.sleep(10)  # 30回/分のレート制限に従う

# Main logic to check for updates in the RSS feed and process them
rss_feed_data = feedparser.parse(rss_url)
latest_entry_date = get_latest_entry_date(rss_feed_data)
last_processed_date = read_latest_entry_date()

if latest_entry_date and (not last_processed_date or latest_entry_date > last_processed_date):
    print("New entry found, processing...")
    extracted_info = process_rss_feed(rss_feed_data, last_processed_date)
    generate_and_send_messages(extracted_info, model, region, project_id, webhook_url)  # Assuming this function is defined elsewhere
    save_latest_entry_date(latest_entry_date)
else:
    print("No new entries, no action required.")
