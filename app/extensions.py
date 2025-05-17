from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flasgger import Swagger
from flask_socketio import SocketIO

login_manager = LoginManager()
csrf = CSRFProtect()
swagger = Swagger()
socketio = SocketIO()