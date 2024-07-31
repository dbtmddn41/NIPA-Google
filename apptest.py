from flask import Flask, request, render_template, redirect, url_for, session
from openai import OpenAI
import google.generativeai as genai
from flask_socketio import SocketIO, emit
import openai_api_key, gemini_api_key, oracle_configs
import oracledb
import sys, base64
import io, wave
from pydub import AudioSegment

# API 키 설정
client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)
genai.configure(api_key=gemini_api_key.GEMINI_API_KEY)

# app
app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your-secret-key-123'
app.secret_key = 'nipa-google'
# websocket connection
socketio = SocketIO(app)

messages = {}
chat_ids = {} 

def upsert_chat_history(table_name, **datas):
    connection = None
    cursor = None
    try:
        # Establish connection
        connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)
        # Create a cursor
        cursor = connection.cursor()
        # Execute SQL command
        cursor.execute(f"""
            INSERT INTO {table_name} (chat_id, message, is_bot_message)
            VALUES (:chat_id, :message, :is_bot_message)
        """, {"chat_id": datas['chat_id'], 'message': datas['message'], 
              "is_bot_message": datas['is_bot_message']})
        
        # Commit the transaction
        connection.commit()
        
    except oracledb.DatabaseError as e:
        print(f"Database error occurred: {e}", file=sys.stderr)
        if connection:
            connection.rollback()
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@socketio.on('connect')
def connected():
    global messages, chat_ids
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id not in chat_ids:
            messages= []
            # 챗 테이블에 새로운 행 추가 및 chat_id 저장
            with oracledb.connect(**oracle_configs.ORACLE_CONFIG) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO CHAT_TABLE (USER_ID) VALUES (:1)", (user_id,))
                    chat_ids[user_id] = cursor.lastrowid
                    connection.commit()  # 변경 사항 커밋
                    cursor.execute("SELECT CHAT_ID FROM CHAT_TABLE WHERE USER_ID = :1", (user_id,))
                    chat_id = cursor.fetchone()[0]
                    session['chat_id'] = chat_id  
                    print('chat_id: ', chat_id)
        else:
            session['chat_id'] = chat_ids[user_id]  # 기존 chat_id 가져오기
            print('chat_id: ', session['chat_id'])
        emit('alert', {'data': '로그인 성공!'})

@socketio.on('user_send')
def handle_user_msg(obj):
    print(obj)
    user_id = session['user_id']
    chat_id = session['chat_id']
    print('chat2: ',chat_id)
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
    upsert_chat_history('message_table', chat_id=chat_id,
                        message=obj['data'], is_bot_message=0)
    upsert_chat_history('message_table', chat_id=chat_id,
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

@app.route('/')
def index():
    return render_template('login.html')

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
            connection.commit()
            cursor.execute("SELECT USER_ID FROM USER_TABLE WHERE USER_NAME = :1", (username,))
            user_id = cursor.fetchone()[0]
            print('user_id',user_id)
            session['user_id'] = user_id  
            return redirect(url_for('chat'))
        except oracledb.DatabaseError as e:
            print(f"Database error occurred: {e}", file=sys.stderr)
            if connection:
                connection.rollback()
            return "Failed to insert user information. Please try again later."
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


@app.route('/chat')
def chat():
    return render_template('index.html') 

if __name__ == '__main__':
    app.run(debug=True)