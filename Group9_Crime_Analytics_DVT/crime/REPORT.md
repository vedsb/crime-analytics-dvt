# Data Detective Challenge – Group 9
## Crime Pattern & Public Safety Analytics
**Course:** Data Visualization Techniques (CCP7005) | B.Tech Cyber Security, Sem VII | RCOEM Nagpur
**Group 9 – Roll Nos.:** 9, 27, 44, 63

---

## 1. Dataset + Source / Reference
| Item | Detail |
|---|---|
| Dataset | Seattle Police Department (SPD) incident reports, 1 Jun – 31 Aug 2014 |
| Original publisher | City of Seattle open data (Seattle Police Department records) |
| Copy used | `data/seattle_incidents_summer_2014.csv` |
| Download link | https://raw.githubusercontent.com/uwescience/datasci_course_materials/master/assignment6/seattle_incidents_summer_2014.csv |
| Size | 32,779 rows × 19 columns (~7 MB) |

---

## 2. Dataset Discovery Summary
**Records and attributes.** 32,779 offence records, 19 raw attributes; 16,937 unique incident numbers (one incident can contain several offence records).

| Type | Variables |
|---|---|
| Numerical | Latitude, Longitude, Census Tract 2000, Offence Code (+ derived: hour, report delay in days) |
| Categorical | Offence Type (147 values), Summarized Offense Description (48), District/Sector (17 + invalid), Zone/Beat (52), Month, Year (+ derived: crime group, weekday, part of day) |
| Temporal | Date Reported, Occurred Date/Range Start, Occurred Date Range End |
| Geographical | Latitude/Longitude, District, Beat, Hundred Block Location, Census Tract |

**Data-quality checks**

| Check | Result | Treatment |
|---|---|---|
| Fully duplicated rows | 0 | None needed |
| Repeated incident numbers | 15,842 rows (multi-offence incidents) | Kept; KPIs count *offence records* |
| Missing `Occurred Date Range End` | 16,280 (49.7%) | These are exact-time records. The other ~50% have a date **range** (crime discovered later), so their start hour is unreliable (spikes at 00:00) → hour-of-day charts use exact-time records only (sidebar toggle) |
| Coordinates `0,0` | 2,050 (6.3%) | Set to missing, excluded from map |
| District blank / `99` | 57 + 40 | Re-labelled "Unknown" |
| Missing census tract | 134 | Not used |
| Report delay outliers | median 0.13 d, 90th pct 4.0 d, 99th pct 62 d, max 388 d | Log scale for box plot |
| Year | all 2014 | Single-year, so no year trend |

**Potential relationships.** Offence type vs hour/weekday; district vs crime group; offence type vs reporting delay; spatial clustering of car prowl and violent crime.

---

## 3. Five Analytical Questions + Visualization Justification
| # | Analytical question | Variables | Visualization | Why appropriate |
|---|---|---|---|---|
| Q1 | Which crime types dominate and how do they group? | category, group, count | **Treemap** | Shows part-to-whole across a 2-level hierarchy (group → category) with 48 categories; area makes dominant types obvious, which a pie or plain bar can't do with so many levels |
| Q2 | How does daily crime volume change over the summer? | date, count | **Time-series (bars + 7-day moving average)** | Time is continuous and ordered; the moving average removes day-to-day noise to reveal the trend |
| Q3 | When do crimes happen (weekday × hour)? | weekday, hour, count | **Heatmap** | Two categorical/ordinal axes plus an intensity value; colour reveals clusters (e.g., evenings) at a glance |
| Q4 | Which police districts carry the most crime and of what kind? | district, group, count | **Stacked bar (sorted)** | Compares categories; stacking adds the crime mix; sorting shows ranking |
| Q5 | Where exactly are the hotspots? | lat, lon | **Density map (Plotly)** | Location is the key variable; density avoids over-plotting 30k points |
| Bonus | How quickly are crimes reported? | report delay, group | **Box plot (log scale)** | Compares distributions and exposes the heavy right-skew/outliers |

---

## 4. Source Code & Dashboard
- `crime_utils.py` – loading and cleaning
- `app.py` – Streamlit dashboard (filters: date range, crime group, category, district, exact-time toggle; 6 KPIs; 5 visualizations; findings, wrong-viz and discovery tabs)
- `make_screenshots.py` – exports charts to `screenshots/`
- Run with: `pip install -r requirements.txt` then `streamlit run app.py`

---

## 5. Five Major Findings
1. **Property crime dominates.** 69.0% of records (22,618) are property offences; car prowl alone is 6,230 records (19.0%). Violent crime is 12.7% (4,148). The top 10 categories make up 78.6% of records.
2. **Crime eased through the summer.** Average daily records: June 370.8 → July 359.8 → August 338.7, an 8.7% fall. Busiest day 25 Jun (447), quietest 3 Jul (255).
3. **Crime is geographically concentrated.** Districts M, K and B hold 22.5% of all records. District K has the highest violent share (23.2% vs 12.7% city-wide); district M is the car-prowl hotspot (868 car prowls = 32.9% of its records).
4. **Timing differs by crime type.** Among exact-time records, 54.0% of violent crime occurs 18:00–05:59 vs 44.2% of property crime; 52.6% of fraud occurs 12:00–17:59. Fridays average 381.5 records/day (~7% above the 356 average); Sundays are lowest (336.8).
5. **Most crime is reported quickly, but some types lag.** 77.8% are reported within a day (median 3.2 hours), yet 6.7% (2,199) take over a week. Fraud (median 1.8 days) and mail theft (1.6 days) are slowest.

