import streamlit as st
import requests
import time
import re

# --- CONFIGURATION ---
FOOTBALL_API_KEY = "de7decb2297442f097c130dfc70494f1"
MISTRAL_API_KEY = "R20I2OGqFNneLIAoR6lQMS1sGaNj1D4k"

st.set_page_config(page_title="Nero · Bet Intelligence", layout="wide", page_icon="⚽")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg:       #F7F6F2;
    --white:    #FFFFFF;
    --ink:      #000000; /* Noir pur pour lisibilité */
    --ink2:     #1A1A1A;
    --muted:    #555555; /* Plus sombre que l'ancien muted */
    --border:   #D1CEC8;
    --accent:   #1B4FD8;
    --accent-l: #EEF2FF;
    --green:    #0D7A4E;
    --shadow:   0 1px 3px rgba(0,0,0,.1);
}

html, body, .stApp {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ink) !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* ─── LANDING ─── */
.land-wrap {
    max-width: 680px;
    margin: 8vh auto 0;
    text-align: center;
    padding: 0 20px;
}
.land-title {
    font-family: 'Instrument Serif', serif;
    font-size: clamp(3.5rem, 8vw, 5.5rem);
    font-weight: 400;
    line-height: 1.05;
    color: var(--ink);
    letter-spacing: -2px;
}
.land-title em { font-style: italic; color: var(--accent); }
.land-desc {
    font-size: 1.1rem;
    color: var(--ink2); /* Plus noir */
    font-weight: 400;
    margin-bottom: 60px;
}

/* ─── LEAGUE TILES CLICQUABLES ─── */
.stButton > button {
    border-radius: 20px !important;
    border: 1.5px solid var(--border) !important;
    background: var(--white) !important;
    color: var(--ink) !important;
    padding: 40px 20px !important;
    height: auto !important;
    transition: all .2s ease-in-out !important;
    box-shadow: var(--shadow) !important;
}

.stButton > button:hover {
    border-color: var(--accent) !important;
    background: var(--white) !important;
    color: var(--accent) !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
}

.stButton > button div p {
    font-family: 'Instrument Serif', serif !important;
    font-size: 1.6rem !important;
    font-weight: 400 !important;
}

/* ─── DASHBOARD TEXTS ─── */
.mc-team-name {
    font-family: 'Instrument Serif', serif;
    font-size: 1.4rem;
    color: var(--ink); /* Noir */
    font-weight: 600;
}
.mc-report-text {
    font-size: 1rem;
    line-height: 1.6;
    color: #111111; /* Presque noir */
    font-weight: 400;
}
.mc-report-text strong {
    font-weight: 700;
    color: var(--ink);
}
.mc-conf-label { font-weight: 700; color: var(--ink); }

/* Sidebar contrast */
section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border) !important;
}
.sb-logo { font-weight: 700; color: var(--ink); }

