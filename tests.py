import unittest
import tempfile
from path import path
from kv import KV


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

    def test_udpate_with_dictionary_items_retrieved_via_getitem(self):
        kv = KV()
        kv.update({'a': 'b'})
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

    def test_value_saved_with_int_key_is_retrieved_with_int_key(self):
        kv = KV()
        kv[13] = 'a'
        self.assertEqual(kv[13], 'a')

    def test_value_saved_with_int_key_is_not_retrieved_with_str_key(self):
        kv = KV()
        kv[13] = 'a'
        self.assertIsNone(kv.get('13'))

    def test_value_saved_with_str_key_is_not_retrieved_with_int_key(self):
        kv = KV()
        kv['13'] = 'a'
        self.assertIsNone(kv.get(13))

    def test_value_saved_at_null_key_is_retrieved(self):
        kv = KV()
        kv[None] = 'a'
        self.assertEqual(kv[None], 'a')

    def test_value_saved_with_float_key_is_retrieved_with_float_key(self):
        kv = KV()
        kv[3.14] = 'a'
        self.assertEqual(kv[3.14], 'a')

    def test_value_saved_with_unicode_key_is_retrieved(self):
        kv = KV()
        key = u'\u2022'
        kv[key] = 'a'
        self.assertEqual(kv[key], 'a')


class KVPersistenceTest(unittest.TestCase):

    def setUp(self):
        self.tmp = path(tempfile.mkdtemp())
        self.addCleanup(self.tmp.rmtree)

    def test_value_saved_by_one_kv_client_is_read_by_another(self):
        kv1 = KV(self.tmp / 'kv.sqlite')
        kv1['a'] = 'b'
        kv2 = KV(self.tmp / 'kv.sqlite')
        self.assertEqual(kv2['a'], 'b')

    def test_deep_structure_is_retrieved_the_same(self):
        from copy import deepcopy
        value = {'a': ['b', {'c': 123}]}
        kv1 = KV(self.tmp / 'kv.sqlite')
        kv1['a'] = deepcopy(value)
        kv2 = KV(self.tmp / 'kv.sqlite')
        self.assertEqual(kv2['a'], value)

    def test_lock_fails_if_db_already_locked(self):
        import sqlite3
        from threading import Thread
        from Queue import Queue
        db_path = self.tmp / 'kv.sqlite'
        q1 = Queue()
        q2 = Queue()
        kv2 = KV(db_path, timeout=0.1)
        def locker():
            kv1 = KV(db_path)
            with kv1.lock():
                q1.put(None)
                q2.get()
        th = Thread(target=locker)
        th.start()
        try:
            q1.get()
            with self.assertRaises(sqlite3.OperationalError) as cm1:
                with kv2.lock(): pass
            self.assertEqual(cm1.exception.message, 'database is locked')
            with self.assertRaises(sqlite3.OperationalError) as cm2:
                kv2['a'] = 'b'
            self.assertEqual(cm2.exception.message, 'database is locked')
        finally:
            q2.put(None)
            th.join()
