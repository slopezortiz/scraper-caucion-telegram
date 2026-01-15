cat > main.py <<'PY'
import os
import requests
from bs4 import BeautifulSoup

def fetch_page(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 scraper-bot/1.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text

def extract_value(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else "SIN_TITULO"
    return title

def send_telegram(bot_token: str, chat_id: str, message: str) -> None:
    api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    }
    r = requests.post(api, json=payload, timeout=20)
    r.raise_for_status()

def main():
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    url = os.environ["TARGET_URL"]

    html = fetch_page(url)
    value = extract_value(html)

    msg = f"Nuevo dato detectado:\n{value}\n{url}"
    send_telegram(bot_token, chat_id, msg)

if __name__ == "__main__":
    main()
PY