</style>
""", unsafe_allow_html=True)


# ─── LOGIQUE IA & DATA (RESTE INCHANGÉ) ───
@st.cache_data(ttl=86400)
def analyse_nero(h_team, a_team, h_pos, a_pos, h_pts, a_pts):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Expert foot : {h_team} vs {a_team}. Verdict court, score probable, confiance %."
    try:
        response = requests.post(url, json={"model": "mistral-small-latest",
                                            "messages": [{"role": "user", "content": prompt}]}, headers=headers)
        txt = response.json()['choices'][0]['message']['content']
        conf_val = 50
        nums = re.findall(r'(\d+)\s*%', txt)
        if nums: conf_val = int(nums[0])
        gagnant = h_team
        if a_team.lower() in txt.lower() and "victoire" in txt.lower():
            gagnant = a_team
        elif "nul" in txt.lower():
            gagnant = "Match Nul"
        return {"full": txt, "gagnant": gagnant, "conf": conf_val}
    except:
        return {"full": "Indisponible", "gagnant": "N/A", "conf": 0}


@st.cache_data(ttl=3600)
def get_data(league_code):
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        s = requests.get(f"https://api.football-data.org/v4/competitions/{league_code}/standings",
                         headers=headers).json()
        m = requests.get(f"https://api.football-data.org/v4/competitions/{league_code}/matches?status=SCHEDULED",
                         headers=headers).json()
        pos_map = {t['team']['name']: t for t in s['standings'][0]['table']}
        return pos_map, m.get('matches', [])
    except:
        return {}, []


if "league_id" not in st.session_state:
    st.session_state.league_id = None

LEAGUES = {
    "FL1": {"name": "Ligue 1", "flag": "🇫🇷", "country": "FRANCE"},
    "PL": {"name": "Premier League", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "country": "UK"},
    "PD": {"name": "La Liga", "flag": "🇪🇸", "country": "SPAIN"},
}

# ══════════════════════════════════════
# PAGE 1 — LANDING (CLICQUABLE)
# ══════════════════════════════════════
if st.session_state.league_id is None:
    st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div class="land-wrap">
            <div class="land-title">Nero <em>Bet</em></div>
            <p class="land-desc">Analyses de haute précision par IA.<br>Choisissez une ligue pour voir les pronostics.</p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, (lid, info) in zip([col1, col2, col3], LEAGUES.items()):
        with col:
            # On utilise le bouton Streamlit stylisé comme une carte
            if st.button(f"{info['flag']}\n\n{info['name']}\n{info['country']}", key=f"btn_{lid}"):
                st.session_state.league_id = lid
                st.rerun()

# ══════════════════════════════════════
# PAGE 2 — DASHBOARD (CONTRASTE RENFORCÉ)
# ══════════════════════════════════════
else:
    league_id = st.session_state.league_id
    info = LEAGUES[league_id]

    with st.sidebar:
        st.markdown(f'<div class="sb-logo">Nero <em>Bet</em></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:black; font-weight:700; margin-top:20px;">{info["flag"]} {info["name"]}</div>',
                    unsafe_allow_html=True)
        if st.button("← Retour"):
            st.session_state.league_id = None
            st.rerun()

    col_main, col_side = st.columns([2.2, 1])
    pos_map, matches = get_data(league_id)
    best_bets = []

    with col_main:
        st.markdown(f'<h1 style="font-family:Instrument Serif; font-size:3rem;">Analyses <em>{info["name"]}</em></h1>',
                    unsafe_allow_html=True)

        if matches:
            for m in matches[:8]:
                h_n, a_n = m['homeTeam']['name'], m['awayTeam']['name']
                h, a = pos_map.get(h_n), pos_map.get(a_n)
                if h and a:
                    res = analyse_nero(h_n, a_n, h['position'], a['position'], h['points'], a['points'])
                    if res['conf'] >= 70:
                        best_bets.append({"match": f"{h_n} vs {a_n}", "pick": res['gagnant'], "conf": res['conf']})

                    bar_col = "#0D7A4E" if res['conf'] >= 70 else "#B45309"

                    st.markdown(f"""
                    <div class="match-card" style="border: 1px solid #000;">
                        <div class="mc-teams">
                            <div class="mc-team"><div class="mc-team-name">{h_n}</div><div class="mc-team-rank">Rang {h['position']}</div></div>
                            <span class="mc-vs">VS</span>
                            <div class="mc-team away"><div class="mc-team-name">{a_n}</div><div class="mc-team-rank">Rang {a['position']}</div></div>
                        </div>
                        <div class="mc-report" style="background: #fff; border: 1px solid #eee;">
                            <div class="mc-report-text">{res['full'].replace('Verdict', '<strong>Verdict</strong>').replace('Score', '<strong>Score</strong>')}</div>
                            <div class="mc-conf">
                                <span class="mc-conf-label">CONFIANCE</span>
                                <div class="mc-conf-track"><div class="mc-conf-fill" style="width:{res['conf']}%;background:{bar_col};"></div></div>
                                <span class="mc-conf-val" style="color:{bar_col}; font-weight:900;">{res['conf']}%</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.05)

    with col_side:
        st.markdown('<div class="panel" style="border: 2px solid #000;">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Golden <em>Ticket</em></div>', unsafe_allow_html=True)
        if best_bets:
            for b in best_bets:
                st.markdown(f"""
                <div class="bet-card" style="background:#fff; border:1px solid #000;">
                    <div class="bet-card-match" style="color:#000; font-weight:700;">{b['match']}</div>
                    <div class="bet-card-pick" style="color:var(--accent); font-size:1.1rem;">{b['pick']} <span class="bet-card-badge">{b['conf']}%</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="panel-empty">Aucun prono VIP.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)