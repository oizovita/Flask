import os


class Configuration(object):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # way to connect to the heroku database
    #SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # local database connection path
    #SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:lesclaypool@localhost/dolly'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://oizovita:lesclaypool@oizovita.mysql.pythonanywhere-services.com/dolly'
    # folder for storing data
    UPLOAD_DATA = BASEDIR + '/file/data/'
    # folder for storing templates
    UPLOAD_TEMPLATE = BASEDIR + '/file/template/'
    UPLOAD_ZIP = BASEDIR + '/file/zip/'
