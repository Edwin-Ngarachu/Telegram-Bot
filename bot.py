import telebot
import requests
import threading
import time
import os
from datetime import datetime

# Get token from Railway environment variables
BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = telebot.TeleBot(BOT_TOKEN)


user_prefs = {}
AUTO_SEND_CHATS = [8148920664]  # Your chat ID

# ===== 1. MEME FUNCTION =====


def get_meme():
    try:
        response = requests.get("https://meme-api.com/gimme", timeout=5)
        data = response.json()
        return data['url'], None
    except Exception as e:
        return None, f"⚠️ Meme error: {str(e)}"

# ===== 2. JOKE FUNCTION =====


def get_joke():
    try:
        response = requests.get(
            "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious",
            timeout=5
        )
        data = response.json()
        if data['type'] == "single":
            return data['joke'], None
        else:
            return f"{data['setup']}\n\n{data['delivery']}", None
    except Exception as e:
        return None, f"⚠️ Joke error: {str(e)}"

# ===== 3. QUOTE FUNCTION (SINGLE API) =====


def get_quote():
    apis = [
        ("https://stoic-quotes.com/api/quote",
         lambda d: f'"{d["text"]}"\n— {d["author"]}'),
        ("https://zenquotes.io/api/random",
         lambda d: f'"{d[0]["q"]}"\n— {d[0]["a"]}'),
        ("https://api.goprogram.ai/inspiration",
         lambda d: f'"{d["quote"]}"\n— {d["author"]}')
    ]

    for url, parser in apis:
        try:
            response = requests.get(url, timeout=3)
            data = response.json()
            return parser(data), None
        except:
            continue

    return None, "All quote services failed. Try again later!"

# ===== 4. SCHEDULER =====


def send_scheduled_content():
    while True:
        now = datetime.now().strftime("%H:%M")
        for chat_id, prefs in user_prefs.copy().items():
            if prefs.get('scheduled_time') == now:
                content_type = prefs.get('content_type', 'quote')

                if content_type == "meme":
                    content, error = get_meme()
                    if content:
                        bot.send_photo(chat_id, content,
                                       caption="⏰ Your Daily Meme!")
                elif content_type == "joke":
                    content, error = get_joke()
                    if content:
                        bot.send_message(
                            chat_id, f"⏰ Daily Joke:\n\n{content}")
                elif content_type == "quote":
                    content, error = get_quote()
                    if content:
                        bot.send_message(
                            chat_id, f"⏰ Daily Motivation:\n\n{content}")

                if error:
                    bot.send_message(chat_id, error)
        time.sleep(60)

# ===== 5. COMMAND HANDLERS =====


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    text = """
    Hi there! I can send you:
    - 😂 Memes (say "meme" or "make me laugh")
    - 🎭 Jokes (say "joke" or "tell me a joke")
    - 💬 Quotes (say "quote" or "motivate me")
    
    Try /schedule to set daily content!
    """
    bot.reply_to(message, text)


@bot.message_handler(commands=['myid'])
def send_chat_id(message):
    bot.reply_to(
        message, f"🔍 Your chat ID: `{message.chat.id}`", parse_mode="Markdown")


@bot.message_handler(commands=['quote', 'motivate'])
def send_quote_cmd(message):
    quote, error = get_quote()
    if quote:
        bot.reply_to(message, f"💬 Quote:\n\n{quote}")
    else:
        bot.reply_to(message, error)

# ===== 6. KEYWORD TRIGGERS =====


@bot.message_handler(func=lambda msg: any(
    word in msg.text.lower() for word in ["meme", "funny", "laugh", "make me laugh"]
))
def send_meme(message):
    meme_url, error = get_meme()
    if meme_url:
        bot.send_photo(message.chat.id, meme_url,
                       caption="😂 Here's your meme!")
    else:
        bot.reply_to(message, error)


@bot.message_handler(func=lambda msg: any(
    word in msg.text.lower() for word in ["joke", "tell me a joke", "crack me up"]
))
def send_joke(message):
    joke, error = get_joke()
    if joke:
        bot.reply_to(message, f"🎭 Joke:\n\n{joke}")
    else:
        bot.reply_to(message, error)


@bot.message_handler(func=lambda msg: any(
    word in msg.text.lower() for word in ["quote", "motivate", "inspire", "wisdom", "motivation"]
))
def send_quote_trigger(message):
    quote, error = get_quote()
    if quote:
        bot.reply_to(message, f"💬 Here's some wisdom:\n\n{quote}")
    else:
        bot.reply_to(message, error)

# ===== 7. SCHEDULING SYSTEM =====


@bot.message_handler(commands=['schedule'])
def set_schedule(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("🌅 Morning (8 AM)", "☀️ Afternoon (1 PM)", "🌙 Evening (7 PM)")
    msg = bot.reply_to(
        message, "⏰ When should I send content?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_time_selection)


def process_time_selection(message):
    time_map = {
        "🌅 Morning (8 AM)": "08:00",
        "☀️ Afternoon (1 PM)": "13:00",
        "🌙 Evening (7 PM)": "19:00"
    }

    if message.text not in time_map:
        bot.send_message(
            message.chat.id, "❌ Invalid choice. Use /schedule to try again.")
        return

    user_prefs[message.chat.id] = {'scheduled_time': time_map[message.text]}

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Memes", "Jokes", "Quotes")
    msg = bot.reply_to(
        message, "🎁 What content would you like?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_content_selection)


def process_content_selection(message):
    if message.text.lower() not in ["memes", "jokes", "quotes"]:
        bot.send_message(
            message.chat.id, "❌ Invalid choice. Use /schedule to try again.")
        return

    user_prefs[message.chat.id]['content_type'] = message.text.lower()[
        :-1]  # Remove 's'
    bot.send_message(message.chat.id,
                     f"✅ Scheduled! You'll get {message.text} daily at {user_prefs[message.chat.id]['scheduled_time']}")

# ===== 8. AUTO-SEND SYSTEM =====


def auto_send():
    while True:
        try:
            for chat_id in AUTO_SEND_CHATS:
                if int(time.time()) % 2 == 0:
                    content, error = get_meme()
                    if content:
                        bot.send_photo(chat_id, content,
                                       caption="⏰ Scheduled Meme!")
                else:
                    content, error = get_joke()
                    if content:
                        bot.send_message(
                            chat_id, f"⏰ Scheduled Joke:\n\n{content}")
            time.sleep(3600)
        except Exception as e:
            print(f"Auto-send error: {e}")
            time.sleep(30)


# ===== 9. START THREADS =====
threading.Thread(target=auto_send, daemon=True).start()
threading.Thread(target=send_scheduled_content, daemon=True).start()

print("🤖 Bot is running with all features!")
bot.infinity_polling()
