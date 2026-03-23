#!/usr/bin/env python3
# SIMPLE TEST BOT
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7913598777:AAHHsSzkhEvTpbwUw87gUJ7OUbkftL9QSfA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running! ✅")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
