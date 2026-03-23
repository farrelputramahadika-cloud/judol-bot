#!/usr/bin/env python3
# JUDOL BOT - REGISTRATION WITH ADMIN APPROVAL
# TOKEN: 8743058682:AAErZ9IteuI9ZMIaPRfhnrM3x1-4uftQR3I
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
TOKEN = "8743058682:AAErZ9IteuI9ZMIaPRfhnrM3x1-4uftQR3I"
ADMIN_ID = 6481058235  # ID TELEGRAM LO

# File data
USERS_FILE = "users.json"
TRANSACTIONS_FILE = "transactions.json"
PENDING_FILE = "pending.json"
REGISTER_FILE = "register_requests.json"

users = {}
transactions = []
pending_deposits = {}
register_requests = {}

# ========== FUNGSI HASH ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# ========== LOAD DATA ==========
def load_data():
    global users, transactions, pending_deposits, register_requests
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
            pending_deposits = json.load(f)
    except:
        pending_deposits = {}
    try:
        with open(REGISTER_FILE, 'r') as f:
            register_requests = json.load(f)
    except:
        register_requests = {}

def save_data():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f)
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending_deposits, f)
    with open(REGISTER_FILE, 'w') as f:
        json.dump(register_requests, f)

load_data()

# ========== FUNGSI USER ==========
def generate_referral_code():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

def generate_trx_id():
    return f"TRX{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"

def create_user_approved(telegram_id, username, password, referrer_code=None):
    """Buat user setelah admin approve"""
    uid = str(telegram_id)
    
    users[uid] = {
        'id': uid,
        'telegram_id': telegram_id,
        'username': username,
        'password': hash_password(password),
        'balance': 0,
        'total_deposit': 0,
        'total_withdraw': 0,
        'total_spin': 0,
        'total_win': 0,
        'referral_code': generate_referral_code(),
        'referred_by': None,
        'referral_count': 0,
        'referral_bonus': 0,
        'joined': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_bonus': None,
        'is_approved': True
    }
    
    # Handle referral
    if referrer_code:
        for uid_ref, data in users.items():
            if data.get('referral_code') == referrer_code:
                users[uid]['referred_by'] = uid_ref
                users[uid_ref]['referral_count'] += 1
                users[uid_ref]['referral_bonus'] += 10000
                users[uid_ref]['balance'] += 10000
                break
    
    save_data()
    return True

def is_user_approved(telegram_id):
    uid = str(telegram_id)
    if uid in users:
        return users[uid].get('is_approved', False)
    return False

def get_user_data(telegram_id):
    uid = str(telegram_id)
    if uid in users and users[uid].get('is_approved'):
        return users[uid]
    return None

# ========== FUNGSI DEPOSIT/WITHDRAW ==========
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

# ========== GAME SPIN ==========
def spin_slot(bet, game):
    rand = random.random()
    if rand < 0.4:
        win, result_type = 0, "LOSE"
    elif rand < 0.65:
        win, result_type = int(bet * 0.5), "SMALL WIN"
    elif rand < 0.8:
        win, result_type = int(bet * 1), "WIN"
    elif rand < 0.9:
        win, result_type = int(bet * 2), "BIG WIN"
    elif rand < 0.95:
        win, result_type = int(bet * 5), "MEGA WIN"
    elif rand < 0.98:
        win, result_type = int(bet * 10), "JACKPOT"
    else:
        win, result_type = int(bet * 25), "SUPER JACKPOT"
    
    return {'win': win, 'type': result_type, 'bet': bet, 'game': game}

# ========== PAYMENT DATA ==========
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

