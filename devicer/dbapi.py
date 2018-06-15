
import re
from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy import text
from collections import OrderedDict
import pandas as pd
import sqlparse


def create_dbapi(db_url):
    db_url = db_url.lower().strip()
    if db_url.startswith('oracle'):
        return Oracle(db_url)
    return DBApi(db_url)

def get_dbapi(db_url, config={}):
    if db_url in config:
        return config[db_url]
    dbapis = [(k, v) for k, v in config.items() if re.match(db_url, k)]
    if dbapis:
        return dbapis
    return create_dbapi(db_url)

def execute(sql, config={}, current=None):
    items = sqlparse.split(sql.strip())
    results = Results()
    result = None
    current = pd.DataFrame(current) if current else None

    regex_query = re.compile('--(?:\s+)?db:(?: +)?(\S+)(?: +as +(\S+))?')
    regex_eval = re.compile('--(?:\s+)?eval(?:\s+)?\n(.*)', re.DOTALL)
    regex_after = re.compile('--(?:\s+)?after(?:\s+)?\n(.*)', re.DOTALL)
    after = None
    for i, item in enumerate(items):
        item = re.sub(';$', '', item)
        match_query = regex_query.search(item)
        match_eval = regex_eval.search(item)
        match_after = regex_after.search(item)
        if match_query:
            dbapis = get_dbapi(match_query.group(1), config)
            if dbapis and isinstance(dbapis, list):
                for dbapi in dbapis:
                    name = '%s_%s' % (match_query.group(2), dbapi[0])\
                        if match_query.group(2) else dbapi[0]
                    results[name] = dbapi[1].read_sql_query(item)
            else:
                name = match_query.group(2) if match_query.group(2) else 'db%d' % i
                results[name] = dbapis.read_sql_query(item)
        elif match_eval:
            result = eval(match_eval.group(1))
        elif match_after:
            after = match_after.group(1)
        else:
            dbapi = config['default']
            results['db%d' % i] = dbapi.read_sql_query(item)
    if result is None and len(results.keys()) == 1:
        result = list(results.values())[0]
    elif result is None and len(results.keys()) > 1:
        result = pd.concat([df for df in results.values()], ignore_index=True, sort=True)
    elif len(results.keys()) == 0:
        raise Exception('Bad query')

    if after: result = eval(after)

    if not hasattr(result, 'task_id'): result['task_id'] = pd.Series()
    if not hasattr(result, 'task_date'): result['task_date'] = pd.Series()
    if not hasattr(result, 'task_error'): result['task_error'] = pd.Series()
    if not hasattr(result, 'task_result'): result['task_result'] = pd.Series()
    if not hasattr(result, 'task_state'): result['task_state'] = pd.Series()
    if hasattr(result, 'rowid'):
        result.drop('rowid', 1, inplace=True)
    result.reset_index(inplace=True)
    result.rename(columns={'index':'rowid'}, inplace=True)
    result = result.where(pd.notnull(result), None)

    return {
        'columns': list(result.columns.values),
        'rows': result.to_dict('record'),
    }

class Results(OrderedDict):
    def __getattr__(self, item):
        return self[item]
    def __setattr__(self, item, value):
        self[item] = value

class DBApi(object):

    def __init__(self, db_url):
        self._db_url = db_url
        self._engine = None

    def __getattr__(self, item):
        return getattr(self.engine, item)

    def zipped(self, rows):
        for i, row in enumerate(rows):
            yield [('rowid', i), *list(zip(row.keys(),row.values()))]

    def dicted(self, rows):
        for i, row in enumerate(rows):
            yield {**{'rowid': i}, **dict(row)}

    def splited(self, rows):
        return {
            'columns': ['rowid', *rows.keys()],
            'rows': list(map(lambda row: dict(rowid=row[0], **dict(row[1])), enumerate(rows)))
        }

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self._db_url)
        return self._engine

    def execute(self, sql, *args, attempt=1, **kwargs):
        try:
            return self.engine.execute(text(sql).execution_options(autocommit=False), *args, **kwargs)
        except exc.OperationalError as err:
            if attempt > 2: raise err
            self._engine = None
            return self.execute(sql, *args, attempt=attempt+1, **kwargs)

    def read_sql_query(self, sql):
        return pd.read_sql_query(sql, self.engine)


class Oracle(DBApi):
    pass
