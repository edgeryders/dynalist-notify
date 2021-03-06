from os import path
import re
import logging
from app.models import Users
from app import config
from app.models import AppSettings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s - %(asctime)s')

file_handler = logging.FileHandler(path.join(config['RESOURCES_PATH'], 'notify.log'))
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

app_sett = AppSettings.query.get('core')


def save(data):  # Content fetched from dynalist api will be saved in server
    if not path.isfile(app_sett.old_file):
        logger.info('Writing old.txt')
        with open(app_sett.old_file, 'w', encoding='utf-8') as f:
            for lines in data['nodes']:
                if not lines['checked']:
                    f.write('{} || {}\n'.format(lines['id'], lines['content'].replace('\n', ' ').strip()))
                    if lines['note']:
                        f.write('{} || {}\n'.format(lines['id'], lines['note'].replace('\n', ' ').strip()))
        logger.info('"old.txt" written.')
        logger.info('Exiting...')
        exit()
    else:
        logger.info('Old file exists.')
        logger.info('Writing new.txt')
        with open(app_sett.new_file, 'w', encoding='utf-8') as f:
            for lines in data['nodes']:
                if not lines['checked']:
                    f.write('{} || {}\n'.format(lines['id'], lines['content'].replace('\n', ' ').strip()))
                    if lines['note']:
                        f.write('{} || {}\n'.format(lines['id'], lines['note'].replace('\n', ' ').strip()))
        logger.info('new.txt written.')
        return [app_sett.old_file, app_sett.new_file]


def get_email(username):  # get email address from database using tag we got from dynalist
    email = False
    logger.info(f'getting email address for {username}')
    req = Users.query.filter_by(username=username, push_email=1).first()
    if req:
        email = req.email
        logger.info(f'Found {email} for {username}.')
    return email


def parse(old, new, dry_run):
    # Compare two files dynalist-a.txt (old) and dynalist-b.txt (new) that were previously saved before by save().
    logger.info('reading old.txt.')
    old_file = open(old, 'r', encoding='utf-8').readlines()
    logger.info('reading new.txt.')
    new_file = open(new, 'r', encoding='utf-8').readlines()
    diff = [line for line in new_file if line not in old_file]
    if diff:
        logger.info('New tasks found.')
        logger.info('Parsing...')
        assigns = []
        mentions = []
        for line in diff:
            if line.count('@'):
                mentions = re.findall('\s@([a-z.]+)', line)
            if line.count('#'):
                assigns = re.findall('\s#([a-z.]+)', line)

            if mentions:
                for mention in mentions:
                    email = get_email(mention)
                    if email:
                        logger.info(f'Sending mail to {mention}, address {email}')
                        if not dry_run:
                            sendmail('Dynalist Notifications: New Mention', email,
                                     f'Hi {mention},\n\nYou have been mentioned in a new task:\n\n'
                                     f'"{split_content[1].rstrip()}"'
                                     f'\n{url}\n\nGood luck :)')
            if assigns:
                for assign in assigns:
                    email = get_email(assign)
                    if email:
                        logger.info(f'Sending mail to {assign}, address {email}')
                        split_content = line.split(' || ')
                        url = f"https://dynalist.io/d/{app_sett.dynalist_api_file_id}#z={split_content[0]}"
                        if not dry_run:
                            sendmail('Dynalist Notifications: New Task', email,
                                      f'Hi {assign},\n\nYou have been assigned a new task:\n\n'
                                      f'"{split_content[1].rstrip()}"\n{url}\n\nGood luck :)')
    else:
        logger.info('No changes detected.')


def sendmail(subject, emailto, message):  # Send email
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    msg = MIMEMultipart()
    fromaddr = app_sett.smtp_email
    msg['From'] = fromaddr
    msg['To'] = emailto
    msg['Subject'] = subject
    password = app_sett.smtp_password
    msg.attach(MIMEText(message, 'plain'))
    server = smtplib.SMTP(app_sett.smtp_host, int(app_sett.smtp_port))
    server.starttls()
    server.login(fromaddr, password)
    body = msg.as_string()
    server.sendmail(fromaddr, emailto, body)
    server.quit()
