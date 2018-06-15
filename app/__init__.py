
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from celery.result import AsyncResult
from apscheduler.triggers.cron import CronTrigger

from .config import config

CONFIG = config[os.getenv('CONFIG') or 'default']
db = SQLAlchemy()
scheduler = APScheduler()

from devicer import Device
from .celery_tasks import celery
from .celery_tasks import cron_task
from .models import View


def create_app(config=CONFIG):
    app = Flask(__name__)
    app.config.from_object(config)

    config.init_app(app)
    db.init_app(app)
    scheduler.init_app(app)

    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    init_blueprints(app)
    #try:
    #    init_scheduler(app)
    #    scheduler.start()
    #except Exception as err:
    #    print(repr(err))


    return app


def init_blueprints(app):
    # /app/main/__init__.py
    from .main import main as main_bp
    app.register_blueprint(main_bp)


def init_scheduler(app):
    with app.app_context():
        views = View.query.filter_by(crontab_enabled=True).all()
        for view in views:
            try: cron = CronTrigger.from_crontab(view.crontab)
            except ValueError:
                print('ValueError: %s' % view.crontab)
                continue
            scheduler.add_job(view.view_key, cron_task,
                trigger=cron, args=(view.view_key,))
            print('%s add to scheduler' % view.view_key)
