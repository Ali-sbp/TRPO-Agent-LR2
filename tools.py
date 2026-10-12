import json

import config
from skills import load_skill, skill_names


def tool_schemas(chat_names):
    return [
        {
            "type": "function",
            "function": {
                "name": "get_new_messages",
                "description": (
                    "Возвращает новые сообщения из учебной группы в Telegram, появившиеся с прошлой проверки, "
                    "в порядке времени. У каждого сообщения: id, дата, автор, текст, id сообщения, на которое "
                    "это ответ (reply_to), и тип вложения (sticker, photo, file или null)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chat": {"type": "string", "enum": chat_names, "description": "Название группы"},
                    },
                    "required": ["chat"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_context",
                "description": (
                    "Возвращает сообщения вокруг указанного: несколько до и после. Вызывать, когда смысл "
                    "сообщения непонятен без соседних, например короткий ответ «да, до пятницы»."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chat": {"type": "string", "enum": chat_names},
                        "message_id": {"type": "integer"},
                        "around": {"type": "integer", "default": 5,
                                   "description": "Сколько сообщений взять до и после, от 1 до 10"},
                    },
                    "required": ["chat", "message_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "send_notification",
                "description": (
                    "Отправляет владельцу одно уведомление в Telegram («Избранное»). Вызывать только если найдено "
                    "что-то важное. Все важные пункты собрать в одно уведомление."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Текст уведомления"},
                        "message_ids": {"type": "array", "items": {"type": "integer"},
                                        "description": "id сообщений, о которых это уведомление"},
                    },
                    "required": ["text", "message_ids"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "load_skill",
                "description": "Загружает навык: инструкцию в markdown под типовую задачу. Список навыков в системном промпте.",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "enum": skill_names()}},
                    "required": ["name"],
                },
            },
        },
    ]


class ToolRunner:
    def __init__(self, source):
        self.source = source
        self.notified_ids = []
        self.notifications = 0

    def run(self, name, args):
        handler = getattr(self, "_" + name, None)
        if handler is None:
            return {"error": f"нет инструмента {name}"}
        try:
            return handler(**args)
        except TypeError as e:
            return {"error": f"неверные аргументы: {e}"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    def _check_chat(self, chat):
        if chat not in self.source.chat_names():
            return {"error": "этот чат не разрешён", "allowed_chats": self.source.chat_names()}
        return None

    def _get_new_messages(self, chat):
        if err := self._check_chat(chat):
            return err
        msgs, has_more = self.source.new_messages(chat)
        # explain empty results, otherwise the model keeps retrying
        if not msgs:
            return {"chat": chat, "count": 0,
                    "hint": "Новых сообщений с прошлой проверки нет. По этому чату делать нечего."}
        result = {"chat": chat, "count": len(msgs), "messages": msgs}
        if has_more:
            result["has_more"] = True
            result["hint"] = "Это не все новые сообщения. Вызовите get_new_messages ещё раз, чтобы получить следующую порцию."
        return result

    def _get_context(self, chat, message_id, around=5):
        if err := self._check_chat(chat):
            return err
        around = max(1, min(int(around), 10))
        msgs = self.source.context(chat, int(message_id), around)
        if not msgs:
            return {"count": 0, "hint": f"Сообщение {message_id} не найдено в «{chat}». "
                                        "Проверьте id в результате get_new_messages."}
        return {"chat": chat, "count": len(msgs), "messages": msgs}

    def _send_notification(self, text, message_ids):
        if self.notifications >= config.MAX_NOTIFICATIONS_PER_RUN:
            return {"error": "лимит уведомлений за прогон исчерпан, больше отправлять нельзя. Завершите работу."}
        if not text.strip():
            return {"error": "пустой текст уведомления"}
        self.source.notify(text)
        self.notifications += 1
        self.notified_ids.extend(int(i) for i in message_ids)
        return {"ok": True, "sent_to": "владелец (Избранное)"}

    def _load_skill(self, name):
        text = load_skill(name)
        if text is None:
            return {"error": "нет такого навыка", "available": skill_names()}
        return {"skill": name, "instructions": text}


def as_text(result):
    return json.dumps(result, ensure_ascii=False)
