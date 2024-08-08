from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import config
import os
from oracle_configs import ORACLE_CONFIG
from flask_mail import Mail
from flask_apscheduler import APScheduler

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
mail = Mail() ### 메일
scheduler = APScheduler()

os.environ['TNS_ADMIN'] = ORACLE_CONFIG['config_dir']
def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models
    
    from .views import main_views, chatting_views, auth_views
    app.register_blueprint(main_views.bp)
    app.register_blueprint(chatting_views.bp)
    app.register_blueprint(auth_views.bp)
    mail.init_app(app)  ### Flask-Mail 초기화
    socketio.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    
    return app