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
    page_title="March Madness Forecast",
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
    # ===== Top 10 (already had) =====
    "Auburn":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2.png",
    "Duke":           "https://a.espncdn.com/i/teamlogos/ncaa/500/150.png",
    "Florida":        "https://a.espncdn.com/i/teamlogos/ncaa/500/57.png",
    "Houston":        "https://a.espncdn.com/i/teamlogos/ncaa/500/248.png",
    "Alabama":        "https://a.espncdn.com/i/teamlogos/ncaa/500/333.png",
    "Tennessee":      "https://a.espncdn.com/i/teamlogos/ncaa/500/2633.png",
    "Texas Tech":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2641.png",
    "Maryland":       "https://a.espncdn.com/i/teamlogos/ncaa/500/120.png",
    "Iowa St":        "https://a.espncdn.com/i/teamlogos/ncaa/500/66.png",
    "Arizona":        "https://a.espncdn.com/i/teamlogos/ncaa/500/12.png",
    
    # ===== Other Power Conference contenders =====
    "Michigan St":    "https://a.espncdn.com/i/teamlogos/ncaa/500/127.png",
    "Michigan":       "https://a.espncdn.com/i/teamlogos/ncaa/500/130.png",
    "Kentucky":       "https://a.espncdn.com/i/teamlogos/ncaa/500/96.png",
    "St John's":      "https://a.espncdn.com/i/teamlogos/ncaa/500/2599.png",
    "Wisconsin":      "https://a.espncdn.com/i/teamlogos/ncaa/500/275.png",
    "Purdue":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2509.png",
    "Missouri":       "https://a.espncdn.com/i/teamlogos/ncaa/500/142.png",
    "Illinois":       "https://a.espncdn.com/i/teamlogos/ncaa/500/356.png",
    "Gonzaga":        "https://a.espncdn.com/i/teamlogos/ncaa/500/2250.png",
    "Texas A&M":      "https://a.espncdn.com/i/teamlogos/ncaa/500/245.png",
    "BYU":            "https://a.espncdn.com/i/teamlogos/ncaa/500/252.png",
    "Kansas":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2305.png",
    "Mississippi":    "https://a.espncdn.com/i/teamlogos/ncaa/500/145.png",
    "UCLA":           "https://a.espncdn.com/i/teamlogos/ncaa/500/26.png",
    "Texas":          "https://a.espncdn.com/i/teamlogos/ncaa/500/251.png",
    "North Carolina": "https://a.espncdn.com/i/teamlogos/ncaa/500/153.png",
    "UConn":          "https://a.espncdn.com/i/teamlogos/ncaa/500/41.png",
    "Connecticut":    "https://a.espncdn.com/i/teamlogos/ncaa/500/41.png",
    "Memphis":        "https://a.espncdn.com/i/teamlogos/ncaa/500/235.png",
    "Marquette":      "https://a.espncdn.com/i/teamlogos/ncaa/500/269.png",
    "Creighton":      "https://a.espncdn.com/i/teamlogos/ncaa/500/156.png",
    "Baylor":         "https://a.espncdn.com/i/teamlogos/ncaa/500/239.png",
    "Oregon":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2483.png",
    "Louisville":     "https://a.espncdn.com/i/teamlogos/ncaa/500/97.png",
    "Cincinnati":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2132.png",
    "Pittsburgh":     "https://a.espncdn.com/i/teamlogos/ncaa/500/221.png",
    "Vanderbilt":     "https://a.espncdn.com/i/teamlogos/ncaa/500/238.png",
    "Georgia":        "https://a.espncdn.com/i/teamlogos/ncaa/500/61.png",
    "South Carolina": "https://a.espncdn.com/i/teamlogos/ncaa/500/2579.png",
    "Arkansas":       "https://a.espncdn.com/i/teamlogos/ncaa/500/8.png",
    "LSU":            "https://a.espncdn.com/i/teamlogos/ncaa/500/99.png",
    "Oklahoma":       "https://a.espncdn.com/i/teamlogos/ncaa/500/201.png",
    "TCU":            "https://a.espncdn.com/i/teamlogos/ncaa/500/2628.png",
    "West Virginia":  "https://a.espncdn.com/i/teamlogos/ncaa/500/277.png",
    "Iowa":           "https://a.espncdn.com/i/teamlogos/ncaa/500/2294.png",
    "Indiana":        "https://a.espncdn.com/i/teamlogos/ncaa/500/84.png",
    "Ohio St":        "https://a.espncdn.com/i/teamlogos/ncaa/500/194.png",
    "Penn St":        "https://a.espncdn.com/i/teamlogos/ncaa/500/213.png",
    "Rutgers":        "https://a.espncdn.com/i/teamlogos/ncaa/500/164.png",
    "Northwestern":   "https://a.espncdn.com/i/teamlogos/ncaa/500/77.png",
    "Nebraska":       "https://a.espncdn.com/i/teamlogos/ncaa/500/158.png",
    "Minnesota":      "https://a.espncdn.com/i/teamlogos/ncaa/500/135.png",
    "Washington":     "https://a.espncdn.com/i/teamlogos/ncaa/500/264.png",
    "USC":            "https://a.espncdn.com/i/teamlogos/ncaa/500/30.png",
    "Stanford":       "https://a.espncdn.com/i/teamlogos/ncaa/500/24.png",
    "Cal":            "https://a.espncdn.com/i/teamlogos/ncaa/500/25.png",
    "Notre Dame":     "https://a.espncdn.com/i/teamlogos/ncaa/500/87.png",
    "Wake Forest":    "https://a.espncdn.com/i/teamlogos/ncaa/500/154.png",
    "NC State":       "https://a.espncdn.com/i/teamlogos/ncaa/500/152.png",
    "Virginia":       "https://a.espncdn.com/i/teamlogos/ncaa/500/258.png",
    "Virginia Tech":  "https://a.espncdn.com/i/teamlogos/ncaa/500/259.png",
    "Clemson":        "https://a.espncdn.com/i/teamlogos/ncaa/500/228.png",
    "Florida St":     "https://a.espncdn.com/i/teamlogos/ncaa/500/52.png",
    "Miami FL":       "https://a.espncdn.com/i/teamlogos/ncaa/500/2390.png",
    "Boston College": "https://a.espncdn.com/i/teamlogos/ncaa/500/103.png",
    "Syracuse":       "https://a.espncdn.com/i/teamlogos/ncaa/500/183.png",
    "Georgetown":     "https://a.espncdn.com/i/teamlogos/ncaa/500/46.png",
    "Villanova":      "https://a.espncdn.com/i/teamlogos/ncaa/500/222.png",
    "Xavier":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2752.png",
    "Providence":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2507.png",
    "Seton Hall":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2550.png",
    "DePaul":         "https://a.espncdn.com/i/teamlogos/ncaa/500/305.png",
    "Butler":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2086.png",
    
    # ===== Mid-major contenders that often make tournament =====
    "Saint Mary's":   "https://a.espncdn.com/i/teamlogos/ncaa/500/2608.png",
    "St Mary's CA":   "https://a.espncdn.com/i/teamlogos/ncaa/500/2608.png",
    "San Diego St":   "https://a.espncdn.com/i/teamlogos/ncaa/500/21.png",
    "New Mexico":     "https://a.espncdn.com/i/teamlogos/ncaa/500/167.png",
    "UNLV":           "https://a.espncdn.com/i/teamlogos/ncaa/500/2439.png",
    "Nevada":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2440.png",
    "Boise St":       "https://a.espncdn.com/i/teamlogos/ncaa/500/68.png",
    "Utah St":        "https://a.espncdn.com/i/teamlogos/ncaa/500/328.png",
    "Drake":          "https://a.espncdn.com/i/teamlogos/ncaa/500/2181.png",
    "Bradley":        "https://a.espncdn.com/i/teamlogos/ncaa/500/71.png",
    "Northern Iowa":  "https://a.espncdn.com/i/teamlogos/ncaa/500/304.png",
    "Liberty":        "https://a.espncdn.com/i/teamlogos/ncaa/500/2335.png",
    "Akron":          "https://a.espncdn.com/i/teamlogos/ncaa/500/2006.png",
    "VCU":            "https://a.espncdn.com/i/teamlogos/ncaa/500/2670.png",
    "Dayton":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2168.png",
    "Davidson":       "https://a.espncdn.com/i/teamlogos/ncaa/500/2166.png",
    "Yale":           "https://a.espncdn.com/i/teamlogos/ncaa/500/43.png",
    "Princeton":      "https://a.espncdn.com/i/teamlogos/ncaa/500/163.png",
    "High Point":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2272.png",
    "Lipscomb":       "https://a.espncdn.com/i/teamlogos/ncaa/500/288.png",
    "McNeese St":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2377.png",
    "Grand Canyon":   "https://a.espncdn.com/i/teamlogos/ncaa/500/2253.png",
    "UC San Diego":   "https://a.espncdn.com/i/teamlogos/ncaa/500/28.png",
    "Troy":           "https://a.espncdn.com/i/teamlogos/ncaa/500/2653.png",
    "UNC Wilmington": "https://a.espncdn.com/i/teamlogos/ncaa/500/350.png",
    "Robert Morris":  "https://a.espncdn.com/i/teamlogos/ncaa/500/2523.png",
    "Wofford":        "https://a.espncdn.com/i/teamlogos/ncaa/500/2747.png",
    "Bryant":         "https://a.espncdn.com/i/teamlogos/ncaa/500/2803.png",
    "Norfolk St":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2450.png",
    "American":       "https://a.espncdn.com/i/teamlogos/ncaa/500/44.png",
    "Mt St Mary's":   "https://a.espncdn.com/i/teamlogos/ncaa/500/116.png",
    "SIUE":           "https://a.espncdn.com/i/teamlogos/ncaa/500/2565.png",
    "Omaha":          "https://a.espncdn.com/i/teamlogos/ncaa/500/2437.png",
    "NB Omaha":       "https://a.espncdn.com/i/teamlogos/ncaa/500/2437.png",
    "Montana":        "https://a.espncdn.com/i/teamlogos/ncaa/500/149.png",
    "Vermont":        "https://a.espncdn.com/i/teamlogos/ncaa/500/261.png",
    "Bucknell":       "https://a.espncdn.com/i/teamlogos/ncaa/500/2083.png",
    
    # ===== Bottom 10 (already had) =====
    "MS Valley St":   "https://a.espncdn.com/i/teamlogos/ncaa/500/2400.png",
    "Ark Pine Bluff": "https://a.espncdn.com/i/teamlogos/ncaa/500/2029.png",
    "Alabama A&M":    "https://a.espncdn.com/i/teamlogos/ncaa/500/2010.png",
    "Chicago St":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2130.png",
    "Coppin St":      "https://a.espncdn.com/i/teamlogos/ncaa/500/2154.png",
    "MD E Shore":     "https://a.espncdn.com/i/teamlogos/ncaa/500/2379.png",
    "Prairie View":   "https://a.espncdn.com/i/teamlogos/ncaa/500/2504.png",
    "Canisius":       "https://a.espncdn.com/i/teamlogos/ncaa/500/2099.png",
    "New Hampshire":  "https://a.espncdn.com/i/teamlogos/ncaa/500/160.png",
    "Citadel":        "https://a.espncdn.com/i/teamlogos/ncaa/500/2643.png",
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
    """
    <div class="hero">
        <h1 class="app-hero-title">🏀 March Madness Forecast</h1>
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

    top10 = df.head(10).copy()
    bottom10 = df.tail(10).sort_values("Net", ascending=True).copy()

    # Strongest teams title + small help icon
    st.subheader(
        "🔥 Strongest teams",
        help=("Strongest teams are the teams with the highest Net rating. "
        "Net rating combines a team's estimated offense and defense into one overall strength score."
        ),
        )

    top3 = top10.head(3)
    top_cols = st.columns(3)

    subtitles = ["Best overall profile", "Major title threat", "Dangerous contender"]

    for i, (_, row) in enumerate(top3.iterrows()):
        with top_cols[i]:
            show_top_team_card(row, subtitle=subtitles[i])

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
        label="",
        options=available_cols,
        default=["Rank", "Team", "Net"],
        label_visibility="collapsed",
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
        "Neutral site means neither team gets home-court advantage."
        )

    c1, c2, c3 = st.columns([2, 2, 1])

    team_a = c1.selectbox("Team A", teams, index=0)
    team_b = c2.selectbox("Team B", teams, index=1)
    neutral = c3.checkbox(
        "Neutral site",
        value=True,
        help=(
            "If checked, the game is treated as being played at a neutral location. "
            "If unchecked, Team A is treated as the home team and gets home-court advantage."
            ),
)

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

        m1, m2 = st.columns(2)
        m1.metric("P(Team A wins)", f"{win_prob:.1%}")
        m2.metric("Projected score", f"{pts_a.mean():.0f} – {pts_b.mean():.0f}")

        st.caption(
            "The histogram shows simulated point differences. "
            "Values above 0 mean Team A wins; values below 0 mean Team B wins."
            )

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
            annotation_text="0 = tie",
            )

        fig.update_layout(
            height=420,
            xaxis_title=f"Point difference: Team A score − Team B score ({team_a} − {team_b})",
            yaxis_title="Simulated games",
            margin=dict(l=50, r=30, t=40, b=50),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Tab 4: Bracket
# ============================================================

with tab4:
    # ---- Headline ----
    bk = bracket.copy()
    bk["seed_num"] = bk.seed.str[1:3].astype(int)
    bk["region_label"] = bk.region.map(
        {"W": "Region 1", "X": "Region 2", "Y": "Region 3", "Z": "Region 4"}
    )
    
    # Map round name -> column
    ROUND_COLS = {
        "Round of 32":  "p_r32",
        "Sweet 16":     "p_sweet16",
        "Elite 8":      "p_elite8",
        "Final 4":      "p_final4",
        "Final":        "p_champgame",
        "Champion":     "p_champ",
    }
    
    ROUND_TITLES = {
        "Round of 32":  "🏀 Who reaches the Round of 32?",
        "Sweet 16":     "🔥 Who survives to the Sweet 16?",
        "Elite 8":      "💪 Who makes the Elite 8?",
        "Final 4":      "🏆 Final Four contenders",
        "Final":        "⭐ Championship game contenders",
        "Champion":     "🏆 Title contenders",
    }

    
    # ---- Round selector + top N slider ----
    sel_col, slider_col = st.columns([3, 2])
    
    with sel_col:
        selected_round = st.radio(
            "Pick a round",
            list(ROUND_COLS.keys()),
            horizontal=True,
            index=5,  # default to Champion
        )
    
    with slider_col:
        top_n_bracket = st.slider(
            "Show top N teams",
            min_value=8, max_value=24, value=12, step=4,
            key="bracket_top_n",
        )
    
    # ---- Build the leaderboard ----
    prob_col = ROUND_COLS[selected_round]
    leaderboard = bk.sort_values(prob_col, ascending=False).head(top_n_bracket).reset_index(drop=True)
    
    # Max value for progress bar scaling
    max_pct = leaderboard[prob_col].max()
    
    st.markdown(f"### {ROUND_TITLES[selected_round]}")
    st.markdown(
        f'<div class="section-note">Top {top_n_bracket} teams by their probability of reaching <b>{selected_round}</b>. '
        f'Bar length is relative to the leader.</div>',
        unsafe_allow_html=True,
    )
    
    # ---- CSS for the leaderboard rows ----
    st.markdown(
        """
        <style>
          .leader-row {
              display: grid;
              grid-template-columns: 60px 60px 1fr 2fr 90px;
              align-items: center;
              gap: 14px;
              padding: 10px 14px;
              margin-bottom: 8px;
              background: linear-gradient(180deg, rgba(255, 107, 26, 0.05), var(--surface));
              border: 1px solid rgba(255, 107, 26, 0.20);
              border-radius: 14px;
              transition: transform 0.12s ease, border-color 0.12s ease;
          }
          .leader-row:hover {
              transform: translateX(3px);
              border-color: rgba(255, 107, 26, 0.55);
          }
          .leader-row.top3 {
              border: 1.5px solid rgba(255, 107, 26, 0.55);
              background: linear-gradient(180deg, rgba(255, 107, 26, 0.13), var(--surface));
          }
          .leader-rank {
              font-family: 'Bebas Neue', sans-serif;
              font-size: 1.65rem;
              color: var(--orange);
              text-align: center;
              letter-spacing: 0.02em;
          }
          .leader-logo {
              display: flex;
              justify-content: center;
              align-items: center;
          }
          .leader-logo img {
              width: 42px; height: 42px;
              object-fit: contain;
              filter: drop-shadow(0 4px 8px rgba(0,0,0,0.20));
          }
          .leader-logo .logo-badge,
          .leader-logo .logo-badge-center {
              width: 42px; height: 42px;
              font-size: 0.85rem;
              margin: 0;
          }
          .leader-info {
              display: flex; flex-direction: column;
          }
          .leader-name {
              color: var(--text-strong);
              font-size: 1.1rem;
              font-weight: 800;
              line-height: 1.1;
          }
          .leader-meta {
              color: var(--muted);
              font-size: 0.74rem;
              font-weight: 700;
              letter-spacing: 0.08em;
              text-transform: uppercase;
              margin-top: 2px;
          }
          .leader-bar-wrap {
              background: rgba(122, 130, 148, 0.18);
              border-radius: 999px;
              height: 14px;
              overflow: hidden;
              position: relative;
          }
          .leader-bar-fill {
              height: 100%;
              background: linear-gradient(90deg, #FF6B1A, #D85A30);
              border-radius: 999px;
              box-shadow: 0 0 12px rgba(255, 107, 26, 0.50);
          }
          .leader-pct {
              font-family: 'Bebas Neue', sans-serif;
              font-size: 1.55rem;
              color: var(--text-strong);
              text-align: right;
              letter-spacing: 0.01em;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # ---- Render leaderboard ----
    rows_html = []
    for i, row in leaderboard.iterrows():
        rank = i + 1
        team = str(row["team"])
        prob = float(row[prob_col])
        bar_pct = (prob / max_pct) * 100 if max_pct > 0 else 0
        
        top3_class = "top3" if rank <= 3 else ""
        logo = logo_html(team, centered=True)
        seed_str = f"Seed {row['seed_num']} · {row['region_label']}"
        
        rows_html.append(f"""
            <div class="leader-row {top3_class}">
                <div class="leader-rank">#{rank}</div>
                <div class="leader-logo">{logo}</div>
                <div class="leader-info">
                    <div class="leader-name">{html.escape(team)}</div>
                    <div class="leader-meta">{html.escape(seed_str)}</div>
                </div>
                <div class="leader-bar-wrap">
                    <div class="leader-bar-fill" style="width: {bar_pct:.1f}%;"></div>
                </div>
                <div class="leader-pct">{prob*100:.1f}%</div>
            </div>
        """)
    
    st.markdown("\n".join(rows_html), unsafe_allow_html=True)
    
    # ---- Full table (collapsed) ----
    with st.expander("📊 Full advancement probability table"):
        show = bk.copy()
        pcols = ["p_r32", "p_sweet16", "p_elite8", "p_final4", "p_champgame", "p_champ"]
        for c in pcols:
            show[c] = (show[c] * 100).round(1).astype(str) + "%"
        show = show[["seed", "region", "team"] + pcols].sort_values(
            "team"
        )
        show.columns = ["Seed", "Region", "Team", "R32", "Sweet 16",
                        "Elite 8", "Final 4", "Final", "Champion"]
        st.dataframe(show, use_container_width=True, height=540, hide_index=True)


# ============================================================
# Tab 5: About
# ============================================================

with tab5:
    st.markdown(
        """
        <style>
          @keyframes funPulse {
              0%   { transform: translateX(0); opacity: 0.92; }
              50%  { transform: translateX(8px); opacity: 1; }
              100% { transform: translateX(0); opacity: 0.92; }
          }

          .fun-warning {
              margin-top: 1.4rem;
              padding: 1rem 1.2rem;
              border-radius: 16px;
              border: 1px solid rgba(255, 107, 26, 0.35);
              background: linear-gradient(
                  135deg,
                  rgba(255, 107, 26, 0.16),
                  rgba(24, 95, 165, 0.08)
              );
              box-shadow: 0 10px 28px rgba(255, 107, 26, 0.10);
              animation: funPulse 2.4s ease-in-out infinite;
          }

          .fun-warning-title {
              font-size: 1.1rem;
              font-weight: 850;
              color: var(--text-strong);
              margin-bottom: 0.25rem;
          }

          .fun-warning-text {
              font-size: 0.95rem;
              color: var(--muted);
              line-height: 1.45;
          }
        </style>

        ### About this dashboard

        This dashboard uses 2025 game data to estimate team strength and simulate future matchups.
        
        Each team gets an estimated offense score and defense score. These are combined into a Net rating,
        which is used to compare teams and forecast possible game outcomes.
        
        This app was built with AI assistance for coding, debugging, and dashboard design.

        <div class="fun-warning">
            <div class="fun-warning-title">🎲 Just for fun</div>
            <div class="fun-warning-text">
                These predictions are for entertainment and exploration only — not guarantees.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )