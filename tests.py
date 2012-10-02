import unittest


class KV(object):

    def __len__(self):
        return 0


class KVTest(unittest.TestCase):

    def test_new_kv_is_empty(self):
        self.assertEqual(len(KV()), 0)
