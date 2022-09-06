from stringprep import map_table_b2
import click 
import hashlib

from Crypto.Cipher import AES 
from Crypto.Util.Padding import pad, unpad  
from Crypto.Protocol.KDF import PBKDF2

import asyncio
import aiohttp
import requests

from tabulate import tabulate

import logging

import numpy as np 
import operator as op 

import pandas as pd 
import json, pickle   

from io import BytesIO
from plot import build_position
from nltk.metrics import edit_distance

import io 
from os import path 
from pydub import AudioSegment
from sentence_transformers import SentenceTransformer, util

from telegram import ReplyKeyboardRemove, Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    ContextTypes,
    MessageHandler,
    CommandHandler, 
    ConversationHandler, 
    filters 
)
from database import quiz
map_teacher2student = {}

with open('map_student2level.pkl', 'rb') as  fp:
    map_student2level = pickle.load(fp)
    for key,val in map_student2level.items():
        print(key, val)

model_name = 'distiluse-base-multilingual-cased-v1'
if path.isfile(model_name):
    with open(model_name, 'rb') as fp:
        model = pickle.load(fp)
else:
    print('model will be downloaded')
    model = SentenceTransformer(model_name)
    with open(model_name, 'wb') as fp:
        pickle.dump(model, fp)

print(model)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO 
)
logger = logging.getLogger(__name__)

def get_duration(audio_stream):
    audio_segment = AudioSegment.from_file(audio_stream).set_frame_rate(16000)
    duration = audio_segment.duration_seconds 
    return duration 
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.debug(f'First name : {user.first_name} has join the chat')
    
    await update.message.reply_text(
        "Bonjour, bienvenu sur le chatbot GENIMI AI\n"
        "Ce chatbot vous permet d'évaluer les élèves\n"
        "Notre but est de reveiller le genie qui sommeille en vous!"
        "Merci de vous authentifier en donnant votre nom et prenom\n"
    )
    return 0 

async def handle_authentification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user 
    received_message = update.message.text
    reply_keyboard = [['CM1'], ['CM2']]
    logger.debug(f'{received_message} was connected to the system')
    outgoing_message = f"""{received_message}, merci d'avoir choisi notre système. Pour continuer, veuillez choisir le niveau de l'élève"""
    map_teacher2student[user.first_name] = {
        'pseudo': received_message
    } 
    await update.message.reply_text(
        outgoing_message,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            input_field_placeholder="CM1 ou CM2"
        )
    
    )
    return 1 

async def handle_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user 
    received_message = update.message.text
    pseudo = map_teacher2student[user.first_name]['pseudo']

    outgoing_message = f"""{pseudo}, vous y êtes presque :).Merci de choisir un elève parmi la liste suivante :""" 
    reply_keyboard = [ [key] for key in map_student2level.keys() ]
    map_teacher2student[user.first_name]['level'] = received_message

    await update.message.reply_text(
        outgoing_message, 
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True,
        )
    )
    return 2 

async def handle_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user 
    received_message = update.message.text
    selected_student = map_student2level[received_message]
    map_teacher2student[user.first_name]['student'] = selected_student 
    reply_keyboard = [['LECTURE'], ['COMPREHENSION']]
    await update.message.reply_text(
        f"Vous avez choisi l'élève :\n{received_message}. "
        "Merci de choisir la matière de lévaluation",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True,
        )
    )
    return 3 

async def handle_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user 
    received_message = update.message.text
    if received_message == 'LECTURE': 
        map_teacher2student[user.first_name]['domain'] = received_message 
        selected_student = map_teacher2student[user.first_name]['student']
        
        selected_student = map_teacher2student[user.first_name]['student']
        student_name = str(selected_student['identité_utilisateur']) + '-' + selected_student['nom']
        io_stream = build_position(map_teacher2student[user.first_name]['student'], 0)
        await update.message.reply_photo(io_stream, f"position actuelle de l'élève : {student_name}")
        
        outgoing_message = "Veillez choisir le type de test à faire\n"
        reply_keyboard = [['TEST DE POSITIONNEMENT'], ['TEST DE VALIDATION']]
        await update.message.reply_text(
            outgoing_message, 
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True,
        )
        )
        return 4 

    elif received_message == 'COMPREHENSION':
        reply_keyboard = [['LECTURE'], ['COMPREHENSION']]
        await update.message.reply_text(
            "Ce type de matière n'est pas encore disponible"
            "Merci de choisir un test de lecture",  
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True,
        )
        )
        return 3 

