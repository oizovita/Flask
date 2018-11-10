import models
from models import Users, Template
from werkzeug.urls import url_parse
from app import app, db, oid, login
from forms import LoginForm, RegistrationForm, TemplateForm
from flask_login import current_user, login_user, login_required, logout_user
from flask import render_template, session, g, flash, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename

from dolly import *
from xlrd import open_workbook
import zipfile
import shutil

ALLOWED_EXTENSIONS = set(['doc', 'docx', 'html', 'xlsx'])


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
            return redirect(url_for('login'))
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
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(login=form.login.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('registration.html', form=form)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def load_file(data, template, user, save):
    create_folder(app.config['UPLOAD_DATA'] + str(user.id))
    create_folder(app.config['UPLOAD_TEMPLATE'] + str(user.id))
    if data and allowed_file(data.filename) and template and allowed_file(template.filename):
        filename = secure_filename(data.filename)
        data.save(os.path.join(app.config['UPLOAD_DATA'] + str(user.id), filename))
        template_name = secure_filename(template.filename)
        template.save(os.path.join(app.config['UPLOAD_TEMPLATE'] + str(user.id), template_name))

        tmp = Template(user_id=user.id, data=filename, template=template_name)
        db.session.add(tmp)
        db.session.commit()

        return True


def create_templates(template, user):
    template_db = Template.query.filter_by(user_id=user.id, template=template.filename).first()
    book = open_workbook(
        app.config['UPLOAD_DATA'] + str(template_db.user_id) + '/' + str(template_db.data),
        on_demand=True)
    sheet = book.sheet_by_name(book.sheet_names()[0])
    create_folder(app.config['BASEDIR'] + '/tmp_' + str(template_db.user_id))

    if template_db.template[-4:] == FILE_HTML:
        create_pdf_from_html_template(sheet, app.config['UPLOAD_TEMPLATE'] + str(template_db.user_id) + '/' +
                                      str(template_db.template),
                                      app.config['BASEDIR'] + '/tmp_' + str(template_db.user_id))
    elif template_db.template[-4:] == FILE_DOCX:
        substitution_into_a_template(sheet, app.config['UPLOAD_TEMPLATE'] + str(template_db.user_id) +
                                     '/' + str(template_db.template),
                                     app.config['BASEDIR'] + '/tmp_' + str(template_db.user_id))


def create_zip(user):
    z = zipfile.ZipFile(str(user.id) + '.zip', 'w')
    for root, dirs, files in os.walk('tmp_' + str(user.id)):
        for file in files:
            z.write(os.path.join(root, file))

    z.close()
    shutil.rmtree('tmp_' + str(user.id), ignore_errors=True)


@app.route('/user/<login>', methods=['POST', 'GET'])
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
        save = form.save_tmp.data
        if load_file(data, template, user, save):
            create_templates(template, user)
            create_zip(user)
        else:
            return render_template('user.html', form=form, user=user, message="Invalid file type")



    return render_template('user.html', form=form, user=user)


@app.route('/uploads/<login>')
def uploads(login):
    user = Users.query.filter_by(login=login).first()
    return send_file(app.config['BASEDIR'] + '/' + str(user.id) + '.zip', as_attachment=True)
