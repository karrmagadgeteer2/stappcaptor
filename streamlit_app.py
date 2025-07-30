"""Streamlit app for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import pandas as pd
import streamlit as st

from graphql_client import GraphqlClient

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
    st.warning("🔐 Authentication required to access Captor’s GraphQL API.")

    if ENV == "local":
        if st.button("🔑 Log in via browser (Local)"):
            with st.spinner("Opening browser and waiting for callback…"):
                try:
                    token = gql.login()
                    st.session_state["token"] = token
                    st.success("✅ Authenticated successfully!")
                except Exception as e:  # noqa: BLE001
                    st.error(f"Login failed: {e}")
        st.stop()

    else:
        auth_url = gql.get_auth_url(redirect_uri=REDIRECT_URI)
        st.markdown(
            f'<a href="{auth_url}" target="_blank" rel="noopener">'
            "🔑 Log in with Captor Portal (Cloud)"
            "</a>",
            unsafe_allow_html=True,
        )
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
