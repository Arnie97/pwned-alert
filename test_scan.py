import json
import random
from unittest import mock
from nose.tools import assert_equal, make_decorator

import scan


def func(test_case):
    'Provide a shortcut for the corresponding function.'
    f = getattr(scan, test_case.__name__.replace('test_', ''))
    return make_decorator(test_case)(lambda: test_case(f))


@func
@mock.patch('scan.requests.get')
def test_search_code(f, http_mock):
    PAGES, ITEMS = 5, 30

    values = [
        {'items': [random.random() for i in range(ITEMS)]}
        for j in range(PAGES)
    ]
    empty = {'items': []}

    response_mock = lambda: json.dumps(values.pop(0) if values else empty)
    http_mock.side_effect = lambda *_, **__: mock.Mock(text=response_mock())

    expect = sum((d['items'] for d in values), [])
    assert_equal(list(f('')), expect)
    assert_equal(http_mock.call_count, PAGES + 1)


@func
def test_find_php_constants(f):
    code = '''
        // define ('DB_PASSWORD','');
        define( 'DB_HOST', 'localhost' );
        #define DB_PASSWORD "test"
        define("DB_NAME",'admin');
        defined('DB_USERNAME') or define('DB_USERNAME', 'vagrant');
    '''
    expect = [
        ('DB_PASSWORD', ''),
        ('DB_HOST', 'localhost'),
        ('DB_NAME', 'admin'),
        ('DB_USERNAME', 'vagrant'),
    ]
    assert_equal(list(f(code)), expect)


@func
@mock.patch('scan.find_php_constants')
def test_find_php_db_password(f, constants_mock):
    constants_mock.return_value = [
        ('PASSWORD', ''),
        ('PASSWORD', 'local'),
        ('HOSTNAME', 'localhost'),
        ('PASSWORD', 'localhost-8080.com'),
        ('PASSWORD', 'correct'),
    ]
    assert_equal(f(''), 'correct')
