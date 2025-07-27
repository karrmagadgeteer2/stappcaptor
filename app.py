"""Streamlit app for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import pandas as pd
import streamlit as st

from graphql_client import GraphqlClient

st.set_page_config(page_title="Captor Resources", layout="wide")
st.title("🔍 Captor Resources")

if "gql" not in st.session_state:
    st.session_state.gql = GraphqlClient()
gql = st.session_state.gql

token = st.session_state.get("token")

if not token:
    st.markdown("<meta http-equiv='refresh' content='2'>", unsafe_allow_html=True)
    st.warning("🔐 You must log in to access Captor’s GraphQL API.")

    if st.button("🔑 Log in via browser"):
        with st.spinner(
            "Opening Captor portal... complete it there, then return here.",
        ):
            try:
                gql.login()
                st.session_state["just_authenticated"] = True
            except Exception as e:  # noqa: BLE001
                st.error(f"Login failed: {e}")

    st.stop()

if st.session_state.pop("just_authenticated", False):
    st.success("👍 You are authenticated!")

st.success("You’re now logged in and can run queries below.")

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
        st.balloons()
        df = pd.DataFrame(data["parties"])
        st.dataframe(df, use_container_width=True)
