import sqlite3
import tempfile
import unittest
from copy import deepcopy
from threading import Thread

import mock
from path import path

import kv

try:
    from queue import Queue
except ImportError:
    from Queue import Queue


class KVTest(unittest.TestCase):

    def setUp(self):
        self.kv = kv.KV()

    def assertCountEqual(self, *args, **kwargs):
        try:
            meth = super(KVTest, self).assertCountEqual
        except AttributeError:
            meth = self.assertItemsEqual
        meth(*args, **kwargs)

    def test_new_kv_is_empty(self):
        self.assertEqual(len(self.kv), 0)

    def test_kv_with_two_items_has_size_two(self):
        self.kv['a'] = 'x'
        self.kv['b'] = 'x'
        self.assertEqual(len(self.kv), 2)

    def test_get_missing_value_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.kv['missing']

    def test_get_missing_value_returns_default(self):
        self.assertIsNone(self.kv.get('missing'))

    def test_get_missing_value_with_default_returns_argument(self):
        fallback = object()
        self.assertEqual(self.kv.get('missing', fallback), fallback)

    def test_contains_missing_value_is_false(self):
        self.assertFalse('missing' in self.kv)

    def test_contains_existing_value_is_true(self):
        self.kv['a'] = 'b'
        self.assertTrue('a' in self.kv)

    def test_saved_item_is_retrieved_via_getitem(self):
        self.kv['a'] = 'b'
        self.assertEqual(self.kv['a'], 'b')

    def test_saved_item_is_retrieved_via_get(self):
        self.kv['a'] = 'b'
        self.assertEqual(self.kv.get('a'), 'b')

    def test_updated_item_is_retrieved_via_getitem(self):
        self.kv['a'] = 'b'
        self.kv['a'] = 'c'
        self.assertEqual(self.kv['a'], 'c')

    def test_udpate_with_dictionary_items_retrieved_via_getitem(self):
        self.kv.update({'a': 'b'})
        self.assertEqual(self.kv['a'], 'b')

    def test_delete_missing_item_raises_key_error(self):
        with self.assertRaises(KeyError):
            del self.kv['missing']

    def test_get_deleted_item_raises_key_error(self):
        self.kv['a'] = 'b'
        del self.kv['a']
        with self.assertRaises(KeyError):
            self.kv['a']

    def test_iter_yields_keys(self):
        self.kv['a'] = 'x'
        self.kv['b'] = 'x'
        self.kv['c'] = 'x'
        self.assertCountEqual(self.kv, ['a', 'b', 'c'])

    def test_value_saved_with_int_key_is_retrieved_with_int_key(self):
        self.kv[13] = 'a'
        self.assertEqual(self.kv[13], 'a')

    def test_value_saved_with_int_key_is_not_retrieved_with_str_key(self):
        self.kv[13] = 'a'
        self.assertIsNone(self.kv.get('13'))

    def test_value_saved_with_str_key_is_not_retrieved_with_int_key(self):
        self.kv['13'] = 'a'
        self.assertIsNone(self.kv.get(13))

    def test_value_saved_at_null_key_is_retrieved(self):
        self.kv[None] = 'a'
        self.assertEqual(self.kv[None], 'a')

    def test_value_saved_with_float_key_is_retrieved_with_float_key(self):
        self.kv[3.14] = 'a'
        self.assertEqual(self.kv[3.14], 'a')

    def test_value_saved_with_unicode_key_is_retrieved(self):
        key = u'\u2022'
        self.kv[key] = 'a'
        self.assertEqual(self.kv[key], 'a')


class KVPersistenceTest(unittest.TestCase):

    def setUp(self):
        self.tmp = path(tempfile.mkdtemp())
        self.addCleanup(self.tmp.rmtree)

    def test_value_saved_by_one_kv_client_is_read_by_another(self):
        kv1 = kv.KV(self.tmp / 'kv.sqlite')
        kv1['a'] = 'b'
        kv2 = kv.KV(self.tmp / 'kv.sqlite')
        self.assertEqual(kv2['a'], 'b')

    def test_deep_structure_is_retrieved_the_same(self):
        value = {'a': ['b', {'c': 123}]}
        kv1 = kv.KV(self.tmp / 'kv.sqlite')
        kv1['a'] = deepcopy(value)
        kv2 = kv.KV(self.tmp / 'kv.sqlite')
        self.assertEqual(kv2['a'], value)

    def test_lock_fails_if_db_already_locked(self):
        db_path = self.tmp / 'kv.sqlite'
        q1 = Queue()
        q2 = Queue()
        kv2 = kv.KV(db_path, timeout=0.1)

        def locker():
            kv1 = kv.KV(db_path)
            with kv1.lock():
                q1.put(None)
                q2.get()
        th = Thread(target=locker)
        th.start()
        try:
            q1.get()
            with self.assertRaises(sqlite3.OperationalError) as cm1:
                with kv2.lock():
                    pass
            self.assertEqual(str(cm1.exception), 'database is locked')
            with self.assertRaises(sqlite3.OperationalError) as cm2:
                kv2['a'] = 'b'
            self.assertEqual(str(cm2.exception), 'database is locked')
        finally:
            q2.put(None)
            th.join()

    def test_lock_during_lock_still_saves_value(self):
        kv1 = kv.KV(self.tmp / 'kv.sqlite')
        with kv1.lock():
            with kv1.lock():
                kv1['a'] = 'b'
        self.assertEqual(kv1['a'], 'b')

    def test_same_database_can_contain_two_namespaces(self):
        kv1 = kv.KV(self.tmp / 'kv.sqlite')
        kv2 = kv.KV(self.tmp / 'kv.sqlite', table='other')
        kv1['a'] = 'b'
        kv2['a'] = 'c'
        self.assertEqual(kv1['a'], 'b')
        self.assertEqual(kv2['a'], 'c')


class CLITest(unittest.TestCase):

    def setUp(self):
        self.tmp = path(tempfile.mkdtemp())
        self.kv_file = str(self.tmp / 'kv.sqlite')
        self.kv = kv.KV(self.kv_file)
        self.addCleanup(self.tmp.rmtree)

    def _run(self, *args):
        with mock.patch('sys.argv', ['kv', self.kv_file] + list(args)):
            with mock.patch('kv.print') as mprint:
                with mock.patch('sys.stderr') as mstderr:
                    mstderr.write = mprint
                    retcode = 0
                    output = ''
                    try:
                        kv.main()
                    except SystemExit as e:
                        retcode = e.code
                    if mprint.called:
                        output = mprint.call_args[0][0]
                    return retcode, output

    def test_get(self):
        assert 'foo' not in self.kv
        self.assertEqual(self._run('get', 'foo'), (1, ''))
        self.kv['foo'] = 'test'
        self.assertEqual(self._run('get', 'foo'), (0, 'test'))

    def test_set(self):
        assert 'foo' not in self.kv
        self.assertEqual(self._run('set', 'foo', 'test'), (0, ''))
        assert 'foo' in self.kv
        self.assertEqual(self.kv['foo'], 'test')

    def test_del(self):
        assert 'foo' not in self.kv
        self.assertEqual(self._run('del', 'foo'), (1, ''))
        self.kv['foo'] = 'test'
        assert 'foo' in self.kv
        self.assertEqual(self._run('del', 'foo'), (0, ''))
        assert 'foo' not in self.kv
