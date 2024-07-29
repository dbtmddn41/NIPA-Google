from flask import Flask, request, render_template
from openai import OpenAI
from flask_socketio import SocketIO, emit
import openai_api_key, oracle_configs
import oracledb
import sys


# API 키 설정
client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)

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
    messages = [("system", "You are an assistant for elderly people with dementia. All you have to do is talk to them affectionately, like you would their children. And you must speak in Korean.")]
    
    emit('my_response', {'data': 'Connected'})

@socketio.on('my_event')
def handle_my_custom_event(obj):
    upsert_chat_history('chat_table', 'user', obj['data'])
    
    messages.append(('user', obj['data']))
    response = get_openai_message()
    upsert_chat_history('chat_table', 'assistant', response)
    messages.append(('assistant', response))
    
    d = {}
    d['data'] = response

    emit('my_response', d)

def txt2voice(txt):
    speech_file_path = f"./audio_files/created_.wav"
    response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=txt
    )
    response.stream_to_file(speech_file_path)
    return response

def apply_openai_chat_template():
    # [
    #         {
    #             "role": "system",
    #             "content": "You are an assistant for elderly people with dementia. All you have to do is talk to them affectionately, like you would their children. And you must speak in Korean."
    #         },
    #         {
    #             "role": "user",
    #             "content": msg
    #         }
    #     ]
    chat_template = []
    global messages
    for m in messages:
        chat_template.append({'role': m[0], 'content': m[1]})
    print(chat_template)
    return chat_template

def get_openai_message():
    # Create a chat completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=apply_openai_chat_template(),
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