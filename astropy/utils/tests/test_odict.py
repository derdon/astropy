# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test the Python 2.6 backport of OrderedDict.

Modified the Python 2.7 Lib/test/test_collections.py to test only
OrderedDict and slightly customized (and renamed) the modules
test_support.py and mapping_tests.py that provide support for those
tests.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ...extern import six

import inspect
import unittest
import pickle
import copy
from random import shuffle

from . import odict_mapping as mapping_tests
from ..compat.odict import OrderedDict
from ...tests.helper import pytest

#Skips all of these tests if the builtin ordered dict is available
pytestmark = pytest.mark.skipif(str("sys.version_info >= (2,7)"))


class TestOrderedDict(unittest.TestCase):

    def test_init(self):

        try:
            OrderedDict([('a', 1), ('b', 2)], None)                                 # too many args
            assert False
        except TypeError:
            pass
        else:
            assert False

        pairs = [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5)]
        self.assertEqual(sorted(OrderedDict(dict(pairs)).items()), pairs)           # dict input
        self.assertEqual(sorted(OrderedDict(**dict(pairs)).items()), pairs)         # kwds input
        self.assertEqual(list(OrderedDict(pairs).items()), pairs)                   # pairs input
        self.assertEqual(list(OrderedDict([('a', 1), ('b', 2), ('c', 9), ('d', 4)],
                                          c=3, e=5).items()), pairs)                # mixed input

        # make sure no positional args conflict with possible kwdargs
        self.assertEqual(inspect.getargspec(OrderedDict.__dict__['__init__']).args,
                         ['self'])

        # Make sure that direct calls to __init__ do not clear previous contents
        d = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 44), ('e', 55)])
        d.__init__([('e', 5), ('f', 6)], g=7, d=4)
        self.assertEqual(list(d.items()),
            [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5), ('f', 6), ('g', 7)])

    def test_update(self):

        try:
            OrderedDict().update([('a', 1), ('b', 2)], None)                        # too many args
            assert False
        except TypeError:
            pass
        else:
            assert False

        pairs = [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5)]
        od = OrderedDict()
        od.update(dict(pairs))
        self.assertEqual(sorted(od.items()), pairs)                                 # dict input
        od = OrderedDict()
        od.update(**dict(pairs))
        self.assertEqual(sorted(od.items()), pairs)                                 # kwds input
        od = OrderedDict()
        od.update(pairs)
        self.assertEqual(list(od.items()), pairs)                                   # pairs input
        od = OrderedDict()
        od.update([('a', 1), ('b', 2), ('c', 9), ('d', 4)], c=3, e=5)
        self.assertEqual(list(od.items()), pairs)                                   # mixed input

        # Make sure that direct calls to update do not clear previous contents
        # add that updates items are not moved to the end
        d = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 44), ('e', 55)])
        d.update([('e', 5), ('f', 6)], g=7, d=4)
        self.assertEqual(list(d.items()),
            [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5), ('f', 6), ('g', 7)])

    def test_clear(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        shuffle(pairs)
        od = OrderedDict(pairs)
        self.assertEqual(len(od), len(pairs))
        od.clear()
        self.assertEqual(len(od), 0)

    def test_delitem(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        od = OrderedDict(pairs)
        del od['a']
        self.assertNotIn('a', od)

        try:
            del od['a']
            assert False
        except KeyError:
            pass
        else:
            assert False

        self.assertEqual(list(od.items()), pairs[:2] + pairs[3:])

    def test_setitem(self):
        od = OrderedDict([('d', 1), ('b', 2), ('c', 3), ('a', 4), ('e', 5)])
        od['c'] = 10           # existing element
        od['f'] = 20           # new element
        self.assertEqual(list(od.items()),
                         [('d', 1), ('b', 2), ('c', 10), ('a', 4), ('e', 5), ('f', 20)])

    def test_iterators(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        shuffle(pairs)
        od = OrderedDict(pairs)
        self.assertEqual(list(od), [t[0] for t in pairs])
        self.assertEqual(od.keys()[:], [t[0] for t in pairs])
        self.assertEqual(od.values()[:], [t[1] for t in pairs])
        self.assertEqual(od.items()[:], pairs)
        self.assertEqual(list(six.iterkeys(od)), [t[0] for t in pairs])
        self.assertEqual(list(six.itervalues(od)), [t[1] for t in pairs])
        self.assertEqual(list(six.iteritems(od)), pairs)
        self.assertEqual(list(reversed(od)),
                         [t[0] for t in reversed(pairs)])

    def test_popitem(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        shuffle(pairs)
        od = OrderedDict(pairs)
        while pairs:
            self.assertEqual(od.popitem(), pairs.pop())

        try:
            od.popitem()
            assert False
        except:
            pass
        else:
            assert False

        self.assertEqual(len(od), 0)

    def test_pop(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        shuffle(pairs)
        od = OrderedDict(pairs)
        shuffle(pairs)
        while pairs:
            k, v = pairs.pop()
            self.assertEqual(od.pop(k), v)

        try:
            od.pop('xyz')
            assert False
        except KeyError:
            pass
        else:
            assert False

        self.assertEqual(len(od), 0)
        self.assertEqual(od.pop(k, 12345), 12345)

    def test_equality(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        shuffle(pairs)
        od1 = OrderedDict(pairs)
        od2 = OrderedDict(pairs)
        self.assertEqual(od1, od2)          # same order implies equality
        pairs = pairs[2:] + pairs[:2]
        od2 = OrderedDict(pairs)
        self.assertNotEqual(od1, od2)       # different order implies inequality
        # comparison to regular dict is not order sensitive
        self.assertEqual(od1, dict(od2))
        self.assertEqual(dict(od2), od1)
        # different length implied inequality
        self.assertNotEqual(od1, OrderedDict(pairs[:-1]))

    def test_copying(self):
        # Check that ordered dicts are copyable, deepcopyable, picklable,
        # and have a repr/eval round-trip
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        od = OrderedDict(pairs)
        update_test = OrderedDict()
        update_test.update(od)
        for i, dup in enumerate([
                    od.copy(),
                    copy.copy(od),
                    copy.deepcopy(od),
                    pickle.loads(pickle.dumps(od, 0)),
                    pickle.loads(pickle.dumps(od, 1)),
                    pickle.loads(pickle.dumps(od, 2)),
                    pickle.loads(pickle.dumps(od, -1)),
                    eval(repr(od)),
                    update_test,
                    OrderedDict(od),
                    ]):
            self.assertTrue(dup is not od)
            self.assertEquals(dup, od)
            self.assertEquals(list(dup.items()), list(od.items()))
            self.assertEquals(len(dup), len(od))
            self.assertEquals(type(dup), type(od))

    def test_yaml_linkage(self):
        # Verify that __reduce__ is setup in a way that supports PyYAML's dump() feature.
        # In yaml, lists are native but tuples are not.
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        od = OrderedDict(pairs)
        # yaml.dump(od) -->
        # '!!python/object/apply:__main__.OrderedDict\n- - [a, 1]\n  - [b, 2]\n'
        self.assertTrue(all(type(pair)==list for pair in od.__reduce__()[1]))

    def test_reduce_not_too_fat(self):
        # do not save instance dictionary if not needed
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        od = OrderedDict(pairs)
        self.assertEqual(len(od.__reduce__()), 2)
        od.x = 10
        self.assertEqual(len(od.__reduce__()), 3)

    def test_repr(self):
        od = OrderedDict([('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)])
        self.assertEqual(repr(od),
            "OrderedDict([(u'c', 1), (u'b', 2), (u'a', 3), (u'd', 4), (u'e', 5), (u'f', 6)])")
        self.assertEqual(eval(repr(od)), od)
        self.assertEqual(repr(OrderedDict()), "OrderedDict()")

    def test_setdefault(self):
        pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
        shuffle(pairs)
        od = OrderedDict(pairs)
        pair_order = list(od.items())
        self.assertEqual(od.setdefault('a', 10), 3)
        # make sure order didn't change
        self.assertEqual(list(od.items()), pair_order)
        self.assertEqual(od.setdefault('x', 10), 10)
        # make sure 'x' is added to the end
        self.assertEqual(list(od.items())[-1], ('x', 10))

    def test_reinsert(self):
        # Given insert a, insert b, delete a, re-insert a,
        # verify that a is now later than b.
        od = OrderedDict()
        od['a'] = 1
        od['b'] = 2
        del od['a']
        od['a'] = 1
        self.assertEqual(list(od.items()), [('b', 2), ('a', 1)])

    def assertIn(self, key, d):
        self.assertTrue(key in d)

    def assertNotIn(self, key, d):
        self.assertFalse(key in d)

class GeneralMappingTests(mapping_tests.BasicTestMappingProtocol):
    type2test = OrderedDict

    def test_popitem(self):
        d = self._empty_mapping()
        self.assertRaises(KeyError, d.popitem)


class MyOrderedDict(OrderedDict):
    pass


class SubclassMappingTests(mapping_tests.BasicTestMappingProtocol):
    type2test = MyOrderedDict

    def test_popitem(self):
        d = self._empty_mapping()
        self.assertRaises(KeyError, d.popitem)
