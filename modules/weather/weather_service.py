import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ssl
import requests
import truststore
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv


# 從專案根目錄讀取 .env，不把授權碼寫進程式
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAIWAN_TIME = timezone(timedelta(hours=8))

API_URL = (
    "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
    "F-D0047-005"
)


class SystemTLSAdapter(HTTPAdapter):
    """讓天氣連線使用系統憑證驗證。"""

    def build_connection_pool_key_attributes(
        self, request, verify, cert=None
    ):
        host_params, pool_kwargs = (
            super().build_connection_pool_key_attributes(
                request, verify, cert
            )
        )
        pool_kwargs["ssl_context"] = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )
        return host_params, pool_kwargs


def parse_time(value):
    """將 API 時間轉為台灣時間。"""
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        result = result.replace(tzinfo=TAIWAN_TIME)
    return result.astimezone(TAIWAN_TIME)

def extract_forecasts(data, now):
    """只取桃園市復興區，排除已結束的預報。"""
    forecasts = []

    for area in data["records"]["Locations"]:
        if area.get("LocationsName") != "桃園市":
            continue

        for location in area.get("Location", []):
            if location.get("LocationName") != "復興區":
                continue

            for element in location.get("WeatherElement", []):
                for period in element.get("Time", []):
                    # 使用官方綜合描述，避免拼接不同時段的數值
                    descriptions = [
                        value.get("WeatherDescription")
                        for value in period.get("ElementValue", [])
                        if value.get("WeatherDescription")
                    ]

                    if not descriptions:
                        continue

                    start = parse_time(period["StartTime"])
                    end = parse_time(period["EndTime"])

                    if end <= now or end <= start:
                        continue

                    forecasts.append(
                        (start, end, str(descriptions[0]))
                    )

    forecasts.sort(key=lambda item: item[0])
    return forecasts[:3]


def get_weather_reply():
    """回傳天氣文字；不直接呼叫 LINE API。"""
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    api_key = os.getenv("WEATHER_API_KEY", "").strip()

    if not api_key:
        return "尚未設定 WEATHER_API_KEY，請確認專案的 .env。"

    try:
        with requests.Session() as session:
            session.mount(
                "https://opendata.cwa.gov.tw/",
                SystemTLSAdapter(),
            )
            response = session.get(
                API_URL,
                params={
                    "Authorization": api_key,
                    "format": "JSON",
                },
                timeout=(5, 20),
            )

        if response.status_code in (401, 403):
            return "氣象署授權未通過，請確認 API 授權碼是否有效。"

        if response.status_code == 429:
            return "氣象署查詢次數暫時達到限制，請稍後再試。"

        response.raise_for_status()
        data = response.json()

        if str(data.get("success")).lower() != "true":
            return "氣象署未成功回傳資料，請確認授權設定後再試。"

        now = datetime.now(TAIWAN_TIME)
        forecasts = extract_forecasts(data, now)

        if not forecasts:
            return "目前沒有取得復興區有效的預報時段，請稍後再試。"

        lines = ["桃園市復興區｜近期天氣預報"]

        for start, end, description in forecasts:
            lines.append(
                f"\n{start:%m/%d %H:%M}～{end:%m/%d %H:%M}"
                f"\n{description}"
            )

        lines.append(f"\n查詢時間：{now:%m/%d %H:%M}（台灣時間）")
        lines.append("資料來源：中央氣象署；以上為預報，非即時觀測。")
        return "\n".join(lines)

    except requests.Timeout:
        return "天氣查詢逾時，請稍後再試。"
    except requests.RequestException as error:
        error_type = type(error).__name__
        status = (
            error.response.status_code
            if error.response is not None
            else "無"
        )
        return f"天氣查詢失敗：類型={error_type}，HTTP 狀態={status}"
    except (ValueError, KeyError, TypeError, AttributeError):
        return "天氣資料格式與預期不符，需要檢查資料解析程式。"


if __name__ == "__main__":
    print(get_weather_reply())