async def handle_test(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user 
    received_message = update.message.text
    if received_message == 'TEST DE POSITIONNEMENT':
        await update.message.reply_text(
            f"Le {received_message} va démarrer. ce sera une suite d'éxercices auquel vous devrez répondre. "
            "Vous avez la possibilité d'arrêter le test en envoyant la commande /stop. "
            "Prenez un peu de café, le test va démarrer dans 5s\n\n"
        )
        await asyncio.sleep(5)  # wait 5s to start the quiz 
        
        current_niveau = map_teacher2student[user.first_name]['student']['niveau']
        niveau_elm = quiz[f'niveau{current_niveau}']
        nb_quiz = len(niveau_elm['content'])
        
        map_teacher2student[user.first_name]['nb_quiz'] = nb_quiz 
        map_teacher2student[user.first_name]['cursor'] = 0 
        map_teacher2student[user.first_name]['quiz_values'] = [] 
        map_teacher2student[user.first_name]['quiz_threshold'] = niveau_elm['threshold'] 
        map_teacher2student[user.first_name]['nb_points'] = 0
       
        await update.message.reply_text(
            f"Vous allez passé {nb_quiz} test(s). {niveau_elm['target']}"
        )  

        key = 0 
        val  = niveau_elm['content'][key]
        outgoing_message = f"Exercice {key} | {val['target']}\n{val['content']['consigne']}\n"
        if val['type'] == 'word':
            nb_words = len(val['content']['value'])
            fst = ' '.join(val['content']['value'][:nb_words//2])
            snd = ' '.join(val['content']['value'][nb_words//2:])
            outgoing_message += '\n'.join([fst, snd])
            await update.message.reply_text(outgoing_message)
            map_teacher2student[user.first_name]['quiz_values'].append({
                'type': 'word', 
                'value': val['content']['value']
            })

        elif val['type'] == 'text': 
            await update.message.reply_text(outgoing_message + f'\n{val["content"]["value"]}')
            map_teacher2student[user.first_name]['quiz_values'].append({
                'type': 'text', 
                'value': val['content']['value'], 
                'duration': val['content']['duration']
            })
        
        return 5 

    if received_message == 'TEST DE VALIDATION':
        await update.message.reply_text("On ne supporte pas encore les tests de validation")
        outgoing_message = "Veillez choisir le type de test à faire\n"
        reply_keyboard = [['TEST DE POSITIONNEMENT'], ['TEST DE VALIDATION']]
        await update.message.reply_text(
            outgoing_message, 
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True,
        )
        )
        return 4 
        
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    nb_quiz = map_teacher2student[user.first_name]['nb_quiz']
    map_teacher2student[user.first_name]['cursor'] += 1 

    audio_stream = await update.message.voice.get_file()
    audio_bytearray = await audio_stream.download_as_bytearray()
    audio_iostream = BytesIO(audio_bytearray)
    duration = get_duration(audio_iostream)
    current_quiz = map_teacher2student[user.first_name]['quiz_values'][map_teacher2student[user.first_name]['cursor'] - 1]
    make_transription = 0
    if current_quiz['type'] == 'text':
        if duration > current_quiz['duration']:
            await update.message.reply_text("oups, vous n'avez pas respecté la durée\n votre audio est trop long")
        else:
            make_transription = 1
    else:
        make_transription = 1
    
    if make_transription:
        async with aiohttp.ClientSession() as session:
            audio_iostream = BytesIO(audio_bytearray)
            print(audio_iostream)
            async with session.post('tcp://localhost:8500/transcript', data={'incoming_audio': audio_iostream}) as resp:
                response = await resp.json()  # transform to_dict 
                print(response)
                if response['status'] == 1:
                    transcription = response['content']['text']
                    if current_quiz['type'] == 'word': 
                        target_words = current_quiz['value']
                        source_words = transcription.lower().split(' ')
                        if len(source_words) != len(target_words):
                            await update.message.reply_text("oups, vous n'avez pas respecté le nombre de mots\n votre score n'est pas valide")
                        else:
                            scores = []
                            points_acc = 0
                            for lft, rgt in zip(source_words, target_words):
                                rgt = rgt.lower()
                                nb_chars = len(rgt)
                                nb_errors = edit_distance(lft, rgt)
                                if nb_errors < nb_chars:
                                    nb_points = int(((nb_chars - nb_errors) / nb_chars) > 0.5)    
                                else:
                                    nb_points = 0 
                                scores.append([rgt, lft, nb_errors, nb_points])
                                points_acc += nb_points 
                            
                            tab_str = tabulate(scores, tablefmt='grid', headers=['target', 'source', 'nb_errors', 'nb_points'])
                            print(tab_str)
                            await update.message.reply_text("voici votre score après évaluation\n\n" + tab_str)
                            map_teacher2student[user.first_name]['nb_points'] += points_acc 
                    else: # text => use semantic score and duration 
                        target_text = current_quiz['value']
                        source_text = transcription
                        [source_vec, target_vec] = model.encode([source_text, target_text], device='cpu')
                        print(source_vec)
                        print(target_vec)
                        dot_score = source_vec @ target_vec 
                        weight = np.linalg.norm(source_vec) * np.linalg.norm(target_vec)
                        weighted_dot_score = dot_score / weight 
                        if weighted_dot_score > 0.8:
                            map_teacher2student[user.first_name]['nb_points'] += 1
                        else:
                            await update.message.reply_text(f"votre audio n'est pas consistant avec ce qui est attendu : score de similarité sémantique est de {weighted_dot_score:02.1f}")
                        print(weighted_dot_score)
                    await update.message.reply_text(f"durée : {response['content']['duration']}\ntexte: {response['content']['text']}")
            # end context manager ...! 
        # end context manager ...!

    if map_teacher2student[user.first_name]['cursor'] < nb_quiz:
        current_niveau = map_teacher2student[user.first_name]['student']['niveau']
        niveau_elm = quiz[f'niveau{current_niveau}']
        key = map_teacher2student[user.first_name]['cursor']
        val  = niveau_elm['content'][key]
        outgoing_message = f"Exercice {key} | {val['target']}\n{val['content']['consigne']}\n"
        if val['type'] == 'word':
            nb_words = len(val['content']['value'])
            fst = ' '.join(val['content']['value'][:nb_words//2])
            snd = ' '.join(val['content']['value'][nb_words//2:])
            outgoing_message += '\n'.join([fst, snd])
            await update.message.reply_text(outgoing_message)
            map_teacher2student[user.first_name]['quiz_values'].append({
                'type': 'word', 
                'value': val['content']['value']
            })

        elif val['type'] == 'text': 
            await update.message.reply_text(outgoing_message + f'\n{val["content"]["value"]}')
            map_teacher2student[user.first_name]['quiz_values'].append({
                'type': 'word', 
                'value': val['content']['value'], 
                'duration': val['content']['duration']
            })

        return 5
    else: 
        await update.message.reply_text("fin du test")
        pseudo = map_teacher2student[user.first_name]['pseudo']
        threshold = map_teacher2student[user.first_name]['quiz_threshold']

        nb_points = map_teacher2student[user.first_name]['nb_points']
        result = nb_points >= threshold 
        msg = "bravo, vous passez au niveau supperieur!" if result else "ummm, encore quelques efforts, ça va venir."
        await update.message.reply_text(
            f"{pseudo}, voici les resultats du test. "
            f"pour passer le test, il vous faut au moins {threshold}. "
            f"votre score est de {nb_points}. {msg}" 
        )
        await asyncio.sleep(1)

        selected_student = map_teacher2student[user.first_name]['student']
        student_name = str(selected_student['identité_utilisateur']) + '-' + selected_student['nom']
        io_stream = build_position(map_teacher2student[user.first_name]['student'], result)
        await update.message.reply_photo(io_stream, f"position de l'élève : {student_name}")
        await asyncio.sleep(2)
        
        if result and map_student2level[student_name]['niveau'] < 3:
            map_student2level[student_name]['niveau'] += 1

        reply_keyboard = [['OUI', 'NON']]
        await update.message.reply_text(
            f"{pseudo}, voulez vous obtenir un programme pour faire progresser l'élève {student_name} ?", 
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, 
                one_time_keyboard=True
            )
        )
        return 6 

async def handle_stop_test(update: Update, context:ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    pseudo = map_teacher2student[user.first_name]['pseudo']
    threshold = map_teacher2student[user.first_name]['quiz_threshold']

    nb_points = map_teacher2student[user.first_name]['nb_points']
    result = nb_points >= threshold 
    msg = "bravo, vous passez au niveau supperieur!" if result else "ummm, encore quelques efforts, ça va venir."
    await update.message.reply_text(
        f"{pseudo}, voici les resultats du test. "
        f"pour passer le test, il vous faut au moins {threshold}. "
        f"votre score est de {nb_points}. {msg}" 
    )
    await asyncio.sleep(1)

    selected_student = map_teacher2student[user.first_name]['student']
    student_name = str(selected_student['identité_utilisateur']) + '-' + selected_student['nom']
    io_stream = build_position(map_teacher2student[user.first_name]['student'], result)
    await update.message.reply_photo(io_stream, f"position de l'élève : {student_name}")
    await asyncio.sleep(2)

    if result and map_student2level[student_name]['niveau'] < 3:
        map_student2level[student_name]['niveau'] += 1

    reply_keyboard = [['OUI', 'NON']]
    await update.message.reply_text(
        f"{pseudo}, voulez vous obtenir un programme pour faire progresser l'élève {student_name} ?", 
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True
        )
    )
    return 6  

async def handle_custom_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    pseudo = map_teacher2student[user.first_name]['pseudo']
    selected_student = map_teacher2student[user.first_name]['student']
    student_name = str(selected_student['identité_utilisateur']) + '-' + selected_student['nom']
    received_message = update.message.text 
    
    # save this version ...!
    with open('map_student2level.pkl', 'wb') as  fp:
        pickle.dump(map_student2level, fp)

    if received_message == 'OUI':
        with open(f'niveau{selected_student["niveau"]}.pdf', 'rb') as fp:  # find the relevant pages 
            await update.message.reply_document(fp, caption=f"guide pedagogique niveau {selected_student['niveau']} pour l'élève {student_name}")
    else:
        pass 
    await update.message.reply_text(
        "C'était un plaisir de vous accuellir dans notre plateforme\n"
        "On espère vous retrouver pour une prochaine session\n"
        "D'ici là, prenez bien soin de vous :)"
    )
    return ConversationHandler.END

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.debug(f'First name : {user.first_name} leave the chat')
    await update.message.reply_text(
        "C'était un plaisir de vous accuellir dans notre plateforme\n"
        "On espère vous retrouver pour une prochaine session\n"
        "prenez bien soin de vous :)"
    )
    return ConversationHandler.END

@click.command()
@click.option('--token', help='path to token file', type=click.Path(True), required=True)
def entrypoint(token):
    try:
        app = Application.builder().token(token).build()
        # add start and close handler 
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                0: [MessageHandler(filters.TEXT, handle_authentification)], 
                1: [MessageHandler(filters.TEXT, handle_level)], 
                2: [MessageHandler(filters.TEXT, handle_student)], 
                3: [MessageHandler(filters.TEXT, handle_domain)], 
                4: [MessageHandler(filters.TEXT, handle_test)], 
                5: [MessageHandler(filters.VOICE, handle_voice_message), CommandHandler('stop', handle_stop_test)], 
                6: [MessageHandler(filters.ALL, handle_custom_program)]
            },
            fallbacks=[CommandHandler('close', close)]
        )

        app.add_handler(conv_handler)
        
        app.run_polling()
    except Exception as e:
        logger.error(e)
    

if __name__ == '__main__':
    entrypoint()