#! venv/bin/python

# cancel setup install if existing install found
from config import SECRET_KEY
if SECRET_KEY:
    print('Installation seems already exists.')
    print('Running twice will damage the previous configuration.')
    print('Exiting...')
    exit()

from setuptools import setup, find_packages
from shutil import rmtree
import secrets
import hashlib
from os import makedirs, path

setup(
    name='dynalist_companion',
    version='1.0.0',
    url='https://github.com/edgeryders/dynalist_companion.git',
    author='Edgeryders Team',
    author_email='anupokharelforedgeryders@gmail.com',
    description='Unofficial utilities for the dynalist.io list management application.',
    license='AGPL-3.0',
    keywords='dynalist notification, auto backup, dynalist advance',
    download_url='',
    project_urls={
        'Documentation': 'https://edgeryders.eu/t/dynalist-manual/7618',
        'Source': 'https://github.com/edgeryders/dynalist_companion',
        'Tracker': 'https://github.com/edgeryders/dynalist_companion/issues',
    },
    packages=find_packages(),
    package_data={
        'app': ['templates/*.html'],
    },
    data_files=[
        ('configuration', ['config.py']),
        ('css', ['app/static/floating-label.css', 'app/static/main.css']),
         ],
    py_modules=['admin'],
    install_requires=['Flask', 'Flask-Login', 'Flask-SQLAlchemy', 'Flask-WTF',
                      'Flask-Login', 'google-api-python-client', 'oauth2client'],
    python_requires='~=3.6'
)


from config import RESOURCES_PATH
makedirs(path.join(RESOURCES_PATH, 'dynalist_backup'), exist_ok=True)

# Configure secret key and secret code
with open('config.py', 'a') as f:
    f.write(f"SECRET_KEY = '{secrets.token_hex(16)}'\n")

from app import db
db.create_all()

# Setup default admin account
from app.models import Users
admin_password = secrets.token_hex(8)
hashed_pw = hashlib.sha256(admin_password.encode()).hexdigest()
default_user = Users(username='admin', email='example@example.com', password=hashed_pw, is_admin=1)
db.session.add(default_user)

# Setup default settings
from app.models import AppSettings
from config import RESOURCES_PATH
secret_code = secrets.token_hex(8)
default_sett = AppSettings(
    sett='core',
    backup_enabled=0,
    backup_type=1,
    backup_file_prefix='Dynalist.EdgerydersTasks',
    email_push_enabled=1,
    web_push_enabled=0,
    dynalist_api_url='https://dynalist.io/api/v1/doc/read',
    smtp_host='smtp.google.com',
    smtp_port=587,
    secret_code=secret_code,
    app_name='Dynalist Companion',
    old_file=RESOURCES_PATH + 'old.txt',
    new_file=RESOURCES_PATH + 'new.txt',
    backup_dir=RESOURCES_PATH + 'dynalist_backup'
)

db.session.add(default_sett)
db.session.commit()

with open('for_admin.txt', 'w') as f:
    f.write(f'\n\nSecret code for registration is {secret_code}\n\n')
    f.write(f'Admin username is "admin" and password is {admin_password}')
for_admin = open('for_admin.txt', 'r').read()
print(for_admin)


# clean un necessary files created 'setup.py install'
rmtree('build')
rmtree('dist')
rmtree('dynalist_companion.egg-info')
