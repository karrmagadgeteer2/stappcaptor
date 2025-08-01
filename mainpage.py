"""Main page for Captor marketing site.

Copyright (c) Captor Fund Management AB.

Licensed under the BSD 3-Clause License. You may obtain a copy of the License at:
https://github.com/karrmagadgeteer2/stappcaptor/blob/master/LICENSE.md
SPDX-License-Identifier: BSD-3-Clause
"""

import time

import requests
import streamlit as st
from openseries import OpenFrame, OpenTimeSeries, report_html

timeout = 10
verify = True
base_url = "captor.se"
url = f"https://api.{base_url}/graphql"


class GraphqlError(Exception):
    """Raised if the Graphql query returns any error(s)."""


if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.exp = None
    st.session_state.user_display_name = None
    st.session_state.user_id = None

st.markdown("# Main page 🎈")

# ─── Check if we already have a valid token ──────────────────────────────────
token = st.session_state.token
valid_token = (
    token is not None
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
                    auth_url = "https://auth.captor.se/token"
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
                        resp = requests.post(
                            url=auth_url,
                            data=payload,
                            headers=headers,
                            timeout=10,
                        )
                        resp.raise_for_status()
                    except requests.RequestException as exc:
                        st.error(f"Authentication failed: {exc}")
                    else:
                        data = resp.json()
                        tok = data.get("access_token")
                        if not tok:
                            st.error("No token returned.")
                        else:
                            st.session_state.token = tok
                            st.session_state.exp = data.get("exp")
                            st.session_state.user_display_name = data.get(
                                "user_display_name"
                            )
                            st.session_state.user_id = data.get("user_id")

                            st.query_params.clear()
                            st.query_params["token"] = [tok]

                            st.success(
                                "Authenticated as "
                                f"{st.session_state.user_display_name}"
                            )
                            login_container.empty()
                            st.rerun()

if valid_token:
    st.write("✅ Logged in. You can now call the Captor API.")

st.subheader("Query Funds")
options = {
    "Captor Iris Bond": {
        "series_id": "5b72a10c23d27735104e0576",
        "comparison_id": "63892890473ba6918f4ee954",
    },
    "Captor Dahlia Green Bond": {
        "series_id": "5b72ccea23d2772e9c014bbc",
        "comparison_id": "6188589536516e22dcf43f91",
    },
    "Captor Scilla Global Equity": {
        "series_id": "5c1115fbce5b131cf0b224fc",
        "comparison_id": "615da9a917999f35f7faede0",
    },
    "Captor Aster Global Credit": {
        "series_id": "606f1ad71e33b60011587f6a",
        "comparison_id": "6391a977e6a359fc24e82ba4",
    },
    "Captor Aster Global Credit Short Term": {
        "series_id": "6310e1cb160b504c72dd91ea",
        "comparison_id": "6396031a19196fe34bcb0397",
    },
    "Captor Aster Global High Yield": {
        "series_id": "638f681e0c2f4c8d28a13392",
        "comparison_id": "630a6fd5935d4f68b57d45e1",
    },
    "Captor Global Fixed Income": {
        "series_id": "65733b0114719695d6624c08",
        "comparison_id": "658d5593d5913159f8909a60",
    },
    "Captor Perenne Short Term Bond": {
        "series_id": "657c75a8d87ac90720fb664c",
        "comparison_id": "560ee63293f8da1218da70de",
    },
}
choice = st.selectbox(
    label="Fund select",
    label_visibility="collapsed",
    options=options,
    index=0,
)

if st.button("Load"):
    if not valid_token:
        st.error("Please authenticate before running data load.")
    else:
        with st.spinner("⏳ Fetching data…"):
            query = """ query timeseries(
                          $idIn: [GraphQLObjectId!],
                          $startDate: GraphQLDateString,
                          $endDate: GraphQLDateString,
                          $includeItems: Boolean = true
                        ) {
                          timeseries(
                            filter: {
                              idIn: $idIn,
                              startDate: $startDate,
                              endDate: $endDate
                            }
                            includeItems: $includeItems
                          ) {
                            _id
                            instrument {
                              _id
                              longName
                              currency
                              isin
                            }
                            dates
                            values
                          }
                        } """
            headers = {
                "Authorization": f"Bearer {st.session_state.token}",
                "accept-encoding": "gzip",
            }
            payload: dict[str, str | dict[str, list[str] | None]] = {
                "query": query,
                "variables": {
                    "idIn": [
                        options[choice]["series_id"],
                        options[choice]["comparison_id"],
                    ],
                    "startDate": None,
                    "endDate": None,
                },
            }
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
        elif not data or not data.get("timeseries"):
            st.warning(f"⚠️ No timeseries found:\n\n{data}")
        else:
            series = {}
            for item in data["timeseries"]:
                series[item["_id"]] = OpenTimeSeries.from_arrays(
                    name=item["instrument"]["longName"],
                    timeseries_id=item["_id"],
                    instrument_id=item["instrument"]["_id"],
                    isin=item["instrument"]["isin"],
                    baseccy=item["instrument"]["currency"],
                    dates=item["dates"],
                    values=item["values"],
                )
            frame = OpenFrame(
                constituents=[
                    series[options[choice]["series_id"]],
                    series[options[choice]["comparison_id"]],
                ]
            )
            frame.trunc_frame().value_nan_handle()
            figure, _ = report_html(
                data=frame,
                filename="frame.html",
                title=frame.constituents[0].label,
                bar_freq="BQE",
                vertical_legend=False,
                output_type="div",
            )
            figure = figure.update_layout(font_size=14, width=1100, height=700)
            st.plotly_chart(figure_or_data=figure, theme=None)
