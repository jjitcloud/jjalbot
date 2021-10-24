import os
import time
import io
import logging
import dataclasses

from google.cloud import storage
from google.cloud import firestore

from telegram import Bot, Document, File, ForceReply, PhotoSize
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (CallbackContext, CommandHandler, Dispatcher, Filters,
                          MessageHandler, Updater)
from telegram.ext import ConversationHandler

from .jjal import JJal

logger = logging.getLogger('jjitjjal')

#'jjit_jjal'
GOOGLE_FIRESTORE_COLLECTION_NAME = os.environ['GOOGLE_FIRESTORE_COLLECTION_NAME']
#'jjit_buckit'
GOOGLE_STORAGE_BUCKET_NAME = os.environ['GOOGLE_STORAGE_BUCKET_NAME']
TELEGRAM_BOT_ADMIN_ID = int(os.environ['TELEGRAM_BOT_ADMIN_ID'])

START_UPLOAD_DOCUMENT_STATUS = 1
ENTER_UPLOAD_DOCUMENT_NAME_STATUS = 2
START_DELETE_DOCUMENT_STATUS = 3
START_PUBLISH_DOCUMENT_STATUS = 4

def start_callback(update: Update, context: CallbackContext) -> None:
    """/start 커맨드 콜백"""
    user = update.message.from_user
    logger.info(f'사용자가 /start 커맨드를 입력했습니다. 유저ID:{user.id}')
    update.message.reply_markdown_v2(
        fr'{user.mention_markdown_v2()}님 화천대유 하세요\! 짤을 출력하려면 짤 이름을 입력해주세요 명령어를 출력하려면 /help 커멘드를 입력하세요',
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data['MUTE_VIEW'] = False


def help_callback(update: Update, context: CallbackContext) -> None:
    """/help 커맨드 콜백"""
    user = update.message.from_user
    logger.info(f'사용자가 /help 커맨드를 입력했습니다. 유저ID:{user.id}')
    update.message.reply_text("""커맨드 일람
/help 도움말을 출력합니다.
/list 공개짤 일람을 출력합니다.
/mylist 개인용짤 일람을 출력합니다.
/upload 새로운 짤을 업로드합니다.
/delete 업로드한 짤을 삭제합니다.""")
    context.user_data['MUTE_VIEW'] = False

def public_documeent_list_callback(update: Update, context: CallbackContext) -> None:
    """/list 커맨드 콜백"""
    user = update.message.from_user
    logger.info(f'사용자가 /list 커맨드를 입력했습니다. 유저ID:{user.id}')

    db = firestore.Client()
    docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where('is_public', '==', True).get()

    if not docs:
        update.message.reply_text(f'공개 짤이 존재하지 않습니다.', reply_markup=ReplyKeyboardRemove())
        return

    names = []
    for doc in docs:
        names.append(doc.get('document_name'))

    else:
        name_text = "\n".join(names)
        update.message.reply_text(name_text, reply_markup=ReplyKeyboardRemove())


def my_documeent_list_callback(update: Update, context: CallbackContext) -> None:
    """/mylist 커맨드 콜백"""
    user = update.message.from_user
    logger.info(f'사용자가 /mylist 커맨드를 입력했습니다. 유저ID:{user.id}')

    db = firestore.Client()
    docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where('user_id', '==', user.id).get()

    if not docs:
        update.message.reply_text(f'개인 짤이 존재하지 않습니다.', reply_markup=ReplyKeyboardRemove())
        return

    names = []
    for doc in docs:
        if(doc.get('is_public')):
            names.append(doc.get('document_name') + '(공개됨)')
        else:
            names.append(doc.get('document_name'))

    name_text = "\n".join(names)
    update.message.reply_text(name_text, reply_markup=ReplyKeyboardRemove())


def document_view_callback(update: Update, context: CallbackContext) -> None:
    """짤 출력 메세지 콜백"""
    user = update.message.from_user
    document_name = update.message.text
    logger.info(f'사용자가 짤 출력 메세지를 입력했습니다. 유저ID:{user.id} document_name:{document_name}')
    db = firestore.Client()
    
    docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where('is_public', '==', False).where('user_id', '==', user.id).where('document_name', '==', document_name).get()

    client = storage.Client()
    bucket = client.get_bucket(GOOGLE_STORAGE_BUCKET_NAME)

    has_photo = False
    for doc in docs:
        #update.message.reply_document(document=)
        jjal = JJal(**doc.to_dict())
        filename = jjal.filename #doc.get('filename')
        blob = bucket.blob(f"u/{filename}")
        file_byte_data = blob.download_as_bytes()
        string_buffer = io.BytesIO(file_byte_data)
        update.message.reply_document(document=string_buffer, filename=filename)
        #update.message.reply_photo(photo=doc.get('public_url'))
        has_photo = True

    docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where('is_public', '==', True).where('document_name', '==', document_name).get()

    for doc in docs:
        jjal = JJal(**doc.to_dict())
        filename = jjal.filename #doc.get('filename')
        blob = bucket.blob(f"u/{filename}")
        file_byte_data = blob.download_as_bytes()
        string_buffer = io.BytesIO(file_byte_data)
        update.message.reply_document(document=string_buffer, filename=filename)
        #update.message.reply_photo(photo=doc.get('public_url'))
        has_photo = True

    if not has_photo:
        update.message.reply_text(f'짤이 존재하지 않습니다.', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

# INSERT

def start_upload_document_callback(update: Update, context: CallbackContext) -> int:
    """문서 등록 시작"""
    user = update.message.from_user
    logger.info(f'사용자가 문서 업로드 대화를 시작했습니다. 유저ID:{user.id}')
    update.message.reply_text('짤 별칭으로 등록할 이름을 입력해주세요.', reply_markup=ReplyKeyboardRemove())
    context.user_data['MUTE_VIEW'] = True
    return START_UPLOAD_DOCUMENT_STATUS


def enter_upload_document_name_callback(update: Update, context: CallbackContext) -> int:
    """짤 별칭 입력"""
    user = update.message.from_user
    document_name = update.message.text
    logger.info(f'사용자가 짤 별칭을 입력했습니다. 유저ID:{user.id} 별칭:{document_name}')
    db = firestore.Client()
    docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where(u'user_id', u'==', user.id).where(u'document_name', u'==', document_name).get()
    if docs:
        update.message.reply_text('이미 등록된 짤 별칭입니다. 다른 별칭을 입력해주세요.', reply_markup=ReplyKeyboardRemove())
        return START_UPLOAD_DOCUMENT_STATUS

    context.user_data['document_name'] = document_name
    update.message.reply_text('10MB이하의 파일을 업로드해주세요. 사진을 업로드하시면 원본이 축소됩니다. 꼭 파일 업로드 기능을 이용해주세요.', reply_markup=ReplyKeyboardRemove())
    context.user_data['MUTE_VIEW'] = True
    return ENTER_UPLOAD_DOCUMENT_NAME_STATUS


def _upload_document(user, file_data: File, file_name: str, mime_type: str, document_name: str) -> str:
    file_byte_data = file_data.download_as_bytearray()
    file_ext = os.path.splitext(file_name)[-1]

    logger.info(f'업로드한 문서. 파일명:{file_name} 확장자:{file_ext} 컨텐츠타입:{mime_type}')

    upload_filename = f"{int(time.time())}{file_ext}"
    client = storage.Client()
    bucket = client.get_bucket(GOOGLE_STORAGE_BUCKET_NAME)
    blob = bucket.blob(f"u/{upload_filename}")

    string_buffer = io.BytesIO(file_byte_data)
    blob.upload_from_file(string_buffer, content_type=mime_type)

    logger.info("문서를 스토리지에 업로드 했습니다.")

    jjal = JJal(
        document_name= document_name,
        public_url= blob.public_url,
        filename= upload_filename,
        content_type= mime_type,
        size= len(file_byte_data),
        user_id= user.id,
        time_stamp= time.time(),
        is_public= False
    )

    db = firestore.Client()
    doc_ref = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).document()
    doc_ref.set(dataclasses.asdict(jjal))

    logger.info("DB에 저장했습니다.")

    return blob.public_url


def upload_document_callback(update: Update, context: CallbackContext) -> int:
    """ """
    user = update.message.from_user
    logger.info(f'사용자가 문서를 업로드했습니다. 유저ID:{user.id}')
    try:
        document_name = context.user_data['document_name']
        document: Document = update.message.document
        file_data: File = document.get_file()
        file_name = document.file_name
        mime_type = document.mime_type

        public_url = _upload_document(user, file_data, file_name, mime_type, document_name)

        update.message.reply_text(f"""파일 업로드에 성공했습니다.
내목록(/mylist)에서 볼수 있습니다. 관리자의 승인후 공개목록에 표시됩니다.
공개URL은 {public_url} 입니다.""")

        context.user_data['MUTE_VIEW'] = False
        return ConversationHandler.END
    except:
        logger.exception("파일 업로드에 실패했습니다.")
        update.message.reply_text(f"파일 업로드에 실패했습니다.")
        context.user_data['MUTE_VIEW'] = False
        return ConversationHandler.END


def upload_photo_callback(update: Update, context: CallbackContext) -> int:
    """ """
    user = update.message.from_user
    logger.info(f'사용자가 사진을 업로드했습니다. 유저ID:{user.id}')
    try:
        document_name = context.user_data['document_name']
        photo: PhotoSize = update.message.photo[-1]
        file_data: File = photo.get_file()
        file_name = photo.file_id + ".jpg"
        mime_type = "image/jpeg"

        public_url = _upload_document(user, file_data, file_name, mime_type, document_name)

        update.message.reply_text(f"""사진 업로드에 성공했습니다. 내목록(/mylist)에서 볼수 있습니다. 관리자의 승인후 공개목록에 표시됩니다.
공개URL은 {public_url} 입니다.""")

        context.user_data['MUTE_VIEW'] = False
        return ConversationHandler.END
    except:
        logger.exception("사진 업로드에 실패했습니다.")
        update.message.reply_text(f"사진 업로드에 실패했습니다.")
        context.user_data['MUTE_VIEW'] = False
        return ConversationHandler.END

# DELETE

def start_delete_document_callback(update: Update, context: CallbackContext) -> int:
    """문서 삭제 시작 핸들러"""
    user = update.message.from_user
    logger.info(f'사용자가 문서 삭제 대화를 시작했습니다. 유저ID:{user.id}')
    update.message.reply_text('삭제할 짤 이름을 입력해주세요.', reply_markup=ReplyKeyboardRemove())

    context.user_data['MUTE_VIEW'] = True
    return START_DELETE_DOCUMENT_STATUS


def delete_document_callback(update: Update, context: CallbackContext) -> int:
    """짤 삭제 별칭 입력 핸들러"""
    user = update.message.from_user
    document_name = update.message.text
    logger.info(f'사용자가 짤 삭제 별칭을 입력했습니다. 유저ID:{user.id} 별칭:{document_name}')
    db = firestore.Client()
    if user.id != TELEGRAM_BOT_ADMIN_ID:
        docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where(u'user_id', u'==', user.id).where(u'document_name', u'==', document_name).get()
    else:
        docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where(u'document_name', u'==', document_name).get()

    client = storage.Client()
    bucket = client.get_bucket(GOOGLE_STORAGE_BUCKET_NAME)

    for doc in docs:
        
        logger.info(f'문서를 삭제합니다. {doc.id} => {doc.to_dict()}')
        filename = doc.get('filename')
        blob = bucket.blob(f"u/{filename}")
        blob.delete()
        db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).document(doc.id).delete()

    update.message.reply_text(f'{document_name} 짤을 삭제했습니다.', reply_markup=ReplyKeyboardRemove())

    context.user_data['MUTE_VIEW'] = False
    return ConversationHandler.END

