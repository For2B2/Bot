import os
import requests
import feedparser

# --- Configuration ---
# Secrets are loaded from GitHub Actions environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# List of sources to check
SOURCES = {
    'BBC News': 'http://feeds.bbci.co.uk/news/rss.xml',
    'TechCrunch': 'https://techcrunch.com/feed/',
    'Verge': 'https://www.theverge.com/rss/index.xml',
    'MKBHD YouTube': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ',
    'Jack Dorsey Twitter': 'https://nitter.net/jack/rss',  # Using a Nitter RSS feed
    'NatGeo Instagram': 'https://bibliogram.art/u/natgeo/rss.xml' # Using a Bibliogram RSS feed
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
        for link in sorted(links): # Sort for consistency
            f.write(link + '\n')

def send_to_telegram(message):
    """Sends a message to the configured Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML' # Use HTML for formatting
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status() # Raise an exception for bad status codes
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
            # We only process the 3 most recent entries to avoid spamming on first run
            for entry in reversed(feed.entries[:3]): 
                link = entry.link
                if link not in posted_links:
                    print(f"  New post found: {entry.title}")
                    
                    # --- Create the message ---
                    # You can customize this message format!
                    message = f"<b>{source_name}</b>\n\n<a href='{link}'>{entry.title}</a>"
                    
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
