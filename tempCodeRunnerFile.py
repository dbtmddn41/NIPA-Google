def handle_user_msg(obj):
    print(obj)
    user_id = session['user_id']
    chat_id = chat_ids.get(user_id)
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