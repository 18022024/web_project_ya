from flask import flash, render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash

from app import db_session
from app.models.users import User
from app_key import TEMP_DIR
from forms.user import RegisterForm, LoginForm
from app.extensions import login_manager

auth_bp = Blueprint('auth', __name__, template_folder=TEMP_DIR)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash('Этот email уже используется', 'error')
            return render_template('register.html', form=form)

        if db_sess.query(User).filter(User.username == form.username.data).first():
            flash('Это имя пользователя уже занято', 'error')
            return render_template('register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=False)
        flash('Вы успешно создали аккаунт!', 'success')
        return redirect(url_for('other.main_page'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('other.main_page'))

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            remember = form.remember.data if 'remember' in request.form else False
            login_user(user, remember=remember)

            flash('Вы успешно вошли в профиль!', 'success')
            return redirect(url_for('other.main_page'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('other.main_page'))