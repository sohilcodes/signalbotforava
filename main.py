"""
╔══════════════════════════════════════════════════════════════╗
║         ZENITH TRADER BOT - Polling Mode (Render)           ║
╚══════════════════════════════════════════════════════════════╝

Deploy on Render:
  - Build Command : pip install -r requirements.txt
  - Start Command : python ava.py
  - Env Variable  : BOT_TOKEN = <your token>
"""

import logging
import random
import asyncio
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

VALID_LICENSE_KEYS = [
    "ZENITH-1234-ABCD",
    "ZENITH-5678-EFGH",
    "ZENITH-9999-ZZZZ",
    "ZENITH-VIP1-2024",
]

ASSETS = [
    "EUR/USD (OTC)",
    "GBP/USD (OTC)",
    "NZD/CHF (OTC)",
    "AUD/JPY (OTC)",
    "USD/CAD (OTC)",
]

TIMEFRAMES = ["15s", "30s", "1m", "5m", "15m"]

# ──────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  USER SESSIONS (in-memory)
# ──────────────────────────────────────────────

user_sessions: dict[int, dict] = {}

def get_session(user_id: int) -> dict:
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "licensed": False,
            "asset": ASSETS[0],
            "timeframe": TIMEFRAMES[2],  # default 1m
        }
    return user_sessions[user_id]

# ──────────────────────────────────────────────
#  KEYBOARDS
# ──────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Select Asset", callback_data="menu_asset")],
        [InlineKeyboardButton("⏱ Expiry Timeframe", callback_data="menu_timeframe")],
        [InlineKeyboardButton("🚀 GENERATE SIGNAL 🚀", callback_data="generate_signal")],
    ])

def asset_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(a, callback_data=f"asset_{a}")] for a in ASSETS]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)

def timeframe_keyboard() -> InlineKeyboardMarkup:
    tf_buttons = [InlineKeyboardButton(t, callback_data=f"tf_{t}") for t in TIMEFRAMES]
    rows = [tf_buttons[i:i+3] for i in range(0, len(tf_buttons), 3)]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)

def signal_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Change Asset", callback_data="menu_asset"),
            InlineKeyboardButton("⏱ Change Expiry", callback_data="menu_timeframe"),
        ],
        [InlineKeyboardButton("🚀 NEXT SIGNAL 🚀", callback_data="generate_signal")],
    ])

# ──────────────────────────────────────────────
#  TEXT BUILDERS
# ──────────────────────────────────────────────

def locked_text() -> str:
    return (
        "👑 *WELCOME TO ZENITH TRADER BOT* 👑\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔒 *Device Status:* LOCKED\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please enter your *License Key* to unlock access\\.\n\n"
        "📩 Buy key → Contact Admin"
    )

def main_menu_text(session: dict) -> str:
    return (
        "👑 *ZENITH TRADER BOT* 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Asset:*  `{session['asset']}`\n"
        f"⏱ *Expiry:* `{session['timeframe']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Choose an option below 👇"
    )

def signal_result_text(session: dict) -> str:
    direction = random.choice(["CALL", "PUT"])
    emoji = "🟢" if direction == "CALL" else "🔴"
    label = "UP ↑" if direction == "CALL" else "DOWN ↓"
    confidence = round(random.uniform(91.2, 98.9), 1)
    return (
        "╔══ 🤖 *ZENITH AI SIGNAL* ══╗\n\n"
        f"📊 *Asset:*      `{session['asset']}`\n"
        f"⏱ *Expiry:*     `{session['timeframe']}`\n\n"
        "──────────────────────────\n"
        f"📈 *Direction:*\n"
        f"   {emoji} *{direction} \\({label}\\)*\n\n"
        f"🧠 *AI Confidence:* `{confidence}%`\n"
        "──────────────────────────\n\n"
        "⚠️ _Trade responsibly\\. Past signals don't guarantee future results\\._"
    )

