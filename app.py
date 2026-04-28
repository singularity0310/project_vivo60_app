"""
Interactive companion to project.qmd.

Reads three artifacts produced by rendering the qmd:
    idata.nc
    idata.meta.json
    bracket_advancement.csv

Run:
    streamlit run app.py
"""

import html
import json

import arviz as az
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import plotly.io as pio

# ============================================================
# Page setup
# ============================================================

st.set_page_config(
    page_title="NCAA Bayesian · M 2025",
    layout="wide",
    page_icon="🏀",
)

BRAND = {
    "orange": "#FF6B1A",
    "blue": "#185FA5",
    "navy": "#0B1020",
    "gold": "#F4D35E",
    "cream": "#F5F1ED",
    "muted": "#7A8294",
}

pio.templates["mm"] = go.layout.Template(
    layout=dict(
        font=dict(family="Inter, sans-serif", color=BRAND["muted"], size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[
            BRAND["orange"],
            BRAND["blue"],
            BRAND["gold"],
            "#7DC4E4",
            "#E89A6B",
            "#A98ED6",
            "#5BB99A",
            "#E26A6A",
            "#C8B98C",
            "#6F89C9",
            "#D87FB1",
            "#88B07A",
        ],
        xaxis=dict(
            gridcolor="rgba(122,130,148,0.18)",
            zerolinecolor="rgba(122,130,148,0.30)",
        ),
        yaxis=dict(
            gridcolor="rgba(122,130,148,0.18)",
            zerolinecolor="rgba(122,130,148,0.30)",
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(l=50, r=30, t=40, b=50),
    )
)

pio.templates.default = "plotly+mm"


# ============================================================
# Theme-aware CSS
# ============================================================

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800&display=swap');

  :root {
      --text: #1F2230;
      --text-strong: #0D1020;
      --muted: rgba(31, 34, 48, 0.66);
      --surface: rgba(255, 255, 255, 0.72);
      --surface-strong: #FFFFFF;
      --border: rgba(31, 34, 48, 0.14);
      --grid-line: rgba(31, 34, 48, 0.06);
      --metric-bg-1: rgba(255, 107, 26, 0.10);
      --metric-bg-2: rgba(255, 255, 255, 0.85);
      --orange: #FF6B1A;
      --blue: #185FA5;
  }

  @media (prefers-color-scheme: dark) {
      :root {
          --text: #F5F1ED;
          --text-strong: #FFFFFF;
          --muted: rgba(245, 241, 237, 0.70);
          --surface: rgba(20, 27, 47, 0.65);
          --surface-strong: #141B2F;
          --border: rgba(245, 241, 237, 0.12);
          --grid-line: rgba(245, 241, 237, 0.06);
          --metric-bg-1: rgba(255, 107, 26, 0.10);
          --metric-bg-2: rgba(20, 27, 47, 0.70);
      }
  }

  html, body, [class*="css"] {
      font-family: 'Inter', sans-serif;
  }

  .stApp::before {
      content: "";
      position: fixed;
      inset: 0;
      background-image:
          linear-gradient(var(--grid-line) 1px, transparent 1px),
          linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
      background-size: 64px 64px;
      pointer-events: none;
      z-index: 0;
  }

  .stApp::after {
      content: "";
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--orange), var(--blue), var(--orange));
      z-index: 999;
  }

  .block-container {
      position: relative;
      z-index: 1;
      padding-top: 1.4rem;
      padding-bottom: 3rem;
      max-width: 1240px;
  }

  h1, h2, h3, h4 {
      font-family: 'Inter', sans-serif !important;
      letter-spacing: -0.02em;
      color: var(--text-strong) !important;
  }

  h1 { font-weight: 700 !important; }
  h2 { font-weight: 700 !important; }
  h3 { font-weight: 650 !important; }

  .hero {
      background: linear-gradient(135deg, #FF6B1A 0%, #D85A30 48%, #185FA5 100%);
      border-radius: 16px;
      padding: 1.35rem 1.8rem 1.25rem 1.8rem;
      margin-bottom: 1.4rem;
      box-shadow: 0 12px 42px -14px rgba(255, 107, 26, 0.45);
      position: relative;
      overflow: hidden;
  }

  .hero::after {
      content: "";
      position: absolute;
      inset: 0;
      background-image:
          radial-gradient(circle at 88% 30%, rgba(255,255,255,0.25), transparent 38%),
          radial-gradient(circle at 18% 90%, rgba(255,255,255,0.12), transparent 30%);
      pointer-events: none;
  }

  .hero-chip {
      display: inline-block;
      background: rgba(255,255,255,0.22);
      color: #FFFFFF !important;
      font-size: 0.74rem;
      font-weight: 750;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 0.28rem 0.75rem;
      border-radius: 999px;
      margin-bottom: 0.55rem;
      border: 1px solid rgba(255,255,255,0.30);
      position: relative;
      z-index: 1;
  }

  .hero-title {
      font-family: 'Bebas Neue', sans-serif !important;
      font-size: 2.65rem !important;
      letter-spacing: 0.045em !important;
      color: #FFFFFF !important;
      -webkit-text-fill-color: #FFFFFF !important;
      line-height: 1 !important;
      margin: 0 !important;
      text-shadow: 0 2px 14px rgba(0,0,0,0.30);
      position: relative;
      z-index: 1;
  }

  .hero-subtitle {
      color: rgba(255,255,255,0.94) !important;
      font-size: 0.98rem;
      font-weight: 500;
      margin-top: 0.55rem;
      max-width: 860px;
      position: relative;
      z-index: 1;
  }

  .muted {
      color: var(--muted) !important;
      font-size: 1rem;
      font-weight: 400;
      margin-bottom: 1.2rem;
      max-width: 820px;
      line-height: 1.55;
  }

  .section-note {
      color: var(--muted) !important;
      font-size: 0.95rem;
      margin-top: -0.25rem;
      margin-bottom: 1rem;
      max-width: 820px;
      line-height: 1.55;
  }

  .section-rule {
      height: 3px;
      width: 64px;
      background: linear-gradient(90deg, var(--orange), var(--blue));
      border-radius: 2px;
      margin: 1.1rem 0 0.7rem 0;
  }

  [data-testid="stMetric"] {
      background: linear-gradient(180deg, var(--metric-bg-1) 0%, var(--metric-bg-2) 100%);
      border: 1px solid rgba(255, 107, 26, 0.30);
      border-radius: 13px;
      padding: 1rem 1.1rem;
      transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.05);
  }

  [data-testid="stMetric"]:hover {
      transform: translateY(-2px);
      border-color: rgba(255, 107, 26, 0.65);
      box-shadow: 0 12px 28px rgba(255, 107, 26, 0.12);
  }

  [data-testid="stMetricValue"] {
      font-family: 'Bebas Neue', sans-serif !important;
      font-size: 2.05rem !important;
      letter-spacing: 0.02em;
      color: var(--orange) !important;
  }

  [data-testid="stMetricLabel"] {
      color: var(--muted) !important;
      font-size: 0.76rem !important;
      font-weight: 750 !important;
      letter-spacing: 0.08em;
      text-transform: uppercase;
  }

  .stTabs [data-baseweb="tab-list"] {
      gap: 0.3rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 0.4rem;
  }

  .stTabs [data-baseweb="tab"] {
      padding: 0.7rem 1.2rem !important;
      font-weight: 750 !important;
      font-size: 0.92rem !important;
      letter-spacing: 0.06em !important;
      text-transform: uppercase !important;
      color: var(--text) !important;
      opacity: 0.65;
      border-radius: 10px 10px 0 0 !important;
      transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease;
  }

  .stTabs [data-baseweb="tab"] p {
      color: inherit !important;
      font-weight: 750 !important;
      font-size: 0.92rem !important;
  }

  .stTabs [data-baseweb="tab"]:hover {
      opacity: 1;
      color: var(--orange) !important;
      background: rgba(255, 107, 26, 0.08);
  }

  .stTabs [aria-selected="true"] {
      color: var(--orange) !important;
      opacity: 1 !important;
      border-bottom: 3px solid var(--orange) !important;
      background: rgba(255, 107, 26, 0.10);
  }

  .stTabs [aria-selected="true"] p {
      color: var(--orange) !important;
  }

  span[data-baseweb="tag"] {
      background-color: var(--orange) !important;
      color: #FFFFFF !important;
      border-radius: 999px !important;
      font-weight: 650 !important;
  }

  span[data-baseweb="tag"] svg {
      fill: #FFFFFF !important;
  }

  div[data-testid="stDataFrame"] {
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--border);
      box-shadow: 0 8px 24px rgba(0,0,0,0.05);
  }

  .small-card {
      background: linear-gradient(180deg, rgba(255, 107, 26, 0.08), var(--surface));
      border: 1px solid rgba(255, 107, 26, 0.26);
      border-radius: 16px;
      padding: 1rem;
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.06);
      min-height: 105px;
  }

  .small-label {
      color: var(--muted);
      font-size: 0.76rem;
      font-weight: 750;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 0.35rem;
  }

  .small-value {
      color: var(--text-strong);
      font-size: 1.12rem;
      font-weight: 800;
      line-height: 1.15;
      margin-bottom: 0.25rem;
  }

  .small-sub {
      color: var(--muted);
      font-size: 0.86rem;
  }

  .overview-top-card {
      background: linear-gradient(135deg, rgba(255, 107, 26, 0.25), rgba(24, 95, 165, 0.10));
      border: 1px solid rgba(255, 107, 26, 0.36);
      border-radius: 22px;
      padding: 1.15rem;
      min-height: 245px;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
      margin-bottom: 0.8rem;
      transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .overview-top-card:hover {
      transform: translateY(-3px);
      border-color: rgba(255, 107, 26, 0.70);
      box-shadow: 0 16px 38px rgba(255, 107, 26, 0.14);
  }

  .overview-small-top {
      background: linear-gradient(180deg, rgba(255, 107, 26, 0.12), var(--surface));
      border: 1px solid rgba(255, 107, 26, 0.26);
      border-radius: 18px;
      padding: 0.9rem;
      min-height: 158px;
      text-align: center;
      margin-bottom: 0.8rem;
      transition: transform 0.15s ease, border-color 0.15s ease;
  }

  .overview-small-top:hover {
      transform: translateY(-2px);
      border-color: rgba(255, 107, 26, 0.55);
  }

  .overview-weak-card {
      background: linear-gradient(180deg, rgba(24, 95, 165, 0.10), var(--surface));
      border: 1px solid rgba(24, 95, 165, 0.23);
      border-radius: 15px;
      padding: 0.82rem;
      min-height: 108px;
      text-align: center;
      margin-bottom: 0.7rem;
  }

  .team-logo {
      width: 72px;
      height: 72px;
      object-fit: contain;
      display: block;
      margin-bottom: 0.8rem;
      filter: drop-shadow(0 6px 10px rgba(0,0,0,0.18));
  }

  .team-logo-center {
      width: 58px;
      height: 58px;
      object-fit: contain;
      display: block;
      margin-left: auto;
      margin-right: auto;
      margin-bottom: 0.55rem;
      filter: drop-shadow(0 5px 8px rgba(0,0,0,0.16));
  }

  .logo-badge {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--orange), var(--blue));
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 850;
      font-size: 1.25rem;
      margin-bottom: 0.8rem;
      box-shadow: 0 8px 16px rgba(0,0,0,0.16);
  }

  .logo-badge-center {
      width: 58px;
      height: 58px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--orange), var(--blue));
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 850;
      font-size: 1rem;
      margin-left: auto;
      margin-right: auto;
      margin-bottom: 0.55rem;
      box-shadow: 0 7px 14px rgba(0,0,0,0.14);
  }

  .rank-label {
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
  }

  .top-team-name {
      color: var(--text-strong);
      font-size: 1.48rem;
      font-weight: 880;
      line-height: 1.12;
      margin-top: 0.3rem;
  }

  .small-team-name {
      color: var(--text-strong);
      font-size: 0.98rem;
      font-weight: 820;
      line-height: 1.12;
  }

  .card-subtitle {
      color: var(--muted);
      font-size: 0.84rem;
      margin-top: 0.35rem;
  }

  .metric-strip {
      height: 4px;
      width: 70px;
      border-radius: 100px;
      background: linear-gradient(90deg, var(--orange), var(--blue));
      margin-top: 0.4rem;
      margin-bottom: 1.4rem;
  }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# Helper functions
