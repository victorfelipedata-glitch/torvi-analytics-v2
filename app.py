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
st.set_page_config(page_title="AXIOM DATA", layout="wide", initial_sidebar_state="collapsed")

# 2. Estilos CSS (Forzando Dark Mode y Diseño)
st.markdown("""
    <style>
    /* Forzar modo oscuro general */
    .stApp, .stApp > header { background-color: #050814 !important; color: #e0e0e0 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    .titulo-futurista { font-family: 'Orbitron', sans-serif; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px;}
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; font-size: 0.8rem;}
    
    /* Contenedores y botones */
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.8) !important; backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2) !important; border-radius: 15px; color: white !important;}
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.8) !important; backdrop-filter: blur(10px); border: 1px solid #00f2ff !important; border-radius: 10px; text-align: center; }
    div[data-testid="stMetric"] label { color: #b3cce6 !important; }
    div[data-testid="stMetric"] div { color: #00f2ff !important; }
    
    hr { border: 0; height: 1px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    
    /* Inputs siempre oscuros */
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: #0a1128 !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    
    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent !important;}
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.1) !important; border-radius: 10px 10px 0 0; color: #b3cce6 !important; padding: 10px 20px; font-family: 'Orbitron'; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.15) !important; border-bottom: 2px solid #00f2ff !important; color: #00f2ff !important; }
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
    item['partido'] = item['partido'].replace("[SENCILLA] ", "").replace("[Otra] ", "")
    data_list.append(item)
df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=['id', 'partido', 'mercado', 'cuota', 'prob_real', 'ev', 'estatus'])

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

# 7. Cabecera Interactiva (Actualizar y Bank)
col_btn1, col_btn2 = st.columns([4, 1])
with col_btn2:
    if st.button("🔄 ACTUALIZAR RADAR", use_container_width=True):
        st.rerun()

with st.expander("⚙️ CONFIGURAR MI CAPITAL INICIAL (BANKROLL)"):
    c_bank1, c_bank2 = st.columns([3, 1])
    nuevo_bank = c_bank1.number_input("Establece el dinero con el que iniciaste:", value=float(st.session_state.get('bank_inicial', 1000.0)), step=100.0)
    if c_bank2.button("Guardar Bank", use_container_width=True):
        db.collection('usuarios').document(st.session_state['user_correo']).update({'bank_inicial': nuevo_bank})
        st.session_state['bank_inicial'] = nuevo_bank
        st.toast('¡Capital actualizado con éxito!', icon='🏦')
        time.sleep(1)
        st.rerun()

# 8. Panel Admin - PUBLICAR
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ PANEL DE CONTROL - PUBLICAR NUEVO"):
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
                st.toast('¡Pick publicado en el Radar!', icon='🚀')
                time.sleep(1)
                st.rerun()

# 9. Dashboard Principal
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    met1, met2, met3 = st.columns(3)
    met1.metric("🔥 MÁXIMA VENTAJA", f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%")
    met2.metric("🎯 PICKS ACTIVOS", len(df_activos))
    met3.metric("🏦 BANKROLL ACTUAL", f"${bank_actual:,.2f}")

    t_futbol, t_parlay, t_hist, t_calc = st.tabs(["⚽ FÚTBOL", "💎 PARLAY VIP", "📈 RENDIMIENTO", "🧮 CALCULADORAS"])
    
    with t_futbol:
        if not df_activos.empty:
            for i, r in df_activos.iterrows():
                if "PARLAY" not in r['partido'].upper():
                    with st.expander(f"📍 {r['partido']} | {r['mercado']} | EV+: {r['ev']}%"):
                        st.markdown(f"<p style='color: #bc13fe; font-size: 0.85rem;'>PROB. REAL: {r.get('prob_real',0)}% | CUOTA: {r['cuota']}</p>", unsafe_allow_html=True)
                        st.write(r.get('analisis', 'Análisis en proceso...'))
                        
                        st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                        
                        # --- CÁLCULO DE KELLY SUGERIDO ---
                        p = float(r.get('prob_real', 0)) / 100.0
                        b = float(r.get('cuota', 1.0)) - 1.0
                        sugerencia = 10.0 # Mínimo
                        if p > 0 and b > 0:
                            kelly_frac = ((b * p - (1 - p)) / b) * 0.25 # 1/4 Kelly seguro
                            if kelly_frac > 0:
                                sugerencia = bank_actual * kelly_frac
                        
                        # --- CONTROLES DE PORTAFOLIO ---
                        if r['id'] not in user_bets:
                            st.markdown(f"<p style='color: #00f2ff; font-size: 0.8rem;'>💡 Inversión sugerida (Gestión Kelly 1/4): <b>${sugerencia:.2f}</b></p>", unsafe_allow_html=True)
                            col_i1, col_i2 = st.columns([2, 1])
                            monto_apuesta = col_i1.number_input("💰 Tu Inversión ($):", min_value=1.0, value=float(max(10.0, round(sugerencia))), step=10.0, key=f"monto_{r['id']}")
                            if col_i2.button("➕ Añadir al Portafolio", key=f"add_{r['id']}"):
                                db.collection('apuestas_usuarios').document(f"{st.session_state['user_correo']}_{r['id']}").set({
                                    'correo': st.session_state['user_correo'], 'pick_id': r['id'], 'monto': monto_apuesta, 'cuota': float(r['cuota'])
                                })
                                st.toast('Pick añadido a tu historial', icon='📋')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.success(f"✅ Pick Activo. Inversión: **${user_bets[r['id']]['monto']}**")
                        
                        # --- CONTROLES DE ADMIN ---
                        if st.session_state['user_rol'] == 'admin':
                            st.markdown("<br><p style='color: #ffcc00; font-size: 0.8rem;'>🛠️ CONTROLES ADMIN:</p>", unsafe_allow_html=True)
                            ca, cb, cc, cd = st.columns(4)
                            if ca.button(f"✅ Ganó", key=f"w_{r['id']}"):
                                db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                                st.rerun()
                            if cb.button(f"❌ Perdió", key=f"l_{r['id']}"):
                                db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                                st.rerun()
                            if cc.button(f"✏️ Editar", key=f"e_{r['id']}"):
                                st.session_state['editando_pick'] = r['id']
                                st.rerun()
                            if cd.button(f"🗑️ Borrar", key=f"del_{r['id']}"):
                                db.collection('pronosticos').document(r['id']).delete()
                                st.toast('Pronóstico eliminado', icon='🗑️')
                                time.sleep(1)
                                st.rerun()
                            
                            # FORMULARIO EDITAR
                            if st.session_state.get('editando_pick') == r['id']:
                                st.warning("Modificando parámetros...")
                                edit_cuota = st.number_input("Nueva Cuota:", value=float(r['cuota']), step=0.01, key=f"ec_{r['id']}")
                                edit_ev = st.number_input("Nuevo EV+ %:", value=float(r['ev']), step=0.1, key=f"eev_{r['id']}")
                                edit_ana = st.text_area("Análisis:", value=r.get('analisis',''), key=f"ea_{r['id']}")
                                c_save, c_cancel = st.columns(2)
                                if c_save.button("💾 Guardar", key=f"save_{r['id']}"):
                                    db.collection('pronosticos').document(r['id']).update({
                                        'cuota': edit_cuota, 'ev': edit_ev, 'analisis': edit_ana
                                    })
                                    st.session_state['editando_pick'] = None
                                    st.rerun()
                                if c_cancel.button("Cancelar", key=f"can_{r['id']}"):
                                    st.session_state['editando_pick'] = None
                                    st.rerun()
        else:
            st.info("Radar limpio. Escaneando mercados...")

    # Pestaña Parlay
    with t_parlay:
        parlays_activos = df_activos[df_activos['partido'].str.contains("PARLAY", case=False)]
        if not parlays_activos.empty:
            for i, p in parlays_activos.iterrows():
                st.markdown(f"### 🚀 {p['mercado']}")
                st.markdown(f"**Cuota Combinada:** {p['cuota']} | **Ventaja:** {p['ev']}%")
                st.success(p.get('analisis', ''))
                if p['id'] not in user_bets:
                    monto_p = st.number_input("💰 Inversión ($):", value=50.0, key=f"monto_{p['id']}")
                    if st.button("➕ Invertir en Parlay", key=f"add_{p['id']}"):
                        db.collection('apuestas_usuarios').document(f"{st.session_state['user_correo']}_{p['id']}").set({
                            'correo': st.session_state['user_correo'], 'pick_id': p['id'], 'monto': monto_p, 'cuota': float(p['cuota'])
                        })
                        st.toast('Parlay guardado', icon='🎫')
                        time.sleep(1)
                        st.rerun()
                else:
                    st.success(f"✅ Invertiste **${user_bets[p['id']]['monto']}** en este parlay.")
                
                if st.session_state['user_rol'] == 'admin':
                    cpa, cpb, cpc = st.columns(3)
                    if cpa.button(f"✅ Cobrar", key=f"wp_{p['id']}"):
                        db.collection('pronosticos').document(p['id']).update({'estatus': 'GANADA'})
                        st.rerun()
                    if cpb.button(f"❌ Fallado", key=f"lp_{p['id']}"):
                        db.collection('pronosticos').document(p['id']).update({'estatus': 'PERDIDA'})
                        st.rerun()
                    if cpc.button(f"🗑️ Borrar", key=f"delp_{p['id']}"):
                        db.collection('pronosticos').document(p['id']).delete()
                        st.rerun()
        else:
            st.info("El algoritmo está procesando las combinaciones de hoy... ⏳")

    # Historial
    with t_hist:
        h1, h2, h3 = st.columns(3)
        h1.metric("✅ ACIERTOS", ganadas_personales)
        h2.metric("❌ FALLOS", perdidas_personales)
        h3.metric("📊 WIN RATE", f"{(ganadas_personales/(ganadas_personales+perdidas_personales)*100) if (ganadas_personales+perdidas_personales)>0 else 0:.1f}%")
        
        st.markdown("#### TUS RESULTADOS HISTÓRICOS")
        hay_historial = False
        for pid, bet in user_bets.items():
            if not df_historial.empty and pid in df_historial['id'].values:
                hay_historial = True
                pick_data = df_historial[df_historial['id'] == pid].iloc[0]
                status_icon = "🟢" if pick_data['estatus'] == 'GANADA' else "🔴"
                ganancia = (bet['monto'] * (bet['cuota'] - 1)) if pick_data['estatus'] == 'GANADA' else -bet['monto']
                with st.expander(f"{status_icon} {pick_data['partido']} | {pick_data['mercado']}"):
                    st.write(f"Invertiste: ${bet['monto']} | Resultado: **${ganancia:+.2f}**")
        if not hay_historial:
            st.info("Tus jugadas resueltas aparecerán aquí.")

    with t_calc:
        st.markdown("### 🧮 GESTIÓN DE RIESGO")
        st.write("Próximamente: Calculadora de Hedging y Cierre Anticipado.")

if st.sidebar.button("🚪 CERRAR SESIÓN"):
    st.session_state['autenticado'] = False
    st.rerun()
