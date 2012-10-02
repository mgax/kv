import unittest
import sqlite3


class KV(object):

    def __init__(self):
        self._db = sqlite3.connect(':memory:')
        self._execute('CREATE TABLE data (key TEXT PRIMARY KEY, value TEXT)')

    def _execute(self, *args):
        return self._db.cursor().execute(*args)

    def __len__(self):
        return 0

    def __getitem__(self, key):
        for row in self._execute('SELECT value FROM data WHERE key=?', (key,)):
            return row[0]
        else:
            raise KeyError

    def get(self, key, fallback=None):
        return fallback

    def __setitem__(self, key, value):
        self._execute('INSERT INTO data VALUES (?, ?)', (key, value))


class KVTest(unittest.TestCase):

    def test_new_kv_is_empty(self):
        self.assertEqual(len(KV()), 0)

    def test_get_missing_value_raises_key_error(self):
        with self.assertRaises(KeyError):
            KV()['missing']

    def test_get_missing_value_returns_default(self):
        self.assertIsNone(KV().get('missing'))

    def test_get_missing_value_with_default_returns_argument(self):
        fallback = object()
        self.assertEqual(KV().get('missing', fallback), fallback)

    def test_set_item_is_saved(self):
        kv = KV()
        kv['a'] = 'b'
        self.assertEqual(kv['a'], 'b')
