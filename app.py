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

# Lógica de Login/Registro Amigable
if not st.session_state['autenticado']:
    # Usamos session_state para alternar entre login y registro sin usar pestañas
    if 'vista_registro' not in st.session_state:
        st.session_state['vista_registro'] = False

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # Tarjeta de bienvenida más amigable y limpia
        st.markdown("""
            <div style='background: rgba(10, 17, 40, 0.3); padding: 25px; border-radius: 15px; border: 1px solid rgba(0, 242, 255, 0.2); text-align: center; margin-bottom: 25px;'>
                <h3 style='font-family: Orbitron; color: #00f2ff; margin-bottom: 5px; margin-top: 0px;'>👋 ¡Hola de nuevo!</h3>
                <p style='color: #b3cce6; font-size: 0.95rem; margin-bottom: 0px;'>Ingresa para ver el radar de hoy.</p>
            </div>
        """, unsafe_allow_html=True)

        # --- VISTA DE INICIO DE SESIÓN ---
        if not st.session_state['vista_registro']:
            with st.form("f_login"):
                u = st.text_input("Correo electrónico:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("Iniciar sesión", use_container_width=True):
                    res = db.collection('usuarios').document(u).get()
                    if res.exists and res.to_dict()['password'] == encriptar_password(p):
                        st.session_state['autenticado'] = True
                        st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                        st.rerun()
                    else: 
                        st.error("Usuario y/o contraseña incorrecto.")
            
            st.markdown("<p style='text-align: center; color: #b3cce6; margin-top: 15px; font-size: 0.9rem;'>¿No tienes una cuenta?</p>", unsafe_allow_html=True)
            if st.button("Crea tu cuenta aquí", use_container_width=True):
                st.session_state['vista_registro'] = True
                st.rerun()
                
        # --- VISTA DE REGISTRO ---
        else:
            with st.form("f_reg"):
                st.markdown("<p style='text-align: center; color: #bc13fe; font-family: Orbitron; font-weight: bold;'>ÚNETE A AXIOM ANALYTICS</p>", unsafe_allow_html=True)
                un = st.text_input("Tu correo electrónico:")
                pn = st.text_input("Crea una contraseña:", type="password")
                if st.form_submit_button("Crear cuenta", use_container_width=True):
                    # Verificamos que el correo no exista ya
                    doc_ref = db.collection('usuarios').document(un).get()
                    if doc_ref.exists:
                        st.warning("Este correo ya está registrado. Intenta iniciar sesión.")
                    else:
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                        st.success("¡Cuenta creada con éxito! Ya puedes iniciar sesión.")
            
            st.markdown("<p style='text-align: center; color: #b3cce6; margin-top: 15px; font-size: 0.9rem;'>¿Ya tienes una cuenta?</p>", unsafe_allow_html=True)
            if st.button("Volver a iniciar sesión", use_container_width=True):
                st.session_state['vista_registro'] = False
                st.rerun()
                
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

# --- 🚀 PANEL DE CONTROL (ADMIN) ---
if st.session_state['user_rol'] == 'admin':
    st.markdown("### 🛠️ PANEL DE CONTROL (ADMIN)")
    with st.expander("➕ AGREGAR NUEVO ANÁLISIS AL RADAR"):
        with st.form("nuevo_pick"):
            # 🔥 NUEVO SELECTOR DE TIPO DE PICK 🔥
            tipo_pick = st.selectbox("📌 Tipo de Pronóstico:", ["Sencilla (Radar EV+)", "Parlay (La Soñadora)"])
            
            col_p1, col_p2 = st.columns(2)
            partido = col_p1.text_input("⚽ Partido(s):", placeholder="Ej: Real Madrid vs City / Arsenal vs Porto")
            mercado = col_p2.text_input("🎯 Mercado(s):", placeholder="Ej: +2.5 Goles en ambos")
            
            col_n1, col_n2, col_n3, col_n4 = st.columns(4)
            cuota = col_n1.number_input("📈 Cuota Total:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = col_n2.number_input("🏦 Prob. Casa (%):", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
            prob_real = col_n3.number_input("🎯 Prob. Real (%):", min_value=0.0, max_value=100.0, value=55.0, step=0.1)
            ev_val = col_n4.number_input("🔥 EV+ (%):", value=5.0, step=0.1)
            
            ana = st.text_area("🧠 Análisis Táctico o Justificación del Parlay:")
            
            if st.form_submit_button("🚀 PUBLICAR"):
                pick_id = f"{int(time.time())}"
                # Definimos si es parlay o sencilla para la base de datos
                tipo_bd = 'parlay' if 'Parlay' in tipo_pick else 'sencilla'
                
                db.collection('pronosticos').document(pick_id).set({
                    'id': pick_id, 'tipo': tipo_bd, 'partido': partido, 'mercado': mercado, 'cuota': cuota,
                    'prob_casa': prob_casa, 'prob_real': prob_real,
                    'ev': ev_val, 'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success(f"¡{tipo_pick} publicado con éxito!")
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
    # Asegurarnos de que los picks viejos no crasheen si no tienen la etiqueta 'tipo'
    if 'tipo' not in df.columns:
        df['tipo'] = 'sencilla'
        
    # 🗂️ FILTRAMOS LOS DATOS (Sencillas vs Parlays)
    df_activos_sencillas = df[(df['estatus'] == 'PENDIENTE') & (df['tipo'] != 'parlay')]
    df_activos_parlays = df[(df['estatus'] == 'PENDIENTE') & (df['tipo'] == 'parlay')]
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # 🔥 AHORA TENEMOS 3 PESTAÑAS 🔥
    tab_radar, tab_parlay, tab_historial = st.tabs(["🛰️ RADAR EN VIVO", "🌌 LA SOÑADORA", "📖 HISTORIAL"])
    
    # ==========================================
    # 🟢 PESTAÑA 1: RADAR ACTIVO (SOLO SENCILLAS EV+)
    # ==========================================
    with tab_radar:
        if not df_activos_sencillas.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔥 MÁX EV ACTUAL", f"{df_activos_sencillas['ev'].max()}%")
            c2.metric("🎯 ANÁLISIS ACTIVOS", len(df_activos_sencillas))
            c3.metric("🏦 BANK SUGERIDO", "$1,000") 
            c4.metric("🛡️ STATUS", "ONLINE")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            fig = px.bar(df_activos_sencillas, x='ev', y='mercado', orientation='h', color='ev', template="plotly_dark")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<h4 style='color: #b3cce6; font-family: Orbitron;'>PRONÓSTICOS EV+ EN JUEGO</h4>", unsafe_allow_html=True)
            for i, r in df_activos_sencillas.iterrows():
                with st.expander(f"⏳ {r['partido']} | {r['mercado']} | EV+: {r['ev']}%"):
                    pcasa = r.get('prob_casa', 'N/A')
                    preal = r.get('prob_real', 'N/A')
                    st.markdown(f"<p style='color: #bc13fe; font-family: Orbitron; font-size: 0.95rem;'><b>🏦 Prob. Implícita:</b> {pcasa}% &nbsp;&nbsp;|&nbsp;&nbsp; <b>🎯 Prob. Real:</b> {preal}%</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', ''))
                    
                    if st.session_state['user_rol'] == 'admin':
                        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
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
            st.info("No hay pronósticos simples activos. El radar está limpio.")

    # ==========================================
    # 🌌 PESTAÑA 2: LA SOÑADORA (PARLAYS)
    # ==========================================
    with tab_parlay:
        st.markdown("<h4 style='text-align: center; color: #ffd700; font-family: Orbitron;'>🎟️ TICKET DORADO DEL DÍAZ</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b3cce6;'>Combos de alta cuota para buscar el gran golpe con un stake bajo.</p>", unsafe_allow_html=True)
        
        if not df_activos_parlays.empty:
            for i, r in df_activos_parlays.iterrows():
                # Diseño especial para el parlay con bordes dorados
                st.markdown(f"""
                <div style="border: 2px solid #ffd700; border-radius: 10px; padding: 15px; background: rgba(255, 215, 0, 0.05); margin-bottom: 15px;">
                    <h4 style="color: #ffd700; margin-top: 0;">🔥 CUOTA TOTAL: {r['cuota']}</h4>
                    <p style="color: #00f2ff;"><b>Partidos:</b> {r['partido']}</p>
                    <p style="color: #00f2ff;"><b>Mercados:</b> {r['mercado']}</p>
                    <hr style="background: #ffd700;">
                    <p style="color: #ffffff;">{r.get('analisis', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Botones de Admin para el Parlay
                if st.session_state['user_rol'] == 'admin':
                    col_pa, col_pb, col_pc = st.columns(3)
                    if col_pa.button(f"✅ Reventamos la casa", key=f"pwin_{r['id']}"):
                        db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                        st.rerun()
                    if col_pb.button(f"❌ Falló una pata", key=f"ploss_{r['id']}"):
                        db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                        st.rerun()
                    if col_pc.button(f"🗑️ Borrar Parlay", key=f"pdel_{r['id']}"):
                        db.collection('pronosticos').document(r['id']).delete()
                        st.rerun()
        else:
            st.info("Aún no hay Ticket Dorado para hoy. Vuelve más tarde.")
            
    # ==========================================
    # 🔴 PESTAÑA 3: HISTORIAL (EL RESTO DEL CÓDIGO QUEDA IGUAL)
    # ==========================================

# --- FOOTER PROFESIONAL ---
st.markdown("<br><br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; font-size: 0.9rem; opacity: 0.7;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)








