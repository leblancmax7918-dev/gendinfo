import requests
from bs4 import BeautifulSoup
import json
import os
import sys

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
URL = "https://www.gendarmerie.interieur.gouv.fr/gendinfo/actualites"
LAST_FILE = "last_article.json"


def get_latest_article():
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch {URL}: {e}") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for article links within the main content area.
    article = soup.select_one("main a[href], article a[href], .article a[href]")

    if not article:
        raise RuntimeError("No article link found on the page")

    title = article.get_text(strip=True)
    link = article["href"]

    if not link.startswith("http"):
        link = "https://www.gendarmerie.interieur.gouv.fr" + link

    return {
        "title": title,
        "link": link
    }


def load_last_article():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            return json.load(f)
    return None


def save_last_article(article):
    with open(LAST_FILE, "w") as f:
        json.dump(article, f)


def send_to_discord(article):
    data = {
        "embeds": [
            {
                "title": article["title"],
                "url": article["link"],
                "description": "Nouvel article GendInfo disponible",
                "color": 3447003
            }
        ]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to send Discord notification: {e}") from e


def main():
    if not WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL environment variable is not set")

    latest = get_latest_article()
    last = load_last_article()

    if not last or latest["link"] != last["link"]:
        send_to_discord(latest)
        save_last_article(latest)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
