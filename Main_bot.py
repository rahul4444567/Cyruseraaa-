import logging, re, time, os, asyncio, sys, json
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

# ╔══════════════════════════════════════════════╗
# ║   🔑 CONFIG & API KEYS                       ║
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9194570834:AAEStKzKYgSS8h4BNQpCMUywpBN2GjE6_AA") 
OWNER_ID = 8961231487
OWNER_USERNAME = "dipesh"
OWNER_PASS = "@Rahul4444"

CHANNEL_LINK = "https://t.me/cyrusseraaaa"
GROUP_LINK = "https://t.me/onlineworkzone7"
CHANNEL_ID = "@cyrusseraaaa"
GROUP_ID = "@onlineworkzone7"
PAYMENT_CHANNEL = "https://t.me/paymentofcyrusseraa" 

NOVA_BASIC_LINK = "https://t.me/Norevix_bot"
NOVA_PRO_LINK = "https://t.me/Norevixpro_bot"
# ╚══════════════════════════════════════════════╝

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ══════════════════════════════════
#  DATABASES & STATES
# ══════════════════════════════════
notes_db, filters_db, warns_db, rules_db = {}, {}, {}, {}
welcome_db, goodbye_db, locked_db, afk_db = {}, {}, {}, {}
flood_db, linkban_db, spamban_db, spam_track = {}, {}, {}, {}
store_products, pending_orders, owner_states = {}, {}, {}
premium_users, trial_used, pending_payments, payment_steps = {}, set(), {}, {}
schedule_states, login_states, logged_in = {}, {}, set()

custom_commands = {} 
command_states = {}
temp_owners = {}
bot_users, bot_groups, issue_states = set(), set(), set()
admin_reply_states = {} 

default_replies = {
    "hi": "👋 Hello! Kaise hain aap? Main aapki kya madad kar sakta hoon?",
    "hii": "👋 Hello! Kaise hain aap?",
    "hello": "👋 Namaste! Main Cyrus Era Bot hoon. Kripya /help type karein.",
    "hey": "✨ Hey! Kya haal hai?",
    "good morning": "🌅 Good Morning! Aapka din mangalmay ho.",
    "gm": "🌅 Good Morning!",
    "good night": "🌙 Good Night! Meethe sapne.",
    "gn": "🌙 Good Night!",
    "bye": "👋 Alvida! Fir milenge.",
    "thanks": "🙏 Aapka swagat hai!",
    "thank you": "🙏 Aapka swagat hai!"
}

MAX_WARNS = 3
LINK_PATTERN = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|bit\.ly/|youtu\.be/)", re.IGNORECASE)

def load_owners():
    global temp_owners
    try:
        with open("owners.json", "r") as f:
            data = json.load(f)
            temp_owners = {int(k): datetime.fromisoformat(v) for k, v in data.items()}
    except: pass

def save_owners():
    data = {k: v.isoformat() for k, v in temp_owners.items()}
    with open("owners.json", "w") as f:
        json.dump(data, f)
load_owners()

# ════════════════════════════════════════════════════════
#  🛡️ HELPERS
# ════════════════════════════════════════════════════════
def is_owner(user_id):
    if user_id == OWNER_ID or user_id in logged_in: return True
    if user_id in temp_owners:
        if datetime.now() < temp_owners[user_id]: return True
        else:
            del temp_owners[user_id]
            save_owners()
    return False

async def check_joined(user_id, context) -> bool:
    try:
        if (await context.bot.get_chat_member(CHANNEL_ID, user_id)).status in ['left', 'kicked']: return False
        if (await context.bot.get_chat_member(GROUP_ID, user_id)).status in ['left', 'kicked']: return False
        return True
    except: return True 

async def is_admin(update, context) -> bool:
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ['administrator', 'creator']
    except: return False

async def get_target(update, context):
    if update.message.reply_to_message: return update.message.reply_to_message.from_user
    if context.args:
        try: return await context.bot.get_chat(context.args[0] if context.args[0].startswith("@") else int(context.args[0]))
        except: pass
    return None

