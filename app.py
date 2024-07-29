from flask import Flask, request, render_template
from openai import OpenAI
import google.generativeai as genai
from flask_socketio import SocketIO, emit
import openai_api_key, gemini_api_key, oracle_configs
import oracledb
import sys

# API 키 설정
client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)
genai.configure(api_key=gemini_api_key.GEMINI_API_KEY)

# app
app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your-secret-key-123'

# websocket connection
socketio = SocketIO(app)

messages = None

def upsert_chat_history(table_name, role, message):
    connection = None
    cursor = None
    try:
        # Establish connection
        connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)
        
        # Create a cursor
        cursor = connection.cursor()
        
        # Execute SQL command
        cursor.execute(f"""
            INSERT INTO {table_name} (user_id, chat)
            VALUES (:user_id, :chat)
        """, {"user_id": 1, "chat": message})
        
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
    global messages
    messages = []
    
    emit('alert', {'data': 'Connected'})

@socketio.on('user_send')
def handle_user_msg(obj):
    print(obj)
    upsert_chat_history('chat_table', 'user', obj['data'])
    
    if obj['ai_option'] == 'openai':
        response = get_openai_message(obj['data'])
    elif obj['ai_option'] == 'gemini':
        response = get_gemini_message(obj['data'])
    else:
        response = "어쩔티비 안물안궁"
    upsert_chat_history('chat_table', 'assistant', response)
    messages.append(('assistant', response))
    
    d = {}
    d['data'] = response

    emit('ai_response', d)

@socketio.on('audio_data')
def handle_user_audio(obj):
    pass

def txt2voice(txt):
    speech_file_path = f"./audio_files/created_.wav"
    response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=txt
    )
    response.stream_to_file(speech_file_path)
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
            chat_template.append({'role': m[0], 'parts': {'text': m[1]}})
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
    response = chat.send_message(msg)
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
    print('>>>>', response.choices[0].message.content)
    return response.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)