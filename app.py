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
st.set_page_config(page_title="AXIOM ANALYTICS", layout="wide")

# CSS Estilo Galáctico con Glassmorphism
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
    .titulo-futurista { font-family: 'Orbitron', sans-serif; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px;}
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; }
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.6); backdrop-filter: blur(10px); border: 1px solid #00f2ff; border-radius: 10px; text-align: center; padding: 10px; }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; color: #b3cce6; font-family: 'Orbitron', sans-serif;}
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }
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

st.markdown('<p class="titulo-futurista">AXIOM DATA</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA (EV+)</p>', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>🔐 ACCESO SEGURO</h3>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🚀 INICIAR SESIÓN", "📝 SOLICITAR ACCESO"])
        with t1:
            with st.form("f_login"):
                u, p = st.text_input("Correo:"), st.text_input("Clave:", type="password")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    res = db.collection('usuarios').document(u).get()
                    if res.exists and res.to_dict()['password'] == encriptar_password(p):
                        st.session_state['autenticado'], st.session_state['user_rol'] = True, res.to_dict().get('rol', 'usuario_vip')
                        st.rerun()
                    else: st.error("Credenciales incorrectas o acceso denegado.")
        with t2:
            with st.form("f_reg"):
                un, pn = st.text_input("Nuevo Correo:"), st.text_input("Nueva Clave:", type="password")
                if st.form_submit_button("REGISTRARME", use_container_width=True):
                    db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                    st.success("¡Usuario creado! Ya puedes iniciar sesión.")
    st.stop()

# --- CARGA DE DATOS DESDE FIREBASE ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data = [d.to_dict() for d in docs]
df = pd.DataFrame(data) if data else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# --- SIDEBAR DE NAVEGACIÓN Y CONTROL ---
st.sidebar.title("📟 CONSOLA DE MANDO")
if st.sidebar.button("🚪 CERRAR SESIÓN", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

# --- 🚀 PANEL DE ADMIN (Solo para Torvi) ---
if st.session_state['user_rol'] == 'admin':
    st.markdown("### 🛠️ PANEL DE CONTROL (ADMIN)")
    with st.expander("➕ AGREGAR NUEVO ANÁLISIS AL RADAR"):
        with st.form("nuevo_pick"):
            col_p1, col_p2 = st.columns(2)
            partido = col_p1.text_input("⚽ Partido:", placeholder="Ej: Real Madrid vs City")
            mercado = col_p2.text_input("🎯 Mercado:", placeholder="Ej: +2.5 Goles")
            
            col_n1, col_n2, col_n3, col_n4 = st.columns(4)
            cuota = col_n1.number_input("📈 Cuota:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = col_n2.number_input("🏦 Prob. Casa (%):", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
            prob_real = col_n3.number_input("🎯 Prob. Real (%):", min_value=0.0, max_value=100.0, value=55.0, step=0.1)
            ev_val = col_n4.number_input("🔥 EV+ (%):", value=5.0, step=0.1)
            
            ana = st.text_area("🧠 Análisis Táctico y Estadístico:")
            
            if st.form_submit_button("🚀 PUBLICAR EN EL RADAR"):
                pick_id = f"{int(time.time())}"
                db.collection('pronosticos').document(pick_id).set({
                    'id': pick_id, 'partido': partido, 'mercado': mercado, 'cuota': cuota,
                    'prob_casa': prob_casa, 'prob_real': prob_real,
                    'ev': ev_val, 'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("¡Análisis publicado con éxito!")
                st.rerun()

# --- DASHBOARD DE USUARIO ---
st.markdown("<hr>", unsafe_allow_html=True)
rol_display = "ADMINISTRADOR SUPREMO" if st.session_state['user_rol'] == 'admin' else "USUARIO VIP"
st.markdown(f"<h3 style='color: #00f2ff; font-family: Orbitron; font-size: 1.2rem; text-align: center;'>👋 BIENVENIDO AL PANEL CENTRAL, {rol_display}</h3>", unsafe_allow_html=True)

# 🔥 BOTÓN DE ACTUALIZAR EN LA PANTALLA PRINCIPAL 🔥
if st.button("🔄 ACTUALIZAR DATOS DEL RADAR", use_container_width=True):
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    tab_radar, tab_historial = st.tabs(["🛰️ RADAR EN VIVO", "📖 HISTORIAL DE JUGADAS"])
    
    # 🟢 PESTAÑA 1: RADAR ACTIVO
    with tab_radar:
        if not df_activos.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔥 MÁX EV ACTUAL", f"{df_activos['ev'].max()}%")
            c2.metric("🎯 ANÁLISIS ACTIVOS", len(df_activos))
            c3.metric("🏦 BANK SUGERIDO", "$1,000") 
            c4.metric("🛡️ STATUS", "ONLINE")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            fig = px.bar(df_activos, x='ev', y='mercado', orientation='h', color='ev', template="plotly_dark")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<h4 style='color: #b3cce6; font-family: Orbitron;'>PRONÓSTICOS EN JUEGO</h4>", unsafe_allow_html=True)
            for i, r in df_activos.iterrows():
                with st.expander(f"⏳ {r['partido']} | {r['mercado']} | EV+: {r['ev']}%"):
                    pcasa = r.get('prob_casa', 'N/A')
                    preal = r.get('prob_real', 'N/A')
                    st.markdown(f"<p style='color: #bc13fe; font-family: Orbitron; font-size: 0.95rem;'><b>🏦 Prob. Implícita:</b> {pcasa}% &nbsp;&nbsp;|&nbsp;&nbsp; <b>🎯 Prob. Real:</b> {preal}%</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', ''))
                    
                    if st.session_state['user_rol'] == 'admin':
                        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                        # 🔥 AGREGAMOS EL BOTÓN DE BORRAR AQUÍ 🔥
                        col_a, col_b, col_c = st.columns(3)
                        if col_a.button(f"✅ Ganada", key=f"win_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if col_b.button(f"❌ Perdida", key=f"loss_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
                        if col_c.button(f"🗑️ Borrar", key=f"del_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).delete()
                            st.rerun()
        else:
            st.info("No hay pronósticos activos. El radar está limpio.")

    # 🔴 PESTAÑA 2: HISTORIAL
    with tab_historial:
        if not df_historial.empty:
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            total_resueltas = ganadas + perdidas
            win_rate = (ganadas / total_resueltas) * 100 if total_resueltas > 0 else 0
            
            st.markdown("<h4 style='color: #b3cce6; font-family: Orbitron; text-align: center;'>MÉTRICAS DE RENDIMIENTO</h4>", unsafe_allow_html=True)
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                st.metric("✅ ACERTADAS", ganadas)
            with h_col2:
                st.metric("❌ FALLADAS", perdidas)
            with h_col3:
                st.metric("📈 WIN RATE", f"{win_rate:.1f}%")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            for i, r in df_historial.iterrows():
                icono = "✅ GANADA" if r['estatus'] == 'GANADA' else "❌ PERDIDA"
                color_borde = "#00ff00" if r['estatus'] == 'GANADA' else "#ff0000"
                
                with st.expander(f"{icono} | {r['partido']} | {r['mercado']}"):
                    st.markdown(f"<div style='border-left: 3px solid {color_borde}; padding-left: 15px;'>", unsafe_allow_html=True)
                    st.write(f"**Cuota Final:** {r['cuota']} | **EV+ Inicial:** {r['ev']}%")
                    st.write(r.get('analisis', ''))
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.session_state['user_rol'] == 'admin':
                        col_rev, col_del = st.columns(2)
                        if col_rev.button("🔄 Regresar a Pendiente", key=f"rev_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'})
                            st.rerun()
                        # 🔥 BOTÓN DE BORRAR EN EL HISTORIAL 🔥
                        if col_del.button("🗑️ Borrar del Historial", key=f"del_h_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).delete()
                            st.rerun()
        else:
            st.info("El historial está vacío.")

else:
    st.info("La base de datos está inicializando.")

# --- FOOTER PROFESIONAL ---
st.markdown("<br><br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; font-size: 0.9rem; opacity: 0.7;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)





