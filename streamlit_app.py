"""Streamlit app for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import pandas as pd
import streamlit as st

from graphql_client import GraphqlClient, requests_post

ENV = "cloud"
STREAMLIT_APP_NAME = "stappcaptor"

if ENV == "cloud":
    REDIRECT_URI = f"https://{STREAMLIT_APP_NAME}.streamlit.app"
else:
    REDIRECT_URI = "http://localhost:8501"

st.set_page_config(page_title="Captor GraphQL Explorer", layout="wide")
st.title("🔍 Captor GraphQL Explorer")

if "gql" not in st.session_state:
    st.session_state.gql = GraphqlClient()
gql: GraphqlClient = st.session_state.gql

if ENV == "cloud" and "token" not in st.session_state:
    params = st.experimental_get_query_params()
    tok = (params.get("api_key") or params.get("token") or [None])[0]
    if tok:
        st.session_state["token"] = tok
        st.experimental_set_query_params()
        st.success("✅ Token captured from URL — you’re authenticated!")

if "token" not in st.session_state:
    st.warning("🔐 Enter your Captor credentials to obtain an API token.")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        with st.spinner("🔄 Requesting token…"):
            try:
                data = {
                    "username": username,
                    "password": password,
                    "client_id": gql.database,
                }
                headers = {
                    "accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                resp = requests_post(
                    url=f"https://{gql.auth_base_url}/token",
                    data=data,
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Login failed: {exc}")
                st.stop()

        result = resp.json()
        st.session_state["token"] = result.get("access_token")
        st.session_state["token_response"] = result
        gql.token = result.get("access_token")
        st.success("✅ Token retrieved!")
        st.json(result)
        st.stop()

if st.session_state.pop("just_authenticated", False):
    st.success("👍 You’re authenticated!")

st.success("You’re now logged in and can run GraphQL queries below.")

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
        data, error = gql.query(query_string=query, variables={"nameIn": [party_name]})

    if error:
        st.error(f"❗ GraphQL Error: {error}")
    elif not data or not data.get("parties"):
        st.warning("⚠️ No parties found for that name.")
    else:
        df = pd.DataFrame(data["parties"])
        st.dataframe(df, use_container_width=True)
        st.balloons()
