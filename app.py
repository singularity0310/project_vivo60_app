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
import streamlit as st

st.set_page_config(page_title="NCAA Bayesian · M 2025", layout="wide", page_icon="🏀")

CSS = """
<style>
  .block-container {
      padding-top: 2.2rem;
      padding-bottom: 3rem;
      max-width: 1200px;
  }
  h1 {
      font-weight: 650 !important;
      letter-spacing: -0.035em;
      margin-bottom: 0.2rem !important;
  }
  h2, h3 {
      font-weight: 600 !important;
      letter-spacing: -0.015em;
  }
  .muted {
      color: rgba(250,250,250,0.62);
      font-size: 1.02rem;
      margin-bottom: 1.4rem;
  }
  [data-testid="stMetricValue"] {
      font-size: 1.7rem;
      font-weight: 650;
  }
  [data-testid="stMetricLabel"] {
      color: rgba(250,250,250,0.58);
      font-size: 0.86rem;
  }
  .stTabs [data-baseweb="tab-list"] {
      gap: 1.2rem;
      border-bottom: 1px solid rgba(250,250,250,0.15);
  }
  .stTabs [data-baseweb="tab"] {
      padding: 0.7rem 0.15rem 0.65rem 0.15rem;
      font-weight: 650;
      font-size: 0.95rem;
  }
  .stTabs [aria-selected="true"] {
      color: #ff4b4b;
      border-bottom: 2px solid #ff4b4b;
  }
  div[data-testid="stDataFrame"] {
      border-radius: 12px;
      overflow: hidden;
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


st.title(f"🏀 NCAA Bayesian · {gender} {season}")
st.markdown(
    '<div class="muted">Hierarchical offense / defense model · partial pooling by conference · uncertainty-aware predictions.</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Team ratings", "Predict", "Bracket", "About"]
)

net = samples["off"] + samples["def"]
df = pd.DataFrame({
    "Team": teams,
    "Conference": [conferences[c] for c in team_to_conf],
    "Offense": samples["off"].mean(0).round(2),
    "Defense": samples["def"].mean(0).round(2),
    "Net": net.mean(0).round(2),
    "Net 5%": np.quantile(net, 0.05, axis=0).round(2),
    "Net 95%": np.quantile(net, 0.95, axis=0).round(2),
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
        "Team offense and defense ratings are partially pooled by conference, so predictions account for both team strength and uncertainty."
    )


with tab2:
    st.markdown(
        "Filter the posterior team ratings by conference. Net rating is offense plus defense; larger values indicate stronger teams."
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
    st.markdown(
        "Simulate a hypothetical game using posterior samples. The margin distribution includes both parameter uncertainty and game-level noise."
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

        mu_a = samples["baseline"] + hfa_effect + samples["off"][:, ia] - samples["def"][:, ib]
        mu_b = samples["baseline"] + samples["off"][:, ib] - samples["def"][:, ia]
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
        fig.add_trace(go.Histogram(x=margin, nbinsx=60, opacity=0.78, name="Margin"))
        fig.add_vline(x=0, line_dash="dash", annotation_text="tie")
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


with tab4:
    st.markdown(
        "Precomputed tournament advancement probabilities from posterior simulation."
    )

    show = bracket.copy()
    pcols = ["p_r32", "p_sweet16", "p_elite8", "p_final4", "p_champgame", "p_champ"]
    for c in pcols:
        show[c] = (show[c] * 100).round(1).astype(str) + "%"

    show = show[["seed", "region", "team"] + pcols]
    show.columns = [
        "Seed", "Region", "Team", "R32", "Sweet 16", "Elite 8",
        "Final 4", "Final", "Champion"
    ]

    st.dataframe(show, use_container_width=True, height=540, hide_index=True)

    top12 = bracket.head(12)
    rounds_labels = ["R32", "Sweet 16", "Elite 8", "Final 4", "Final", "Champion"]

    fig = go.Figure()
    for _, row in top12.iterrows():
        fig.add_trace(go.Scatter(
            x=rounds_labels,
            y=[row[c] for c in pcols],
            mode="lines+markers",
            name=f"{row['seed']} {row['team']}",
            hovertemplate="%{y:.1%}<extra>%{fullData.name}</extra>",
        ))

    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig.update_layout(height=480, margin=dict(l=50, r=30, t=30, b=50))
    st.plotly_chart(fig, use_container_width=True)


with tab5:
    st.markdown(
        """
        ### About this model

        This is an interactive companion to the Quarto report. The model assigns each team a latent
        offense and defense rating and uses a Bayesian hierarchical structure to partially pool ratings
        by conference.

        A game prediction is computed from posterior samples rather than from a single point estimate.
        Therefore, the predicted margin and win probability reflect both rating uncertainty and
        game-level randomness.

        The bracket tab uses precomputed tournament simulations based on the posterior draws.
        """
    )
