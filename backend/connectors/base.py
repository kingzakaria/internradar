"""Base classes for every connector (API client, spider...)."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common.config import settings
from common.schemas import Offer


class HttpClient:
    """Polite HTTP client: identifies itself, retries, and waits between requests."""

    def __init__(
        self,
        user_agent: str | None = None,
        timeout: float | None = None,
        min_interval: float | None = None,
    ) -> None:
        self.timeout = timeout if timeout is not None else settings.request_timeout
        self.min_interval = (
            min_interval if min_interval is not None else settings.min_request_interval
        )
        self._last_request = 0.0
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent or settings.user_agent
        retry = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def get(self, url: str, **kwargs) -> requests.Response:
        wait = self.min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.get(url, **kwargs)
        self._last_request = time.monotonic()
        response.raise_for_status()
        return response


class BaseConnector(ABC):
    """A connector turns one source into a stream of standard `Offer` objects."""

    name: str = "base"

    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()

    @abstractmethod
    def fetch(self) -> Iterator[Offer]:
        """Yield offers from the source. Must never crash on a single bad offer."""