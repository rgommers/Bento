import os
import sys

from unittest \
    import \
        TestCase
from nose.tools \
    import \
        assert_equal, assert_raises

from bento.core.parser.nodes \
    import \
        ast_walk
from bento.core.parser.visitor \
    import \
        Dispatcher
from bento.core.parser.parser \
    import \
        parse as _parse

def parse(data):
    p = _parse(data)
    dispatcher = Dispatcher()
    return ast_walk(p, dispatcher)

def _test_functional(root):
    d = os.path.abspath(os.path.dirname(__file__))
    info = os.path.join(d, root + ".info")

    tested = parse(open(info).read())
    sys.path.insert(0, d)
    try:
        mod = __import__(root)
        assert_equal(tested, mod.ref, "divergence for %s" % info)
    finally:
        sys.path.pop(0)

def test_sphinx():
    _test_functional("sphinx")

def test_jinja2():
    _test_functional("jinja2")
