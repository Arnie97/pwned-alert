import json
import requests
from typing import Tuple

from scan import validate_login, API


class GitHub:
    'API for GitHub social activities.'

    def __init__(self, *auth: Tuple[str, str]):
        'Validate the credentials.'
        assert validate_login(*auth), 'Invalid credentials'
        self.session = requests.Session()
        self.session.auth = tuple(s.encode('utf-8') for s in auth)

    def put(self, endpoint, *args, **kwargs):
        'Shortcut for the API.'
        return self.session.put(API + endpoint, *args, **kwargs)

    def follow(self, username):
        'Follow a user.'
        url = '/user/following/{username}'.format(**vars())
        return self.put(url)

    def star(self, owner, repo):
        'Star a repository.'
        url = '/user/starred/{owner}/{repo}'.format(**vars())
        return self.put(url)

    def subscribe(self, owner, repo, no):
        'Subscribe to an issue.'
        issue_id = self.issue_id(owner, repo, no)
        url = '/notifications/threads/{issue_id}/subscription'.format(**vars())
        return self.put(url)

    def issue_id(self, owner, repo, no) -> int:
        'Get the thread ID for an issue.'
        url = '/repos/{owner}/{repo}/issues/{no}'.format(**vars())
        issue = json.loads(self.session.get(API + url).text)
        return issue['id']
