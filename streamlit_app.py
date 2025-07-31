"""Streamlit app for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import time

import pandas as pd
import requests
import streamlit as st


class GraphqlError(Exception):
    """Raised if the Graphql query returns any error(s)."""


if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user_display_name = None
    st.session_state.user_id = None
    st.session_state.exp = None

st.title("Captor.se API Authentication")

timeout = 10

valid_token = (
    st.session_state.token is not None
    and st.session_state.exp is not None
    and time.time() < st.session_state.exp
)

login_container = st.container()
if not valid_token:
    with login_container:
        st.write("**Please login to continue**")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    url = "https://auth.captor.se/token"
                    payload = {
                        "username": username,
                        "password": password,
                        "client_id": "prod",
                    }
                    headers = {
                        "accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    }
                    try:
                        response = requests.post(
                            url=url, data=payload, headers=headers, timeout=timeout
                        )
                        response.raise_for_status()
                    except requests.RequestException as exc:
                        st.error(
                            f"Authentication failed: {response.status_code} "
                            f"{response.text}\n{exc!s}"
                        )
                    else:
                        data = response.json()
                        st.session_state.token = data.get("access_token")
                        st.session_state.exp = data.get("exp")
                        st.session_state.user_display_name = data.get(
                            "user_display_name"
                        )
                        st.session_state.user_id = data.get("user_id")
                        st.success(
                            f"Authenticated as {st.session_state.user_display_name}"
                        )
                        login_container.empty()

if valid_token:
    st.info(f"Authenticated as {st.session_state.user_display_name}")
    st.write(
        "Access token stored in session. "
        "You can now call the Captor API using this token."
    )

st.subheader("Query Parties")
party_name = st.text_input("Party name", "Captor Iris Bond")

if st.button("Fetch Parties"):
    with st.spinner("⏳ Fetching data…"):
        query = """
        query parties($nameIn: [String!]) {
          parties(filter: {nameIn: $nameIn}) {
            longName
            legalEntityIdentifier
          }
        }
        """
        prefix = ""
        base_url = "captor.se"
        url = f"https://{prefix}api.{base_url}/graphql"
        variables = {"nameIn": [party_name]}
        verify = True
        headers = {
            "Authorization": f"Bearer {st.session_state.token}",
            "accept-encoding": "gzip",
        }
        payload: dict[str, object] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = requests.post(
                url=url,
                json=payload,
                headers=headers,
                verify=verify,
                timeout=timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise GraphqlError(str(exc)) from exc

        result = resp.json()
        data, error = result.get("data"), result.get("errors")

    if error:
        st.error(f"❗ GraphQL Error: {error}")
    elif not data or not data.get("parties"):
        st.warning("⚠️ No parties found for that name.")
    else:
        df = pd.DataFrame(data["parties"])
        st.dataframe(df, use_container_width=True)
        st.balloons()
