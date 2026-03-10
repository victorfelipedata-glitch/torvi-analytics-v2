import streamlit as st
import pandas as pd
import time
import json
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AXIOM DATA | Terminal", layout="wide")

# --- CSS: ESTILO FINTECH / TERMINAL DE TRADING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #0B0F19; font-family: 'Inter', sans-serif; }
    
    .titulo-axiom { font-family: 'Inter', sans-serif; color: #E2E8F0; font-size: 2.8rem; font-weight: 800; text-align: center; margin-bottom: -10px; letter-spacing: -1px; }
    .titulo-axiom span { color: #3B82F6; }
    .subtitulo { color: #64748B; font-family: 'JetBrains Mono', monospace; text-align: center; letter-spacing: 2px; margin-bottom: 30px; font-size: 0.85rem; }
    
    .pick-card { background-color: #111827; border: 1px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #3B82F6; }
    .pick-card.vip { border-left: 4px solid #F59E0B; background: linear-gradient(145deg, #111827, #1A1500); border: 1px solid #453300; }
    
    .pick-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 15px; }
    .pick-title { font-size: 1.2rem; font-weight: 600; color: #F8FAFC; margin: 0; }
    .pick-ev { background-color: rgba(16, 185, 129, 0.1); color: #10B981; padding: 4px 10px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.9rem;}
    
    .pick-stats { display: flex; gap: 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #94A3B8; margin-bottom: 15px;}
    .stat-box { background: #0F172A; padding: 10px 15px; border-radius: 8px; border: 1px solid #1E293B; }
    .stat-box span { display: block; font-size: 0.7rem; color: #64748B; text-transform: uppercase; margin-bottom: 3px;}
    .stat-val { color: #E2E8F0; font-weight: 700; font-size: 1.1rem; }
    
    .kelly-box { background: rgba(59, 130, 246, 0.1); border: 1px solid #3B82F6; color: #60A5FA; padding: 10px; border-radius: 8px; text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; margin-bottom: 15px;}
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { background-color: #1E293B; border-radius: 8px 8px 0 0; color: #94A3B8; padding: 10px 20px; font-weight: 600; border: none; }
    .stTabs [aria-selected="true"] { background-color: #3B82F6 !important; color: white !important; border-bottom: none !important; }
    
    div[data-testid="stMetric"] { background-color: #111827; border: 1px solid #1E293B; border-radius: 10px; padding: 15px; box-shadow: none; }
    
    /* Input custom para la inversión */
    .stNumberInput input { background-color: #0F172A !important; color: #10B981 !important; border: 1px solid #1E293B !important; font-weight: bold; font-family: 'JetBrains Mono'; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A FIREBASE ---
try:
    if not firebase_admin._apps:
        dict_claves = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(dict_claves)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception:
    st.error("Error conectando a los servidores.")
    st.stop()

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- SESIÓN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'invitado'
if 'user_email' not in st.session_state: st.session_state['user_email'] = ''

st.markdown('<p class="titulo-axiom">AXIOM <span>DATA</span></p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE VENTAJA ESTADÍSTICA Y EV+</p>', unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state['autenticado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='background: #111827; padding: 30px; border-radius: 16px; border: 1px solid #1E293B;'>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INICIAR SESIÓN", "CREAR CUENTA"])
        with t1:
            with st.form("f_login"):
                u = st.text_input("Correo:")
                p = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("ACCEDER AL TERMINAL", use_container_width=True):
                    if u.strip(): 
                        try:
                            res = db.collection('usuarios').document(u).get()
                            if res.exists and res.to_dict().get('password') == encriptar_password(p):
                                st.session_state['autenticado'] = True
                                st.session_state['user_rol'] = res.to_dict().get('rol', 'usuario_vip')
                                st.session_state['user_email'] = u
                                st.rerun()
                            else: st.error("Credenciales incorrectas.")
                        except Exception: st.error("Error de red.")
        with t2:
            with st.form("f_reg"):
                un = st.text_input("Nuevo Correo:")
                pn = st.text_input("Nueva Contraseña:", type="password")
                if st.form_submit_button("REGISTRARSE", use_container_width=True):
                    if un.strip() and pn.strip():
                        db.collection('usuarios').document(un).set({'correo': un, 'password': encriptar_password(pn), 'rol': 'usuario_vip', 'bankroll': 1000.0})
                        st.success("Cuenta creada. Inicia sesión.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- BLINDAJE DE SEGURIDAD ---
user_email = st.session_state.get('user_email', '').strip()
if not user_email:
    st.session_state['autenticado'] = False
    st.rerun()

# --- DATOS DEL USUARIO Y PORTAFOLIO ---
base_bankroll = 1000.0
mis_picks_dict = {}

try:
    user_doc = db.collection('usuarios').document(user_email).get()
    if user_doc.exists:
        base_bankroll = float(user_doc.to_dict().get('bankroll', 1000.0))
        
    mis_picks_refs = db.collection('usuarios').document(user_email).collection('portafolio').stream()
    mis_picks_dict = {doc.id: doc.to_dict() for doc in mis_picks_refs}
except Exception:
    pass

# --- CARGA DE PRONÓSTICOS GLOBALES ---
data = []
try:
    docs = db.collection('pronosticos').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
    for d in docs:
        item = d.to_dict()
        if 'estatus' not in item: item['estatus'] = 'PENDIENTE'
        data.append(item)
except Exception:
    pass

df = pd.DataFrame(data) if data else pd.DataFrame(columns=['id', 'partido', 'mercado', 'cuota', 'prob_casa', 'prob_real', 'ev', 'analisis', 'estatus'])

# --- SIDEBAR LIMPIO ---
st.sidebar.markdown(f"<h3 style='color: #E2E8F0; font-family: Inter;'>👤 {user_email.split('@')[0]}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='color: #64748B; font-family: JetBrains Mono; font-size: 0.8rem;'>ROL: {st.session_state['user_rol'].upper()}</p>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color: #1E293B;'>", unsafe_allow_html=True)
if st.sidebar.button("Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.session_state['user_email'] = ''
    st.rerun()

# --- FUNCIONES MATEMÁTICAS (CORREGIDAS: Quarter-Kelly + Tope 5%) ---
def calcular_kelly(ev_pct, cuota, bankroll):
    if cuota <= 1 or ev_pct <= 0: return 0.0, 0.0
    p = (ev_pct / 100) + (1 / cuota) 
    b = cuota - 1
    kelly_frac = (p * b - (1 - p)) / b
    
    # Usamos Quarter-Kelly (25%) para absorber varianza
    quarter_kelly = max(0, kelly_frac * 0.25)
    # Regla de oro: Jamás superar el 5% del bankroll
    pct_final = min(quarter_kelly, 0.05) 
    
    inversion = bankroll * pct_final
    return inversion, pct_final * 100

st.markdown("<hr style='border-color: #1E293B;'>", unsafe_allow_html=True)

if not df.empty:
    df_activos = df[df['estatus'] == 'PENDIENTE']
    df_normales = df_activos[~df_activos['partido'].str.contains("Parlay", case=False, na=False)]
    df_parlays = df_activos[df_activos['partido'].str.contains("Parlay", case=False, na=False)]

    m1, m2, m3 = st.columns(3)
    m1.metric("🔥 MAYOR VENTAJA", f"{df_activos['ev'].max()}%" if not df_activos.empty else "0%")
    m2.metric("🎯 EN EL RADAR", len(df_activos))
    m3.metric("🏦 MI CAPITAL (BANK)", f"${base_bankroll:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tabs = ["📡 RADAR", "💎 PARLAY VIP", "💼 MI PORTAFOLIO", "⚙️ PERFIL"]
    if st.session_state['user_rol'] == 'admin': tabs.append("👑 ADMIN")
    paneles = st.tabs(tabs)
    
    # === PESTAÑA 1: RADAR (MERCADO GLOBAL) ===
    with paneles[0]:
        if not df_normales.empty:
            for i, r in df_normales.iterrows():
                pid = r['id']
                inv_recomendada, pct_bank = calcular_kelly(r.get('ev',0), r.get('cuota',1.01), base_bankroll)
                
                st.markdown(f"""
                <div class="pick-card">
                    <div class="pick-header">
                        <h3 class="pick-title">{str(r.get('partido','')).replace('[SENCILLA]','')}</h3>
                        <span class="pick-ev">EV+ {r.get('ev',0)}%</span>
                    </div>
                    <p style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 15px;">🎯 {r.get('mercado','')}</p>
                    <div class="pick-stats">
                        <div class="stat-box"><span>Cuota</span><div class="stat-val">{r.get('cuota',0)}</div></div>
                        <div class="stat-box"><span>Prob. Casa</span><div class="stat-val">{r.get('prob_casa',0)}%</div></div>
                        <div class="stat-box"><span>Prob. Real</span><div class="stat-val" style="color:#3B82F6;">{r.get('prob_real',0)}%</div></div>
                    </div>
                    <div class="kelly-box">
                        💡 <b>Gestión de Riesgo:</b> Sugerencia del <b>{pct_bank:.1f}%</b> de tu Bankroll (${inv_recomendada:.2f})
                    </div>
                    <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">{r.get('analisis','')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # --- SISTEMA DE INVERSIÓN LIBRE ---
                if pid in mis_picks_dict:
                    st.success(f"✅ En tu Portafolio (Apostaste: ${mis_picks_dict[pid].get('stake', 0):.2f})")
                else:
                    c_input, c_btn = st.columns([1, 2])
                    with c_input:
                        monto_elegido = st.number_input("Tu Inversión ($):", min_value=0.0, value=float(inv_recomendada), step=10.0, key=f"in_{pid}")
                    with c_btn:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("📥 Guardar en Mi Portafolio", key=f"add_{pid}"):
                            try:
                                db.collection('usuarios').document(user_email).collection('portafolio').document(pid).set({
                                    'pick_id': pid, 'stake': monto_elegido, 'fecha': datetime.now()
                                })
                                st.rerun()
                            except Exception: st.error("Error al guardar.")
                st.markdown("<hr style='border-color: #1E293B; margin-top: 30px;'>", unsafe_allow_html=True)
        else:
            st.info("Radar analizando mercados. No hay oportunidades sencillas por ahora.")

    # === PESTAÑA 2: PARLAY VIP ===
    with paneles[1]:
        if not df_parlays.empty:
            for i, r in df_parlays.iterrows():
                pid = r['id']
                inv_recomendada, pct_bank = calcular_kelly(r.get('ev',0), r.get('cuota',1.01), base_bankroll)
                
                st.markdown(f"""
                <div class="pick-card vip">
                    <div class="pick-header">
                        <h3 class="pick-title" style="color:#F59E0B;">👑 {str(r.get('partido','')).replace('[PARLAY]','').strip()}</h3>
                        <span class="pick-ev" style="background:rgba(245,158,11,0.1); color:#F59E0B;">EV+ {r.get('ev',0)}%</span>
                    </div>
                    <p style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 15px;">🎯 {r.get('mercado','')}</p>
                    <div class="pick-stats">
                        <div class="stat-box" style="border-color:#453300;"><span>Cuota Combinada</span><div class="stat-val" style="color:#F59E0B;">{r.get('cuota',0)}</div></div>
                    </div>
                    <div class="kelly-box" style="background:rgba(245,158,11,0.05); border-color:#F59E0B; color:#FCD34D;">
                        💡 <b>Gestión de Riesgo:</b> Sugerencia de ${inv_recomendada:.2f}
                    </div>
                    <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">{r.get('analisis','')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if pid in mis_picks_dict:
                    st.success(f"✅ Parlay guardado (Inversión: ${mis_picks_dict[pid].get('stake', 0):.2f})")
                else:
                    c_input, c_btn = st.columns([1, 2])
                    with c_input:
                        monto_elegido = st.number_input("Tu Inversión ($):", min_value=0.0, value=float(inv_recomendada), step=10.0, key=f"in_p_{pid}")
                    with c_btn:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("📥 Seguir Parlay", key=f"add_p_{pid}"):
                            try:
                                db.collection('usuarios').document(user_email).collection('portafolio').document(pid).set({
                                    'pick_id': pid, 'stake': monto_elegido, 'fecha': datetime.now()
                                })
                                st.rerun()
                            except Exception: st.error("Error al guardar.")
                st.markdown("<hr style='border-color: #453300; margin-top: 30px;'>", unsafe_allow_html=True)
        else:
            st.info("El algoritmo está procesando la combinada de hoy...")

    # === PESTAÑA 3: MI PORTAFOLIO (PERSONAL) ===
    with paneles[2]:
        st.markdown("<h3 style='color: #E2E8F0; font-family: Inter;'>Mis Apuestas Activas</h3>", unsafe_allow_html=True)
        
        mis_picks_completos = []
        for pid, pdata in mis_picks_dict.items():
            info_global = df[df['id'] == pid]
            if not info_global.empty:
                pick_info = info_global.iloc[0].to_dict()
                pick_info['mi_stake'] = pdata.get('stake', 0)
                mis_picks_completos.append(pick_info)
                
        df_mi_portafolio = pd.DataFrame(mis_picks_completos)
        
        if not df_mi_portafolio.empty:
            activos_mios = df_mi_portafolio[df_mi_portafolio['estatus'] == 'PENDIENTE']
            resueltos_mios = df_mi_portafolio[df_mi_portafolio['estatus'] != 'PENDIENTE']
            
            if not activos_mios.empty:
                for i, r in activos_mios.iterrows():
                    c_info, c_del = st.columns([5, 1])
                    with c_info:
                        st.markdown(f"""
                        <div style="background:#0F172A; padding:15px; border-radius:8px; border-left:3px solid #3B82F6; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="color:#E2E8F0; font-weight:bold;">{r.get('partido','')}</span><br>
                                <span style="color:#64748B; font-size:0.8rem;">{r.get('mercado','')} | Cuota {r.get('cuota',0)}</span>
                            </div>
                            <div style="text-align:right;">
                                <span style="color:#94A3B8; font-size:0.8rem;">Invertido</span><br>
                                <span style="color:#10B981; font-weight:bold; font-family:JetBrains Mono;">${r.get('mi_stake',0):.2f}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_del:
                        # --- BOTÓN PARA ELIMINAR DEL PORTAFOLIO ---
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{r['id']}", help="Eliminar de mi portafolio"):
                            try:
                                db.collection('usuarios').document(user_email).collection('portafolio').document(r['id']).delete()
                                st.rerun()
                            except Exception: st.error("Error al borrar.")
            else: st.write("No tienes apuestas en juego en este momento.")
            
            st.markdown("<hr style='border-color: #1E293B;'><h3 style='color: #E2E8F0; font-family: Inter;'>Mi Historial</h3>", unsafe_allow_html=True)
            if not resueltos_mios.empty:
                mis_ganadas = len(resueltos_mios[resueltos_mios['estatus'] == 'GANADA'])
                mis_perdidas = len(resueltos_mios[resueltos_mios['estatus'] == 'PERDIDA'])
                mi_wr = (mis_ganadas/(mis_ganadas+mis_perdidas))*100 if (mis_ganadas+mis_perdidas)>0 else 0
                
                ch1, ch2, ch3 = st.columns(3)
                ch1.metric("MIS ACIERTOS", mis_ganadas)
                ch2.metric("MIS FALLOS", mis_perdidas)
                ch3.metric("MI WIN RATE", f"{mi_wr:.1f}%")
                
                for i, r in resueltos_mios.iterrows():
                    color = "#10B981" if r['estatus'] == 'GANADA' else "#EF4444"
                    icon = "✅" if r['estatus'] == 'GANADA' else "❌"
                    st.markdown(f"""
                    <div style="background:#0F172A; padding:10px 15px; border-radius:8px; border-left:3px solid {color}; margin-bottom:5px; opacity: 0.8;">
                        <span style="color:#E2E8F0; font-size:0.9rem;">{icon} {r.get('partido','')} ({r.get('mercado','')})</span>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.write("Tu historial está vacío.")
        else:
            st.info("Ve a la pestaña RADAR y añade pronósticos a tu portafolio.")

    # === PESTAÑA 4: PERFIL ===
    with paneles[3]:
        st.markdown("<h3 style='color: #E2E8F0; font-family: Inter;'>Configuración de Capital</h3>", unsafe_allow_html=True)
        st.write("Axiom Data utiliza la fórmula Quarter-Kelly (max 5%) para calcular tu riesgo basado en tu Bankroll configurado.")
        with st.form("form_bank"):
            nuevo_b = st.number_input("Mi Bankroll Actual ($):", value=base_bankroll, step=50.0)
            if st.form_submit_button("Actualizar Sistema"):
                try:
                    db.collection('usuarios').document(user_email).update({'bankroll': nuevo_b})
                    st.success("Bankroll actualizado.")
                    time.sleep(1)
                    st.rerun()
                except Exception: st.error("Error guardando el bankroll.")

    # === PESTAÑA 5: ADMIN ===
    if st.session_state['user_rol'] == 'admin':
        with paneles[4]:
            st.markdown("<h3 style='color: #E2E8F0;'>Panel de Resolución</h3>", unsafe_allow_html=True)
            st.write("Cierra los picks activos aquí. Esto actualizará el portafolio de todos los usuarios automáticamente.")
            if not df_activos.empty:
                for i, r in df_activos.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"{r.get('partido','')} - {r.get('mercado','')}")
                    if cb.button("✅ Win", key=f"ad_w_{r['id']}"):
                        try:
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'GANADA'})
                            st.rerun()
                        except Exception: pass
                    if cc.button("❌ Loss", key=f"ad_l_{r['id']}"):
                        try:
                            db.collection('pronosticos').document(r['id']).update({'estatus': 'PERDIDA'})
                            st.rerun()
                        except Exception: pass
            else: st.write("No hay picks pendientes por resolver.")
            
            st.markdown("<hr style='border-color: #1E293B;'><h3 style='color: #E2E8F0;'>Publicar Nueva Señal</h3>", unsafe_allow_html=True)
            with st.form("form_admin_nuevo"):
                c1, c2 = st.columns(2)
                p_partido = c1.text_input("Partido (Usa 'Parlay' para VIP):")
                p_mercado = c2.text_input("Mercado:")
                n1, n2, n3, n4 = st.columns(4)
                p_cuota = n1.number_input("Cuota:", value=1.90, step=0.01)
                p_casa = n2.number_input("Prob. Casa %:", value=50.0)
                p_real = n3.number_input("Prob. Real %:", value=60.0)
                p_ev = n4.number_input("EV+ %:", value=10.0)
                p_ana = st.text_area("Análisis:")
                
                if st.form_submit_button("Lanzar al Radar"):
                    try:
                        p_id = f"{int(time.time())}"
                        db.collection('pronosticos').document(p_id).set({
                            'id': p_id, 'partido': p_partido, 'mercado': p_mercado, 'cuota': p_cuota,
                            'prob_casa': p_casa, 'prob_real': p_real, 'ev': p_ev, 'analisis': p_ana, 
                            'estatus': 'PENDIENTE', 'fecha': datetime.now()
                        })
                        st.success("Señal publicada.")
                        time.sleep(1)
                        st.rerun()
                    except Exception: st.error("Error publicando la señal.")

else:
    st.info("Conectado a la base de datos de Axiom. Esperando datos...")

