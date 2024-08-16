import base64
import logging
import requests
import time
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    Update,
)
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    filters,
)
import asyncio
from aiohttp import web

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Telegram bot token
SERVER = "https://triend-wenworldgame-05ef17649d0d.herokuapp.com"
# TOKEN = "7459681930:AAFOt3d0hKT7LgFiGfB7sLA9UjNVPPg2-RQ"

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
        web_app=WebAppInfo("https://triend-wenworldgame-05ef17649d0d.herokuapp.com/"),
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


# Webhook handler
async def handle(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return web.Response()


if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    # Add handler to the bot
    application.add_handler(CommandHandler("start", start))
    # If running on Windows, set the event loop policy accordingly
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    application.run_polling(allowed_updates=Update.ALL_TYPES)
