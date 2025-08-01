"""Navigation page for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import streamlit as st

st.set_page_config(page_title="Captor Resources", layout="wide")

qp = st.query_params
if "token" in qp and "token" not in st.session_state:
    st.session_state.token = qp["token"][0]

st.markdown(
    """
    <style>
      [data-testid="stSidebarNav"] nav {
        display: flex;
        flex-direction: column;
        height: 100vh;
      }
      [data-testid="stSidebarNav"] nav > div:last-child {
        margin-top: auto;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

main_page = st.Page("mainpage.py", title="Main Page", icon="🎈")
page_2 = st.Page("page_two.py", title="Page 2", icon="❄️")
page_3 = st.Page("page_three.py", title="Page 3", icon="🎉")
pg = st.navigation([main_page, page_2, page_3])


def logout() -> None:
    """Log out routine."""
    for k in ("token", "exp", "user_display_name", "user_id"):
        st.session_state.pop(k, None)
    st.query_params.clear()
    st.rerun()


st.sidebar.button("🔒 Logout", on_click=logout)

pg.run()
