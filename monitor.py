import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests


ISPORTS_API_KEY = os.environ.get("ISPORTS_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

API_URL = "https://api.isportsapi.com/sport/basketball/odds/fulltime/changes"

last_odds = {}


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN or CHAT_ID missing")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=10
    )


def get_odds():
    response = requests.get(
        API_URL,
        params={"api_key": ISPORTS_API_KEY},
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def monitor():
    send_telegram("🏀 皇冠篮球水位监控已启动")

    while True:
        try:
            data = get_odds()

            spreads = data.get("data", {}).get("spread", [])

            for item in spreads:
                parts = item.split(",")

                if len(parts) < 6:
                    continue

                match_id = parts[0]
                company_id = parts[1]
                handicap = parts[2]
                home = parts[3]
                away = parts[4]

                # 皇冠让分公司 ID = 3
                if company_id != "3":
                    continue

                current = (handicap, home, away)
                previous = last_odds.get(match_id)

                if previous and previous != current:
                    old_handicap, old_home, old_away = previous

                    message = (
                        "🚨 皇冠水位变化\n\n"
                        f"比赛ID：{match_id}\n"
                        f"让分：{old_handicap} → {handicap}\n"
                        f"主队水位：{old_home} → {home}\n"
                        f"客队水位：{old_away} → {away}"
                    )

                    send_telegram(message)

                last_odds[match_id] = current

        except Exception as e:
            print("Monitor error:", e)

        time.sleep(2)


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Crown odds monitor is running")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", "10000"))

    server = HTTPServer(("0.0.0.0", port), HealthHandler)

    print(f"Web server running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    run_web_server()
