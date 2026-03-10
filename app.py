import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import hashlib
import traceback
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="AXIOM DATA", layout="wide", initial_sidebar_state="collapsed")

# 2. Estilos CSS (Forzando Dark Mode y Diseño Premium)
st.markdown("""
    <style>
    .stApp, .stApp > header { background-color: #050814 !important; color: #e0e0e0 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .titulo-futurista { font-family: 'Orbitron', sans-serif; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px;}
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; font-size: 0.8rem;}
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.8) !important; backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2) !important; border-radius: 15px; color: white !important;}
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.8) !important; backdrop-filter: blur(10px); border: 1px solid #00f2ff !important; border-radius: 10px; text-align: center; }
    div[data-testid="stMetric"] label { color: #b3cce6 !important; }
    div[data-testid="stMetric"] div { color: #00f2ff !important; }
    hr { border: 0; height: 1px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: #0a1128 !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent !important;}
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.1) !important; border-radius: 10px 10px 0 0; color: #b3cce6 !important; padding: 10px 20px; font-family: 'Orbitron'; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.15) !important; border-bottom: 2px solid #00f2ff !important; color: #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛡️ CÚPULA ANTI-ERRORES GLOBAL
# ==========================================
try:
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
    if 'user_correo' not in st.session_state: st.session_state['user_correo'] = ''
    if 'editando_pick' not in st.session_state: st.session_state['editando_pick'] = None

    st.markdown('<p class="titulo-futurista">AXIOM DATA</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

    # 5. Interfaz de Acceso
    if not st.session_state['autenticado']:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<div style='text-align: center; padding: 20px; background: rgba(0,242,255,0.05); border-radius: 20px; border: 1px solid rgba(0,242,255,0.1);'>", unsafe_allow_html=True)
            t_login, t_reg = st.tabs(["🚀 INICIAR SESIÓN", "📝 REGISTRO"])
            with t_login:
                with st.form("login_form"):
                    u = st.text_input("Correo:")
                    p = st.text_input("Clave:", type="password")
                    if st.form_submit_button("ENTRAR", use_container_width=True):
                        if u:
                            res = db.collection('usuarios').document(u).get()
                            if res.exists and res.to_dict()['password'] == encriptar_password(p):
                                st.session_state['autenticado'] = True
                                st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                                st.session_state['user_correo'] = u
                                st.session_state['bank_inicial'] = res.to_dict().get('bank_inicial', 1000.0)
                                st.rerun()
                            else: st.error("Credenciales incorrectas.")
                        else: st.warning("Ingresa un usuario.")
            with t_reg:
                with st.form("reg_form"):
                    un = st.text_input("Nuevo Correo:")
                    pn = st.text_input("Nueva Clave:", type="password")
                    if st.form_submit_button("CREAR CUENTA", use_container_width=True):
                        if un and pn:
                            db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip', 'bank_inicial': 1000.0})
                            st.success("¡Cuenta creada! Inicia sesión.")
            st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # 6. Carga de Datos
    docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
    data_list = []
    for d in docs:
        item = d.to_dict()
        if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
        data_list.append(item)
    df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=['id', 'partido', 'mercado', 'cuota', 'prob_real', 'ev', 'estatus', 'selecciones'])

    user_bets_docs = db.collection('apuestas_usuarios').where('correo', '==', st.session_state['user_correo']).stream()
    user_bets = {b.to_dict()['pick_id']: b.to_dict() for b in user_bets_docs}

    # Cálculo de Bank Actual
    bank_actual = st.session_state.get('bank_inicial', 1000.0)
    ganadas_personales, perdidas_personales = 0, 0
    for pid, bet in user_bets.items():
        if not df.empty and pid in df['id'].values:
            estado_global = df[df['id'] == pid].iloc[0]['estatus']
            if estado_global == 'GANADA':
                bank_actual += bet['monto'] * (bet['cuota'] - 1)
                ganadas_personales += 1
            elif estado_global == 'PERDIDA':
                bank_actual -= bet['monto']
                perdidas_personales += 1

    col_btn1, col_btn2 = st.columns([4, 1])
    with col_btn2:
        if st.button("🔄 ACTUALIZAR RADAR", use_container_width=True):
            st.rerun()

    # 7. Panel Admin - PUBLICAR (CON PARLAY MULTISELECCIÓN)
    if st.session_state['user_rol'] == 'admin':
        with st.expander("🛠️ PANEL DE CONTROL - PUBLICAR NUEVO"):
            with st.form("admin_pick"):
                es_parlay = st.checkbox("🎟️ Es una apuesta Combinada (Parlay VIP)")
                
                partido_in = st.text_input("⚽ Título o Partido Principal:", placeholder="Ej: Parlay Champions / Real Madrid vs City")
                
                if es_parlay:
                    selecciones_in = st.text_area("📌 Lista de Pronósticos del Parlay (Uno por línea):", placeholder="- Pumas +4.5 SoT\n- West Ham Gana\n- Barcelona +2.5 Goles")
                    mercado_in = "Combinada Múltiple"
                else:
                    mercado_in = st.text_input("🎯 Mercado Especializado:", placeholder="Ej: +4.5 Tiros a puerta")
                    selecciones_in = ""

                cn1, cn2, cn3, cn4 = st.columns(4)
                cuota_in = cn1.number_input("📈 Cuota Final:", value=1.90, step=0.01)
                pcasa_in = cn2.number_input("🏦 Prob. Casa %:", value=50.0)
                preal_in = cn3.number_input("🎯 Prob. Real %:", value=55.0)
                ev_in = cn4.number_input("🔥 EV+ %:", value=5.0)
                ana_in = st.text_area("🧠 Análisis Táctico o Justificación:")
                
                if st.form_submit_button("🚀 LANZAR AL RADAR"):
                    pid = f"{int(time.time())}"
                    nombre_partido = f"PARLAY: {partido_in}" if es_parlay else partido_in
                    
                    db.collection('pronosticos').document(pid).set({
                        'id': pid, 'partido': nombre_partido, 'mercado': mercado_in, 'cuota': cuota_in,
                        'prob_casa': pcasa_in, 'prob_real': preal_in, 'ev': ev_in,
                        'analisis': ana_in, 'selecciones': selecciones_in, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                    })
                    st.toast('¡Publicado en el Radar!', icon='🚀')
                    time.sleep(1)
                    st.rerun()

    # 8. Dashboard Principal
    st.markdown("<hr>", unsafe_allow_html=True)
    if not df.empty:
        df_activos = df[df['estatus'] == 'PENDIENTE']
        df_historial = df[df['estatus'] != 'PENDIENTE']

        met1, met2, met3 = st.columns(3)
        met1.metric("🔥 MÁXIMA VENTAJA", f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%")
        met2.metric("🎯 OPORTUNIDADES ACTIVAS", len(df_activos))
        met3.metric("🏦 BANKROLL ACTUAL", f"${bank_actual:,.2f}")

        t_futbol, t_parlay, t_hist, t_perfil = st.tabs(["⚽ FÚTBOL", "💎 PARLAY VIP", "📈 HISTORIAL", "⚙️ MI PERFIL & TOOLS"])
        
        with t_futbol:
            if not df_activos.empty:
                for i, r in df_activos.iterrows():
                    if "PARLAY" not in r['partido'].upper():
                        with st.expander(f"📍 {r['partido']} | {r['mercado']} | EV+: {r['ev']}%"):
                            st.markdown(f"<p style='color: #bc13fe; font-size: 0.85rem;'>PROB. REAL: {r.get('prob_real',0)}% | CUOTA: {r['cuota']}</p>", unsafe_allow_html=True)
                            st.write(r.get('analisis', ''))
                            st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                            
                            p, b = float(r.get('prob_real', 0)) / 100.0, float(r.get('cuota', 1.0)) - 1.0
                            sugerencia = max(10.0, bank_actual * (((b * p - (1 - p)) / b) * 0.25)) if (p>0 and b>0) else 10.0
                            
                            if r['id'] not in user_bets:
                                st.markdown(f"<p style='color: #00f2ff; font-size: 0.85rem;'>💡 <b>Kelly Fraccionario Sugerido:</b> ${sugerencia:.2f}</p>", unsafe_allow_html=True)
                                col_i1, col_i2 = st.columns([2, 1])
                                monto_apuesta = col_i1.number_input("💰 Tu Inversión ($):", min_value=1.0, value=float(round(sugerencia)), step=10.0, key=f"monto_{r['id']}")
                                if col_i2.button("➕ Invertir", key=f"add_{r['id']}"):
                                    db.collection('apuestas_usuarios').document(f"{st.session_state['user_correo']}_{r['id']}").set({
                                        'correo': st.session_state['user_correo'], 'pick_id': r['id'], 'monto': monto_apuesta, 'cuota': float(r['cuota'])
                                    })
                                    st.rerun()
                            else:
                                c_ok, c_del = st.columns([3, 1])
                                c_ok.success(f"✅ Invertiste **${user_bets[r['id']]['monto']}**")
                                if c_del.button("🗑️ Anular", key=f"cancel_{r['id']}"):
                                    db.collection('apuestas_usuarios').document(f"{st.session_state['user_correo']}_{r['id']}").delete()
                                    st.rerun()

        with t_parlay:
            parlays_activos = df_activos[df_activos['partido'].str.contains("PARLAY", case=False)]
            if not parlays_activos.empty:
                for i, p in parlays_activos.iterrows():
                    st.markdown("<div style='background: linear-gradient(45deg, #1a0b2e, #bc13fe33); padding: 25px; border-radius: 15px; border: 1px solid #bc13fe; box-shadow: 0 0 20px rgba(188, 19, 254, 0.2);'>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='color: #ffcc00; font-family: Orbitron;'>🎟️ {p['partido'].replace('PARLAY: ', '')}</h3>", unsafe_allow_html=True)
                    st.markdown(f"**Cuota Combinada:** {p['cuota']} | **EV+:** {p['ev']}%")
                    
                    # Mostrar las multiselecciones limpias
                    if p.get('selecciones'):
                        st.markdown("#### 📌 Selecciones:")
                        st.info(p['selecciones'])
                    
                    st.write(p.get('analisis', ''))
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

                    if p['id'] not in user_bets:
                        monto_p = st.number_input("💰 Tu Inversión ($):", value=50.0, key=f"monto_{p['id']}")
                        if st.button("➕ Invertir en Parlay", key=f"add_{p['id']}"):
                            db.collection('apuestas_usuarios').document(f"{st.session_state['user_correo']}_{p['id']}").set({
                                'correo': st.session_state['user_correo'], 'pick_id': p['id'], 'monto': monto_p, 'cuota': float(p['cuota'])
                            })
                            st.rerun()
                    else:
                        c_ok, c_del = st.columns([3, 1])
                        c_ok.success(f"✅ Invertiste **${user_bets[p['id']]['monto']}**")
                        if c_del.button("🗑️ Anular", key=f"cancel_{p['id']}"):
                            db.collection('apuestas_usuarios').document(f"{st.session_state['user_correo']}_{p['id']}").delete()
                            st.rerun()
                    st.markdown("</div><br>", unsafe_allow_html=True)
            else:
                st.info("Buscando combinaciones de alto valor... ⏳")

        with t_hist:
            h1, h2, h3 = st.columns(3)
            h1.metric("✅ ACIERTOS", ganadas_personales)
            h2.metric("❌ FALLOS", perdidas_personales)
            h3.metric("📊 WIN RATE", f"{(ganadas_personales/(ganadas_personales+perdidas_personales)*100) if (ganadas_personales+perdidas_personales)>0 else 0:.1f}%")
            st.markdown("#### HISTORIAL DE PORTAFOLIO")
            hay_hist = False
            for pid, bet in user_bets.items():
                if not df_historial.empty and pid in df_historial['id'].values:
                    hay_hist = True
                    p_data = df_historial[df_historial['id'] == pid].iloc[0]
                    icon = "🟢" if p_data['estatus'] == 'GANADA' else "🔴"
                    ganancia = (bet['monto'] * (bet['cuota'] - 1)) if p_data['estatus'] == 'GANADA' else -bet['monto']
                    with st.expander(f"{icon} {p_data['partido'].replace('PARLAY: ', '[PARLAY] ')}"):
                        st.write(f"Invertiste: ${bet['monto']} | **Resultado: ${ganancia:+.2f}**")
            if not hay_hist:
                st.info("Tus jugadas resueltas aparecerán aquí.")

        with t_perfil:
            st.markdown("### ⚙️ CONFIGURACIÓN DE CUENTA")
            st.info(f"Usuario activo: **{st.session_state['user_correo']}**")
            c_bank1, c_bank2 = st.columns([3, 1])
            nuevo_bank = c_bank1.number_input("Capital Inicial (Bankroll Fijo):", value=float(st.session_state.get('bank_inicial', 1000.0)), step=100.0)
            if c_bank2.button("Guardar Cambios", use_container_width=True):
                db.collection('usuarios').document(st.session_state['user_correo']).set({'bank_inicial': nuevo_bank}, merge=True)
                st.session_state['bank_inicial'] = nuevo_bank
                st.toast('Perfil actualizado', icon='🏦')
                time.sleep(1)
                st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("### 🧮 CALCULADORAS VIP")
            st.write("Herramientas de gestión de riesgo próximamente...")
            if st.button("🚪 CERRAR SESIÓN DE FORMA SEGURA"):
                st.session_state['autenticado'] = False
                st.rerun()

# ==========================================
# 🛑 MANEJO DE ERRORES INVISIBLE AL USUARIO
# ==========================================
except Exception as e:
    if st.session_state.get('user_rol') == 'admin':
        st.error(f"⚠️ ERROR TÉCNICO (Visible solo para Admin): {e}")
        st.code(traceback.format_exc())
    else:
        st.info("🔄 Axiom Data está sincronizando información con los servidores. Por favor, recarga la página en unos segundos.")

st.markdown("<br><hr><p style='text-align: center; color: #00f2ff; font-family: Orbitron; font-size: 0.8rem; opacity: 0.6;'>© 2026 DESARROLLADO POR TORVI ANALYTICS | DATA & FORESIGHT</p>", unsafe_allow_html=True)
