import os
from oracle_configs import ORACLE_CONFIG

BASE_DIR = os.path.dirname(__file__)

SQLALCHEMY_DATABASE_URI = f"oracle+oracledb://{ORACLE_CONFIG['user']}:{ORACLE_CONFIG['password']}@{ORACLE_CONFIG['dsn']}?wallet_location={ORACLE_CONFIG['wallet_location']}&wallet_password={ORACLE_CONFIG['wallet_password']}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "dnflxlaghkdlxld!"