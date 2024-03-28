
# APSBot: American Physical Society Feed Translator and Notifier

`apsbot.py` is a Python script designed to monitor updates from the American Physical Society's Physical Review Journals RSS feed (Editors' Suggestions), translate the new entries into Japanese (while keeping certain elements in English), and post the summaries to a Discord channel. This tool is invaluable for researchers, students, and enthusiasts looking to stay updated on the latest publications in the field of physics and share this knowledge within a community on Discord.

## Features

- Monitors the RSS feed from American Physical Society's Physical Review Journals for new publications (Editors' Suggestions).
- Translates the titles, summaries, and other key details of publications to Japanese, retaining the titles and authors in English.
- Posts the translated summaries to a specified Discord channel through a webhook.
- Uses environment variables to manage sensitive information like API keys and webhook URLs securely.

## Prerequisites

To use `apsbot.py`, you need:

- Python 3.6 or newer.
- An Anthropic API access with credentials (`model`, `region`, `project_id`) using Google Cloud VertexAI.
- A Discord channel and a webhook URL for posting the updates.

## Setup

1. **Clone the Repository**

    Start by cloning the repository and navigating into the project directory:

    ```bash
    git clone https://github.com/yasuhiroinoue/apsbot.git
    cd apsbot
    ```

2. **Install Dependencies**

    Install the required Python libraries:

    ```bash
    pip install feedparser requests python-dotenv python-dateutil
    ```

3. **Configure Environment Variables**

    Make a copy of `.env.example` as `.env` and update it with your specific details:

    ```
    WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
    MODEL=your_model_identifier
    REGION=your_region
    PROJECT_ID=your_project_id
    DATE_FILE_PATH=path_to_store_last_processed_date.txt
    RSS_URL=http://feeds.aps.org/rss/allsuggestions.xml
    ```

    These settings include your webhook URL, API access credentials, and the path for a file to track the last processed date from the RSS feed.

4. **Running the Script**

    Run `apsbot.py` to start monitoring the RSS feed and posting updates:

    ```bash
    python apsbot.py
    ```

## Usage

With `apsbot.py`, you can ensure that you and your community are always informed about the latest research and articles published in the Physical Review Journals. The script can be set up to run periodically via a cron job or another task scheduler to automate the process of fetching, translating, and posting updates.

## Contributing

Contributions, feature requests, and bug reports are welcome! Feel free to fork the repository, make your changes, and submit a pull request to improve `apsbot`.
