import sqlite3
from collections import MutableMapping


class KV(MutableMapping):

    def __init__(self, **kwargs):
        self._db = sqlite3.connect(':memory:')
        self._execute('CREATE TABLE data (key TEXT PRIMARY KEY, value TEXT)')
        self.update(kwargs)

    def _execute(self, *args):
        return self._db.cursor().execute(*args)

    def __len__(self):
        [[n]] = self._execute('SELECT COUNT(*) FROM data')
        return n

    def __getitem__(self, key):
        for row in self._execute('SELECT value FROM data WHERE key=?', (key,)):
            return row[0]
        else:
            raise KeyError

    def __iter__(self):
        return (key for [key] in self._execute('SELECT key FROM data'))

    def __setitem__(self, key, value):
        try:
            self._execute('INSERT INTO data VALUES (?, ?)', (key, value))
        except sqlite3.IntegrityError:
            self._execute('UPDATE data SET value=? WHERE key=?', (value, key))

    def __delitem__(self, key):
        if key in self:
            self._execute('DELETE FROM data WHERE key=?', (key,))
        else:
            raise KeyError
