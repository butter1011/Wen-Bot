import base64
import logging
import requests
import time
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    Update,
    Bot
)
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    filters,
    Dispatcher, 
    CommandHandler, 
    MessageHandler, 
    Filters
)
import asyncio
from aiohttp import web
from flask import Flask, request

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Telegram bot token
TOKEN = "7459681930:AAFOt3d0hKT7LgFiGfB7sLA9UjNVPPg2-RQ"
SERVER = "https://telegram-1-triend.replit.app"
URL = ''

app = Flask(__name__)
bot = Bot(token=TOKEN)

# Initialize dispatcher
dispatcher = Dispatcher(bot, None, workers=0)

def setInviterUserId(context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get("inviter_id"):
        response = requests.post(f"{SERVER}/api/v2/invite",
                                 json={
                                     "inviter_id":
                                     context.chat_data["inviter_id"],
                                     "user_id": context.chat_data["userId"]
                                 })
        return response


def setUserId(context: ContextTypes.DEFAULT_TYPE):
    # Init the user
    response = requests.post(f"{SERVER}/api/v2/initUser",
                             json={
                                 "user_id": context.chat_data["userId"],
                                 "user_name": context.chat_data["name"],
                                 "picture": context.chat_data["picture"]
                             })

    # Reply Buttons when click '/start'
    startGameButton = InlineKeyboardButton(
        text="💰 Start the Game!",
        web_app=WebAppInfo("https://telegram-1-triend.replit.app/"),
    )

    joinCommunityButton = InlineKeyboardButton(text="👤 Join Community",
                                               url="https://t.me/triendapp")

    configKeyboardMarkup = InlineKeyboardMarkup([[startGameButton],
                                                 [joinCommunityButton]])

    return configKeyboardMarkup


# start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        username = user.username or ""

        context.chat_data["name"] = username
        context.chat_data["userId"] = update.effective_message.chat_id

        picture = await context.bot.get_user_profile_photos(user.id)

        if picture.photos:
            file_id = picture.photos[0][-1].file_id
            file = await context.bot.get_file(file_id)
            image_data = await file.download_as_bytearray()
            context.chat_data["picture"] = base64.b64encode(image_data).decode(
                'utf-8')

        else:
            context.chat_data["picture"] = ""

        # Get User ID
        if update.effective_user:
            print(
                f"Username------------>{update.effective_user.username}\nTime-------------------->{time.strftime('%y/%m/%d %H:%M:%S', time.localtime())}\n"
            )

        args = context.args
        # Set the Inviter Id
        if args:
            inviter_id = args[0]
            context.chat_data["inviter_id"] = inviter_id
            newUser = context.chat_data["userId"]
            response = setInviterUserId(context)

            if response.status_code == 200:
                # Send messages to the inviter and new user.
                await context.bot.send_message(
                    chat_id=inviter_id,
                    text=
                    f"💰You were invited by {response.nickname}. He earned the bonus 4000.💰",
                )

        # Set User
        configKeyboardMarkup = setUserId(context)
        photo_file = open("./public/background.jpg", "rb")

        # Hello Message
        descText = f"""
        Minute-long games can add up to 5 or 10 minutes. Please consider your schedule and enter Wen World at your own caution
        """

        # Send the image with the text
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo_file,
            caption=descText,
            reply_markup=configKeyboardMarkup,
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An error occurred. Please try again later.")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    bot.set_webhook(URL)
    app.run(port=8443)