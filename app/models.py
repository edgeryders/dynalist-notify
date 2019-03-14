from . import db, login_manager
from re import findall
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.inspection import inspect


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


def serialize(object_):
    # @ returns dictionary object with model field name as key
    return {c: getattr(object_, c) for c in inspect(object_).attrs.keys()}


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    browser_pushid = db.Column(db.Text)
    push_email = db.Column(db.SmallInteger, default='1')
    push_web = db.Column(db.SmallInteger, default='1')
    alert_deadline = db.Column(db.Integer, default='1')
    is_admin = db.Column(db.SmallInteger, default='0')


def deadlines(username):
    try:
        app_sett = AppSettings.query.get('core')
        read_file = open(app_sett.old_file, 'r', encoding='utf-8').read()
        dates = findall('.*(20[0-9]{2}-\d{2}-\d{2}).*\.\s.*#%s' % username, read_file)
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
        now = datetime.now()

        past_dates = [date for date in dates if date < now]
        last_deadline = max(date for date in dates if date < now) if past_dates else 'None'

        future_dates = [date for date in dates if date > now]
        next_deadline = min(date for date in dates if date > now) if future_dates else 'None'

        return {'last': str(last_deadline)[:10], 'next': str(next_deadline)[:10]}

    except FileNotFoundError:

        return {'last': 'None', 'next': 'None'}


class AppSettings(db.Model):
    sett = db.Column(db.String(), primary_key=True)
    backup_enabled = db.Column(db.Boolean)
    backup_type = db.Column(db.SmallInteger)  # 1 = drive, 2 = google drive
    google_drive_id = db.Column(db.String(100))
    backup_file_prefix = db.Column(db.String(32))
    email_push_enabled = db.Column(db.Boolean)
    web_push_enabled = db.Column(db.Boolean)
    dynalist_api_token = db.Column(db.String(255))
    dynalist_api_url = db.Column(db.String(255))
    dynalist_api_file_id = db.Column(db.String(255))
    smtp_host = db.Column(db.String(50))
    smtp_port = db.Column(db.Integer)
    smtp_email = db.Column(db.String(50))
    smtp_password = db.Column(db.String(32))
    secret_code = db.Column(db.String(32))
    app_name = db.Column(db.String(32))
    old_file = db.Column(db.String(100))
    new_file = db.Column(db.String(100))
    backup_dir = db.Column(db.String(100))


def get_dynalist_data():
    app_sett = AppSettings.query.get('core')
    from urllib import request
    from json import dumps, loads

    body = {
        'token': app_sett.dynalist_api_token,
        'file_id': app_sett.dynalist_api_file_id
    }
    params = dumps(body).encode('utf-8')
    headers = {'Content-Type': 'application/json', 'User-Agent': 'Debendra Bot'}
    try:
        req = request.Request(app_sett.dynalist_api_url, data=params, headers=headers)
        resp = request.urlopen(req)
        raw_data = resp.read().decode('utf-8')
    except Exception as e:
        return e
    finally:
        load_data = loads(raw_data)
        if load_data['_code'] == 'Ok':
            return load_data
        return load_data['_msg']
