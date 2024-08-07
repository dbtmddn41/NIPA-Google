import os
from oracle_configs import ORACLE_CONFIG
from gmail_configs import GMAIL_CONFIG

BASE_DIR = os.path.dirname(__file__)

SQLALCHEMY_DATABASE_URI = f"oracle+oracledb://{ORACLE_CONFIG['user']}:{ORACLE_CONFIG['password']}@{ORACLE_CONFIG['dsn']}?wallet_location={ORACLE_CONFIG['wallet_location']}&wallet_password={ORACLE_CONFIG['wallet_password']}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "dnflxlaghkdlxld!"

MAIL_SERVER = GMAIL_CONFIG['MAIL_SERVER']
MAIL_PORT = GMAIL_CONFIG['MAIL_PORT']
MAIL_USE_TLS = GMAIL_CONFIG['MAIL_USE_TLS']
MAIL_USE_SSL = GMAIL_CONFIG['MAIL_USE_SSL']
MAIL_USERNAME = GMAIL_CONFIG['MAIL_USERNAME']
MAIL_PASSWORD = GMAIL_CONFIG['MAIL_PASSWORD']