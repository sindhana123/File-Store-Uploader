# Made by @Awakeners_Bots
# GitHub: https://github.com/Awakener_Bots

# ============================================================================
# CREDIT SYSTEM PANELS
# ============================================================================

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyromod import ListenerTimeout
from helper.enhanced_credit_db import EnhancedCreditDB
from helper.payment import PaymentGateway, DEFAULT_PACKAGES
from helper.font_converter import to_small_caps as sc
import json

# Load credit config
try:
    with open("setup.json", "r") as f:
        setup_data = json.load(f)
        credit_config = setup_data[0].get("credit_config", {})
except:
    credit_config = {}

payment_gateway = PaymentGateway(credit_config)


@Client.on_callback_query(filters.regex("^credit_system$"))
async def credit_system_panel(client, query):
    """Main credit system settings panel"""
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    stats = await enhanced_db.get_credit_statistics()
    
    expiry_days = credit_config.get("expiry_days", 30)
    referral_reward = credit_config.get("referral_reward", 5)
    payment_method = credit_config.get("payment_method", "manual")
    
    msg = f"""<blockquote>**{sc('credit system settings')}:**</blockquote>
**{sc('total users with credits')}:** `{stats['total_users']}`
**{sc('total credits in circulation')}:** `{stats['total_balance']}`
**{sc('total earned')}:** `{stats['total_earned']}`
**{sc('total spent')}:** `{stats['total_spent']}`
**{sc('total referrals')}:** `{stats['total_referrals']}`

**{sc('configuration')}:**
• {sc('credit expiry')}: `{expiry_days} {sc('days')}`
• {sc('referral reward')}: `{referral_reward} {sc('credits')}`
• {sc('payment method')}: `{payment_method}`

__{sc('use buttons below to manage credit system')}!__
"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'👤 {sc("manage users")}', 'credit_manage_users')],
        [InlineKeyboardButton(f'⚙️ {sc("settings")}', 'credit_settings'), InlineKeyboardButton(f'💰 {sc("payments")}', 'credit_payments')],
        [InlineKeyboardButton(f'🎁 {sc("referrals")}', 'credit_referrals'), InlineKeyboardButton(f'📊 {sc("stats")}', 'credit_stats')],
        [InlineKeyboardButton(f'◂ {sc("back")}', 'settings')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^credit_manage_users$"))
async def credit_manage_users(client, query):
    """User credit management panel"""
    msg = f"""<blockquote>**{sc('user credit management')}:**</blockquote>

{sc('choose an action')}:
"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'➕ {sc("add credits")}', 'credit_add_user')],
        [InlineKeyboardButton(f'⚙️ {sc("set credits")}', 'credit_set_user')],
        [InlineKeyboardButton(f'🗑️ {sc("remove credits")}', 'credit_remove_user')],
        [InlineKeyboardButton(f'📋 {sc("list users")}', 'credit_list_users')],
        [InlineKeyboardButton(f'🔍 {sc("check user")}', 'credit_check_user')],
        [InlineKeyboardButton(f'◂ {sc("back")}', 'credit_system')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^credit_add_user$"))
async def credit_add_user(client, query):
    """Add credits to user"""
    try:
        await query.message.edit_text(
            f"**{sc('add credits to user')}**\n\n"
            f"{sc('send user id, amount, and expiry days')}:\n"
            f"`{sc('format')}: user_id amount expiry_days`\n"
            f"`{sc('example')}: 123456789 10 30`\n\n"
            f"{sc('send')} /cancel {sc('to cancel')}"
        )
        
        response = await client.listen(query.message.chat.id, timeout=60)
        
        if response.text == "/cancel":
            return await credit_manage_users(client, query)
        
        parts = response.text.split()
        if len(parts) < 2:
            await response.reply(f"❌ {sc('invalid format')}!")
            return await credit_manage_users(client, query)
        
        user_id = int(parts[0])
        amount = int(parts[1])
        expiry_days = int(parts[2]) if len(parts) > 2 else credit_config.get("expiry_days", 30)
        
        enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
        await enhanced_db.add_credits(user_id, amount, expiry_days, reason="admin_added")
        
        await response.reply(
            f"✅ {sc('added')} **{amount}** {sc('credits')} {sc('to user')} `{user_id}`\n"
            f"⏰ {sc('expires in')} {expiry_days} {sc('days')}"
        )
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"🎉 **{sc('credits added')}!**\n\n"
                f"{sc('you received')} **{amount} {sc('credits')}**!\n"
                f"⏰ {sc('expires in')} {expiry_days} {sc('days')}\n\n"
                f"{sc('use')} /credits {sc('to check balance')}"
            )
        except:
            pass
        
    except ListenerTimeout:
        await query.message.edit_text(f"⏱️ {sc('timeout')}! {sc('try again')}")
    except Exception as e:
        await query.message.edit_text(f"❌ {sc('error')}: {e}")
    
    return await credit_manage_users(client, query)


