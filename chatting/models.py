from chatting import db
from datetime import datetime
from sqlalchemy.schema import Sequence

class user_table(db.Model):
    user_id_seq = Sequence('user_id_seq', start=5)
    user_id = db.Column(db.Integer, user_id_seq,
                        server_default=user_id_seq.next_value(), primary_key=True)
    user_name = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.now(), onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime(), nullable=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    
class chat_table(db.Model):
    chat_id_seq = Sequence('chat_id_seq')
    chat_id = db.Column(db.Integer, chat_id_seq,
                        server_default=chat_id_seq.next_value(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_table.user_id', ondelete='CASCADE'))
    user = db.relationship('user_table', backref=db.backref('chat_set'))
    chat_vector = db.Column(db.PickleType, nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.now(), onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime(), nullable=True)
    is_end = db.Column(db.Integer, nullable=False, default=0)
    summary = db.Column(db.String(3000), nullable=True)
    
    
class message_table(db.Model):
    message_id_seq = Sequence('message_id_seq')
    message_id = db.Column(db.Integer, message_id_seq,
                        server_default=message_id_seq.next_value(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_table.user_id', ondelete='CASCADE'))
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_table.chat_id', ondelete='CASCADE'))
    user = db.relationship('user_table', backref=db.backref('message_set'))
    chat = db.relationship('chat_table', backref=db.backref('message_set'))
    message = db.Column(db.String(4000), nullable=True)
    is_bot_message = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.now(), onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime(), nullable=True)