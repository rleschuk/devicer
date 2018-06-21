
import os

from devicer.dbapi import create_dbapi

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or "sqlite:///%s/devicer.db" % BASE_DIR
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY') or 'devicer'
    TEMPLATES_AUTO_RELOAD = True

    SQL_DEVICER_URLS = {
        '__main__': create_dbapi(SQLALCHEMY_DATABASE_URI),
        'default': create_dbapi("oracle://os_usr:os_usr@192.168.66.38:1521/orange"),
        'eqm.enforta.net': create_dbapi("oracle://os_usr:os_usr@192.168.66.38:1521/orange"),
    }

    TAC_USERNAME = os.getenv('TAC_USERNAME') or "devicer"
    TAC_PASSWORD = os.getenv('TAC_PASSWORD') or "devicer"
    DEF_SELECT_CODE = os.getenv('DEF_SELECT_CODE') or ''

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL_DEV') or "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND_DEV') or "redis://localhost:6379/0"
    LOG_LEVEL = 'DEBUG'
    DEBUG = True


class ProductionConfig(Config):
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL') or "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND') or "redis://localhost:6379/0"


config = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
