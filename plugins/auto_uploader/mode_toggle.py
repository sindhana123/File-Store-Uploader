
from pyrogram import Client, filters
from pyrogram.types import Message

UPLOADER_USERS = set()

async def is_uploader_filter(_, __, m: Message):
    return (m.from_user and m.from_user.id in UPLOADER_USERS)

uploader_mode_filter = filters.create(is_uploader_filter)

@Client.on_message(filters.command("upload_mode") & filters.private)
async def toggle_upload_mode(client, message):
    if message.from_user.id in UPLOADER_USERS:
        UPLOADER_USERS.remove(message.from_user.id)
        await message.reply_text("✅ Auto-Uploader mode Disabled! You are now in File-Store mode.", quote=True)
    else:
        UPLOADER_USERS.add(message.from_user.id)
        await message.reply_text("✅ Auto-Uploader mode Enabled! Send videos here to queue them for uploading/renaming.", quote=True)
