import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

ISPORTS_API_KEY = os.environ.get("ISPORTS_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://api.isportsapi.com/sport/basketball/odds/fulltime/changes"

last_odds = {}


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )
        print("Telegram status:", r.status_code, r.text, flush=True)
    except Exception as e:
        print("Telegram error:", e)


def get_odds():
    try:
        response = requests.get(
            API_URL,
            params={"api_key": ISPORTS_API_KEY},
            timeout=15
        )

        data = response.json()
        print("API DEBUG:", response.status_code, "code:", data.get("code"), "data_type:", type(data.get("data")).__name__, "data_keys:", list(data.get("data", {}).keys()) if isinstance(data.get("data"), dict) else "N/A", flush=True)
        if data.get("code") != 0:
            print("API response:", data)
            return []

        return data.get("data", {}).get("spread", [])

    except Exception as e:
        print("API error:", e)
        return []


def monitor():
    send_telegram("✅ 皇冠水位监控程序已启动")

    while True:
        odds = get_odds()

        for item in odds:
            try:
                parts = item.split(",")

                if len(parts) < 6:
                    continue

                match_id = parts[0]
                company_id = parts[1]
                handicap = parts[2]
                home = parts[3]
                away = parts[4]
                change_time = parts[5]

                # 皇冠让分 companyId = 3
                if company_id != "3":
                    continue

                current = (handicap, home, away)

                if match_id not in last_odds:
                    last_odds[match_id] = current
                    continue

                old = last_odds[match_id]

                if old != current:
                    message = (
                        "🚨 皇冠水位变化\n\n"
                        f"比赛ID：{match_id}\n"
                        f"让分：{old[0]} → {handicap}\n"
                        f"主队水位：{old[1]} → {home}\n"
                        f"客队水位：{old[2]} → {away}\n"
                        f"更新时间：{change_time}"
                    )

                    send_telegram(message)
                    last_odds[match_id] = current

            except Exception as e:
                print("Parse error:", e)

        time.sleep(60)


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Crown Odds Monitor OK")

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()

    port = int(os.environ.get("PORT", "10000"))

    server = HTTPServer(("0.0.0.0", port), HealthHandler)

    print(f"Server running on port {port}")

    server.serve_forever()
