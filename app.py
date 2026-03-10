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
st.set_page_config(page_title="AXIOM DATA", layout="wide")

# CSS Estilo Galáctico con Glassmorphism
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
    .titulo-futurista { font-family: 'Orbitron', sans-serif; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px;}
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; font-size: 0.8rem;}
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.6); backdrop-filter: blur(10px); border: 1px solid #00f2ff; border-radius: 10px; text-align: center; }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.1); border-radius: 10px 10px 0 0; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.2) !important; border-bottom: 2px solid #00f2ff !important; }
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
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; padding: 20px; background: rgba(0,242,255,0.05); border-radius: 20px; border: 1px solid rgba(0,242,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>👋 ¡Hola de nuevo!</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #b3cce6;'>Ingresa para ver el radar de valor de hoy.</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🚀 INICIAR SESIÓN", "📝 CREAR CUENTA"])
        with t1:
            with st.form("f_login"):
                u = st.text_input("Correo electrónico:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("INICIAR SESIÓN", use_container_width=True):
                    if u: # Corregimos el error de campo vacío
                        res = db.collection('usuarios').document(u).get()
                        if res.exists and res.to_dict()['password'] == encriptar_password(p):
                            st.session_state['autenticado'] = True
                            st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                            st.rerun()
                        else: st.error("Credenciales incorrectas. Verifica tu correo y clave.")
                    else: st.warning("Por favor, ingresa tu correo electrónico.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARME AHORA", use_container_width=True):
                    if un and pn:
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                    else: st.warning("Completa todos los campos para continuar.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- CARGA DE DATOS ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data = []
for d in docs:
    item = d.to_dict()
    if 'estatus' not in item: item['estatus'] = 'PENDIENTE' # Recuperamos picks viejos
    data.append(item)

df = pd.DataFrame(data) if data else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# --- SIDEBAR ---
st.sidebar.title("📟 CONSOLA")
st.sidebar.write(f"Usuario: {st.session_state['user_rol'].upper()}")
if st.sidebar.button("🚪 CERRAR SESIÓN"):
    st.session_state['autenticado'] = False
    st.rerun()

# --- PANEL DE ADMIN ---
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ PANEL DE CONTROL (AGREGAR PRONÓSTICO)"):
        with st.form("nuevo_pick"):
            c_a, c_b = st.columns(2)
            partido = c_a.text_input("⚽ Encuentro:", placeholder="Ej: Man City vs Liverpool")
            mercado = c_b.text_input("🎯 Mercado:", placeholder="Ej: +4.5 Tiros a Puerta")
            
            c_n1, c_n2, c_n3, c_n4 = st.columns(4)
            cuota = c_n1.number_input("📈 Cuota:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = c_n2.number_input("🏦 Prob. Casa %:", value=50.0)
            prob_real = c_n3.number_input("🎯 Prob. Real %:", value=60.0)
            ev_val = c_n4.number_input("🔥 EV+ %:", value=10.0)
            
            ana = st.text_area("🧠 Análisis Táctico y Matemático:")
            if st.form_submit_button("🚀 PUBLICAR EN EL RADAR"):
                p_id = f"{int(time.time())}"
                db.collection('pronosticos').document(p_id).set({
                    'id': p_id, 'partido': partido, 'mercado': mercado, 'cuota': cuota,
                    'prob_casa': prob_casa, 'prob_real': prob_real, 'ev': ev_val,
                    'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("Publicado con éxito.")
                st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    # Filtros de estado
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # Métricas de la parte superior
    m1, m2, m3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    m1.metric("🔥 MÁXIMA VENTAJA", max_ev)
    m2.metric("🎯 PICKS ACTIVOS", len(df_activos))
    # Bankroll dinámico basado en historial
    ganancias = len(df_historial[df_historial['estatus'] == 'GANADA']) * 80 # Asumiendo ganancia promedio
    perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA']) * 100
    bank_total = 1000 + ganancias - perdidas
    m3.metric("🏦 MI CAPITAL (BANK)", f"${bank_total:,.2f}")
    
    # NUEVA ESTRUCTURA DE PESTAÑAS VIP
    tab_futbol, tab_parlay, tab_historial, tab_tools = st.tabs(["⚽ FÚTBOL", "💎 PARLAY DIARIO", "📈 RENDIMIENTO", "🧮 TOOLS"])
    
    with tab_futbol:
        if not df_activos.empty:
            st.markdown("<h4 style='color: #00f2ff; font-family: Orbitron;'>🛰️ RADAR DE SEÑALES</h4>", unsafe_allow_html=True)
            for i, r in df_activos.iterrows():
                # Limpiamos el título quitando [SENCILLA] o etiquetas raras
                titulo_limpio = r['partido'].replace("[SENCILLA] ", "").replace("[Otra] ", "")
                with st.expander(f"📍 {titulo_limpio} | {r['mercado']} | EV+: {r['ev']}%"):
                    st.markdown(f"<p style='color: #bc13fe; font-size: 0.85rem;'>PROB. REAL: {r.get('prob_real',0)}% | CUOTA: {r['cuota']}</p>", unsafe_allow_html=True)
                    st.info(r.get('analisis', 'Analizando datos tácticos...'))
                    if st.session_state['user_rol'] == 'admin':
                        ca, cb = st.columns(2)
                        if ca.button(f"✅ Ganó", key=f"w_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Perdió", key=f"l_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
        else:
            st.info("Buscando nuevas ventajas en las ligas europeas...")

    with tab_parlay:
        st.markdown("<div style='background: linear-gradient(45deg, #1a0b2e, #bc13fe33); padding: 20px; border-radius: 15px; border: 1px solid #bc13fe;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #ffcc00; font-family: Orbitron;'>⭐ PARLAY VIP DEL DÍA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white;'>Esta sección solo es visible para miembros con acceso de alta ventaja.</p>", unsafe_allow_html=True)
        
        # Aquí puedes filtrar por picks que tengan la palabra "Parlay" en el nombre
        df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False)]
        if not df_parlays.empty:
            for i, p in df_parlays.iterrows():
                st.success(f"🚀 {p['mercado']} - Momio: {p['cuota']}")
                st.write(p['analisis'])
        else:
            st.markdown("<p style='text-align: center; opacity: 0.5;'>Cocinando la combinada de hoy... ⏳</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_historial:
        if not df_historial.empty:
            # Gráfica de crecimiento
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            st.markdown(f"### Win Rate Global: {wr:.1f}%")
            # Gráfica simple de barras por estatus
            resumen = df_historial.groupby('estatus').size().reset_index(name='cantidad')
            fig_h = px.pie(resumen, values='cantidad', names='estatus', color='estatus',
                           color_discrete_map={'GANADA': '#00ff00', 'PERDIDA': '#ff0000'},
                           hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.info("El historial se construye con tus aciertos.")

    with tab_tools:
        st.markdown("### 🧮 CALCULADORAS DE GESTIÓN")
        # Aquí pones el código de tus calculadoras de Kelly y Hedge que ya tienes
        st.write("Usa estas herramientas para proteger tu capital.")

else:
    st.info("Bienvenido a Axiom Data. Esperando actualización del radar...")

