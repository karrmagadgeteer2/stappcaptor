"""Streamlit app for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import os

import pandas as pd
import streamlit as st

from graphql_client import GraphqlClient

APP_NAME = os.environ.get("STREAMLIT_APP_NAME")
if APP_NAME:
    ENV = "cloud"
    REDIRECT_URI = f"https://{APP_NAME}.streamlit.app"
else:
    ENV = "local"
    REDIRECT_URI = "http://localhost:5678"

st.set_page_config(page_title="Captor GraphQL Explorer", layout="wide")
st.title("🔍 Captor GraphQL Explorer")

if "gql" not in st.session_state:
    st.session_state.gql = GraphqlClient()
gql = st.session_state.gql

token = st.session_state.get("token")

if not token:
    st.warning("🔐 Authentication required to access Captor’s GraphQL API.")

    if ENV == "local":
        if st.button("🔑 Log in via browser (Local)"):
            with st.spinner("Opening browser and waiting for callback…"):
                try:
                    gql.login()
                    st.session_state["just_authenticated"] = True
                except Exception as e:  # noqa: BLE001
                    st.error(f"Login failed: {e}")
        st.stop()

    else:
        auth_url = gql.get_auth_url(redirect_uri=REDIRECT_URI)
        st.markdown(
            f'<a href="{auth_url}" target="_blank" rel="noopener">'
            "🔑 Click here to log in (Cloud)" + "</a>",
            unsafe_allow_html=True,
        )
        if st.button("✅ I completed login, proceed"):
            params = st.experimental_get_query_params()
            token_list = params.get("api_key") or params.get("token")
            if token_list:
                token_value = token_list[0]
                st.session_state["token"] = token_value
                st.session_state["just_authenticated"] = True
            else:
                st.error("No token found in URL. Did you finish logging in?")
            st.stop()

if st.session_state.pop("just_authenticated", False):
    st.success("👍 Authentication successful!")

st.success("You’re now logged in and can run queries below.")

st.subheader("Query Parties")
party_name = st.text_input("Party name", "Captor Iris Bond")

if st.button("Fetch Parties"):
    with st.spinner("⏳ Fetching data…"):
        graphql = """
        query parties($nameIn: [String!]) {
          parties(filter: {nameIn: $nameIn}) {
            longName
            legalEntityIdentifier
          }
        }
        """
        data, error = gql.query(
            query_string=graphql,
            variables={"nameIn": [party_name]},
        )

    if error:
        st.error(f"❗ GraphQL Error: {error}")
    elif not data or not data.get("parties"):
        st.warning("⚠️ No parties found for that name.")
    else:
        df = pd.DataFrame(data["parties"])
        st.dataframe(df, use_container_width=True)
        st.balloons()
