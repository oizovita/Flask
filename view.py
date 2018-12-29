from scripts import *
from app import app, db
from models import Users, Template
from werkzeug.urls import url_parse
from forms import LoginForm, RegistrationForm, TemplateForm
from flask_login import current_user, login_user, login_required, logout_user
from flask import render_template, g, flash, request, redirect, url_for, send_file, after_this_request


@app.route('/')
def index():
    return render_template('index.html')


@app.before_request
def before_request():
    g.user = current_user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user', login=current_user.login))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(login=form.login.data).first()
        if user is None or not user.check_password(form.password.data):
            return render_template('login.html', form=form, error="Wrong login or password")
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('user', login=current_user.login)
        return redirect(next_page)
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('user', login=current_user.login))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(login=form.login.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registration.html', form=form)


@app.route('/user/<login>/', methods=['POST', 'GET'])
@login_required
def user(login):
    logged_in_user = Users.query.filter_by(login=login).first()
    all_downloaded_template = Template.query.filter_by(user_id=logged_in_user.id).all()
    form = TemplateForm()

    if logged_in_user == None:
        flash('User ' + login + ' not found.')
        return redirect(url_for('index'))

    using_loaded_template = False
    if request.method == 'POST':
        data = form.data.data
        template = form.template.data
        loaded_template = request.form['template_select']

        if template and loaded_template != 'Choose a template':
            using_loaded_template = False

        if not template and loaded_template != 'Choose a template':
            template = loaded_template
            using_loaded_template = True

        handler_result = data_and_template_handler(data, template, logged_in_user, using_loaded_template)

        if handler_result[0]:
            return render_template('user.html', form=form, user=logged_in_user, message=handler_result[1],
                                   templates=all_downloaded_template)
        else:
            return render_template('user.html', form=form, user=logged_in_user, error="Invalid file type",
                                   templates=all_downloaded_template)

    return render_template('user.html', form=form, user=logged_in_user, templates=all_downloaded_template)


@app.route('/uploads/<filename>/<login>')
def uploads(filename, login):
    logged_in_user = Users.query.filter_by(login=login).first()
    path_to_file = app.config['UPLOAD_ZIP'] + str(logged_in_user.id) + '/' + filename

    @after_this_request
    def remove_file(response):
        os.remove(path_to_file)
        return response

    return send_file(path_to_file, as_attachment=True, cache_timeout=-1)


@app.route('/uploads_temlate/<filename>/<login>')
def uploads_template(filename, login):
    logged_in_user = Users.query.filter_by(login=login).first()

    return send_file(app.config['UPLOAD_TEMPLATE'] + '/' + str(logged_in_user.id) + '/' + filename, as_attachment=True,
                     cache_timeout=-1)


@app.route('/template/<login>')
def template(login):
    logged_in_user = Users.query.filter_by(login=login).first()
    all_downloaded_template = Template.query.filter_by(user_id=logged_in_user.id).all()

    return render_template('template.html', login=login, templates=all_downloaded_template)


@app.route('/delete_template/<filename>/<login>')
def delete_template(filename, login):
    Template.query.filter_by(server_template=filename).delete()
    db.session.commit()
    return redirect(url_for('template', login=login))
