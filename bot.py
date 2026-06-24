import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

user_stamps = {}

# Define the exact stations that are allowed to give stamps
VALID_STATIONS = {"station_1", "station_2"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_stamps:
        user_stamps[user_id] = set()

    # 1. Handle QR Code Scans
    if context.args:
        station = context.args[0]

        # Check if the scanned station is actually a real station
        if station not in VALID_STATIONS:
            await update.message.reply_text("❌ Invalid QR code! Nice try though.")
            return

        # Check if they already have this specific stamp
        if station in user_stamps[user_id]:
            await update.message.reply_text(f"You already collected the stamp for {station}!")
            return

        # Add the stamp and celebrate
        user_stamps[user_id].add(station)
        stamps = "\n".join(f"✅ {s}" for s in sorted(user_stamps[user_id]))
        await update.message.reply_text(f"Stamp collected!\n\n{stamps}")
        return 

    # 2. Handle standard /start commands (No QR code scanned)
    try:
        with open("FRONT 1.png", "rb") as f:
            await update.message.reply_photo(photo=f, caption="Stamp Card — Front")
    except Exception:
        await update.message.reply_text("(Missing image) Stamp card front not found.")

    try:
        with open("BACK 1.png", "rb") as f:
            await update.message.reply_photo(photo=f, caption="Stamp Card — Back")
    except Exception:
        pass

    if len(user_stamps[user_id]) == 0:
        await update.message.reply_text("Welcome to the Club Fair! Scan a station QR code to collect stamps.")
    else:
        stamps = "\n".join(f"✅ {s}" for s in sorted(user_stamps[user_id]))
        await update.message.reply_text(f"Welcome back! Here is your current progress:\n\n{stamps}")

async def emoji_stamp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message and update.message.text else ""
    if not text:
        return

    heart_variants = {
        "❤️",
        "♥️",
        "♥",
        "💛",
        "💚",
        "💙",
        "💜",
        "🖤",
        "💗",
        "💖",
        "💘",
        "💝",
        "💓",
        "💕",
        "❣️",
    }

    if text in heart_variants:
        await update.message.reply_text(text)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is missing.")
    else:
        print("Bot is starting up and ready to collect stamps...")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, emoji_stamp))
        app.run_polling()