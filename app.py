"""
Interactive companion to project.qmd.

Reads three artifacts produced by rendering the qmd:
    idata.nc
    idata.meta.json
    bracket_advancement.csv

Run: streamlit run app.py
"""

import json
import arviz as az
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

st.set_page_config(
    page_title="March Madness · Bayesian Bracket",
    layout="wide",
    page_icon="🏀",
)

BRAND = {
    "orange": "#FF6B1A",
    "blue":   "#185FA5",
    "navy":   "#0B1020",
    "gold":   "#F4D35E",
    "cream":  "#F5F1ED",
    "muted":  "rgba(245,241,237,0.55)",
}

pio.templates["mm"] = go.layout.Template(
    layout=dict(
        font=dict(family="Inter, sans-serif", color=BRAND["cream"], size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[BRAND["orange"], BRAND["blue"], BRAND["gold"],
                  "#7DC4E4", "#E89A6B", "#A98ED6", "#5BB99A", "#E26A6A",
                  "#C8B98C", "#6F89C9", "#D87FB1", "#88B07A"],
        xaxis=dict(gridcolor="rgba(245,241,237,0.08)",
                   zerolinecolor="rgba(245,241,237,0.12)"),
        yaxis=dict(gridcolor="rgba(245,241,237,0.08)",
                   zerolinecolor="rgba(245,241,237,0.12)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(l=50, r=30, t=40, b=50),
    )
)
pio.templates.default = "plotly_dark+mm"


CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800&display=swap');

  /* Force dark sports theme on every Streamlit container */
  html, body,
  .stApp,
  [data-testid="stAppViewContainer"],
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  .main, .main > div {
      background-color: #0B1020 !important;
      color: #F5F1ED !important;
  }
  [data-testid="stHeader"] { background: transparent !important; }

  /* Subtle court-line grid in the page background */
  .stApp::before {
      content: "";
      position: fixed;
      inset: 0;
      background-image:
          linear-gradient(rgba(255,107,26,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(24,95,165,0.04) 1px, transparent 1px);
      background-size: 64px 64px;
      pointer-events: none;
      z-index: 0;
  }
  .block-container {
      position: relative;
      z-index: 1;
      padding-top: 1.2rem;
      padding-bottom: 3rem;
      max-width: 1240px;
  }

  /* Thin orange accent strip pinned to the top of the viewport */
  .stApp::after {
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, #FF6B1A, #185FA5, #FF6B1A);
      z-index: 999;
  }

  html, body, [class*="css"] {
      font-family: 'Inter', sans-serif !important;
      color: #F5F1ED !important;
  }

  /* Hero banner */
  .hero {
      background: linear-gradient(135deg, #FF6B1A 0%, #D85A30 50%, #185FA5 100%);
      border-radius: 14px;
      padding: 1.3rem 1.8rem 1.2rem 1.8rem;
      margin-bottom: 1.4rem;
      box-shadow: 0 10px 40px -12px rgba(255, 107, 26, 0.35);
      position: relative;
      overflow: hidden;
  }
  .hero::after {
      content: "";
      position: absolute;
      inset: 0;
      background-image: radial-gradient(circle at 90% 30%, rgba(255,255,255,0.18), transparent 40%);
      pointer-events: none;
  }
  .hero-title, h1.hero-title {
      font-family: 'Bebas Neue', sans-serif !important;
      font-size: 2.5rem !important;
      letter-spacing: 0.04em !important;
      color: #FFFFFF !important;
      -webkit-text-fill-color: #FFFFFF !important;
      line-height: 1 !important;
      margin: 0 !important;
      text-shadow: 0 2px 14px rgba(0,0,0,0.3);
  }
  .hero-subtitle {
      color: rgba(255,255,255,0.94) !important;
      font-size: 0.96rem;
      font-weight: 500;
      margin-top: 0.5rem;
      max-width: 820px;
      position: relative;
  }
  .hero-chip {
      display: inline-block;
      background: rgba(255,255,255,0.22);
      color: #FFFFFF !important;
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 0.26rem 0.7rem;
      border-radius: 999px;
      margin-bottom: 0.55rem;
      border: 1px solid rgba(255,255,255,0.25);
  }

  /* Headings */
  h1, h2, h3, h4 {
      font-family: 'Inter', sans-serif !important;
      letter-spacing: -0.02em;
      color: #F5F1ED !important;
  }
  h2 { font-weight: 700 !important; }
  h3 { font-weight: 650 !important; }

  .stMarkdown p, .stMarkdown li, .stMarkdown {
      color: rgba(245,241,237,0.92) !important;
  }
  .stMarkdown strong { color: #FFFFFF !important; }

  /* Metric cards */
  [data-testid="stMetric"] {
      background: linear-gradient(180deg, rgba(255,107,26,0.10) 0%, rgba(20,27,47,0.7) 100%);
      border: 1px solid rgba(255,107,26,0.22);
      border-radius: 12px;
      padding: 1rem 1.1rem;
      transition: transform 0.15s ease, border-color 0.15s ease;
  }
  [data-testid="stMetric"]:hover {
      transform: translateY(-2px);
      border-color: rgba(255,107,26,0.55);
  }
  [data-testid="stMetricValue"] {
      font-family: 'Bebas Neue', sans-serif !important;
      font-size: 2rem !important;
      letter-spacing: 0.02em;
      color: #FF6B1A !important;
  }
  [data-testid="stMetricLabel"] {
      color: rgba(245,241,237,0.85) !important;
      font-size: 0.76rem !important;
      font-weight: 700 !important;
      letter-spacing: 0.08em;
      text-transform: uppercase;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
      gap: 0.3rem;
      border-bottom: 1px solid rgba(245,241,237,0.14);
      margin-bottom: 0.4rem;
  }
  .stTabs [data-baseweb="tab"] {
      padding: 0.7rem 1.2rem !important;
      font-weight: 700 !important;
      font-size: 0.92rem !important;
      letter-spacing: 0.06em !important;
      text-transform: uppercase !important;
      color: #F5F1ED !important;
      opacity: 0.7;
      border-radius: 10px 10px 0 0 !important;
      transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease;
  }
  .stTabs [data-baseweb="tab"] p {
      color: inherit !important;
      font-weight: 700 !important;
      font-size: 0.92rem !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
      opacity: 1;
      color: #FF6B1A !important;
      background: rgba(255,107,26,0.07);
  }
  .stTabs [aria-selected="true"] {
      color: #FF6B1A !important;
      opacity: 1 !important;
      border-bottom: 3px solid #FF6B1A !important;
      background: rgba(255,107,26,0.10);
  }
  .stTabs [aria-selected="true"] p { color: #FF6B1A !important; }

  /* Multiselect chips, selectbox, dropdowns */
  span[data-baseweb="tag"] {
      background-color: #FF6B1A !important;
      color: #FFFFFF !important;
      border-radius: 999px !important;
      font-weight: 600 !important;
  }
  span[data-baseweb="tag"] svg { fill: #FFFFFF !important; }
  div[data-baseweb="select"] > div {
      background-color: rgba(20,27,47,0.85) !important;
      border-color: rgba(255,107,26,0.25) !important;
      color: #F5F1ED !important;
  }
  div[data-baseweb="select"] > div:hover {
      border-color: rgba(255,107,26,0.55) !important;
  }
  div[data-baseweb="popover"] li { color: #F5F1ED !important; }
  div[data-baseweb="popover"] li:hover { background: rgba(255,107,26,0.15) !important; }

  label, .stCheckbox label, .stSelectbox label, .stMultiSelect label {
      color: #F5F1ED !important;
      font-weight: 600 !important;
  }

  /* Buttons */
  .stDownloadButton button, .stButton button {
      background: linear-gradient(180deg, #FF6B1A 0%, #D85A30 100%) !important;
      color: #FFFFFF !important;
      border: none !important;
      border-radius: 999px !important;
      padding: 0.55rem 1.4rem !important;
      font-weight: 700 !important;
      letter-spacing: 0.06em !important;
      text-transform: uppercase !important;
      font-size: 0.82rem !important;
      box-shadow: 0 6px 20px -8px rgba(255,107,26,0.6) !important;
      transition: transform 0.15s ease, box-shadow 0.15s ease !important;
  }
  .stDownloadButton button:hover, .stButton button:hover {
      transform: translateY(-1px);
      box-shadow: 0 10px 24px -8px rgba(255,107,26,0.85) !important;
  }

  /* Checkbox accent */
  .stCheckbox [data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] {
      background-color: #FF6B1A !important;
      border-color: #FF6B1A !important;
  }

  /* DataFrames */
  div[data-testid="stDataFrame"] {
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(245,241,237,0.10);
  }

  /* Info / alert callouts */
  div[data-testid="stAlert"] {
      border-radius: 12px;
      border-left: 4px solid #FF6B1A;
      background-color: rgba(255,107,26,0.10) !important;
      color: #F5F1ED !important;
  }
  div[data-testid="stAlert"] * { color: #F5F1ED !important; }

  /* Helpers */
  .muted {
      color: rgba(245,241,237,0.88) !important;
      font-size: 1rem;
      font-weight: 400;
      margin-bottom: 1.2rem;
      max-width: 820px;
      line-height: 1.55;
  }
  .section-rule {
      height: 3px;
      width: 64px;
      background: linear-gradient(90deg, #FF6B1A, #185FA5);
      border-radius: 2px;
      margin: 1.2rem 0 0.5rem 0;
  }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def load():
    idata = az.from_netcdf("idata.nc")
    with open("idata.meta.json") as f:
        meta = json.load(f)
    bracket = pd.read_csv("bracket_advancement.csv")

    post = idata.posterior
    n_teams = len(meta["teams"])
    samples = {
        "off":      post["off"].values.reshape(-1, n_teams),
        "def":      post["def"].values.reshape(-1, n_teams),
        "baseline": post["baseline"].values.flatten(),
        "hfa":      post["hfa"].values.flatten(),
        "sigma":    post["sigma_pts"].values.flatten(),
    }
    return meta, samples, bracket


meta, samples, bracket = load()
teams = meta["teams"]
conferences = meta["conferences"]
team_to_conf = meta["team_to_conf"]
season = meta.get("season", 2025)


st.markdown(
    f"""
    <div class="hero">
        <div class="hero-chip">NCAA · Men's Tournament · {season}</div>
        <h1 class="hero-title">MARCH MADNESS · BAYESIAN BRACKET</h1>
        <div class="hero-subtitle">
            Hierarchical offense / defense ratings &nbsp;·&nbsp; partial pooling by conference
            &nbsp;·&nbsp; uncertainty-aware predictions from {len(samples['baseline']):,} posterior draws.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Team ratings", "Predict", "Bracket", "About"]
)

net = samples["off"] + samples["def"]
df = pd.DataFrame({
    "Team":       teams,
    "Conference": [conferences[c] for c in team_to_conf],
    "Offense":    samples["off"].mean(0).round(2),
    "Defense":    samples["def"].mean(0).round(2),
    "Net":        net.mean(0).round(2),
    "Net 5%":     np.quantile(net, 0.05, axis=0).round(2),
    "Net 95%":    np.quantile(net, 0.95, axis=0).round(2),
}).sort_values("Net", ascending=False).reset_index(drop=True)
df.index += 1


with tab1:
    c1, c2, c3, c4 = st.columns(4)
    hfa = samples["hfa"]
    sigma = samples["sigma"]

    c1.metric("Teams", f"{len(teams):,}")
    c2.metric("Conferences", f"{len(conferences):,}")
    c3.metric(
        "Home-court advantage",
        f"{hfa.mean():+.2f} pts",
        help=f"90% interval: [{np.quantile(hfa, 0.05):.2f}, {np.quantile(hfa, 0.95):.2f}]",
    )
    c4.metric("Per-game noise", f"{sigma.mean():.2f} pts")

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown("### Top and bottom of the league")
    left, right = st.columns(2)

    with left:
        st.markdown("**Strongest 10 teams**")
        top = df.head(10)[["Team", "Conference", "Net", "Net 5%", "Net 95%"]]
        st.dataframe(top, use_container_width=True, height=390)

    with right:
        st.markdown("**Weakest 10 teams**")
        bottom = df.tail(10).sort_values("Net", ascending=True)[
            ["Team", "Conference", "Net", "Net 5%", "Net 95%"]
        ]
        st.dataframe(bottom, use_container_width=True, height=390)

    st.info(
        "The app reports posterior summaries from a Bayesian hierarchical model. "
        "Team offense and defense ratings are partially pooled by conference, so "
        "predictions account for both team strength and uncertainty."
    )


with tab2:
    st.markdown(
        "Filter posterior team ratings by conference. Net rating is offense plus defense; larger values indicate stronger teams."
    )

    confs_show = st.multiselect(
        "Filter by conference",
        conferences,
        default=conferences,
    )

    view = df[df["Conference"].isin(confs_show)].copy()

    if view.empty:
        st.warning("No teams selected. Please choose at least one conference.")
    else:
        # -------------------------
        # Summary cards
        # -------------------------
        st.markdown("### Rating summary")

        view["Uncertainty"] = view["Net 95%"] - view["Net 5%"]

        top_team = view.sort_values("Net", ascending=False).iloc[0]
        best_off = view.sort_values("Offense", ascending=False).iloc[0]
        best_def = view.sort_values("Defense", ascending=False).iloc[0]
        most_uncertain = view.sort_values("Uncertainty", ascending=False).iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Top net rating",
            top_team["Team"],
            f"{top_team['Net']:+.2f}"
        )

        c2.metric(
            "Best offense",
            best_off["Team"],
            f"{best_off['Offense']:+.2f}"
        )

        c3.metric(
            "Best defense",
            best_def["Team"],
            f"{best_def['Defense']:+.2f}"
        )

        c4.metric(
            "Most uncertain",
            most_uncertain["Team"],
            f"width {most_uncertain['Uncertainty']:.2f}"
        )

        # -------------------------
        # Top-N chart
        # -------------------------
        st.markdown("### Top teams by net rating")

        top_n = st.slider(
            "Number of teams to show",
            min_value=5,
            max_value=min(50, len(view)),
            value=min(20, len(view)),
            step=5,
        )

        plot_df = view.sort_values("Net", ascending=False).head(top_n)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=plot_df["Net"],
                y=plot_df["Team"],
                orientation="h",
                customdata=np.stack(
                    [
                        plot_df["Conference"],
                        plot_df["Offense"],
                        plot_df["Defense"],
                        plot_df["Net 5%"],
                        plot_df["Net 95%"],
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Conference: %{customdata[0]}<br>"
                    "Net: %{x:.2f}<br>"
                    "Offense: %{customdata[1]:.2f}<br>"
                    "Defense: %{customdata[2]:.2f}<br>"
                    "90% interval: [%{customdata[3]:.2f}, %{customdata[4]:.2f}]"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            height=max(420, top_n * 24),
            xaxis_title="Net rating",
            yaxis_title="",
            margin=dict(l=120, r=30, t=20, b=50),
        )

        fig.update_yaxes(autorange="reversed")

        st.plotly_chart(fig, use_container_width=True)

        # -------------------------
        # Compact ranking table
        # -------------------------
        st.markdown("### Compact ranking")

        compact = plot_df[["Team", "Conference", "Net"]].copy()
        compact["Net"] = compact["Net"].round(2)

        st.dataframe(
            compact,
            use_container_width=True,
            height=360,
            hide_index=True,
        )

        # -------------------------
        # Optional full table
        # -------------------------
        with st.expander("View full rating table"):
            full_view = view[
                ["Team", "Conference", "Offense", "Defense", "Net", "Net 5%", "Net 95%"]
            ].copy()

            st.dataframe(
                full_view,
                use_container_width=True,
                height=520,
            )

        csv = view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered ratings",
            data=csv,
            file_name="team_ratings.csv",
            mime="text/csv",
        )


with tab3:
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Simulate a hypothetical game using posterior samples. '
        'The margin distribution includes both parameter uncertainty and game-level '
        'noise.</div>',
        unsafe_allow_html=True,
    )