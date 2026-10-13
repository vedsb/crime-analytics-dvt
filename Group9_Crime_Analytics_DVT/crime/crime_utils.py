"""Loading + cleaning for the Seattle Police incident dataset (Jun-Aug 2014)."""
import pandas as pd
import numpy as np

DATA_PATH = "data/seattle_incidents_summer_2014.csv"
DT_FMT = "%m/%d/%Y %I:%M:%S %p"

GROUPS = {
    "Violent": ["ASSAULT", "ROBBERY", "THREATS", "HOMICIDE", "WEAPON", "INJURY"],
    "Property": ["CAR PROWL", "OTHER PROPERTY", "BURGLARY", "VEHICLE THEFT", "PROPERTY DAMAGE",
                 "STOLEN PROPERTY", "SHOPLIFTING", "BIKE THEFT", "BURGLARY-SECURE PARKING-RES",
                 "MAIL THEFT", "PICKPOCKET", "THEFT OF SERVICES", "PURSE SNATCH",
                 "RECKLESS BURNING", "LOST PROPERTY", "RECOVERED PROPERTY"],
    "Fraud & Financial": ["FRAUD", "COUNTERFEIT", "FORGERY", "EMBEZZLE"],
}
CAT_TO_GROUP = {c: g for g, cs in GROUPS.items() for c in cs}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_raw(path=DATA_PATH):
    return pd.read_csv(path, low_memory=False)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d = d.rename(columns={
        "Summarized Offense Description": "category",
        "Offense Type": "offense_type",
        "District/Sector": "district",
        "Zone/Beat": "beat",
        "Hundred Block Location": "block",
        "Latitude": "lat", "Longitude": "lon",
    })
    d["occurred"] = pd.to_datetime(d["Occurred Date or Date Range Start"], format=DT_FMT, errors="coerce")
    d["reported"] = pd.to_datetime(d["Date Reported"], format=DT_FMT, errors="coerce")
    d["category"] = d["category"].str.strip().str.title()
    cat_map = {k.title(): v for k, v in CAT_TO_GROUP.items()}
    d["group"] = d["category"].map(cat_map).fillna("Public Order & Other")
    # District: blank or '99' are not real police sectors
    d["district"] = d["district"].astype("string").str.strip()
    d.loc[d["district"].isna() | (d["district"] == "99"), "district"] = "Unknown"
    # Zero coordinates are placeholders for 'no location' -> NaN so maps are not distorted
    bad = (d["lat"] == 0) | (d["lon"] == 0)
    d["geo_valid"] = ~bad
    d.loc[bad, ["lat", "lon"]] = np.nan
    # Time features
    d["date"] = d["occurred"].dt.normalize()
    d["hour"] = d["occurred"].dt.hour
    d["weekday"] = pd.Categorical(d["occurred"].dt.day_name(), categories=DAYS, ordered=True)
    d["month"] = d["occurred"].dt.month_name()
    d["report_lag_days"] = (d["reported"] - d["occurred"]).dt.total_seconds() / 86400
    d["part_of_day"] = pd.cut(d["hour"], [-1, 5, 11, 17, 23],
                              labels=["Night (00-05)", "Morning (06-11)", "Afternoon (12-17)", "Evening (18-23)"])
    d["is_weekend"] = d["weekday"].isin(["Saturday", "Sunday"])
    keep = ["RMS CDW ID", "General Offense Number", "category", "offense_type", "group", "district", "beat",
            "block", "occurred", "reported", "date", "hour", "weekday", "month", "part_of_day",
            "is_weekend", "report_lag_days", "lat", "lon", "geo_valid"]
    return d[keep]


def load_clean(path=DATA_PATH):
    return clean(load_raw(path))
