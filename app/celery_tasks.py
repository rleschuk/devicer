
import os
import re
import json
import time
import datetime

from celery import Celery, Task
from celery import states
#from celery import current_app
#from celery.signals import before_task_publish, task_prerun, after_task_publish
from celery.result import AsyncResult
from devicer import Device
from devicer import dbapi
from .config import config
from .models import View
from . import scheduler
from . import db
from . import utils

CONFIG = config[os.getenv('CONFIG') or 'default']
celery = Celery(__name__, broker=CONFIG.CELERY_BROKER_URL)

#@after_task_publish.connect
#def after_task_publish_signal(sender=None, body=None, **kwargs):
#    task = current_app.tasks.get(sender)
#    backend = task.backend if task else current_app.backend
#    backend.store_result(body['id'], None, 'SENT')
#    #task.update_state(state='PENDING')


@celery.task(bind=True)
def exec_user_code(self, row, code):
    #self.update_state(state='PENDING')
    state = error = None
    device = Device(**row)
    device.init()
    namespace = locals()
    namespace['re'] = re
    try:
        exec(code, namespace, namespace)
        device.run_tasks()
        device.run_columns()
        state = 'SUCCESS'
    except Exception as err:
        state = 'FAILURE'
        error = [type(err).__name__, err.args[0]]
    return {
        'state': state,
        'datetime': datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        'result': device.to_dict(),
        'error': error
    }


def get_task_result(task_id=None, task=None):
    if task is None and task_id is not None:
        task = AsyncResult(task_id, app=celery)
    result = dict(task_id=task.id, task_date=None, task_error=None,
                  task_result=None, task_state=task.state)
    if isinstance(task.result, Exception):
        name = task.result.__class__.__name__
        args = utils.parse_tuple(task.result.args[0])
        result['task_error'] = ('%s: %s' % (name, args[0])) if args[0] else name
        result['task_date'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    elif task.result and task.state not in ('PENDING', 'PROCESSING'):
        result['task_state'] = task.result['state']
        result['task_result'] = task.result['result']['results']
        result['task_date'] = task.result['datetime']
        if task.result['error']:
            result['task_error'] = '%s: %s' % (*task.result['error'],)
        for attr, value in task.result['result']['rowattrs'].items():
            result[attr] = value
    return result


def cron_task(view_key):
    app = scheduler.app
    with app.app_context():
        view = View.query.filter_by(view_key=view_key).first()
        data = json.loads(view.data)
        settings = json.loads(view.settings)
        if settings['selecter']['mode'] == 'sql':
            data = dbapi.execute(settings['selecter']['code'],
                config=app.config['SQL_DEVICER_URLS'],
                current=data['rows'])
        tasks = []

        for row in data['rows']:
            if row.get('task_id'):
                task = exec_user_code.s(row, settings['devicer']['code'])\
                    .apply_async(task_id=row['task_id'])
                task.forget()
            else:
                task = exec_user_code.s(row, settings['devicer']['code'])\
                    .apply_async()
            tasks.append(task)

        while len([t.state for t in tasks if t.state in ('PENDING','PROCESSING')]) > 0:
            time.sleep(10)

        for i, task in enumerate(tasks):
            result = get_task_result(task=task)
            data['rows'][i].update(result)
            '''
            data['rows'][i]['task_id'] = task.id
            data['rows'][i]['task_state'] = task.state
            if isinstance(task.result, Exception):
                name = task.result.__class__.__name__
                data['rows'][i]['task_error'] = ('%s: %s' % (name, task.result.args[:1]))\
                    if task.result.args else name
                data['rows'][i]['task_date'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            elif task.result:
                data['rows'][i]['task_state'] = task.result['state']
                if task.result['result']:
                    data['rows'][i]['task_result'] = task.result['result']['results']
                    for attr, value in task.result['result']['rowattrs'].items():
                        if attr in (c['name'] for c in data['columns']):
                            data['rows'][i][attr] = value
                if task.result['error']:
                    data['rows'][i]['task_error'] = '%s: %s' % (*task.result['error'],)
                else:
                    data['rows'][i]['task_error'] = None
                data['rows'][i]['task_date'] = task.result['datetime']
            '''

        view.data = json.dumps(data)
        db.session.add(view)
        db.session.commit()
        print('%s scheduled %s' % (datetime.datetime.now(), view_key))