# ════════════════════════════════════════════════════════
#  🏠 MENUS
# ════════════════════════════════════════════════════════
def get_main_user_menu(bot_username, user_name, user_id):
    kb_list = [
        [InlineKeyboardButton("📖 GROUP COMMANDS (Help)", callback_data="help_group")],
        [InlineKeyboardButton("🧰 EXTRA STUFF (Premium/Store)", callback_data="extra_stuff_menu")],
        [InlineKeyboardButton("➕ ADD ME TO GROUP", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("🤖 Chat Support (Coming Soon)", url=NOVA_BASIC_LINK)],
        [InlineKeyboardButton("⚠️ Report an Issue", callback_data="report_issue")]
    ]
    if user_id in premium_users and datetime.now() < premium_users[user_id]["expiry"]:
        kb_list.insert(0, [InlineKeyboardButton("👑 MY PREMIUM PANEL", callback_data="premium_panel")])
        
    if is_owner(user_id):
        kb_list.insert(0, [InlineKeyboardButton("🔐 MAIN OWNER DASHBOARD", callback_data="btn_main_owner_dash")])
        
    text = f"🌹 **CYRUS ERA BOT**\nNamaste {user_name}!\n\nMain ek powerful Group Management Bot hoon. Kisi bhi help ke liye support par click karein."
    return text, InlineKeyboardMarkup(kb_list)

def get_extra_stuff_menu(user_id):
    kb_list = [
        [InlineKeyboardButton("💎 PREMIUM AUTO-POST", callback_data="view_premium")],
        [InlineKeyboardButton("🛍️ VISIT STORE", callback_data="view_store")]
    ]
    if user_id in premium_users and datetime.now() < premium_users[user_id]["expiry"]:
        kb_list.insert(0, [InlineKeyboardButton("👑 MY PREMIUM PANEL", callback_data="premium_panel")])
    if is_owner(user_id):
        kb_list.insert(0, [InlineKeyboardButton("🔐 EXTRA STUFF OWNER PANEL", callback_data="btn_extra_owner_dash")])
        
    kb_list.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")])
    return "🧰 **EXTRA STUFF MENU**\n\nYahan se Premium aur Store ka use karein.", InlineKeyboardMarkup(kb_list)

def get_main_owner_dashboard():
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 BROADCAST MESSAGE", callback_data="btn_broadcast")],
        [InlineKeyboardButton("👥 TEAM MANAGER", callback_data="btn_team_info")],
        [InlineKeyboardButton("🔄 RESTART BOT", callback_data="btn_restart")],
        [InlineKeyboardButton("🔙 Exit to Main Menu", callback_data="back_to_main")]
    ])
    return "👑 **MAIN OWNER DASHBOARD**\nBot settings manage karein:", kb

def get_extra_owner_dashboard():
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ STORE MANAGER", callback_data="btn_store_manager")],
        [InlineKeyboardButton("💎 PREMIUM USERS", callback_data="btn_premium_list")],
        [InlineKeyboardButton("⚙️ MANAGE CUSTOM COMMANDS", callback_data="btn_custom_cmds")],
        [InlineKeyboardButton("🔙 Back to Extra Stuff", callback_data="extra_stuff_menu")]
    ])
    return "🔐 **EXTRA STUFF OWNER PANEL**\nStore aur Premium manage karein:", kb

def get_admin_panel_menu():
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔨 Moderation", callback_data="adm_mod"), InlineKeyboardButton("⚠️ Warn System", callback_data="adm_warn")],
        [InlineKeyboardButton("📝 Notes & Filters", callback_data="adm_notes"), InlineKeyboardButton("👋 Welcome/Goodbye", callback_data="adm_welcome")],
        [InlineKeyboardButton("🔒 Locks & Security", callback_data="adm_locks"), InlineKeyboardButton("🛠️ Utilities", callback_data="adm_util")]
    ])
    return "👮 **GROUP ADMIN PANEL**\nGroup manage karne ke liye option chunein:", kb

# ════════════════════════════════════════════════════════
#  👑 START, HELP, CANCEL & ISSUE
# ════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot_users.add(user.id) 
    
    login_states.pop(user.id, None)
    payment_steps.pop(user.id, None)
    pending_payments.pop(user.id, None)
    pending_orders.pop(user.id, None)
    schedule_states.pop(user.id, None)
    command_states.pop(user.id, None)
    issue_states.discard(user.id)
    admin_reply_states.pop(user.id, None)
    
    if is_owner(user.id):
        if user.id == OWNER_ID and user.id not in logged_in:
            await update.message.reply_text("🔐 **Owner Login**\nKripya apna Username darj karein:")
            login_states[user.id] = "waiting_for_user"
            return
        dash_text, dash_kb = get_main_owner_dashboard()
        await update.message.reply_text(dash_text, reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
        return

    if not await check_joined(user.id, context):
        text = "🌹 **Welcome!** Kripya humare Channel aur Group join karein."
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 JOIN CHANNEL (1)", url=CHANNEL_LINK), InlineKeyboardButton("💬 JOIN GROUP (2)", url=GROUP_LINK)],
            [InlineKeyboardButton("✅ I HAVE JOINED (Verify)", callback_data="verify_join")]
        ])
        return await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    text, kb = get_main_user_menu(context.bot.username, user.first_name, user.id)
    await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    login_states.pop(user_id, None)
    payment_steps.pop(user_id, None)
    pending_payments.pop(user_id, None)
    pending_orders.pop(user_id, None)
    schedule_states.pop(user_id, None)
    command_states.pop(user_id, None)
    owner_states.pop(user_id, None)
    issue_states.discard(user_id)
    admin_reply_states.pop(user_id, None)
    
    await update.message.reply_text("🔄 **Action Cancelled.**")
    if is_owner(user_id):
        dash_text, dash_kb = get_main_owner_dashboard()
        await update.message.reply_text(dash_text, reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
    else:
        text, kb = get_main_user_menu(context.bot.username, update.effective_user.first_name, user_id)
        await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def issue_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    issue_states.add(update.effective_user.id)
    await update.message.reply_text("⚠️ **Report an Issue**\n\nKripya apna issue type karein. Owner ko message chala jayega.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="back_to_main")]]))

async def help_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛡️ **GROUP MANAGEMENT COMMANDS** 🛡️\n\n"
        "👮 **Admin Commands:**\n"
        "• `/adminpanel` — Admin panel kholne ke liye\n"
        "• `/ban` `/unban` `/kick` — User manage karein\n"
        "• `/mute` `/unmute` — Mute manage karein\n"
        "• `/warn` `/unwarn` `/warns` — Warn system\n"
        "• `/lock` `/unlock` `/lockall` `/unlockall` — Chat band/chalu\n\n"
        "📝 **Notes & Filters:**\n"
        "• `/save` `/get` `/notes` — Notes save karein\n"
        "• `/filter` — Auto-reply set karein\n\n"
        "ℹ️ **Utility:**\n"
        "• `/id` `/info` `/stats`"
    )
    if update.callback_query:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]])
        await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else: await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ════════════════════════════════════════════════════════
