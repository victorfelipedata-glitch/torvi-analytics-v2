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
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
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

# Cálculo de Kelly Fraccional (25% para gestión de riesgo segura)
def calcular_kelly(prob_real, cuota, bankroll):
    p = prob_real / 100.0
    q = 1.0 - p
    b = cuota - 1.0
    if b <= 0: return 0.0
    k_pct = ((p * b - q) / b)
    k_pct = max(0.0, k_pct) * 0.25 # Tomamos solo 1/4 del Kelly puro
    return round(k_pct * bankroll, 2), round(k_pct * 100, 2)

# Seguridad y Sesión
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = ''

st.markdown('<p class="titulo-futurista">AXIOM DATA</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

# --- LÓGICA DE LOGIN AMIGABLE ---
if not st.session_state['autenticado']:
    if 'vista_registro' not in st.session_state: st.session_state['vista_registro'] = False
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
            <div style='background: rgba(10, 17, 40, 0.3); padding: 25px; border-radius: 15px; border: 1px solid rgba(0, 242, 255, 0.2); text-align: center; margin-bottom: 25px;'>
                <h3 style='font-family: Orbitron; color: #00f2ff; margin-bottom: 5px; margin-top: 0px;'>👋 ¡Hola de nuevo!</h3>
                <p style='color: #b3cce6; font-size: 0.95rem; margin-bottom: 0px;'>Ingresa para ver el radar de valor de hoy.</p>
            </div>
        """, unsafe_allow_html=True)
        if not st.session_state['vista_registro']:
            with st.form("f_login"):
                u = st.text_input("Correo electrónico:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("Iniciar sesión", use_container_width=True):
                    res = db.collection('usuarios').document(u).get()
                    if res.exists and res.to_dict()['password'] == encriptar_password(p):
                        st.session_state['autenticado'], st.session_state['user_rol'], st.session_state['usuario_actual'] = True, res.to_dict().get('rol', 'usuario_vip'), u
                        st.rerun()
                    else: st.error("Usuario y/o contraseña incorrecto.")
            if st.button("Crea tu cuenta aquí", use_container_width=True):
                st.session_state['vista_registro'] = True
                st.rerun()
        else:
            with st.form("f_reg"):
                st.markdown("<p style='text-align: center; color: #bc13fe; font-family: Orbitron; font-weight: bold;'>ÚNETE A AXIOM</p>", unsafe_allow_html=True)
                un, pn = st.text_input("Tu correo electrónico:"), st.text_input("Crea una contraseña:", type="password")
                if st.form_submit_button("Crear cuenta", use_container_width=True):
                    if db.collection('usuarios').document(un).get().exists:
                        st.warning("Este correo ya está registrado. Intenta iniciar sesión.")
                    else:
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip', 'bank_inicial': 1000.0})
                        st.success("¡Cuenta creada con éxito! Ya puedes iniciar sesión.")
            if st.button("Volver a iniciar sesión", use_container_width=True):
                st.session_state['vista_registro'] = False
                st.rerun()
    st.stop()

# --- CARGA DE DATOS DESDE FIREBASE ---
docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
df = pd.DataFrame([d.to_dict() for d in docs]) if docs else pd.DataFrame()
if not df.empty and 'liga' not in df.columns: df['liga'] = 'Competición Global'
if not df.empty and 'tipo' not in df.columns: df['tipo'] = 'sencilla'

# Cargar jugadas personales del usuario (SOLO SI ESTÁ AUTENTICADO)
user_email = st.session_state['usuario_actual']
mis_jugadas = {}
bank_inicial = 1000.0

if st.session_state['autenticado'] and user_email != '':
    user_doc = db.collection('usuarios').document(user_email).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        bank_inicial = float(user_data.get('bank_inicial', 1000.0))
        
    docs_jugadas = db.collection('usuarios').document(user_email).collection('mis_jugadas').stream()
    mis_jugadas = {d.id: d.to_dict() for d in docs_jugadas}
# Calcular el Bankroll Actual del Usuario basado en sus jugadas
bank_actual = bank_inicial
historial_grafica = [{"fecha": datetime.now().strftime("%Y-%m-%d"), "bank": bank_inicial}] # Para la gráfica
if not df.empty and mis_jugadas:
    for _, pick in df.iterrows():
        pick_id = pick['id']
        if pick_id in mis_jugadas:
            monto = mis_jugadas[pick_id]['monto']
            if pick['estatus'] == 'GANADA':
                ganancia = monto * (pick['cuota'] - 1)
                bank_actual += ganancia
            elif pick['estatus'] == 'PERDIDA':
                bank_actual -= monto

# --- SIDEBAR: CONSOLA Y GESTIÓN ---
st.sidebar.title("📟 CONSOLA")
if st.sidebar.button("🔄 ACTUALIZAR DATOS", use_container_width=True): st.rerun()
st.sidebar.markdown("<hr>", unsafe_allow_html=True)

# GESTIÓN DE CAPITAL EN SIDEBAR
st.sidebar.markdown("### 🏦 MI BANKROLL")
nuevo_bank = st.sidebar.number_input("Configurar Capital Inicial:", min_value=100.0, value=float(bank_inicial), step=100.0)
if st.sidebar.button("💾 Guardar Capital"):
    db.collection('usuarios').document(user_email).update({'bank_inicial': nuevo_bank})
    st.sidebar.success("Capital actualizado.")
    st.rerun()

st.sidebar.markdown(f"<h2 style='color: #00ff00; text-align: center;'>${bank_actual:.2f}</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr>", unsafe_allow_html=True)

# FILTRO DE LIGAS
ligas_disponibles = ["Todas"] + list(df['liga'].unique()) if not df.empty else ["Todas"]
liga_seleccionada = st.sidebar.selectbox("🎯 Filtrar Competición:", ligas_disponibles)

if st.sidebar.button("🚪 CERRAR SESIÓN", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

# --- 🚀 PANEL DE ADMIN ---
if st.session_state['user_rol'] == 'admin':
    st.markdown("### 🛠️ CENTRO DE COMANDO (ADMIN)")
    with st.expander("➕ PUBLICAR NUEVO ANÁLISIS"):
        with st.form("nuevo_pick"):
            col_t, col_l = st.columns(2)
            tipo_pick = col_t.selectbox("📌 Tipo:", ["Sencilla (Radar EV+)", "Parlay (La Soñadora)"])
            liga = col_l.text_input("🏆 Liga/Competición:", placeholder="Ej: Champions League")
            
            col_p1, col_p2 = st.columns(2)
            partido = col_p1.text_input("⚽ Partido:", placeholder="Ej: Real Madrid vs City")
            mercado = col_p2.text_input("🎯 Mercado:", placeholder="Ej: +2.5 Goles")
            
            col_n1, col_n2, col_n3, col_n4 = st.columns(4)
            cuota = col_n1.number_input("📈 Cuota:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = col_n2.number_input("🏦 Prob. Casa (%):", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
            prob_real = col_n3.number_input("🎯 Prob. Real (%):", min_value=0.0, max_value=100.0, value=55.0, step=0.1)
            ev_val = col_n4.number_input("🔥 EV+ (%):", value=5.0, step=0.1)
            
            ana = st.text_area("🧠 Análisis Táctico:")
            
            if st.form_submit_button("🚀 INYECTAR AL SISTEMA"):
                pick_id = f"{int(time.time())}"
                db.collection('pronosticos').document(pick_id).set({
                    'id': pick_id, 'tipo': 'parlay' if 'Parlay' in tipo_pick else 'sencilla', 'liga': liga.strip(),
                    'partido': partido, 'mercado': mercado, 'cuota': cuota, 'prob_casa': prob_casa, 'prob_real': prob_real,
                    'ev': ev_val, 'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("¡Datos inyectados a la red!")
                st.rerun()

# --- TABLERO PRINCIPAL (USUARIO) ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos_s = df[(df['estatus'] == 'PENDIENTE') & (df['tipo'] != 'parlay')]
    df_activos_p = df[(df['estatus'] == 'PENDIENTE') & (df['tipo'] == 'parlay')]
    
    if liga_seleccionada != "Todas":
        df_activos_s = df_activos_s[df_activos_s['liga'] == liga_seleccionada]

    tab_radar, tab_parlay, tab_portafolio = st.tabs(["🛰️ RADAR DE VALOR", "🌌 LA SOÑADORA", "📖 MI PORTAFOLIO"])
    
    # ==========================================
    # 🟢 PESTAÑA 1: RADAR (AGRUPADO Y CON KELLY)
    # ==========================================
    with tab_radar:
        if not df_activos_s.empty:
            # MÉTRICAS GENERALES
            c1, c2, c3 = st.columns(3)
            c1.metric("🔥 MAYOR VENTAJA (EV+)", f"{df_activos_s['ev'].max()}%")
            c2.metric("🎯 OPORTUNIDADES ACTIVAS", len(df_activos_s))
            c3.metric("🏦 TU CAPITAL ACTUAL", f"${bank_actual:.2f}")
            st.markdown("<br>", unsafe_allow_html=True)

            # AGRUPACIÓN POR LIGA Y PARTIDO
            for liga_nombre, df_liga in df_activos_s.groupby('liga'):
                st.markdown(f"<h3 style='color: #bc13fe; font-family: Orbitron; margin-bottom: 5px;'>🏆 {liga_nombre}</h3>", unsafe_allow_html=True)
                for partido_nombre, df_partido in df_liga.groupby('partido'):
                    st.markdown(f"<h4 style='color: #00f2ff; margin-left: 10px;'>⚽ {partido_nombre}</h4>", unsafe_allow_html=True)
                    
                    for i, r in df_partido.iterrows():
                        with st.expander(f"📌 {r['mercado']} | Cuota: {r['cuota']} | EV+: {r['ev']}%"):
                            # Kelly Calculation
                            sugerencia_usd, kelly_pct = calcular_kelly(r.get('prob_real', 50), r['cuota'], bank_actual)
                            
                            st.markdown(f"""
                            <div style='display: flex; justify-content: space-between; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 8px;'>
                                <div><b style='color:#b3cce6'>🏦 Prob. Casa:</b> {r.get('prob_casa', 'N/A')}%</div>
                                <div><b style='color:#00f2ff'>🎯 Prob. Real:</b> {r.get('prob_real', 'N/A')}%</div>
                                <div><b style='color:#00ff00'>💰 Kelly (25%):</b> Invertir {kelly_pct}% (${sugerencia_usd:.2f})</div>
                            </div><br>
                            """, unsafe_allow_html=True)
                            st.write(r.get('analisis', ''))
                            
                            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                            
                            # Registro de Jugada para el Usuario
                            if r['id'] not in mis_jugadas:
                                col_i1, col_i2 = st.columns([2, 1])
                                monto_apuesta = col_i1.number_input("¿Cuánto vas a invertir?", min_value=1.0, value=float(sugerencia_usd) if sugerencia_usd > 0 else 10.0, key=f"inp_{r['id']}")
                                if col_i2.button("✅ Registrar en mi Portafolio", key=f"btn_{r['id']}"):
                                    db.collection('usuarios').document(user_email).collection('mis_jugadas').document(r['id']).set({'monto': monto_apuesta, 'fecha': datetime.now()})
                                    st.rerun()
                            else:
                                st.success(f"🎟️ Ya tienes registrado este pick con una inversión de ${mis_jugadas[r['id']]['monto']}")

                            # Controles del Admin
                            if st.session_state['user_rol'] == 'admin':
                                st.markdown("<b>[Admin Zone]</b>", unsafe_allow_html=True)
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
            st.info("No hay pronósticos activos para esta competición.")

    # ==========================================
    # 🌌 PESTAÑA 2: LA SOÑADORA (PARLAYS)
    # ==========================================
    with tab_parlay:
        st.markdown("<h4 style='text-align: center; color: #ffd700; font-family: Orbitron;'>🎟️ TICKET DORADO DEL DÍA</h4>", unsafe_allow_html=True)
        if not df_activos_p.empty:
            for i, r in df_activos_p.iterrows():
                sugerencia_usd, kelly_pct = calcular_kelly(r.get('prob_real', 30), r['cuota'], bank_actual)
                st.markdown(f"""
                <div style="border: 2px solid #ffd700; border-radius: 10px; padding: 15px; background: rgba(255, 215, 0, 0.05); margin-bottom: 15px;">
                    <h4 style="color: #ffd700; margin-top: 0;">🔥 CUOTA TOTAL: {r['cuota']}</h4>
                    <p style="color: #00f2ff;"><b>Partidos:</b> {r['partido']}</p>
                    <p style="color: #00f2ff;"><b>Mercados:</b> {r['mercado']}</p>
                    <p style="color: #00ff00; font-size: 0.9rem;"><b>Sugerencia (Stake Bajo):</b> ${sugerencia_usd:.2f}</p>
                    <hr style="background: #ffd700;">
                    <p style="color: #ffffff;">{r.get('analisis', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Opcion para el usuario de guardarlo
                if r['id'] not in mis_jugadas:
                    col_p1, col_p2 = st.columns([2, 1])
                    monto_p = col_p1.number_input("Inversión para la Soñadora:", min_value=1.0, value=float(sugerencia_usd) if sugerencia_usd > 0 else 10.0, key=f"inpp_{r['id']}")
                    if col_p2.button("✅ Registrar Ticket", key=f"btnp_{r['id']}"):
                        db.collection('usuarios').document(user_email).collection('mis_jugadas').document(r['id']).set({'monto': monto_p, 'fecha': datetime.now()})
                        st.rerun()
                else:
                    st.success(f"🎟️ Ticket Dorado registrado por ${mis_jugadas[r['id']]['monto']}")

                if st.session_state['user_rol'] == 'admin':
                    c_a, c_b, c_c = st.columns(3)
                    if c_a.button(f"✅ Cobrar", key=f"pwin_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'}); st.rerun()
                    if c_b.button(f"❌ Fallada", key=f"ploss_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'}); st.rerun()
                    if c_c.button(f"🗑️ Borrar", key=f"pdel_{r['id']}"): db.collection('pronosticos').document(r['id']).delete(); st.rerun()
        else:
            st.info("Aún no hay Ticket Dorado para hoy. El modelo sigue calculando.")

    # ==========================================
    # 📖 PESTAÑA 3: MI PORTAFOLIO (CONTROL DE BANK)
    # ==========================================
    with tab_portafolio:
        st.markdown("<h4 style='color: #b3cce6; font-family: Orbitron; text-align: center;'>TU DESEMPEÑO FINANCIERO</h4>", unsafe_allow_html=True)
        
        jugadas_resueltas = []
        for _, pick in df.iterrows():
            if pick['id'] in mis_jugadas and pick['estatus'] != 'PENDIENTE':
                p_info = pick.copy()
                p_info['monto_apostado'] = mis_jugadas[pick['id']]['monto']
                jugadas_resueltas.append(p_info)

        if jugadas_resueltas:
            ganadas = len([j for j in jugadas_resueltas if j['estatus'] == 'GANADA'])
            perdidas = len([j for j in jugadas_resueltas if j['estatus'] == 'PERDIDA'])
            total_r = ganadas + perdidas
            win_rate = (ganadas / total_r) * 100 if total_r > 0 else 0
            
            h_col1, h_col2, h_col3 = st.columns(3)
            h_col1.metric("✅ ACERTADAS", ganadas)
            h_col2.metric("❌ FALLADAS", perdidas)
            h_col3.metric("📈 WIN RATE", f"{win_rate:.1f}%")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            st.markdown("### 📜 Historial de Inversiones")
            for r in jugadas_resueltas:
                icono = "✅" if r['estatus'] == 'GANADA' else "❌"
                color_bg = "rgba(0, 255, 0, 0.1)" if r['estatus'] == 'GANADA' else "rgba(255, 0, 0, 0.1)"
                color_borde = "#00ff00" if r['estatus'] == 'GANADA' else "#ff0000"
                
                # Calculo de retorno
                retorno = (r['monto_apostado'] * r['cuota']) if r['estatus'] == 'GANADA' else 0
                beneficio = retorno - r['monto_apostado'] if r['estatus'] == 'GANADA' else -r['monto_apostado']

                st.markdown(f"""
                <div style='border-left: 4px solid {color_borde}; background: {color_bg}; padding: 10px; margin-bottom: 10px; border-radius: 4px;'>
                    <b>{icono} {r['partido']} | {r['mercado']}</b><br>
                    <span style='font-size: 0.9rem; color: #b3cce6;'>Invertido: ${r['monto_apostado']} | Cuota: {r['cuota']} | <b>Beneficio Neto: ${beneficio:.2f}</b></span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.session_state['user_rol'] == 'admin':
                    if st.button("🔄 Regresar a Pendiente (Admin)", key=f"rev_{r['id']}"):
                        db.collection('pronosticos').document(r['id']).update({'estatus': 'PENDIENTE'})
                        st.rerun()
        else:
            st.info("Aún no tienes jugadas resueltas en tu portafolio personal. ¡Empieza a invertir en el Radar!")

else:
    st.info("La red de Axiom está iniciando. Esperando inyección de datos.")

# --- FOOTER ---
st.markdown("<br><br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; font-size: 0.9rem; opacity: 0.7;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)











