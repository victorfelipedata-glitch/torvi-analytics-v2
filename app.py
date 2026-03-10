import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid # 👈 Nueva librería para generar IDs únicos infalibles

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
                    # 👈 CORRECCIÓN 1: Evitar consulta vacía para quitar el error rojo
                    u_limpio = u.strip()
                    if u_limpio: 
                        try:
                            res = db.collection('usuarios').document(u_limpio).get()
                            if res.exists and res.to_dict().get('password') == encriptar_password(p):
                                st.session_state['autenticado'] = True
                                st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                                st.rerun()
                            else: st.error("Credenciales incorrectas. Verifica tu correo y clave.")
                        except Exception as e:
                            st.error("Error al validar datos. Revisa el formato de tu correo.")
                    else: 
                        st.warning("Por favor, ingresa tu correo electrónico.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARME AHORA", use_container_width=True):
                    un_limpio = un.strip()
                    if un_limpio and pn:
                        db.collection('usuarios').document(un_limpio).set({'correo': un_limpio, 'password': encriptar_password(pn), 'rol': 'usuario_vip'})
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                    else: st.warning("Completa todos los campos para continuar.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- CARGA DE DATOS ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data = []
for d in docs:
    item = d.to_dict()
    if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
    if 'id' not in item: item['id'] = str(uuid.uuid4()) # ID de respaldo por si falta
    data.append(item)

df = pd.DataFrame(data) if data else pd.DataFrame(columns=['id', 'partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# 👈 CORRECCIÓN 2: Forzar números para que la gráfica no explote
if not df.empty:
    df['ev'] = pd.to_numeric(df['ev'], errors='coerce').fillna(0)
    df['cuota'] = pd.to_numeric(df['cuota'], errors='coerce').fillna(0)

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
                # 👈 CORRECCIÓN 3: Generar un ID verdaderamente único
                p_id = str(uuid.uuid4())
                db.collection('pronosticos').document(p_id).set({
                    'id': p_id, 'partido': partido, 'mercado': mercado, 'cuota': float(cuota),
                    'prob_casa': float(prob_casa), 'prob_real': float(prob_real), 'ev': float(ev_val),
                    'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("Publicado con éxito.")
                st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # Métricas
    m1, m2, m3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    m1.metric("🔥 MAYOR VENTAJA (EV+)", max_ev)
    m2.metric("🎯 OPORTUNIDADES ACTIVAS", len(df_activos))
    m3.metric("🏦 TU CAPITAL ACTUAL", "$1000.00")
    
    tab_radar, tab_historial = st.tabs(["🛰️ RADAR DE VALOR", "📖 HISTORIAL Y RENDIMIENTO"])
    
    with tab_radar:
        if not df_activos.empty:
            try:
                fig = px.bar(df_activos, x='ev', y='mercado', orientation='h', color='ev', 
                             template="plotly_dark", labels={'ev': 'Ventaja %', 'mercado': 'Mercado'})
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning("Ajustando gráfica... Se recuperará en el próximo pick.")

            for i, r in df_activos.iterrows():
                with st.expander(f"📌 {r.get('partido', 'Partido')} | {r.get('mercado', 'Mercado')} | EV+: {r.get('ev', 0)}%"):
                    st.markdown(f"<p style='color: #bc13fe; font-size: 0.9rem;'>🏦 Prob. Casa: {r.get('prob_casa',0)}% | 🎯 Prob. Real: {r.get('prob_real',0)}%</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', 'Análisis en proceso...'))
                    if st.session_state['user_rol'] == 'admin':
                        ca, cb = st.columns(2)
                        # 👈 CORRECCIÓN 4: Claves (keys) únicas para cada botón usando el índice 'i'
                        if ca.button(f"✅ Ganada", key=f"w_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Perdida", key=f"l_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
        else:
            st.info("No hay señales activas. El radar está buscando nuevas ventajas...")

    with tab_historial:
        if not df_historial.empty:
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            c_h1, c_h2, c_h3 = st.columns(3)
            c_h1.metric("✅ ACIERTOS", ganadas)
            c_h2.metric("❌ FALLOS", perdidas)
            c_h3.metric("📈 WIN RATE", f"{wr:.1f}%")
            
            for i, r in df_historial.iterrows():
                icon = "✅" if r['estatus'] == 'GANADA' else "❌"
                with st.expander(f"{icon} {r.get('partido', '')} | {r.get('mercado', '')}"):
                    st.write(f"Cuota: {r.get('cuota', 0)} | Ventaja: {r.get('ev', 0)}%")
                    st.write(r.get('analisis', ''))
                    if st.session_state['user_rol'] == 'admin':
                        if st.button("🔄 Revertir", key=f"rev_{r['id']}_{i}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'})
                            st.rerun()
        else:
            st.info("El historial aparecerá aquí conforme se resuelvan los partidos.")

else:
    st.info("Base de datos vacía. Esperando primer análisis...")

st.markdown("<br><hr><p style='text-align: center; color: #00f2ff; font-family: Orbitron; font-size: 0.8rem; opacity: 0.6;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)