# ============================================================

logo_map = {
    # Top 10
    "Auburn": "https://a.espncdn.com/i/teamlogos/ncaa/500/2.png",
    "Duke": "https://a.espncdn.com/i/teamlogos/ncaa/500/150.png",
    "Florida": "https://a.espncdn.com/i/teamlogos/ncaa/500/57.png",
    "Houston": "https://a.espncdn.com/i/teamlogos/ncaa/500/248.png",
    "Alabama": "https://a.espncdn.com/i/teamlogos/ncaa/500/333.png",
    "Tennessee": "https://a.espncdn.com/i/teamlogos/ncaa/500/2633.png",
    "Texas Tech": "https://a.espncdn.com/i/teamlogos/ncaa/500/2641.png",
    "Maryland": "https://a.espncdn.com/i/teamlogos/ncaa/500/120.png",
    "Iowa St": "https://a.espncdn.com/i/teamlogos/ncaa/500/66.png",
    "Arizona": "https://a.espncdn.com/i/teamlogos/ncaa/500/12.png",

    # Bottom 10
    "MS Valley St": "https://a.espncdn.com/i/teamlogos/ncaa/500/2400.png",
    "Ark Pine Bluff": "https://a.espncdn.com/i/teamlogos/ncaa/500/2029.png",
    "Alabama A&M": "https://a.espncdn.com/i/teamlogos/ncaa/500/2010.png",
    "Chicago St": "https://a.espncdn.com/i/teamlogos/ncaa/500/2130.png",
    "Coppin St": "https://a.espncdn.com/i/teamlogos/ncaa/500/2154.png",
    "MD E Shore": "https://a.espncdn.com/i/teamlogos/ncaa/500/2379.png",
    "Prairie View": "https://a.espncdn.com/i/teamlogos/ncaa/500/2504.png",
    "Canisius": "https://a.espncdn.com/i/teamlogos/ncaa/500/2099.png",
    "New Hampshire": "https://a.espncdn.com/i/teamlogos/ncaa/500/160.png",
    "Citadel": "https://a.espncdn.com/i/teamlogos/ncaa/500/2643.png",
}


