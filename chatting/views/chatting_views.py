from flask import Blueprint, render_template

from chatting.models import chat_table, message_table
from chating import socketio
from .utils.chatting_utils import *

bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/chat_list/<int:user_id>/')
def chat_list(user_id):
    chat_rooms = (
                chat_table.query
                .filter(chat_table.user_id==user_id)
                .order_by(chat_table.created_at.desc())
    )
    for chat_room in chat_rooms:
        print(chat_room.chat_id, chat_room.created_at)
    return render_template('chat/chat_list.html', chatting_rooms=chat_rooms)

@bp.route('/chatting_room/<int:user_id>/<int:chat_id>')
def chatting_room(user_id, chat_id):
    msgs = (
            message_table.query
            .filter(message_table.user_id==user_id, message_table.chat_id==chat_id)
            .order_by(message_table.created_at)
            .all()
    )
    return render_template('chat/chatting_room.html', messages=msgs)