#  👮 GROUP ADMIN PANEL & ROSE COMMANDS
# ════════════════════════════════════════════════════════
async def adminpanel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return await update.message.reply_text("❌ Sirf group me kaam karti hai.")
    if not await is_admin(update, context): return await update.message.reply_text("❌ Sirf admins.")
    text, kb = get_admin_panel_menu()
    await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    t = await get_target(update, context)
    if not t: return await update.message.reply_text("⚠️ Reply karo!")
    if is_owner(t.id): return await update.message.reply_text("❌ Owner ko ban nahi kar sakte!")
    await context.bot.ban_chat_member(update.effective_chat.id, t.id)
    await update.message.reply_text(f"🚫 {t.first_name} ban ho gaya!")

async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    t = await get_target(update, context)
    if not t: return
    await context.bot.ban_chat_member(update.effective_chat.id, t.id)
    await context.bot.unban_chat_member(update.effective_chat.id, t.id)
    await update.message.reply_text(f"👢 {t.first_name} kick ho gaya!")

async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    t = await get_target(update, context)
    if not t: return
    await context.bot.restrict_chat_member(update.effective_chat.id, t.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🔇 {t.first_name} mute ho gaya!")

async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    t = await get_target(update, context)
    if not t: return
    await context.bot.restrict_chat_member(update.effective_chat.id, t.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await update.message.reply_text(f"🔊 {t.first_name} unmute ho gaya!")

async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    t = await get_target(update, context)
    if not t: return
    if is_owner(t.id): return await update.message.reply_text("❌ Owner ko warn nahi de sakte!")
    cid = update.effective_chat.id
    warns_db.setdefault(cid, {})
    warns_db[cid][t.id] = warns_db[cid].get(t.id, 0) + 1
    if warns_db[cid][t.id] >= MAX_WARNS:
        await context.bot.ban_chat_member(cid, t.id)
        warns_db[cid][t.id] = 0
        await update.message.reply_text(f"⛔ {t.first_name} ko {MAX_WARNS} warns mile — BAN!")
    else: await update.message.reply_text(f"⚠️ Warn {warns_db[cid][t.id]}/{MAX_WARNS} diya {t.first_name} ko.")

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text("🔒 Chat lock ho gaya!")

async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await update.message.reply_text("🔓 Chat unlock ho gaya!")

async def lockall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False, can_add_web_page_previews=False, can_send_polls=False))
    await update.message.reply_text("🔒🔒 Sab kuch lock ho gaya!")

async def unlockall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True, can_send_polls=True))
    await update.message.reply_text("🔓 Sab kuch unlock ho gaya!")

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context) or len(context.args) < 2: return
    notes_db.setdefault(update.effective_chat.id, {})[context.args[0].lower()] = " ".join(context.args[1:])
    await update.message.reply_text(f"✅ Note `{context.args[0]}` save ho gaya!")

async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    note = notes_db.get(update.effective_chat.id, {}).get(context.args[0].lower())
    if note: await update.message.reply_text(f"📝 *{context.args[0]}*\n\n{note}", parse_mode=ParseMode.MARKDOWN)
    else: await update.message.reply_text(f"❌ Note nahi mila!")

async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = notes_db.get(update.effective_chat.id, {})
    if not notes: return await update.message.reply_text("📭 Koi note nahi!")
    await update.message.reply_text("📝 *Notes:*\n\n" + "\n".join([f"• `#{k}`" for k in notes]), parse_mode=ParseMode.MARKDOWN)

async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context) or len(context.args) < 2: return
    filters_db.setdefault(update.effective_chat.id, {})[context.args[0].lower()] = " ".join(context.args[1:])
    await update.message.reply_text(f"✅ Filter `{context.args[0]}` add ho gaya!")

async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text: return
    for kw, reply in filters_db.get(update.effective_chat.id, {}).items():
        if kw in msg.text.lower():
            await msg.reply_text(reply)
            break

async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context) or not context.args: return
    welcome_db[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("✅ Welcome set!")

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f"👤 ID: `{u.id}`\n💬 Chat ID: `{update.effective_chat.id}`", parse_mode=ParseMode.MARKDOWN)

