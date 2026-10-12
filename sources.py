import asyncio
import json

import config


def _short(text, limit=600):
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit] + "..."


class FileSource:
    """Chats from a json file, used by evaluate.py."""

    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            self.chats = json.load(f)["chats"]
        self.sent = []

    def chat_names(self):
        return list(self.chats)

    def new_messages(self, chat):
        return self.chats[chat][-config.MAX_MESSAGES_PER_CALL:], False

    def context(self, chat, message_id, around):
        msgs = self.chats[chat]
        idx = next((i for i, m in enumerate(msgs) if m["id"] == message_id), None)
        if idx is None:
            return None
        return msgs[max(0, idx - around): idx + around + 1]

    def notify(self, text):
        self.sent.append(text)

    def commit(self):
        pass


class TelegramSource:
    def __init__(self):
        # telethon.sync needs an event loop, python 3.14 doesn't create one by default
        asyncio.set_event_loop(asyncio.new_event_loop())
        from telethon.sync import TelegramClient

        self.client = TelegramClient(str(config.SESSION_FILE), config.TG_API_ID, config.TG_API_HASH)
        self.client.start()
        self.entities = {}
        for dialog in self.client.iter_dialogs():
            if dialog.name in config.ALLOWED_CHATS:
                self.entities[dialog.name] = dialog.entity
        missing = set(config.ALLOWED_CHATS) - set(self.entities)
        if missing:
            print("chats not found:", ", ".join(missing))

        self.state = {}
        if config.STATE_FILE.exists():
            self.state = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
        self.new_state = dict(self.state)
        self.sent = []

    def commit(self):
        config.STATE_FILE.write_text(json.dumps(self.new_state, ensure_ascii=False, indent=2), encoding="utf-8")

    def chat_names(self):
        return list(self.entities)

    def _to_dict(self, m):
        if m.sticker:
            media = "sticker"
        elif m.photo:
            media = "photo"
        elif m.document:
            media = "file"
        else:
            media = None
        sender = m.sender
        name = getattr(sender, "first_name", None) or getattr(sender, "title", None) or "?"
        return {
            "id": m.id,
            "date": m.date.strftime("%Y-%m-%d %H:%M"),
            "from": name,
            "text": _short(m.message),
            "reply_to": m.reply_to_msg_id,
            "media": media,
        }

    def new_messages(self, chat):
        entity = self.entities[chat]
        # new_state so a second call in the same run continues where the first stopped
        last_id = self.new_state.get(chat)
        if last_id is None:
            msgs = list(reversed(self.client.get_messages(entity, limit=config.FIRST_RUN_LIMIT)))
            has_more = False
        else:
            msgs = self.client.get_messages(entity, min_id=last_id, limit=config.MAX_MESSAGES_PER_CALL, reverse=True)
            has_more = len(msgs) == config.MAX_MESSAGES_PER_CALL
        if msgs:
            self.new_state[chat] = max(m.id for m in msgs)
        return [self._to_dict(m) for m in msgs if m.action is None], has_more

    def context(self, chat, message_id, around):
        entity = self.entities[chat]
        target = self.client.get_messages(entity, ids=message_id)
        if target is None:
            return None
        before = self.client.get_messages(entity, max_id=message_id, limit=around)
        after = self.client.get_messages(entity, min_id=message_id, limit=around, reverse=True)
        msgs = list(reversed(before)) + [target] + list(after)
        return [self._to_dict(m) for m in msgs if m.action is None]

    def notify(self, text):
        # always to saved messages, the model can't pick the recipient
        self.client.send_message("me", text)
        self.sent.append(text)
