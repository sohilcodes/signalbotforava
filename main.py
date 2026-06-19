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

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN env variable missing")

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

# ==========================
# LOGGING
# ==========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ==========================
# SESSION
# ==========================

sessions = {}


def get_session(uid):
    if uid not in sessions:
        sessions[uid] = {
            "licensed": False,
            "asset": ASSETS[0],
            "timeframe": "1m",
        }

    return sessions[uid]


# ==========================
# UI
# ==========================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Asset", callback_data="asset")],
        [InlineKeyboardButton("⏱ Timeframe", callback_data="time")],
        [InlineKeyboardButton("🚀 GENERATE SIGNAL", callback_data="signal")]
    ])


def assets():
    rows = []

    for a in ASSETS:
        rows.append([
            InlineKeyboardButton(a, callback_data=f"a|{a}")
        ])

    rows.append([
        InlineKeyboardButton("🔙 Back", callback_data="home")
    ])

    return InlineKeyboardMarkup(rows)


def times():
    rows = []

    for t in TIMEFRAMES:
        rows.append([
            InlineKeyboardButton(t, callback_data=f"t|{t}")
        ])

    rows.append([
        InlineKeyboardButton("🔙 Back", callback_data="home")
    ])

    return InlineKeyboardMarkup(rows)


def home_text(s):
    return (
        "👑 ZENITH TRADER BOT 👑\n\n"
        f"Asset: {s['asset']}\n"
        f"Timeframe: {s['timeframe']}"
    )


# ==========================
# COMMANDS
# ==========================

async def start(update, context):

    uid = update.effective_user.id
    s = get_session(uid)

    if not s["licensed"]:

        await update.message.reply_text(
            "🔒 Enter License Key"
        )

        return

    await update.message.reply_text(
        home_text(s),
        reply_markup=menu()
    )


async def messages(update, context):

    uid = update.effective_user.id
    s = get_session(uid)

    if s["licensed"]:
        return

    key = update.message.text.strip()

    if key in VALID_LICENSE_KEYS:

        s["licensed"] = True

        await update.message.reply_text(
            "✅ Access Granted"
        )

        await update.message.reply_text(
            home_text(s),
            reply_markup=menu()
        )

    else:

        await update.message.reply_text(
            "❌ Invalid License"
        )


async def buttons(update, context):

    q = update.callback_query

    await q.answer()

    s = get_session(q.from_user.id)

    data = q.data

    if data == "home":

        await q.edit_message_text(
            home_text(s),
            reply_markup=menu()
        )

    elif data == "asset":

        await q.edit_message_text(
            "Select Asset",
            reply_markup=assets()
        )

    elif data == "time":

        await q.edit_message_text(
            "Select Timeframe",
            reply_markup=times()
        )

    elif data.startswith("a|"):

        s["asset"] = data.split("|")[1]

        await q.edit_message_text(
            home_text(s),
            reply_markup=menu()
        )

    elif data.startswith("t|"):

        s["timeframe"] = data.split("|")[1]

        await q.edit_message_text(
            home_text(s),
            reply_markup=menu()
        )

    elif data == "signal":

        await q.edit_message_text(
            "🤖 Analysing..."
        )

        await asyncio.sleep(2)

        direction = random.choice([
            "🟢 CALL",
            "🔴 PUT"
        ])

        confidence = round(
            random.uniform(91, 99),
            1
        )

        await q.edit_message_text(
            f"""
🤖 SIGNAL READY

📊 {s['asset']}
⏱ {s['timeframe']}

{direction}

Confidence:
{confidence}%
""",
            reply_markup=menu()
        )


# ==========================
# MAIN
# ==========================

async def main():

    logger.info("Starting...")

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            messages
        )
    )

    logger.info("Polling started")

    await app.initialize()

    await app.start()

    await app.updater.start_polling(
        drop_pending_updates=True
    )

    try:
        await asyncio.Event().wait()

    finally:

        logger.info("Stopping")

        await app.updater.stop()

        await app.stop()

        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
