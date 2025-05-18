import telebot
import requests
import threading
import time
from datetime import datetime

BOT_TOKEN = "7764475888:AAGUykeeKTrj7hiwNKLIJrW_TQ1EljC79fA"
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['myid'])
def send_chat_id(message):
    bot.reply_to(
        message, f"🔍 Your chat ID: `{message.chat.id}`", parse_mode="Markdown")


# Store chats for auto-send (add your chat ID here)
AUTO_SEND_CHATS = [8148920664, ]  # 1804297570

# ===== 1. GREETING =====


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    username = message.from_user.username
    if username:
        bot.reply_to(
            message, f"Hello @{username}! Want a meme or a joke? Just ask! 😆")
    else:
        bot.reply_to(message, "Hello there! Ask for a meme or joke!")

# ===== 2. MEME API =====


def get_meme():
    try:
        response = requests.get("https://meme-api.com/gimme")
        data = response.json()
        return data['url'], None  # Return meme URL
    except:
        return None, "Failed to fetch meme. Try again later! 😅"

# ===== 3. JOKE API =====


def get_joke():
    try:
        response = requests.get(
            "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious")
        data = response.json()
        if data['type'] == "single":
            return data['joke'], None
        else:
            # Two-part joke
            return f"{data['setup']}\n\n{data['delivery']}", None
    except:
        return None, "Joke service is down. Oops! 🤖"


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
        bot.reply_to(message, f"🎭 Joke for you:\n\n{joke}")
    else:
        bot.reply_to(message, error)

# ===== 5. AUTO-SEND EVERY 1 MINUTE =====


def auto_send():
    while True:
        try:
            for chat_id in AUTO_SEND_CHATS:
                # Alternate between meme and joke
                if int(time.time()) % 2 == 0:
                    content, error = get_meme()
                    caption = "⏰ Scheduled Meme Delivery! 🚀"
                    if content:
                        bot.send_photo(chat_id, content, caption=caption)
                else:
                    content, error = get_joke()
                    caption = "⏰ Scheduled Joke Delivery! 🎤"
                    if content:
                        bot.send_message(chat_id, f"{caption}\n\n{content}")
            time.sleep(60)  # 1-minute interval
        except Exception as e:
            print(f"Auto-send error: {e}")
            time.sleep(30)

# ===== 6. ADMIN CONTROLS =====


@bot.message_handler(commands=['start_auto'])
def enable_auto(message):
    if message.chat.id not in AUTO_SEND_CHATS:
        AUTO_SEND_CHATS.append(message.chat.id)
        bot.reply_to(
            message, "✅ Auto memes/jokes enabled! Sending every 1 minute.")
    else:
        bot.reply_to(message, "❌ Already enabled here.")


@bot.message_handler(commands=['stop_auto'])
def disable_auto(message):
    if message.chat.id in AUTO_SEND_CHATS:
        AUTO_SEND_CHATS.remove(message.chat.id)
        bot.reply_to(message, "❌ Auto-send disabled.")
    else:
        bot.reply_to(message, "❌ Not active here.")


# ===== START THREAD & BOT =====
threading.Thread(target=auto_send, daemon=True).start()
print("Bot is running...")
bot.infinity_polling()
