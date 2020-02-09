from flask import Blueprint, redirect, url_for, render_template, flash
from flask_login import login_user, current_user, login_required, logout_user

from tijdherped import db, bcrypt
from tijdherped.models import User
from tijdherped import app

from .forms import LoginForm

auth = Blueprint('auth', __name__, url_prefix='/auth/', template_folder='templates/auth/')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not (user and bcrypt.check_password_hash(user.password, form.password.data)):
            flash('Email and password don\'t match.', 'danger')
            return render_template('login.html', title='Login', form=form)
        login_user(user, remember=True)
        return redirect(url_for('index'))

    return render_template('login.html', title='Login', form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