@Client.on_callback_query(filters.regex("^credit_set_user$"))
async def credit_set_user(client, query):
    """Set exact credit amount for user"""
    try:
        await query.message.edit_text(
            f"**{sc('set exact credits')}**\n\n"
            f"{sc('send user id and amount')}:\n"
            f"`{sc('format')}: user_id amount [expiry_days]`\n"
            f"`{sc('example')}: 123456789 50 30`\n\n"
            f"{sc('send')} /cancel {sc('to cancel')}"
        )
        
        response = await client.listen(query.message.chat.id, timeout=60)
        
        if response.text == "/cancel":
            return await credit_manage_users(client, query)
        
        parts = response.text.split()
        if len(parts) < 2:
            await response.reply(f"❌ {sc('invalid format')}!")
            return await credit_manage_users(client, query)
        
        user_id = int(parts[0])
        amount = int(parts[1])
        expiry_days = int(parts[2]) if len(parts) > 2 else credit_config.get("expiry_days", 30)
        
        enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
        await enhanced_db.set_credits(user_id, amount, expiry_days)
        
        await response.reply(
            f"✅ {sc('set credits for user')} `{user_id}` {sc('to')} **{amount}**\n"
            f"⏰ {sc('expires in')} {expiry_days} {sc('days')}"
        )
        
    except ListenerTimeout:
        await query.message.edit_text(f"⏱️ {sc('timeout')}! {sc('try again')}")
    except Exception as e:
        await query.message.edit_text(f"❌ {sc('error')}: {e}")
    
    return await credit_manage_users(client, query)


@Client.on_callback_query(filters.regex("^credit_remove_user$"))
async def credit_remove_user(client, query):
    """Remove all credits from user"""
    try:
        await query.message.edit_text(
            f"**{sc('remove all credits')}**\n\n"
            f"{sc('send user id')}:\n"
            f"`{sc('example')}: 123456789`\n\n"
            f"{sc('send')} /cancel {sc('to cancel')}"
        )
        
        response = await client.listen(query.message.chat.id, timeout=60)
        
        if response.text == "/cancel":
            return await credit_manage_users(client, query)
        
        user_id = int(response.text.strip())
        
        enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
        await enhanced_db.reset_credits(user_id)
        
        await response.reply(f"🗑️ {sc('all credits removed for user')} `{user_id}`")
        
    except ListenerTimeout:
        await query.message.edit_text(f"⏱️ {sc('timeout')}! {sc('try again')}")
    except Exception as e:
        await query.message.edit_text(f"❌ {sc('error')}: {e}")
    
    return await credit_manage_users(client, query)


@Client.on_callback_query(filters.regex("^credit_list_users$"))
async def credit_list_users(client, query):
    """List all users with credits"""
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    users = await enhanced_db.get_all_users_with_credits()
    
    if not users:
        msg = f"📭 {sc('no users have credits currently')}"
    else:
        msg = f"💳 **{sc('users with credits')}** ({len(users)} {sc('total')})\n\n"
        
        for user in users[:15]:  # Show first 15
            user_id = user["_id"]
            balance = user.get("balance", 0)
            expiry = user.get("expiry")
            expiry_text = f" ({sc('expires')}: {expiry.strftime('%Y-%m-%d')})" if expiry else ""
            
            msg += f"• `{user_id}`: {balance} {sc('credits')}{expiry_text}\n"
        
        if len(users) > 15:
            msg += f"\n... {sc('and')} {len(users) - 15} {sc('more users')}"
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'◂ {sc("back")}', 'credit_manage_users')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^credit_check_user$"))
async def credit_check_user(client, query):
    """Check specific user's credits"""
    try:
        await query.message.edit_text(
            f"**{sc('check user credits')}**\n\n"
            f"{sc('send user id')}:\n"
            f"`{sc('example')}: 123456789`\n\n"
            f"{sc('send')} /cancel {sc('to cancel')}"
        )
        
        response = await client.listen(query.message.chat.id, timeout=60)
        
        if response.text == "/cancel":
            return await credit_manage_users(client, query)
        
        user_id = int(response.text.strip())
        
        enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
        credit_info = await enhanced_db.get_credits(user_id)
        
        expiry_text = ""
        if credit_info["expiry"]:
            expiry_date = credit_info["expiry"].strftime("%Y-%m-%d %H:%M")
            expiry_text = f"\n⏰ **{sc('expires')}**: {expiry_date}"
        
        msg = (
            f"💳 **{sc('credit info for user')} `{user_id}`**\n\n"
            f"💰 **{sc('balance')}**: {credit_info['balance']} {sc('credits')}{expiry_text}\n"
            f"📊 **{sc('total earned')}**: {credit_info['total_earned']}\n"
            f"📉 **{sc('total spent')}**: {credit_info['total_spent']}\n"
            f"🎁 **{sc('referrals')}**: {credit_info['referral_count']} {sc('users')}\n"
            f"👤 **{sc('referred by')}**: {credit_info['referred_by'] or sc('none')}"
        )
        
        await response.reply(msg)
        
    except ListenerTimeout:
        await query.message.edit_text(f"⏱️ {sc('timeout')}! {sc('try again')}")
    except Exception as e:
        await query.message.edit_text(f"❌ {sc('error')}: {e}")
    
    return await credit_manage_users(client, query)


