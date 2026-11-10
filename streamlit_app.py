import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="IS 445 HW6: Illinois State Buildings", layout="wide")

DATA_URL = (
    "https://raw.githubusercontent.com/UIUC-iSchool-DataViz/"
    "is445_data/main/building_inventory.csv"
)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_URL)
    # Year 0 is a placeholder for "unknown" in this dataset, so drop those rows.
    df = df[(df["Year Constructed"] > 0) & (df["Square Footage"] > 0)].copy()
    df["Decade"] = (df["Year Constructed"] // 10) * 10
    df["Usage"] = df["Usage Description"].replace(
        {
            "Detention & Correc": "Detention & Corrections",
            "Utiility & Miscellan": "Utility & Misc.",
            "Not provided": "Unusual",
        }
    )
    return df


df = load_data()

# ---------------------------------------------------------------- header
st.title("What the State of Illinois Built, and When")
st.markdown(
    "This app explores the **Illinois state building inventory**, a list of "
    f"{len(df):,} buildings owned by state agencies (after removing rows with an "
    "unknown construction year or zero square footage). Both charts start at "
    "the 1850s, because earlier decades contain only a handful of buildings. Both charts are "
    "interactive: drag across the first chart, and use the controls above the second."
)

# ---------------------------------------------------------------- plot 1
st.header("1. Construction by decade, and who built it")
st.markdown(
    "**Click and drag across the top chart** to select a range of decades. "
    "The bottom chart updates to show which agencies added the most square "
    "footage during the decades you picked. Double-click to clear the selection."
)

top_agencies = df.groupby("Agency Name")["Square Footage"].sum().nlargest(12).index
plot1_df = df[df["Decade"] >= 1850].copy()
plot1_df["Agency"] = plot1_df["Agency Name"].where(
    plot1_df["Agency Name"].isin(top_agencies), "All other agencies"
)

brush = alt.selection_interval(encodings=["x"], name="decades")

timeline = (
    alt.Chart(plot1_df)
    .mark_bar(color="#4c78a8")
    .encode(
        x=alt.X("Decade:O", title="Decade constructed", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(
            "sum(Square Footage):Q",
            title="Square feet built",
            axis=alt.Axis(format="~s"),
        ),
        opacity=alt.condition(brush, alt.value(1.0), alt.value(0.3)),
        tooltip=[
            alt.Tooltip("Decade:O", title="Decade"),
            alt.Tooltip("sum(Square Footage):Q", title="Square feet", format=","),
            alt.Tooltip("count():Q", title="Buildings"),
        ],
    )
    .add_params(brush)
    .properties(height=260, title="Total square footage built per decade (drag to select)")
)

agencies = (
    alt.Chart(plot1_df)
    .transform_filter(brush)
    .mark_bar(color="#f58518")
    .encode(
        y=alt.Y("Agency:N", sort="-x", title=None),
        x=alt.X(
            "sum(Square Footage):Q",
            title="Square feet built in selected decades",
            axis=alt.Axis(format="~s"),
        ),
        tooltip=[
            alt.Tooltip("Agency:N"),
            alt.Tooltip("sum(Square Footage):Q", title="Square feet", format=","),
            alt.Tooltip("count():Q", title="Buildings"),
        ],
    )
    .properties(height=340, title="Square footage by agency for the selected decades")
)

st.altair_chart(
    alt.vconcat(timeline, agencies).configure_axis(labelFontSize=12, titleFontSize=13)
    .configure_title(fontSize=15, anchor="start"),
    width="stretch",
)

st.subheader("Write-up: plot 1")
st.write(
    "This view highlights *when* the state did most of its building and *who* was "
    "responsible for it. The top chart shows a clear postwar boom: square footage "
    "built roughly doubles from the 1950s to the 1960s, which is the clear peak "
    "(about 21 million square feet), then declines decade by decade. Selecting a "
    "range of decades shows how the mix of agencies changes over time. The "
    "University of Illinois leads the 1960s and 1970s, while the Department of "
    "Corrections leads every decade from the 1980s through the 2000s, during the "
    "prison expansion. For design, I used bars for "
    "both charts because decades and agencies are discrete categories and we "
    "compare totals by length along a common baseline. The decade axis is "
    "ordinal so every decade gets equal width, and the square-footage axes use "
    "SI abbreviations (e.g. 2M) to keep the labels short. I used one color per "
    "chart instead of a color scale, because color would not add any "
    "information here. Unselected decades fade to 30% opacity, which shows "
    "the selection without hiding the overall shape. The agency chart is sorted "
    "largest to smallest, and agencies outside the top 12 are grouped together "
    "so the labels stay readable. If I had more time, I would let the user switch "
    "between square footage and building count, and I would normalize by "
    "agency size, since the raw totals favor large agencies."
)

# ---------------------------------------------------------------- plot 2
st.header("2. What kinds of buildings, and in what condition")
st.markdown(
    "Use the controls to pick an agency and a measure. The heatmap shows how "
    "each type of building is spread across the decades."
)

col1, col2, col3 = st.columns([2, 1, 1])
agency_options = ["All agencies"] + sorted(df["Agency Name"].unique())
with col1:
    agency_choice = st.selectbox("Agency", agency_options)
with col2:
    metric_choice = st.radio("Measure", ["Number of buildings", "Square footage"])
with col3:
    status_choice = st.multiselect(
        "Building status",
        sorted(df["Bldg Status"].unique()),
        default=sorted(df["Bldg Status"].unique()),
    )

plot2_df = df[df["Bldg Status"].isin(status_choice)]
if agency_choice != "All agencies":
    plot2_df = plot2_df[plot2_df["Agency Name"] == agency_choice]
plot2_df = plot2_df[plot2_df["Decade"] >= 1850]

if plot2_df.empty:
    st.warning("No buildings match these filters. Try selecting more options.")
else:
    if metric_choice == "Number of buildings":
        color_field, color_title, fmt = "count():Q", "Buildings", ","
    else:
        color_field, color_title, fmt = "sum(Square Footage):Q", "Square feet", ","

    heatmap = (
        alt.Chart(plot2_df)
        .mark_rect()
        .encode(
            x=alt.X("Decade:O", title="Decade constructed", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("Usage:N", title="Building use", sort="-color"),
            color=alt.Color(
                color_field,
                title=color_title,
                scale=alt.Scale(scheme="viridis", type="sqrt"),
                legend=alt.Legend(format="~s"),
            ),
            tooltip=[
                alt.Tooltip("Usage:N", title="Use"),
                alt.Tooltip("Decade:O"),
                alt.Tooltip("count():Q", title="Buildings"),
                alt.Tooltip("sum(Square Footage):Q", title="Square feet", format=fmt),
            ],
        )
        .properties(
            height=380,
            title=f"{color_title} by building use and decade: {agency_choice}",
        )
        .configure_axis(labelFontSize=12, titleFontSize=13)
        .configure_title(fontSize=15, anchor="start")
    )
    st.altair_chart(heatmap, width="stretch")
    st.caption(
        f"Showing {len(plot2_df):,} buildings."
    )

st.subheader("Write-up: plot 2")
st.write(
    "The first chart asks *when* and *who*. This one asks *what*: which types "
    "of buildings were built in each era, and how that changes by agency and "
    "building status. For the whole state, storage and \"unusual\" structures "
    "(sheds, shelters, and other small outbuildings, mostly at Natural "
    "Resources sites) account for the most buildings. When you switch the "
    "measure to square footage, assembly, business, and education buildings "
    "stand out instead, and \"unusual\" nearly disappears because those "
    "structures are tiny. This shows how the choice of measure changes the "
    "story. Filtering to \"Abandon\" shows that most abandoned buildings are "
    "older storage, industrial, and \"unusual\" structures. For design, I used a heatmap (rect marks) "
    "because both axes are categorical and the question is about the pattern "
    "across the whole grid, not exact values. I chose the sequential viridis "
    "color map because it is perceptually uniform and readable for colorblind "
    "viewers, and I put it on a square-root scale. Otherwise a few huge cells "
    "(like 1960s assembly buildings) would wash out everything else. The rows are sorted "
    "by total so the most common uses are at the top. The Streamlit dropdown, "
    "radio button, and multiselect re-filter the data before Altair draws it, "
    "and the tooltips give exact counts. If I had more time, I would add a small "
    "bar chart of totals on each side of the grid. I would also clean up the "
    "vague \"Unusual\" category using the secondary usage columns."
)

# ---------------------------------------------------------------- HW5 overlap
st.header("Overlap with Homework #5")
st.write(
    "There is no overlap with Homework #5. HW5 used the professional licenses "
    "dataset (licenses_fall2022.csv), with a stacked bar chart of the top license "
    "types by status and a line chart of licenses issued per year. This "
    "assignment uses a different dataset from a different source (the Illinois "
    "building inventory) and different plot types: a brushable decade bar chart "
    "linked to an agency bar chart, and a heatmap filtered by Streamlit widgets. "
    "Both plots, the data processing, and this write-up are new for this "
    "assignment, and no text or code is copied from HW5."
)

st.caption(f"Data: Illinois building inventory, via the IS 445 data repository ({DATA_URL}).")