# ──────────────────────────────────────────────
#  HANDLERS
# ──────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = get_session(user_id)
    logger.info(f"User {user_id} /start | licensed={session['licensed']}")

    if session["licensed"]:
        await update.message.reply_text(
            main_menu_text(session),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(locked_text(), parse_mode="MarkdownV2")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = get_session(user_id)
    text = update.message.text.strip()

    if session["licensed"]:
        return  # ignore random messages after unlock

    logger.info(f"User {user_id} entered key: {text}")

    if text in VALID_LICENSE_KEYS:
        session["licensed"] = True
        await update.message.reply_text(
            "✅ *ACCESS GRANTED\\!*\n\nWelcome to Zenith Trader Bot 🎉",
            parse_mode="MarkdownV2",
        )
        await asyncio.sleep(0.5)
        await update.message.reply_text(
            main_menu_text(session),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            "❌ *Invalid License Key\\!*\nContact Admin to get a valid key\\.",
            parse_mode="MarkdownV2",
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = get_session(user_id)
    data = query.data
    logger.info(f"User {user_id} pressed: {data}")

    if data in ("back_main", "menu_main"):
        await query.edit_message_text(
            main_menu_text(session),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "menu_asset":
        await query.edit_message_text(
            "📊 *Select Trading Asset*\n\nChoose the pair you want to trade:",
            parse_mode="MarkdownV2",
            reply_markup=asset_keyboard(),
        )

    elif data.startswith("asset_"):
        session["asset"] = data.replace("asset_", "")
        await query.edit_message_text(
            f"✅ Asset updated\\!\n\n" + main_menu_text(session),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "menu_timeframe":
        await query.edit_message_text(
            "⏱ *Select Expiry Timeframe*\n\nChoose how long each trade lasts:",
            parse_mode="MarkdownV2",
            reply_markup=timeframe_keyboard(),
        )

    elif data.startswith("tf_"):
        session["timeframe"] = data.replace("tf_", "")
        await query.edit_message_text(
            f"✅ Timeframe updated\\!\n\n" + main_menu_text(session),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "generate_signal":
        chat_id = query.message.chat_id

        # Step 1 — suspense message
        asset = session["asset"]
        timeframe = session["timeframe"]

        await query.edit_message_text(
            "🤖 *ZENITH AI\\+ TRADE BOT*\n\n"
            f"📊 *ASSET* 🔸 `{asset}`\n"
            f"⏱ *TIME* 🔸 `{timeframe}`\n\n"
            "🚨 *The Next Message Will Send*\n"
            "*Direction* 🌲 *UP or DOWN* 🔻",
            parse_mode="MarkdownV2",
        )
        await asyncio.sleep(1.5)

        # Pick direction
        direction = random.choice(["CALL", "PUT"])
        confidence = round(random.uniform(91.2, 98.9), 1)

        # Step 2 — arrow animation message
        arrows = "🟢\n🟢\n🟢" if direction == "CALL" else "🔴\n🔴\n🔴"
        arrow_msg = await context.bot.send_message(chat_id=chat_id, text=arrows)
        await asyncio.sleep(1.2)

        # Step 3 — edit arrow msg to full signal result
        emoji = "🟢" if direction == "CALL" else "🔴"
        label = "UP ↑" if direction == "CALL" else "DOWN ↓"
        asset_e = asset.replace("/", "\\/").replace("(", "\\(").replace(")", "\\)")

        result_text = (
            "╔══ 🤖 *ZENITH AI SIGNAL* ══╗\n\n"
            f"📊 *Asset:*      `{asset_e}`\n"
            f"⏱ *Expiry:*     `{timeframe}`\n\n"
            "──────────────────────────\n"
            f"📈 *Direction:*\n"
            f"   {emoji} *{direction} \\({label}\\)*\n\n"
            f"🧠 *AI Confidence:* `{confidence}%`\n"
            "──────────────────────────\n\n"
            "⚠️ _Trade responsibly\\. Past signals don't guarantee future results\\._"
        )

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=arrow_msg.message_id,
            text=result_text,
            parse_mode="MarkdownV2",
            reply_markup=signal_result_keyboard(),
        )


    else:
        logger.warning(f"Unknown callback: {data}")

# ──────────────────────────────────────────────
#  MAIN — Polling Mode (works on Render free tier)
# ──────────────────────────────────────────────

async def main() -> None:
    logger.info("Starting Zenith Trader Bot (Polling Mode)...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("Bot is live! Polling for updates...")

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        # Run forever until interrupted
        await asyncio.Event().wait()

        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
