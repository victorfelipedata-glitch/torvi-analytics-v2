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

# 🔄 Auto-Refresh Silencioso (60 segundos)
st_autorefresh(interval=5000, limit=None, key="quasar_autorefresh")

# CSS Estilo Galáctico y Botones Premium
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

# --- CARGA DE DATOS ---
docs_picks = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
data_picks = [d.to_dict() for d in docs_picks]
df = pd.DataFrame(data_picks) if data_picks else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus', 'id', 'deporte', 'liga', 'tipo', 'fecha'])

if not df.empty:
    if 'estatus' not in df.columns: df['estatus'] = 'PENDIENTE'
    if 'deporte' not in df.columns: df['deporte'] = 'Fútbol'
    if 'liga' not in df.columns: df['liga'] = 'General'
    if 'tipo' not in df.columns: df['tipo'] = 'Sencilla'
    df['estatus'] = df['estatus'].fillna('PENDIENTE')
    df['deporte'] = df['deporte'].fillna('Fútbol')
    df['liga'] = df['liga'].fillna('General')
    df['tipo'] = df['tipo'].fillna('Sencilla')

docs_port = db.collection('portafolio').where('user', '==', st.session_state['user_email']).stream()
df_port = pd.DataFrame([d.to_dict() for d in docs_port]) if docs_port else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'monto'])

user_ref = db.collection('usuarios').document(st.session_state['user_email'])
bank_actual = user_ref.get().to_dict().get('bankroll', 1000.0) if user_ref.get().exists else 1000.0