def team_initials(team):
    words = str(team).replace("&", " ").replace("-", " ").split()

    if len(words) == 0:
        return "?"

    if len(words) == 1:
        return words[0][:2].upper()

    return "".join(w[0] for w in words[:2]).upper()


def logo_html(team, centered=False):
    url = logo_map.get(team)

    if url is not None:
        klass = "team-logo-center" if centered else "team-logo"
        return f'<img class="{klass}" src="{url}" alt="{team} logo">'

    badge_class = "logo-badge-center" if centered else "logo-badge"
    return f'<div class="{badge_class}">{team_initials(team)}</div>'




def show_small_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div class="small-card">
            <div class="small-label">{html.escape(str(title))}</div>
            <div class="small-value">{html.escape(str(value))}</div>
            <div class="small-sub">{html.escape(str(subtitle))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_top_team_card(row, subtitle="Top title contender"):
    team = str(row["Team"])
    st.markdown(
        f"""
        <div class="overview-top-card">
            {logo_html(team, centered=False)}
            <div class="rank-label">#{int(row["Rank"])}</div>
            <div class="top-team-name">{html.escape(team)}</div>
            <div class="card-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_small_top_card(row):
    team = str(row["Team"])
    st.markdown(
        f"""
        <div class="overview-small-top">
            {logo_html(team, centered=True)}
            <div class="rank-label">#{int(row["Rank"])}</div>
            <div class="small-team-name">{html.escape(team)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_weak_card(row):
    team = str(row["Team"])
    st.markdown(
        f"""
        <div class="overview-weak-card">
            <div class="rank-label">#{int(row["Rank"])}</div>
            <div class="small-team-name">{html.escape(team)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Load model artifacts
# ============================================================

@st.cache_resource
def load():
    idata = az.from_netcdf("idata.nc")

    with open("idata.meta.json") as f:
        meta = json.load(f)

    bracket = pd.read_csv("bracket_advancement.csv")

    post = idata.posterior
    n_teams = len(meta["teams"])

    samples = {
        "off": post["off"].values.reshape(-1, n_teams),
        "def": post["def"].values.reshape(-1, n_teams),
        "baseline": post["baseline"].values.flatten(),
        "hfa": post["hfa"].values.flatten(),
        "sigma": post["sigma_pts"].values.flatten(),
    }

    return meta, samples, bracket


meta, samples, bracket = load()

teams = meta["teams"]
conferences = meta["conferences"]
team_to_conf = meta["team_to_conf"]
season = meta.get("season", 2025)
gender = meta.get("gender", "M")


# ============================================================
# Posterior rating table
# ============================================================

net = samples["off"] + samples["def"]

df = pd.DataFrame(
    {
        "Team": teams,
        "Conference": [conferences[c] for c in team_to_conf],
        "Offense": samples["off"].mean(0),
        "Defense": samples["def"].mean(0),
        "Net": net.mean(0),
        "Net 5%": np.quantile(net, 0.05, axis=0),
        "Net 95%": np.quantile(net, 0.95, axis=0),
    }
)

df["Uncertainty"] = df["Net 95%"] - df["Net 5%"]

df = df.sort_values("Net", ascending=False).reset_index(drop=True)
df["Rank"] = np.arange(1, len(df) + 1)

for col in ["Offense", "Defense", "Net", "Net 5%", "Net 95%", "Uncertainty"]:
    df[col] = df[col].round(2)


# ============================================================
# Header
# ============================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-chip">Bayesian Bracket Forecast</div>
        <h1 class="hero-title">NCAA Bayesian · {gender} {season}</h1>
        <div class="hero-subtitle">
            A March Madness dashboard powered by Bayesian offense / defense ratings,
            posterior predictive simulation, and bracket advancement probabilities.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Team ratings", "Predict", "Bracket", "About"]
)


# ============================================================
# Tab 1: Overview
# ============================================================

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

    st.markdown('<div class="metric-strip"></div>', unsafe_allow_html=True)

    st.markdown("## Teams to watch")
    st.markdown(
        '<div class="section-note">A quick, entertainment-first snapshot of the strongest and weakest teams according to the model.</div>',
        unsafe_allow_html=True,
    )

    top10 = df.head(10).copy()
    bottom10 = df.tail(10).sort_values("Net", ascending=True).copy()

    st.markdown("### 🔥 Strongest teams")

    top3 = top10.head(3)
    top_cols = st.columns(3)

    subtitles = ["Best overall profile", "Major title threat", "Dangerous contender"]

    for i, (_, row) in enumerate(top3.iterrows()):
        with top_cols[i]:
            show_top_team_card(row, subtitle=subtitles[i])

    st.markdown("#### More teams near the top")

    other_top = top10.iloc[3:10].reset_index(drop=True)
    small_cols = st.columns(7)

    for i, (_, row) in enumerate(other_top.iterrows()):
        with small_cols[i]:
            show_small_top_card(row)

    st.markdown("---")

    st.markdown("### ❄️ Weakest teams")
    weak_cols = st.columns(5)

    for i, (_, row) in enumerate(bottom10.iterrows()):
        with weak_cols[i % 5]:
            show_weak_card(row)

    st.info(
        "This overview intentionally hides detailed numbers. "
        "Use Team ratings for custom tables and Predict for head-to-head simulations."
    )


# ============================================================
# Tab 2: Team ratings
# ============================================================

with tab2:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Team Strength Ratings</div>
            <div class="hero-subtitle">
                Net rating summarizes overall team strength. Higher values indicate stronger teams.
                This page keeps the main view simple and lets you create your own table.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    view = df.copy().sort_values("Net", ascending=False).reset_index(drop=True)

    top_team = view.iloc[0]
    most_uncertain = view.sort_values("Uncertainty", ascending=False).iloc[0]
    median_net = view["Net"].median()

    st.markdown("### Quick takeaways")
    st.markdown(
        '<div class="section-note">Only the most useful information is shown upfront.</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)

    with s1:
        show_small_card(
            "Top team",
            top_team["Team"],
            f"Net {top_team['Net']:+.2f}",
        )

    with s2:
        show_small_card(
            "Median Net",
            f"{median_net:+.2f}",
            f"{len(view)} teams included",
        )

    with s3:
        show_small_card(
            "Most uncertain",
            most_uncertain["Team"],
            f"Interval width {most_uncertain['Uncertainty']:.2f}",
        )

    st.markdown("### Net rating ranking")

    top_n = st.slider(
        "Number of teams to show",
        min_value=5,
        max_value=min(50, len(view)),
        value=min(20, len(view)),
        step=5,
    )

    plot_df = view.head(top_n).copy()

    color_values = np.linspace(0.95, 0.35, len(plot_df))
    bar_colors = [f"rgba(255, 104, 31, {v:.2f})" for v in color_values]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=plot_df["Net"],
            y=plot_df["Team"],
            orientation="h",
            marker=dict(color=bar_colors),
            customdata=np.stack(
                [
                    plot_df["Conference"],
                    plot_df["Rank"],
                    plot_df["Net 5%"],
                    plot_df["Net 95%"],
                    plot_df["Uncertainty"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Overall rank: #%{customdata[1]}<br>"
                "Conference: %{customdata[0]}<br>"
                "Net rating: %{x:.2f}<br>"
                "90% interval: [%{customdata[2]:.2f}, %{customdata[3]:.2f}]<br>"
                "Uncertainty width: %{customdata[4]:.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=max(430, top_n * 25),
        xaxis_title="Net rating",
        yaxis_title="",
        margin=dict(l=130, r=30, t=20, b=50),
        showlegend=False,
    )

    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Create your own rating table")
    st.markdown(
        '<div class="section-note">Choose only the columns you want to see. This avoids a large default table.</div>',
        unsafe_allow_html=True,
    )

    available_cols = [
        "Rank",
        "Team",
        "Conference",
        "Offense",
        "Defense",
        "Net",
        "Net 5%",
        "Net 95%",
        "Uncertainty",
    ]

    selected_cols = st.multiselect(
        "Columns to include",
        available_cols,
        default=["Rank", "Team", "Net"],
    )

    if selected_cols:
        custom_table = view[selected_cols].copy()

        st.dataframe(
            custom_table,
            use_container_width=True,
            height=520,
            hide_index=True,
        )

        csv = custom_table.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download this table",
            data=csv,
            file_name="custom_team_ratings.csv",
            mime="text/csv",
        )

    else:
        st.warning("Please select at least one column.")


# ============================================================
# Tab 3: Predict
# ============================================================

with tab3:
    st.markdown(
        "Simulate a hypothetical game using posterior samples. "
        "The margin distribution includes both parameter uncertainty and game-level noise."
    )

    c1, c2, c3 = st.columns([2, 2, 1])

    team_a = c1.selectbox("Team A", teams, index=0)
    team_b = c2.selectbox("Team B", teams, index=1)
    neutral = c3.checkbox("Neutral site", value=True)

    if team_a == team_b:
        st.warning("Pick two different teams.")

    else:
        ia = teams.index(team_a)
        ib = teams.index(team_b)

        rng = np.random.default_rng(0)

        hfa_effect = 0.0 if neutral else samples["hfa"]

        mu_a = (
            samples["baseline"]
            + hfa_effect
            + samples["off"][:, ia]
            - samples["def"][:, ib]
        )

        mu_b = (
            samples["baseline"]
            + samples["off"][:, ib]
            - samples["def"][:, ia]
        )

        pts_a = rng.normal(mu_a, samples["sigma"])
        pts_b = rng.normal(mu_b, samples["sigma"])

        margin = pts_a - pts_b
        win_prob = float((margin > 0).mean())

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(f"P({team_a} wins)", f"{win_prob:.1%}")
        m2.metric("Mean margin", f"{margin.mean():+.1f} pts")
        m3.metric("Expected score", f"{pts_a.mean():.0f} – {pts_b.mean():.0f}")
        m4.metric("Total", f"{(pts_a + pts_b).mean():.1f}")

        fig = go.Figure()

        fig.add_trace(
            go.Histogram(
                x=margin,
                nbinsx=60,
                opacity=0.78,
                name="Margin",
                marker=dict(color="rgba(255, 104, 31, 0.75)"),
            )
        )

        fig.add_vline(
            x=0,
            line_dash="dash",
            annotation_text="tie",
        )

        fig.add_vline(
            x=float(margin.mean()),
            line_dash="dot",
            annotation_text=f"mean {margin.mean():+.1f}",
        )

        fig.update_layout(
            height=420,
            xaxis_title=f"Margin ({team_a} − {team_b}, pts)",
            yaxis_title="Posterior simulations",
            margin=dict(l=50, r=30, t=40, b=50),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tab 4: Bracket
# ============================================================

with tab4:
    st.markdown(
        "Precomputed tournament advancement probabilities from posterior simulation."
    )

    show = bracket.copy()

    pcols = [
        "p_r32",
        "p_sweet16",
        "p_elite8",
        "p_final4",
        "p_champgame",
        "p_champ",
    ]

    for c in pcols:
        show[c] = (show[c] * 100).round(1).astype(str) + "%"

    show = show[["seed", "region", "team"] + pcols]

    show.columns = [
        "Seed",
        "Region",
        "Team",
        "R32",
        "Sweet 16",
        "Elite 8",
        "Final 4",
        "Final",
        "Champion",
    ]

    st.dataframe(
        show,
        use_container_width=True,
        height=540,
        hide_index=True,
    )

    top12 = bracket.head(12)

    rounds_labels = [
        "R32",
        "Sweet 16",
        "Elite 8",
        "Final 4",
        "Final",
        "Champion",
    ]

    fig = go.Figure()

    for _, row in top12.iterrows():
        fig.add_trace(
            go.Scatter(
                x=rounds_labels,
                y=[row[c] for c in pcols],
                mode="lines+markers",
                name=f"{row['seed']} {row['team']}",
                hovertemplate="%{y:.1%}<extra>%{fullData.name}</extra>",
            )
        )

    fig.update_yaxes(tickformat=".0%", range=[0, 1])

    fig.update_layout(
        height=480,
        margin=dict(l=50, r=30, t=30, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tab 5: About
# ============================================================

with tab5:
    st.markdown(
        """
        ### About this model

        This is an interactive companion to the Quarto report.

        The model assigns each team a latent offense and defense rating.
        It uses a Bayesian hierarchical structure, so team ratings are partially pooled by conference.

        A game prediction is computed from posterior samples rather than from a single point estimate.
        Therefore, the predicted margin and win probability reflect both rating uncertainty and game-level randomness.

        The bracket tab uses precomputed tournament simulations based on the posterior draws.
        """
    )