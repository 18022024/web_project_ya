from .extensions import login_manager, csrf, socketio

from app_key import MY_KEY


def config_app(app):
    app.config['SECRET_KEY'] = MY_KEY
    app.config['SWAGGER'] = {
        'title': 'Chat API',
        'uiversion': 3,
        'description': 'API documentation for the chat application',
        'termsOfService': '',
        'specs_route': '/swagger'
    }

    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, async_mode="eventlet")

    from .routes.auth import auth_bp
    from .routes.main_profile_routes import main_bp
    from .routes.room_routes import rooms_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(rooms_bp)

    return app