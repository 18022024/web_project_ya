import datetime

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, flash, url_for, request
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_socketio import emit, SocketIO, join_room
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from flasgger import Swagger, swag_from

from app_key import MY_KEY
from app import db_session
from app.messages import Messages
from app.room_access import RoomAccess
from app.rooms import Rooms
from app.users import User
from forms.room import RoomForm, RoomAccessForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = MY_KEY

app.config['SWAGGER'] = {
    'title': 'Chat API',
    'uiversion': 3,
    'description': 'API documentation for the chat application',
    'termsOfService': '',
    'specs_route': '/swagger'
}
swagger = Swagger(app)

socketio = SocketIO(app, async_mode='eventlet')

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)


@socketio.on('join_room')
def on_join(data):
    print(f"Пользователь {data['username']} присоединился")
    join_room(data['room_id'])


@socketio.on('send_message')
def handle_send_message(data):
    db_sess = db_session.create_session()
    content = data['content']

    msg = Messages(user_id=current_user.id, content=content, room_id=data['room_id'])
    db_sess.add(msg)
    db_sess.commit()

    emit('new_message', {'sender': current_user.username, 'sender_id': current_user.id, 'time': datetime.datetime.now().strftime('%H:%M'), 'content': content}, broadcast=True)


@app.route("/")
def main_page():
    """
    Main page endpoint
    ---
    tags:
      - Pages
    responses:
      200:
        description: Returns the main page with all rooms
    """
    db_sess = db_session.create_session()
    rooms = db_sess.query(Rooms).all()
    return render_template("main_page.html", rooms=rooms)


