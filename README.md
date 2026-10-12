# tg-study-agent

Reads new messages in my uni Telegram groups and sends me a short summary of what matters
(homework, deadlines, schedule changes, exams). Skips stickers, memes and chatter.

Made for TRPO lab 2.

## Setup

```
uv sync
cp .env.example .env
```

Fill in `.env`: Telegram `api_id` / `api_hash` from my.telegram.org and a DeepSeek API key.
Put the group names into `ALLOWED_CHATS` in `config.py`.

## Run

```
uv run agent.py            # check groups, send notification to Saved Messages
uv run agent.py --reset    # forget what was read and check again
uv run agent.py --test tests/case1_week.json
uv run evaluate.py         # 10 runs per test case, prints success rate
```

First run asks for phone number and login code in the terminal.

## Files

- `agent.py` - agent loop, step limit, logs to `logs/`
- `tools.py` - tool schemas and implementations
- `skills/` - markdown skills the agent loads itself
- `sources.py` - telegram (telethon) or test chats from json
- `evaluate.py` - success rate on `tests/`
