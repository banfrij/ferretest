"""Estilos compartidos: identidad visual 'industrial/mecánica' en tonos azul petróleo y cian."""
import streamlit as st

_CSS = """<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'JetBrains Mono', 'Roboto Mono', monospace; color: #F1F5F9; }
h1, h2, h3 { font-family: 'Oswald', sans-serif !important; text-transform: uppercase; letter-spacing: 1.5px; border-bottom: 3px solid #00D2FF; padding-bottom: 8px; color: #FFFFFF !important; text-shadow: 0 0 10px rgba(0,210,255,0.3); }
div.stButton > button, div.stFormSubmitButton > button, .stDownloadButton button { border-radius: 2px !important; border: 2px solid #00D2FF !important; background-color: #032B3A !important; color: #FFFFFF !important; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; transition: all 0.2s ease; }
div.stButton > button:hover, div.stFormSubmitButton > button:hover { border-color: #38BDF8 !important; background-color: #00E5FF !important; color: #011A24 !important; box-shadow: 0 0 12px rgba(0,229,255,0.6); }
[data-testid="stMetric"] { background-color: #032B3A; border: 2px solid #0B4F6C; border-radius: 2px; padding: 14px; box-shadow: inset 0 0 8px rgba(0,0,0,0.5); }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 0.9rem !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700 !important; font-size: 1.6rem !important; text-shadow: 0 0 8px rgba(0,210,255,0.25); }
.stTabs [data-baseweb="tab"] { border-radius: 2px 2px 0 0; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #CBD5E1; }
.stTabs [aria-selected="true"] { color: #00E5FF !important; border-bottom-color: #00E5FF !important; }
.stDataFrame, div[data-testid="stDataEditor"] { border-radius: 2px !important; border: 1px solid #0B4F6C; }
[data-testid="stSidebar"] { border-right: 3px solid #00D2FF; background-color: #01141C !important; }
hr { border-top: 2px solid #00D2FF !important; opacity: 0.7; }
.tuerca-card { border: 2px solid #0B4F6C; border-radius: 2px; padding: 10px; background-color: #032B3A; text-align: center; }

/* Efecto de alerta tintilante / pulsante (Glow Pulse) */
@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); border-color: #EF4444; }
  50% { box-shadow: 0 0 15px 4px rgba(239, 68, 68, 0.9); border-color: #F87171; }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); border-color: #EF4444; }
}
@keyframes pulse-yellow {
  0% { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.8); border-color: #EAB308; }
  50% { box-shadow: 0 0 15px 4px rgba(234, 179, 8, 0.9); border-color: #FACC15; }
  100% { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0); border-color: #EAB308; }
}
.alerta-pulsante-roja {
  border: 2px solid #EF4444;
  border-radius: 2px;
  padding: 12px;
  background-color: rgba(239, 68, 68, 0.12);
  animation: pulse-red 1.8s infinite;
  margin-bottom: 10px;
}
.alerta-pulsante-amarilla {
  border: 2px solid #EAB308;
  border-radius: 2px;
  padding: 12px;
  background-color: rgba(234, 179, 8, 0.12);
  animation: pulse-yellow 2.2s infinite;
  margin-bottom: 10px;
}
</style>"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def section_header(titulo: str, icono: str = "🔩") -> None:
    st.markdown(f"### {icono} {titulo}")


def format_mxn(valor: float) -> str:
    """Formato estándar de moneda para toda la app: $ 1,234.56 MXN."""
    return f"$ {valor:,.2f} MXN"


