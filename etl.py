"""ETL for Residential Market Insights: rebuild processed CSVs from Realtor.com Metro files."""

import pandas as pd


def average_by_state(df: pd.DataFrame):
    date_columns = df.columns[6:]

    states = df.groupby("StateName").mean(numeric_only=True)

    dates = states[date_columns].reset_index()

    states = dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")

    country = df[df["RegionType"] == "country"]

    country_dates = country[date_columns].reset_index()
    country_dates["StateName"] = "United States"

    country = country_dates.melt(
        id_vars=["StateName"], var_name="Date", value_name="Value"
    )

    res = pd.concat([states, country])

    return res[res["Date"] != "index"]


listings = average_by_state(pd.read_csv("Metro_new_listings_uc_sfrcondo_sm_month.csv"))
listings.to_csv("listings.csv", index=False)

list_price = average_by_state(pd.read_csv("Metro_mlp_uc_sfrcondo_sm_month.csv"))
list_price.to_csv("list_price.csv", index=False)

for_sale = average_by_state(pd.read_csv("Metro_invt_fs_uc_sfrcondo_sm_month.csv"))
for_sale.to_csv("for_sale.csv", index=False)
