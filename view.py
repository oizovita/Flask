import os
import models
import shutil
import zipfile
from dolly import *
from xlrd import open_workbook
from models import Users, Template
from werkzeug.urls import url_parse
from app import app, db, oid, login
from werkzeug.utils import secure_filename
from forms import LoginForm, RegistrationForm, TemplateForm
from flask_login import current_user, login_user, login_required, logout_user
from flask import render_template, session, g, flash, request, redirect, url_for, send_file
import time

# valid template files
ALLOWED_EXTENSIONS_TEMPLATE = ['doc', 'docx', 'html']
# valid data files
ALLOWED_EXTENSIONS_DATA = 'xlsx'


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


# data file check
def allowed_file_data(filename):
    return ('.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS_DATA)


# data template check
def allowed_file_template(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS_TEMPLATE


# checks patterns and data and if everything puts them well into the database.
# runs file and archive creation.
def data_and_template_handler(data, template, user):
    data_file_name = check_file(data, 'data', user, 'UPLOAD_DATA', )
    template_file_name = check_file(template, 'template', user, 'UPLOAD_TEMPLATE')
    if data_file_name and template_file_name:
        global name_zip
        name_zip = str(time.ctime()).replace(" ", "_") + '.zip'

        tmp = Template(user_id=user.id, template=template_file_name)
        db.session.add(tmp)
        db.session.commit()

        creating_files_by_template(user, data_file_name, template_file_name)
        create_zip(user, name_zip, 'UPLOAD_ZIP')

        return True


# checks incoming data files and templates and if everything loads them correctly
def check_file(file, type, user, dir):
    if type == 'data':
        if file and allowed_file_data(file.filename):
            try:
                filename = load_file(file, user, dir)
                return filename
            except Exception:
                return False
    elif type == 'template':
        if file and allowed_file_template(file.filename):
            try:
                filename = load_file(file, user, dir)
                return filename
            except Exception:
                return False
    else:
        return False


# uploads file to server
def load_file(file, user, dir):
    create_folder(app.config[dir] + str(user.id))

    filename = 'file_' + str(int(time.time())) + '_' + secure_filename(file.filename)
    file.save(os.path.join(app.config[dir] + str(user.id), filename))
    return filename


# creates files based on the specified template in pdf or doc format
def creating_files_by_template(user, data_file_name, template_file_name):
    book = open_workbook(
        app.config['UPLOAD_DATA'] + str(user.id) + '/' + str(data_file_name),
        on_demand=True)
    sheet = book.sheet_by_name(book.sheet_names()[0])
    create_folder(app.config['BASEDIR'] + '/tmp_' + str(user.id))

    if template_file_name[-4:] == FILE_HTML:
        create_pdf_from_html_template(sheet, app.config['UPLOAD_TEMPLATE'] + str(user.id) + '/' +
                                      str(template_file_name),
                                      app.config['BASEDIR'] + '/tmp_' + str(user.id))
    elif template_file_name[-4:] == FILE_DOCX:
        substitution_into_a_template(sheet, app.config['UPLOAD_TEMPLATE'] + str(user.id) +
                                     '/' + str(template_file_name),
                                     app.config['BASEDIR'] + '/tmp_' + str(user.id))

    shutil.rmtree(app.config['UPLOAD_DATA'])


# creates archive for download
def create_zip(user, name_zip, dir):
    create_folder(app.config[dir] + str(user.id))
    if os.path.isfile(name_zip):
        os.remove(name_zip)

    z = zipfile.ZipFile(name_zip, 'w')
    for root, dirs, files in os.walk('tmp_' + str(user.id)):
        for file in files:
            z.write(os.path.join(root, file))

    z.close()

    shutil.rmtree('tmp_' + str(user.id))
    shutil.move(name_zip, app.config[dir] + str(user.id))


@app.route('/user/<login>/', methods=['POST', 'GET'])
@login_required
def user(login):
    user = Users.query.filter_by(login=login).first()
    form = TemplateForm()
    if user == None:
        flash('User ' + login + ' not found.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = form.data.data
        template = form.template.data

        if data_and_template_handler(data, template, user):
            return render_template('user.html', form=form, user=user, message=name_zip)
        else:
            return render_template('user.html', form=form, user=user, error="Invalid file type")

    return render_template('user.html', form=form, user=user)


@app.route('/uploads/<filename>/<login>')
def uploads(filename, login):
    user = Users.query.filter_by(login=login).first()
    return send_file(app.config['UPLOAD_ZIP'] + str(user.id) + '/' + filename, as_attachment=True, cache_timeout=-1)


@app.route('/template/<login>')
def template(login):
    user = Users.query.filter_by(login=login).first()
    templ = Template.query.filter_by(user_id=user.id).all()

    return render_template('template.html', login=login, templates=templ)


@app.route('/uploads_template/<filename>/<login>')
def uploads_template(filename, login):
    user = Users.query.filter_by(login=login).first()
    return send_file(app.config['UPLOAD_TEMPLATE'] + str(user.id) + '/' + filename, as_attachment=True,
                     cache_timeout=-1)


