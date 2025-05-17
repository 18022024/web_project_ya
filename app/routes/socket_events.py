import datetime

from flask_login import current_user
from flask_socketio import join_room, emit

from app import db_session
from app.models.messages import Messages
from run import socketio


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

    emit('new_message', {'sender': current_user.username, 'sender_id': current_user.id,
                         'time': datetime.datetime.now().strftime('%H:%M'), 'content': content}, broadcast=True)
