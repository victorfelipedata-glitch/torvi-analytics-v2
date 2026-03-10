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
st.set_page_config(page_title="QUASAR ANALYTICS", layout="wide", initial_sidebar_state="collapsed")

# CSS Estilo Galáctico
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #050814 50%, #000000 100%); background-attachment: fixed; }
    .subtitulo { color: #b3cce6; font-family: 'Orbitron', sans-serif; text-align: center; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; font-size: 0.8rem;}
    [data-testid="stForm"], div.stExpander { background: rgba(10, 17, 40, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 15px; }
    div[data-testid="stMetric"] { background: rgba(10, 17, 40, 0.6); backdrop-filter: blur(10px); border: 1px solid #00f2ff; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,242,255,0.1); }
    hr { border: 0; height: 2px; background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); }
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color: rgba(0, 0, 0, 0.6) !important; color: #00f2ff !important; border: 1px solid rgba(188, 19, 254, 0.5) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: rgba(188, 19, 254, 0.1); border-radius: 10px 10px 0 0; color: white; padding: 10px 20px; transition: all 0.3s ease;}
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 255, 0.2) !important; border-bottom: 2px solid #00f2ff !important; text-shadow: 0 0 10px #00f2ff;}
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
        <img src="https://raw.githubusercontent.com/victorfelipedata-glitch/torvi-analytics-v2/38bce5a4aa1f6ebf5cf113ebf193f03547f1dd2c/logo.jpg" width="350" style="border-radius: 15px; box-shadow: 0px 0px 30px rgba(188, 19, 254, 0.6);">
    </div>
    """, unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

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
df = pd.DataFrame(data_picks) if data_picks else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus', 'id', 'deporte'])

# Rescate de datos antiguos: Llenamos vacíos para que no desaparezcan
if not df.empty:
    if 'estatus' not in df.columns: df['estatus'] = 'PENDIENTE'
    if 'deporte' not in df.columns: df['deporte'] = 'Fútbol'
    df['estatus'] = df['estatus'].fillna('PENDIENTE')
    df['deporte'] = df['deporte'].fillna('Fútbol')

docs_port = db.collection('portafolio').where('user', '==', st.session_state['user_email']).stream()
df_port = pd.DataFrame([d.to_dict() for d in docs_port]) if docs_port else pd.DataFrame(columns=['partido', 'mercado', 'cuota', 'monto'])

user_ref = db.collection('usuarios').document(st.session_state['user_email'])
bank_actual = user_ref.get().to_dict().get('bankroll', 1000.0) if user_ref.get().exists else 1000.0

# --- BARRA SUPERIOR: ACTUALIZAR Y LOGOUT ---
col_head1, col_head2, col_head3 = st.columns([6, 2, 2])
if col_head2.button("🔄 ACTUALIZAR RADAR", use_container_width=True):
    st.toast("Actualizando datos del servidor...")
    time.sleep(0.5)
    st.rerun()
if col_head3.button("🚪 CERRAR SESIÓN", use_container_width=True):
    st.session_state['autenticado'] = False
    st.rerun()

# --- PANEL DE ADMIN INTACTO ---
if st.session_state['user_rol'] == 'admin':
    with st.expander("🛠️ EDITOR Y PANEL DE CONTROL (ADMIN)"):
        with st.form("nuevo_pick"):
            c_a, c_b, c_c = st.columns([2, 2, 1])
            partido = c_a.text_input("⚽/🏀 Encuentro:", placeholder="Ej: Man City vs Liverpool")
            mercado = c_b.text_input("🎯 Mercado:", placeholder="Ej: +4.5 Tiros a Puerta")
            deporte = c_c.selectbox("Deporte:", ["Fútbol", "NBA", "NFL", "Tenis"])
            
            c_n1, c_n2, c_n3, c_n4 = st.columns(4)
            cuota = c_n1.number_input("📈 Cuota:", min_value=1.01, value=1.90, step=0.01)
            prob_casa = c_n2.number_input("🏦 Prob. Casa %:", value=50.0)
            prob_real = c_n3.number_input("🎯 Prob. Real %:", value=60.0)
            ev_val = c_n4.number_input("🔥 EV+ %:", value=10.0)
            
            ana = st.text_area("🧠 Análisis Táctico y Matemático:")
            if st.form_submit_button("🚀 PUBLICAR EN EL RADAR"):
                p_id = f"{int(time.time())}"
                db.collection('pronosticos').document(p_id).set({
                    'id': p_id, 'partido': partido, 'mercado': mercado, 'deporte': deporte, 'cuota': cuota,
                    'prob_casa': prob_casa, 'prob_real': prob_real, 'ev': ev_val,
                    'analisis': ana, 'estatus': 'PENDIENTE', 'fecha': datetime.now()
                })
                st.success("¡Pick publicado!")
                st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.markdown("<hr>", unsafe_allow_html=True)
if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_historial = df[df['estatus'] != 'PENDIENTE']

    # Métricas Pro
    m1, m2, m3 = st.columns(3)
    max_ev = f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%"
    m1.metric("🔥 MAYOR VENTAJA (EV+)", max_ev)
    m2.metric("🎯 OPORTUNIDADES ACTIVAS", len(df_activos))
    m3.metric("🏦 BANKROLL ACTUAL", f"${bank_actual:,.2f}")
    
    # 🗂️ FILTROS Y PESTAÑAS
    tab_futbol, tab_nba, tab_parlay, tab_port, tab_historial, tab_tools = st.tabs(["⚽ FÚTBOL", "🏀 NBA", "💎 PARLAY VIP", "💼 PORTAFOLIO", "📈 HISTORIAL", "⚙️ PERFIL"])
    
    # --- ⚽ PESTAÑA FÚTBOL ---
    with tab_futbol:
        df_futbol = df_activos[(df_activos['deporte'] == 'Fútbol') & (~df_activos['partido'].str.contains("Parlay", case=False, na=False))]
        if not df_futbol.empty:
            # 📊 GRÁFICA DE RADAR (Con altura dinámica para que no se vea como bloque)
            altura_grafica = max(200, len(df_futbol) * 60)
            fig = px.bar(df_futbol, x='ev', y='mercado', orientation='h', color='ev', template="plotly_dark", color_continuous_scale="Viridis")
            fig.update_layout(height=altura_grafica, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

            for i, r in df_futbol.iterrows():
                sugerencia = bank_actual * 0.05 
                st.markdown(f"""
                    <div style='background: rgba(10, 17, 40, 0.7); padding: 20px; border-radius: 15px; border: 1px solid #00f2ff; margin-bottom: 10px;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <h3 style='color: white; margin: 0;'>{r['partido']}</h3>
                            <span style='color: #00ff00; font-weight: bold; font-family: Orbitron; background: rgba(0,255,0,0.1); padding: 5px 10px; border-radius: 8px;'>EV+ {r['ev']}%</span>
                        </div>
                        <p style='color: #bc13fe; font-weight: bold; margin-top: 10px;'>🎯 {r['mercado']}</p>
                        <div style='display: flex; gap: 15px; margin: 15px 0;'>
                            <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>CUOTA: <b>{r['cuota']}</b></div>
                            <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>PROB. CASA: <b>{r.get('prob_casa',0)}%</b></div>
                            <div style='background: rgba(0,0,0,0.5); padding: 8px 15px; border-radius: 5px; color: #00f2ff; border: 1px solid #333;'>PROB. REAL: <b>{r.get('prob_real',0)}%</b></div>
                        </div>
                        <p style='font-size: 0.95rem; color: #b3cce6;'>{r.get('analisis', '')}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 💰 CALCULADORA DE INVERSIÓN
                st.markdown("<div style='background: rgba(0, 242, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #00f2ff; margin-bottom: 20px;'>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: white; margin-bottom: 5px;'>💡 <b>Gestión de Riesgo:</b> Sugerencia del 5.0% de tu Bankroll</p>", unsafe_allow_html=True)
                col_i1, col_i2 = st.columns([1, 2])
                monto_invertir = col_i1.number_input("Tu Inversión ($):", value=float(sugerencia), key=f"inv_{r['id']}")
                if col_i2.button("📥 Guardar en Mi Portafolio", key=f"btn_{r['id']}"):
                    db.collection('portafolio').document(f"{st.session_state['user_email']}_{r['id']}").set({
                        'user': st.session_state['user_email'], 'partido': r['partido'], 'mercado': r['mercado'],
                        'cuota': r['cuota'], 'monto': monto_invertir, 'fecha': datetime.now()
                    })
                    st.toast("¡Inversión guardada en el portafolio!")
                st.markdown("</div>", unsafe_allow_html=True)

                if st.session_state['user_rol'] == 'admin':
                    c_wa, c_wb, c_wc = st.columns(3)
                    if c_wa.button(f"✅ Ganada", key=f"w_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'}); st.rerun()
                    if c_wb.button(f"❌ Perdida", key=f"l_{r['id']}"): db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'}); st.rerun()
                    if c_wc.button(f"🗑️ Eliminar", key=f"del_{r['id']}"): db.collection('pronosticos').document(r['id']).delete(); st.rerun()
                st.markdown("<hr style='opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("El radar de fútbol está despejado.")

    # --- 🏀 PESTAÑA NBA ---
    with tab_nba:
        df_nba = df_activos[(df_activos['deporte'] == 'NBA') & (~df_activos['partido'].str.contains("Parlay", case=False, na=False))]
        if not df_nba.empty:
            st.success("Pronósticos de NBA listos.")
        else:
            st.info("Aún no inicia la cobertura de la duela.")

    # --- 💎 PESTAÑA PARLAY ---
    with tab_parlay:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #1a0b2e 0%, #bc13fe 100%); padding: 25px; border-radius: 20px; border: 2px solid #ffcc00; box-shadow: 0px 0px 20px rgba(188, 19, 254, 0.5);'>
                <h2 style='text-align: center; color: #ffcc00; font-family: Orbitron; margin:0;'>👑 PARLAY EXCLUSIVO VIP</h2>
            </div><br>
        """, unsafe_allow_html=True)
        
        df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False, na=False)]
        if not df_parlays.empty:
            for i, p in df_parlays.iterrows():
                st.markdown(f"""
                    <div style='background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #ffcc00;'>
                        <h3 style='color: white;'>{p['partido']}</h3>
                        <h4 style='color: #ffcc00; margin-bottom: 5px;'>{p['mercado']}</h4>
                        <p style='color: #00f2ff; font-weight: bold;'>CUOTA FINAL: {p['cuota']} | EV+: {p['ev']}%</p>
                        <p style='font-size: 0.95rem; color: white;'>{p.get('analisis','')}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.session_state['user_rol'] == 'admin':
                    c_pa, c_pb, c_pc = st.columns(3)
                    if c_pa.button(f"✅ Cobrar", key=f"wp_{p['id']}"): db.collection('pronosticos').document(p['id']).update({'estatus': 'GANADA'}); st.rerun()
                    if c_pb.button(f"❌ Fallado", key=f"lp_{p['id']}"): db.collection('pronosticos').document(p['id']).update({'estatus': 'PERDIDA'}); st.rerun()
                    if c_pc.button(f"🗑️ Eliminar", key=f"delp_{p['id']}"): db.collection('pronosticos').document(p['id']).delete(); st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("Cocinando la combinada perfecta del día...")

    # --- 💼 PESTAÑA PORTAFOLIO ---
    with tab_port:
        st.markdown("### 💼 MIS INVERSIONES ACTIVAS")
        if not df_port.empty:
            inversion_total = df_port['monto'].sum()
            st.markdown(f"<p style='font-size: 1.2rem; color: #00f2ff;'>Total en Riesgo: <b>${inversion_total:,.2f}</b></p>", unsafe_allow_html=True)
            for i, r in df_port.iterrows():
                st.markdown(f"<div style='border-left: 3px solid #bc13fe; padding: 15px; background: rgba(0,0,0,0.4); border-radius: 5px; margin-bottom: 10px;'><b style='color:white;'>{r['partido']}</b><br><span style='color:#b3cce6;'>{r['mercado']} | Cuota: {r['cuota']} | Inversión: <b>${r['monto']:,.2f}</b></span></div>", unsafe_allow_html=True)
        else:
            st.info("Aún no tienes apuestas guardadas. Usa el botón 'Guardar en Mi Portafolio' en el radar.")

    # --- 📈 PESTAÑA HISTORIAL ---
    with tab_historial:
        if not df_historial.empty:
            ganadas = len(df_historial[df_historial['estatus'] == 'GANADA'])
            perdidas = len(df_historial[df_historial['estatus'] == 'PERDIDA'])
            wr = (ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0
            
            c_h1, c_h2, c_h3 = st.columns(3)
            c_h1.metric("✅ ACIERTOS", ganadas)
            c_h2.metric("❌ FALLOS", perdidas)
            c_h3.metric("📈 WIN RATE", f"{wr:.1f}%")
            
            # 📊 GRÁFICAS DEL HISTORIAL
            c_g1, c_g2 = st.columns(2)
            resumen = df_historial.groupby('estatus').size().reset_index(name='cantidad')
            fig_pie = px.pie(resumen, values='cantidad', names='estatus', color='estatus', color_discrete_map={'GANADA': '#00ff00', 'PERDIDA': '#ff0000'}, hole=0.4, template="plotly_dark", title="Rendimiento Global")
            c_g1.plotly_chart(fig_pie, use_container_width=True)
            
            # Gráfica de línea simulando crecimiento
            df_historial_ordenado = df_historial.sort_values(by='fecha')
            crecimiento = []
            dinero = 0
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
        else:
            st.info("El historial aparecerá aquí conforme se resuelvan los partidos.")

    # --- ⚙️ PESTAÑA PERFIL / TOOLS ---
    with tab_tools:
        st.markdown("### ⚙️ CONFIGURACIÓN DE CUENTA")
        st.markdown(f"<p style='color: #b3cce6;'>Usuario activo: {st.session_state['user_email']}</p>", unsafe_allow_html=True)
        col_u1, col_u2 = st.columns([2, 1])
        nuevo_bank = col_u1.number_input("Capital Inicial (Bankroll Fijo):", value=float(bank_actual), step=50.0)
        
        if col_u2.button("💾 GUARDAR CAMBIOS", use_container_width=True):
            user_ref.update({'bankroll': nuevo_bank})
            st.success("¡Datos sincronizados con éxito!")
            time.sleep(1)
            st.rerun()

else:
    st.info("Base de datos vacía. Esperando primer análisis del núcleo...")

# --- FOOTER CON TU AUTORÍA ---
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("""
    <p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; font-size: 0.85rem; opacity: 0.8;'>
        © 2026 DESARROLLADO POR VÍCTOR ANTONIO FELIPE MARTÍNEZ | QUASAR ANALYTICS
    </p>
""", unsafe_allow_html=True)



