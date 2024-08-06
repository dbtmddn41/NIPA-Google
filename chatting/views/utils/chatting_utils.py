from flask import Flask, request, render_template, redirect, url_for, g
from openai import OpenAI
import google.generativeai as genai
import openai_api_key, gemini_api_key
from flask_socketio import emit
from flask import session
import io, base64
from pydub import AudioSegment
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from chatting import socketio, db
from chatting.models import message_table, chat_table, user_table
from chatting.views.utils.vector_search import search_similar_chats

client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)
genai.configure(api_key=gemini_api_key.GEMINI_API_KEY)
messages = []

def upsert_chat_history(table, **datas):
    # chat = chat_table.query.get_or_404(datas['chat_id'])
    # user = user_table.query.get_or_404(datas['user_id'])
    msg = message_table(user_id=datas['user_id'], chat_id=datas['chat_id'],
                        message=datas['message'], is_bot_message=datas['is_bot_message'], 
    )
                        # chat=chat, user=user)
    db.session.add(msg)
    db.session.commit()
    
    
@socketio.on('connect')
def connected():
    global messages
    messages = []
    
    emit('alert', {'data': 'Connected'})

@socketio.on('user_send')
def handle_user_msg(obj):

    print(g, session)
    user_id = session['user_id']
    chat_id = session['chat_id']
    similar_chats = search_similar_chats(user_id, obj['data'])
    print(similar_chats)
    if obj['ai_option'] == 'openai':
        response = get_openai_message(obj['data'])
        ai_id = 1
    elif obj['ai_option'] == 'gemini':
        response = get_gemini_message(obj['data'])
        ai_id = 2
    else:
        response = "어쩔티비 안물안궁"
        ai_id = 3
    messages.append(('assistant', response))
    txt2voice(response, './tmp/tmp.wav')
    with open('./tmp/tmp.wav', 'rb') as audio_file:
        audio_data = audio_file.read()
        # 음성 데이터를 base64로 인코딩
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    emit('ai_response', {'data': response, 'audio': audio_base64})



    upsert_chat_history('message_table', user_id=user_id, chat_id=chat_id,
                        message=obj['data'], is_bot_message=0)
    upsert_chat_history('message_table', user_id=user_id, chat_id=chat_id,
                        message=response, is_bot_message=ai_id)

@socketio.on('audio_data')
def handle_user_audio(obj):
    audio_obj = base64.b64decode(obj.split(',')[-1])
    audio_io = io.BytesIO(audio_obj)

    # sys.path.append('/path/to/ffmpeg')
    audio = AudioSegment.from_file(audio_io, format="webm")

    # Export as WAV
    audio.export('./tmp/tmp.wav', format="wav")
    txt = voice2txt('./tmp/tmp.wav')
    print(txt)
    
    emit('user_input', {'data': txt})
    
def voice2txt(audio_file):
    with open(audio_file, 'rb') as f:
        transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=f
        )
    return transcript.text

def txt2voice(txt, file_path):
    response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=txt
    )
    response.stream_to_file(file_path)
    return response

def apply_chat_template(ai_option='openai'):
#    history=[{'parts':
#         {
#             "text": "You are an assistant for elderly people with dementia. All you have to do is talk to them affectionately, like you would their children. And you must speak in Korean."
#         },
#         "role": "user",},
#     ]
    chat_template = []
    global messages
    for m in messages:
        if ai_option == 'openai':
            chat_template.append({'role': m[0], 'content': m[1]})
        elif ai_option == 'gemini':
            chat_template.append({'role': m[0] if m[0] == 'user' else 'model', 'parts': m[1]})
    return chat_template

def get_gemini_message(msg):
    # Create a chat completion
    model = genai.GenerativeModel('gemini-1.5-flash',
                    system_instruction="You are an assistant for elderly people with dementia. All you have to do is talk to them affectionately, like you would their children. And you must speak in Korean.",
                    generation_config=genai.GenerationConfig(
                                max_output_tokens=128,
                                temperature=0.5,
                    ))
    chat = model.start_chat(history=apply_chat_template('gemini'))
    print(chat.history)
    global messages
    response = chat.send_message(msg)
    messages.append(('user', msg))
    return response.text


def get_openai_message(msg):
    # Create a chat completion
    global messages
    messages.insert(0, ("system", "You are an assistant for elderly people with dementia. All you have to do is talk to them affectionately, like you would their children. And you must speak in Korean."))
    messages.append(('user', msg))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=apply_chat_template('openai'),
        temperature=0.7,
        max_tokens=128,
        top_p=0.8
    )
    messages.pop(0)
    print(apply_chat_template('openai'))
    print('>>>>', response.choices[0].message.content)
    return response.choices[0].message.content
