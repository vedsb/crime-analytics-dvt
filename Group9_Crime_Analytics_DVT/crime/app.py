"""
Data Detective Challenge - Crime Pattern & Public Safety Analytics
Dataset : Seattle Police Department incident reports, Jun-Aug 2014
Run     : streamlit run app.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from crime_utils import DAYS, load_raw, clean

st.set_page_config(page_title="Crime Pattern & Public Safety Analytics", page_icon="🚓", layout="wide")


# ----------------------------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------------------------
@st.cache_data
def get_data():
    raw = load_raw()
    d = clean(raw)
    # Rows with an 'occurred end' date are date RANGES (crime discovered later, exact time unknown)
    d["exact_time"] = raw["Occurred Date Range End"].isna().values
    return d


df = get_data()
GROUP_ORDER = ["Property", "Violent", "Fraud & Financial", "Public Order & Other"]
COLORS = {"Property": "#2a6f97", "Violent": "#c1121f", "Fraud & Financial": "#e9a100", "Public Order & Other": "#7e5aa2"}

# ----------------------------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------------------------
st.title("🚓 Crime Pattern & Public Safety Analytics")
st.caption("Data Visualization Techniques (CCP7005) | Data Detective Challenge | Seattle Police incident reports, Jun-Aug 2014")

with st.expander("Project objective & dataset description", expanded=False):
    st.markdown(
        """
**Objective.** Act as a data-visualization consulting team for a city police department: find *what* crimes
happen, *when* and *where* they cluster, and *how fast* they are reported, so that patrol and prevention
resources can be placed where they have the most impact.

**Dataset.** Seattle Police Department incident reports (public records), 1 Jun - 31 Aug 2014.
32,779 offence records, 19 raw attributes (offence type, occurrence/report timestamps, police district & beat,
block, latitude/longitude, census tract). One incident can have several offence records.

