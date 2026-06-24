import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Define the exact stations that are allowed to give stamps
VALID_STATIONS = {"station_1", "station_2"}

# Define your Heart Emoji configurations here
HEART_EMOJI = "❤️" 
HEART_PASSWORD = "heart" # Change this to your actual password
HEART_CODE_STAMP = "Heart Station"

# Temporary memory for users typing passwords (does not need JSON saving)
pending_password_requests = set()

# --- JSON Save and Load Functions ---
def load_data():
    try:
        with open("stamps.json", "r") as f:
            data = json.load(f)
            return {int(user): set(stamps) for user, stamps in data.items()}
    except FileNotFoundError:
        return {} 

def save_data():
    with open("stamps.json", "w") as f:
        data_to_save = {user: list(stamps) for user, stamps in user_stamps.items()}
        json.dump(data_to_save, f)

# Initialize data from the JSON file
user_stamps = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_stamps:
        user_stamps[user_id] = set()
        save_data() 

    # 1. Handle QR Code Scans
    if context.args:
        station = context.args[0]

        if station not in VALID_STATIONS:
            await update.message.reply_text("❌ Invalid QR code! Nice try though.")
            return

        if station in user_stamps[user_id]:
            await update.message.reply_text(f"You already collected the stamp for {station}!")
            return

        user_stamps[user_id].add(station)
        save_data() 
        
        stamps = "\n".join(f"✅ {s}" for s in sorted(user_stamps[user_id]))
        await update.message.reply_text(f"Stamp collected!\n\n{stamps}")
        return 

    # 2. Handle standard /start commands
    try:
        with open("FRONT 1.png", "rb") as f:
            await update.message.reply_photo(photo=f, caption="Stamp Card — Front")
    except Exception:
        pass

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

    user_id = update.effective_user.id

    if text == HEART_EMOJI:
        pending_password_requests.add(user_id)
        await update.message.reply_text(
            "Nice! To claim the heart stamp, type the password in chat."
        )
        return

    if user_id in pending_password_requests:
        if text == HEART_PASSWORD:
            if user_id not in user_stamps:
                user_stamps[user_id] = set()
                save_data() 

            if HEART_CODE_STAMP in user_stamps[user_id]:
                await update.message.reply_text("You already claimed the heart stamp!")
            else:
                user_stamps[user_id].add(HEART_CODE_STAMP)
                save_data() 
                await update.message.reply_text("✅ Heart stamp claimed! Nice job.")
        else:
            await update.message.reply_text(
                "That password is incorrect. Send the heart emoji again to try again."
            )
        pending_password_requests.discard(user_id)
        return

# --- Debug Command to Reset Only Your Data --- (to be removed later)
async def reset_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes only the current user's data."""
    user_id = update.effective_user.id

    if user_id in user_stamps:
        del user_stamps[user_id]  
        save_data()               
        await update.message.reply_text("🗑️ Your personal stamp data has been completely erased. Send /start to begin as a brand new user!")
    else:
        await update.message.reply_text("You don't have any data saved yet!")
# --- till here ---

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is missing.")
    else:
        print("Bot is starting up and ready to collect stamps...")
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, emoji_stamp))
        
        # Added ONLY the resetme handler here (delete later if you want to remove it)
        app.add_handler(CommandHandler("resetme", reset_me))
        
        app.run_polling()