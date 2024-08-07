from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, EmailField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, Email, NumberRange

class UserCreateForm(FlaskForm):
    user_name = StringField('사용자 이름', validators=[DataRequired(), Length(min=3, max=25)])
    password1 = PasswordField('비밀번호', validators=[DataRequired(), EqualTo('password2', '비밀번호가 일치하지 않습니다.')])
    password2 = PasswordField('비밀번호', validators=[DataRequired()])
    gender = StringField('성별', validators=[DataRequired()])
    age = IntegerField('나이', validators=[DataRequired(), NumberRange(min=0, max=200, message='나이가 그럴 수가 있다고?')])
    email = EmailField('이메일', validators=[DataRequired(), Email()])
    

class UserLoginForm(FlaskForm):
    user_name = StringField('사용자이름', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('비밀번호', validators=[DataRequired()])
