import os
import requests
import feedparser
import re

# --- Configuration ---
# Secrets are loaded from GitHub Actions environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# --- Enriched List of Persian Sources ---
SOURCES = {
    'جادی میرمیرانی': {
        'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCB2-_N3_a6utDbT0934gXnQ',
        'type': 'video'
    },
    'SkepticWise': {
        'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_sCeyc4I8l1n2_yXw24o8w',
        'type': 'video'
    },
    'زومیت': {
        'url': 'https://www.zoomit.ir/feed/',
        'type': 'article'
    },
    'دیجیاتو': {
        'url': 'https://digiato.com/feed/',
        'type': 'article'
    },
    'ورزش سه': {
        'url': 'https://www.varzesh3.com/rss/all',
        'type': 'article'
    },
    'دنیای اقتصاد': {
        'url': 'https://donya-e-eqtesad.com/feed',
        'type': 'article'
    },
    'BBC Persian': {
        'url': 'https://feeds.bbci.co.uk/persian/rss.xml',
        'type': 'article'
    }
}

# File to store links of already posted articles
POSTED_LINKS_FILE = 'posted_links.txt'

# --- Functions ---

def load_posted_links():
    """Loads the set of already posted links from a file."""
    try:
        with open(POSTED_LINKS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_posted_links(links):
    """Saves the set of posted links back to the file."""
    with open(POSTED_LINKS_FILE, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(link + '\n')

def clean_html(raw_html):
    """Removes HTML tags from a string for a clean summary."""
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def get_thumbnail_url(entry):
    """Tries to extract a thumbnail URL from a feed entry."""
    # For YouTube standard RSS
    if 'media_thumbnail' in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0]['url']
    # For many news RSS feeds (media:content)
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'image' and 'url' in media:
                return media['url']
    # Sometimes it's in links
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.href
    return None

def send_to_telegram(message, photo_url=None):
    """
    Sends a message to the Telegram channel.
    If a photo_url is provided, it sends a photo with a caption.
    Otherwise, it sends a standard text message.
    """
    if photo_url:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'photo': photo_url,
            'caption': message,
            'parse_mode': 'HTML'
        }
    else:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'text': message,
            'parse_mode': 'HTML'
        }

    try:
        response = requests.post(api_url, data=payload, timeout=20)
        response.raise_for_status()
        
        if not response.json().get('ok'):
             print(f"Telegram API Error: {response.json().get('description')}")
             if photo_url:
                 print("Sending photo failed, falling back to text message.")
                 send_to_telegram(message, photo_url=None)
        else:
             print("Successfully sent message to Telegram.")

    except requests.exceptions.RequestException as e:
        print(f"Network error sending to Telegram: {e}")
        if photo_url:
            print("Retrying as a text-only message due to network error.")
            send_to_telegram(message, photo_url=None)


def process_feeds():
    """Fetches, processes, and posts new entries from all configured RSS feeds."""
    posted_links = load_posted_links()
    new_links_found = False

    for source_name, source_info in SOURCES.items():
        feed_url = source_info['url']
        source_type = source_info['type']
        
        print(f"--- Checking {source_name} ---")
        try:
            feed = feedparser.parse(feed_url)
            for entry in reversed(feed.entries[:3]):
                link = entry.link
                if link not in posted_links:
                    print(f"  New post found: {entry.title}")

                    title = entry.title
                    thumbnail_url = get_thumbnail_url(entry)
                    summary = ""
                    if 'summary' in entry:
                        summary = clean_html(entry.summary)
                        if len(summary) > 300:
                           summary = summary[:300] + "..."
                    
                    if source_type == 'video':
                        intro = f"🎬 <b>ویدیوی جدید از {source_name}</b>"
                        call_to_action = "🔗 تماشای کامل ویدیو"
                    else:
                        intro = f"📝 <b>مقاله جدید در {source_name}</b>"
                        call_to_action = "🔗 خواندن ادامه مطلب"

                    hashtag = '#' + source_name.replace(' ', '_')

                    # --- Create the engaging message ---
                    # THIS ENTIRE BLOCK HAS BEEN REWRITTEN FROM SCRATCH TO FIX THE SYNTAX ERROR.
                    # It now uses a triple-quoted f-string, which is safer for multiline content.
                    message = f"""{intro}

<b>{title}</b>

{summary}

<a href='{link}'>{call_to_action}</a>

{hashtag}"""
                    
                    send_to_telegram(message, photo_url=thumbnail_url)
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
