import time
import shutil
import zipfile
import datetime
from dolly import *
from app import app, db, mail
from flask_mail import Message
from models import Template
from werkzeug.utils import secure_filename
from flask import render_template
from threading import Thread


# valid template files
ALLOWED_EXTENSIONS_TEMPLATE = ['doc', 'docx', 'html', 'pdf', 'json']
# valid data files
ALLOWED_EXTENSIONS_DATA = 'xlsx'


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
def data_and_template_handler(data, template, user, using_loaded_template, template_json=None):
    name_zip = str(time.ctime()).replace(" ", "_") + '.zip'
    data_file_name = check_file(data, 'data', user, 'UPLOAD_DATA', )
    template_file_json = None
    if template_json:
        template_file_json = check_file(template_json, 'json', user, 'UPLOAD_JSON')

    if not using_loaded_template:
        template_file_name = check_file(template, 'template', user, 'UPLOAD_TEMPLATE')
        if data_file_name and template_file_name:
            tmp = Template(user_id=user.id, template=template.filename, server_template=template_file_name,
                           create_date=datetime.datetime.today())
            db.session.add(tmp)
            db.session.commit()

            creating_files_by_template(user, data_file_name, template_file_name, template_file_json)
            create_zip(user, name_zip, 'UPLOAD_ZIP')
            # os.remove(app.config['UPLOAD_TEMPLATE'] + str(user.id) + '/' + template_file_name)
            return True, name_zip
    else:
        if data_file_name:
            creating_files_by_template(user, data_file_name, template, template_file_json)
            create_zip(user, name_zip, 'UPLOAD_ZIP')

            return True, name_zip

    return False, name_zip


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
    elif type == 'json':

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
def creating_files_by_template(user, data_file_name, template_file_name, template_file_json=None):
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
    elif template_file_name[-3:] == 'pdf' and template_file_json:
        create_pdf_templates(sheet, app.config['UPLOAD_JSON'] + str(user.id) +
                             '/' + str(template_file_json), app.config['UPLOAD_TEMPLATE'] + str(user.id) +
                             '/' + str(template_file_name), app.config['BASEDIR'] + '/tmp_' + str(user.id))
        shutil.rmtree(app.config['UPLOAD_JSON'])
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


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    with app.app_context():
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()
    return app


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('Reset Your Password',
               sender=app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('reset_password_mail.txt', user=user, token=token),
               html_body=render_template('reset_password_mail.html', user=user, token=token))
