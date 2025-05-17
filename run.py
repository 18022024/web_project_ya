from flask import Flask

from app.config import config_app
from app.db_session import global_init
from app.extensions import socketio

app = Flask(__name__)

app = config_app(app)


if __name__ == '__main__':
    global_init('db/chat.sqlite')
    socketio.run(
        app,
        port=8080,
        host='127.0.0.1',
        debug=True,
        use_reloader=True,
        log_output=True
    )