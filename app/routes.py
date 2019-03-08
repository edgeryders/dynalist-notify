from flask import render_template, redirect, url_for, flash, abort, jsonify, request
from . import app, db
from . models import Users, deadlines, AppSettings, serialize
from . forms import RegistrationForm, LoginForm, SettingsForm
from flask_login import login_required, login_user, current_user, logout_user
import hashlib


@app.route('/')
@login_required
def index():
    tags = Users.query.filter(Users.id != current_user.id).all()
    return render_template('index.html', taskinfo=deadlines(current_user.username), tags=tags)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
            user = Users.query.filter_by(username=form.username.data).first()
            if user and hashlib.sha256(form.password.data.encode()).hexdigest() == user.password:
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
            flash('Invalid credentials', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hash_pw = hashlib.sha256(form.password.data.encode()).hexdigest()
        user = Users(username=form.username.data, email=form.email.data, password=hash_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Hi {form.username.data}, your account has been created successfully.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Sign Up', form=form)


@app.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.alert_deadline = form.alert_deadline.data
        current_user.push_email = form.push_email.data
        current_user.push_web = form.push_web.data
        db.session.commit()
        flash('Settings updated', 'success')
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.push_email.data = current_user.push_email
    form.push_web.data = current_user.push_web
    form.alert_deadline.data = current_user.alert_deadline
    return render_template('settings.html', form=form, title='Settings')


@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.is_admin:
        app_sett = AppSettings.query.get('core')
        if request.method == 'POST':
            if current_user.is_admin and request.is_json:
                data = request.json
                app_sett.app_name = data['app_name']
                app_sett.backup_enabled = data['backup_enabled']
                app_sett.backup_type = data['backup_type']
                app_sett.google_drive_id = data['google_drive_id']
                app_sett.backup_file_prefix = data['backup_file_prefix']
                app_sett.email_push_enabled = data['email_push_enabled']
                app_sett.web_push_enabled = data['web_push_enabled']
                app_sett.dynalist_api_token = data['dynalist_api_token']
                app_sett.dynalist_api_url = data['dynalist_api_url']
                app_sett.dynalist_api_file_id = data['dynalist_api_file_id']
                app_sett.smtp_host = data['smtp_host']
                app_sett.smtp_port = data['smtp_port']
                app_sett.smtp_email = data['smtp_email']
                app_sett.smtp_password = data['smtp_password']
                db.session.commit()
                return jsonify({'status': True, 'message': 'Saved successfully.'})
        return render_template('admin.html', title='Admin panel', data=app_sett)
    abort(403)


@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.context_processor
def app_name():
    return dict(app_name=AppSettings.query.with_entities(AppSettings.app_name).one()[0])


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
