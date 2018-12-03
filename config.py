import os
import subprocess
import sys
import os


class Configuration(object):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # way to connect to the heroku database
    # SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # local database connection path
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:lesclaypool@localhost/dolly'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))

    # folder for storing data
    UPLOAD_DATA = BASEDIR + '/file/data/'
    # folder for storing templates
    UPLOAD_TEMPLATE = BASEDIR + '/file/template/'

    # Ensure virtualenv path is part of PATH env var
    os.environ['PATH'] += os.pathsep + os.path.dirname(sys.executable)
    WKHTMLTOPDF_CMD = subprocess.Popen(['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf')],
                                          stdout=subprocess.PIPE).communicate()[0].strip()
