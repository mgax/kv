import unittest


class KV(object):

    def __len__(self):
        return 0

    def __getitem__(self, key):
        raise KeyError

    def get(self, key):
        return None


class KVTest(unittest.TestCase):

    def test_new_kv_is_empty(self):
        self.assertEqual(len(KV()), 0)

    def test_get_missing_value_raises_key_error(self):
        with self.assertRaises(KeyError):
            KV()['missing']

    def test_get_missing_value_returns_default(self):
        self.assertIsNone(KV().get('missing'))
