"""Page two for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import plotly.graph_objects as go
import streamlit as st
from openseries import load_plotly_dict

figdict, _ = load_plotly_dict()


def make_scatter() -> go.Figure:
    """Sample line+scatter."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[1, 2, 3, 4, 5],
            y=[10, 15, 13, 17, 14],
            mode="lines+markers",
            name="Line + Scatter",
        )
    )
    fig.update_layout(figdict.get("layout"))
    fig.update_layout(title="Line & Scatter Plot")
    return fig


def make_bar() -> go.Figure:
    """Sample bar chart."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=["A", "B", "C", "D"], y=[20, 14, 23, 25], name="Bar Values")
    )
    fig.update_layout(figdict.get("layout"))
    fig.update_layout(title="Bar Chart")
    return fig


def make_table() -> go.Figure:
    """Sample table."""
    header = {
        "values": ["Metric", "Value"],
        "fill_color": "paleturquoise",
        "align": "left",
    }
    cells = {
        "values": [["Mean", "Median", "Std Dev"], [15.8, 14.5, 4.2]],
        "fill_color": "lavender",
        "align": "left",
    }

    fig = go.Figure(data=[go.Table(header=header, cells=cells)])
    fig.update_layout(figdict.get("layout"))
    fig.update_layout(height=600, title="Summary Table")
    return fig


st.markdown("# Page 2 ❄️")

scatter_fig = make_scatter()
bar_fig = make_bar()
table_fig = make_table()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.plotly_chart(scatter_fig, use_container_width=True, config=figdict["config"])
    st.plotly_chart(bar_fig, use_container_width=True, config=figdict["config"])

with col_right:
    st.plotly_chart(table_fig, use_container_width=True, config=figdict["config"])
