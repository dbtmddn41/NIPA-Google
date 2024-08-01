<<<<<<< HEAD:chatting/views/utils/chatting_utils.py
=======
from flask import Flask, request, render_template, redirect, url_for
>>>>>>> ce8f108615e74ee42166e3637e0a4a0349b948f1:app.py
from openai import OpenAI
import google.generativeai as genai
import openai_api_key, gemini_api_key
from flask_socketio import emit
from flask import session
import io, base64
from pydub import AudioSegment

<<<<<<< HEAD:chatting/views/utils/chatting_utils.py
from chating import socketio, db
from chating.models import message_table, chat_table, user_table

=======
# API 키 설정
>>>>>>> ce8f108615e74ee42166e3637e0a4a0349b948f1:app.py
client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)
genai.configure(api_key=gemini_api_key.GEMINI_API_KEY)
messages = []

def upsert_chat_history(table, **datas):
    chat = chat_table.query.get_or_404(datas['chat_id'])
    user = user_table.query.get_or_404(datas['user_id'])
    msg = message_table(user_id=datas['user_id'], chat_id=datas['chat_id'],
                        message=datas['message'], is_bot_message=datas['is_bot_message'], 
                        chat=chat, user=user)
    db.session.add(msg)
    db.session.commit()
    
    
@socketio.on('connect')
def connected():
    global messages
    messages = []
    
    emit('alert', {'data': 'Connected'})

@socketio.on('user_send')
def handle_user_msg(obj):
    print(socketio.__dir__)
    user_id = 5#session['user_id']
    chat_id = 1#session['chat_id']
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
<<<<<<< HEAD:chatting/views/utils/chatting_utils.py
=======

@app.route('/')
def index():
    return render_template('login.html')  # 초기 페이지는 login.html

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    sex = request.form['sex']
    age = int(request.form['age'])

    # 사용자 정보 유효성 검증 (실제 환경에서는 데이터베이스 조회 등 추가 로직 필요)
    if username and sex and age:
        try:
            connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)
            cursor = connection.cursor()
            cursor.execute(
                    "INSERT INTO USER_TABLE (USER_NAME, SEX, AGE) VALUES (:1, :2, :3)",
                    (username, sex, age)
                    )
            connection.commit()  # 변경 사항 커밋
            return redirect(url_for('chat'))
        except oracledb.DatabaseError as e:
            print(f"Database error occurred: {e}", file=sys.stderr)
            if connection:
                connection.rollback()
            return "Failed to insert user information. Please try again later."
        finally:
        # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()


@app.route('/chat')
def chat():
    return render_template('index.html') 

if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> ce8f108615e74ee42166e3637e0a4a0349b948f1:app.py
