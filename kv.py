import sqlite3
from collections import MutableMapping
from contextlib import contextmanager
try:
    import simplejson as json
except ImportError:
    import json


class KV(MutableMapping):

    def __init__(self, db_uri=':memory:', timeout=5):
        self._db = sqlite3.connect(db_uri, timeout=timeout)
        self._db.isolation_level = None
        self._execute('CREATE TABLE IF NOT EXISTS data '
                      '(key PRIMARY KEY, value)')
        self._locks = 0

    def _execute(self, *args):
        return self._db.cursor().execute(*args)

    def __len__(self):
        [[n]] = self._execute('SELECT COUNT(*) FROM data')
        return n

    def __getitem__(self, key):
        if key is None:
            q = ('SELECT value FROM data WHERE key is NULL', ())
        else:
            q = ('SELECT value FROM data WHERE key=?', (key,))
        for row in self._execute(*q):
            return json.loads(row[0])
        else:
            raise KeyError

    def __iter__(self):
        return (key for [key] in self._execute('SELECT key FROM data'))

    def __setitem__(self, key, value):
        jvalue = json.dumps(value)
        with self.lock():
            try:
                self._execute('INSERT INTO data VALUES (?, ?)',
                              (key, jvalue))
            except sqlite3.IntegrityError:
                self._execute('UPDATE data SET value=? WHERE key=?',
                              (jvalue, key))

    def __delitem__(self, key):
        if key in self:
            self._execute('DELETE FROM data WHERE key=?', (key,))
        else:
            raise KeyError

    @contextmanager
    def lock(self):
        if not self._locks:
            self._execute('BEGIN IMMEDIATE TRANSACTION')
        self._locks += 1
        try:
            yield
        finally:
            self._locks -= 1
            if not self._locks:
                self._execute('COMMIT')
