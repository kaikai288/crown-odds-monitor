
import os
import requests

API_KEY = os.environ.get("ISPORTS_API_KEY")
URL = "https://api.isportsapi.com/sport/basketball/schedule/basic"

if not API_KEY:
    print("错误：未设置 ISPORTS_API_KEY")
else:
    try:
        response = requests.get(
            URL,
            params={
                "api_key": API_KEY,
                "date": "2026-10-13"
            },
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        print("MATCH DATA:", str(result)[:3000])
        if result.get("code") == 0:
            matches = result.get("data") or []
            if isinstance(matches, dict):
                matches = [matches]

            found = False
            for match in matches:
                if str(match.get("matchId")) == "21207370":
                    print("联赛：", match.get("leagueName"))
                    print("主队：", match.get("homeName"))
                    print("客队：", match.get("awayName"))
                    print("比赛ID：", match.get("matchId"))
                    found = True

            if not found:
                print("未找到比赛 21207370")
        else:
            print("API 返回错误：", result.get("message"))

    except Exception as e:
        print("查询失败：", e)
  
