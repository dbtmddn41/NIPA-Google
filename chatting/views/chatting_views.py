from flask import Blueprint, render_template, g, request

from chatting.models import chat_table, message_table
from chatting import socketio
from .utils.chatting_utils import *
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
    ################################
    i = 0
    for chat_room in chat_rooms:
        print(chat_room.chat_id, chat_room.created_at)
        chat_room.chat_vector = np.array([i] * 1024) # 임시
        i += 1
    db.session.commit()
    chat_rooms = (
                chat_table.query
                .filter(chat_table.user_id==user_id)
                .order_by(chat_table.created_at.desc())
    )
    for chat_room in chat_rooms:
        print(chat_room.chat_id, chat_room.chat_vector)
    ################################
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
    msgs = (
            message_table.query
            .filter(message_table.user_id==user_id, message_table.chat_id==chat_id)
            .order_by(message_table.created_at)
            .all()
    )
    return render_template('chat/chatting_room.html', messages=msgs, g=g)

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