# --- BARRA SUPERIOR: LOGOUT SOLAMENTE ---
col_head1, col_head2 = st.columns([8, 2])
if col_head2.button("🚪 CERRAR SESIÓN", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

# --- PANEL DE ADMIN ---
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ EDITOR Y PANEL DE CONTROL (ADMIN)"):
        tab_admin_sencilla, tab_admin_parlay = st.tabs(["📌 AGREGAR SENCILLA", "💎 ARMAR PARLAY VIP"])
        
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
                    p_id = f"{int(time.time())}"
                    db.collection('pronosticos').document(p_id).set({'id': p_id, 'partido': partido, 'mercado': mercado, 'deporte': deporte, 'liga': liga, 'tipo': 'Sencilla', 'cuota': cuota, 'prob_casa': prob_casa, 'prob_real': prob_real, 'ev': ev_val, 'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()})
                    st.success("¡Pick publicado!"); st.rerun()
                    
        with tab_admin_parlay:
            with st.form("nuevo_parlay"):
                st.info("Esta sección creará un ticket dorado exclusivo en la pestaña de Parlay VIP.")
                titulo_parlay = st.text_input("👑 Título del Parlay:", placeholder="Ej: Combinada VIP Europea")
                partidos_parlay = st.text_area("⚽ Partidos incluidos (uno por línea):")
                c_p1, c_p2 = st.columns(2)
                cuota_parlay = c_p1.number_input("📈 Cuota Total:", min_value=1.01, value=3.50, step=0.01)
                ev_parlay = c_p2.number_input("🔥 EV+ Total %:", value=15.0)
                ana_parlay = st.text_area("🧠 Justificación del Parlay:")
                if st.form_submit_button("💎 PUBLICAR PARLAY VIP"):
                    p_id = f"{int(time.time())}"
                    db.collection('pronosticos').document(p_id).set({'id': p_id, 'partido': titulo_parlay, 'mercado': partidos_parlay, 'deporte': 'Varios', 'liga': 'VIP', 'tipo': 'Parlay', 'cuota': cuota_parlay, 'prob_casa': 0, 'prob_real': 0, 'ev': ev_parlay, 'analisis': ana_parlay, 'estatus': 'PENDIENTE', 'fecha': datetime.now()})
                    st.success("¡Parlay VIP publicado!"); st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'].fillna('PENDIENTE') == 'PENDIENTE']
    df_historial = df[df['estatus'].fillna('PENDIENTE') != 'PENDIENTE']

    # CÁLCULO DE RACHA ACTUAL (ON FIRE)
    racha_actual = 0
    if not df_historial.empty:
        df_historial_ordenado = df_historial.sort_values(by='fecha', ascending=False)
        for _, row in df_historial_ordenado.iterrows():
            if row['estatus'] == 'GANADA': racha_actual += 1
            elif row['estatus'] == 'PERDIDA': break

    # MÉTRICA DE EV+ EXCLUSIVA PARA SENCILLAS
    m1, m2, m3, m4 = st.columns(4)
    df_sencillas_activas = df_activos[df_activos['tipo'] != 'Parlay']
    max_ev = f"{df_sencillas_activas['ev'].max()}%" if not df_sencillas_activas.empty else "0%"
    
    m1.metric("🔥 MÁX VENTAJA (SENCILLAS)", max_ev)
    m2.metric("🎯 ACTIVOS", len(df_activos))
    m3.metric("🔥 RACHA ACTUAL", f"{racha_actual} AL HILO")
    m4.metric("🏦 BANKROLL", f"${bank_actual:,.2f}")
    
    # 🗂️ PESTAÑAS PRINCIPALES
    tab_futbol, tab_nba, tab_parlay, tab_port, tab_historial_tab, tab_tools = st.tabs(["⚽ FÚTBOL", "🏀 NBA", "💎 PARLAY VIP", "💼 PORTAFOLIO", "📈 HISTORIAL", "⚙️ PERFIL"])
    
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
                                db.collection('pronosticos').document(r['id']).update({'cuota': n_cuota, 'ev': n_ev, 'analisis': n_ana})
                                st.session_state[edit_key] = False; st.rerun()
                            if col_sf2.form_submit_button("❌ Cancelar"): st.session_state[edit_key] = False; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div style='background: rgba(10, 17, 40, 0.7); padding: 20px; border-radius: 15px; border: 1px solid #00f2ff; margin-bottom: 10px;'>
                                <div style='display: flex; justify-content: space-between;'><h3 style='color: white; margin: 0;'>{r['partido']}</h3><span style='color: #00ff00; font-weight: bold; font-family: Orbitron; background: rgba(0,255,0,0.1); padding: 5px 10px; border-radius: 8px;'>EV+ {r['ev']}%</span></div>
                                <p style='color: #b3cce6; font-size: 0.8rem; margin: 0;'>🏆 {r.get('liga', 'General')}</p>
                                <p style='color: #bc13fe; font-weight: bold; margin-top: 10px;'>🎯 {r['mercado']}</p>
                                <div style='display: flex; gap: 15px; margin: 15px 0;'>
                                    <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>CUOTA: <b>{r['cuota']}</b></div>
                                    <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>PROB. CASA: <b>{r.get('prob_casa',0)}%</b></div>
                                    <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>PROB. REAL: <b>{r.get('prob_real',0)}%</b></div>
                                </div>
                                <p style='font-size: 0.95rem; color: #b3cce6; white-space: pre-line;'>{r.get('analisis', '')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='background: rgba(0, 242, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #00f2ff; margin-bottom: 20px;'>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color: white; margin-bottom: 5px;'>💡 <b>Gestión de Riesgo:</b> Sugerencia del 5.0% de tu Bankroll</p>", unsafe_allow_html=True)
                        col_i1, col_i2 = st.columns([1, 2])
                        monto_invertir = col_i1.number_input("Tu Inversión ($):", value=float(sugerencia), key=f"inv_{r['id']}")
                        if col_i2.button("📥 Guardar en Mi Portafolio", key=f"btn_{r['id']}"):
                            db.collection('portafolio').document(f"{st.session_state['user_email']}_{r['id']}").set({'user': st.session_state['user_email'], 'partido': r['partido'], 'mercado': r['mercado'], 'cuota': r['cuota'], 'monto': monto_invertir, 'fecha': datetime.now()})
                            st.toast("¡Inversión guardada en el portafolio!")
                        st.markdown("</div>", unsafe_allow_html=True)

                        if st.session_state['user_rol'] == 'admin':
                            c_wa, c_wb, c_wc, c_wd = st.columns(4)
                            if c_wa.button(f"✅ Ganada", key=f"w_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'}); st.rerun()
                            if c_wb.button(f"❌ Perdida", key=f"l_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'}); st.rerun()
                            if c_wc.button(f"✏️ Editar", key=f"edt_{r['id']}"): st.session_state[edit_key] = True; st.rerun()
                            if c_wd.button(f"🗑️ Eliminar", key=f"del_{r['id']}"): db.collection('pronosticos').document(r['id']).delete(); st.rerun()
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
                            db.collection('pronosticos').document(p['id']).update({
                                'partido': n_titulo, 'mercado': n_mercado, 'cuota': n_cuota_p, 'ev': n_ev_p, 'analisis': n_ana_p
                            })
                            st.session_state[edit_key_p] = False; st.rerun()
                        if col_sp2.form_submit_button("❌ Cancelar"): st.session_state[edit_key_p] = False; st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style='background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #ffcc00;'>
                            <h3 style='color: white;'>{p['partido']}</h3>
                            <p style='color: #b3cce6; white-space: pre-line;'>{p['mercado']}</p>
                            <p style='color: #00f2ff; font-weight: bold;'>CUOTA FINAL: {p['cuota']} | EV+: {p['ev']}%</p>
                            <p style='font-size: 0.95rem; color: white; white-space: pre-line;'>{p.get('analisis','')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.session_state['user_rol'] == 'admin':
                        c_pa, c_pb, c_pc, c_pd = st.columns(4)
                        if c_pa.button(f"✅ Cobrar", key=f"wp_{p['id']}"): db.collection('pronosticos').document(p['id']).update({'estatus': 'GANADA'}); st.rerun()
                        if c_pb.button(f"❌ Fallado", key=f"lp_{p['id']}"): db.collection('pronosticos').document(p['id']).update({'estatus': 'PERDIDA'}); st.rerun()
                        if c_pc.button(f"✏️ Editar", key=f"edtp_{p['id']}"): st.session_state[edit_key_p] = True; st.rerun()
                        if c_pd.button(f"🗑️ Eliminar", key=f"delp_{p['id']}"): db.collection('pronosticos').document(p['id']).delete(); st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)
        else: st.info("Cocinando la combinada perfecta del día...")

    # --- 💼 PESTAÑA PORTAFOLIO ---
    with tab_port:
        st.markdown("### 💼 MIS INVERSIONES ACTIVAS")
        if not df_port.empty:
            inversion_total = df_port['monto'].sum()
            st.markdown(f"<p style='font-size: 1.2rem; color: #00f2ff;'>Total en Riesgo: <b>${inversion_total:,.2f}</b></p>", unsafe_allow_html=True)
            for i, r in df_port.iterrows():
                st.markdown(f"<div style='border-left: 3px solid #bc13fe; padding: 15px; background: rgba(0,0,0,0.4); border-radius: 5px; margin-bottom: 10px;'><b style='color:white;'>{r['partido']}</b><br><span style='color:#b3cce6;'>{r['mercado']} | Cuota: {r['cuota']} | Inversión: <b>${r['monto']:,.2f}</b></span></div>", unsafe_allow_html=True)
        else: st.info("Aún no tienes apuestas guardadas. Usa el botón 'Guardar en Mi Portafolio' en el radar.")

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
                        if st.button("🔄 Revertir a Pendiente", key=f"rev_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'}); st.rerun()
        else: st.info("El historial aparecerá aquí conforme se resuelvan los partidos.")

    # --- ⚙️ PESTAÑA PERFIL Y HERRAMIENTAS VIP ---
    with tab_tools:
        st.markdown("### ⚙️ CONFIGURACIÓN DE CUENTA")
        st.markdown(f"<p style='color: #b3cce6;'>Usuario activo: {st.session_state['user_email']}</p>", unsafe_allow_html=True)
        col_u1, col_u2 = st.columns([2, 1])
        nuevo_bank = col_u1.number_input("Capital Inicial (Bankroll Fijo):", value=float(bank_actual), step=50.0)
        if col_u2.button("💾 GUARDAR CAMBIOS", use_container_width=True):
            user_ref.update({'bankroll': nuevo_bank})
            st.success("¡Datos sincronizados con éxito!"); time.sleep(1); st.rerun()
            
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
            
            # Variables predeterminadas basadas en historial o valores base
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
                    
                    # Matriz de resultados
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

                    # Extraer métricas clave
                    bankroll_final_promedio = np.mean(bankrolls[:, -1])
                    peor_escenario = np.min(bankrolls[:, -1])
                    mejor_escenario = np.max(bankrolls[:, -1])
                    
                    # Gráfica de estilo Quasar
                    fig_mc = go.Figure()
                    
                    # Dibujar 100 líneas aleatorias (opacidad baja)
                    indices_muestra = np.random.choice(simulaciones, 100, replace=False)
                    for idx in indices_muestra:
                        fig_mc.add_trace(go.Scatter(y=bankrolls[idx], mode='lines', line=dict(color='rgba(0, 242, 255, 0.05)', width=1), showlegend=False))
                    
                    # Dibujar línea promedio (Morado neón)
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

