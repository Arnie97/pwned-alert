#!/usr/bin/env python3

import os
import itertools
import json
import requests
from typing import Tuple, Iterable

API = 'https://api.github.com'
HEADERS = {
    'Authorization': 'token ' + os.environ.get('GITHUB_TOKEN', ''),
    'Accept': 'application/vnd.github.v3.text-match+json',
}


def test_login(*auth: Tuple[str, str]) -> bool:
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
