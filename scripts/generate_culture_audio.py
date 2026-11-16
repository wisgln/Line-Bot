
import asyncio
import json
from pathlib import Path

import edge_tts


DATA_FILE = Path("data/culture.json")
OUTPUT_DIR = Path("static/audio/culture")

VOICE = "zh-TW-HsiaoChenNeural"


async def generate_audio():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("r", encoding="utf-8") as file:
        cultures = json.load(file)

    for culture in cultures:
        culture_id = culture["id"]
        output_file = OUTPUT_DIR / f"{culture_id}.mp3"

        # 已經製作過的語音不重新覆蓋
        if output_file.exists():
            print(f"略過：{culture_id}（已存在）")
            continue

        title = culture["title"]
        description = culture["description"]

        text = f"{title}。{description}"

        print(f"正在產生：{culture_id} - {title}")

        communicate = edge_tts.Communicate(
            text=text,
            voice=VOICE
        )

        await communicate.save(str(output_file))

        print(f"完成：{output_file}")

    print("所有泰雅文化語音已產生完成！")


if __name__ == "__main__":
    asyncio.run(generate_audio())
