import time
import urllib.request
import email.utils

# MOCK SYSTEM CLOCK TO FIX PYROGRAM MSG_ID TIMEOUT IN THIS ENVIRONMENT
original_time = time.time
try:
    with urllib.request.urlopen("https://api.telegram.org") as response:
        tg_time_str = response.headers["date"]
        tg_time = email.utils.parsedate_to_datetime(tg_time_str).timestamp()
        offset = tg_time - original_time()
        print(f"DEBUG: Setting time offset {offset}s to fix Pyrogram.")
        time.time = lambda: original_time() + offset
except Exception as e:
    print("Failed to sync time:", e)

import asyncio
import json
import logging
from bot import Bot, web_app
from pyrogram import compose

logging.getLogger('pyrogram').setLevel(logging.INFO)

# Static default fallback message templates (can be overridden per setup entry if needed)
default_messages = {
    'START': '<blockquote expandable>__Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit sed.\nVivamus luctus urna sed urna.\nCurabitur blandit tempus porttitor.\nNullam quis risus eget urna.__</blockquote>',
    'FSUB': '',
    'ABOUT': 'ABOUT MSG',
    'REPLY': 'reply_text',
    'START_PHOTO': '',
    'FSUB_PHOTO': ''
}

import os

async def main():
    app = []

    # Check if running in production via ENV variables
    if os.getenv("BOT_TOKEN"):
        print("Starting via Environment Variables (Production Mode)")
        try:
            admin_list = [int(x.strip()) for x in os.getenv("ADMINS", str(os.getenv("OWNER_ID", "0"))).split(",") if x.strip()]
            fsub_list = [int(x.strip()) for x in os.getenv("FSUBS", "").split(",") if x.strip()]
            
            # Format fsubs correctly (Pyrogram usually expects list of lists/tuples, but we pass list of ints based on old setup)
            # Actually setup.json has list of lists for fsubs: [[id, link], ...] or just ints? 
            # In setup.json it's usually empty [] or list. Let's just pass empty list and manage it inside bot.
            
            config = {
                "session": os.getenv("SESSION", "ses1"),
                "workers": int(os.getenv("WORKERS", "8")),
                "db": int(os.getenv("DB_CHANNEL")),
                "fsubs": [], # Configure this from /settings panel instead
                "token": os.getenv("BOT_TOKEN"),
                "admins": admin_list,
                "messages": default_messages,
                "auto_del": int(os.getenv("AUTO_DEL", "300")),
                "db_uri": os.getenv("DATABASE_URI"),
                "db_name": os.getenv("DATABASE_NAME", "Cluster0"),
                "api_id": int(os.getenv("API_ID")),
                "api_hash": os.getenv("API_HASH"),
                "protect": os.getenv("PROTECT_CONTENT", "False").lower() in ('true', '1', 't'),
                "disable_btn": os.getenv("DISABLE_BTN", "True").lower() in ('true', '1', 't')
            }
            setups = [config]
        except Exception as e:
            print(f"Failed to parse Environment Variables: {e}")
            return
    else:
        # Fallback to local setup.json
        print("Starting via setup.json (Local Mode)")
        try:
            with open("setup.json", "r", encoding="utf-8") as f:
                setups = json.load(f)
                if isinstance(setups, dict):
                    setups = [setups]
        except Exception as e:
            print(f"Failed to load setup.json: {e}")
            return

    # Loop through each bot setup config
    for config in setups:
        session = config["session"]
        workers = config["workers"]
        db = config["db"]
        fsubs = config["fsubs"]
        token = config["token"]
        admins = config["admins"]
        messages = config.get("messages", default_messages)
        auto_del = config["auto_del"]
        db_uri = config["db_uri"]
        db_name = config["db_name"]
        api_id = int(config["api_id"]) if config.get("api_id") else 0
        api_hash = config["api_hash"]
        protect = config["protect"]
        disable_btn = config["disable_btn"]

        app.append(
            Bot(
                session,
                workers,
                db,
                fsubs,
                token,
                admins,
                messages,
                auto_del,
                db_uri,
                db_name,
                api_id,
                api_hash,
                protect,
                disable_btn
            )
        )

    await compose(app)


async def runner():
    await asyncio.gather(
        main(),
        web_app()
    )

asyncio.run(runner())