# ════════════════════════════════════════════════════════
#  💎 PREMIUM & STORE
# ════════════════════════════════════════════════════════
async def view_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    text = "💎 **CYRUS ERA PREMIUM** 💎\n\n🎁 **24 Hours Free Trial**\n₹149 / Weekly\n₹699 / Monthly\n₹1099 / 3 Months\n\nNiche se plan chunein:"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Start 24H Free Trial", callback_data="premium_trial")],
        [InlineKeyboardButton("💳 Buy Weekly - ₹149", callback_data="buy_149")],
        [InlineKeyboardButton("💳 Buy Monthly - ₹699", callback_data="buy_699")],
        [InlineKeyboardButton("💳 Buy 3 Months - ₹1099", callback_data="buy_1099")],
        [InlineKeyboardButton("🔙 Back to Extra Stuff", callback_data="extra_stuff_menu")]
    ])
    if q: await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else: await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def view_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not store_products: return await q.message.edit_text("🛍️ Store khali hai.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="extra_stuff_menu")]]))
    text = "🛍️ **CYRUS ERA STORE**\n\n"
    kb_buttons = []
    for pid, prod in store_products.items():
        if prod["file_id"]:
            text += f"🔹 **{prod['name']}**\n💰 Price: ₹{prod['price']}\n\n"
            kb_buttons.append([InlineKeyboardButton(f"Buy {prod['name']} (₹{prod['price']})", callback_data=f"buy_prod_{pid}")])
    kb_buttons.append([InlineKeyboardButton("🔙 Back to Extra Stuff", callback_data="extra_stuff_menu")])
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb_buttons), parse_mode=ParseMode.MARKDOWN)

async def add_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    full_text = " ".join(context.args)
    if not full_text: return await update.message.reply_text("⚠️ Format: `/addproduct [Name] [Price]`", parse_mode=ParseMode.MARKDOWN)
    parts = full_text.rsplit(" ", 1)
    if len(parts) < 2: return await update.message.reply_text("⚠️ Price dalein. Example: `/addproduct Instagram Method 99`", parse_mode=ParseMode.MARKDOWN)
        
    name = parts[0].strip()
    price = parts[1].strip().replace("₹", "")
    pid = str(int(time.time()))[-4:] 
    store_products[pid] = {"name": name, "price": price, "file_id": None}
    owner_states[update.effective_user.id] = {"action": "upload_file", "pid": pid}
    await update.message.reply_text(f"✅ Product **{name}** (₹{price}) create ho gaya. Ab file bhejein.")

