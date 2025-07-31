"""Navigation page for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import streamlit as st

# Define the pages
main_page = st.Page("mainpage.py", title="Main Page", icon="🎈")
page_2 = st.Page("page_two.py", title="Page 2", icon="❄️")
page_3 = st.Page("page_three.py", title="Page 3", icon="🎉")

# Set up navigation
pg = st.navigation([main_page, page_2, page_3])

# Run the selected page
pg.run()
