import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Define each stamp category here.
# Change the passwords to the real booth passwords before the fair.
STAMP_CONFIGS = {
    "community_service": {
        "stamp": "Community Service😎",
        "emoji": "😎",
        "password": "community_service",
    },
    "performing_arts": {
        "stamp": "PERFORMING ARTS💃",
        "emoji": "💃",
        "password": "performing_arts",
    },
    "varsity": {
        "stamp": "VARSITY🥇",
        "emoji": "🥇",
        "password": "varsity",
    },
    "sports_clubs": {
        "stamp": "SPORTS CLUBS🏆",
        "emoji": "🏆",
        "password": "sports_clubs",
    },
    "student_chapters": {
        "stamp": "STUDENT CHAPTERS📖",
        "emoji": "📖",
        "password": "student_chapters",
    },
    "special_interest": {
        "stamp": "SPECIAL INTEREST❤️",
        "emoji": "❤️",
        "password": "heart",
    },
}

VALID_STATIONS = {key: config["stamp"] for key, config in STAMP_CONFIGS.items()}
STAMP_TRIGGERS = {}
for key, config in STAMP_CONFIGS.items():
    STAMP_TRIGGERS[config["emoji"]] = key
    STAMP_TRIGGERS[config["stamp"]] = key

# Temporary memory for users typing passwords (does not need JSON saving)
pending_password_requests = {}

# --- JSON Save and Load Functions ---
def load_data():
    try:
        with open("stamps.json", "r") as f:
            data = json.load(f)
            return {int(user): set(stamps) for user, stamps in data.items()}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Warning: stamps.json is not valid JSON. Starting with empty stamp data.")
        return {} 

def save_data():
    data_to_save = {user: list(stamps) for user, stamps in user_stamps.items()}
    temp_path = "stamps.json.tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False)

    os.replace(temp_path, "stamps.json")

# Initialize data from the JSON file
user_stamps = load_data()

def display_stamp_name(stamp_name):
    for config in STAMP_CONFIGS.values():
        stamp_name = stamp_name.replace(config["emoji"], "")
    return stamp_name

def format_stamps(user_id):
    stamps = user_stamps.get(user_id, set())
    if not stamps:
        return "No stamps collected yet."
    return "\n".join(f"✅ {display_stamp_name(s)}" for s in sorted(stamps))

def format_remaining_stamps(user_id):
    collected_stamps = user_stamps.get(user_id, set())
    remaining_stamps = [
        config["stamp"] for config in STAMP_CONFIGS.values()
        if config["stamp"] not in collected_stamps
    ]

    if not remaining_stamps:
        return "All stamps collected!"
    return "\n".join(f"⬜ {display_stamp_name(stamp)}" for stamp in remaining_stamps)

def progress_message(user_id):
    return (
        f"Your current progress:\n{format_stamps(user_id)}\n\n"
        f"Remaining stamps:\n{format_remaining_stamps(user_id)}"
    )

def starter_message():
    category_list = "\n".join(
        display_stamp_name(config["stamp"]) for config in STAMP_CONFIGS.values()
    )
    return (
        "Welcome to the Club Fair Stamp Hunt!\n\n"
        "How to collect stamps:\n"
        "1. Visit a booth category.\n"
        "2. Send the category emoji here.\n"
        "3. Type the booth password when the bot asks for it.\n"
        "4. Your stamp will be saved automatically.\n\n"
        "Categories:\n"
        f"{category_list}\n\n"
        "Send /progress anytime to see your current progress."
    )

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

        station_name = VALID_STATIONS[station]
        station_display_name = display_stamp_name(station_name)

        if station_name in user_stamps[user_id]:
            await update.message.reply_text(f"You already collected the stamp for {station_display_name}!")
            return

        user_stamps[user_id].add(station_name)
        save_data() 
        
        await update.message.reply_text(
            f"You have claimed the {station_display_name} stamp!\n\nStamps collected:\n{format_stamps(user_id)}"
        )
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

    await update.message.reply_text(starter_message())

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_stamps:
        user_stamps[user_id] = set()
        save_data()

    await update.message.reply_text(progress_message(user_id))

async def emoji_stamp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message and update.message.text else ""
    if not text:
        return

    user_id = update.effective_user.id

    if text in STAMP_TRIGGERS:
        stamp_key = STAMP_TRIGGERS[text]
        pending_password_requests[user_id] = stamp_key
        stamp_name = STAMP_CONFIGS[stamp_key]["stamp"]
        stamp_display_name = display_stamp_name(stamp_name)
        await update.message.reply_text(
            f"Nice! To claim the {stamp_display_name} stamp, type the password in chat."
        )
        return

    if user_id in pending_password_requests:
        stamp_key = pending_password_requests[user_id]
        stamp_config = STAMP_CONFIGS[stamp_key]
        stamp_name = stamp_config["stamp"]
        stamp_display_name = display_stamp_name(stamp_name)

        if text == stamp_config["password"]:
            if user_id not in user_stamps:
                user_stamps[user_id] = set()
                save_data() 

            if stamp_name in user_stamps[user_id]:
                await update.message.reply_text(
                    f"You already claimed the {stamp_display_name} stamp!\n\n{progress_message(user_id)}"
                )
            else:
                user_stamps[user_id].add(stamp_name)
                save_data() 
                await update.message.reply_text(
                    f"You have claimed the {stamp_display_name} stamp!\n\n{progress_message(user_id)}"
                )
        else:
            stamp_emoji = stamp_config["emoji"]
            await update.message.reply_text(
                f"That password is incorrect. Send {stamp_emoji} again to try again."
            )
        del pending_password_requests[user_id]
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
        app.add_handler(CommandHandler("progress", progress))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, emoji_stamp))
        
        # Added ONLY the resetme handler here (delete later if you want to remove it)
        app.add_handler(CommandHandler("resetme", reset_me))
        
        app.run_polling()
