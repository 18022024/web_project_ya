from flask import Flask

from .config import config_app

def create_app():

    app = Flask(__name__)

    app = config_app(app)

    return app