**Data-quality handling.** 2,050 rows with `0,0` coordinates were treated as missing locations; district `99`/blank
became *Unknown*; ~50% of records carry a date **range** (crime discovered later) so hour-of-day charts use
exact-time records only (switchable in the sidebar).
        """
    )

# ----------------------------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------------------------
st.sidebar.header("Filters")
dmin, dmax = df["date"].min().date(), df["date"].max().date()
date_range = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
groups = st.sidebar.multiselect("Crime group", GROUP_ORDER, default=GROUP_ORDER)
cat_options = sorted(df[df["group"].isin(groups)]["category"].unique())
cats = st.sidebar.multiselect("Offence category (blank = all in group)", cat_options)
districts = st.sidebar.multiselect("Police district", sorted(df["district"].unique()), default=[])
exact_only = st.sidebar.checkbox("Hour-of-day charts: exact-time records only", value=True,
                                 help="Records with a date range have an unreliable start hour (often midnight).")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
else:
    start = end = date_range[0] if isinstance(date_range, tuple) else date_range

f = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end) & df["group"].isin(groups)]
if cats:
    f = f[f["category"].isin(cats)]
if districts:
    f = f[f["district"].isin(districts)]

if f.empty:
    st.warning("No records match the current filters.")
    st.stop()

n_days = (end - start).days + 1
hf = f[f["exact_time"]] if exact_only else f

# ----------------------------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Offence records", f"{len(f):,}")
k2.metric("Avg per day", f"{len(f) / n_days:,.0f}")
k3.metric("Violent share", f"{(f['group'] == 'Violent').mean():.1%}")
top_d = f[f["district"] != "Unknown"]["district"].value_counts()
k4.metric("Top district", f"{top_d.index[0]} ({top_d.iloc[0]:,})" if len(top_d) else "-")
peak = hf["hour"].value_counts()
k5.metric("Peak hour", f"{peak.index[0]:02d}:00" if len(peak) else "-")
k6.metric("Median report delay", f"{f['report_lag_days'].median() * 24:,.1f} h")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔎 Findings & Recommendations",
                                  "⚠️ Wrong Visualization Challenge", "🧾 Dataset Discovery"])

# ----------------------------------------------------------------------------------------------
# TAB 1 - Dashboard
# ----------------------------------------------------------------------------------------------
with tab1:
    # Q1 - composition
    st.subheader("Q1. Which crime types dominate?")
    tm = f.groupby(["group", "category"]).size().reset_index(name="records")
    fig = px.treemap(tm, path=[px.Constant("All crime"), "group", "category"], values="records",
                     color="group", color_discrete_map={**COLORS, "(?)": "#999"})
    fig.update_traces(textinfo="label+value+percent root")
    fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=430)
    st.plotly_chart(fig, use_container_width=True)

    # Q2 - trend
    st.subheader("Q2. How does daily crime volume change over the summer?")
    daily = f.groupby("date").size().rename("records").reset_index()
    daily["7-day average"] = daily["records"].rolling(7, min_periods=1).mean()
    fig = go.Figure()
    fig.add_bar(x=daily["date"], y=daily["records"], name="Daily records", marker_color="#bcd4e6")
    fig.add_scatter(x=daily["date"], y=daily["7-day average"], name="7-day average",
                    line=dict(color="#c1121f", width=3))
    fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=350, yaxis_title="Offence records",
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    # Q3 - heatmap
    with c1:
        st.subheader("Q3. When do crimes happen?")
        st.caption("Average records per weekday-hour" + (" (exact-time records only)" if exact_only else ""))
        weekday_days = pd.Series(pd.date_range(start, end)).dt.day_name().value_counts()
        hm = hf.groupby(["weekday", "hour"], observed=False).size().unstack(fill_value=0).reindex(DAYS)
        hm = hm.reindex(columns=range(24), fill_value=0)
        hm = hm.div(weekday_days.reindex(DAYS).fillna(1).values, axis=0)
        fig = px.imshow(hm, aspect="auto", color_continuous_scale="YlOrRd",
                        labels=dict(x="Hour of day", y="", color="Avg records"))
        fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=380)
        st.plotly_chart(fig, use_container_width=True)

    # Q4 - district comparison
    with c2:
        st.subheader("Q4. Which districts carry the most crime?")
        mode = st.radio("Show", ["Counts", "Share of district (%)"], horizontal=True, label_visibility="collapsed")
        st.caption("Stacked by crime group, sorted by total. Counts show volume, not risk per resident "
                   "(the dataset has no population data). Districts are SPD police sectors.")
        dd = f[f["district"] != "Unknown"].groupby(["district", "group"]).size().reset_index(name="records")
        tot = dd.groupby("district")["records"].sum().sort_values(ascending=False)
        order = tot.index.tolist()
        pct = mode.startswith("Share")
        fig = px.bar(dd, x="district", y="records", color="group", color_discrete_map=COLORS,
                     category_orders={"district": order, "group": GROUP_ORDER})
        if pct:
            fig.update_layout(barnorm="percent")
        if not pct:  # total label above each bar
            fig.add_scatter(x=order, y=tot.values, mode="text", text=[f"{v:,}" for v in tot.values],
                            textposition="top center", showlegend=False, hoverinfo="skip")
        fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=380, xaxis_title="Police district",
                          yaxis_title="% of district's records" if pct else "Offence records",
                          legend=dict(orientation="h", y=1.12, title=None))
        st.plotly_chart(fig, use_container_width=True)

    # Q5 - map
    st.subheader("Q5. Where exactly are the hotspots?")
    geo = f[f["geo_valid"]]
    st.caption(f"{len(geo):,} geo-located records shown ({len(f) - len(geo):,} with missing coordinates excluded)")
    fig = px.density_map(geo, lat="lat", lon="lon", radius=7, zoom=10.3,
                         center=dict(lat=47.62, lon=-122.33), map_style="carto-positron",
                         color_continuous_scale="Inferno")
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=520)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------------------------
# TAB 2 - Findings & recommendations (numbers computed on the full dataset)
# ----------------------------------------------------------------------------------------------
with tab2:
    st.header("Five major findings")
    st.caption("Figures refer to the full, unfiltered dataset (32,779 offence records).")
    st.markdown(
        """
1. **Property crime dominates.** 69.0% of records (22,618) are property offences; **car prowl** alone is the single
   largest category at 6,230 records (19.0%). Violent crime is 12.7% (4,148). The top 10 categories make up 78.6% of all records.
2. **Crime eased through the summer.** Daily volume fell from 370.8 (June) to 359.8 (July) to 338.7 (August), an **8.7% drop**.
   The busiest day was 25 Jun (447 records); the quietest was 3 Jul (255).