# ════════════════════════════════════════════════════════
#  📝 TEXT & MEDIA HANDLERS
# ════════════════════════════════════════════════════════
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # ADMIN REPLY TO ISSUE
    if is_owner(user_id) and user_id in admin_reply_states:
        target_id = admin_reply_states.pop(user_id)
        try:
            await context.bot.send_message(target_id, f"📩 **Reply from Admin:**\n\n{text}", parse_mode=ParseMode.MARKDOWN)
            await update.message.reply_text("✅ Reply user ko bhej diya gaya hai.")
        except: await update.message.reply_text("❌ User ko message nahi bhej paye.")
        return

    # BROADCAST
    if is_owner(user_id) and owner_states.get(user_id) == "waiting_for_broadcast":
        if text == "/cancel":
            del owner_states[user_id]
            dash_text, dash_kb = get_main_owner_dashboard()
            return await update.message.reply_text(f"❌ Cancelled.\n\n{dash_text}", reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
        del owner_states[user_id]
        msg = await update.message.reply_text("⏳ Broadcasting...")
        targets = set(list(bot_users) + list(premium_users.keys()) + list(bot_groups))
        success, fail = 0, 0
        for cid in targets:
            try: 
                await update.message.copy(chat_id=cid)
                success += 1
                await asyncio.sleep(0.05)
            except: fail += 1
        dash_text, dash_kb = get_main_owner_dashboard()
        await msg.edit_text(f"✅ **Complete!**\n✅ Sent: {success}\n❌ Failed: {fail}\n\n{dash_text}", reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
        return

    # LOGIN
    state = login_states.get(user_id)
    if state == "waiting_for_user":
        if text == OWNER_USERNAME:
            login_states[user_id] = "waiting_for_pass"
            await update.message.reply_text("✅ Ab Password darj karein:")
        else: del login_states[user_id]; await update.message.reply_text("❌ Galat.")
        return
    elif state == "waiting_for_pass":
        if text == OWNER_PASS:
            del login_states[user_id]; logged_in.add(user_id) 
            dash_text, dash_kb = get_main_owner_dashboard()
            await update.message.reply_text(dash_text, reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
        else: del login_states[user_id]; await update.message.reply_text("❌ Galat.")
        return

    # REPORT ISSUE
    if user_id in issue_states:
        issue_states.discard(user_id)
        await update.message.reply_text("✅ Aapka issue Owner ko bhej diya gaya hai.")
        owner_msg = f"🚨 **New Issue!**\n👤 {update.effective_user.first_name} (`{user_id}`)\n💬 Issue: {text}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Reply to User", callback_data=f"reply_issue_{user_id}")]])
        await context.bot.send_message(OWNER_ID, owner_msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        await update.message.forward(OWNER_ID)
        return

    # CUSTOM COMMANDS SETUP
    if is_owner(user_id) and user_id in command_states:
        state = command_states[user_id]
        if state["step"] == "waiting_for_name":
            if not text.startswith("/"): return await update.message.reply_text("❌ `/` se shuru karein.")
            command_states[user_id] = {"step": "waiting_for_reply", "cmd": text.split()[0].lower()}
            await update.message.reply_text("✅ Reply bhejein (Text/Photo/Video/Doc):")
            return
        elif state["step"] == "waiting_for_reply":
            cmd = state["cmd"]
            custom_commands[cmd] = {"type": "text", "content": text}
            del command_states[user_id]
            await update.message.reply_text(f"✅ `{cmd}` updated!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_custom_cmds")]]))
            return

    # CUSTOM COMMAND TRIGGER
    if text.startswith("/"):
        cmd = text.split()[0].lower()
        if cmd in custom_commands:
            c_data = custom_commands[cmd]
            if c_data["type"] == "text": return await update.message.reply_text(c_data["content"], parse_mode=ParseMode.MARKDOWN)
            elif c_data["type"] == "photo": return await update.message.reply_photo(c_data["content"])
            elif c_data["type"] == "video": return await update.message.reply_video(c_data["content"])
            elif c_data["type"] == "document": return await update.message.reply_document(c_data["content"])

    # AUTO-REPLY (GREETINGS)
    text_lower = text.lower().strip()
    if text_lower in default_replies:
        return await update.message.reply_text(default_replies[text_lower])

    # PREMIUM CHAT ADD
    if payment_steps.get(user_id) == "waiting_for_new_chat":
        try:
            chat = await context.bot.get_chat(text)
            premium_users[user_id]["chats"].append(chat.id)
            del payment_steps[user_id]
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Panel", callback_data="premium_panel")]])
            await update.message.reply_text(f"✅ **{chat.title}** add ho gaya!", reply_markup=kb)
        except: await update.message.reply_text("❌ Invalid ID.")
        return

    # UTR
    if payment_steps.get(user_id) == "waiting_for_utr":
        utr = text; payment = pending_payments[user_id]; del payment_steps[user_id]
        await update.message.reply_text("⏳ Details bhej di gayi.")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")],
            [InlineKeyboardButton("💬 Reply / Clarify", callback_data=f"reply_issue_{user_id}")]
        ])
        await context.bot.send_message(OWNER_ID, f"🔔 **Payment!**\n👤 {payment['name']}\n📦 {payment['plan']}\n🧾 UTR: `{utr}`", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_photo(OWNER_ID, photo=payment["screenshot"])
        return

    # SCHEDULE
    sched = schedule_states.get(user_id)
    if sched:
        if sched["step"] == "time":
            sched["time"] = text; sched["step"] = "message"
            await update.message.reply_text("✅ Time saved. Message type karein:")
        elif sched["step"] == "message":
            msg_text, target_cid, time_str = text, sched["cid"], sched["time"]
            del schedule_states[user_id]
            delay = 0
            if time_str.endswith("h"): delay = int(time_str[:-1]) * 3600
            elif time_str.endswith("m"): delay = int(time_str[:-1]) * 60
            elif ":" in time_str:
                target = datetime.strptime(time_str, "%H:%M").time()
                now = datetime.now()
                target_dt = datetime.combine(now.date(), target)
                if target_dt < now: target_dt += timedelta(days=1)
                delay = (target_dt - now).total_seconds()
            else: return await update.message.reply_text("❌ Galat time format.")
            context.job_queue.run_once(send_scheduled_msg, when=delay, data={"chat_id": target_cid, "text": msg_text})
            await update.message.reply_text("✅ Scheduled!")
        return

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # CUSTOM COMMAND MEDIA
    if is_owner(user_id) and user_id in command_states:
        state = command_states[user_id]
        if state["step"] == "waiting_for_reply":
            cmd = state["cmd"]
            if update.message.photo: custom_commands[cmd] = {"type": "photo", "content": update.message.photo[-1].file_id}
            elif update.message.video: custom_commands[cmd] = {"type": "video", "content": update.message.video.file_id}
            elif update.message.document: custom_commands[cmd] = {"type": "document", "content": update.message.document.file_id}
            else: return await update.message.reply_text("⚠️ Sirf Photo, Video ya Document.")
            del command_states[user_id]
            return await update.message.reply_text(f"✅ Media saved for `{cmd}`!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_custom_cmds")]]))

    # OWNER PRODUCT UPLOAD
    if is_owner(user_id) and owner_states.get(user_id, {}).get("action") == "upload_file":
        if update.message.document:
            pid = owner_states[user_id]["pid"]
            store_products[pid]["file_id"] = update.message.document.file_id
            del owner_states[user_id]
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]])
            await update.message.reply_text(f"✅ File Uploaded! Product Live.", reply_markup=kb)
        else: await update.message.reply_text("⚠️ Kripya Document bhejein.")
        return

    # USER SCREENSHOTS
    if update.message.photo or update.message.document:
        if payment_steps.get(user_id) == "waiting_for_screenshot":
            pending_payments[user_id]["screenshot"] = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
            payment_steps[user_id] = "waiting_for_utr"
            await update.message.reply_text("✅ Screenshot received! **UTR** type karein.")
            return
        elif user_id in pending_orders:
            pid = pending_orders[user_id]
            prod = store_products.get(pid)
            await update.message.reply_text("✅ Sent to Owner!")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"appr_store_{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"rej_store_{user_id}")]])
            await context.bot.send_message(OWNER_ID, f"🔔 **Store Order!**\nBuyer: `{user_id}`\nProd: {prod['name']}", reply_markup=kb)
            await update.message.forward(OWNER_ID)
            del pending_orders[user_id]

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            bot_groups.add(update.effective_chat.id)
            await update.message.reply_text("🌹 **Thank you for adding me!** Mujhe Admin banayein taaki main group manage kar saku.")
            continue
            
        if member.is_bot: continue
        w = welcome_db.get(update.effective_chat.id, "🌹 Welcome to *{chat}*, [{name}](tg://user?id={id})!")
        await update.message.reply_text(w.replace("{name}", member.first_name).replace("{chat}", update.effective_chat.title or "group").replace("{id}", str(member.id)), parse_mode=ParseMode.MARKDOWN)

