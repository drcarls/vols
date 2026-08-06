import json
import os
import sys

import pytest

# Make the src/ package importable without an install step.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture
def sru_xml() -> str:
    return _read("sru_response.xml")


@pytest.fixture
def alto_xml() -> str:
    return _read("alto_sample.xml")


@pytest.fixture
def iiif_info() -> dict:
    return json.loads(_read("iiif_info.json"))


class FakeClient:
    """A stand-in HttpClient that serves canned responses by URL substring.

    Records every requested URL in ``.calls`` for assertions.
    """

    def __init__(self, *, text_routes=None, json_routes=None, bytes_routes=None):
        self.text_routes = text_routes or {}
        self.json_routes = json_routes or {}
        self.bytes_routes = bytes_routes or {}
        self.calls = []

    def _match(self, url, routes):
        self.calls.append(url)
        for needle, value in routes.items():
            if needle in url:
                return value
        raise AssertionError(f"no fake route for {url!r}")

    def get_text(self, url, params=None):
        # Fold params into the URL so routes can match on them.
        if params:
            url = url + "?" + "&".join(f"{k}={v}" for k, v in params.items())
        return self._match(url, self.text_routes)

    def get_json(self, url, params=None):
        return self._match(url, self.json_routes)

    def get_bytes(self, url, params=None):
        return self._match(url, self.bytes_routes)


@pytest.fixture
def fake_client_factory():
    def make(**kwargs):
        return FakeClient(**kwargs)

    return make
