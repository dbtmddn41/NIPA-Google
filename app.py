from flask import Flask, request, render_template
from openai import OpenAI
from flask_socketio import SocketIO, emit
import openai_api_key
import oracle_configs
import oracledb
import atexit


connection = oracledb.connect(**oracle_configs.ORACLE_CONFIG)

cursor = connection.cursor()

def cleanup_function():
    cursor.close()
    connection.close()

atexit.register(cleanup_function)
# API 키 설정
client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)

# app
app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your-secret-key-123'

# websocket connection
socketio = SocketIO(app)

@socketio.on('connect')
def test_connect():
    emit('my_response', {'data': 'Connected'})

@socketio.on('my_event')
def handle_my_custom_event(obj):
    print('received json: ' + str(obj))
    cursor.execute(f"""
    insert into chat_table (chat,  user_id)
    values (:sent_msg, 1)
    """, sent_msg=obj['data'])
    
    response = get_openai(obj['data'])
    print(response)
    cursor.execute(f"""
    insert into chat_table (chat,  user_id)
    values (:response, 0)
    """, response=response)
    d = {}
    d['data'] = response
    connection.commit()
    


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

def get_openai(msg):
    # Create a chat completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant for elderly people with dementia. All you have to do is talk to them affectionately, like you would their children."
            },
            {
                "role": "user",
                "content": msg
            }
        ],
        temperature=0.7,
        max_tokens=64,
        top_p=1
    )
    print('>>>>', response.choices[0].message.content)
    return response.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)