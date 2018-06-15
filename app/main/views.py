
import os
import re
import time
import json
import string
import random
import datetime

from flask import (Flask, render_template, jsonify, request, Response,
                   abort, redirect, make_response, url_for, current_app)
from celery.result import AsyncResult
from apscheduler.triggers.cron import CronTrigger

from devicer import Device
from devicer import dbapi
from . import main
from .. import db
from .. import celery
from .. import utils
from .. import scheduler
from ..celery_tasks import exec_user_code, cron_task, get_task_result
from ..models import View


@main.route('/', methods=['GET'])
def home():
    view_key = request.cookies.get('view_key')
    if view_key is None:
        view_key = ''.join((
            random.choice(string.ascii_letters + string.digits) for _ in range(8)
        ))
    return redirect(url_for('main.view', view_key=view_key))


@main.route('/new', methods=['GET'])
def new():
    view_key = ''.join((
        random.choice(string.ascii_letters + string.digits) for _ in range(8)
    ))
    return redirect(url_for('main.view', view_key=view_key))


@main.route('/lock/<string:view_key>', methods=['POST'])
def lock(view_key):
    data = request.get_json()
    view = View.query.filter_by(view_key=view_key).first()
    if view:
        if data.get('lock') == True:
            if view.lock == False:
                view.lock = True
                view.lock_password = data.get('lock_password', view_key)
        elif data.get('lock') == False:
            if view.lock == True:
                if view.lock_password == data.get('lock_password'):
                    view.lock = False
                else:
                    return Response(render_template('error.html',
                        name='Password invalid',
                        args=('lock password incorrect',)), 403)
        else: Response(render_template('error.html', name='Bad Request', args=('',)), 400)
        db.session.add(view)
        db.session.commit()
        return jsonify(result=True)
    return Response(render_template('error.html',
        name='View not found',
        args=('current view is not saved',)), 404)


@main.route('/view/<string:view_key>', methods=['GET'])
def view(view_key):
    view = View.query.filter_by(view_key=view_key).first()
    crontab_job = scheduler.get_job(view_key)
    response = make_response(render_template('view.html',
        now = datetime.datetime.now(),
        view_key = view_key,
        view = view.to_dict() if view else None,
        next_run = crontab_job.next_run_time\
            .strftime('%Y/%m/%d %H:%M:%S') if crontab_job else None
        #def_select_code = current_app.config['DEF_SELECT_CODE']
    ))
    response.set_cookie('view_key', view_key)
    return response


@main.route('/log/<string:task_id>', methods=['GET'])
def task_log(task_id):
    task = AsyncResult(task_id, app=celery)
    #if task and task.result and not isinstance(task.result, Exception):
    #    result = task.result['task_result']
        #data = '\n'.join([
        #    '# task_id: %s' % task.id,
        #    '# task_state: %s' % task.result['state'],
        #    '\n', log if log else 'no log'
        #])
    #else:
        #data = '\n'.join([
        #    '# task_id: %s' % task.id,
        #    '# task_state: %s' % task.result['state'],
        #    '\n', 'no log'
        #])
    if task: return render_template('log.html', task=task)
    return abort(404)


@main.route('/task/<string:task_id>', methods=['GET'])
def task_info(task_id):
    return jsonify(get_task_result(task_id))


@main.route('/tasks', methods=['POST'])
def tasks():
    def generate(rows):
        while 'PENDING' in [row['task_state'] for row in rows]:
            for i, row in enumerate(rows[:]):
                result = get_task_result(row['task_id'])
                if result['task_state'] not in ('PENDING', 'PROCESSING'):
                    rows.remove(row)
                    yield json.dumps(result, ensure_ascii=False) + '\n'
            time.sleep(5)
    rows = request.get_json()
    return Response(generate(rows), content_type='text/plain')


@main.route('/exec_select', methods=['POST'])
def exec_select():
    data = request.get_json()
    rows = data.get('rows')
    code = data.get('code')
    if rows is None or code is None:
        return abort(400)
    for i, row in enumerate(rows):
        if row.get('task_id'):
            task = exec_user_code.s(row, code).apply_async(task_id=row['task_id'])
            task.forget()
        else:
            task = exec_user_code.s(row, code).apply_async()
        rows[i].update(task_id=task.id, task_state=task.state)
    return jsonify(rows)


@main.route('/exec_device', methods=['POST'])
def exec_device():
    data = request.get_json()
    row = data.get('row')
    code = data.get('code')
    if row is None and code is None:
        return abort(400)
    if row.get('task_id'):
        task = exec_user_code.s(row, code).apply_async(task_id=row['task_id'])
        task.forget()
    else:
        task = exec_user_code.s(row, code).apply_async()
    return jsonify(task_id=task.id, task_state='PENDING')


@main.route('/execute_sql', methods=['POST'])
def execute_sql():
    data = request.get_json()
    sql = data.get('sql')
    current = data.get('current')
    if sql is None:
        return Response('Bad SQL query', 400)
    try:
        data = dbapi.execute(sql,
            config=current_app.config['SQL_DEVICER_URLS'],
            current=current)
        return jsonify(data)
    except Exception as err:
        return Response(render_template('error.html',
            name=err.__class__.__name__,
            args=err.args), 400)


@main.route('/save_view/<string:view_key>', methods=['POST'])
def save_view(view_key):
    data = request.get_json()
    view = View(view_key, **data)

    if view.crontab_enabled == True:
        try: cron = CronTrigger.from_crontab(view.crontab)
        except ValueError:
            return Response(render_template('error.html',
                name='CronTab value error',
                args=('crontab string not valid',)), 403)
        if view_key in [j.id for j in scheduler.get_jobs()]:
            scheduler.remove_job(view_key)
        scheduler.add_job(view_key, cron_task, trigger=cron, args=(view_key,))
        print(scheduler.get_jobs())
    elif view.crontab_enabled == False:
        if view_key in [j.id for j in scheduler.get_jobs()]:
            scheduler.remove_job(view_key)
        print(scheduler.get_jobs())

    db.session.merge(view)
    db.session.commit()
    return jsonify(result='ok')
