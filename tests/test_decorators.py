# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

from django import http
from django.test import RequestFactory

from tecken.base import decorators


def test_set_request_debug():

    @decorators.set_request_debug
    def myview(request):
        return http.HttpResponse('debug={}'.format(request._request_debug))

    request = RequestFactory().get('/')
    response = myview(request)
    assert response.content == b'debug=False'

    request = RequestFactory(HTTP_DEBUG='true').get('/')
    response = myview(request)
    assert response.content == b'debug=True'

    request = RequestFactory(HTTP_DEBUG='0').get('/')
    response = myview(request)
    assert response.content == b'debug=False'


def test_cache_memoize():

    calls_made = []

    @decorators.cache_memoize(10)
    def runmeonce(a, b, k='bla'):
        calls_made.append((a, b, k))
        return '{} {} {}'.format(a, b, k)  # sample implementation

    runmeonce(1, 2)
    runmeonce(1, 2)
    assert len(calls_made) == 1
    runmeonce(1, 3)
    assert len(calls_made) == 2
    # should work with most basic types
    runmeonce(1.1, 'foo')
    runmeonce(1.1, 'foo')
    assert len(calls_made) == 3
    # even more "advanced" types
    runmeonce(1.1, 'foo', k=list('åäö'))
    runmeonce(1.1, 'foo', k=list('åäö'))
    assert len(calls_made) == 4
    # And shouldn't be a problem even if the arguments are really long
    runmeonce('A' * 200, 'B' * 200, {'C' * 100: 'D' * 100})
    assert len(calls_made) == 5

    # different prefixes
    @decorators.cache_memoize(10, prefix='first')
    def foo(value):
        calls_made.append(value)
        return 'ho'

    @decorators.cache_memoize(10, prefix='second')
    def bar(value):
        calls_made.append(value)
        return 'ho'

    foo('hey')
    bar('hey')
    assert len(calls_made) == 7

    # Test when you don't care about the result
    @decorators.cache_memoize(10, store_result=False, prefix='different')
    def returnnothing(a, b, k='bla'):
        calls_made.append((a, b, k))
        # note it returns None
    returnnothing(1, 2)
    returnnothing(1, 2)
    assert len(calls_made) == 8


def test_cache_memoize_hit_miss_callables():

    hits = []
    misses = []
    calls_made = []

    def hit_callable(arg):
        hits.append(arg)

    def miss_callable(arg):
        misses.append(arg)

    @decorators.cache_memoize(
        10,
        hit_callable=hit_callable,
        miss_callable=miss_callable,
    )
    def runmeonce(arg):
        calls_made.append(arg)
        return arg * 2

    result = runmeonce(100)
    assert result == 200
    assert len(calls_made) == 1
    assert len(hits) == 0
    assert len(misses) == 1

    result = runmeonce(100)
    assert result == 200
    assert len(calls_made) == 1
    assert len(hits) == 1
    assert len(misses) == 1

    result = runmeonce(100)
    assert result == 200
    assert len(calls_made) == 1
    assert len(hits) == 2
    assert len(misses) == 1

    result = runmeonce(200)
    assert result == 400
    assert len(calls_made) == 2
    assert len(hits) == 2
    assert len(misses) == 2


def test_cache_memoize_refresh():

    calls_made = []

    @decorators.cache_memoize(10)
    def runmeonce(a):
        calls_made.append(a)
        return a * 2

    runmeonce(10)
    assert len(calls_made) == 1
    runmeonce(10)
    assert len(calls_made) == 1
    runmeonce(10, _refresh=True)
    assert len(calls_made) == 2


def test_cache_memoize_different_functions_same_arguments():

    calls_made_1 = []
    calls_made_2 = []

    @decorators.cache_memoize(10)
    def function_1(a):
        calls_made_1.append(a)
        return a * 2

    @decorators.cache_memoize(10)
    def function_2(a):
        calls_made_2.append(a)
        return a * 3

    assert function_1(100) == 200
    assert len(calls_made_1) == 1

    assert function_1(100) == 200
    assert len(calls_made_1) == 1

    # Same arguments but to different function
    assert function_2(100) == 300
    assert len(calls_made_1) == 1
    assert len(calls_made_2) == 1

    assert function_2(100) == 300
    assert len(calls_made_1) == 1
    assert len(calls_made_2) == 1

    assert function_2(1000) == 3000
    assert len(calls_made_1) == 1
    assert len(calls_made_2) == 2

    # If you set the prefix, you can cross wire functions.
    # Note sure why you'd ever want to do this though

    @decorators.cache_memoize(10, prefix=function_2.__name__)
    def function_3(a):
        raise Exception

    assert function_3(100) == 300


def test_set_cors_headers(rf):

    # Happy patch
    @decorators.set_cors_headers()
    def view_function(request):
        return http.HttpResponse('hello world')

    request = rf.get('/')
    response = view_function(request)
    assert response['Access-Control-Allow-Origin'] == '*'
    assert response['Access-Control-Allow-Methods'] == 'GET'

    # Overrides
    @decorators.set_cors_headers(origin='example.com', methods=['HEAD', 'GET'])
    def view_function(request):
        return http.HttpResponse('hello world')
    response = view_function(request)
    assert response['Access-Control-Allow-Origin'] == 'example.com'
    assert response['Access-Control-Allow-Methods'] == 'HEAD,GET'


def test_make_tempdir():

    mutable = []

    @decorators.make_tempdir(
        prefix='PREFIX',
        suffix='SUFFIX',
    )
    def view_function(request, tmpdir, foo=None):
        assert os.path.isdir(tmpdir)
        basename = os.path.basename(tmpdir)
        assert 'PREFIX' in basename
        assert 'SUFFIX' in basename
        mutable.append(tmpdir)

        if foo == 'ERROR':
            raise NameError('anything')

    view_function('somerequest', foo='bar')
    assert not os.path.isdir(mutable[0])

    # Let it fail this time
    with pytest.raises(NameError):
        view_function('somerequest', foo='ERROR')

    assert not os.path.isdir(mutable[1])
