import os


class Configuration(object):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    #SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:lesclaypool@localhost/dolly'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))

    UPLOAD_DATA = BASEDIR + '/file/data/'
    UPLOAD_TEMPLATE = BASEDIR + '/file/template/'
    UPLOAD_ZIP = BASEDIR + '/zip_file'

