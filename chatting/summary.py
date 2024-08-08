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

    for m in messages:
        message = m.message
        role = "Assistant" if m.is_bot_message else "User"
        conversation_text += f"{role}: {message}\n" 

    system_prompt = f"Diagnose the user's health based on the conversations you've had with them and summarize what you've talked about today. You must write in Korean. Please summarize shorter than 100 words."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"{conversation_text}\n\nSummary:"}],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content

def send_summary_to_gmail(user_id, chat_id, **kargs):
    """요약된 대화 내용을 해당 사용자의 Gmail로 전송합니다."""

    with current_app.app_context():
        user = user_table.query.get(user_id)
        guardian_email = user.email

        if guardian_email:
            if 'contents' in kargs:

                msg = Message(
                    kargs["title"],
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[guardian_email],
                )
                msg.body = f"\n{kargs['contents']}"

                try:
                    mail.send(msg)
                except Exception as e:
                    print(f"Failed to send email: {e}")
        else:
            print("Guardian email not found for user_id:", user_id)