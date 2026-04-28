"""
Interactive companion to project.qmd.

Reads three artifacts produced by rendering the qmd:
    idata.nc
    idata.meta.json
    bracket_advancement.csv

Run:
    streamlit run app.py
"""

import json
import arviz as az
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# Page setup
# ============================================================

st.set_page_config(
    page_title="NCAA Bayesian · M 2025",
    layout="wide",
    page_icon="🏀",
)


# ============================================================
# Theme-aware CSS
# ============================================================

CSS = """
<style>
  :root {
      --app-bg-card: rgba(255, 255, 255, 0.72);
      --app-bg-soft: rgba(255, 75, 75, 0.08);
      --app-bg-strong: rgba(255, 75, 75, 0.16);
      --app-text-muted: rgba(49, 51, 63, 0.68);
      --app-border: rgba(49, 51, 63, 0.13);
      --app-shadow: rgba(0, 0, 0, 0.08);
      --app-accent: #ff4b4b;
  }

  @media (prefers-color-scheme: dark) {
      :root {
          --app-bg-card: rgba(38, 39, 48, 0.82);
          --app-bg-soft: rgba(255, 75, 75, 0.13);
          --app-bg-strong: rgba(255, 75, 75, 0.22);
          --app-text-muted: rgba(250, 250, 250, 0.64);
          --app-border: rgba(250, 250, 250, 0.13);
          --app-shadow: rgba(0, 0, 0, 0.32);
          --app-accent: #ff4b4b;
      }
  }

  .block-container {
      padding-top: 2.2rem;
      padding-bottom: 3rem;
      max-width: 1200px;
  }

  h1 {
      font-weight: 700 !important;
      letter-spacing: -0.035em;
      margin-bottom: 0.2rem !important;
  }

  h2, h3 {
      font-weight: 650 !important;
      letter-spacing: -0.015em;
  }

  .muted {
      color: var(--app-text-muted);
      font-size: 1.02rem;
      margin-bottom: 1.4rem;
  }

  .section-note {
      color: var(--app-text-muted);
      font-size: 0.95rem;
      margin-top: -0.35rem;
      margin-bottom: 1rem;
  }

  .hero-card {
      background: linear-gradient(
          135deg,
          rgba(255, 75, 75, 0.20),
          rgba(255, 180, 80, 0.12)
      );
      border: 1px solid var(--app-border);
      border-radius: 18px;
      padding: 1.2rem 1.3rem;
      box-shadow: 0 8px 24px var(--app-shadow);
      margin-bottom: 1.2rem;
  }

  .hero-title {
      font-size: 1.15rem;
      font-weight: 750;
      margin-bottom: 0.2rem;
  }

  .hero-subtitle {
      color: var(--app-text-muted);
      font-size: 0.95rem;
  }

  .rating-card {
      border: 1px solid var(--app-border);
      border-radius: 16px;
      padding: 1rem 1.1rem;
      box-shadow: 0 8px 20px var(--app-shadow);
      margin-bottom: 0.75rem;
  }

  .rating-rank {
      font-size: 0.78rem;
      color: var(--app-text-muted);
      font-weight: 650;
      margin-bottom: 0.25rem;
  }

  .rating-team {
      font-size: 1.18rem;
      font-weight: 760;
      line-height: 1.15;
  }

  .rating-conf {
      color: var(--app-text-muted);
      font-size: 0.86rem;
      margin-top: 0.15rem;
      margin-bottom: 0.55rem;
  }

  .rating-net {
      font-size: 1.45rem;
      font-weight: 800;
  }

  .rating-label {
      font-size: 0.78rem;
      color: var(--app-text-muted);
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: 0.04em;
  }

  .small-card {
      background: var(--app-bg-card);
      border: 1px solid var(--app-border);
      border-radius: 16px;
      padding: 1rem;
      box-shadow: 0 6px 18px var(--app-shadow);
      min-height: 105px;
  }

  .small-label {
      color: var(--app-text-muted);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 0.35rem;
  }

  .small-value {
      font-size: 1.12rem;
      font-weight: 780;
      line-height: 1.15;
      margin-bottom: 0.25rem;
  }

  .small-sub {
      color: var(--app-text-muted);
      font-size: 0.86rem;
  }

  [data-testid="stMetricValue"] {
      font-size: 1.7rem;
      font-weight: 650;
  }

  [data-testid="stMetricLabel"] {
      color: var(--app-text-muted);
      font-size: 0.86rem;
  }

  .stTabs [data-baseweb="tab-list"] {
      gap: 1.2rem;
      border-bottom: 1px solid var(--app-border);
  }

  .stTabs [data-baseweb="tab"] {
      padding: 0.7rem 0.15rem 0.65rem 0.15rem;
      font-weight: 650;
      font-size: 0.95rem;
  }

  .stTabs [aria-selected="true"] {
      color: var(--app-accent);
      border-bottom: 2px solid var(--app-accent);
  }

  div[data-testid="stDataFrame"] {
      border-radius: 12px;
      overflow: hidden;
  }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# Helper functions
# ============================================================

def card_bg(net, min_net, max_net):
    """
    Create a red/orange intensity based on net rating.
    Higher Net gets stronger color.
    """
    norm = (net - min_net) / (max_net - min_net + 1e-8)
    opacity = 0.08 + 0.28 * norm
    return f"rgba(255, 75, 75, {opacity:.3f})"


def show_small_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div class="small-card">
            <div class="small-label">{title}</div>
            <div class="small-value">{value}</div>
            <div class="small-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_rating_card(rank, team, conference, net, min_net, max_net):
    bg = card_bg(net, min_net, max_net)
    st.markdown(
        f"""
        <div class="rating-card" style="background:{bg};">
            <div class="rating-rank">#{rank}</div>
            <div class="rating-team">{team}</div>
            <div class="rating-conf">{conference}</div>
            <div class="rating-label">Net rating</div>
            <div class="rating-net">{net:+.2f}</div>
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