@Client.on_callback_query(filters.regex("^credit_settings$"))
async def credit_settings_panel(client, query):
    """Credit system configuration panel"""
    expiry_days = credit_config.get("expiry_days", 30)
    referral_reward = credit_config.get("referral_reward", 5)
    verification_reward = await client.mongodb.get_bot_config('verification_reward', 3)
    
    msg = f"""<blockquote>**{sc('credit system configuration')}:**</blockquote>

**{sc('current settings')}:**
• {sc('credit expiry')}: `{expiry_days} {sc('days')}`
• {sc('referral reward')}: `{referral_reward} {sc('credits')}`
• {sc('verification reward')}: `{verification_reward} {sc('credits')}`

__{sc('note')}: {sc('some settings are in setup.json')}__
"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'⏰ {sc("set expiry days")}', 'credit_set_expiry')],
        [InlineKeyboardButton(f'🎁 {sc("set referral reward")}', 'credit_set_referral')],
        [InlineKeyboardButton(f'✅ {sc("set verification reward")}', 'credit_set_verification')],
        [InlineKeyboardButton(f'🧹 {sc("cleanup expired")}', 'credit_cleanup_expired')],
        [InlineKeyboardButton(f'◂ {sc("back")}', 'credit_system')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^credit_set_verification$"))
async def credit_set_verification(client, query):
    """Set verification reward amount"""
    msg = f"""<blockquote>**{sc('set verification reward')}:**</blockquote>
    
__{sc('enter the amount of credits a user earns after solving the shortener')}.__
__{sc('default is 3 credits')}.__

__{sc('send the number or wait for timeout')}!__
"""
    await query.message.edit_text(msg)
    try:
        res = await client.listen(user_id=query.from_user.id, filters=filters.text, timeout=60)
        if res.text.isdigit():
            reward = int(res.text)
            await client.mongodb.set_bot_config('verification_reward', reward)
            await query.message.edit_text(f"**{sc('verification reward updated to')} {reward} {sc('credits')}!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'◂ {sc("back")}', 'credit_settings')]]))
        else:
            await query.message.edit_text(f"**{sc('invalid number')}!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'◂ {sc("back")}', 'credit_settings')]]))
    except ListenerTimeout:
        await query.message.edit_text(f"**{sc('timeout')}!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'◂ {sc("back")}', 'credit_settings')]]))


@Client.on_callback_query(filters.regex("^credit_cleanup_expired$"))
async def credit_cleanup_expired(client, query):
    """Manually cleanup expired credits"""
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    count = await enhanced_db.cleanup_all_expired()
    
    await query.answer(f"🧹 {sc('cleaned up')} {count} {sc('expired credit accounts')}", show_alert=True)
    return await credit_settings_panel(client, query)


@Client.on_callback_query(filters.regex("^credit_payments$"))
async def credit_payments_panel(client, query):
    """Payment management panel"""
    payment_method = credit_config.get("payment_method", "manual")
    packages = credit_config.get("packages", DEFAULT_PACKAGES)
    
    msg = f"""<blockquote>**{sc('payment management')}:**</blockquote>

**{sc('payment method')}:** `{payment_method}`

