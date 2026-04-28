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
      --app-orange: #ff681f;
      --app-blue: #2f6fed;
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
          rgba(255, 104, 31, 0.18),
          rgba(47, 111, 237, 0.10)
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

  .overview-top-card {
      background: linear-gradient(
          135deg,
          rgba(255, 104, 31, 0.28),
          rgba(255, 190, 70, 0.12)
      );
      border: 1px solid rgba(255, 104, 31, 0.34);
      border-radius: 22px;
      padding: 1.15rem;
      min-height: 235px;
      box-shadow: 0 12px 30px var(--app-shadow);
      margin-bottom: 0.8rem;
  }

  .overview-small-top {
      background: rgba(255, 104, 31, 0.12);
      border: 1px solid rgba(255, 104, 31, 0.23);
      border-radius: 18px;
      padding: 0.9rem;
      min-height: 155px;
      text-align: center;
      margin-bottom: 0.8rem;
  }

  .overview-weak-card {
      background: rgba(47, 111, 237, 0.10);
      border: 1px solid rgba(47, 111, 237, 0.20);
      border-radius: 15px;
      padding: 0.82rem;
      min-height: 108px;
      text-align: center;
      margin-bottom: 0.7rem;
  }

  .team-logo {
      width: 68px;
      height: 68px;
      object-fit: contain;
      display: block;
      margin-bottom: 0.8rem;
  }

  .team-logo-center {
      width: 56px;
      height: 56px;
      object-fit: contain;
      display: block;
      margin-left: auto;
      margin-right: auto;
      margin-bottom: 0.55rem;
  }

  .logo-badge {
      width: 68px;
      height: 68px;
      border-radius: 50%;
      background: linear-gradient(135deg, rgba(255,104,31,0.92), rgba(47,111,237,0.88));
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 850;
      font-size: 1.25rem;
      margin-bottom: 0.8rem;
  }

  .logo-badge-center {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, rgba(255,104,31,0.92), rgba(47,111,237,0.88));
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 850;
      font-size: 1rem;
      margin-left: auto;
      margin-right: auto;
      margin-bottom: 0.55rem;
  }

  .rank-label {
      color: var(--app-text-muted);
      font-size: 0.82rem;
      font-weight: 800;
      letter-spacing: 0.03em;
  }

  .top-team-name {
      font-size: 1.45rem;
      font-weight: 880;
      line-height: 1.12;
      margin-top: 0.3rem;
  }

  .small-team-name {
      font-size: 0.98rem;
      font-weight: 820;
      line-height: 1.12;
  }

  .card-subtitle {
      color: var(--app-text-muted);
      font-size: 0.84rem;
      margin-top: 0.35rem;
  }

  .metric-strip {
      height: 4px;
      width: 65px;
      border-radius: 100px;
      background: linear-gradient(90deg, var(--app-orange), var(--app-blue));
      margin-top: 0.4rem;
      margin-bottom: 1.4rem;
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
      color: var(--app-orange);
      border-bottom: 2px solid var(--app-orange);
  }

  [data-testid="stMetricValue"] {
      font-size: 1.7rem;
      font-weight: 750;
      color: var(--app-orange);
  }

  [data-testid="stMetricLabel"] {
      color: var(--app-text-muted);
      font-size: 0.86rem;
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