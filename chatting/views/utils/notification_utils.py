from flask import Flask, request, render_template, redirect, url_for, g, session
from flask_socketio import emit
import io, base64
from datetime import datetime, timedelta
# from apscheduler.schedulers.background import BackgroundScheduler
# from flask_mail import Mail, Message
from chatting import socketio, db, scheduler
from chatting.models import message_table, chat_table, user_table
# from chatting.views.utils.vector_search import search_similar_chats, chat_vector_embedding   # 채팅방 종료시 호출 : chat_vector_embedding(chat_id) -> chat_vector, messages
from chatting.summary import send_summary_to_gmail 
import threading

user_responses = {}

@socketio.on('connect', namespace='/notification')
def connected():
    print("hello")
    print('Client connected:', request.sid)
    # emit('notification', {'message': '저와 대화할래요?'})
    # timer = threading.Timer(5, check_notification_response, [request.sid])
    # timer.start()
    # user_responses[request.sid] = timer
    
@socketio.on('notification_clicked', namespace='/chat_list')
def handle_notification_click(data):
    sid = request.sid
    if sid in user_responses:
        # 응답이 도착하면 타이머를 취소합니다.
        user_responses[sid].cancel()
        del user_responses[sid]
    print('Notification clicked:', data)


@socketio.on('disconnect', namespace='/chat_list')
def handle_disconnect():
    sid = request.sid
    if sid in user_responses:
        user_responses[sid].cancel()
        del user_responses[sid]
    print('Client disconnected:', sid)
    
def check_notification_response(notification_id):
    if notification_id in user_responses:
        if len(user_responses) > 3:
            print("Hello world")
            user_responses = {}


@scheduler.task('cron', id='hourly_notification', minute='0')  # 매 시간 0분에 실행
def scheduled_task():
    emit('notification', {'data': '저와 대화해볼까요?'})#, broadcast=True)
    timer = threading.Timer(300, check_notification_response, [request.sid])
    timer.start()
    user_responses[request.sid] = timer

