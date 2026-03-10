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
st.set_page_config(page_title="QUASAR ANALYTICS", layout="wide")

# CSS Estilo Galáctico con Glassmorphism
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
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
if 'user_email' not in st.session_state: st.session_state['user_email'] = 'default'

# --- ENCABEZADO CON LOGO QUASAR ---
st.markdown("""
    <div style='text-align: center; margin-bottom: 10px; margin-top: 20px;'>
        <img src="https://raw.githubusercontent.com/victorfelipedata-glitch/torvi-analytics-v2/38bce5a4aa1f6ebf5cf113ebf193f03547f1dd2c/logo.jpg" width="350" style="border-radius: 15px; box-shadow: 0px 0px 25px rgba(188, 19, 254, 0.5);">
    </div>
    """, unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA (EV+)</p>', unsafe_allow_html=True)

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
                        if res.exists and res.to_dict()['password'] == encriptar_password(p):
                            st.session_state['autenticado'] = True
                            st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                            st.session_state['user_email'] = u
                            st.rerun()
                        else: st.error("Credenciales incorrectas. Verifica tu correo y clave.")
                    else: st.warning("Por favor, ingresa tu correo electrónico.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARME AHORA", use_container_width=True):
                    if un and pn:
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip', 'bankroll': 1000.0})
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                    else: st.warning("Completa todos los campos para continuar.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- CARGA DE DATOS ---
# Picks
docs_picks = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data_picks = []
for d in docs_picks:
    item = d.to_dict()
    if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
    data_picks.append(item)
df = pd.DataFrame(data_picks) if data_picks else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus', 'id'])

# Portafolio Activo del Usuario
docs_port = db.collection('portafolio').where('user', '==', st.session_state['user_email']).stream()
data_port = [d.to_dict() for d in docs_port]
df_port = pd.DataFrame(data_port) if data_port else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'monto'])

