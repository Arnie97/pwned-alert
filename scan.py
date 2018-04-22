#!/usr/bin/env python3

import json
import requests
from typing import Tuple

API = 'https://api.github.com'


def test_login(*auth: Tuple[str, str]) -> bool:
    'Try to login with the username and password.'
    r = requests.get(API + '/user', auth=auth)
    return r.status_code == 200


def search_code(keywords: str) -> dict:
    'Search across all the public repositories.'
    r = requests.get(API + '/search/code', dict(q=keywords))
    return json.loads(r.text)
