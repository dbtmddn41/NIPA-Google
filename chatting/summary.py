from flask import current_app
from openai import OpenAI
from datetime import datetime, timedelta
from telegram import Bot
from chatting.models import user_table, message_table, chat_table
import openai_api_key
from flask_mail import Message
from chatting import mail

client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)

def summarize_conversation(chat_id):
    """주어진 chat_id의 대화 내용을 요약합니다."""
    messages = message_table.query.filter_by(chat_id=chat_id).all()
    conversation_text = ""
    # for i in range(0, len(messages), 2):  # 두 개씩 묶어서 처리
    #     user_message = messages[i].message
    #     ai_message = messages[i + 1].message if i + 1 < len(messages) else ""  # AI 메시지가 없을 경우 빈 문자열
    #     conversation_text += f"User: {user_message}\nAI: {ai_message}\n" 
        
    for m in messages:  # 두 개씩 묶어서 처리
        message = m.message
        role = "Assistant" if m.is_bot_message else "User"  # AI 메시지가 없을 경우 빈 문자열
        conversation_text += f"{role}: {message}\n" 

    system_prompt = f"Diagnose the user's health based on the conversations you've had with them and summarize what you've talked about today. You must write in Korean."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"{conversation_text}\n\nSummary:"}],
        temperature=0.7,
        max_tokens=200,  # 요약 길이 조절 가능
    )
    return response.choices[0].message.content

def send_summary_to_gmail(user_id, chat_id):
    """요약된 대화 내용을 해당 사용자의 Gmail로 전송합니다."""

    with current_app.app_context():
        user = user_table.query.get(user_id)
        guardian_email = user.email  # 보호자 이메일 주소

        if guardian_email:
            summary = summarize_conversation(chat_id)

            msg = Message(
                "어르신과의 채팅 요약",
                sender=current_app.config['MAIL_USERNAME'],  # 발신자 이메일 주소
                recipients=[guardian_email],
            )
            msg.body = f"채팅 요약:\n\n{summary}"
            # print(user)
            # print(guardian_email)
            # print(chat_id)
            # print(summary)
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send email: {e}")
        else:
            print("Guardian email not found for user_id:", user_id)