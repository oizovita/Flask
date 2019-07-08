import os
from flask import Flask
from flask_openid import OpenID
from config import Configuration
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
app = Flask(__name__)
app.config.from_object(Configuration)
mail = Mail(app)

db = SQLAlchemy(app)

login = LoginManager(app)
login.init_app(app)
login.login_view = 'login'

oid = OpenID(app, os.path.join(Configuration.BASEDIR, 'tmp'))


