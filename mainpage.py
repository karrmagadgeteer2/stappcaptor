"""Main page for Captor marketing site.

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


# Initialize session state variables
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user_display_name = None
    st.session_state.user_id = None
    st.session_state.exp = None

st.markdown("# Main page 🎈")
st.sidebar.markdown("# Main page 🎈")

timeout = 10

# Check if token is valid (not expired)
valid_token = (
    st.session_state.token is not None
    and st.session_state.exp is not None
    and time.time() < st.session_state.exp
)

# Use a container for the login form
login_container = st.container()
if not valid_token:
    with login_container:
        st.write("**Please login to continue**")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")  # Masked input
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
                        "Content-Type": ("application/x-www-form-urlencoded"),
                    }
                    try:
                        response = requests.post(
                            url=url,
                            data=payload,
                            headers=headers,
                            timeout=timeout,
                        )
                        response.raise_for_status()
                    except requests.RequestException as exc:
                        # Shorten line by splitting error message
                        err_msg = (
                            f"Authentication failed: {response.status_code} "
                            f"{response.text}\n{exc!s}"
                        )
                        st.error(err_msg)
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
    st.write(
        "Access token stored in session. "
        "You can now call the Captor API using this token."
    )

st.subheader("Query Funds")
options = {
    "Captor Iris Bond": "SE0009807308",
    "Captor Dahlia Green Bond": "SE0011337195",
    "Captor Scilla Global Equity": "SE0011670843",
    "Captor Aster Global Credit": "SE0015243886",
    "Captor Aster Global Credit Short Term": "SE0017832330",
    "Captor Aster Global High Yield": "SE0017832280",
    "Captor Global Fixed Income": "SE0020999670",
    "Captor Perenne Short Term Bond": "SE0020552602",
}
choice = st.selectbox(
    label="Fund select",
    label_visibility="collapsed",
    options=options,
    index=0,
)

if st.button("Load"):
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
        variables = {"nameIn": [choice]}
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
        df["ISIN code"] = options[choice]
        st.dataframe(df, use_container_width=True)
        st.balloons()
