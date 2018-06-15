
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app import celery

app = create_app()
