import requests

from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, ChosenInlineResultHandler, CallbackQueryHandler
import logging

import re
import os

TOKEN = os.environ["TG_TOKEN"]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

_url_regex = re.compile(r'^((https?|ftp):\/\/[^\s/$.?#].[^\s]*)$')


def valid_url(url):
    return bool(_url_regex.match(url))


def start(bot, update):
    update.message.reply_text('Please use this bot inline')


def help(bot, update):
    update.message.reply_text('Type "@jelbzbot <link>" to shorten your url')


def escape_markdown(text):
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)


def error(bot, update, error):
    logger.warn("Update {} caused error {}".format(update, error))


def inlinequery(bot, update):
    query = escape_markdown(update.inline_query.query)
    results = list()
    keyboard = [[
        InlineKeyboardButton(
            "Generating...", callback_data='nuffin')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if valid_url(query):
        results = [
            InlineQueryResultArticle(
                id="public",
                title="public",
                description="Create a short link",
                reply_markup=reply_markup,
                input_message_content=InputTextMessageContent(
                    "Generating link...")), InlineQueryResultArticle(
                        id="private",
                        title="private",
                        description="Create a slightly longer private link",
                        reply_markup=reply_markup,
                        input_message_content=InputTextMessageContent(
                            "Generating link..."))
        ]
    update.inline_query.answer(results=results, cache_time=0)


def generatelink(bot, update):
    message_id = update.chosen_inline_result.inline_message_id
    result_id = update.chosen_inline_result.result_id
    query = update.chosen_inline_result.query

    if result_id == "public":
        secret = ""
    else:
        secret = "true"

    r = requests.post(
        "https://jel.bz/urls/", data={"url": query,
                                      "secret": secret})
    if r.status_code == 200:
        link = "https://jel.bz/" + r.json()["message"]
    else:
        link = r.json()["message"]
    bot.editMessageText(inline_message_id=message_id, text=link)


def button(bot, update):
    pass


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(InlineQueryHandler(inlinequery))
    dp.add_handler(ChosenInlineResultHandler(generatelink))
    # on callback
    dp.add_handler(CallbackQueryHandler(button))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