## 6. Three Actionable Recommendations
1. **Target evening car-prowl prevention in districts M, R and D** (≈34% of exact-time car prowls): evening patrols, better lighting, "no valuables visible" signage near parking.
2. **Shift violent-crime resources to evenings/weekends in district K, then E.** K has 553 violent records (assault 302, threats 128, robbery 100).
3. **Fix data capture and promote faster reporting.** Make time and GPS mandatory (6.3% missing coordinates, 50% date ranges); add online/phone reporting and awareness campaigns for fraud and mail theft.

---

## 7. Wrong Visualization Challenge
**Question:** Did average daily crime change much between June, July and August?

| ✅ Correct | ❌ Misleading |
|---|---|
| Bar chart, y-axis from 0 (`screenshots/06_wrongviz_correct`) | Same bars, y-axis from 335 (`screenshots/06_wrongviz_misleading`) |

- **Why the first is appropriate:** bar length encodes value, so bars must start at zero. It honestly shows August (338.7/day) slightly lower than June (370.8/day), a −8.7% change.
- **Why the second is inappropriate:** the truncated axis makes August's bar ~3.7 units tall vs ~35.8 for June, so it looks ~90% lower.
- **Effect on interpretation:** decision-makers could believe crime collapsed, credit a programme that did nothing, or cut patrol budgets. A modest seasonal dip becomes a dramatic story.

---

## 8. AI as a Critic
> **NOTE FOR TEAM:** The critique below was produced by an AI assistant for the **Q3 heatmap**. Your faculty expects *your team* to ask a generative AI yourselves. Re-run it with the prompt below, paste your own result and keep or edit the decisions. Every member must be able to explain each decision.
>
> **Prompt:** "Critique this heatmap of average crime records by weekday and hour (sequential YlOrRd colour scale, hours 0–23 on the x-axis, weekdays on the y-axis, exact-time records only). Suggest improvements for accuracy, readability and accessibility."

| # | AI recommendation | Decision | Team justification |
|---|---|---|---|
| 1 | Records with a date range have an unreliable start hour (spike at 00:00); exclude or flag them | **ACCEPTED** | ~50% of records are ranges and 00:00 is inflated. We added an "exact-time only" toggle (on by default). |
| 2 | Plot raw counts normalised per weekday occurrence, since there are 14 Sundays and 13 of other days | **ACCEPTED** | The heatmap now shows average records per weekday-hour so days are comparable. |
| 3 | Facet the heatmap by crime group so patterns of violent vs property crime are not blended | **PARTIALLY ACCEPTED** | Static facets would add four more panels; instead the sidebar crime-group filter redraws the heatmap per group, keeping the dashboard compact. |
| 4 | Replace YlOrRd with a perceptually uniform colour map such as viridis | **REJECTED** | YlOrRd is a standard sequential scale where darker/redder naturally means "more", and it remains readable for most colour-vision deficiencies. Switching gave no clear gain. |

---

## 9. Two-Minute Data Story (≈ 260 words, speak at normal pace)
**What did we discover?**
"We analysed nearly 33,000 police offence records from Seattle over summer 2014. The headline: this is overwhelmingly a property-crime city. Seven in ten offences are property crimes, and car break-ins alone make up almost one in five. Crime is also concentrated. Just three districts account for over a fifth of all incidents. District M is the car-break-in hotspot, while district K stands out for violence: nearly one in four of its offences is violent, almost double the city average.

Timing matters too. Violent crime leans towards evenings and nights, with 54% happening after six in the evening, while fraud mostly happens in office hours. Overall, daily crime fell almost nine percent from June to August, and Fridays were the busiest day.

**Why does it matter?**
Police have limited officers. If patrols are spread evenly, they miss where and when harm actually happens. We also found that half of the records only have a time range and six percent have no location, so even good analysis is limited by weak data capture. And fraud is reported slowly, so recent fraud numbers will always look lower than reality.

**What action should be taken?**
First, focus evening car-prowl prevention on districts M, R and D. Second, move violent-crime patrols to evenings and weekends in district K, then E. Third, require exact time and GPS location when recording incidents and promote faster reporting of fraud. Data-driven deployment, not equal deployment, is how we make the city safer."

---

## 10. Limitations
- Data covers only 3 months of 2014, so there are no seasonal or multi-year conclusions and patterns may not reflect today.
- Counts are not normalised by population or area, so district rankings show volume, not risk per resident.
- Reported crime under-represents actual crime; delayed reporting biases the most recent dates.
- Crime-group labels (Violent / Property / Fraud / Public Order) are our own grouping of SPD categories (see `crime_utils.py`).
