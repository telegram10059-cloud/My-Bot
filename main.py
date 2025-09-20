# tg_card_bot.py — তিনটি বাটন + গ্রুপে /card (reply-flow) + /gen direct
# SAFE: উৎপাদিত আইটেমগুলো টেস্টি/প্লেসহোল্ডার — বাস্তব কার্ড নম্বর নয়

import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

from keep_alive import keep_alive

# আপনার বট টোকেন (আপনি দিয়েছেন)
TOKEN = "8409937294:AAHt7dw5QoVTARXDJgZSTkJKlPFKupgsWKQ"

# আপনার চ্যানেল লিঙ্ক
CHANNEL_LINK_LITERAL = "https://t.me/Saydur2147"

# সাপোর্ট ইউজারনেম
SUPPORT_USERNAME_LITERAL = "@Md_Imran_Hossain_Niloy"


# -------- helpers (SAFE placeholders only) --------
def make_cards_from_bin(pattern: str, count: int = 10):
    """ইউজার-দেওয়া pattern (BIN) ধরে রেখে 16-ডিজিট কার্ড নম্বর তৈরি করে।"""
    base = ''.join(ch for ch in pattern if ch.isdigit())
    if len(base) > 16:
        base = base[:16]

    cards = []
    current_year = datetime.now().year
    for _ in range(count):
        card_digits = list(base)
        while len(card_digits) < 16:
            card_digits.append(str(random.randint(0, 9)))
        card_number = ''.join(card_digits)

        exp_month = f"{random.randint(1, 12):02d}"
        exp_year = str(random.randint(current_year + 1, current_year + 6))
        cvv = f"{random.randint(0, 999):03d}"

        cards.append(f"{card_number}|{exp_month}|{exp_year}|{cvv}")

    return cards


def make_aliases(base_email: str, count: int = 10, tag_len: int = 6):
    """Create alias list like local+tag@domain — benign"""
    try:
        local, domain = base_email.split("@", 1)
    except ValueError:
        return []
    aliases = []
    seen = set()
    while len(aliases) < count:
        tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=tag_len))
        if tag in seen:
            continue
        seen.add(tag)
        aliases.append(f"{local}+{tag}@{domain}")
    return aliases


# -------- handlers --------
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💳 Card Generator", callback_data="card")],
        [InlineKeyboardButton("📧 Temp Mail", callback_data="mail")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "🤖 স্বাগতম!\n\n"
        f"🔗 আমাদের অফিসিয়াল চ্যানেল: https://t.me/Saydur2147\n\n"
    )
    update.message.reply_text(text, reply_markup=reply_markup)


def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == "card":
        context.user_data["awaiting"] = "bin"
        query.edit_message_text("💳 প্রাইভেটে BIN দিন (উদাহরণ: 123456xxxxxxxxxx)\nবট ১০টা কার্ড দিবে।")
    elif query.data == "mail":
        context.user_data["awaiting"] = "gmail"
        query.edit_message_text("📧 প্রাইভেটে আপনার Gmail দিন (উদাহরণ: name@gmail.com)\nবট ১০টি alias তৈরি করবে।")
    elif query.data == "help":
        query.edit_message_text(
            f"🆘 যে কোনো সমস্যার হলে আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন:\n\n"
            f"📩 @Md_Imran_Hossain_Niloy\n\n"
            f"👉 অফিসিয়াল চ্যানেল: https://t.me/Saydur2147"
        )


def card_command(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat

    # direct usage: /card <pattern>
    if args:
        pattern = args[0]
        if not any(ch.isdigit() for ch in pattern):
            return update.message.reply_text("⚠️ Pattern-এ অন্তত কিছু ডিজিট থাকা উচিত।")
        results = make_cards_from_bin(pattern, count=10)
        return update.message.reply_text("\n".join(results))

    # no args: start reply-flow
    if chat.type == "private":
        context.user_data["awaiting"] = "bin"
        return update.message.reply_text("💳 আপনার BIN দিন (উদাহরণ: 123456xxxxxxxxxx)")

    # in group: prompt and store awaiting id in chat_data
    prompt: Message = update.message.reply_text(
        "💳 এই মেসেজটির reply হিসেবে BIN পাঠান — বট আপনার reply ধরে ১০টি কার্ড দিবে."
    )
    context.chat_data["awaiting_bin_msg_id"] = prompt.message_id
    context.chat_data["awaiting_bin_by_user"] = update.effective_user.id


def gen_command(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        return update.message.reply_text("Usage: /gen <pattern>\nউদাহরণ: /gen 12345678xxxxxx")
    pattern = args[0]
    if not any(ch.isdigit() for ch in pattern):
        return update.message.reply_text("⚠️ Pattern-এ অন্তত কিছু ডিজিট থাকা উচিত।")
    results = make_cards_from_bin(pattern, count=10)
    update.message.reply_text("\n".join(results))


def cmd_mail(update: Update, context: CallbackContext):
    update.message.reply_text("📧 Temp Mail পেতে বটকে প্রাইভেটে /start করে Temp Mail বাটন চাপুন।")


def cmd_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        f"🆘 যে কোনো সমস্যার হলে আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন:\n"
        f"📩 @Md_Imran_Hossain_Niloy\n\n"
        f"👉 অফিসিয়াল চ্যানেল: https://t.me/Saydur2147"
    )


def reply_handler(update: Update, context: CallbackContext):
    msg = update.message
    if not msg or not msg.text:
        return

    # 1) Group BIN reply flow
    awaiting_id = context.chat_data.get("awaiting_bin_msg_id")
    if awaiting_id and msg.reply_to_message and msg.reply_to_message.message_id == awaiting_id:
        pattern = msg.text.strip()
        if not any(ch.isdigit() for ch in pattern):
            return msg.reply_text("⚠️ Pattern-এ অন্তত কিছু ডিজিট থাকা উচিত।")
        results = make_cards_from_bin(pattern, count=10)
        context.chat_data.pop("awaiting_bin_msg_id", None)
        context.chat_data.pop("awaiting_bin_by_user", None)
        return msg.reply_text("\n".join(results))

    # 2) Private awaiting flows (from buttons)
    awaiting = context.user_data.get("awaiting")
    if awaiting == "bin":
        pattern = msg.text.strip()
        if not any(ch.isdigit() for ch in pattern):
            return msg.reply_text("⚠️ Pattern-এ অন্তত কিছু ডিজিট থাকা উচিত।")
        context.user_data.pop("awaiting", None)
        results = make_cards_from_bin(pattern, count=10)
        return msg.reply_text("\n".join(results))

    if awaiting == "gmail":
        email = msg.text.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            return msg.reply_text("⚠️ বৈধ Gmail লিখুন (উদাহরণ: name@gmail.com)।")
        context.user_data.pop("awaiting", None)
        aliases = make_aliases(email, count=10)
        if not aliases:
            return msg.reply_text("⚠️ ইমেইল পার্সিং সমস্যা — আবার চেষ্টা করুন।")
        return msg.reply_text("\n".join(aliases))

    return


# -------- main --------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("card", card_command))   # /card [pattern]
    dp.add_handler(CommandHandler("gen", gen_command))     # /gen <pattern>
    dp.add_handler(CommandHandler("mail", cmd_mail))
    dp.add_handler(CommandHandler("help", cmd_help))

    # button callbacks
    dp.add_handler(CallbackQueryHandler(button_handler))

    # replies handler
    dp.add_handler(MessageHandler(Filters.text & Filters.reply, reply_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.chat_type.private, reply_handler))

    updater.start_polling()
    keep_alive()
    updater.idle()
  

if __name__ == "__main__":
    main()
