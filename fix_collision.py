import re

# 1. Remove start handler from commands.py
commands_path = "plugins/auto_uploader/commands.py"
with open(commands_path, "r") as f:
    text = f.read()

# Using regex to remove the start function
text = re.sub(r'@Client\.on_message\(filters\.command\("start"\) & filters\.private\)\nasync def start\(client, message\):.*?(?=@Client\.on_message|$)', '', text, flags=re.DOTALL)
with open(commands_path, "w") as f:
    f.write(text)

# 2. Add Mode Toggle state script
with open("plugins/auto_uploader/mode_toggle.py", "w") as f:
    f.write('''
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
''')

# 3. Update process.py to use this filter
process_path = "plugins/auto_uploader/process.py"
with open(process_path, "r") as f:
    p_text = f.read()

p_text = "from plugins.auto_uploader.mode_toggle import uploader_mode_filter\n" + p_text
p_text = p_text.replace(
    "@Client.on_message((filters.video | filters.document | filters.audio | filters.text) & filters.private & ~filters.command([c for c in [\"start\", \"settings\", \"set_name\", \"clear_queue\", \"set_audio_order\", \"set_default_audio\", \"set_sub_watermark\", \"set_details\", \"cancel_task\", \"start_process\"]]))",
    "@Client.on_message((filters.video | filters.document | filters.audio | filters.text) & filters.private & uploader_mode_filter & ~filters.command([c for c in [\"start\", \"settings\", \"auto_settings\", \"set_name\", \"clear_queue\", \"set_audio_order\", \"set_default_audio\", \"set_sub_watermark\", \"set_details\", \"cancel_task\", \"start_process\", \"upload_mode\"]]))"
)
with open(process_path, "w") as f:
    f.write(p_text)

# 4. Update link_generator.py to NOT be in uploader mode
link_path = "plugins/link_generator.py"
with open(link_path, "r") as f:
    l_text = f.read()

l_text = "from plugins.auto_uploader.mode_toggle import uploader_mode_filter\n" + l_text
l_text = l_text.replace(
    "@Client.on_message(filters.private & (filters.document | filters.video | filters.audio) & ~filters.command([\"start\", \"batch\", \"genlink\"]))",
    "@Client.on_message(filters.private & (filters.document | filters.video | filters.audio) & ~uploader_mode_filter & ~filters.command([\"start\", \"batch\", \"genlink\", \"upload_mode\"]))"
)
with open(link_path, "w") as f:
    f.write(l_text)

