from flask import Flask, request, render_template, redirect, url_for, g, session
from flask_socketio import emit
import io, base64
from datetime import datetime, timedelta
# from apscheduler.schedulers.background import BackgroundScheduler
# from flask_mail import Mail, Message
from chatting import socketio
# from chatting.views.utils.vector_search import search_similar_chats, chat_vector_embedding   # 채팅방 종료시 호출 : chat_vector_embedding(chat_id) -> chat_vector, messages
from chatting.summary import send_mail 
import threading
import time

user_responses = {}
no_response = False

@socketio.on('connect', namespace='/notification')
def connected():
    print("hello")
    print('Client connected:', request.sid)
    
@socketio.on('send_notification', namespace='/notification')
def start():
    emit('notification', {'message': '저와 대화할래요?'})
    
            
@socketio.on('send_mail', namespace='/notification')
def _send_mail():
    print("응답이 없습니다!")
    send_mail(session['user_id'], title='사용자의 응답이 없습니다.', contents='사용자의 응답이 없습니다.')


@socketio.on('disconnect', namespace='/notification')
def handle_disconnect():
    sid = request.sid
    print('Client disconnected:', sid)
