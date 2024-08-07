from flask import current_app
from openai import OpenAI
from datetime import datetime, timedelta
from telegram import Bot
from chatting.models import user_table, message_table, chat_table
import openai_api_key
from flask_mail import Message

client = OpenAI(api_key=openai_api_key.OPENAI_API_KEY)

def summarize_conversation(chat_id):
    """주어진 chat_id의 대화 내용을 요약합니다."""
    messages = message_table.query.filter_by(chat_id=chat_id).all()
    conversation_text = ""
    for i in range(0, len(messages), 2):  # 두 개씩 묶어서 처리
        user_message = messages[i].message
        ai_message = messages[i + 1].message if i + 1 < len(messages) else ""  # AI 메시지가 없을 경우 빈 문자열
        conversation_text += f"User: {user_message}\nAI: {ai_message}\n" 

    prompt = f"Summarize the following conversation in Korean for a dementia patient's guardian:\n\n{conversation_text}\n\nSummary:"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,  # 요약 길이 조절 가능
    )
    return response.choices[0].message.content

def send_summary_to_gmail(user_id, chat_id):
    """요약된 대화 내용을 해당 사용자의 Gmail로 전송합니다."""

    with current_app.app_context():
        user = user_table.query.get(user_id)
        guardian_email = user.guardian_email  # 보호자 이메일 주소

        if guardian_email:
            summary = summarize_conversation(chat_id)

            msg = Message(
                "어르신과의 채팅 요약",
                sender=current_app.config['MAIL_USERNAME'],  # 발신자 이메일 주소
                recipients=[guardian_email],
            )
            msg.body = f"채팅 요약:\n\n{summary}"
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send email: {e}")
        else:
            print("Guardian email not found for user_id:", user_id)