# 관리자용

def start_publish_document_callback(update: Update, context: CallbackContext) -> int:
    """문서 공개 시작 핸들러"""
    user = update.message.from_user
    logger.info(f'사용자가 문서 공개 대화를 시작했습니다. 유저ID:{user.id} 관리자ID:{TELEGRAM_BOT_ADMIN_ID}')
    if user.id != TELEGRAM_BOT_ADMIN_ID:
        update.message.reply_text('관리자만 공개 가능합니다.', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    update.message.reply_text('공개할 짤 이름을 입력해주세요.', reply_markup=ReplyKeyboardRemove())

    context.user_data['MUTE_VIEW'] = True

    return START_PUBLISH_DOCUMENT_STATUS


def publish_document_callback(update: Update, context: CallbackContext) -> int:
    """문서 공개 핸들러"""
    user = update.message.from_user
    document_name = update.message.text
    logger.info(f'사용자가 문서 공개 별칭을 입력했습니다. 유저ID:{user.id} 별칭:{document_name}')

    if user.id != TELEGRAM_BOT_ADMIN_ID:
        update.message.reply_text('관리자만 공개 가능합니다.', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    db = firestore.Client()
    docs = db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).where(u'document_name', u'==', document_name).get()

    is_updated = False
    for doc in docs:
        logger.info(f'문서를 공개합니다. {doc.id} => {doc.to_dict()}')
        if doc.get('is_public'):
            logger.info(f'이미 공개된 문서입니다. {doc.id} => {doc.to_dict()}')
            update.message.reply_text(f'{document_name}는 이미 공개된 짤입니다.', reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        else:
            db.collection(GOOGLE_FIRESTORE_COLLECTION_NAME).document(doc.id).update({'is_public': True})
            is_updated = True

    if is_updated:
        update.message.reply_text(f'{document_name} 짤을 공개했습니다.', reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'{document_name} 짤이 존재하지 않습니다.', reply_markup=ReplyKeyboardRemove())

    context.user_data['MUTE_VIEW'] = False
    return ConversationHandler.END


def cancel_callback(update: Update, context: CallbackContext) -> int:
    """취소 콜백."""
    user = update.message.from_user
    logger.info(f'사용자가 /cancel 커맨드를 입력했습니다. 유저ID:{user.id}')
    update.message.reply_text('작업을 취소했습니다.', reply_markup=ReplyKeyboardRemove())

    context.user_data['MUTE_VIEW'] = False
    return ConversationHandler.END


document_upload_handler = ConversationHandler(
    entry_points=[CommandHandler('upload', start_upload_document_callback)],
    states={
        START_UPLOAD_DOCUMENT_STATUS: [MessageHandler(Filters.text & ~Filters.command, enter_upload_document_name_callback)],
        ENTER_UPLOAD_DOCUMENT_NAME_STATUS: [
            MessageHandler(Filters.photo, upload_photo_callback),
            MessageHandler(Filters.document, upload_document_callback),
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_callback)],
)


document_delete_handler = ConversationHandler(
    entry_points=[CommandHandler('delete', start_delete_document_callback)],
    states={
        START_DELETE_DOCUMENT_STATUS: [MessageHandler(Filters.text & ~Filters.command, delete_document_callback)],
    },
    fallbacks=[CommandHandler('cancel', cancel_callback)],
)

document_publish_handler = ConversationHandler(
    entry_points=[CommandHandler('publish', start_publish_document_callback)],
    states={
        START_PUBLISH_DOCUMENT_STATUS: [MessageHandler(Filters.text & ~Filters.command, publish_document_callback)],
    },
    fallbacks=[CommandHandler('cancel', cancel_callback)],
)

start_handler = CommandHandler('start', start_callback)
help_handler = CommandHandler('help', help_callback)
document_list_handler = CommandHandler('list', public_documeent_list_callback)
my_document_list_handler = CommandHandler('mylist', my_documeent_list_callback)
document_view_handler = MessageHandler(Filters.text & ~Filters.command, document_view_callback)
