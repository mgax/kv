import unittest
import sqlite3


class KV(object):

    def __init__(self, **kwargs):
        self._db = sqlite3.connect(':memory:')
        self._execute('CREATE TABLE data (key TEXT PRIMARY KEY, value TEXT)')
        for k in kwargs:
            self[k] = kwargs[k]

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

    def get(self, key, fallback=None):
        try:
            return self[key]
        except KeyError:
            return fallback

    def __contains__(self, key):
        [[n]] =  self._execute('SELECT COUNT(*) FROM data WHERE key=?', (key,))
        return bool(n)

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


class KVTest(unittest.TestCase):

    def test_new_kv_is_empty(self):
        self.assertEqual(len(KV()), 0)

    def test_kv_with_two_items_has_size_two(self):
        kv = KV()
        kv['a'] = 'x'
        kv['b'] = 'x'
        self.assertEqual(len(kv), 2)

    def test_get_missing_value_raises_key_error(self):
        with self.assertRaises(KeyError):
            KV()['missing']

    def test_get_missing_value_returns_default(self):
        self.assertIsNone(KV().get('missing'))

    def test_get_missing_value_with_default_returns_argument(self):
        fallback = object()
        self.assertEqual(KV().get('missing', fallback), fallback)

    def test_contains_missing_value_is_false(self):
        self.assertFalse('missing' in KV())

    def test_contains_existing_value_is_true(self):
        kv = KV()
        kv['a'] = 'b'
        self.assertTrue('a' in kv)

    def test_saved_item_is_retrieved_via_getitem(self):
        kv = KV()
        kv['a'] = 'b'
        self.assertEqual(kv['a'], 'b')

    def test_saved_item_is_retrieved_via_get(self):
        kv = KV()
        kv['a'] = 'b'
        self.assertEqual(kv.get('a'), 'b')

    def test_updated_item_is_retrieved_via_getitem(self):
        kv = KV()
        kv['a'] = 'b'
        kv['a'] = 'c'
        self.assertEqual(kv['a'], 'c')

    def test_constructor_kwargs_retrieved_via_getitem(self):
        kv = KV(a='b')
        self.assertEqual(kv['a'], 'b')

    def test_delete_missing_item_raises_key_error(self):
        kv = KV()
        with self.assertRaises(KeyError):
            del kv['missing']

    def test_get_deleted_item_raises_key_error(self):
        kv = KV()
        kv['a'] = 'b'
        del kv['a']
        with self.assertRaises(KeyError):
            kv['a']

    def test_iter_yields_keys(self):
        kv = KV()
        kv['a'] = 'x'
        kv['b'] = 'x'
        kv['c'] = 'x'
        self.assertItemsEqual(kv, ['a', 'b', 'c'])
