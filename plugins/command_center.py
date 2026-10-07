from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.font_converter import to_small_caps as sc

@Client.on_message(filters.command("cc") & filters.private)
async def command_center(client, message):
    text = f"""<blockquote>**📍 {sc('command center')}**</blockquote>

**{sc('core mode toggle')}:**
• `/upload_mode` - Toggle between File-Store and Auto-Uploader modes.

**{sc('file-store commands')}:**
• `/start` - Main menu
• `/settings` - Configure Main File-Store Database & UI settings
• `/batch` - Generate a batch link for multiple files
• `/genlink` - Generate a link for a single file
• `/usage` - Check your usage limits
• `/mypremium` - Check your premium status

**{sc('auto-uploader commands')}:**
• `/auto_start` - Initialize auto-upload pipeline
• `/start_process` - Manually trigger the queued file upload process
• `/auto_settings` - Manage configuration for the uploader

**{sc('uploader customization')}:**
• `/set_caption` & `/del_caption` - Manage custom file captions
• `/set_rename` & `/del_rename` - Configure filename styling
• `/set_prefix` & `/set_suffix` - Add custom prefix/suffix to files
• `/auto_add_rename_rule` - Add a global clean string (e.g., website URLs to strip)
• `/auto_view_rename_rules` - View all active rename stripping rules
• `/auto_remove_rename_rule` - Remove a rename stripping rule
• `/set_sticker` & `/del_sticker` - Add dynamic watermark stickers to videos
• `/set_audio_order` - Reorder dual-audio tracks (e.g., `hi, en, ja`)"""

    await message.reply_text(
        text,
        quote=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ ᴄʟᴏꜱᴇ", callback_data="close_cc")]])
    )

@Client.on_callback_query(filters.regex("^close_cc$"))
async def close_cc_cb(client, query):
    await query.message.delete()
