import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from requests import HTTPError, RequestException

from graphql_client import GraphqlClient, GraphqlError


def setup_function(_):
    st.session_state.clear()


def test_query_raises_graphql_error_on_http_error():
    st.session_state["token"] = "tok"
    client = GraphqlClient()
    client.token = "tok"
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = HTTPError("boom")
    with patch("graphql_client.requests_post", return_value=mock_resp):
        with pytest.raises(GraphqlError):
            client.query("query { }")


def test_query_raises_graphql_error_on_request_exception():
    st.session_state["token"] = "tok"
    client = GraphqlClient()
    client.token = "tok"
    with patch("graphql_client.requests_post", side_effect=RequestException("fail")):
        with pytest.raises(GraphqlError) as exc_info:
            client.query("query { }")
        assert isinstance(exc_info.value.__cause__, RequestException)


def test_query_success_returns_data():
    st.session_state["token"] = "tok"
    client = GraphqlClient()
    client.token = "tok"
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"data": {"hello": "world"}}
    with patch("graphql_client.requests_post", return_value=mock_resp):
        data, errors = client.query("query { hello }")
    assert data == {"hello": "world"}
    assert errors is None


def test_get_dot_config_file_name(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    from graphql_client import get_dot_config_file_name

    result = get_dot_config_file_name("foo")
    assert result == tmp_path / "foo"


def test_write_and_get_token(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    import graphql_client as gc

    monkeypatch.setattr(gc.pyjwt, "decode", lambda jwt, options: {"aud": "prod"})

    gc.write_token_to_file("jwt-token", "tokfile")
    token = gc.get_token_from_file("prod", "tokfile")
    assert token == "jwt-token"


def test_get_auth_url_and_login(monkeypatch):
    import graphql_client as gc

    monkeypatch.setattr(gc, "token_get_server", lambda **_: "token123")
    monkeypatch.setattr(gc.pyjwt, "decode", lambda jwt, options: {"user": "x"})
    st.session_state.clear()
    client = gc.GraphqlClient(database="test", base_url="example.com")

    auth_url = client.get_auth_url("http://localhost")
    assert auth_url.startswith("https://auth.captor.se/login?")

    token = client.login()
    assert token == "token123"
    assert client.token == "token123"
    assert st.session_state["decoded_token"] == {"user": "x"}


def test_token_get_server(monkeypatch):
    import graphql_client as gc

    class DummyQueue:
        def get(self, block=True):
            return "abc"

        def put(self, item):
            pass

    class DummyServer:
        def serve_forever(self):
            pass

        def shutdown(self):
            pass

    class DummyThread:
        def __init__(self, target):
            self.target = target

        def start(self):
            pass

        def join(self):
            pass

    monkeypatch.setattr(gc, "Queue", DummyQueue)
    monkeypatch.setattr(gc, "make_server", lambda host, port, app: DummyServer())
    monkeypatch.setattr(gc.threading, "Thread", DummyThread)
    monkeypatch.setattr(gc, "check_internet", lambda: True)
    monkeypatch.setattr(gc.webbrowser, "open", lambda **_: None)
    monkeypatch.setattr(gc, "write_token_to_file", lambda jwt_token, filename: None)

    token = gc.token_get_server("prod", "captor.se", "file", port=1234)
    assert token == "abc"


def test_check_internet(monkeypatch):
    import graphql_client as gc

    class DummySocket:
        def __init__(self, raises=False):
            self.raises = raises

        def connect(self, addr):
            if self.raises:
                raise OSError

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(gc.socket, "socket", lambda *a, **k: DummySocket())
    assert gc.check_internet()
    monkeypatch.setattr(gc.socket, "socket", lambda *a, **k: DummySocket(True))
    assert not gc.check_internet()


def test_query_requires_token(monkeypatch):
    client = GraphqlClient()
    client.token = None
    with pytest.raises(GraphqlError):
        client.query("q")
