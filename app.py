import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Configuro mi página
st.set_page_config(page_title="TORVI ANALYTICS", layout="wide")

# CSS Estilo Galáctico con Glassmorphism
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
    .titulo-futurista { font-family: 'Orbitron', sans-serif; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px;}
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; }
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.6); backdrop-filter: blur(10px); border: 1px solid #00f2ff; border-radius: 10px; text-align: center; }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    </style>
    """, unsafe_allow_html=True)

# Conexión Firebase
if not firebase_admin._apps:
    dict_claves = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(dict_claves)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Seguridad y Sesión
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'

st.markdown('<p class="titulo-futurista">NUEVO NOMBRE AQUÍ</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE ANÁLISIS EV+ AVANZADO</p>', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>🔐 ACCESO</h3>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🚀 LOGIN", "📝 REGISTRO"])
        with t1:
            with st.form("f_login"):
                u, p = st.text_input("Correo:"), st.text_input("Clave:", type="password")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    res = db.collection('usuarios').document(u).get()
                    if res.exists and res.to_dict()['password'] == encriptar_password(p):
                        st.session_state['autenticado'], st.session_state['user_rol'] = True, res.to_dict().get('rol', 'usuario_vip')
                        st.rerun()
                    else: st.error("Datos incorrectos")
        with t2:
            with st.form("f_reg"):
                un, pn = st.text_input("Nuevo Correo:"), st.text_input("Nueva Clave:", type="password")
                if st.form_submit_button("REGISTRARME", use_container_width=True):
                    db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                    st.success("¡Listo! Ya puedes iniciar sesión.")
    st.stop()

# --- MIGRACIÓN: CARGA DE DATOS DESDE FIREBASE ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data = [d.to_dict() for d in docs]
df = pd.DataFrame(data) if data else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# --- SIDEBAR ---
st.sidebar.title("📟 CONSOLA")
if st.sidebar.button("🚪 CERRAR SESIÓN"):
    st.session_state['autenticado'] = False
    st.rerun()

# --- 🚀 PANEL DE ADMIN (Solo para Torvi) ---
if st.session_state['user_rol'] == 'admin':
    st.markdown("### 🛠️ PANEL DE CONTROL (ADMIN)")
    with st.expander("➕ AGREGAR NUEVO PRONÓSTICO"):
        with st.form("nuevo_pick"):
            col_p1, col_p2 = st.columns(2)
            partido = col_p1.text_input("⚽ Partido:", placeholder="Ej: Real Madrid vs City")
            mercado = col_p2.text_input("🎯 Mercado:", placeholder="Ej: +2.5 Goles")
            
            # 🔥 LAS 4 COLUMNAS MATEMÁTICAS 🔥
            col_n1, col_n2, col_n3, col_n4 = st.columns(4)
            cuota = col_n1.number_input("📈 Cuota:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = col_n2.number_input("🏦 Prob. Casa (%):", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
            prob_real = col_n3.number_input("🎯 Prob. Real (%):", min_value=0.0, max_value=100.0, value=55.0, step=0.1)
            ev_val = col_n4.number_input("🔥 EV+ (%):", value=5.0, step=0.1)
            
            ana = st.text_area("🧠 Análisis Táctico:")
            
            if st.form_submit_button("🚀 PUBLICAR EN EL RADAR"):
                pick_id = f"{int(time.time())}"
                db.collection('pronosticos').document(pick_id).set({
                    'id': pick_id, 'partido': partido, 'mercado': mercado, 'cuota': cuota,
                    'prob_casa': prob_casa, 'prob_real': prob_real,
                    'ev': ev_val, 'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("¡Pick publicado con desglose matemático!")
                st.rerun()

# --- DASHBOARD DE USUARIO ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 MÁX EV", f"{df['ev'].max()}%")
    c2.metric("🎯 ACTIVOS", len(df[df['estatus'] == 'PENDIENTE']))
    c3.metric("🏦 BANK", "$1,000") 
    c4.metric("🛡️ STATUS", "ONLINE")

    st.markdown("### 🛰️ RADAR DE VALOR")
    fig = px.bar(df, x='ev', y='mercado', orientation='h', color='ev', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    for i, r in df.iterrows():
        with st.expander(f"📌 {r['partido']} | {r['mercado']} | EV+: {r['ev']}%"):
            # 🔥 DESGLOSE DE PROBABILIDADES PARA EL USUARIO 🔥
            pcasa = r.get('prob_casa', 'N/A')
            preal = r.get('prob_real', 'N/A')
            st.markdown(f"<p style='color: #bc13fe; font-family: Orbitron; font-size: 0.95rem;'><b>🏦 Prob. Implícita de la Casa:</b> {pcasa}% &nbsp;&nbsp;|&nbsp;&nbsp; <b>🎯 Prob. Real Calculada:</b> {preal}%</p>", unsafe_allow_html=True)
            
            st.write(r.get('analisis', ''))
            if st.session_state['user_rol'] == 'admin':
                col_a, col_b = st.columns(2)
                if col_a.button(f"✅ Ganada", key=f"win_{r['id']}"):
                    db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                    st.rerun()
                if col_b.button(f"❌ Perdida", key=f"loss_{r['id']}"):
                    db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                    st.rerun()
else:
    st.info("No hay pronósticos activos en el radar. Esperando señal del Admin...")

# --- FOOTER PROFESIONAL ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; font-size: 0.9rem; opacity: 0.7;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)


