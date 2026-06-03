# Residential Market Insights — U.S. residential housing trends by state (Shiny Express app).

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import shinyswatch
from faicons import icon_svg
from shinywidgets import render_plotly
from state_choices import STATE_CHOICES

from shiny import reactive
from shiny.express import input, render, ui

# The directory containing this file
app_dir = Path(__file__).parent


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def string_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def filter_by_date(df: pd.DataFrame, date_range: tuple):
    rng = sorted(date_range)
    dates = pd.to_datetime(df["Date"], format="%Y-%m-%d").dt.date
    return df[(dates >= rng[0]) & (dates <= rng[1])]


def style_line_fig(fig, *, hover_template: str, compare_all_states: bool):
    """Dark theme styling; closest hover when all states are shown avoids clipped unified tooltips."""
    fig.update_traces(hovertemplate=hover_template)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="State",
        hovermode="closest" if compare_all_states else "x unified",
        hoverlabel=dict(
            bgcolor="#212529",
            bordercolor="#495057",
            font=dict(color="#f8f9fa", size=12 if compare_all_states else 13),
            namelength=-1,
            align="left",
        ),
        margin=dict(l=60, r=10, t=10, b=40),
        font=dict(color="#dee2e6"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
    )
    return fig


_date_series = pd.to_datetime(
    pd.read_csv(app_dir / "list_price.csv")["Date"],
    format="%Y-%m-%d",
)
min_date = _date_series.min().date()
max_date = _date_series.max().date()


# ---------------------------------------------------------------------
# Reactive calculations to read data
# ---------------------------------------------------------------------
@reactive.calc
def listings_df():
    return pd.read_csv(app_dir / "listings.csv")


@reactive.calc
def list_price_df():
    return pd.read_csv(app_dir / "list_price.csv")


@reactive.calc
def for_sale_df():
    return pd.read_csv(app_dir / "for_sale.csv")


# ---------------------------------------------------------------------
# Reactive calculations to filter data by date range
# N.B. since the reading of data happens in an *upstream* reactive calculation,
# the data will be read only once and then filtered as needed
# ---------------------------------------------------------------------
@reactive.calc
def listings_filtered():
    return filter_by_date(listings_df(), input.date_range())


@reactive.calc
def list_price_filtered():
    return filter_by_date(list_price_df(), input.date_range())


@reactive.calc
def for_sale_filtered():
    return filter_by_date(for_sale_df(), input.date_range())


@reactive.calc
def list_price_yoy():
    df = list_price_filtered()
    wide = df.pivot(index="Date", columns="StateName", values="Value").sort_index()
    yoy = wide.pct_change(periods=12)
    return yoy.reset_index().melt(
        id_vars="Date", var_name="StateName", value_name="YoY_Change"
    )


# ---------------------------------------------------------------------
# Start building the UI
# ---------------------------------------------------------------------

ui.page_opts(
    title="Residential Market Insights",
    id="page",
    theme=shinyswatch.theme.darkly(),
    fillable=False,
)

with ui.sidebar():
    ui.h5(
        "Residential Market Insights",
        style="margin-top: 0; margin-bottom: 0.25rem; font-weight: 600; color: #f8f9fa;",
    )
    ui.p(
        "U.S. Housing Market Dashboard",
        style="margin-top: 0; margin-bottom: 1.25rem; font-size: 0.78rem; color: #adb5bd;",
    )
    ui.input_select(
        "state",
        "Filter by state",
        choices=STATE_CHOICES,
    )
    ui.input_slider(
        "date_range",
        "Filter by date range",
        min=min_date,
        max=max_date,
        value=[min_date, max_date],
    )

with ui.layout_column_wrap(width="300px", heights_equal="row"):
    with ui.value_box(showcase=icon_svg("dollar-sign"), theme="primary"):
        "Latest Median List Price"

        @render.ui
        def price():
            df = list_price_filtered()
            df = df[df["StateName"] == input.state()]
            df = df.sort_values("Date")
            if df.empty:
                return "N/A"
            last_value = df.iloc[-1, -1]
            return f"${last_value:,.0f}"

    with ui.value_box(showcase=icon_svg("house"), theme="secondary"):
        "Latest Home Inventory Change"

        @render.ui
        def change():
            df = for_sale_filtered()
            df = df[df["StateName"] == input.state()]
            df = df.sort_values("Date")
            if len(df) < 2:
                return "N/A"
            last_value = df.iloc[-1, -1]
            second_last_value = df.iloc[-2, -1]
            percent_change = (last_value - second_last_value) / second_last_value * 100
            sign = "+" if percent_change > 0 else ""
            return f"{sign}{percent_change:.2f}%"

    with ui.value_box(showcase=icon_svg("arrow-trend-up"), theme="success"):
        "Latest YoY Median List Price Change"

        @render.ui
        def yoy_change():
            df = list_price_yoy()
            df = df[df["StateName"] == input.state()]
            df = df.sort_values("Date").dropna(subset=["YoY_Change"])
            if df.empty:
                return "N/A"
            yoy_pct = df.iloc[-1]["YoY_Change"] * 100
            sign = "+" if yoy_pct > 0 else ""
            return f"{sign}{yoy_pct:.1f}%"

