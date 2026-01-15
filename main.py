import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
from zoneinfo import ZoneInfo

ROW_RE = re.compile(
    r"""
    (?P<plazo>\b\d+\b)\s+
    (?P<moneda>PESOS|DOLARES|DÓLARES)\s+
    (?P<monto_contado>[\d\.\,]+)\s+
    (?P<monto_futuro>[\d\.\,]+)\s+
    (?P<tasa>[\d\,]+)\s*%\s+
    (?P<fecha>\d{1,2}/\d{1,2}/\d{4})\s+
    (?P<hora>\d{2}:\d{2}:\d{2})
    """,
    re.VERBOSE | re.IGNORECASE,
)

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")
START_AR = time(10, 30)  # 10:30
END_AR = time(17, 0)     # 17:00

def allowed_to_run_now() -> bool:
    """
    Corre solo L-V de 10:30 a 17:00 hora Argentina.
    """
    now_ar = datetime.now(TZ_AR)
    weekday = now_ar.weekday()  # 0=Lun ... 5=Sáb 6=Dom

    # Fin de semana
    if weekday >= 5:
        return False

    t = now_ar.time()
    # Ventana horaria inclusiva
    return START_AR <= t <= END_AR

def fetch_page(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 scraper-bot/1.0"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    return r.text

def extract_first_line(html: str) -> str:
    """
    Devuelve SOLO la primer fila válida de cauciones (prioriza PESOS).
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)

    rows = []
    for m in ROW_RE.finditer(text):
        plazo = m.group("plazo")
        moneda = m.group("moneda").upper().replace("DÓLARES", "DOLARES")
        tasa = m.group("tasa")
        fecha_hora = f'{m.group("fecha")} {m.group("hora")}'
        rows.append((moneda, int(plazo), tasa, fecha_hora))

    if not rows:
        return "No pude leer la tabla de cauciones (cambió el HTML o hay bloqueo)"

    # Priorizar PESOS y luego el menor plazo
    rows_sorted = sorted(rows, key=lambda x: (0 if x[0] == "PESOS" else 1, x[1]))
    moneda, plazo, tasa, fecha_hora = rows_sorted[0]
    return f"Caución {moneda} {plazo}d — {tasa}% ({fecha_hora})"

def send_telegram(bot_token: str, chat_id: str, message: str) -> None:
    api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    }
    r = requests.post(api, json=payload, timeout=25)
    r.raise_for_status()

def main():
    # Filtro horario/fin de semana
    if not allowed_to_run_now():
        return

    bot_token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    url = os.environ["TARGET_URL"]

    html = fetch_page(url)
    msg = extract_first_line(html)  # SOLO una línea
    send_telegram(bot_token, chat_id, msg)

if __name__ == "__main__":
    main()