df = (
    df.sort_values("Net", ascending=False)
    .reset_index(drop=True)
)

df["Rank"] = np.arange(1, len(df) + 1)

for col in ["Offense", "Defense", "Net", "Net 5%", "Net 95%", "Uncertainty"]:
    df[col] = df[col].round(2)


# ============================================================
# Header
# ============================================================

st.title(f"🏀 NCAA Bayesian · {gender} {season}")

st.markdown(
    """
    <div class="muted">
    Hierarchical offense / defense model · partial pooling by conference · uncertainty-aware predictions.
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

    st.markdown("### Top and bottom of the league")

    left, right = st.columns(2)

    with left:
        st.markdown("**Strongest 10 teams**")
        top = df.head(10)[["Rank", "Team", "Conference", "Net"]]
        st.dataframe(top, use_container_width=True, height=390, hide_index=True)

    with right:
        st.markdown("**Weakest 10 teams**")
        bottom = (
            df.tail(10)
            .sort_values("Net", ascending=True)[["Rank", "Team", "Conference", "Net"]]
        )
        st.dataframe(bottom, use_container_width=True, height=390, hide_index=True)

    st.info(
        "The app reports posterior summaries from a Bayesian hierarchical model. "
        "Team offense and defense ratings are partially pooled by conference, so predictions account for both team strength and uncertainty."
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
                Use the filter to focus on specific conferences.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
        view = view.sort_values("Net", ascending=False).reset_index(drop=True)
        view["Filtered Rank"] = np.arange(1, len(view) + 1)

        min_net = float(view["Net"].min())
        max_net = float(view["Net"].max())

        top_team = view.iloc[0]
        most_uncertain = view.sort_values("Uncertainty", ascending=False).iloc[0]
        median_net = view["Net"].median()

        # ----------------------------------------------------
        # Summary cards
        # ----------------------------------------------------

        st.markdown("### Quick takeaways")
        st.markdown(
            '<div class="section-note">The page focuses on the most useful information: ranking, Net rating, and uncertainty.</div>',
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
                f"{len(view)} teams selected",
            )

        with s3:
            show_small_card(
                "Most uncertain",
                most_uncertain["Team"],
                f"Interval width {most_uncertain['Uncertainty']:.2f}",
            )

        # ----------------------------------------------------
        # Color cards
        # ----------------------------------------------------

        st.markdown("### Highest-rated teams")
        st.markdown(
            '<div class="section-note">Color intensity reflects Net rating. Stronger teams appear in darker red blocks.</div>',
            unsafe_allow_html=True,
        )

        n_cards = min(6, len(view))
        card_df = view.head(n_cards)

        cols = st.columns(3)

        for i, row in card_df.iterrows():
            with cols[i % 3]:
                show_rating_card(
                    rank=int(row["Filtered Rank"]),
                    team=row["Team"],
                    conference=row["Conference"],
                    net=float(row["Net"]),
                    min_net=min_net,
                    max_net=max_net,
                )

        # ----------------------------------------------------
        # Top-N chart
        # ----------------------------------------------------

        st.markdown("### Net rating ranking")

        max_slider = min(40, len(view))
        default_n = min(20, len(view))

        top_n = st.slider(
            "Number of teams to show",
            min_value=5,
            max_value=max_slider,
            value=default_n,
            step=5,
        )

        plot_df = view.head(top_n).copy()

        color_values = np.linspace(0.95, 0.35, len(plot_df))
        bar_colors = [
            f"rgba(255, 75, 75, {v:.2f})"
            for v in color_values
        ]

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

        # ----------------------------------------------------
        # Compact table
        # ----------------------------------------------------

        st.markdown("### Compact list")

        compact = plot_df[
            ["Filtered Rank", "Team", "Conference", "Net"]
        ].rename(columns={"Filtered Rank": "Rank"})

        st.dataframe(
            compact,
            use_container_width=True,
            height=360,
            hide_index=True,
        )

        # ----------------------------------------------------
        # Optional full table
        # ----------------------------------------------------

        with st.expander("View full rating table"):
            full_view = view[
                [
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
            ]

            st.dataframe(
                full_view,
                use_container_width=True,
                height=520,
                hide_index=True,
            )

        csv = view.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download filtered ratings",
            data=csv,
            file_name="team_ratings.csv",
            mime="text/csv",
        )


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
                marker=dict(color="rgba(255, 75, 75, 0.75)"),
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