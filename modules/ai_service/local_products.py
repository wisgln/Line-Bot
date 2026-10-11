"""依官方來源整理農產介紹；不查詢即時庫存或代客下單。"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

from .intent import normalize

DATA_PATH = Path(__file__).resolve().parents[2] / 'data' / 'local_products.json'
logger = logging.getLogger(__name__)
GENERAL_WORDS = ('農產品', '農特產', '農產', '伴手禮', '特產', '土產')
PRODUCT_WORDS = ('水蜜桃', '甜柿', '桂竹筍', '綠竹筍', '香菇', '高山茶', '五月桃', '媽媽桃', '烏龍茶', '茶葉', '柑橘', '柑桔', '奇異果', '獼猴桃', '彌猴桃', '咖啡', '蔬菜', '花卉', '園藝')


def load_products(data_path=None):
    path = Path(data_path) if data_path is not None else DATA_PATH
    with path.open(encoding='utf-8-sig') as stream:
        entries = json.load(stream)
    if not isinstance(entries, list) or not entries:
        raise ValueError('農產資料必須為非空陣列')
    seen = set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError('農產項目必須為物件')
        for field in ('id', 'name', 'description', 'season', 'source_url', 'purchase_url', 'checked_on', 'group'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f'缺少有效欄位：{field}')
        if item['id'] in seen:
            raise ValueError('農產 id 不可重複')
        seen.add(item['id'])
        aliases = item.get('keywords')
        if not isinstance(aliases, list) or not aliases or not all(isinstance(x, str) and x.strip() for x in aliases):
            raise ValueError('keywords 必須為非空文字陣列')
        for field in ('source_url', 'purchase_url'):
            url = urlparse(item[field])
            if url.scheme != 'https' or not url.netloc:
                raise ValueError('來源與購買資訊必須為 HTTPS 網址')
    return entries


def get_local_products_reply(text, *, data_path=None):
    query = normalize(text)
    if len(text) > 2000:
        return '問題太長了，請縮短至 2000 字以內。'
    if not any(word in query for word in GENERAL_WORDS + PRODUCT_WORDS):
        return None
    try:
        entries = load_products(data_path)
    except (OSError, ValueError):
        logger.exception('Unable to load local product data')
        return '農產介紹暫時讀取不順，請稍後再試。也可以到復興區農會查看資訊：https://fushin-eshop.org/'

    matches = [item for item in entries if any(normalize(word) in query for word in item['keywords'])]
    # 加工品的具體名稱優先於同時命中的水蜜桃。
    if len(matches) > 1 and any(word in query for word in ('加工', '米乖乖', '霜淇淋', '甘糀')):
        processed = [item for item in matches if item['name'] == '水蜜桃加工伴手禮']
        if processed and not any(word in query for word in ('和', '與', '還有')):
            matches = processed
    if len(matches) != 1:
        selection = matches or entries
        lines = ['🌿 復興好物，跟著喜好慢慢找！', '從果香、茶香到花草，挑一種你喜歡的旅途紀念吧。']
        groups = dict.fromkeys(item['group'] for item in selection)
        for group in groups:
            lines.append('\n' + group)
            lines.append('・' + '、'.join(item['name'] for item in selection if item['group'] == group))
        lines.append('\n💬 輸入品名，例如「水蜜桃產季」或「甜柿哪裡買」，看看介紹與洽詢入口。')
        lines.append('這是探索在地好物的起點，還有更多品種與季節限定等你發現。')
    else:
        item = matches[0]
        lines = ['🌿 山裡好物｜' + item['name'], '\n✨ 小小介紹\n' + item['description'],
                 '\n🗓 產季參考\n' + item['season'],
                 '採收時間會受品種、海拔與天候影響；產季不代表今天有現貨。',
                 '\n🛍️ 購買資訊與洽詢｜復興區農會\n' + item['purchase_url'],
                 '這是農會資訊入口。先確認當期販售品項、規格、價格及取貨方式，再自行聯絡購買喔！',
                 '\n📖 產季資料來源\n' + item['source_url'],
                 '\n資料查詢日期：' + item['checked_on']]
    if any(word in query for word in ('附近', '最近', '周邊', '週邊')):
        lines.append('\n📍 下方資訊未依你的位置排序，不能視為最近的販售地點。')
    return '\n'.join(lines)
