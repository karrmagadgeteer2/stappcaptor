"""Navigation page for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import streamlit as st

st.set_page_config(page_title="Captor Resources", layout="wide")

# 2) inject flexbox CSS so that the last nav‐item (our Logout) sits at the bottom
st.markdown(
    """
    <style>
      /* make the sidebar nav a full-height column */
      [data-testid="stSidebarNav"] nav {
        display: flex;
        flex-direction: column;
        height: 100vh;
      }
      /* push only the very last nav-child (our Logout button wrapper) down */
      [data-testid="stSidebarNav"] nav > div:last-child {
        margin-top: auto;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Define the pages
main_page = st.Page("mainpage.py", title="Main Page", icon="🎈")
page_2 = st.Page("page_two.py", title="Page 2", icon="❄️")
page_3 = st.Page("page_three.py", title="Page 3", icon="🎉")

# Set up navigation
pg = st.navigation([main_page, page_2, page_3])

# 5) a standalone Logout button that will be the last <div> in the nav
#    Use on_click so it doesn’t break the nav’s return value
st.sidebar.button(
    "🔒 Logout",
    on_click=lambda: (st.session_state.pop("token", None), st.rerun()),
)

pg.run()
