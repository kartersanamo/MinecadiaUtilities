# Minecadia Utilities Bot

Discord bot for community utilities, polls, and server helpers on Minecadia.

Music playback lives in **MinecadiaMusic** (`../MinecadiaMusic/`).

## What it does

- Polls, tags, suggestions, and embed builder
- Screenshare logging, message counter, and player count
- Sync tools, helper commands, and Telegram integration

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add DISCORD_TOKEN, DB_*, webhooks, etc.
python main.py
```

## Config

- `.env` — token, database, webhooks (see `.env.example`)
- `assets/config.json` — channels, roles, Trello boards