@app.route("/profile")
@login_required
def profile_page():
    """
    User profile page
    ---
    tags:
      - Pages
    responses:
      200:
        description: Returns the profile page of the current user
      401:
        description: Unauthorized access
    """
    db_sess = db_session.create_session()
    rooms = db_sess.query(Rooms).filter(Rooms.creator_id == current_user.id).all()
    return render_template("profile.html", user=current_user, rooms=rooms)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: formData
        name: username
        type: string
        required: true
        description: The desired username
      - in: formData
        name: email
        type: string
        required: true
        description: User's email address
      - in: formData
        name: password
        type: string
        required: true
        description: User's password
      - in: formData
        name: confirm_password
        type: string
        required: true
        description: Password confirmation
    responses:
      200:
        description: Registration form or success message
      302:
        description: Redirect to main page after successful registration
    """
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
        return redirect(url_for('main_page'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: formData
        name: email
        type: string
        required: true
        description: User's email address
      - in: formData
        name: password
        type: string
        required: true
        description: User's password
      - in: formData
        name: remember
        type: boolean
        required: false
        description: Remember me option
    responses:
      200:
        description: Login form or success message
      302:
        description: Redirect to main page after successful login
    """
    if current_user.is_authenticated:
        return redirect(url_for('main_page'))

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            remember = form.remember.data if 'remember' in request.form else False
            login_user(user, remember=remember)

            flash('Вы успешно вошли в профиль!', 'success')
            return redirect(url_for('main_page'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html', form=form)


@app.route("/create_room", methods=['GET', 'POST'])
@login_required
def create_room():
    """
    Create a new room
    ---
    tags:
      - Rooms
    parameters:
      - in: formData
        name: name
        type: string
        required: true
        description: Room name
      - in: formData
        name: is_private
        type: boolean
        required: false
        description: Is the room private
      - in: formData
        name: password
        type: string
        required: false
        description: Room password (if private)
    responses:
      200:
        description: Room creation form or success message
      302:
        description: Redirect to main page after room creation
      401:
        description: Unauthorized access
    """
    form = RoomForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        room = Rooms(
            name=form.name.data,
            creator_id=current_user.id,
            is_private=form.is_private.data
        )

        room.set_password(form.password.data)

        db_sess.add(room)
        db_sess.commit()

        access = RoomAccess(user_id=current_user.id, room_id=room.id)
        db_sess.add(access)
        db_sess.commit()

        flash(f'Комната "{form.name.data}" создана', 'success')

        return redirect(url_for('main_page'))

    return render_template('create_room.html', form=form)


@app.route("/delete_room/<int:room_id>", methods=['POST'])
@login_required
def delete_room(room_id):
    """
    Delete a room
    ---
    tags:
      - Rooms
    parameters:
      - in: path
        name: room_id
        type: integer
        required: true
        description: ID of the room to delete
    responses:
      302:
        description: Redirect to profile page after deletion
      401:
        description: Unauthorized access
      404:
        description: Room not found
    """
    db_sess = db_session.create_session()
    room = db_sess.query(Rooms).filter(Rooms.id == room_id, Rooms.creator_id == current_user.id).first()
    accesses = db_sess.query(RoomAccess).filter(RoomAccess.room_id == room.id).all()
    if room:
        for access in accesses:
            db_sess.delete(access)
        db_sess.delete(room)
        db_sess.commit()
        print(accesses)
        flash('Комната успешно удалена', 'success')
    else:
        flash('Комната не найдена или у вас нет прав', 'error')

    return redirect(url_for('profile_page'))


@app.route('/search')
@login_required
def search_rooms():
    """
    Search for rooms
    ---
    tags:
      - Rooms
    parameters:
      - in: query
        name: query
        type: string
        required: false
        description: Search query
    responses:
      200:
        description: Returns search results
      401:
        description: Unauthorized access
    """
    query = request.args.get('query', '').strip()
    db_sess = db_session.create_session()

    if query:
        rooms = db_sess.query(Rooms).filter(
            Rooms.name.ilike(f'%{query}%')
        ).order_by(Rooms.created_at.desc()).all()
    else:
        rooms = db_sess.query(Rooms).order_by(Rooms.created_at.desc()).all()

    return render_template('main_page.html',
                           rooms=rooms,
                           tittle_word=f"Результаты поиска: '{query}'" if query else "Все комнаты")


@app.route('/enter_private_room/<int:room_id>', methods=['POST', 'GET'])
def enter_private_room(room_id):
    """
    Enter a private room
    ---
    tags:
      - Rooms
    parameters:
      - in: path
        name: room_id
        type: integer
        required: true
        description: ID of the private room
      - in: formData
        name: password
        type: string
        required: true
        description: Room password
    responses:
      200:
        description: Password form or redirect to room
      302:
        description: Redirect to room if access granted
      401:
        description: Unauthorized access
      404:
        description: Room not found
    """
    db_sess = db_session.create_session()
    room = db_sess.get(Rooms, room_id)
    form = RoomAccessForm()

    if not room:
        flash('Комната не найдена', 'error')
        return redirect(url_for('main_page'))

    if not room.is_private:
        return redirect(url_for('join_room', room_id=room.id))

    access = db_sess.query(RoomAccess).filter(RoomAccess.user_id == current_user.id,
                                              RoomAccess.room_id == room_id).first()
    if access:
        return redirect(url_for('join_room', room_id=room.id))

    if form.validate_on_submit():
        if check_password_hash(room.password, form.password.data):

            access = RoomAccess(user_id=current_user.id, room_id=room.id)

            db_sess.add(access)
            db_sess.commit()

            return redirect(url_for('join_room', room_id=room.id))
        else:
            flash('Неверный пароль', 'error')

    return render_template('room_password.html', room=room, form=form)


@app.route('/join_room/<int:room_id>')
@login_required
def join_room(room_id):
    """
    Join a room
    ---
    tags:
      - Rooms
    parameters:
      - in: path
        name: room_id
        type: integer
        required: true
        description: ID of the room to join
    responses:
      200:
        description: Returns the room page
      302:
        description: Redirect to main page if room not found
      401:
        description: Unauthorized access
    """
    db_sess = db_session.create_session()
    room = db_sess.get(Rooms, room_id)

    if not room:
        flash('Комната не найдена', 'error')
        return redirect(url_for('main_page'))

    messages = db_sess.query(Messages).filter(Messages.room_id == room.id).order_by(Messages.date.asc()).all()

    return render_template('room.html', room=room, messages=messages, current_user=current_user)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/logout')
@login_required
def logout():
    """
    Logout endpoint
    ---
    tags:
      - Authentication
    responses:
      302:
        description: Redirect to main page after logout
      401:
        description: Unauthorized access
    """
    logout_user()
    return redirect(url_for('main_page'))


def main():
    db_session.global_init('db/chat.sqlite')
    socketio.run(app,
                 port=8080,
                 host='127.0.0.1',
                 debug=True,
                 use_reloader=True,
                 log_output=True)


if __name__ == '__main__':
    main()