ui.hr()

with ui.navset_card_underline(title="Median List Price"):

    with ui.nav_panel(" Plot", icon=icon_svg("chart-line")):

        @render_plotly
        def list_price_plot():
            df = list_price_filtered()
            compare_all = input.state() == "United States"
            if compare_all:
                df = df[df["StateName"] != "United States"]
            else:
                df = df[df["StateName"] == input.state()]

            fig = px.line(
                df,
                x="Date",
                y="Value",
                color="StateName",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"Value": "Median list price ($)", "Date": "Date"},
                height=320,
            )
            return style_line_fig(
                fig,
                hover_template="%{fullData.name}<br>%{x|%b %Y}: $%{y:,.0f}<extra></extra>",
                compare_all_states=compare_all,
            )

    with ui.nav_panel(" Table", icon=icon_svg("table")):

        @render.data_frame
        def list_price_table():
            df = list_price_filtered()
            df = df[df["StateName"] == input.state()]
            return render.DataGrid(df)


with ui.navset_card_underline(title="Home Inventory"):

    with ui.nav_panel(" Plot", icon=icon_svg("chart-line")):

        @render_plotly
        def for_sale_plot():
            df = for_sale_filtered()
            compare_all = input.state() == "United States"
            if compare_all:
                df = df[df["StateName"] != "United States"]
            else:
                df = df[df["StateName"] == input.state()]

            fig = px.line(
                df,
                x="Date",
                y="Value",
                color="StateName",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"Value": "Active homes for sale", "Date": "Date"},
                height=320,
            )
            return style_line_fig(
                fig,
                hover_template="%{fullData.name}<br>%{x|%b %Y}: %{y:,.0f}<extra></extra>",
                compare_all_states=compare_all,
            )

    with ui.nav_panel(" Table", icon=icon_svg("table")):

        @render.data_frame
        def for_sale_table():
            df = for_sale_filtered()
            df = df[df["StateName"] == input.state()]
            return render.DataGrid(df)


with ui.navset_card_underline(title="New Listings"):

    with ui.nav_panel(" Plot", icon=icon_svg("chart-line")):

        @render_plotly
        def listings_plot():
            df = listings_filtered()
            compare_all = input.state() == "United States"
            if compare_all:
                df = df[df["StateName"] != "United States"]
            else:
                df = df[df["StateName"] == input.state()]

            fig = px.line(
                df,
                x="Date",
                y="Value",
                color="StateName",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"Value": "New listings", "Date": "Date"},
                height=320,
            )
            return style_line_fig(
                fig,
                hover_template="%{fullData.name}<br>%{x|%b %Y}: %{y:,.0f}<extra></extra>",
                compare_all_states=compare_all,
            )

    with ui.nav_panel(" Table", icon=icon_svg("table")):

        @render.data_frame
        def listings_table():
            df = listings_filtered()
            df = df[df["StateName"] == input.state()]
            return render.DataGrid(df)


with ui.navset_card_underline(title="YoY Price Change"):

    with ui.nav_panel(" Plot", icon=icon_svg("chart-line")):

        @render_plotly
        def list_price_yoy_plot():
            df = list_price_yoy()
            compare_all = input.state() == "United States"
            if compare_all:
                df = df[df["StateName"] != "United States"]
            else:
                df = df[df["StateName"] == input.state()]

            fig = px.line(
                df,
                x="Date",
                y="YoY_Change",
                color="StateName",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"YoY_Change": "YoY median list price change", "Date": "Date"},
                height=320,
            )
            fig = style_line_fig(
                fig,
                hover_template="%{fullData.name}<br>%{x|%b %Y}: %{y:.1%}<extra></extra>",
                compare_all_states=compare_all,
            )
            fig.update_yaxes(tickformat=".1%")
            return fig

    with ui.nav_panel(" Table", icon=icon_svg("table")):

        @render.data_frame
        def list_price_yoy_table():
            df = list_price_yoy()
            df = df[df["StateName"] == input.state()]
            return render.DataGrid(df)

