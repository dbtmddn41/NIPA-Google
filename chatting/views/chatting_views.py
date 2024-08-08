from flask import Blueprint, render_template, g, request

from chatting.models import chat_table, message_table
from chatting import socketio
from .utils.chatting_utils import *
from .utils.notification_utils import *
from chatting.views.auth_views import login_required
import numpy as np

bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/chat_list/<int:user_id>/')
@login_required
def chat_list(user_id):
    if g.user.user_id != user_id:
        return "세션 오류"
    chat_rooms = (
                chat_table.query
                .filter(chat_table.user_id==user_id)
                .order_by(chat_table.created_at.desc())
    )
    socketio.emit('notification', {'message': '새로운 알림이 있습니다!'})
    return render_template('chat/chat_list.html', chatting_rooms=chat_rooms, g=g)

@bp.route('/chatting_room/<int:user_id>/<int:chat_id>')
@login_required
def chatting_room(user_id, chat_id):
    if g.user.user_id != user_id:
        return "세션 오류"
    else:
        chat = chat_table.query.get_or_404(chat_id)
        session['chat_id'] = chat.chat_id
        g.chat = chat
        if chat.is_end:
            messages = (
                    message_table.query
                    .filter(message_table.user_id==user_id, message_table.chat_id==chat_id)
                    .order_by(message_table.created_at.desc())
                    .all()
            )
        else:
            messages=[]
    return render_template('chat/chatting_room.html', messages=messages, g=g)

@bp.route('/create_room/')
@login_required
def create_room():
    print(request.args)
    user_id = int(request.args.get('user_id', -1))
    if g.user.user_id != user_id:
        return "세션 오류"
    chat = chat_table(user_id=user_id)
    db.session.add(chat)
    db.session.commit()
    return redirect(url_for('chat.chat_list', user_id=user_id))
