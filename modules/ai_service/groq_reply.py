"""Groq 官方 SDK；沿用既有行程驗證、精簡資料與記憶。"""

import os
import time


def enabled():
    return (
        os.getenv("GROQ_ENABLED", "").strip().lower()
        in ("1", "true")
    )


def get_groq_reply(text, *, session_id=None):
    from . import gemini_reply as core

    if not enabled():
        return None

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip() or len(text) > 2000:
        return None

    key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()

    if not key or not model:
        return (
            "🌿 Groq 設定尚未完成，請管理者確認金鑰與模型。"
            "行程未更新。"
        )

    try:
        from groq import (
            Groq,
            APIStatusError,
            APITimeoutError,
            APIConnectionError,
        )
    except ImportError:
        return (
            "🌿 尚未安裝 Groq 套件，"
            "請管理者安裝 requirements.txt。行程未更新。"
        )

    # 沿用原本的單一程序鎖，保持對話及行程更新順序。
    with core._lock:
        core._prune()

        old = core._sessions.get(session_id) if session_id else None
        history = list(old[1]) if old else []

        user_message = {
            "role": "user",
            "parts": [{"text": text}],
        }

        try:
            raw_context = core.build_context()
            raw_context["attractions"] = core.load_attraction_context()
            raw_context["events"] = core.event_context()
            raw_context["current_plan"] = core.get_saved_stops(session_id)

            context = core.compact_context(raw_context, text, history)
            reference = core.json_text(context)

        except core.ContextBudgetError:
            return (
                "🌿 行程資料較多，尚未送出 AI 請求。"
                "請縮小規劃範圍；原行程仍保留。"
            )

        except (OSError, ValueError, TypeError):
            return (
                "🌿 旅遊資料讀取失敗（LOCAL_DATA），"
                "尚未發送 AI 請求。"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    core.INSTRUCTIONS
                    + "\n參考資料：\n"
                    + reference
                ),
            }
        ]

        # 原記憶格式仍保留，只在送出前轉為 Groq 格式。
        for entry in history:
            content = "\n".join(
                part["text"]
                for part in entry.get("parts", [])
                if isinstance(part.get("text"), str)
                and not part.get("thought")
            )

            if content:
                messages.append(
                    {
                        "role": (
                            "assistant"
                            if entry["role"] == "model"
                            else "user"
                        ),
                        "content": content,
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        options = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 2000,
            "stream": False,
        }

        if model == "qwen/qwen3.8-27b":
            options["reasoning_effort"] = "none"

        # 只記錄長度，不記錄金鑰、對話內容或使用者 ID。
        core.logger.info(
            "Groq chars: reference=%d history=%d question=%d",
            len(reference),
            len(core.json_text(history)),
            len(text),
        )

        try:
            # 僅送一次，不自動重試、不切換其他服務。
            with Groq(
                api_key=key,
                timeout=30.0,
                max_retries=0,
            ) as client:
                result = client.chat.completions.create(**options)

            if not result.choices:
                return (
                    "🌿 沒有取得回答（NO_CANDIDATES），"
                    "行程未更新。"
                )

            choice = result.choices[0]

            if choice.finish_reason == "length":
                return (
                    "🌿 回答尚未完成（MAX_TOKENS），"
                    "行程未更新。請縮小規劃範圍。"
                )

            if choice.finish_reason != "stop":
                return (
                    "🌿 回答中斷（GENERATION_STOPPED），"
                    "行程未更新。"
                )

            raw_answer = choice.message.content

            if not isinstance(raw_answer, str) or not raw_answer.strip():
                return (
                    "🌿 沒有取得文字回答（EMPTY_TEXT），"
                    "行程未更新。"
                )

            try:
                answer, stops = core.decode_plan(raw_answer, context)
            except (ValueError, TypeError, AttributeError, KeyError):
                return core.FORMAT_ERROR

            if len(answer.encode("utf-16-le")) // 2 > 4400:
                return (
                    "🌿 回答超過訊息限制（ANSWER_TOO_LONG），"
                    "行程未更新。"
                )

            # 通過全部驗證後，才更新記憶與行程。
            if session_id:
                history += [
                    user_message,
                    {
                        "role": "model",
                        "parts": [{"text": raw_answer}],
                    },
                ]

                core._sessions[session_id] = (
                    time.monotonic(),
                    history[-core.MAX_MESSAGES:],
                )

                core._plans[session_id] = stops
                core._sessions.move_to_end(session_id)

                while len(core._sessions) > core.MAX_SESSIONS:
                    expired_id, _ = core._sessions.popitem(last=False)
                    core._plans.pop(expired_id, None)

            return answer

        except APITimeoutError:
            return (
                "🌿 等待 Groq 回應逾時（TIMEOUT，30秒），"
                "行程未更新。"
            )

        except APIConnectionError:
            return (
                "🌿 Groq 網路連線失敗（NETWORK），"
                "行程未更新。"
            )

        except APIStatusError as error:
            code = error.status_code

            # 不將服務端原始錯誤或金鑰傳給 LINE 使用者。
            if code == 429:
                return (
                    "🌿 暫時達到 AI 使用限制，請稍後再試。"
                    "行程仍保留，不會自動切換付費服務。"
                )

            if code in (500, 502, 503, 504):
                return (
                    f"🌿 Groq 暫時無法服務（HTTP {code}），"
                    "行程未更新。"
                )

            if code in (400, 401, 403, 404, 413):
                return (
                    f"🌿 Groq 請求未成功（HTTP {code}），"
                    "請管理者確認設定。行程未更新。"
                )

            return (
                f"🌿 Groq 服務回傳錯誤（HTTP {code}），"
                "行程未更新。"
            )

        except (OSError, ValueError, TypeError, AttributeError, IndexError, KeyError):
            return (
                "🌿 Groq 回應無法處理（RESPONSE_FORMAT），"
                "行程未更新。"
            )