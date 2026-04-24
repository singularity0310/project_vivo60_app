"""
Interactive companion to project.qmd.

Reads three artifacts produced by rendering the qmd:
    idata.nc                posterior samples
    idata.meta.json         team / conference metadata
    bracket_advancement.csv precomputed tournament advancement probabilities

No dependency on data_slim/ or on any model code -- everything the app needs
has already been computed upstream.

Run:  streamlit run app.py
"""

import json
import arviz as az
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="NCAA Bayesian", layout="wide", page_icon="🏀")


# ---------- Load artifacts (cached) ----------

@st.cache_resource
def load():
    idata = az.from_netcdf("idata.nc")
    with open("idata.meta.json") as f:
        meta = json.load(f)
    bracket = pd.read_csv("bracket_advancement.csv")

    # Pull posterior samples once and flatten (chain, draw) -> samples
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
season = meta["season"]


# ---------- Header ----------

st.title("🏀 NCAA Bayesian")
st.caption(
    f"Hierarchical offense/defense ratings · {season} season · "
    f"{len(teams)} teams across {len(conferences)} conferences"
)

tab1, tab2, tab3, tab4 = st.tabs(["Ratings", "Predict", "Bracket", "About"])


# ---------- Tab 1: Ratings ----------

with tab1:
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

    confs_show = st.multiselect(
        "Filter by conference", conferences, default=conferences
    )
    view = df[df["Conference"].isin(confs_show)]
    st.dataframe(view, use_container_width=True, height=600)

    st.caption(
        "Net rating = Offense + Defense. Larger Defense = better "
        "(concedes fewer points). 5%/95% are posterior quantiles."
    )


# ---------- Tab 2: Predict a game ----------

with tab2:
    c1, c2, c3 = st.columns([2, 2, 1])
    team_a = c1.selectbox("Team A (home)", teams, index=0)
    team_b = c2.selectbox("Team B (away)", teams, index=1)
    neutral = c3.checkbox("Neutral site", value=True,
                          help="Unchecks adds home-court advantage for Team A.")

    if team_a == team_b:
        st.warning("Pick two different teams.")
    else:
        ia = teams.index(team_a)
        ib = teams.index(team_b)

        rng = np.random.default_rng(0)
        hfa = 0.0 if neutral else samples["hfa"]

        mu_a = samples["baseline"] + hfa + samples["off"][:, ia] - samples["def"][:, ib]
        mu_b = samples["baseline"]       + samples["off"][:, ib] - samples["def"][:, ia]
        pts_a = rng.normal(mu_a, samples["sigma"])
        pts_b = rng.normal(mu_b, samples["sigma"])
        margin = pts_a - pts_b

        win_prob = float((margin > 0).mean())
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"P({team_a} wins)", f"{win_prob:.1%}")
        m2.metric("Mean margin", f"{margin.mean():+.1f}")
        m3.metric("Expected score",
                  f"{pts_a.mean():.0f} – {pts_b.mean():.0f}")
        m4.metric("Total (O/U)", f"{(pts_a + pts_b).mean():.1f}")

        # Margin distribution
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=margin, nbinsx=60,
            marker=dict(color="#185FA5"), opacity=0.75,
            name="Margin",
        ))
        fig.add_vline(x=0, line_color="#D85A30", line_dash="dash",
                      annotation_text="tie", annotation_position="top")
        fig.add_vline(x=float(margin.mean()), line_color="black",
                      line_dash="dot",
                      annotation_text=f"mean {margin.mean():+.1f}",
                      annotation_position="top right")
        fig.update_layout(
            xaxis_title=f"Margin  ({team_a} − {team_b}, pts)",
            yaxis_title="Count",
            height=380, plot_bgcolor="white",
            margin=dict(l=50, r=30, t=40, b=50), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "The spread of the margin distribution mixes **parameter uncertainty** "
            "(what the true ratings are) with **game-level noise** (how much a "
            "single game deviates from its mean). An overconfident model would "
            "produce a narrow distribution."
        )


# ---------- Tab 3: Bracket ----------

with tab3:
    st.markdown("Precomputed tournament advancement probabilities, from "
                "the posterior simulation in the report.")

    show = bracket.copy()
    pcols = ["p_r32", "p_sweet16", "p_elite8",
             "p_final4", "p_champgame", "p_champ"]
    for c in pcols:
        show[c] = (show[c] * 100).round(1).astype(str) + "%"
    show = show[["seed", "region", "team"] + pcols]
    show.columns = ["Seed", "Region", "Team",
                    "R32", "Sweet 16", "Elite 8",
                    "Final 4", "Final", "Champion"]
    st.dataframe(show, use_container_width=True, height=560, hide_index=True)

    # Top-12 line plot
    top12 = bracket.head(12)
    rounds_labels = ["R32", "Sweet 16", "Elite 8", "Final 4", "Final", "Champion"]

    fig = go.Figure()
    palette = ["#185FA5", "#D85A30", "#1D9E75", "#7F77DD", "#EF9F27",
               "#888780", "#C64A91", "#0097A7", "#F56300", "#6A4C93",
               "#57A773", "#4E4E50"]
    for i, (_, row) in enumerate(top12.iterrows()):
        fig.add_trace(go.Scatter(
            x=rounds_labels,
            y=[row[c] for c in pcols],
            mode="lines+markers",
            name=f"{row['seed']} {row['team']}",
            line=dict(width=1.5, color=palette[i % len(palette)]),
            marker=dict(size=7),
            hovertemplate="%{y:.1%}<extra>%{fullData.name}</extra>",
        ))
    fig.update_yaxes(tickformat=".0%", range=[0, 1],
                     showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig.update_layout(
        height=480, plot_bgcolor="white",
        margin=dict(l=50, r=30, t=30, b=50),
        legend=dict(font=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------- Tab 4: About ----------

with tab4:
    st.markdown(
        """
        ### About this model

        Each team has a latent **offense** and **defense** rating, learned jointly
        from regular-season scores. The expected points in a game are:

        ```
        mu_home = baseline + hfa·is_home + off[home] − def[away]
        mu_away = baseline +                off[away] − def[home]
        ```

        Team ratings are partially pooled toward their conference mean, so
        small-conference teams with thin schedule overlap shrink toward the
        group rather than drifting to extreme values.

        Inference is MCMC (PyMC with the NumPyro/JAX backend). Every prediction
        you see in this app is computed from full posterior samples, so win
        probabilities and margin distributions reflect genuine parameter
        uncertainty, not just point estimates.

        For the full model specification, diagnostics, calibration results on
        the held-out tournament, and the bracket simulation code, see the
        accompanying report.
        """
    )