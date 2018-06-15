
import os
import sys
import click

from dotenv import load_dotenv
load_dotenv()

from flask_migrate import Migrate
from app import create_app
from app import db
from app import celery
from app import scheduler, init_scheduler
from app.models import View

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, View=View)

try:
    init_scheduler(app)
    scheduler.start()
except Exception as err:
    print(repr(err))
