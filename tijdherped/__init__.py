""" Defines core app components """

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='templates')
app.config.from_object('config.DevelopmentConfig')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tijdherped.db'
db = SQLAlchemy(app)
db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

bcrypt = Bcrypt(app)

from tijdherped.auth import auth
from tijdherped.api.v1 import v1
from tijdherped.teachers import teachers
from tijdherped.students import students
app.register_blueprint(auth)
app.register_blueprint(v1)
app.register_blueprint(teachers)
app.register_blueprint(students)

import tijdherped.routes
