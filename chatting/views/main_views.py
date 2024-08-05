from flask import Blueprint, render_template

from chatting.models import user_table, chat_table, message_table

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def hello_pybo():
    return "hello"
