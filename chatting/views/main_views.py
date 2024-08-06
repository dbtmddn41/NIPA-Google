from flask import Blueprint, render_template, session, g, redirect, url_for

from chatting.models import user_table, chat_table, message_table

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def main():
    if g.user is None:
        return render_template('main.html')
    else:
        return redirect(url_for('chat.chat_list', user_id=g.user.user_id))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = user_table.query.get(user_id)