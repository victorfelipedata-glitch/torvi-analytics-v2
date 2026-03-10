import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="AXIOM DATA", layout="wide")

# 2. Estilos CSS Personalizados (Axiom Design)
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
    
    /* Estilo de pestañas VIP */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.05); border-radius: 10px 10px 0 0; color: #b3cce6; padding: 10px 20px; font-family: 'Orbitron'; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.1) !important; border-bottom: 2px solid #00f2ff !important; color: #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Conexión a Firebase
if not firebase_admin._apps:
    dict_claves = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(dict_claves)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 4. Gestión de Sesión
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'

st.markdown('<p class="titulo-futurista">AXIOM DATA</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

# 5. Interfaz de Acceso
if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; padding: 20px; background: rgba(0,242,255,0.05); border-radius: 20px; border: 1px solid rgba(0,242,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>🔓 ACCESO AL RADAR</h3>", unsafe_allow_html=True)
        
        t_login, t_reg = st.tabs(["🚀 INICIAR SESIÓN", "📝 REGISTRO"])
        with t_login:
            with st.form("login_form"):
                u = st.text_input("Usuario (Correo):")
                p = st.text_input("Clave:", type="password")
                if st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True):
                    if u:
                        res = db.collection('usuarios').document(u).get()
                        if res.exists and res.to_dict()['password'] == encriptar_password(p):
                            st.session_state['autenticado'] = True
                            st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                            st.rerun()
                        else: st.error("Credenciales incorrectas.")
                    else: st.warning("Ingresa un usuario.")
        with t_reg:
            with st.form("reg_form"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Clave:", type="password")
                if st.form_submit_button("CREAR CUENTA VIP", use_container_width=True):
                    if un and pn:
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                        st.success("¡Cuenta creada! Inicia sesión.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 6. Carga de Datos y Limpieza
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data_list = []
for d in docs:
    item = d.to_dict()
    if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
    # Limpiamos el ruido de los títulos viejos
    item['partido'] = item['partido'].replace("[SENCILLA] ", "").replace("[Otra] ", "").replace("[OTRA] ", "")
    data_list.append(item)

df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'ev', 'estatus'])

# 7. Sidebar
st.sidebar.markdown(f"### 🛡️ SESIÓN: {st.session_state['user_rol'].upper()}")
if st.sidebar.button("🚪 CERRAR SESIÓN"):
    st.session_state['autenticado'] = False
    st.rerun()

# 8. Panel Administrativo (Solo Admin)
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ PANEL DE CONTROL - PUBLICAR"):
        with st.form("admin_pick"):
            c1, c2 = st.columns(2)
            partido_in = c1.text_input("⚽ Encuentro:")
            mercado_in = c2.text_input("🎯 Mercado:")
            
            cn1, cn2, cn3, cn4 = st.columns(4)
            cuota_in = cn1.number_input("📈 Cuota:", value=1.90, step=0.01)
            pcasa_in = cn2.number_input("🏦 Prob. Casa %:", value=50.0)
            preal_in = cn3.number_input("🎯 Prob. Real %:", value=55.0)
            ev_in = cn4.number_input("🔥 EV+ %:", value=5.0)
            
            ana_in = st.text_area("🧠 Análisis Táctico:")
            if st.form_submit_button("🚀 LANZAR AL RADAR"):
                pid = f"{int(time.time())}"
                db.collection('pronosticos').document(pid).set({
                    'id': pid, 'partido': partido_in, 'mercado': mercado_in, 'cuota': cuota_in,
                    'prob_casa': pcasa_in, 'prob_real': preal_in, 'ev': ev_in,
                    'analisis': ana_in, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("¡Pick publicado!")
                st.rerun()

# 9. Dashboard Principal
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # Métricas de Cabecera
    met1, met2, met3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    met1.metric("🔥 MÁXIMA VENTAJA", max_ev)
    met2.metric("🎯 PICKS ACTIVOS", len(df_activos))
    
    # Cálculo de Bank dinámico para darle vida a la UI
    wins = len(df_historial[df_historial['estatus'] == 'GANADA'])
    losses = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
    met3.metric("🏦 BANKROLL ESTIMADO", f"${1000 + (wins*85) - (losses*100):,.2f}")

    # ESTRUCTURA DE PESTAÑAS VIP
    t_futbol, t_parlay, t_hist, t_calc = st.tabs(["⚽ FÚTBOL", "💎 PARLAY VIP", "📈 RENDIMIENTO", "🧮 CALCULADORAS"])
    
    with t_futbol:
        if not df_activos.empty:
            for i, r in df_activos.iterrows():
                if "PARLAY" not in r['partido'].upper():
                    with st.expander(f"📍 {r['partido']} | {r['mercado']} | EV+: {r['ev']}%"):
                        st.markdown(f"<p style='color: #bc13fe; font-size: 0.85rem;'>PROB. REAL: {r.get('prob_real',0)}% | CUOTA: {r['cuota']}</p>", unsafe_allow_html=True)
                        st.write(r.get('analisis', 'Análisis táctico en proceso...'))
                        if st.session_state['user_rol'] == 'admin':
                            ca, cb = st.columns(2)
                            if ca.button(f"✅ Ganada", key=f"w_{r['id']}"):
                                db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                                st.rerun()
                            if cb.button(f"❌ Perdida", key=f"l_{r['id']}"):
                                db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                                st.rerun()
        else:
            st.info("No hay señales de fútbol activas. Esperando ventaja estadística...")

    with t_parlay:
        st.markdown("<div style='background: linear-gradient(45deg, #1a0b2e, #bc13fe33); padding: 25px; border-radius: 15px; border: 1px solid #bc13fe; box-shadow: 0 0 20px rgba(188, 19, 254, 0.2);'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #ffcc00; font-family: Orbitron; text-shadow: 0 0 10px #ffcc00;'>🎫 PARLAY DEL DÍA</h2>", unsafe_allow_html=True)
        
        parlays_activos = df_activos[df_activos['partido'].str.contains("PARLAY", case=False)]
        if not parlays_activos.empty:
            for i, p in parlays_activos.iterrows():
                st.markdown(f"### 🚀 {p['mercado']}")
                st.markdown(f"**Cuota Combinada:** {p['cuota']} | **Ventaja:** {p['ev']}%")
                st.success(p['analisis'])
                if st.session_state['user_rol'] == 'admin':
                    if st.button("✅ Resolver Parlay", key=f"wp_{p['id']}"):
                        db.collection('pronosticos').document(p['id']).update({'estatus': 'GANADA'})
                        st.rerun()
        else:
            st.markdown("<p style='text-align: center; opacity: 0.6;'>Cocinando la combinada de alta ventaja... ⏳</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with t_hist:
        if not df_historial.empty:
            h1, h2, h3 = st.columns(3)
            h1.metric("✅ ACIERTOS", wins)
            h2.metric("❌ FALLOS", losses)
            h3.metric("📊 WIN RATE", f"{(wins/(wins+losses)*100) if (wins+losses)>0 else 0:.1f}%")
            
            st.markdown("#### ÚLTIMOS RESULTADOS")
            for i, r in df_historial.iterrows():
                status_icon = "🟢" if r['estatus'] == 'GANADA' else "🔴"
                with st.expander(f"{status_icon} {r['partido']} | {r['mercado']}"):
                    st.write(r['analisis'])
        else:
            st.info("Historial vacío. Las jugadas resueltas aparecerán aquí.")

    with t_calc:
        st.markdown("### 🧮 GESTIÓN DE RIESGO")
        c_kelly, c_hedge = st.columns(2)
        with c_kelly:
            st.markdown("#### Criterio de Kelly")
            k_bank = st.number_input("Bankroll ($):", value=1000)
            k_cuota = st.number_input("Cuota:", value=2.0)
            k_prob = st.number_input("Probabilidad Real (%):", value=55.0)
            if st.button("Calcular Stake"):
                p = k_prob/100
                q = 1 - p
                b = k_cuota - 1
                f = (b * p - q) / b
                st.write(f"Inversión recomendada: **{f*100:.2f}%** del bank (${k_bank*f:.2f})")
        with c_hedge:
            st.markdown("#### Cobertura (Hedge)")
            st.write("Calcula cuánto apostar a la contra para asegurar ganancias.")
            # Aquí podrías poner campos básicos de hedge
else:
    st.info("Axiom Data está sincronizando con los mercados mundiales...")

# 10. Footer
st.markdown("<br><br><hr><p style='text-align: center; color: #00f2ff; font-family: Orbitron; font-size: 0.8rem; opacity: 0.6;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)