async def left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message.left_chat_member
    if m and not m.is_bot:
        g = goodbye_db.get(update.effective_chat.id, "👋 [{name}](tg://user?id={id}) ne group chod diya. Hum unhe miss karenge!")
        await update.message.reply_text(g.replace("{name}", m.first_name).replace("{id}", str(m.id)), parse_mode=ParseMode.MARKDOWN)

async def send_scheduled_msg(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try: await context.bot.send_message(chat_id=job.data["chat_id"], text=job.data["text"])
    except: pass

# ════════════════════════════════════════════════════════
#  🎛️ BUTTON HANDLER
# ════════════════════════════════════════════════════════
async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = q.from_user.id

    if data == "back_to_main":
        text, kb = get_main_user_menu(context.bot.username, q.from_user.first_name, q.from_user.id) 
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "help_group": await help_group(update, context)
    elif data == "extra_stuff_menu": 
        text, kb = get_extra_stuff_menu(user_id)
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "report_issue":
        issue_states.add(user_id)
        await q.message.edit_text("⚠️ **Report Issue**\n\nApna issue type karein. Owner ko jayega.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="back_to_main")]]))

    # OWNER DASHBOARDS
    elif data == "btn_main_owner_dash":
        if not is_owner(user_id): return
        dash_text, dash_kb = get_main_owner_dashboard()
        await q.message.edit_text(dash_text, reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "btn_extra_owner_dash":
        if not is_owner(user_id): return
        dash_text, dash_kb = get_extra_owner_dashboard()
        await q.message.edit_text(dash_text, reply_markup=dash_kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "btn_broadcast":
        if not is_owner(user_id): return
        owner_states[user_id] = "waiting_for_broadcast"
        await q.message.edit_text("📢 **Broadcast Mode**\nMessage bhejein. Cancel: `/cancel`")

    # ADMIN PANEL
    elif data == "adm_mod": await q.message.edit_text("🔨 **Moderation**\n`/ban` `/kick` `/mute` `/unmute`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adminpanel_back")]]))
    elif data == "adm_warn": await q.message.edit_text("⚠️ **Warn**\n`/warn` `/warns` `/unwarn`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adminpanel_back")]]))
    elif data == "adm_notes": await q.message.edit_text("📝 **Notes & Filters**\n`/save` `/get` `/notes` `/filter`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adminpanel_back")]]))
    elif data == "adm_welcome": await q.message.edit_text("👋 **Welcome/Goodbye**\n`/setwelcome` `/setgoodbye`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adminpanel_back")]]))
    elif data == "adm_locks": await q.message.edit_text("🔒 **Security**\n`/lock` `/unlock` `/lockall` `/unlockall`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adminpanel_back")]]))
    elif data == "adm_util": await q.message.edit_text("🛠️ **Utilities**\n`/id` `/info` `/stats`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adminpanel_back")]]))
    elif data == "adminpanel_back":
        text, kb = get_admin_panel_menu()
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    # EXTRA OWNER
    elif data == "btn_store_manager": await q.message.edit_text("🛍️ **Store**\n`/addproduct [Name] [Price]`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_extra_owner_dash")]]))
    elif data == "btn_premium_list":
        if not is_owner(user_id): return
        text = "💎 **Premium Users:**\n\n" + "".join([f"• `{uid}` - {pdata['plan']}\n" for uid, pdata in premium_users.items()])
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_extra_owner_dash")]]), parse_mode=ParseMode.MARKDOWN)
    elif data == "btn_team_info": await q.message.edit_text("👥 **Team**\n`/addteam 123456789`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_main_owner_dash")]]))
    elif data == "btn_restart":
        if not is_owner(user_id): return
        await q.message.edit_text("🔄 Restarting...")
        await asyncio.sleep(2)
        os.execl(sys.executable, sys.executable, *sys.argv)

    # CUSTOM COMMANDS MANAGER
    elif data == "btn_custom_cmds":
        if not is_owner(user_id): return
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add New Command", callback_data="cmd_add")],
            [InlineKeyboardButton("📋 Edit / Delete Commands", callback_data="cmd_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="btn_extra_owner_dash")]
        ])
        await q.message.edit_text("⚙️ **Custom Commands Manager**\n\nYahan se apne commands manage karein.", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "cmd_add":
        command_states[user_id] = {"step": "waiting_for_name"}
        await q.message.edit_text("➕ **Add New Command**\n\nNaya command type karein (jaise `/hello`):")
    elif data == "cmd_list":
        if not custom_commands: return await q.answer("Koi command nahi.", show_alert=True)
        kb_buttons = [[InlineKeyboardButton(f"⚙️ {cmd}", callback_data=f"cmd_edit_{cmd}")] for cmd in custom_commands.keys()]
        kb_buttons.append([InlineKeyboardButton("🔙 Back", callback_data="btn_custom_cmds")])
        await q.message.edit_text("📋 **Commands:**\nEdit/Delete ke liye click karein:", reply_markup=InlineKeyboardMarkup(kb_buttons), parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("cmd_edit_"):
        cmd_name = data.split("_")[2]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Reply", callback_data=f"cmd_update_{cmd_name}")],
            [InlineKeyboardButton("🗑️ Delete Command", callback_data=f"cmd_delete_{cmd_name}")],
            [InlineKeyboardButton("🔙 Back", callback_data="cmd_list")]
        ])
        await q.message.edit_text(f"⚙️ **Command:** `{cmd_name}`\n\nKya karna chahte hain?", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("cmd_update_"):
        cmd_name = data.split("_")[2]
        command_states[user_id] = {"step": "waiting_for_reply", "cmd": cmd_name}
        await q.message.edit_text(f"✏️ **Editing `{cmd_name}`**\n\nNaya Reply bhejein (Text/Photo/Video/Doc):")
    elif data.startswith("cmd_delete_"):
        cmd_name = data.split("_")[2]
        if cmd_name in custom_commands:
            del custom_commands[cmd_name]
            await q.message.edit_text(f"🗑️ Deleted `{cmd_name}`!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to List", callback_data="cmd_list")]]))

    # PREMIUM PANEL
    elif data == "premium_panel":
        user_prem = premium_users.get(user_id)
        if not is_owner(user_id) and not user_prem: return await q.answer("Premium nahi hai.", show_alert=True)
        exp = premium_users[user_id]['expiry'].strftime('%d-%b-%Y') if user_prem else "Lifetime"
        plan = premium_users[user_id]['plan'] if user_prem else "Owner"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🕒 Auto-Post (Schedule Msg)", callback_data="prem_schedule_start")],
            [InlineKeyboardButton("➕ Add Chat for Auto-Post", callback_data="prem_add_chat")],
            [InlineKeyboardButton("🚀 Chat with Nova Pro (Coming Soon)", url=NOVA_PRO_LINK)],
            [InlineKeyboardButton("🔙 Back to Extra Stuff", callback_data="extra_stuff_menu")]
        ])
        await q.message.edit_text(f"👑 **MY PREMIUM PANEL**\n\nPlan: {plan}\nExpires: {exp}", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "view_premium": await view_premium(update, context)
    elif data == "premium_trial":
        if user_id in trial_used: return await q.answer("❌ Trial used.", show_alert=True)
        trial_used.add(user_id)
        premium_users[user_id] = {"plan": "Trial (24H)", "expiry": datetime.now() + timedelta(hours=24), "chats": []}
        
        exp = premium_users[user_id]['expiry'].strftime('%d-%b-%Y %H:%M')
        text = f"🎉 **Trial Activated!**\n\nPlan: **Trial (24H)**\nExpires: **{exp}**"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🕒 Auto-Post", callback_data="prem_schedule_start")],
            [InlineKeyboardButton("➕ Add Chat", callback_data="prem_add_chat")],
            [InlineKeyboardButton("🔙 Back to Extra Stuff", callback_data="extra_stuff_menu")]
        ])
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    
    # BUYING
    elif data.startswith("buy_"):
        price = data.split("_")[1]
        plan_name = "Weekly" if price == "149" else ("Monthly" if price == "699" else "3 Months")
        pending_payments[user_id] = {"plan": plan_name, "price": price, "name": q.from_user.first_name}
        payment_steps[user_id] = "waiting_for_screenshot"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Pay Here", url=PAYMENT_CHANNEL)], [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]])
        await q.message.edit_text(f"🧾 **Payment**\nPlan: **{plan_name}**\n\nScreenshot bhejein.", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    
    # BUYING STORE
    elif data.startswith("buy_prod_"):
        pid = data.split("_")[2]
        prod = store_products.get(pid)
        if not prod: return await q.answer("❌ Not found.", show_alert=True)
        pending_orders[user_id] = pid
        text = f"🛒 **Order**\nProduct: **{prod['name']}**\nPrice: **₹{prod['price']}**\n\nScreenshot bhejein."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Pay Here", url=PAYMENT_CHANNEL)], [InlineKeyboardButton("❌ Cancel", callback_data="view_store")]])
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    elif data == "cancel_payment":
        payment_steps.pop(user_id, None); pending_payments.pop(user_id, None)
        text, kb = get_extra_stuff_menu(user_id)
        await q.message.edit_text(f"❌ Cancelled.\n\n{text}", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    elif data == "view_store": await view_store(update, context)
    elif data == "verify_join":
        if await check_joined(user_id, context):
            text, kb = get_main_user_menu(context.bot.username, q.from_user.first_name, q.from_user.id)
            await q.message.edit_text(f"✅ Verified!\n\n{text}", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else: await q.answer("❌ Join nahi kiya.", show_alert=True)

    # ADMIN REPLY
    elif data.startswith("reply_issue_"):
        if not is_owner(user_id): return
        target_id = int(data.split("_")[2])
        admin_reply_states[user_id] = target_id
        await q.message.reply_text(f"✍️ **Reply to User (`{target_id}`)**\n\nKripya wo message type karein jo aap user ko bhejna chahte hain. (Cancel: /cancel)")

    # APPROVALS
    elif data.startswith("approve_"):
        if not is_owner(user_id): return
        buyer_id = int(data.split("_")[1])
        pay = pending_payments.get(buyer_id)
        if not pay: return
        days = 7 if pay["plan"] == "Weekly" else (30 if pay["plan"] == "Monthly" else 90)
        premium_users[buyer_id] = {"plan": pay["plan"], "expiry": datetime.now() + timedelta(days=days), "chats": []}
        exp = premium_users[buyer_id]['expiry'].strftime('%d-%b-%Y %H:%M')
        text = f"🎉 **Payment Approved!**\nPlan: **{pay['plan']}**\nExpires: **{exp}**"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🕒 Auto-Post", callback_data="prem_schedule_start")],
            [InlineKeyboardButton("➕ Add Chat", callback_data="prem_add_chat")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ])
        await context.bot.send_message(buyer_id, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        await q.message.edit_text("✅ Approved!")
        del pending_payments[buyer_id]

    elif data.startswith("reject_"):
        if not is_owner(user_id): return
        buyer_id = int(data.split("_")[1])
        if buyer_id in pending_payments:
            del pending_payments[buyer_id]
            await context.bot.send_message(buyer_id, "❌ Rejected.")
            await q.message.edit_text("❌ Rejected.")

    # STORE APPROVALS
    elif data.startswith("appr_store_"):
        if not is_owner(user_id): return
        buyer_id = int(data.split("_")[2])
        pid = pending_orders.get(buyer_id)
        if not pid: return
        prod = store_products[pid]
        try:
            await context.bot.send_document(chat_id=buyer_id, document=prod["file_id"], caption=f"✅ **Approved!**\nFile: {prod['name']}")
            await q.message.edit_text("✅ File bhej di gayi!")
            del pending_orders[buyer_id]
        except: await q.message.reply_text("❌ Error.")
    elif data.startswith("rej_store_"):
        if not is_owner(user_id): return
        buyer_id = int(data.split("_")[2])
        if buyer_id in pending_orders:
            del pending_orders[buyer_id]
            await context.bot.send_message(buyer_id, "❌ Rejected.")
            await q.message.edit_text("❌ Rejected.")

    # PREMIUM SCHEDULE
    elif data == "prem_add_chat":
        payment_steps[user_id] = "waiting_for_new_chat"
        await q.message.edit_text("➕ **Add Chat**\nGroup/Channel ID ya Username bhejein:")
    elif data == "prem_schedule_start":
        user_chats = premium_users.get(user_id, {}).get("chats", [])
        if not user_chats: return await q.answer("❌ Pehle 'Add Chat' karein.", show_alert=True)
        if len(user_chats) == 1:
            schedule_states[user_id] = {"step": "time", "cid": user_chats[0]}
            await q.message.edit_text(f"🕒 **Schedule**\nTarget: `{user_chats[0]}`\n\n**Time** bhejein (`10:00`, `2h`):")
        else:
            kb_btns = [[InlineKeyboardButton(f"Chat {cid}", callback_data=f"prem_target_{cid}")] for cid in user_chats]
            await q.message.edit_text("🕒 Target chat:", reply_markup=InlineKeyboardMarkup(kb_btns))
    elif data.startswith("prem_target_"):
        cid = data.split("_")[2]
        schedule_states[user_id] = {"step": "time", "cid": cid}
        await q.message.edit_text(f"🕒 **Schedule**\nTarget: `{cid}`\n\n**Time** bhejein:")

# ════════════════════════════════════════════════════════
#  🚀 MAIN
# ════════════════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_group))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("issue", issue_cmd))
    app.add_handler(CommandHandler("adminpanel", adminpanel_cmd))
    
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("kick", kick_cmd))
    app.add_handler(CommandHandler("mute", mute_cmd))
    app.add_handler(CommandHandler("unmute", unmute_cmd))
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("unlock", unlock_cmd))
    app.add_handler(CommandHandler("lockall", lockall_cmd))
    app.add_handler(CommandHandler("unlockall", unlockall_cmd))
    app.add_handler(CommandHandler("save", save_note))
    app.add_handler(CommandHandler("get", get_note))
    app.add_handler(CommandHandler("notes", list_notes))
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(CommandHandler("id", id_cmd))

    app.add_handler(CommandHandler("premium", view_premium))
    app.add_handler(CommandHandler("addproduct", add_product_cmd))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_filters), group=1)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member), group=2)
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member), group=2)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=0)
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media), group=3)
    app.add_handler(CallbackQueryHandler(btn_handler))

    print("🌹 ULTIMATE ROSE + CYRUS BOT RUNNING!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
