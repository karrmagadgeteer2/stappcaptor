"""Module defining the GraphqlClient class and its helper functions.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import json
import socket
import threading
import webbrowser
from logging import WARNING, basicConfig, getLogger
from pathlib import Path
from queue import Queue
from urllib.parse import urlencode

import jwt as pyjwt
import streamlit as st
from requests import RequestException
from requests import post as requests_post
from werkzeug.serving import make_server
from werkzeug.wrappers import Request, Response

basicConfig(level=WARNING)
logger = getLogger(__name__)


class DatabaseChoiceError(Exception):
    """Raised when an invalid database choice is provided."""

    def __init__(
        self,
        message: str = "Can only handle database prod or test.",
    ) -> None:
        """Initialize the DatabaseChoiceError.

        Args:
            message (str): Exception message.
                Defaults to 'Can only handle database prod or test.'.

        """
        self.message = message
        super().__init__(message)


class NoInternetError(Exception):
    """Raised when there is no internet connectivity."""

    def __init__(self, message: str = "No internet connection.") -> None:
        """Initialize the NoInternetError.

        Args:
            message (str): Exception message.
                Defaults to 'No internet connection.'.

        """
        self.message = message
        super().__init__(message)


def check_internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """Check if there is an active internet connection.

    Args:
        host (str): Host to ping. Defaults to "8.8.8.8".
        port (int): Port to use. Defaults to 53.
        timeout (int): Timeout in seconds. Defaults to 3.

    Returns:
        bool: True if internet is available, False otherwise.

    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
    except OSError:
        return False
    else:
        return True


def get_dot_config_file_name(filename: str) -> Path:
    """Get the full path to the config file in the user's home directory.

    Args:
        filename (str): Filename to append to home directory.

    Returns:
        Path: Path object to the config file.

    """
    return Path.home() / filename


def write_token_to_file(jwt_token: str, filename: str) -> None:
    """Write the decoded JWT token to a file.

    Args:
        jwt_token (str): JWT token string.
        filename (str): Target file name to write the token to.

    Raises:
        FileNotFoundError: If the file could not be written.

    """
    dot_config_file_name = get_dot_config_file_name(filename=filename)

    data = pyjwt.decode(jwt=jwt_token, options={"verify_signature": False})
    database = data["aud"]
    if dot_config_file_name.exists():
        with dot_config_file_name.open(mode="r", encoding="utf-8") as file_handle:
            local_token = json.load(fp=file_handle)
        local_token["tokens"][database] = {"token": jwt_token, "decoded": data}
    else:
        local_token = {"tokens": {database: {"token": jwt_token, "decoded": data}}}

    with dot_config_file_name.open(mode="w", encoding="utf-8") as file_handle:
        # noinspection PyTypeChecker
        json.dump(obj=local_token, fp=file_handle, indent=2, sort_keys=True)

    if not dot_config_file_name.exists():
        msg = "Writing token to file failed."
        raise FileNotFoundError(msg)

    logger_message = f"Wrote token to file: {dot_config_file_name}."
    logger.info(logger_message)


def get_token_from_file(database: str, filename: str) -> str:
    """Read the token from a local file.

    Args:
        database (str): Database identifier.
        filename (str): File containing the token.

    Returns:
        str: Token string.

    Raises:
        FileNotFoundError: If the token file doesn't exist.
        DatabaseChoiceError: If the database is not supported.

    """
    dot_config_file_name = get_dot_config_file_name(filename=filename)

    if not dot_config_file_name.exists():
        msg = f"File '{dot_config_file_name}' with token not found"
        raise FileNotFoundError(msg)

    with dot_config_file_name.open(mode="r", encoding="utf-8") as file_handle:
        dot_config = json.load(fp=file_handle)

    try:
        token = dot_config["tokens"][database]["token"]
    except KeyError as exc:
        raise DatabaseChoiceError from exc

    logger_message = "get_token_from_file()"
    logger.info(logger_message)

    return token


