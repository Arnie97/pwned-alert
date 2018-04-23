#!/usr/bin/env python3

import os
import json
import requests
from typing import Tuple

API = 'https://api.github.com'
TOKEN = {'Authorization': 'token ' + os.environ.get('GITHUB_TOKEN', '')}


def test_login(*auth: Tuple[str, str]) -> bool:
    'Try to login with the username and password.'
    r = requests.get(API, auth=auth)
    return r.status_code == 200


def search_code(keywords: str) -> dict:
    'Search across all the public repositories.'
    r = requests.get(API + '/search/code', dict(q=keywords), headers=TOKEN)
    return json.loads(r.text)
