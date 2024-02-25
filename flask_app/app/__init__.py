from flask import Flask

from .config import DevConfig, ProdConfig

from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager

db = SQLAlchemy()

from .models import User

import os

env = os.environ.get('ENV')

if env == 'dev':
    env_config = DevConfig
    os.environ["FLASK_DEBUG"] = "1"
else :
    env_config = ProdConfig

def create_app(config_class=env_config):
    app = Flask(__name__, static_folder='./static')
    app.config.from_object(config_class) 
    db.init_app(app) 
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))


    # Initialize Flask extensions here
    from app.main import main_bp
    from app.auth import auth_bp
    # Register blueprints here
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app