# ========== NOTIFIKASI ADMIN ==========
async def notify_admin_register(context, telegram_id, username, password, referrer):
    """Kirim notifikasi registrasi ke admin"""
    keyboard = [
        [InlineKeyboardButton("✅ APPROVE", callback_data=f"reg_approve_{telegram_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"reg_reject_{telegram_id}")]
    ]
    
    message = f"📝 *REGISTRASI BARU*\n\n"
    message += f"👤 Username: {username}\n"
    message += f"🆔 Telegram ID: {telegram_id}\n"
    message += f"🔑 Password: {password}\n"
    message += f"👥 Referral: {referrer or 'Tidak ada'}\n"
    message += f"🕐 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    message += f"Klik APPROVE untuk mengaktifkan akun."
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def notify_admin_deposit(context, user_id, username, amount, method, trx_id):
    """Kirim notifikasi deposit ke admin"""
    keyboard = [
        [InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{trx_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{trx_id}")]
    ]
    
    message = f"💰 *DEPOSIT PENDING*\n\n"
    message += f"👤 User: {username}\n"
    message += f"🆔 ID: {user_id}\n"
    message += f"💰 Nominal: Rp {amount:,.0f}\n"
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
    telegram_id = user.id
    
    # Cek apakah user sudah approved
    if is_user_approved(telegram_id):
        user_data = get_user_data(telegram_id)
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
            f"🎰 *JUDOL BOT - SLOT GAME* 🎰\n\n"
            f"👋 Welcome {user_data['username']}!\n\n"
            f"💰 *Saldo:* Rp {user_data['balance']:,.0f}\n"
            f"🎲 *Total Spin:* {user_data['total_spin']}\n"
            f"🏆 *Total Win:* Rp {user_data['total_win']:,.0f}\n"
            f"👥 *Referral:* {user_data['referral_count']} orang\n\n"
            f"📌 *Pilih menu:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        # Belum registrasi, tampilkan menu registrasi
        keyboard = [
            [InlineKeyboardButton("📝 REGISTER", callback_data='register')],
            [InlineKeyboardButton("🔐 LOGIN", callback_data='login')]
        ]
        
        await update.message.reply_text(
            f"🎰 *JUDOL BOT* 🎰\n\n"
            f"👋 Halo {user.first_name}!\n\n"
            f"⚠️ *Anda belum memiliki akun!*\n\n"
            f"Silakan REGISTER terlebih dahulu.\n"
            f"Atau LOGIN jika sudah punya akun.\n\n"
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
        f"Silakan masukkan data berikut:\n\n"
        f"1️⃣ *Username* (tanpa spasi)\n"
        f"2️⃣ *Password* (minimal 4 karakter)\n"
        f"3️⃣ *Kode Referral* (opsional)\n\n"
        f"Format: `username|password|kode_referral`\n\n"
        f"Contoh: `jokosusanto|12345|ABC123`\n\n"
        f"Ketik format di chat:",
        parse_mode='Markdown'
    )
    context.user_data['waiting_register'] = True

async def handle_register(update: Update, context):
    try:
        text = update.message.text.strip()
        parts = text.split('|')
        
        if len(parts) < 2:
            await update.message.reply_text("❌ Format salah! Gunakan: username|password|kode_referral")
            return
        
        username = parts[0].strip()
        password = parts[1].strip()
        referrer = parts[2].strip() if len(parts) > 2 else None
        
        # Validasi
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
        
        telegram_id = update.effective_user.id
        
        # Simpan request registrasi
        register_requests[str(telegram_id)] = {
            'telegram_id': telegram_id,
            'username': username,
            'password': password,
            'referrer': referrer,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data()
        
        # Kirim notifikasi ke admin
        await notify_admin_register(context, telegram_id, username, password, referrer)
        
        await update.message.reply_text(
            f"✅ *REGISTRASI DIAJUKAN!*\n\n"
            f"👤 Username: {username}\n"
            f"🔑 Password: {password}\n\n"
            f"📌 *TUNGGU KONFIRMASI DARI ADMIN*\n"
            f"Admin akan mengaktifkan akun Anda.\n\n"
            f"⏱️ Estimasi: 1-5 menit",
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
        f"Masukkan username dan password:\n\n"
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
            if data.get('username') == username and verify_password(password, data.get('password', '')):
                if data.get('is_approved'):
                    # Update telegram_id
                    users[telegram_id] = data
                    users[telegram_id]['telegram_id'] = telegram_id
                    del users[uid]
                    save_data()
                    found = True
                    break
                else:
                    await update.message.reply_text("❌ Akun belum di-approve admin!")
                    return
        
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

# ========== ADMIN APPROVE/REJECT REGISTRATION ==========
async def admin_approve_register(update: Update, context):
    query = update.callback_query
    data = query.data
    telegram_id = data.replace('reg_approve_', '')
    
    if telegram_id not in register_requests:
        await query.answer("Request tidak ditemukan!", show_alert=True)
        return
    
    req = register_requests[telegram_id]
    
    # Buat user
    create_user_approved(
        int(telegram_id),
        req['username'],
        req['password'],
        req.get('referrer')
    )
    
    # Hapus request
    del register_requests[telegram_id]
    save_data()
    
    await query.edit_message_text(
        f"✅ *REGISTRASI APPROVED!*\n\n"
        f"👤 Username: {req['username']}\n"
        f"🆔 Telegram ID: {telegram_id}\n\n"
        f"✅ Akun telah diaktifkan!\n"
        f"User sekarang bisa login.",
        parse_mode='Markdown'
    )
    
    # Kirim notifikasi ke user
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
    
    if telegram_id not in register_requests:
        await query.answer("Request tidak ditemukan!", show_alert=True)
        return
    
    req = register_requests[telegram_id]
    
    # Hapus request
    del register_requests[telegram_id]
    save_data()
    
    await query.edit_message_text(
        f"❌ *REGISTRASI REJECTED!*\n\n"
        f"👤 Username: {req['username']}\n"
        f"🆔 Telegram ID: {telegram_id}\n\n"
        f"❌ Registrasi ditolak!",
        parse_mode='Markdown'
    )
    
    # Kirim notifikasi ke user
    try:
        await context.bot.send_message(
            chat_id=int(telegram_id),
            text=f"❌ *REGISTRASI DITOLAK!*\n\n"
                 f"👤 Username: {req['username']}\n\n"
                 f"⚠️ Pendaftaran Anda ditolak oleh admin.\n"
                 f"Silakan hubungi admin untuk info lebih lanjut.",
            parse_mode='Markdown'
        )
    except:
        pass

# ========== DEPOSIT (SAMA KAYAK SEBELUMNYA) ==========
async def deposit_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
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
        f"⚠️ *SETELAH TRANSFER, KETIK NOMINAL DI CHAT*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def deposit_method(update: Update, context):
    query = update.callback_query
    method = query.data.replace('deposit_', '')
    await query.answer()
    
    payment = PAYMENT[method]
    
    await query.edit_message_text(
        f"💳 *DEPOSIT {payment['name'].upper()}*\n\n"
        f"📱 *Nomor:* `{payment['number']}`\n"
        f"👤 *Nama:* {payment['owner']}\n\n"
        f"💰 *Masukkan nominal deposit:*\n"
        f"Contoh: *50000*\n\n"
        f"📌 *CARA DEPOSIT:*\n"
        f"1. Transfer ke nomor di atas\n"
        f"2. Ketik nominal di chat\n"
        f"3. *TUNGGU KONFIRMASI DARI ADMIN*\n\n"
        f"⚠️ Saldo akan masuk setelah admin APPROVE!",
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
        user_data = get_user_data(telegram_id)
        
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

# ========== ADMIN APPROVE/REJECT DEPOSIT ==========
async def admin_approve_deposit(update: Update, context):
    query = update.callback_query
    data = query.data
    trx_id = data.replace('approve_', '')
    
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
    
    # Tambah saldo
    success, trx_id_deposit = add_balance(user_id, total, f"Deposit via {method.upper()}", is_deposit=True)
    
    # Update status
    pending['status'] = 'approved'
    pending['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_data()
    
    await query.edit_message_text(
        f"✅ *DEPOSIT APPROVED!*\n\n"
        f"👤 User: {username}\n"
        f"💰 Nominal: Rp {amount:,.0f}\n"
        f"🎁 Bonus: Rp {bonus:,.0f}\n"
        f"💵 Total Masuk: Rp {total:,.0f}\n"
        f"🆔 Trx ID: {trx_id}\n\n"
        f"✅ Saldo telah ditambahkan!",
        parse_mode='Markdown'
    )
    
    # Notifikasi ke user
    try:
        user_data = get_user_data(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ *DEPOSIT BERHASIL!*\n\n"
                 f"💰 Nominal: Rp {amount:,.0f}\n"
                 f"🎁 Bonus: Rp {bonus:,.0f}\n"
                 f"💵 Total Masuk: Rp {total:,.0f}\n"
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
    trx_id = data.replace('reject_', '')
    
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
    
    # Notifikasi ke user
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

# ========== GAME MENU ==========
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
        f"🎮 Pilih game:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def game_play(update: Update, context):
    query = update.callback_query
    game_key = query.data.replace('game_', '')
    game_data = GAMES[game_key]
    
    await query.answer()
    
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
        f"🎲 Pilih nominal spin:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def spin_handler(update: Update, context):
    query = update.callback_query
    parts = query.data.split('_')
    
    game_key = parts[1]
    bet = int(parts[2])
    telegram_id = update.effective_user.id
    user_data = get_user_data(telegram_id)
    
    if not user_data:
        await query.answer("Anda belum login!", show_alert=True)
        return
    
    game_data = GAMES[game_key]
    
    if user_data['balance'] < bet:
        await query.answer("Saldo tidak mencukupi!", show_alert=True)
        return
    
    success, _ = deduct_balance(telegram_id, bet, f"SPIN {game_data['name']}")
    if not success:
        await query.answer("Gagal melakukan spin!", show_alert=True)
        return
    
    result = spin_slot(bet, game_key)
    
    if result['win'] > 0:
        add_win(telegram_id, result['win'], game_data['name'])
    
    user_data = get_user_data(telegram_id)
    
    result_text = f"🎲 *SPIN RESULT* 🎲\n\n"
    result_text += f"{game_data['emoji']} {game_data['name']}\n"
    result_text += f"💰 Bet: Rp {result['bet']:,}\n"
    result_text += f"🎯 Result: {result['type']}\n"
    if result['win'] > 0:
        result_text += f"🏆 Win: Rp {result['win']:,.0f}\n"
    result_text += f"\n💵 Saldo Baru: Rp {user_data['balance']:,.0f}"
    
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

# ========== STATUS ==========
async def status_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user_data(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login! Ketik /start")
        return
    
    win_rate = (user_data['total_win'] / max(user_data['total_spin'] * 1000, 1)) * 100 if user_data['total_spin'] > 0 else 0
    
    status_text = f"📊 *STATUS AKUN*\n\n"
    status_text += f"👤 Username: {user_data['username']}\n"
    status_text += f"💰 Saldo: Rp {user_data['balance']:,.0f}\n"
    status_text += f"💵 Total Deposit: Rp {user_data['total_deposit']:,.0f}\n"
    status_text += f"🎲 Total Spin: {user_data['total_spin']}\n"
    status_text += f"🏆 Total Win: Rp {user_data['total_win']:,.0f}\n"
    status_text += f"📈 Win Rate: {win_rate:.1f}%\n"
    status_text += f"👥 Referral: {user_data['referral_count']} orang\n"
    status_text += f"🎁 Referral Bonus: Rp {user_data['referral_bonus']:,.0f}\n"
    status_text += f"📅 Bergabung: {user_data['joined']}\n"
    
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
    
    user_data = get_user_data(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login! Ketik /start")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    can_claim = user_data.get('last_bonus') != today
    
    keyboard = []
    if can_claim:
        keyboard.append([InlineKeyboardButton("🎁 DAILY BONUS", callback_data='bonus_daily')])
    keyboard.append([InlineKeyboardButton("👥 REFERRAL BONUS", callback_data='bonus_referral')])
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data='back_main')])
    
    await query.edit_message_text(
        f"🎁 *BONUS MENU*\n\n"
        f"💰 Saldo: Rp {user_data['balance']:,.0f}\n\n"
        f"🎁 Daily Bonus: {'✅ READY' if can_claim else '❌ SUDAH CLAIM'}\n"
        f"👥 Referral Bonus: Rp 10,000 per referral aktif\n\n"
        f"Pilih bonus:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def bonus_daily(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not user_data:
        await query.edit_message_text("❌ Anda belum login!")
        return
    
    if user_data.get('last_bonus') == today:
        await query.edit_message_text("❌ Anda sudah claim daily bonus hari ini!")
        return
    
    bonus = random.randint(5000, 25000)
    user_data['last_bonus'] = today
    add_balance(user_id, bonus, "Daily Bonus")
    
    await query.edit_message_text(
        f"🎉 *DAILY BONUS CLAIMED!*\n\n"
        f"💰 Bonus: Rp {bonus:,.0f}\n"
        f"💵 Saldo Baru: Rp {get_user_data(user_id)['balance']:,.0f}\n\n"
        f"Kembali besok untuk claim lagi!",
        parse_mode='Markdown'
    )

async def bonus_referral(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user_data(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login!")
        return
    
    await query.edit_message_text(
        f"👥 *REFERRAL BONUS*\n\n"
        f"🔗 *Kode Referral:* `{user_data['referral_code']}`\n\n"
        f"👥 *Total Referral:* {user_data['referral_count']} orang\n"
        f"💰 *Bonus Diterima:* Rp {user_data['referral_bonus']:,.0f}\n\n"
        f"📌 *CARA DAPAT BONUS:*\n"
        f"1. Bagikan link ini ke teman:\n"
        f"`https://t.me/JudolBot?start={user_data['referral_code']}`\n"
        f"2. Teman daftar\n"
        f"3. Anda dapat bonus Rp 10,000\n\n"
        f"🎁 *BONUS TAMBAHAN:*\n"
        f"• 5 referral = +Rp 50,000\n"
        f"• 10 referral = +Rp 100,000",
        parse_mode='Markdown'
    )

# ========== REFERRAL ==========
async def referral_menu(update: Update, context):
    await bonus_referral(update, context)

# ========== HISTORY ==========
async def history_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user_data(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login! Ketik /start")
        return
    
    user_transactions = [t for t in transactions if str(t['user_id']) == str(update.effective_user.id)]
    user_transactions.reverse()
    last_10 = user_transactions[:10]
    
    if not last_10:
        await query.edit_message_text("📜 Belum ada history transaksi", parse_mode='Markdown')
        return
    
    text = "📜 *HISTORY TRANSAKSI*\n\n"
    for t in last_10:
        icon = "➕" if t['type'] in ['DEPOSIT', 'BONUS', 'WIN', 'REFERRAL'] else "➖"
        text += f"{icon} *{t['type']}*: Rp {t['amount']:,.0f}\n"
        text += f"   🕐 {t['time'][:16]}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data='back_main')]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== WITHDRAW ==========
async def withdraw_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_data = get_user_data(update.effective_user.id)
    if not user_data:
        await query.edit_message_text("❌ Anda belum login! Ketik /start")
        return
    
    keyboard = [
        [InlineKeyboardButton("💙 DANA", callback_data='withdraw_dana')],
        [InlineKeyboardButton("💚 GOPAY", callback_data='withdraw_gopay')],
        [InlineKeyboardButton("🔙 BACK", callback_data='back_main')]
    ]
    
    await query.edit_message_text(
        f"💳 *WITHDRAW*\n\n"
        f"💰 Saldo: Rp {user_data['balance']:,.0f}\n\n"
        f"📌 *Minimal Withdraw:* Rp 50,000\n"
        f"⚡ *Proses:* 1-5 menit\n\n"
        f"Pilih metode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def withdraw_form(update: Update, context):
    query = update.callback_query
    method = query.data.replace('withdraw_', '')
    await query.answer()
    
    user_data = get_user_data(update.effective_user.id)
    
    await query.edit_message_text(
        f"💳 *WITHDRAW {method.upper()}*\n\n"
        f"💰 Saldo: Rp {user_data['balance']:,.0f}\n\n"
        f"📝 *Format:* `nominal|nomor_akun`\n\n"
        f"Contoh: *100000|085969081186*\n\n"
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
        user_data = get_user_data(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ Anda belum login! Ketik /start")
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
                f"💵 Sisa Saldo: Rp {get_user_data(user_id)['balance']:,.0f}\n\n"
                f"🆔 ID: {trx_id}\n\n"
                f"💰 Dana akan dikirim dalam 1-5 menit!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {trx_id}")
        
        context.user_data['waiting_withdraw'] = False
        
    except ValueError:
        await update.message.reply_text("❌ Masukkan nominal yang benar! Contoh: 100000|085969081186")

# ========== BACK TO MAIN ==========
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
        await referral_menu(update, context)
    elif data == 'history':
        await history_menu(update, context)
    elif data.startswith('deposit_'):
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
    elif data.startswith('approve_'):
        await admin_approve_deposit(update, context)
    elif data.startswith('reject_'):
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
    print("🎰 JUDOL BOT - WITH ADMIN APPROVAL")
    print("🤖 Bot Started!")
    print("=" * 55)
    print("💳 PAYMENT ACTIVE:")
    print(f"💙 DANA: 085969081186 (YULIANA)")
    print(f"💚 GOPAY: 085969081186 (YULIANA)")
    print("=" * 55)
    print("📝 REGISTRATION:")
    print("User harus register, ADMIN yang approve!")
    print("=" * 55)
    
    application.run_polling()

if __name__ == "__main__":
    main()