# Bankroll del Usuario
user_ref = db.collection('usuarios').document(st.session_state['user_email'])
user_data = user_ref.get().to_dict() if user_ref.get().exists else {}
bank_actual = user_data.get('bankroll', 1000.0)

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
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # Métricas
    m1, m2, m3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    m1.metric("🔥 MAYOR VENTAJA (EV+)", max_ev)
    m2.metric("🎯 EN EL RADAR", len(df_activos))
    m3.metric("🏦 MI CAPITAL (BANK)", f"${bank_actual:,.2f}")
    
    tab_radar, tab_parlay, tab_portafolio, tab_historial, tab_tools = st.tabs(["🛰️ RADAR", "💎 PARLAY VIP", "💼 MI PORTAFOLIO", "📈 HISTORIAL", "⚙️ PERFIL"])
    
    with tab_radar:
        if not df_activos.empty:
            for i, r in df_activos.iterrows():
                # Ocultamos los parlays de esta pestaña
                if "Parlay" in str(r['partido']): continue 
                
                sugerencia_stake = bank_actual * 0.05 
                
                st.markdown(f"""
                    <div style='background: rgba(10, 17, 40, 0.7); padding: 20px; border-radius: 15px; border: 1px solid #00f2ff; margin-bottom: 20px;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <h3 style='color: white; margin: 0;'>{r['partido'].replace('[SENCILLA] ', '').replace('[Otra] ', '')}</h3>
                            <span style='color: #00ff00; font-family: Orbitron;'>EV+ {r['ev']}%</span>
                        </div>
                        <p style='color: #bc13fe; font-weight: bold;'>🎯 {r['mercado']}</p>
                        <div style='display: flex; gap: 10px; margin: 10px 0;'>
                            <div style='background: #000; padding: 5px 15px; border-radius: 5px; color: #00f2ff;'>CUOTA: {r['cuota']}</div>
                            <div style='background: #000; padding: 5px 15px; border-radius: 5px; color: #00f2ff;'>PROB. REAL: {r.get('prob_real',0)}%</div>
                        </div>
                        <div style='background: rgba(0, 242, 255, 0.1); padding: 10px; border-radius: 8px; border-left: 4px solid #00f2ff; color: white;'>
                            💡 <b>Gestión de Riesgo:</b> Sugerencia del 5.0% de tu Bankroll (${sugerencia_stake:,.2f})
                        </div>
                        <p style='margin-top: 15px; font-size: 0.9rem; color: #b3cce6;'>{r.get('analisis', 'Análisis en proceso...')}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns([1, 2])
                if col_btn1.button(f"📥 Guardar en Mi Portafolio", key=f"port_{r['id']}"):
                    db.collection('portafolio').document(f"{st.session_state['user_email']}_{r['id']}").set({
                        'user': st.session_state['user_email'], 'partido': r['partido'], 'mercado': r['mercado'],
                        'cuota': r['cuota'], 'monto': sugerencia_stake, 'fecha': datetime.now()
                    })
                    st.toast("Añadido al portafolio activo")
                    
                if st.session_state['user_rol'] == 'admin':
                    c_wa, c_wb = st.columns(2)
                    if c_wa.button(f"✅ Ganada", key=f"w_{r['id']}"):
                        db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                        st.rerun()
                    if c_wb.button(f"❌ Perdida", key=f"l_{r['id']}"):
                        db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                        st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No hay señales activas. El radar está buscando nuevas ventajas...")

    with tab_parlay:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #1a0b2e 0%, #bc13fe 100%); 
                        padding: 25px; border-radius: 20px; border: 2px solid #ffcc00; 
                        box-shadow: 0px 0px 20px rgba(188, 19, 254, 0.5);'>
                <h2 style='text-align: center; color: #ffcc00; font-family: Orbitron; margin:0;'>👑 PARLAY EXCLUSIVO VIP</h2>
                <p style='text-align: center; color: #00f2ff; letter-spacing: 2px; margin:0;'>ACCESO DE ALTA VENTAJA ESTADÍSTICA</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False)]
        if not df_parlays.empty:
            for i, p in df_parlays.iterrows():
                st.markdown(f"""
                    <div style='background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #ffcc00;'>
                        <h4 style='color: #ffcc00; margin-bottom: 5px;'>{p['mercado']}</h4>
                        <p style='color: #00f2ff; font-weight: bold;'>CUOTA FINAL: {p['cuota']} | EV+: {p['ev']}%</p>
                        <p style='font-size: 0.9rem; color: white;'>{p['analisis']}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.session_state['user_rol'] == 'admin':
                    c_pa, c_pb = st.columns(2)
                    if c_pa.button(f"✅ Cobrar Parlay", key=f"wp_{p['id']}"):
                        db.collection('pronosticos').document(p['id']).update({'estatus': 'GANADA'})
                        st.rerun()
                    if c_pb.button(f"❌ Fallado", key=f"lp_{p['id']}"):
                        db.collection('pronosticos').document(p['id']).update({'estatus': 'PERDIDA'})
                        st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("El equipo de analistas está terminando de procesar la combinada de hoy. Vuelve en unos minutos...")

    with tab_portafolio:
        st.markdown("### 💼 MIS INVERSIONES ACTIVAS")
        if not df_port.empty:
            inversion_total = df_port['monto'].sum()
            st.markdown(f"<p style='font-size: 1.2rem; color: #00f2ff;'>Total en Riesgo: <b>${inversion_total:,.2f}</b></p>", unsafe_allow_html=True)
            for i, r in df_port.iterrows():
                st.markdown(f"<div style='border-left: 3px solid #bc13fe; padding-left: 10px; margin-bottom: 10px;'><b style='color:white;'>{r['partido']}</b><br><span style='color:#b3cce6;'>{r['mercado']} | Inversión: ${r['monto']:.2f}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Aún no tienes apuestas guardadas en tu portafolio activo.")

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
                with st.expander(f"{icon} {r['partido']} | {r['mercado']}"):
                    st.write(f"Cuota: {r['cuota']} | Ventaja: {r['ev']}%")
                    if st.session_state['user_rol'] == 'admin':
                        if st.button("🔄 Revertir", key=f"rev_{r['id']}"):
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'})
                            st.rerun()
        else:
            st.info("El historial aparecerá aquí conforme se resuelvan los partidos.")

    with tab_tools:
        st.markdown("### ⚙️ CONFIGURACIÓN DE CUENTA")
        col_u1, col_u2 = st.columns([2, 1])
        nuevo_bank = col_u1.number_input("Capital Total (Bankroll):", value=float(bank_actual), step=50.0)
        
        if col_u2.button("💾 ACTUALIZAR DATOS"):
            user_ref.update({'bankroll': nuevo_bank})
            st.success("Sincronizando con servidores...")
            time.sleep(1)
            st.rerun()

else:
    st.info("Base de datos vacía. Esperando primer análisis...")

st.markdown("<br><hr><p style='text-align: center; color: #00f2ff; font-family: Orbitron; font-size: 0.8rem; opacity: 0.6;'>© 2026 DESARROLLADO POR QUASAR ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)