def token_get_server(  # pragma: no cover
    database: str,
    base_url: str,
    filename: str,
    port: int = 6789,
) -> str:
    """Start a temporary server to retrieve a token via browser.

    Args:
        database (str): Database name.
        base_url (str): Base URL for the authentication service.
        filename (str): File to store the token.
        port (int): Local server port. Defaults to 6789.

    Returns:
        str: Retrieved token.

    Raises:
        DatabaseChoiceError: If an unsupported database is given.
        NoInternetError: If no internet connection is available.

    """
    logger_message = "token_get_server()"
    logger.info(logger_message)

    if database not in {"prod", "test"}:
        raise DatabaseChoiceError

    if check_internet():
        params = urlencode({"redirect_uri": f"http://localhost:{port}/token"})
        webbrowser.open(
            url=f"https://auth.captor.se/login?{params}",
            new=2,
        )
    else:
        raise NoInternetError

    @Request.application
    def app(request: Request) -> Response:
        """Local HTTP handler to receive the API key from the browser."""
        queue.put(item=request.args.get("token") or request.args.get("api_key"))
        return Response(
            response=""" <!DOCTYPE html>
                         <html lang=\"en-US\">
                             <head>
                                 <script>
                                     setTimeout(function () {
                                         window.close();
                                     }, 2000);
                                 </script>
                             </head>
                             <body>
                                 <p>Writing token to local machine</p>
                             </body>
                         </html> """,
            status=200,
            content_type="text/html; charset=UTF-8",
        )

    queue = Queue()
    server = make_server(host="localhost", port=port, app=app)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    token = queue.get(block=True)
    write_token_to_file(jwt_token=token, filename=filename)
    server.shutdown()
    thread.join()

    return token


class GraphqlError(Exception):
    """Raised if the Graphql query returns any error(s)."""


class GraphqlClient:
    """Streamlit-adapted GraphQL client."""

    def __init__(
        self,
        database: str = "prod",
        base_url: str = "captor.se",
        auth_base_url: str = "auth.captor.se",
    ) -> None:
        """Initialize the GraphqlClient.

        Attempts to load an existing token from Streamlit session state
        or from a local file (~/.streamlit_token). If found, stores it in
        session state for persistence.

        Args:
            database: 'prod' or 'test'
            base_url: e.g. 'captor.se'
        """
        self.database = database
        self.base_url = base_url
        self.auth_base_url = auth_base_url
        prefix = "" if database == "prod" else "test"
        self.url = f"https://{prefix}api.{base_url}/graphql"
        self.tokenfile = ".captor_streamlit"

        # Load token from session or fallback to file
        token = st.session_state.get("token")
        if not token:
            try:
                token = get_token_from_file(database=database, filename=self.tokenfile)
                st.session_state["token"] = token
            except Exception:  # noqa: BLE001
                token = None

        self.token: str | None = token

    def get_auth_url(self, redirect_uri: str) -> str:
        """Construct the URL for redirecting the user to the OAuth login page.

        Args:
            redirect_uri: The URL to which the auth service will redirect
            after successful login.

        Returns:
            The complete authentication URL.
        """
        params = urlencode({"redirect_uri": redirect_uri})
        return f"https://{self.auth_base_url}/login?{params}"

    def login(self) -> str:
        """Start the local HTTP callback flow.

        Returns:
            The raw token string.
        """
        token = token_get_server(
            database=self.database,
            base_url=self.auth_base_url,
            filename=self.tokenfile,
        )
        st.session_state["token"] = token
        self.token = token

        # Decode JWT metadata if possible
        try:
            decoded = pyjwt.decode(jwt=token, options={"verify_signature": False})
            st.session_state["decoded_token"] = decoded
        except pyjwt.DecodeError:
            pass

        return token

    def query(
        self,
        query_string: str,
        variables: dict[str, object] | None = None,
        timeout: int = 10,
        *,
        verify: bool = True,
    ) -> tuple[dict[str, object] | list | None, str | list | None]:
        """Execute a GraphQL query using the current authentication token.

        Args:
            query_string: The GraphQL query text.
            variables: Variables for the query.
            timeout: Request timeout in seconds.
            verify: Whether to verify SSL certificates.

        Returns:
            A tuple where the first element is the data (dict, list, or None)
            and the second element is any errors (str, list, or None).

        Raises:
            GraphqlError: If no token is set or the request fails.
        """
        if not self.token:
            msg = "Authentication token is missing. Please log in."
            raise GraphqlError(msg)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept-encoding": "gzip",
        }
        payload: dict[str, object] = {"query": query_string}
        if variables:
            payload["variables"] = variables

        try:
            resp = requests_post(
                url=self.url,
                json=payload,
                headers=headers,
                verify=verify,
                timeout=timeout,
            )
            resp.raise_for_status()
        except RequestException as exc:
            raise GraphqlError(str(exc)) from exc

        result = resp.json()
        return result.get("data"), result.get("errors")
