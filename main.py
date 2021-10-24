import os
import time
import io
import logging

from google.cloud import storage
from google.cloud import firestore

from telegram import Bot, Document, File, ForceReply, PhotoSize
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (CallbackContext, CommandHandler, Dispatcher, Filters,
                          MessageHandler, Updater)
from telegram.ext import ConversationHandler
from commons import common

common.setup_logging()

from commons import bot_handler


logger = logging.getLogger("jjitjjal")


telegram_bot_token = os.environ.get('TELEGRAM_TOKEN')
if not telegram_bot_token:
    raise common.MissingEnvironmentVariable(f'TELEGRAM_TOKEN does not exist')

# TELEGRAM_BOT_ADMIN_ID:1624261534
updater = Updater(token=telegram_bot_token)

dispatcher = updater.dispatcher

# 문서등록  핸들러
dispatcher.add_handler(bot_handler.document_upload_handler)
dispatcher.add_handler(bot_handler.document_delete_handler)
dispatcher.add_handler(bot_handler.document_publish_handler)
dispatcher.add_handler(bot_handler.start_handler)
dispatcher.add_handler(bot_handler.help_handler)
dispatcher.add_handler(bot_handler.document_list_handler)
dispatcher.add_handler(bot_handler.my_document_list_handler)
dispatcher.add_handler(bot_handler.document_view_handler)

def webhook(request):
    logger.info(f"webhook start method:{request.method}")

    if request.method == "POST":
        json_data = request.get_json(force=True)
        logger.debug(f"json_data:{json_data}")
        dispatcher.process_update(Update.de_json(json_data, updater.bot))

    logger.info("webhook end")
    return "ok"
