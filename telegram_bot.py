import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ✅ Replace with your actual Telegram Bot API token
TOKEN = "8020046356:AAE46_mwRDN9kuJ9hF_4iNID1K82J8p_hPo"

# ✅ Set directory where CSV files are stored
data_dir = "exchange_rates"

async def get_exchange_rate(update: Update, context: CallbackContext):
    try:
        if not context.args:
            await update.message.reply_text("❌ Please provide a currency. Example: /rate USD")
            return
        
        currency = " ".join(context.args).upper()

        # ✅ Find the latest CSV file
        csv_files = sorted(
            [f for f in os.listdir(data_dir) if f.startswith("exchange_rates_") and f.endswith(".csv")],
            reverse=True
        )

        if not csv_files:
            await update.message.reply_text("❌ No exchange rate data found.")
            return

        latest_file = os.path.join(data_dir, csv_files[0])

        # ✅ Load the latest exchange rate data
        df = pd.read_csv(latest_file, header=0)

        if "Currency" not in df.columns or "Buying Price" not in df.columns or "Selling Price" not in df.columns:
            await update.message.reply_text("❌ CSV format error.")
            return

        rate_info = df[df["Currency"].str.upper() == currency]

        if rate_info.empty:
            await update.message.reply_text(f"❌ Currency {currency} not found.")
        else:
            buy = rate_info["Buying Price"].values[0]
            sell = rate_info["Selling Price"].values[0]
            await update.message.reply_text(f"💵 {currency} Rate:\nBuying: {buy} SDG\nSelling: {sell} SDG")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Welcome! Use /rate <currency> to get exchange rates.\nExample: /rate USD")

# ✅ Initialize the bot
def main():
    app = Application.builder().token(TOKEN).build()

    # ✅ Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rate", get_exchange_rate))

    # ✅ Start polling
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
