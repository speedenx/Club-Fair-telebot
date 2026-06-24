from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

user_stamps = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # If this is the user's first time, initialize their stamp set
    first_time = user_id not in user_stamps
    if first_time:
        user_stamps[user_id] = set()

        # Try to send the front and back stamp card images if they exist
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

        await update.message.reply_text("Welcome! Scan a station QR code to collect stamps.")

    # If /start was invoked with an argument (station code), treat it as a scan
    if context.args:
        station = context.args[0]

        if station in user_stamps[user_id]:
            await update.message.reply_text(f"You already collected {station}")
            return

        user_stamps[user_id].add(station)

        stamps = "\n".join(f"✅ {s}" for s in sorted(user_stamps[user_id]))

        await update.message.reply_text(f"Stamp collected!\n\n{stamps}")

app = Application.builder().token("8908219789:AAFXfLgEe2MeF_F7D9c8NE0jW-vefl-NbFc").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()