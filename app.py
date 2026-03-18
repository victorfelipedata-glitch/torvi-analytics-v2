import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import numpy as np

# Configuro mi página
st.set_page_config(page_title="QUASAR ANALYTICS", layout="wide", initial_sidebar_state="collapsed")

# 🔄 Auto-Refresh Silencioso (30 segundos para soportar a tus usuarios VIP sin quemar Firebase)
st_autorefresh(interval=30000, limit=None, key="quasar_autorefresh")

# CSS Estilo Galáctico y Botones Premium + Estilo En Vivo
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; font-size: 0.8rem;}
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.6); backdrop-filter: blur(10px); border: 1px solid #00f2ff; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,242,255,0.1); }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.1); border-radius: 10px 10px 0 0; color: white; padding: 10px 20px; transition: all 0.3s ease;}
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.2) !important; border-bottom: 2px solid #00f2ff !important; text-shadow: 0 0 10px #00f2ff;}
    button[kind="primary"] { background: linear-gradient(45deg, #ff3366, #ff9933) !important; color: white !important; font-weight: bold !important; border: none !important; border-radius: 8px !important; box-shadow: 0 0 15px rgba(255,51,102,0.4) !important; }
    .live-card { background: rgba(40, 10, 10, 0.7); padding: 20px; border-radius: 15px; border: 1px solid #ff0044; margin-bottom: 10px; box-shadow: 0 0 15px rgba(255, 0, 68, 0.3); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { box-shadow: 0 0 10px rgba(255,0,68,0.2); } 50% { box-shadow: 0 0 20px rgba(255,0,68,0.6); } 100% { box-shadow: 0 0 10px rgba(255,0,68,0.2); } }
    </style>
    """, unsafe_allow_html=True)

# Conexión Firebase
try:
    if not firebase_admin._apps:
        dict_claves = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(dict_claves)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception:
    st.error("⚠️ Error crítico al conectar con la base de datos central.")
    st.stop()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 🏦 MOTOR FINANCIERO CORREGIDO Y BLINDADO
def resolver_apuesta(pick_id, resultado_final):
    try:
        p_id = str(pick_id) # Forzamos a texto para evitar errores de tipo en Firebase
        db.collection('pronosticos').document(p_id).update({'estatus': resultado_final})
        
        inversiones = db.collection('portafolio').where('id_pick', '==', p_id).stream()
        
        conteo = 0
        for inv in inversiones:
            conteo += 1
            datos = inv.to_dict()
            user_email = datos['user']
            monto = float(datos.get('monto', 0))
            cuota = float(datos.get('cuota', 1))
            
            if resultado_final == 'GANADA':
                pago_total = monto * cuota
                u_ref = db.collection('usuarios').document(user_email)
                u_doc = u_ref.get()
                if u_doc.exists:
                    b_actual = float(u_doc.to_dict().get('bankroll', 0))
                    u_ref.update({'bankroll': round(b_actual + pago_total, 2)})
                    
            db.collection('portafolio').document(inv.id).update({'estatus': resultado_final})
        st.toast(f"✅ Motor ejecutado: Se actualizaron {conteo} portafolios.")
        st.cache_data.clear() # <- LIMPIEZA DE CACHÉ PARA REFLEJAR SALDOS
    except Exception as e:
        st.toast(f"⚠️ Ocurrió un error procesando el pago: {e}")

# Seguridad y Sesión
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'
if 'user_email' not in st.session_state: st.session_state['user_email'] = 'default'

# --- ENCABEZADO CON EL NUEVO LOGO QUASAR ---
st.markdown("""
    <div style='text-align: center; margin-bottom: 10px; margin-top: 20px;'>
        <img src="https://raw.githubusercontent.com/victorfelipedata-glitch/torvi-analytics-v2/57c54d118a85d753a818cc39f0e5ce9ab5a02a6a/nuevo_logo_quasar.png" width="350" style="border-radius: 15px; box-shadow: 0px 0px 30px rgba(188, 19, 254, 0.6);">
    </div>
    """, unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA (EV+)</p>', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; padding: 20px; background: rgba(0,242,255,0.05); border-radius: 20px; border: 1px solid rgba(0,242,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>👋 ¡Bienvenido a Quasar!</h3>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🚀 INICIAR SESIÓN", "📝 CREAR CUENTA"])
        with t1:
            with st.form("f_login"):
                u = st.text_input("Correo electrónico:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("ENTRAR AL NÚCLEO", use_container_width=True):
                    if u: 
                        res = db.collection('usuarios').document(u).get()
                        if res.exists and res.to_dict()['password'] == encriptar_password(p):
                            st.session_state['autenticado'], st.session_state['user_rol'], st.session_state['user_email'] = True, res.to_dict().get('rol', 'usuario_vip'), u
                            st.rerun()
                        else: st.error("Credenciales incorrectas.")
                    else: st.warning("Ingresa tu correo.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARME AHORA", use_container_width=True):
                    if un and pn:
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip', 'bankroll': 1000.0})
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- CARGA DE DATOS BLINDADA Y CACHEADA (ANTIFALLOS Y ANTI-QUEMADO) ---

@st.cache_data(ttl=30, show_spinner=False)
def cargar_pronosticos():
    try:
        docs_picks = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
        data_picks = [d.to_dict() for d in docs_picks]
        return pd.DataFrame(data_picks) if data_picks else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus', 'id', 'deporte', 'liga', 'tipo', 'fecha'])
    except Exception:
        return pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus', 'id', 'deporte', 'liga', 'tipo', 'fecha'])

df = cargar_pronosticos()

if not df.empty:
    if 'estatus' not in df.columns: df['estatus'] = 'PENDIENTE'
    if 'deporte' not in df.columns: df['deporte'] = 'Fútbol'
    if 'liga' not in df.columns: df['liga'] = 'General'
    if 'tipo' not in df.columns: df['tipo'] = 'Sencilla'
    df['estatus'] = df['estatus'].fillna('PENDIENTE')
    df['deporte'] = df['deporte'].fillna('Fútbol')
    df['liga'] = df['liga'].fillna('General')
    df['tipo'] = df['tipo'].fillna('Sencilla')

@st.cache_data(ttl=30, show_spinner=False)
def cargar_portafolio(user_email):
    try:
        docs_port = db.collection('portafolio').where('user', '==', user_email).stream()
        port_data = [d.to_dict() for d in docs_port]
        if port_data:
            df_p = pd.DataFrame(port_data)
            if 'fecha' in df_p.columns:
                df_p = df_p.sort_values(by='fecha', ascending=False)
            return df_p
        return pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'monto', 'estatus', 'id_pick'])
    except Exception:
        return pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'monto', 'estatus', 'id_pick'])

df_port = cargar_portafolio(st.session_state['user_email'])

if not df_port.empty and 'estatus' not in df_port.columns:
    df_port['estatus'] = 'PENDIENTE'

@st.cache_data(ttl=30, show_spinner=False)
def cargar_bankroll(user_email):
    try:
        u_ref = db.collection('usuarios').document(user_email).get()
        return float(u_ref.to_dict().get('bankroll', 1000.0)) if u_ref.exists else 1000.0
    except Exception:
        return 1000.0

bank_actual = cargar_bankroll(st.session_state['user_email'])

# --- BARRA SUPERIOR: LOGOUT ---
col_head1, col_head2 = st.columns([8, 2])
if col_head2.button("🚪 CERRAR SESIÓN", use_container_width=True):
    st.session_state['autenticado'] = False
    st.cache_data.clear()
    st.rerun()

# --- PANEL DE ADMIN ---
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ EDITOR Y PANEL DE CONTROL (ADMIN)"):
        tab_admin_sencilla, tab_admin_parlay, tab_admin_vivo = st.tabs(["📌 AGREGAR SENCILLA", "💎 ARMAR PARLAY VIP", "🔴 LANZAR EN VIVO"])
        
        with tab_admin_sencilla:
            with st.form("nuevo_pick_sencillo"):
                c_a, c_b = st.columns(2)
                partido = c_a.text_input("⚽/🏀 Encuentro:", placeholder="Ej: Man City vs Liverpool")
                mercado = c_b.text_input("🎯 Mercado:", placeholder="Ej: +4.5 Tiros a Puerta")
                c_L1, c_L2 = st.columns(2)
                deporte = c_L1.selectbox("Deporte:", ["Fútbol", "NBA", "NFL", "Tenis"])
                liga = c_L2.text_input("🏆 Liga / Torneo:", placeholder="Ej: Champions League")
                c_n1, c_n2, c_n3, c_n4 = st.columns(4)
                cuota = c_n1.number_input("📈 Cuota:", min_value=1.01, value=1.90, step=0.01)
                prob_casa = c_n2.number_input("🏦 Prob. Casa %:", value=50.0)
                prob_real = c_n3.number_input("🎯 Prob. Real %:", value=60.0)
                ev_val = c_n4.number_input("🔥 EV+ %:", value=10.0)
                ana = st.text_area("🧠 Análisis Táctico y Matemático:")
                if st.form_submit_button("🚀 PUBLICAR SENCILLA"):
                    p_id = str(int(time.time()))
                    db.collection('pronosticos').document(p_id).set({'id': p_id, 'partido': partido, 'mercado': mercado, 'deporte': deporte, 'liga': liga, 'tipo': 'Sencilla', 'cuota': cuota, 'prob_casa': prob_casa, 'prob_real': prob_real, 'ev': ev_val, 'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()})
                    st.success("¡Pick publicado!"); st.cache_data.clear(); st.rerun()
                    
        with tab_admin_parlay:
            with st.form("nuevo_parlay"):
                st.info("Esta sección creará un ticket dorado exclusivo en la pestaña de Parlay VIP.")
                titulo_parlay = st.text_input("👑 Título del Parlay:", placeholder="Ej: Combinada VIP Europea")
                partidos_parlay = st.text_area("⚽ Partidos incluidos (uno por línea):")
                c_p1, c_p2, c_p3 = st.columns(3)
                cuota_parlay = c_p1.number_input("📈 Cuota Total:", min_value=1.01, value=3.50, step=0.01)
                ev_parlay = c_p2.number_input("🔥 EV+ Total %:", value=15.0)
                prob_real_parlay = c_p3.number_input("🎯 Prob. Real Quasar %:", value=35.0)
                ana_parlay = st.text_area("🧠 Justificación del Parlay:")
                if st.form_submit_button("💎 PUBLICAR PARLAY VIP"):
                    p_id = str(int(time.time()))
                    db.collection('pronosticos').document(p_id).set({'id': p_id, 'partido': titulo_parlay, 'mercado': partidos_parlay, 'deporte': 'Varios', 'liga': 'VIP', 'tipo': 'Parlay', 'cuota': cuota_parlay, 'prob_casa': 0, 'prob_real': prob_real_parlay, 'ev': ev_parlay, 'analisis': ana_parlay, 'estatus': 'PENDIENTE', 'fecha': datetime.now()})
                    st.success("¡Parlay VIP publicado!"); st.cache_data.clear(); st.rerun()

        with tab_admin_vivo:
            with st.form("nuevo_pick_vivo"):
                st.info("Esta alerta saldrá resaltada en rojo intenso para que los usuarios entren de inmediato.")
                c_v1, c_v2 = st.columns(2)
                partido_vivo = c_v1.text_input("🔴 Encuentro (Minuto/Marcador):", placeholder="Ej: Arsenal 0-0 (Min 45)")
                mercado_vivo = c_v2.text_input("🎯 Mercado a Atacar:", placeholder="Ej: Gana Cualquiera (12)")
                c_vn1, c_vn2 = st.columns(2)
                cuota_vivo = c_vn1.number_input("📈 Cuota Actual:", min_value=1.01, value=1.50, step=0.01)
                ev_vivo = c_vn2.number_input("🔥 EV+ Instantáneo %:", value=20.0)
                ana_vivo = st.text_area("🧠 Razón rápida del pick en vivo:")
                if st.form_submit_button("🔴 LANZAR ALERTA EN VIVO"):
                    p_id = str(int(time.time()))
                    db.collection('pronosticos').document(p_id).set({'id': p_id, 'partido': partido_vivo, 'mercado': mercado_vivo, 'deporte': 'Fútbol', 'liga': 'LIVE', 'tipo': 'En Vivo', 'cuota': cuota_vivo, 'prob_casa': 0, 'prob_real': 0, 'ev': ev_vivo, 'analisis': ana_vivo, 'estatus': 'PENDIENTE', 'fecha': datetime.now()})
                    st.success("¡Alerta en vivo enviada!"); st.cache_data.clear(); st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'].fillna('PENDIENTE') == 'PENDIENTE']
    df_historial = df[df['estatus'].fillna('PENDIENTE') != 'PENDIENTE']

    racha_actual = 0
    if not df_historial.empty:
        df_historial_ordenado = df_historial.sort_values(by='fecha', ascending=False)
        for _, row in df_historial_ordenado.iterrows():
            if row['estatus'] == 'GANADA': racha_actual += 1
            elif row['estatus'] == 'PERDIDA': break

    m1, m2, m3, m4 = st.columns(4)
    df_sencillas_activas = df_activos[(df_activos['tipo'] != 'Parlay') & (df_activos['tipo'] != 'En Vivo')]
    max_ev = f"{df_sencillas_activas['ev'].max()}%" if not df_sencillas_activas.empty else "0%"
    
    m1.metric("🔥 MÁX VENTAJA (SENCILLAS)", max_ev)
    m2.metric("🎯 ACTIVOS", len(df_activos))
    m3.metric("🔥 RACHA ACTUAL", f"{racha_actual} AL HILO")
    m4.metric("🏦 BANKROLL", f"${bank_actual:,.2f}")
    
    tab_vivo, tab_futbol, tab_nba, tab_parlay, tab_port, tab_historial_tab, tab_tools = st.tabs(["🔴 EN VIVO", "⚽ FÚTBOL", "🏀 NBA", "💎 PARLAY VIP", "💼 PORTAFOLIO", "📈 HISTORIAL", "⚙️ PERFIL"])
    
    # --- 🔴 PESTAÑA EN VIVO ---
    with tab_vivo:
        df_vivo = df_activos[df_activos['tipo'] == 'En Vivo']
        if not df_vivo.empty:
            st.markdown("<h3 style='text-align: center; color: #ff0044; font-family: Orbitron; text-shadow: 0 0 10px #ff0044;'>🔥 ALERTA DE MERCADO EN DIRECTO 🔥</h3><br>", unsafe_allow_html=True)
            for i, r in df_vivo.iterrows():
                st.markdown(f"""
                    <div class='live-card'>
                        <div style='display: flex; justify-content: space-between;'>
                            <h3 style='color: white; margin: 0;'>🔴 {r['partido']}</h3>
                            <span style='color: #ffffff; font-weight: bold; background: #ff0044; padding: 5px 15px; border-radius: 8px;'>CUOTA: {r['cuota']}</span>
                        </div>
                        <p style='color: #ffcccc; font-size: 1.1rem; font-weight: bold; margin-top: 10px;'>🎯 {r['mercado']}</p>
                        <p style='color: #00f2ff; font-weight: bold;'>⚡ EV+ Instantáneo: {r['ev']}%</p>
                        <p style='font-size: 0.95rem; color: #b3cce6; white-space: pre-line;'>{r.get('analisis', '')}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col_iv1, col_iv2 = st.columns([1, 2])
                monto_vivo = col_iv1.number_input("Inversión ($):", value=float(bank_actual * 0.05), key=f"inv_v_{r['id']}")
                if col_iv2.button("📥 Apostar en Vivo", key=f"btn_v_{r['id']}", use_container_width=True):
                    if bank_actual >= monto_vivo:
                        db.collection('usuarios').document(st.session_state['user_email']).update({'bankroll': bank_actual - monto_vivo})
                        db.collection('portafolio').document(f"{st.session_state['user_email']}_{r['id']}").set({
                            'id_pick': str(r['id']), 'user': st.session_state['user_email'], 'partido': r['partido'], 
                            'mercado': r['mercado'], 'cuota': r['cuota'], 'monto': monto_vivo, 'fecha': datetime.now(), 'estatus': 'PENDIENTE'
                        })
                        st.toast("¡Apuesta registrada y cobrada del Bankroll!")
                        time.sleep(1); st.cache_data.clear(); st.rerun()
                    else: st.error("❌ Bankroll insuficiente.")

                if st.session_state['user_rol'] == 'admin':
                    c_va, c_vb, c_vc = st.columns(3)
                    if c_va.button(f"✅ Cobrar", key=f"wv_{r['id']}"): resolver_apuesta(r['id'], 'GANADA'); st.rerun()
                    if c_vb.button(f"❌ Fallado", key=f"lv_{r['id']}"): resolver_apuesta(r['id'], 'PERDIDA'); st.rerun()
                    if c_vc.button(f"🗑️ Eliminar", key=f"delv_{r['id']}"): db.collection('pronosticos').document(str(r['id'])).delete(); st.cache_data.clear(); st.rerun()
        else:
            st.info("📡 Escaneando ineficiencias en directo... No hay alertas activas en este momento.")

    # --- ⚽ PESTAÑA FÚTBOL ---
    with tab_futbol:
        df_futbol = df_sencillas_activas[(df_sencillas_activas['deporte'] == 'Fútbol')]
        
        if not df_futbol.empty:
            ligas_disponibles = df_futbol['liga'].dropna().unique().tolist()
            liga_seleccionada = st.selectbox("🏆 Filtrar por Liga / Torneo:", ["Todas las Ligas"] + ligas_disponibles)
            if liga_seleccionada != "Todas las Ligas": df_futbol = df_futbol[df_futbol['liga'] == liga_seleccionada]

            if not df_futbol.empty:
                st.markdown("<h4 style='text-align:center; color:#00f2ff; font-family:Orbitron; margin-top:20px;'>🛰️ MAPA DE VALOR (PROBABILIDADES VS EV+)</h4>", unsafe_allow_html=True)
                fig_burbujas = px.scatter(
                    df_futbol, x='prob_casa', y='prob_real', size='ev', color='ev',
                    hover_name='partido', hover_data={'mercado': True, 'cuota': True, 'prob_casa': True, 'prob_real': True, 'ev': True},
                    labels={'prob_casa': 'Prob. Implícita Casa (%)', 'prob_real': 'Prob. Real Estimada (%)', 'ev': 'Ventaja EV+ (%)'},
                    template="plotly_dark", color_continuous_scale="Purp", size_max=35
                )
                fig_burbujas.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20))
                fig_burbujas.update_traces(marker=dict(line=dict(width=2, color='#00f2ff')))
                st.plotly_chart(fig_burbujas, use_container_width=True)

                for i, r in df_futbol.iterrows():
                    sugerencia = bank_actual * 0.05 
                    edit_key = f"edit_mode_{r['id']}"
                    if edit_key not in st.session_state: st.session_state[edit_key] = False
                        
                    if st.session_state[edit_key]:
                        st.markdown(f"<div style='background: rgba(188, 19, 254, 0.2); padding: 15px; border-radius: 10px; border: 1px solid #bc13fe;'>", unsafe_allow_html=True)
                        with st.form(f"form_edit_{r['id']}"):
                            st.write(f"✏️ Editando: {r['partido']}")
                            n_cuota = st.number_input("Nueva Cuota:", value=float(r['cuota']), step=0.01)
                            n_ev = st.number_input("Nuevo EV+:", value=float(r['ev']), step=0.1)
                            n_ana = st.text_area("Nuevo Análisis:", value=str(r.get('analisis','')))
                            col_sf1, col_sf2 = st.columns(2)
                            if col_sf1.form_submit_button("💾 Guardar"):
                                db.collection('pronosticos').document(str(r['id'])).update({'cuota': n_cuota, 'ev': n_ev, 'analisis': n_ana})
                                st.session_state[edit_key] = False; st.cache_data.clear(); st.rerun()
                            if col_sf2.form_submit_button("❌ Cancelar"): st.session_state[edit_key] = False; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div style='background: rgba(10, 17, 40, 0.7); padding: 20px; border-radius: 15px; border: 1px solid #00f2ff; margin-bottom: 10px;'>
                                <div style='display: flex; justify-content: space-between;'><h3 style='color: white; margin: 0;'>{r['partido']}</h3><span style='color: #00ff00; font-weight: bold; font-family: Orbitron; background: rgba(0,255,0,0.1); padding: 5px 10px; border-radius: 8px;'>EV+ {r['ev']}%</span></div>
                                <p style='color: #b3cce6; font-size: 0.8rem; margin: 0;'>🏆 {r.get('liga', 'General')}</p>
                                <p style='color: #bc13fe; font-weight: bold; margin-top: 10px;'>🎯 {r['mercado']}</p>
                                <div style='display: flex; gap: 15px; margin: 15px 0;'>
                                    <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>CUOTA REFERENCIA: <b>{r['cuota']}</b></div>
                                    <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>PROB. CASA: <b>{r.get('prob_casa',0)}%</b></div>
                                    <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>PROB. REAL: <b>{r.get('prob_real',0)}%</b></div>
                                </div>
                                <p style='font-size: 0.95rem; color: #b3cce6; white-space: pre-line;'>{r.get('analisis', '')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='background: rgba(0, 242, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #00f2ff; margin-bottom: 20px;'>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color: white; margin-bottom: 5px;'>💡 <b>Calculadora de Valor Dinámico y Gestión (5.0% Bank):</b></p>", unsafe_allow_html=True)
                        
                        col_i1, col_i2, col_i3 = st.columns([1, 1, 1.5])
                        user_cuota = col_i1.number_input("Momio Actual:", value=float(r['cuota']), step=0.01, key=f"cuota_{r['id']}")
                        monto_invertir = col_i2.number_input("Tu Inversión ($):", value=float(sugerencia), key=f"inv_{r['id']}")
                        
                        prob_r = float(r.get('prob_real', 0)) / 100.0
                        nuevo_ev = (prob_r * user_cuota - 1) * 100
                        
                        with col_i3:
                            st.write("") 
                            if nuevo_ev > 0:
                                st.markdown(f"<div style='background: rgba(0,255,0,0.1); padding: 5px; border-radius: 5px; border: 1px solid #00ff00; text-align: center;'><span style='color:#00ff00; font-weight:bold;'>✅ AÚN HAY VALOR (EV+ {nuevo_ev:.1f}%)</span></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='background: rgba(255,0,0,0.1); padding: 5px; border-radius: 5px; border: 1px solid #ff0000; text-align: center;'><span style='color:#ff0000; font-weight:bold;'>❌ LÍNEA CAÍDA (EV {nuevo_ev:.1f}%)</span></div>", unsafe_allow_html=True)
                            
                            if st.button("📥 Guardar y Descontar", key=f"btn_{r['id']}", use_container_width=True):
                                if bank_actual >= monto_invertir:
                                    db.collection('usuarios').document(st.session_state['user_email']).update({'bankroll': bank_actual - monto_invertir})
                                    db.collection('portafolio').document(f"{st.session_state['user_email']}_{r['id']}").set({
                                        'id_pick': str(r['id']), 'user': st.session_state['user_email'], 'partido': r['partido'], 
                                        'mercado': r['mercado'], 'cuota': user_cuota, 'monto': monto_invertir, 
                                        'fecha': datetime.now(), 'estatus': 'PENDIENTE'
                                    })
                                    st.toast("¡Apuesta registrada y cobrada del Bankroll!")
                                    time.sleep(1); st.cache_data.clear(); st.rerun()
                                else: st.error("❌ Bankroll insuficiente.")
                        st.markdown("</div>", unsafe_allow_html=True)

                        if st.session_state['user_rol'] == 'admin':
                            c_wa, c_wb, c_wc, c_wd = st.columns(4)
                            if c_wa.button(f"✅ Ganada", key=f"w_{r['id']}"): resolver_apuesta(r['id'], 'GANADA'); st.rerun()
                            if c_wb.button(f"❌ Perdida", key=f"l_{r['id']}"): resolver_apuesta(r['id'], 'PERDIDA'); st.rerun()
                            if c_wc.button(f"✏️ Editar", key=f"edt_{r['id']}"): st.session_state[edit_key] = True; st.rerun()
                            if c_wd.button(f"🗑️ Eliminar", key=f"del_{r['id']}"): db.collection('pronosticos').document(str(r['id'])).delete(); st.cache_data.clear(); st.rerun()
                        st.markdown("<hr style='opacity: 0.2;'>", unsafe_allow_html=True)
            else: st.info("No hay partidos para esta liga específica.")
        else: st.info("El radar de fútbol está despejado.")

    # --- 🏀 PESTAÑA NBA ---
    with tab_nba:
        st.info("Aún no inicia la cobertura de la duela.")

    # --- 💎 PESTAÑA PARLAY VIP ---
    with tab_parlay:
        df_parlays = df_activos[df_activos['tipo'] == 'Parlay']
        
        # Alerta Sonora
        if not df_parlays.empty:
            ultimo_parlay_id = df_parlays.iloc[0]['id']
            if 'last_parlay_alert' not in st.session_state:
                st.session_state['last_parlay_alert'] = ultimo_parlay_id
            elif st.session_state['last_parlay_alert'] != ultimo_parlay_id:
                st.session_state['last_parlay_alert'] = ultimo_parlay_id
                st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
                st.toast("🚨 ¡NUEVO PARLAY VIP DISPONIBLE!", icon="💎")

        st.markdown("""
            <div style='background: linear-gradient(135deg, #1a0b2e 0%, #bc13fe 100%); padding: 25px; border-radius: 20px; border: 2px solid #ffcc00; box-shadow: 0px 0px 20px rgba(188, 19, 254, 0.5);'>
                <h2 style='text-align: center; color: #ffcc00; font-family: Orbitron; margin:0;'>👑 PARLAY EXCLUSIVO VIP</h2>
            </div><br>
        """, unsafe_allow_html=True)
        
        if not df_parlays.empty:
            for i, p in df_parlays.iterrows():
                edit_key_p = f"edit_parlay_{p['id']}"
                if edit_key_p not in st.session_state: st.session_state[edit_key_p] = False
                
                if st.session_state[edit_key_p]:
                    st.markdown(f"<div style='background: rgba(255, 204, 0, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ffcc00;'>", unsafe_allow_html=True)
                    with st.form(f"form_edit_p_{p['id']}"):
                        st.write(f"✏️ Editando Parlay: {p['partido']}")
                        n_titulo = st.text_input("Nuevo Título:", value=str(p['partido']))
                        n_mercado = st.text_area("Nuevos Partidos:", value=str(p['mercado']))
                        col_ep1, col_ep2 = st.columns(2)
                        n_cuota_p = col_ep1.number_input("Nueva Cuota:", value=float(p['cuota']), step=0.01)
                        n_ev_p = col_ep2.number_input("Nuevo EV+:", value=float(p['ev']), step=0.1)
                        n_ana_p = st.text_area("Nuevo Análisis:", value=str(p.get('analisis','')))
                        
                        col_sp1, col_sp2 = st.columns(2)
                        if col_sp1.form_submit_button("💾 Guardar"):
                            db.collection('pronosticos').document(str(p['id'])).update({
                                'partido': n_titulo, 'mercado': n_mercado, 'cuota': n_cuota_p, 'ev': n_ev_p, 'analisis': n_ana_p
                            })
                            st.session_state[edit_key_p] = False; st.cache_data.clear(); st.rerun()
                        if col_sp2.form_submit_button("❌ Cancelar"): st.session_state[edit_key_p] = False; st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style='background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #ffcc00;'>
                            <h3 style='color: white;'>{p['partido']}</h3>
                            <p style='color: #b3cce6; white-space: pre-line;'>{p['mercado']}</p>
                            <p style='color: #00f2ff; font-weight: bold;'>CUOTA: {p['cuota']} | PROB. REAL: {p.get('prob_real', 0)}% | EV+: {p['ev']}%</p>
                            <p style='font-size: 0.95rem; color: white; white-space: pre-line;'>{p.get('analisis','')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<div style='background: rgba(255, 204, 0, 0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #ffcc00; margin-top: 15px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                    sugerencia_parlay = bank_actual * 0.02 
                    st.markdown(f"<p style='color: white; margin-bottom: 5px;'>💡 <b>Calculadora de Valor VIP y Gestión (2.0% Bank):</b></p>", unsafe_allow_html=True)
                    
                    col_ip1, col_ip2, col_ip3 = st.columns([1, 1, 1.5])
                    user_cuota_p = col_ip1.number_input("Momio Actual:", value=float(p['cuota']), step=0.01, key=f"cuota_p_{p['id']}")
                    monto_invertir_p = col_ip2.number_input("Tu Inversión ($):", value=float(sugerencia_parlay), key=f"inv_p_{p['id']}")
                    
                    prob_real_guardada = float(p.get('prob_real', 0))
                    if prob_real_guardada > 0:
                        prob_r_p = prob_real_guardada / 100.0
                    else:
                        prob_r_p = (float(p['ev']) / 100.0 + 1) / float(p['cuota'])
                        
                    nuevo_ev_p = (prob_r_p * user_cuota_p - 1) * 100
                    
                    with col_ip3:
                        st.write("") 
                        if nuevo_ev_p > 0:
                            st.markdown(f"<div style='background: rgba(0,255,0,0.1); padding: 5px; border-radius: 5px; border: 1px solid #00ff00; text-align: center;'><span style='color:#00ff00; font-weight:bold;'>✅ AÚN HAY VALOR (EV+ {nuevo_ev_p:.1f}%)</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='background: rgba(255,0,0,0.1); padding: 5px; border-radius: 5px; border: 1px solid #ff0000; text-align: center;'><span style='color:#ff0000; font-weight:bold;'>❌ LÍNEA CAÍDA (EV {nuevo_ev_p:.1f}%)</span></div>", unsafe_allow_html=True)
                        
                        if st.button("📥 Apostar Ticket Dorado", key=f"btn_p_{p['id']}", use_container_width=True):
                            if bank_actual >= monto_invertir_p:
                                db.collection('usuarios').document(st.session_state['user_email']).update({'bankroll': bank_actual - monto_invertir_p})
                                db.collection('portafolio').document(f"{st.session_state['user_email']}_{p['id']}").set({
                                    'id_pick': str(p['id']), 'user': st.session_state['user_email'], 'partido': p['partido'], 
                                    'mercado': 'Combinada VIP', 'cuota': user_cuota_p, 'monto': monto_invertir_p, 
                                    'fecha': datetime.now(), 'estatus': 'PENDIENTE'
                                })
                                st.toast("¡Ticket Dorado registrado y cobrado del Bankroll!")
                                time.sleep(1); st.cache_data.clear(); st.rerun()
                            else: st.error("❌ Bankroll insuficiente.")
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state['user_rol'] == 'admin':
                        c_pa, c_pb, c_pc, c_pd = st.columns(4)
                        if c_pa.button(f"✅ Cobrar", key=f"wp_{p['id']}"): resolver_apuesta(p['id'], 'GANADA'); st.rerun()
                        if c_pb.button(f"❌ Fallado", key=f"lp_{p['id']}"): resolver_apuesta(p['id'], 'PERDIDA'); st.rerun()
                        if c_pc.button(f"✏️ Editar", key=f"edtp_{p['id']}"): st.session_state[edit_key_p] = True; st.rerun()
                        if c_pd.button(f"🗑️ Eliminar", key=f"delp_{p['id']}"): db.collection('pronosticos').document(str(p['id'])).delete(); st.cache_data.clear(); st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
        else: st.info("Cocinando la combinada perfecta del día...")

    # --- 💼 PESTAÑA PORTAFOLIO (Escudo Quasar Integrado) ---
    with tab_port:
        st.markdown("### 💼 MIS INVERSIONES")
        
        if not df_port.empty:
            # 🚀 SINCRONIZACIÓN MAESTRA ULTRA-REFORZADA 🚀
            if not df.empty and 'id_pick' in df_port.columns:
                df_master_clean = df[['id', 'estatus']].copy()
                df_master_clean['id'] = df_master_clean['id'].astype(str)
                df_port['id_pick'] = df_port['id_pick'].astype(str)
                
                df_port = df_port.drop(columns=['estatus'], errors='ignore')
                df_port = df_port.merge(
                    df_master_clean, 
                    left_on='id_pick', 
                    right_on='id', 
                    how='left'
                )
            
            df_port['estatus'] = df_port['estatus'].fillna('PENDIENTE')
            
            df_port_pendientes = df_port[df_port['estatus'] == 'PENDIENTE']
            inversion_total = df_port_pendientes['monto'].sum()
            st.markdown(f"<div style='background: rgba(0, 242, 255, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #00f2ff; margin-bottom: 20px;'><h4 style='color: #00f2ff; margin: 0;'>Total en Riesgo Activo: <b style='color: white;'>${inversion_total:,.2f}</b></h4></div>", unsafe_allow_html=True)
            
            for i, r in df_port.iterrows():
                estatus = r['estatus']
                borde, badge = ("#00ff00", "✅ GANADA") if estatus == 'GANADA' else \
                               ("#ff0000", "❌ PERDIDA") if estatus == 'PERDIDA' else \
                               ("#bc13fe", "⏳ PENDIENTE")
                
                b_color = "#00ff00" if estatus == 'GANADA' else "#ff0000" if estatus == 'PERDIDA' else "#ffcc00"
                b_bg = "rgba(0,255,0,0.1)" if estatus == 'GANADA' else "rgba(255,0,0,0.1)" if estatus == 'PERDIDA' else "rgba(255,204,0,0.1)"
                
                st.markdown(f"""
                    <div style='border-left: 4px solid {borde}; padding: 15px; background: rgba(0,0,0,0.4); border-radius: 5px; margin-bottom: 10px;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <b style='color:white; font-size:1.1rem;'>{r['partido']}</b>
                            <span style='color:{b_color}; font-weight:bold; background:{b_bg}; padding:2px 8px; border-radius:4px;'>{badge}</span>
                        </div>
                        <span style='color:#b3cce6;'>{r['mercado']} | Momio: {r['cuota']} | Inversión: <b style='color:white;'>${r['monto']:,.2f}</b></span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no tienes apuestas guardadas. Usa el botón 'Guardar y Descontar' en el radar.")

    # --- 📈 PESTAÑA HISTORIAL Y YIELD ---
    with tab_historial_tab:
        if not df_historial.empty:
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            ganancia_unidades = 0
            for _, r in df_historial.iterrows():
                if r['estatus'] == 'GANADA': ganancia_unidades += (float(r['cuota']) - 1)
                elif r['estatus'] == 'PERDIDA': ganancia_unidades -= 1
            yield_pct = (ganancia_unidades / len(df_historial)) * 100 if len(df_historial) > 0 else 0
            
            c_h1, c_h2, c_h3, c_h4 = st.columns(4)
            c_h1.metric("✅ ACIERTOS", ganadas)
            c_h2.metric("❌ FALLOS", perdidas)
            c_h3.metric("📈 WIN RATE", f"{wr:.1f}%")
            c_h4.metric("💸 YIELD (ROI)", f"{yield_pct:+.1f}%")
            
            c_g1, c_g2 = st.columns(2)
            resumen = df_historial.groupby('estatus').size().reset_index(name='cantidad')
            fig_pie = px.pie(resumen, values='cantidad', names='estatus', color='estatus', color_discrete_map={'GANADA': '#00ff00', 'PERDIDA': '#ff0000'}, hole=0.4, template="plotly_dark", title="Rendimiento Global")
            c_g1.plotly_chart(fig_pie, use_container_width=True)
            
            df_historial_ordenado = df_historial.sort_values(by='fecha')
            crecimiento, dinero = [], 0
            for estatus in df_historial_ordenado['estatus']:
                if estatus == 'GANADA': dinero += 80
                elif estatus == 'PERDIDA': dinero -= 100
                crecimiento.append(dinero)
            df_historial_ordenado['crecimiento'] = crecimiento
            
            fig_line = px.line(df_historial_ordenado, x='fecha', y='crecimiento', template="plotly_dark", title="Curva de Beneficio")
            fig_line.update_traces(line_color='#00f2ff')
            c_g2.plotly_chart(fig_line, use_container_width=True)
            
            for i, r in df_historial.iterrows():
                icon = "✅ GANADA" if r['estatus'] == 'GANADA' else "❌ PERDIDA"
                color = "#00ff00" if r['estatus'] == 'GANADA' else "#ff0000"
                with st.expander(f"{icon} | {r['partido']} | {r['mercado']}"):
                    st.markdown(f"<p style='color:{color};'>Cuota: {r['cuota']} | Ventaja: {r['ev']}%</p>", unsafe_allow_html=True)
                    if st.session_state['user_rol'] == 'admin':
                        if st.button("🔄 Revertir a Pendiente", key=f"rev_{r['id']}"): 
                            db.collection('pronosticos').document(str(r['id'])).update({'estatus': 'PENDIENTE'})
                            st.cache_data.clear(); st.rerun()
        else: st.info("El historial aparecerá aquí conforme se resuelvan los partidos.")

    # --- ⚙️ PESTAÑA PERFIL Y HERRAMIENTAS VIP ---
    with tab_tools:
        st.markdown("### ⚙️ CONFIGURACIÓN DE CUENTA")
        st.markdown(f"<p style='color: #b3cce6;'>Usuario activo: {st.session_state['user_email']}</p>", unsafe_allow_html=True)
        col_u1, col_u2 = st.columns([2, 1])
        nuevo_bank = col_u1.number_input("Capital Actual (Bankroll Fijo):", value=float(bank_actual), step=50.0)
        if col_u2.button("💾 GUARDAR CAMBIOS", use_container_width=True):
            db.collection('usuarios').document(st.session_state['user_email']).update({'bankroll': nuevo_bank})
            st.success("¡Datos sincronizados con éxito!")
            time.sleep(1); st.cache_data.clear(); st.rerun()
            
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 🧮 CALCULADORAS MATEMÁTICAS Y PROYECCIÓN VIP")
        calc_kelly, calc_hedge, calc_montecarlo = st.tabs(["📊 Criterio de Kelly", "🛡️ Cobertura (Hedge)", "🎲 Simulador Monte Carlo"])
        
        with calc_kelly:
            st.info("Calcula el % exacto de tu bankroll a invertir basándote en la ventaja matemática.")
            k_cuota = st.number_input("Cuota de la apuesta:", min_value=1.01, value=1.90, step=0.01)
            k_prob = st.number_input("Probabilidad Real de Acierto (%):", min_value=1.0, max_value=100.0, value=55.0, step=1.0)
            if st.button("Calcular Inversión (Kelly)"):
                b = k_cuota - 1
                p = k_prob / 100.0
                q = 1 - p
                kelly_pct = ((p * b) - q) / b
                if kelly_pct > 0:
                    st.success(f"Porcentaje óptimo sugerido: **{kelly_pct*100:.2f}%** de tu Bankroll (**${bank_actual * kelly_pct:,.2f}**)")
                else:
                    st.error("EV Negativo detectado. Matemáticamente no se recomienda apostar en esta línea.")
                    
        with calc_hedge:
            st.info("Asegura ganancias matemáticas cuando a tu Parlay VIP solo le falta un partido para acertarse.")
            h_inversion = st.number_input("Inversión Inicial del Parlay ($):", value=100.0, step=10.0)
            h_cuota_parlay = st.number_input("Momio Total del Parlay:", value=5.0, step=0.1)
            h_cuota_contra = st.number_input("Momio a la Contra (del partido restante):", value=2.1, step=0.1)
            if st.button("Calcular Cobertura Perfecta"):
                ganancia_potencial = h_inversion * h_cuota_parlay
                monto_hedge = ganancia_potencial / h_cuota_contra
                beneficio_seguro = ganancia_potencial - h_inversion - monto_hedge
                st.success(f"Estrategia: Apuesta exactamente **${monto_hedge:,.2f}** a la contra.")
                st.info(f"Pase lo que pase en el último partido, tu beneficio neto asegurado será de: **${beneficio_seguro:,.2f}**")
                
        with calc_montecarlo:
            st.info("Simula 1,000 realidades alternativas de tus próximas apuestas usando tu Win Rate actual para calcular el crecimiento esperado y tu peor racha posible (Drawdown).")
            
            wr_actual = float(wr) if 'wr' in locals() and wr > 0 else 65.0
            
            c_mc1, c_mc2, c_mc3 = st.columns(3)
            mc_apuestas = c_mc1.number_input("Futuras Apuestas a Simular:", min_value=10, max_value=500, value=50, step=10)
            mc_wr = c_mc2.number_input("Win Rate Estimado (%):", min_value=1.0, max_value=99.0, value=wr_actual, step=1.0)
            mc_cuota = c_mc3.number_input("Cuota Promedio (Ej. 1.85):", min_value=1.01, value=1.85, step=0.05)
            mc_riesgo = st.slider("Riesgo por Apuesta (% del Bankroll):", min_value=1.0, max_value=20.0, value=5.0, step=0.5)

            if st.button("🚀 INICIAR SIMULACIÓN CUÁNTICA", use_container_width=True):
                with st.spinner("Procesando 1,000 universos paralelos..."):
                    simulaciones = 1000
                    win_rate_prob = mc_wr / 100.0
                    
                    bankrolls = np.zeros((simulaciones, mc_apuestas + 1))
                    bankrolls[:, 0] = bank_actual
                    
                    for i in range(simulaciones):
                        for j in range(1, mc_apuestas + 1):
                            gano = np.random.rand() < win_rate_prob
                            apuesta = bankrolls[i, j-1] * (mc_riesgo / 100.0)
                            if gano:
                                bankrolls[i, j] = bankrolls[i, j-1] + (apuesta * (mc_cuota - 1))
                            else:
                                bankrolls[i, j] = bankrolls[i, j-1] - apuesta

                    bankroll_final_promedio = np.mean(bankrolls[:, -1])
                    peor_escenario = np.min(bankrolls[:, -1])
                    mejor_escenario = np.max(bankrolls[:, -1])
                    
                    fig_mc = go.Figure()
                    
                    indices_muestra = np.random.choice(simulaciones, 100, replace=False)
                    for idx in indices_muestra:
                        fig_mc.add_trace(go.Scatter(y=bankrolls[idx], mode='lines', line=dict(color='rgba(0, 242, 255, 0.05)', width=1), showlegend=False))
                    
                    promedio_historico = np.mean(bankrolls, axis=0)
                    fig_mc.add_trace(go.Scatter(y=promedio_historico, mode='lines', line=dict(color='#bc13fe', width=4), name='Crecimiento Esperado'))
                    
                    fig_mc.update_layout(title="Proyección de Bankroll a Futuro", template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_mc, use_container_width=True)
                    
                    st.markdown(f"""
                    <div style='background: rgba(10, 17, 40, 0.8); padding: 15px; border-radius: 10px; border: 1px solid #00f2ff; text-align: center;'>
                        <h4 style='color: white;'>🔮 RESUMEN MULTIVERSAL</h4>
                        <p style='color: #00f2ff; font-size: 1.1rem;'>Bankroll Promedio Esperado: <b>${bankroll_final_promedio:,.2f}</b></p>
                        <p style='color: #ff0000; font-size: 0.9rem;'>Peor Escenario Posible: ${peor_escenario:,.2f}</p>
                        <p style='color: #00ff00; font-size: 0.9rem;'>Mejor Escenario Posible: ${mejor_escenario:,.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)

else:
    st.info("Base de datos vacía. Esperando primer análisis del núcleo...")

# --- FOOTER CON TU AUTORÍA ---
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("""
    <p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; font-size: 0.85rem; opacity: 0.8;'>
        © 2026 DESARROLLADO POR TORVI ANTONIO | QUASAR ANALYTICS
    </p>
""", unsafe_allow_html=True)
