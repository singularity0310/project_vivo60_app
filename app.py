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

  html, body, [class*="css"] {
      font-family: 'Inter', sans-serif;
  }

  .block-container {
      padding-top: 1.4rem;
      padding-bottom: 3rem;
      max-width: 1240px;
  }

  .hero {
      background: linear-gradient(135deg, #FF6B1A 0%, #D85A30 45%, #185FA5 100%);
      border-radius: 16px;
      padding: 1.8rem 2rem 1.6rem 2rem;
      margin-bottom: 1.8rem;
      box-shadow: 0 10px 40px -10px rgba(255, 107, 26, 0.35);
  }
  .hero-title {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 3.2rem;
      letter-spacing: 0.04em;
      color: #FFFFFF;
      line-height: 1;
      margin: 0;
      text-shadow: 0 2px 12px rgba(0,0,0,0.25);
  }
  .hero-subtitle {
      color: rgba(255,255,255,0.92);
      font-size: 1.02rem;
      font-weight: 500;
      margin-top: 0.55rem;
      letter-spacing: 0.005em;
      max-width: 820px;
  }
  .hero-chip {
      display: inline-block;
      background: rgba(255,255,255,0.18);
      backdrop-filter: blur(4px);
      color: #FFFFFF;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 0.28rem 0.7rem;
      border-radius: 999px;
      margin-bottom: 0.6rem;
  }

  h1, h2, h3 {
      font-family: 'Inter', sans-serif;
      letter-spacing: -0.02em;
  }
  h2 { font-weight: 700 !important; }
  h3 { font-weight: 650 !important; }

  [data-testid="stMetric"] {
      background: linear-gradient(180deg, rgba(255,107,26,0.08) 0%, rgba(20,27,47,0.6) 100%);
      border: 1px solid rgba(255,107,26,0.25);
      border-radius: 12px;
      padding: 1rem 1.1rem;
      box-shadow: 0 4px 20px -8px rgba(0,0,0,0.5);
      transition: transform 0.15s ease, border-color 0.15s ease;
  }
  [data-testid="stMetric"]:hover {
      transform: translateY(-2px);
      border-color: rgba(255,107,26,0.55);
  }
  [data-testid="stMetricValue"] {
      font-family: 'Bebas Neue', sans-serif !important;
      font-size: 2.1rem !important;
      letter-spacing: 0.02em;
      color: #FF6B1A !important;
  }
  [data-testid="stMetricLabel"] {
      color: rgba(245,241,237,0.72) !important;
      font-size: 0.78rem !important;
      font-weight: 600 !important;
      letter-spacing: 0.06em;
      text-transform: uppercase;
  }

  .stTabs [data-baseweb="tab-list"] {
      gap: 0.4rem;
      border-bottom: 1px solid rgba(245,241,237,0.1);
      padding-bottom: 0;
  }
  .stTabs [data-baseweb="tab"] {
      padding: 0.75rem 1.1rem;
      font-weight: 700;
      font-size: 0.92rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: rgba(245,241,237,0.6);
      border-radius: 10px 10px 0 0;
      transition: color 0.15s ease, background 0.15s ease;
  }
  .stTabs [data-baseweb="tab"]:hover {
      color: #FF6B1A;
      background: rgba(255,107,26,0.06);
  }
  .stTabs [aria-selected="true"] {
      color: #FF6B1A !important;
      border-bottom: 3px solid #FF6B1A !important;
      background: rgba(255,107,26,0.08);
  }

  div[data-testid="stDataFrame"] {
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(245,241,237,0.08);
  }

  div[data-testid="stAlert"] {
      border-radius: 12px;
      border-left: 4px solid #FF6B1A;
  }

  .muted {
      color: rgba(245,241,237,0.65);
      font-size: 1rem;
      font-weight: 400;
      margin-bottom: 1.2rem;
      max-width: 780px;
      line-height: 1.55;
  }

  .section-rule {
      height: 3px;
      width: 56px;
      background: linear-gradient(90deg, #FF6B1A, #185FA5);
      border-radius: 2px;
      margin: 1.6rem 0 0.6rem 0;
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
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Filter the posterior team ratings by conference. '
        'Net rating is offense plus defense; larger values indicate stronger teams.</div>',
        unsafe_allow_html=True,
    )

    confs_show = st.multiselect(
        "Filter by conference",
        conferences,
        default=conferences,
    )

    view = df[df["Conference"].isin(confs_show)]
    st.dataframe(view, use_container_width=True, height=620)

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

    c1, c2, c3 = st.columns([2, 2, 1])
    team_a = c1.selectbox("Team A", teams, index=0)
    team_b = c2.selectbox("Team B", [t for t in teams if t != team_a], index=0)
    neutral = c3.checkbox("Neutral site", value=True)

    ia = teams.index(team_a)
    ib = teams.index(team_b)

    rng = np.random.default_rng(0)
    hfa_effect = 0.0 if neutral else samples["hfa"]

    mu_a = samples["baseline"] + hfa_effect + samples["off"][:, ia] - samples["def"][:, ib]
    mu_b = samples["baseline"]              + samples["off"][:, ib] - samples["def"][:, ia]
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
    fig.add_trace(go.Histogram(
        x=margin, nbinsx=60, opacity=0.85, name="Margin",
        marker_color=BRAND["orange"], marker_line_width=0,
    ))
    fig.add_vline(x=0, line_dash="dash", line_color=BRAND["muted"],
                  annotation_text="tie")
    fig.add_vline(
        x=float(margin.mean()),
        line_dash="dot", line_color=BRAND["gold"],
        annotation_text=f"mean {margin.mean():+.1f}",
    )
    fig.update_layout(
        height=420,
        xaxis_title=f"Margin ({team_a} − {team_b}, pts)",
        yaxis_title="Posterior simulations",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


with tab4:
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Precomputed tournament advancement probabilities '
        'from posterior simulation.</div>',
        unsafe_allow_html=True,
    )

    show = bracket.copy()
    pcols = ["p_r32", "p_sweet16", "p_elite8", "p_final4", "p_champgame", "p_champ"]
    for c in pcols:
        show[c] = (show[c] * 100).round(1).astype(str) + "%"

    show = show[["seed", "region", "team"] + pcols]
    show.columns = [
        "Seed", "Region", "Team",
        "R32", "SWEET 16", "ELITE 8", "FINAL 4", "FINAL", "CHAMPION",
    ]
    st.dataframe(show, use_container_width=True, height=540, hide_index=True)

    top12 = bracket.head(12)
    rounds_labels = ["R32", "SWEET 16", "ELITE 8", "FINAL 4", "FINAL", "CHAMPION"]

    fig = go.Figure()
    for _, row in top12.iterrows():
        fig.add_trace(go.Scatter(
            x=rounds_labels,
            y=[row[c] for c in pcols],
            mode="lines+markers",
            name=f"{row['seed']} {row['team']}",
            hovertemplate="%{y:.1%}<extra>%{fullData.name}</extra>",
        ))
    fig.update_traces(line=dict(width=2.2),
                      marker=dict(size=7, line=dict(width=1, color=BRAND["navy"])))
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig.update_layout(height=480)
    st.plotly_chart(fig, use_container_width=True)


with tab5:
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        ### About this model

        This is an interactive companion to the Quarto report. The model assigns
        each team a latent offense and defense rating and uses a Bayesian
        hierarchical structure to partially pool ratings by conference.

        A game prediction is computed from posterior samples rather than from a
        single point estimate. Therefore, the predicted margin and win
        probability reflect both rating uncertainty and game-level randomness.

        The bracket tab uses precomputed tournament simulations based on the
        posterior draws.
        """
    )