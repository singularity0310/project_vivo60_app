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
import time

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
    page_title="March Madness Forecast · 2025",
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
# Full-screen intro overlay (only on first load)
# ============================================================

if "intro_played" not in st.session_state:
    st.session_state.intro_played = False

if not st.session_state.intro_played:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;700;800&display=swap');

          @keyframes overlayFadeOut {
              0%, 75% { opacity: 1; }
              100%    { opacity: 0; visibility: hidden; }
          }
          @keyframes ballBounce {
              0%, 100% { transform: translateY(0) rotate(0deg); }
              25%      { transform: translateY(-40px) rotate(90deg); }
              50%      { transform: translateY(0) rotate(180deg); }
              75%      { transform: translateY(-25px) rotate(270deg); }
          }
          @keyframes titleRise {
              from { opacity: 0; transform: translateY(30px); }
              to   { opacity: 1; transform: translateY(0); }
          }
          @keyframes subtitleFade {
              0%, 30% { opacity: 0; transform: translateY(15px); }
              100%    { opacity: 1; transform: translateY(0); }
          }
          @keyframes dotPulse {
              0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
              40%           { opacity: 1; transform: scale(1.15); }
          }
          @keyframes bgShift {
              0%   { background-position: 0% 50%; }
              50%  { background-position: 100% 50%; }
              100% { background-position: 0% 50%; }
          }

          .intro-overlay {
              position: fixed;
              top: 0; left: 0; right: 0; bottom: 0;
              background: linear-gradient(135deg, #FF6B1A 0%, #D85A30 35%, #185FA5 100%);
              background-size: 200% 200%;
              animation:
                  bgShift 6s ease-in-out infinite,
                  overlayFadeOut 4.0s ease-in-out forwards;
              z-index: 9999;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              text-align: center;
          }

          .intro-overlay::before {
              content: "";
              position: absolute;
              inset: 0;
              background-image:
                  radial-gradient(circle at 22% 18%, rgba(255,255,255,0.15), transparent 35%),
                  radial-gradient(circle at 80% 82%, rgba(255,255,255,0.10), transparent 30%);
              pointer-events: none;
          }

          .intro-ball {
              font-size: 5.5rem;
              animation: ballBounce 1.4s ease-in-out infinite;
              margin-bottom: 1.5rem;
              filter: drop-shadow(0 8px 18px rgba(0,0,0,0.35));
          }

          .intro-chip {
              display: inline-block;
              background: rgba(255,255,255,0.22);
              color: #FFFFFF;
              font-family: 'Inter', sans-serif;
              font-size: 0.8rem;
              font-weight: 750;
              letter-spacing: 0.18em;
              text-transform: uppercase;
              padding: 0.35rem 1rem;
              border-radius: 999px;
              margin-bottom: 1rem;
              border: 1px solid rgba(255,255,255,0.32);
              animation: subtitleFade 1.4s ease-out 0.2s both;
          }

          .intro-title {
              font-family: 'Bebas Neue', sans-serif;
              font-size: 4.2rem;
              letter-spacing: 0.06em;
              color: #FFFFFF;
              margin: 0 0 0.6rem 0;
              line-height: 1;
              text-shadow: 0 4px 24px rgba(0,0,0,0.35);
              animation: titleRise 1s cubic-bezier(0.16, 1, 0.3, 1) both;
          }

          .intro-sub {
              font-family: 'Inter', sans-serif;
              color: rgba(255,255,255,0.94);
              font-size: 1.15rem;
              font-weight: 500;
              max-width: 560px;
              margin-bottom: 1.8rem;
              animation: subtitleFade 1.6s ease-out 0.5s both;
          }

          .intro-dots {
              display: flex;
              gap: 0.6rem;
              animation: subtitleFade 1.4s ease-out 1.0s both;
          }

          .intro-dots span {
              width: 11px;
              height: 11px;
              border-radius: 50%;
              background: rgba(255,255,255,0.85);
              animation: dotPulse 1.4s ease-in-out infinite;
          }

          .intro-dots span:nth-child(1) { animation-delay: 0s; }
          .intro-dots span:nth-child(2) { animation-delay: 0.2s; }
          .intro-dots span:nth-child(3) { animation-delay: 0.4s; }

          @media (max-width: 640px) {
              .intro-title  { font-size: 2.6rem; }
              .intro-sub    { font-size: 0.95rem; padding: 0 1rem; }
              .intro-ball   { font-size: 4rem; }
          }
        </style>

        <div class="intro-overlay">
            <div class="intro-ball">🏀</div>
            <div class="intro-chip">March Madness Forecast</div>
            <h1 class="intro-title">SIMULATING THE BRACKET</h1>
            <div class="intro-sub">Running 4,000 posterior simulations of the tournament&hellip;</div>
            <div class="intro-dots"><span></span><span></span><span></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Match the overlay total animation duration (4.0s)
    time.sleep(4.0)
    st.session_state.intro_played = True
    st.rerun()


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

  /* ========== Hero entrance animations after intro ========== */

  @keyframes heroSlideDown {
      from { transform: translateY(-50px); opacity: 0; }
      to   { transform: translateY(0); opacity: 1; }
  }

  @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(15px); }
      to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes contentRiseUp {
      from { opacity: 0; transform: translateY(30px); }
      to   { opacity: 1; transform: translateY(0); }
  }

  .hero {
      background: linear-gradient(135deg, #FF6B1A 0%, #D85A30 48%, #185FA5 100%);
      border-radius: 16px;
      padding: 1.25rem 1.8rem;
      margin-bottom: 1.4rem;
      box-shadow: 0 12px 42px -14px rgba(255, 107, 26, 0.45);
      position: relative;
      overflow: hidden;
      animation: heroSlideDown 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
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

  .app-hero-title {
      font-family: 'Bebas Neue', sans-serif !important;
      font-size: 2.75rem !important;
      letter-spacing: 0.045em !important;
      color: #FFFFFF !important;
      -webkit-text-fill-color: #FFFFFF !important;
      line-height: 1 !important;
      margin: 0 !important;
      text-shadow: 0 2px 14px rgba(0,0,0,0.30);
      position: relative;
      z-index: 1;
  }

  .stTabs {
      animation: contentRiseUp 0.9s ease-out 0.5s both;
  }

  .hero-card {
      background: linear-gradient(135deg, rgba(255, 107, 26, 0.13), rgba(24, 95, 165, 0.08));
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.05rem 1.25rem;
      margin-bottom: 1.2rem;
      box-shadow: 0 8px 22px rgba(0,0,0,0.05);
  }

  .hero-card-title {
      color: var(--text-strong) !important;
      font-size: 1.25rem;
      font-weight: 800;
      margin-bottom: 0.25rem;
  }

  .hero-card-subtitle {
      color: var(--muted) !important;
      font-size: 0.95rem;
      line-height: 1.5;
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
        return f'<img class="{klass}" src="{url}" alt="{html.escape(team)} logo">'

    badge_class = "logo-badge-center" if centered else "logo-badge"
    return f'<div class="{badge_class}">{html.escape(team_initials(team))}</div>'


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
        <h1 class="app-hero-title">🏀 March Madness Forecast · {season}</h1>
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

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

    st.markdown("## Who looks dangerous?")
    st.markdown(
        '<div class="section-note">A quick look at the teams the model likes most — and least.</div>',
        unsafe_allow_html=True,
    )

    top10 = df.head(10).copy()
    bottom10 = df.tail(10).sort_values("Net", ascending=True).copy()

    title_col, help_col = st.columns([5, 2])

    with title_col:
        st.markdown("### 🔥 Strongest teams")

    with help_col:
        with st.expander("What does strong mean?"):
            st.write(
                "A stronger team has a higher Net rating. "
                "Net combines the team's estimated offense and defense into one overall strength score."
            )

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

    st.markdown("### ❄️ Long shots")
    weak_cols = st.columns(5)

    for i, (_, row) in enumerate(bottom10.iterrows()):
        with weak_cols[i % 5]:
            show_weak_card(row)


# ============================================================
# Tab 2: Team ratings
# ============================================================

with tab2:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-card-title">Team Strength Ratings</div>
            <div class="hero-card-subtitle">
                See which teams look strongest in the model. Higher rating means a stronger team.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    view = df.copy().sort_values("Net", ascending=False).reset_index(drop=True)

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
        '<div class="section-note">Choose the columns you want to include.</div>',
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
        "Pick two teams and simulate a possible matchup. "
        "The chart shows the range of possible point margins."
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
            yaxis_title="Simulated games",
            margin=dict(l=50, r=30, t=40, b=50),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tab 4: Bracket
# ============================================================

with tab4:
    # ---- Load seed information ----
    seeds_raw = pd.read_csv("data_slim/MNCAATourneySeeds.csv")
    seeds_df = seeds_raw[seeds_raw.Season == season].copy()
    seeds_df["region"]   = seeds_df.Seed.str[0]
    seeds_df["seed_num"] = seeds_df.Seed.str[1:3].astype(int)
    
    # Map TeamID -> team name (team_ids is in meta)
    id_to_name = dict(zip(meta["team_ids"], teams))
    seeds_df["team"] = seeds_df.TeamID.map(id_to_name)
    seeds_df = seeds_df.dropna(subset=["team"])
    
    # Map team -> net rating from df (which is already sorted by rank)
    team_to_net = dict(zip(df.Team, df.Net))
    seeds_df["net"] = seeds_df.team.map(team_to_net)
    
    # ---- Build the bracket: simulate each round, pick higher net rating ----
    R1_PAIRS = [(1, 16), (8, 9), (5, 12), (4, 13),
                (6, 11), (3, 14), (7, 10), (2, 15)]
    REGIONS = ["W", "X", "Y", "Z"]
    REGION_NAMES = {"W": "South", "X": "East", "Y": "Midwest", "Z": "West"}
    
    def pick_winner(team_a_dict, team_b_dict):
        """Higher net rating wins. Returns the winner dict."""
        if team_a_dict is None: return team_b_dict
        if team_b_dict is None: return team_a_dict
        return team_a_dict if team_a_dict["net"] > team_b_dict["net"] else team_b_dict
    
    def get_seed_team(region, seed_num):
        """Return dict for the team with given seed in given region."""
        sub = seeds_df[(seeds_df.region == region) & (seeds_df.seed_num == seed_num)]
        if len(sub) == 0:
            return None
        # If two teams share a seed (First Four), pick higher net
        rows = sub.to_dict("records")
        if len(rows) == 1:
            return rows[0]
        return pick_winner(rows[0], rows[1])
    
    # Build region brackets
    region_results = {}  # region -> list of rounds, each round is list of winners
    for region in REGIONS:
        # Round 1: 8 games
        r1 = []
        for hi, lo in R1_PAIRS:
            winner = pick_winner(get_seed_team(region, hi), get_seed_team(region, lo))
            r1.append(winner)
        # Round 2: 4 games
        r2 = [pick_winner(r1[i], r1[i+1]) for i in range(0, 8, 2)]
        # Sweet 16: 2 games
        s16 = [pick_winner(r2[i], r2[i+1]) for i in range(0, 4, 2)]
        # Elite 8: 1 game (regional final)
        e8 = pick_winner(s16[0], s16[1])
        region_results[region] = {
            "r1": r1, "r2": r2, "s16": s16, "e8": e8
        }
    
    # Final Four: W vs X, Y vs Z
    f4_a = pick_winner(region_results["W"]["e8"], region_results["X"]["e8"])
    f4_b = pick_winner(region_results["Y"]["e8"], region_results["Z"]["e8"])
    champion = pick_winner(f4_a, f4_b)
    
    # ---- Headline ----
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-card-title">🏆 Predicted bracket</div>
            <div class="hero-card-subtitle">
                Each game's winner is the team with the higher Net rating. 
                Predicted champion: <b>{champion['team']}</b> (#{champion['seed_num']} {REGION_NAMES[champion['region']]}).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # ---- Draw the bracket using plotly ----
    fig = go.Figure()
    
    # Coordinate system: x = round (0=R64, 6=champion), y = vertical position
    # Left side: regions W and X (top to bottom: W on top, X on bottom)
    # Right side: regions Y and Z  
    # We mirror the right side (rounds go right-to-left from x=6)
    
    def add_game_box(fig, x, y, team_dict, won=False):
        """Add a single game-result box at position (x, y)."""
        if team_dict is None:
            label = "?"
            seed_str = ""
        else:
            label = team_dict["team"]
            seed_str = f"#{team_dict['seed_num']}"
        
        color = "#FF6B1A" if won else "#185FA5"
        bgcolor = "rgba(255, 107, 26, 0.15)" if won else "rgba(24, 95, 165, 0.10)"
        
        fig.add_shape(
            type="rect",
            x0=x - 0.45, y0=y - 0.18,
            x1=x + 0.45, y1=y + 0.18,
            line=dict(color=color, width=1.5),
            fillcolor=bgcolor,
        )
        fig.add_annotation(
            x=x, y=y,
            text=f"<b>{seed_str}</b> {label}",
            showarrow=False,
            font=dict(size=10, color="#1F2230"),
        )
    
    # Draw left half (W on top, X on bottom)
    # Round 1: 16 teams (8 per region)
    # Round positions: x=0 R64, x=1 R32, x=2 S16, x=3 E8, x=4 F4, x=5 final, x=6 champion
    
    # ---- Layout: each region has 16 R64 slots ----
    # We draw W in y from 30 down to 0
    # Then X in y from -1 down to -31
    # Right side: Y from 30 down to 0, Z from -1 down to -31, mirrored x
    
    # Helper: y position for R64 game in a region (8 games)
    def y_pos(region_idx, game_in_round, total_in_round):
        """Region 0,1,2,3 = W, X, Y, Z. Returns y for game_in_round of total."""
        region_height = 8  # 8 games per region in R1
        # Vertical span per region: 16 units (with some padding)
        spacing = 16 / total_in_round
        offset_within = (game_in_round + 0.5) * spacing
        if region_idx == 0:    # W: y in [16, 32]
            return 32 - offset_within
        elif region_idx == 1:  # X: y in [0, 16]
            return 16 - offset_within
        elif region_idx == 2:  # Y: y in [16, 32]
            return 32 - offset_within
        else:                  # Z: y in [0, 16]
            return 16 - offset_within
    
    REGION_X_LEFT  = [0, 1, 2, 3]   # x for R64, R32, S16, E8 on left half
    REGION_X_RIGHT = [6, 5, 4, 3]   # x for R64, R32, S16, E8 on right half (mirrored)
    F4_X = [4, 4]                   # F4 game x positions (sort of, we tweak)
    
    # Draw W and X on left
    for r_idx, region in enumerate(["W", "X"]):
        rr = region_results[region]
        
        # R1
        for i in range(8):
            tA = get_seed_team(region, R1_PAIRS[i][0])
            tB = get_seed_team(region, R1_PAIRS[i][1])
            yA = y_pos(r_idx, 2*i, 16)
            yB = y_pos(r_idx, 2*i + 1, 16)
            winner = rr["r1"][i]
            add_game_box(fig, 0, yA, tA, won=(winner == tA))
            add_game_box(fig, 0, yB, tB, won=(winner == tB))
        
        # R2
        for i in range(4):
            y = y_pos(r_idx, i, 4)
            add_game_box(fig, 1, y, rr["r2"][i], won=True)
        
        # S16
        for i in range(2):
            y = y_pos(r_idx, i, 2)
            add_game_box(fig, 2, y, rr["s16"][i], won=True)
        
        # E8 (regional final)
        y = y_pos(r_idx, 0, 1)
        add_game_box(fig, 3, y, rr["e8"], won=True)
    
    # Draw Y and Z on right (mirror x)
    for r_idx, region in enumerate(["Y", "Z"]):
        rr = region_results[region]
        actual_idx = r_idx + 2  # Y=2, Z=3
        
        for i in range(8):
            tA = get_seed_team(region, R1_PAIRS[i][0])
            tB = get_seed_team(region, R1_PAIRS[i][1])
            yA = y_pos(actual_idx, 2*i, 16)
            yB = y_pos(actual_idx, 2*i + 1, 16)
            winner = rr["r1"][i]
            add_game_box(fig, 8, yA, tA, won=(winner == tA))
            add_game_box(fig, 8, yB, tB, won=(winner == tB))
        
        for i in range(4):
            y = y_pos(actual_idx, i, 4)
            add_game_box(fig, 7, y, rr["r2"][i], won=True)
        
        for i in range(2):
            y = y_pos(actual_idx, i, 2)
            add_game_box(fig, 6, y, rr["s16"][i], won=True)
        
        y = y_pos(actual_idx, 0, 1)
        add_game_box(fig, 5, y, rr["e8"], won=True)
    
    # Final Four: 2 games in middle
    add_game_box(fig, 4, 12, f4_a, won=(champion == f4_a))
    add_game_box(fig, 4, 4,  f4_b, won=(champion == f4_b))
    
    # Champion in center
    fig.add_shape(
        type="rect",
        x0=3.5, y0=7.5, x1=4.5, y1=8.5,
        line=dict(color="#FFD700", width=3),
        fillcolor="rgba(255, 215, 0, 0.20)",
    )
    fig.add_annotation(
        x=4, y=8,
        text=f"🏆<br><b>{champion['team']}</b>",
        showarrow=False,
        font=dict(size=14, color="#1F2230"),
    )
    
    fig.update_layout(
        height=900,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.6, 8.6]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 33]),
        margin=dict(l=10, r=10, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    # Round labels at top
    round_labels = ["R64", "R32", "S16", "E8", "F4", "E8", "S16", "R32", "R64"]
    for i, lbl in enumerate(round_labels):
        fig.add_annotation(
            x=i, y=33,
            text=f"<b>{lbl}</b>",
            showarrow=False,
            font=dict(size=11, color="#888780"),
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ---- Full table (collapsed) ----
    with st.expander("📊 Full advancement probability table"):
        show = bracket.copy()
        pcols = ["p_r32", "p_sweet16", "p_elite8", "p_final4", "p_champgame", "p_champ"]
        for c in pcols:
            show[c] = (show[c] * 100).round(1).astype(str) + "%"
        show = show[["seed", "region", "team"] + pcols]
        show.columns = ["Seed", "Region", "Team", "R32", "Sweet 16",
                        "Elite 8", "Final 4", "Final", "Champion"]
        st.dataframe(show, use_container_width=True, height=540, hide_index=True)


# ============================================================
# Tab 5: About
# ============================================================

with tab5:
    st.markdown(
        """
        ### About this dashboard

        This dashboard uses past game data to estimate team strength and simulate future matchups.

        Each team gets an estimated offense score and defense score. These are combined into a Net rating,
        which is used to compare teams and forecast possible game outcomes.

        The predictions are for entertainment and exploration. They are not guarantees.
        """
    )