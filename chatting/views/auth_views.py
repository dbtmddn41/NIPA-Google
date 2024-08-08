from flask import Blueprint, url_for, render_template, flash, request, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
from chatting import db
from chatting.forms import UserCreateForm, UserLoginForm
from chatting.models import user_table, chat_table, message_table
import functools
#from FlagEmbedding import BGEM3FlagModel

def upsert_chat_history(table, **datas):
    # chat = chat_table.query.get_or_404(datas['chat_id'])
    # user = user_table.query.get_or_404(datas['user_id'])
    msg = message_table(user_id=datas['user_id'], chat_id=datas['chat_id'],
                        message=datas['message'], is_bot_message=datas['is_bot_message'], 
    )
    db.session.add(msg)
    db.session.commit()

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/signup/', methods=('GET', 'POST'))
def signup():
    form = UserCreateForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = user_table.query.filter_by(user_name=form.user_name.data).first()
            if not user:
                user = user_table(user_name=form.user_name.data,
                                password=generate_password_hash(form.password1.data),
                                gender=form.gender.data,
                                age=form.age.data,
                                email=form.email.data,
                                )
                db.session.add(user)
                db.session.commit()
                                                        # 로그인 성공 시 사용자 정보 메시지 생성 및 저장
               # chat = chat_table(user_id=user.user_id)
               # db.session.add(chat)
               # db.session.commit()
               # session['chat_id'] = chat.chat_id
               # user_info_message = f"사용자 이름: {user.user_name}, 성별: {user.gender}, 나이: {user.age}"
               # upsert_chat_history('message_table', user_id=user.user_id, chat_id=session['chat_id'],
               #                     message=user_info_message, is_bot_message=0)
                return redirect(url_for('main.main'))
        else:
            flash('이미 존재하는 사용자입니다.')
    return render_template('auth/signup.html', form=form)

@bp.route('/login/', methods=('GET', 'POST'))
def login():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        user = user_table.query.filter_by(user_name=form.user_name.data).first()
        if not user:
            error = "존재하지 않는 사용자입니다."
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 올바르지 않습니다."
        if error is None:
            session.clear()
            session['user_id'] = user.user_id
            _next = request.args.get('next', '')
            if _next:
                return redirect(_next)
            else:
                return redirect(url_for('main.main'))
        flash(error)
    return render_template('auth/login.html', form=form)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = user_table.query.get(user_id)

# model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

# def text_embedding_bge(text):
#     embedding = model.encode(text, batch_size=12, max_length=8192)['dense_vecs']
#     return embedding

@bp.route('/logout/')
def logout():
    session.clear()  
    return redirect(url_for('main.main'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            _next = request.url if request.method == 'GET' else ''
            return redirect(url_for('auth.login', next=_next))
        return view(*args, **kwargs)
    return wrapped_view
