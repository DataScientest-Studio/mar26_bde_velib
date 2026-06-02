import streamlit as st

st.set_page_config(
    page_title="Vélos en libre-service",
    page_icon="🚲",
    layout="wide"
)

# ── Pages visibles dans le menu ────────────────────
accueil   = st.Page("pages/accueil.py",     title="Accueil",   icon="🏠")
dashboard = st.Page("pages/map_station.py", title="Stations",  icon="🗺️")
#test      = st.Page("pages/test.py",        title="Test",      icon="🧪")

# ── Pages cachées (accès via switch_page uniquement) ──
station   = st.Page("pages/station.py",     title="Détails Station", icon="🚉")
metro     = st.Page("pages/metro.py",       title="Détails Métro",   icon="🚇")

# ── Navigation ─────────────────────────────────────
pg = st.navigation([accueil, dashboard,  station, metro])

# ── Styles ─────────────────────────────────────────
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }

        [data-testid="stSidebarNav"] ul li:nth-child(3) {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

pg.run()