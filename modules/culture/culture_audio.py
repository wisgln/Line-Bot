
from pathlib import Path
from linebot.v3.messaging import AudioMessage


# 已上傳 GitHub 的公開 MP3 網址
AUDIO_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "wisgln/Line-Bot/develop/static/audio/culture"
)

# 本機語音檔位置
AUDIO_DIR = Path("static/audio/culture")


def get_culture_audio_message(culture_id):
    """根據文化主題 ID 建立 LINE 音訊訊息。"""

    # 只允許 8 個已建立的文化主題
    valid_ids = {
        f"culture{i:03d}" for i in range(1, 9)
    }

    if culture_id not in valid_ids:
        return None

    audio_file = AUDIO_DIR / f"{culture_id}.mp3"

    if not audio_file.is_file():
        return None

    # 以 MP3 的實際長度計算毫秒數
    from mutagen.mp3 import MP3

    duration_ms = round(MP3(str(audio_file)).info.length * 1000)

    audio_url = f"{AUDIO_BASE_URL}/{culture_id}.mp3"

    return AudioMessage(
        original_content_url=audio_url,
        duration=duration_ms
    )
