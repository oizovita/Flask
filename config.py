import os


class Configuration(object):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # way to connect to the heroku database
    #SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # local database connection path
    SQLALCHEMY_DATABASE_URI = 'postgresql://dolly:test1234@db:5432/dolly'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    # folder for storing data
    UPLOAD_DATA = BASEDIR + '/file/data/'
    UPLOAD_JSON = BASEDIR + '/file/json/'
    # folder for storing templates
    UPLOAD_TEMPLATE = BASEDIR + '/file/template/'
    UPLOAD_ZIP = BASEDIR + '/file/zip/'

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS =True
    MAIL_USERNAME = "oles1103@gmail.com"
    MAIL_PASSWORD = "bmrxibwydbaybxet"



