from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "rie/1.0 (github.com/violhex/rie)"
RETRY_STATUS_CODES: frozenset[int] = frozenset({500, 502, 503, 504})


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        status_forcelist=list(RETRY_STATUS_CODES),
        backoff_factor=1.5,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = USER_AGENT
    return session