3. **Crime is geographically concentrated.** Three districts (M, K, B) hold 22.5% of all records. **District K has the
   highest violent share (23.2% vs 12.7% city-wide)**, while **district M is the car-prowl hotspot** (868 car prowls =
   32.9% of M's records).
4. **Timing differs by crime type.** Among exact-time records, 54.0% of violent crime happens in the evening/night
   (18:00-05:59) versus 44.2% of property crime, while 52.6% of fraud occurs in the afternoon (business hours).
   Fridays average **381.5** records/day (about 7% above the 356 daily average); Sundays are the quietest (336.8).
5. **Most crime is reported fast, but some types lag.** 77.8% of records are reported within a day (median 3.2 h), yet 6.7%
   (2,199) take more than a week. Fraud (median 1.8 days) and mail theft (1.6 days) are slowest, so
   fraud counts are probably under-stated for recent dates.
        """
    )
    st.header("Three actionable recommendations")
    st.markdown(
        """
1. **Target evening car-prowl prevention in districts M, R and D.** Run evening patrols, better lighting and "don't leave
   valuables visible" signage near parking areas. These three districts hold about 34% of exact-time car prowls.
2. **Shift violent-crime resources to evenings and weekends in district K (then E).** K alone has 553 violent records
   (assault 302, threats 128, robbery 100). Schedule extra evening foot/bike patrols and street-outreach teams there.
3. **Fix data capture and promote fast reporting.** Make the incident time and GPS location mandatory (6.3% of records have
   no coordinates and 50% have only a date range), and launch online/phone reporting plus public awareness for fraud and
   mail theft so victims report sooner and analysis becomes more reliable.
        """
    )

# ----------------------------------------------------------------------------------------------
# TAB 3 - Wrong visualization challenge
# ----------------------------------------------------------------------------------------------
with tab3:
    st.header("Wrong Visualization Challenge")
    st.markdown("**Question:** *Did average daily crime change much between June, July and August?*")
    rate = (df.groupby("month").size() / pd.Series({"June": 30, "July": 31, "August": 31})).reindex(["June", "July", "August"])
    cA, cB = st.columns(2)
    with cA:
        st.markdown("#### ✅ Correct: bar chart, axis starts at zero")
        fig = px.bar(x=rate.index, y=rate.values, text=[f"{v:.1f}" for v in rate.values],
                     labels=dict(x="", y="Avg records per day"), color_discrete_sequence=["#2a6f97"])
        fig.update_yaxes(range=[0, 420])
        fig.update_layout(height=380, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
    with cB:
        st.markdown("#### ❌ Misleading: same data, truncated axis")
        fig = px.bar(x=rate.index, y=rate.values, text=[f"{v:.1f}" for v in rate.values],
                     labels=dict(x="", y="Avg records per day"), color_discrete_sequence=["#c1121f"])
        fig.update_yaxes(range=[335, 372])
        fig.update_layout(height=380, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f"""
**Why the first is appropriate.** Bar length encodes value, so bars must start at zero. Here August ({rate['August']:.1f}) is visibly
a little shorter than June ({rate['June']:.1f}), an honest **{(rate['August'] / rate['June'] - 1):.1%}** change.

**Why the second is misleading.** The y-axis starts at 335, so the bar for August is only ~3.7 units tall against ~35.8 for June.
Bar *heights* now suggest August crime is roughly **90% lower** than June, while the real fall is under 9%.

**Effect on interpretation.** A reader (or a city council) might conclude crime has collapsed and cut patrol budgets, or assume a
dramatic prevention programme worked. The truncated chart turns a modest seasonal decline into an apparent crisis-to-calm story.
        """
    )

# ----------------------------------------------------------------------------------------------
# TAB 4 - Dataset discovery
# ----------------------------------------------------------------------------------------------
with tab4:
    st.header("Dataset Discovery Summary")
    raw_missing = pd.DataFrame({
        "Issue": ["Total records (rows)", "Raw attributes (columns)", "Unique incident numbers", "Fully duplicated rows",
                  "Missing 'Occurred Date Range End' (exact-time records)", "Missing/blank district", "District = 99 (invalid)",
                  "Coordinates = 0,0 (missing location)", "Missing census tract", "Reports filed >7 days after occurrence"],
        "Value": ["32,779", "19", "16,937 (15,842 repeat rows = multi-offence incidents)", "0", "16,280 of 32,779 (49.7%)",
                  "57", "40", "2,050 (6.3%)", "134", "2,199 (6.7%)"],
    })
    st.table(raw_missing)
    st.markdown(
        """
**Variable types.** *Numerical:* latitude, longitude, hour, report delay (days), census tract (identifier-like).
*Categorical:* offence code/type/category, crime group, district, beat, weekday, month, part of day.
*Temporal:* occurred date-time, reported date-time. *Geographical:* lat/lon, district, beat, block, census tract.

**Outliers.** Report delay is heavily right-skewed (median 0.13 days, 90th percentile 4.0 days, 99th percentile 62 days, max 388 days).
Daily counts range 255-447 with no extreme outliers.

**Candidate relationships.** Offence type vs hour/weekday; district vs offence group; offence type vs reporting delay.
        """
    )
    st.subheader("Supplementary: reporting delay by crime group (log scale)")
    bx = df[df["report_lag_days"] > 0].copy()
    fig = px.box(bx, x="group", y="report_lag_days", color="group", color_discrete_map=COLORS, log_y=True,
                 category_orders={"group": GROUP_ORDER}, labels=dict(report_lag_days="Days between occurrence and report (log)", group=""))
    fig.update_layout(height=400, showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Records with zero delay are omitted because a log axis cannot show zero.")
    st.subheader("Cleaned data sample")
    st.dataframe(f.head(200), use_container_width=True)