**{sc('credit packages')}:**
"""
    
    for pkg in packages:
        popular = " ⭐" if pkg.get("popular") else ""
        msg += f"• {pkg['credits']} {sc('credits')} - ₹{pkg['price']}{popular}\n"
    
    msg += f"\n__{sc('configure packages in setup.json')}__"
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'✅ {sc("approve payment")}', 'credit_approve_payment')],
        [InlineKeyboardButton(f'❌ {sc("reject payment")}', 'credit_reject_payment')],
        [InlineKeyboardButton(f'📜 {sc("payment logs")}', 'credit_payment_logs')],
        [InlineKeyboardButton(f'◂ {sc("back")}', 'credit_system')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^credit_approve_payment$"))
async def credit_approve_payment_handler(client, query):
    """Approve manual payment"""
    try:
        await query.message.edit_text(
            f"**{sc('approve payment')}**\n\n"
            f"{sc('send payment id')}:\n"
            f"`{sc('example')}: MANUAL_123456_abc123`\n\n"
            f"{sc('send')} /cancel {sc('to cancel')}"
        )
        
        response = await client.listen(query.message.chat.id, timeout=60)
        
        if response.text == "/cancel":
            return await credit_payments_panel(client, query)
        
        payment_id = response.text.strip()
        
        # Verify payment
        result = await payment_gateway.verify_payment(payment_id)
        
        if not result.get("success"):
            await response.reply(f"❌ {result.get('error', sc('payment not found'))}")
            return await credit_payments_panel(client, query)
        
        # Add credits
        user_id = result["user_id"]
        package = result["package"]
        
        enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
        expiry_days = credit_config.get("expiry_days", 30)
        await enhanced_db.add_credits(user_id, package["credits"], expiry_days, reason=f"purchase_{payment_id}")
        
        # Approve
        await payment_gateway.approve_payment(payment_id)
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"✅ **{sc('payment approved')}!**\n\n"
                f"💰 **{package['credits']} {sc('credits')}** {sc('added to your account')}!\n"
                f"⏰ {sc('expires in')} {expiry_days} {sc('days')}\n\n"
                f"{sc('use')} /credits {sc('to check balance')}"
            )
        except:
            pass
        
        await response.reply(
            f"✅ {sc('payment approved')}!\n"
            f"{sc('added')} {package['credits']} {sc('credits to user')} `{user_id}`"
        )
        
    except ListenerTimeout:
        await query.message.edit_text(f"⏱️ {sc('timeout')}! {sc('try again')}")
    except Exception as e:
        await query.message.edit_text(f"❌ {sc('error')}: {e}")
    
    return await credit_payments_panel(client, query)


@Client.on_callback_query(filters.regex("^credit_referrals$"))
async def credit_referrals_panel(client, query):
    """Referral system management"""
    referral_reward = credit_config.get("referral_reward", 5)
    
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    stats = await enhanced_db.get_credit_statistics()
    
    msg = f"""<blockquote>**{sc('referral system')}:**</blockquote>

**{sc('total referrals')}:** `{stats['total_referrals']}`
**{sc('reward per referral')}:** `{referral_reward} {sc('credits')}`

__{sc('users earn credits by inviting friends')}!__
"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'👤 {sc("top referrers")}', 'credit_top_referrers')],
        [InlineKeyboardButton(f'🔍 {sc("check user referrals")}', 'credit_check_referrals')],
        [InlineKeyboardButton(f'◂ {sc("back")}', 'credit_system')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^credit_stats$"))
async def credit_stats_panel(client, query):
    """Detailed credit statistics"""
    enhanced_db = EnhancedCreditDB(client.db_uri, client.db_name)
    stats = await enhanced_db.get_credit_statistics()
    
    msg = f"""<blockquote>**{sc('credit system statistics')}:**</blockquote>

👥 **{sc('total users')}**: {stats['total_users']}
💰 **{sc('total balance')}**: {stats['total_balance']} {sc('credits')}
📈 **{sc('total earned')}**: {stats['total_earned']} {sc('credits')}
📉 **{sc('total spent')}**: {stats['total_spent']} {sc('credits')}
🎁 **{sc('total referrals')}**: {stats['total_referrals']}

**{sc('economy health')}:**
• {sc('credits per user')}: {stats['total_balance'] / max(stats['total_users'], 1):.1f}
• {sc('usage rate')}: {(stats['total_spent'] / max(stats['total_earned'], 1) * 100):.1f}%
"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'🔄 {sc("refresh")}', 'credit_stats')],
        [InlineKeyboardButton(f'◂ {sc("back")}', 'credit_system')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)
