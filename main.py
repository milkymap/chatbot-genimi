import click 
import hashlib

from Crypto.Cipher import AES 
from Crypto.Util.Padding import pad, unpad  
from Crypto.Protocol.KDF import PBKDF2

import asyncio
import aiohttp
import requests

import logging
import loguru 

import numpy as np 
import operator as op 

import json, pickle   

from io import BytesIO

from telegram import ReplyKeyboardRemove, Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    ContextTypes,
    MessageHandler,
    CommandHandler, 
    ConversationHandler, 
    filters 
)

from database import french_words
usefull_words = [ item['label'] for item in french_words if item['type'] == 'subst.' ]

textes = [
    """
    De nos jours, la lecture devient de moins en moins pratiquée, chez les jeunes comme chez les
    adultes, malgré ses nombreux avantages.
    """,
    """
    D'abord, la lecture développe l'imagination et la créativité. La lecture est une ouverture sur un
    monde enchanté qui nous fait rejoindre les auteur. On s'identifie au héros, on épouse ses
    aventures, ses sentiments ; on sort ainsi de nous-mêmes et on vit plusieurs vies.
    """, 
    """
    Ensuite, le fait de lire aide à enrichir son vocabulaire et à renforcer son emprise sur la langue.
    Chaque fois que nous lisons un nouveau roman ou une fiction, nous rencontrons plusieurs
    mots nouveaux.
    """, 
    """
    De plus, la lecture est une source de divertissement. Tout comme les spectacles, les jeux et le
    sport, elle nous procure un plaisir en nous faisant oublier nos soucis.
    """, 
    """
    En outre, elle est un moyen de développement personnel. Lire élargit nos connaissances.
    Enfin, c'est une activité culturelle importante qui rend les gens plus ouverts et plus tolérants.
    C'est pour cela qu'il devient très important d'encourager et d'entretenir l'acte de lire, partout et
    tous les jours.
    """, 
    """
    Lorsque nous sommes entièrement honnêtes, nous avons la paix de l'esprit et nous gardons
    notre respect de nous-mêmes. Nous acquérons une plus grande force de caractère; et nous
    sommes dignes de confiance aux yeux des personnes de notre entourage.
    """, 
    """
    En revanche, si nous sommes malhonnêtes en paroles ou en actions, nous nous faisons du mal
    et souvent aussi aux autres. Si nous mentons, volons, trichons, ou négligeons de fournir un
    travail complet pour notre salaire, nous perdons le respect de nous-mêmes et celui des
    membres de notre famille et de nos amis.
    """, 
    """
    Être honnête demande souvent du courage et des sacrifices, surtout quand les gens essaient de
    nous persuader de justifier un comportement malhonnête. Si nous nous trouvons dans une
    telle situation, souvenons-nous que la paix durable qu'apporte l'honnêteté vaut plus que le
    soulagement momentané qui découle du fait de faire comme tout le monde.
    """
]

src_history = []
tgt_history = []

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO 
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    reply_keyboard = [['YES', 'NO']]
    loguru.logger.debug(f'First name : {user.first_name} join the chat')
    await update.message.reply_text(
        "welcome to genimi-chat AI\n"
        "do you want to make an evaluation ?"
        "please choose an option", 
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            input_field_placeholder="YES ou NO"
        )
    )
    return 0 

async def handle_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global src_history
    global tgt_history
    user = update.message.from_user
    user_response = update.message.text
    if user_response == 'YES':
        reply_keyboard = [['Lecture'], ['Comprehension']]
        loguru.logger.debug(f'First name : {user.first_name} join the chat')
        await update.message.reply_text(
            "great, you choose to make an evaluation"
            "you can choose between [Lecture or Comprehension]"
            "please choose an option", 
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, 
                one_time_keyboard=True, 
                input_field_placeholder="Lecture ou Comprehension"
            )
        )
        return 1
    else:
        if len(src_history) > 0:
            logger.debug('an evaluation was made')
            response = requests.post(
                url='http://localhost:8500/scoring',
                data=json.dumps({
                    'source': src_history,
                    'target': tgt_history
                })
            )
            response_map = response.json()
            print(response_map)
            scores = response_map['contents']['scores']
            await update.message.reply_text(
                'evaluation is done\n' 
                'here is your score\n'
                f'lexical score : {scores["lexic"]} errors\n\n'
                f'semantic score : {scores["semantic"]}\n\n'
                'thanks for using our api' 
            )
            src_history = []
            tgt_history = []
        else:
            await update.message.reply_text("ummm, ok, hope we will meet gain")
    return ConversationHandler.END

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_response = update.message.text
    if user_response == 'Lecture':
        if np.random.random() < 0.5:
            picked_index = np.random.choice(range(len(usefull_words)), size=5, replace=False)
            picked_word = list(op.itemgetter(*picked_index)(usefull_words))
            src_history.append(' '.join(picked_word))
            order = "\n".join(picked_word)
            await update.message.reply_text(
                "please, read the next words in order\n\n" + order 
            )
        else:
            picked_text = np.random.choice(textes)
            src_history.append(picked_text)
            await update.message.reply_text(
                "please, read the next text\n\n" + picked_text 
            )
        return 2
    await update.message.reply_tex("this option is not available")
    return ConversationHandler.END

async def upload_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global src_history
    global tgt_history
    
    user = update.message.from_user
    loguru.logger.debug(f'First name : {user.first_name} sent an audio for prediction')
    audio_stream = await update.message.voice.get_file()
    audio_bytearray = await audio_stream.download_as_bytearray()
    audio_iostream = BytesIO(audio_bytearray)

        
    response = requests.post(
        url='http://localhost:8500/transcript',
        files={'incoming_audio': audio_iostream}
    )

    response_map = response.json()
    transcripion = response_map['contents']['contents']
    tgt_history.append(transcripion)
    reply_keyboard = [['YES', 'NO']]
    for lft, rgt in zip(src_history, tgt_history):
        print(lft, rgt)

    await update.message.reply_text(f'transcription : {transcripion}')
    await update.message.reply_text(
        'oh great, your voice was saved and processed'
        'do you wanna keep the evaluation?'
        'if yes, choose an option', 
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            input_field_placeholder="YES ou NO"
        )
    )
    return 0 
    
async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    loguru.logger.debug(f'First name : {user.first_name} leave the chat')
    await update.message.reply_text(
        "c'était un plaisir."
        "Bien des choses à vous"
    )
    return ConversationHandler.END

@click.command()
@click.option('--path2token', help='path to encrypted token file', type=click.Path(True), required=True)
@click.option('--password', help='AES password', hide_input=True, prompt=True, confirmation_prompt=True)
def entrypoint(path2token, password):
    salt = hashlib.sha256(password.encode()).digest()
    aes_key = PBKDF2(password, salt, 32)
    with open(path2token, 'rb') as fp:
        iv = fp.read(16)
        encrypted_token = fp.read()
    
    encryptor = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted_token = unpad(encryptor.decrypt(encrypted_token), AES.block_size).decode()

    try:
        app = Application.builder().token(decrypted_token).build()
        # add start and close handler 
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={  
                0: [ MessageHandler(filters.TEXT, handle_option) ],
                1: [ MessageHandler(filters.TEXT, handle_task) ],
                2: [ MessageHandler(filters.AUDIO | filters.VOICE, upload_audio) ]
            },
            fallbacks=[CommandHandler('close', close)]
        )

        app.add_handler(conv_handler)
        
        app.run_polling()
    except Exception as e:
        logger.error(e)
    

if __name__ == '__main__':
    entrypoint()