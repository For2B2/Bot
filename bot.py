import os
import requests
import feedparser
import re # Import the regular expressions library for cleaning text

# --- Configuration ---
# Secrets are loaded from GitHub Actions environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# List of Persian sources to check
# To find a YouTube channel's RSS feed:
# 1. Go to the channel's page.
# 2. View the page source (Ctrl+U or right-click -> View Page Source).
# 3. Search (Ctrl+F) for "channel_id". The string next to it is the ID.
# 4. The feed URL is: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
SOURCES = {
    'جادی میرمیرانی': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCB2-_N3_a6utDbT0934gXnQ',
    'SkepticWise': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_sCeyc4I8l1n2_yXw24o8w',
    'BBC Persian (تازه ترین ها)': 'https://feeds.bbci.co.uk/persian/rss.xml',
    'زومیت (فناوری)': 'https://www.zoomit.ir/feed/',
    'دیجیاتو (تکنولوژی)': 'https://digiato.com/feed/'
}

# File to store links of already posted articles
POSTED_LINKS_FILE = 'posted_links.txt'

# --- Functions ---

def load_posted_links():
    """Loads the set of already posted links from a file."""
    try:
        with open(POSTED_LINKS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_posted_links(links):
    """Saves the set of posted links back to the file."""
    with open(POSTED_LINKS_FILE, 'w') as f:
        for link in sorted(links):
            f.write(link + '\n')

def clean_html(raw_html):
    """Removes HTML tags from a string."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def send_to_telegram(message):
    """Sends a message to the configured Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML' # Use HTML for formatting links and bold text
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(f"Successfully sent message. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

def process_feeds():
    """Fetches and processes all configured RSS feeds."""
    posted_links = load_posted_links()
    new_links_found = False

    for source_name, feed_url in SOURCES.items():
        print(f"--- Checking {source_name} ---")
        try:
            feed = feedparser.parse(feed_url)
            # Process the 3 most recent entries to avoid spamming
            for entry in reversed(feed.entries[:3]): 
                link = entry.link
                if link not in posted_links:
                    print(f"  New post found: {entry.title}")
                    
                    # --- Create the engaging message ---
                    title = entry.title
                    
                    # Get a summary/description, clean it of HTML tags, and truncate it
                    summary = ""
                    if 'summary' in entry:
                        summary = clean_html(entry.summary)
                        # Truncate summary to keep the message clean
                        if len(summary) > 400:
                           summary = summary[:400] + "..."

                    # Create a hashtag from the source name (removes spaces)
                    hashtag = '#' + source_name.replace(' ', '_').replace('(', '').replace(')', '')

                    # Define a more engaging message format
                    message = (
                        f"📣 <b>منبع: {source_name}</b>\n\n"
                        f"ር title}\n\n"
                        f"{summary}\n\n"
                        f"🔗 <a href='{link}'>ادامه مطلب یا تماشای ویدیو</a>\n\n"
                        f"{hashtag}"
                    )
                    
                    send_to_telegram(message)
                    posted_links.add(link)
                    new_links_found = True
        except Exception as e:
            print(f"Could not process feed for {source_name}. Error: {e}")

    if new_links_found:
        save_posted_links(posted_links)
    else:
        print("No new posts found.")

# --- Main Execution ---
if __name__ == "__main__":
    process_feeds()
