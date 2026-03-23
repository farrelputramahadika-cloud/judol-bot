#!/usr/bin/env python3
import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7913598777:AAHHsSzkhEvTpbwUw87gUJ7OUbkftL9QSfA"
ADMIN_ID = 6481058235

users = {}

def get_user(uid):
    if str(uid) not in users:
        users[str(uid)] = {'balance': 0, 'spin': 0}
    return users[str(uid)]

async def start(update: Update, context):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎰 SPIN", callback_data='spin')],
        [InlineKeyboardButton("💰 DEPOSIT", callback_data='deposit')],
        [InlineKeyboardButton("📊 STATUS", callback_data='status')]
    ]
    await update.message.reply_text(
        f"🎰 BOT JALAN!\n\nWelcome {user.first_name}!\nSaldo: Rp {get_user(user.id)['balance']:,}\n\nPilih menu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def spin_handler(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    await query.answer()
    
    if user_data['balance'] < 1000:
        await query.edit_message_text("Saldo tidak cukup! Silakan deposit.")
        return
    
    user_data['balance'] -= 1000
    user_data['spin'] += 1
    
    # Random win
    win = random.choice([0, 0, 0, 0, 500, 1000, 2000, 5000, 10000])
    if win > 0:
        user_data['balance'] += win
    
    result = f"🎰 SPIN RESULT\n\nBet: Rp 1,000\n"
    if win > 0:
        result += f"WIN: Rp {win:,}\n"
    else:
        result += "LOSE\n"
    result += f"Saldo: Rp {user_data['balance']:,}"
    
    keyboard = [[InlineKeyboardButton("🔄 SPIN LAGI", callback_data='spin')]]
    await query.edit_message_text(result, reply_markup=InlineKeyboardMarkup(keyboard))

async def deposit_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💰 DEPOSIT\n\nTransfer ke:\nDANA: 085969081186 (YULIANA)\nGOPAY: 085969081186 (YULIANA)\n\nSetelah transfer, ketik /start"
    )

async def status_handler(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = get_user(user_id)
    await query.answer()
    await query.edit_message_text(
        f"📊 STATUS\n\nSaldo: Rp {user_data['balance']:,}\nTotal Spin: {user_data['spin']}\n\nKetik /start untuk kembali"
    )

async def callback(update: Update, context):
    query = update.callback_query
    data = query.data
    
    if data == 'spin':
        await spin_handler(update, context)
    elif data == 'deposit':
        await deposit_handler(update, context)
    elif data == 'status':
        await status_handler(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    print("BOT STARTED! ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
