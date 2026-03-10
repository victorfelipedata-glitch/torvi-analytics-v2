import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AXIOM DATA", layout="wide")

# --- CSS ESTILO GALÁCTICO / NEÓN ---
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

# --- CONEXIÓN A FIREBASE ---
if not firebase_admin._apps:
    dict_claves = json.loads(st.secrets["firebase_key"])
    cred = credentials.Certificate(dict_claves)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- SEGURIDAD Y SESIÓN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'
if 'user_email' not in st.session_state: st.session_state['user_email'] = ''

st.markdown('<p class="titulo-futurista">AXIOM DATA</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

# --- PANTALLA DE LOGIN ---
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
                    if u: 
                        res = db.collection('usuarios').document(u).get()
                        if res.exists and res.to_dict().get('password') == encriptar_password(p):
                            st.session_state['autenticado'] = True
                            st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                            st.session_state['user_email'] = u  # Guardamos el correo en sesión
                            st.rerun()
                        else: st.error("Credenciales incorrectas. Verifica tu correo y clave.")
                    else: st.warning("Por favor, ingresa tu correo electrónico.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARME AHORA", use_container_width=True):
                    if un and pn:
                        # Creamos el usuario con un bankroll inicial por defecto de 1000
                        db.collection('usuarios').document(un).set({
                            'correo': un, 
                            'password': encriptar_password(pn), 
                            'rol': 'usuario_vip',
                            'bankroll': 1000.0
                        })
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                    else: st.warning("Completa todos los campos para continuar.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- RECUPERAR DATOS DEL USUARIO ---
user_doc = db.collection('usuarios').document(st.session_state['user_email']).get()
user_data = user_doc.to_dict() if user_doc.exists else {}
base_bankroll = float(user_data.get('bankroll', 1000.0))

# --- CARGA DE PRONÓSTICOS ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data = []
for d in docs:
    item = d.to_dict()
    if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
    data.append(item)

df = pd.DataFrame(data) if data else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# --- SIDEBAR ---
st.sidebar.title("📟 CONSOLA")
st.sidebar.write(f"**Usuario:** {st.session_state['user_email']}")
st.sidebar.write(f"**Nivel:** {st.session_state['user_rol'].upper()}")
if st.sidebar.button("🚪 CERRAR SESIÓN"):
    st.session_state['autenticado'] = False
    st.session_state['user_email'] = ''
    st.rerun()

# --- PANEL DE ADMIN ---
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ PANEL DE CONTROL (AGREGAR PRONÓSTICO)"):
        with st.form("nuevo_pick"):
            c_a, c_b = st.columns(2)
            st.info("💡 Tip: Si escribes la palabra 'Parlay' en el Encuentro, se irá a la pestaña VIP.")
            partido = c_a.text_input("⚽ Encuentro / Nombre:", placeholder="Ej: Parlay del Día")
            mercado = c_b.text_input("🎯 Mercado:", placeholder="Ej: +1.5 Goles y Local Gana")
            
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
                st.success("¡Publicado con éxito!")
                st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']
    
    # Separamos normales de parlays
    df_normales = df_activos[~df_activos['partido'].str.contains("Parlay", case=False, na=False)]
    df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False, na=False)]

    # Métricas Top
    m1, m2, m3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    m1.metric("🔥 MAYOR VENTAJA", max_ev)
    m2.metric("🎯 OPORTUNIDADES ACTIVAS", len(df_activos))
    m3.metric("🏦 BANKROLL ACTUAL", f"${base_bankroll:,.2f}")
    
    # SISTEMA DE PESTAÑAS
    tab_futbol, tab_parlay, tab_historial, tab_tools = st.tabs(["⚽ FÚTBOL", "💎 PARLAY VIP", "📈 HISTORIAL", "⚙️ MI PERFIL & TOOLS"])
    
    # --- PESTAÑA FÚTBOL (Sencillas) ---
    with tab_futbol:
        if not df_normales.empty:
            for i, r in df_normales.iterrows():
                # Limpiamos basurita visual como [SENCILLA] o [Otra]
                titulo_limpio = str(r['partido']).replace("[SENCILLA]", "").replace("[Otra]", "").strip()
                with st.expander(f"📍 {titulo_limpio} | {r['mercado']} | EV+: {r['ev']}%"):
                    st.markdown(f"<p style='color: #bc13fe; font-size: 0.9rem;'>🏦 Prob. Casa: {r.get('prob_casa',0)}% | 🎯 Prob. Real: {r.get('prob_real',0)}% | 📈 Cuota: {r['cuota']}</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', 'Análisis en proceso...'))
                    if st.session_state['user_rol'] == 'admin':
                        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                        ca, cb = st.columns(2)
                        if ca.button(f"✅ Ganada", key=f"w_n_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Perdida", key=f"l_n_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
        else:
            st.info("No hay señales individuales activas. El radar está buscando nuevas ventajas...")

    # --- PESTAÑA PARLAY VIP ---
    with tab_parlay:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #1a0b2e 0%, #3a0d5c 100%); 
                        padding: 25px; border-radius: 20px; border: 2px solid #ffcc00; 
                        box-shadow: 0px 0px 20px rgba(188, 19, 254, 0.3); margin-bottom: 20px;'>
                <h2 style='text-align: center; color: #ffcc00; font-family: Orbitron; margin-bottom: 5px;'>👑 PARLAY EXCLUSIVO VIP</h2>
                <p style='text-align: center; color: #00f2ff; letter-spacing: 2px; font-size: 0.8rem;'>ACCESO DE ALTA VENTAJA ESTADÍSTICA</p>
            </div>
        """, unsafe_allow_html=True)
        
        if not df_parlays.empty:
            for i, p in df_parlays.iterrows():
                with st.container():
                    st.markdown(f"""
                        <div style='background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #ffcc00; margin-bottom: 15px;'>
                            <h4 style='color: #ffcc00; margin-bottom: 10px; font-family: Orbitron;'>{str(p['partido']).replace("[PARLAY]", "").strip()}</h4>
                            <p style='color: white; font-size: 1.1rem; margin-bottom: 5px;'>🎯 <b>Mercado:</b> {p['mercado']}</p>
                            <p style='color: #00f2ff; font-weight: bold; font-size: 1.1rem; margin-bottom: 15px;'>📈 CUOTA FINAL: {p['cuota']} &nbsp;|&nbsp; 🔥 EV+: {p['ev']}%</p>
                            <div style='background: rgba(0,0,0,0.5); padding: 15px; border-radius: 8px; color: #e0e0e0;'>
                                {p.get('analisis', '')}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.session_state['user_rol'] == 'admin':
                        ca, cb = st.columns(2)
                        if ca.button(f"✅ Parlay Acertado", key=f"w_p_{p['id']}"):
                            db.collection('pronosticos').document(p['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        if cb.button(f"❌ Parlay Fallado", key=f"l_p_{p['id']}"):
                            db.collection('pronosticos').document(p['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
        else:
            st.info("El equipo de analistas está terminando de procesar la combinada de hoy. Vuelve en unos minutos...")

    # --- PESTAÑA HISTORIAL ---
    with tab_historial:
        if not df_historial.empty:
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            c_h1, c_h2, c_h3 = st.columns(3)
            c_h1.metric("✅ ACIERTOS", ganadas)
            c_h2.metric("❌ FALLOS", perdidas)
            c_h3.metric("📈 WIN RATE GLOBAL", f"{wr:.1f}%")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            for i, r in df_historial.iterrows():
                icon = "✅" if r['estatus'] == 'GANADA' else "❌"
                color = "#00ff00" if r['estatus'] == 'GANADA' else "#ff0000"
                with st.expander(f"{icon} {r['partido']} | {r['mercado']}"):
                    st.markdown(f"<p style='color: {color}; font-weight: bold;'>CUOTA: {r['cuota']} | EV+: {r['ev']}%</p>", unsafe_allow_html=True)
                    st.write(r.get('analisis', ''))
                    if st.session_state['user_rol'] == 'admin':
                        if st.button("🔄 Revertir Estado", key=f"rev_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'})
                            st.rerun()
        else:
            st.info("El historial aparecerá aquí conforme se resuelvan los partidos.")

    # --- PESTAÑA MI PERFIL Y TOOLS ---
    with tab_tools:
        st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>⚙️ CONFIGURACIÓN DE CUENTA</h3>", unsafe_allow_html=True)
        st.write(f"**Usuario activo:** {st.session_state['user_email']}")
        
        # Formulario para actualizar el Bankroll en Firebase
        with st.form("form_bankroll"):
            nuevo_bank = st.number_input("Capital Inicial (Bankroll Fijo):", value=base_bankroll, step=10.0)
            submit_bank = st.form_submit_button("💾 Guardar Cambios")
            
            if submit_bank:
                db.collection('usuarios').document(st.session_state['user_email']).update({
                    'bankroll': nuevo_bank
                })
                st.success("¡Bankroll actualizado y guardado en la nube con éxito!")
                time.sleep(1.5)
                st.rerun()
                
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #ffcc00; font-family: Orbitron;'>🧮 CALCULADORAS VIP</h3>", unsafe_allow_html=True)
        st.info("Herramientas de gestión de riesgo (Kelly, Cashout) en construcción...")

else:
    st.info("Base de datos conectada. Esperando primer análisis...")

st.markdown("<br><hr><p style='text-align: center; color: #00f2ff; font-family: Orbitron; font-size: 0.8rem; opacity: 0.6;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)
