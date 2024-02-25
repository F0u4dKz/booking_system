import os

#basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    AIRTABLE_KEY = os.environ.get('AIRTABLE_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'


class DevConfig(Config):

    DEVELOPMENT = True
    DEBUG = True


class ProdConfig(Config):

    DEVELOPMENT = False
    DEBUG = False