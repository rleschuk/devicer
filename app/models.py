
import json
import datetime
from . import db


class View(db.Model):
    __tablename__   = 'devicer_views'
    view_key        = db.Column(db.String(20), primary_key=True)
    view_name       = db.Column(db.String)
    view_saved      = db.Column(db.DateTime, default=datetime.datetime.now())
    selecter_mode   = db.Column(db.String)
    selecter_code   = db.Column(db.Text())
    devicer_code    = db.Column(db.Text())
    data            = db.Column(db.Text())
    lock            = db.Column(db.Boolean, default=False)
    lock_password   = db.Column(db.String)
    settings        = db.Column(db.Text())
    crontab_enabled = db.Column(db.Boolean, default=False)
    crontab         = db.Column(db.String, default='0 0 * * 1')

    def __init__(self, view_key, view_name=None, data=None, settings=None, **kwargs):
        self.view_key = view_key
        self.view_name = view_name
        if self.view_name is None:
            self.view_name = view_key
        if data is not None:
            self.data = json.dumps(data, ensure_ascii=False)
        if settings is not None:
            self.settings = json.dumps(settings, ensure_ascii=False)
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)

    def to_dict(self):
        return {
            'view_key': self.view_key,
            'view_name': self.view_name,
            'view_saved': self.view_saved.strftime('%Y/%m/%d %H:%M:%S'),
            'data': json.loads(self.data) if self.data else None,
            'settings': json.loads(self.settings) if self.settings else None,
            'lock': self.lock,
            'crontab_enabled': self.crontab_enabled,
            'crontab': self.crontab
        }

    @staticmethod
    def before_update_listener(mapper, connection, target):
        target.view_saved = datetime.datetime.now()

db.event.listen(View, 'before_update', View.before_update_listener)
