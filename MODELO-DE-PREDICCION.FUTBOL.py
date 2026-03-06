import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. SETUP DEL DASHBOARD ---
st.set_page_config(page_title="Torvi | Bet Analytics Center", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #050b14; }
    .stMetric { 
        background-color: rgba(15, 23, 42, 0.8); 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #00ffcc; 
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.15);
    }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Arial', sans-serif; }
    .dataframe { border: 1px solid #00ffcc !important; }
    .streamlit-expanderHeader { font-weight: bold !important; color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS EN LA NUBE (INMUNE A ERRORES) ---
@st.cache_data(ttl=60)
def cargar_picks_del_dia():
    url_sheet = "https://docs.google.com/spreadsheets/d/12lDBRn6nXm4yvzjHhqL6w2FbCw8FPS1dYt5BoZYuP4w/export?format=csv"
    
    try:
        df = pd.read_csv(url_sheet)
        
        # 🛡️ TRUCO DE ORO: Limpia los títulos de las columnas (mayúsculas y sin espacios extra)
        df.columns = df.columns.str.strip().str.upper()
        
        df = df.dropna(subset=['PARTIDO', 'EV+'])
        
        df['PROBABILIDAD'] = pd.to_numeric(df['PROBABILIDAD'], errors='coerce')
        df['CUOTA CASA'] = pd.to_numeric(df['CUOTA CASA'], errors='coerce')
        df['CUOTA REAL'] = pd.to_numeric(df['CUOTA REAL'], errors='coerce')
        df['EV+'] = pd.to_numeric(df['EV+'], errors='coerce')
        
        # Si la celda de análisis está vacía, le ponemos un texto por defecto
        if 'ANALISIS' not in df.columns:
            df['ANALISIS'] = "Análisis en desarrollo. Cargando contexto táctico..."
        else:
            df['ANALISIS'] = df['ANALISIS'].fillna("Análisis puramente matemático (Ventaja EV+).")
            
        condiciones = [
            (df['EV+'] > 10) & (df['PROBABILIDAD'] >= 50),
            (df['EV+'] > 15) & (df['PROBABILIDAD'] < 50),
            (df['EV+'] <= 0)
        ]
        decisiones = ['🔥 Stake Alto', '⚠️ Stake Bajo (Longshot)', '❌ No Apostar']
        df['Recomendación'] = np.select(condiciones, decisiones, default='✅ Stake Medio')
        
        return df
        
    except Exception as e:
        return pd.DataFrame()

df_picks = cargar_picks_del_dia()

# --- 3. FILTROS LATERALES (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5351/5351486.png", width=100)
st.sidebar.header("🔍 Centro de Mando")
st.sidebar.write("Filtra los mercados según tu estrategia:")

if not df_picks.empty and 'LIGA' in df_picks.columns:
    ligas_disponibles = ['Todas'] + list(df_picks['LIGA'].dropna().unique())
    liga_sel = st.sidebar.selectbox("⚽ Competición:", ligas_disponibles)
    
    if liga_sel != 'Todas':
        df_filtrado = df_picks[df_picks['LIGA'] == liga_sel]
    else:
        df_filtrado = df_picks
else:
    df_filtrado = df_picks

# --- 4. HEADER PRINCIPAL ---
st.title("⚡ Torvi Bet Analytics | Algoritmo EV+")
st.write("Buscador de Cuotas de Valor (Value Bets) basado en modelos matemáticos y contexto deportivo.")
st.divider()

if df_picks.empty:
    st.warning("⚠️ No se encontraron picks. Asegúrate de tener datos en tu Google Sheet.")
else:
    # --- 5. PESTAÑAS PRO (TABS) ---
    tab1, tab2, tab3 = st.tabs(["🎯 Picks de Hoy", "📈 Historial", "🧮 Calculadora de Ganancias"])

    # ---------- PESTAÑA 1: PICKS DE HOY ----------
    with tab1:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Partidos Escaneados", len(df_filtrado['PARTIDO'].unique()))
        k2.metric("Picks con Valor", len(df_filtrado[df_filtrado['EV+'] > 0]))
        max_ev = df_filtrado['EV+'].max()
        k3.metric("Mayor EV Detectado", f"+{round(max_ev, 2)}%" if max_ev > 0 else "0%")
        k4.metric("Estatus", "En Línea 🟢")

        st.markdown("### 📋 Radar de Mercado")

        def color_tabla(val):
            if '🔥' in str(val): return 'color: #00ffcc; font-weight: bold'
            elif '⚠️' in str(val): return 'color: #ffaa00; font-weight: bold'
            elif '❌' in str(val): return 'color: #ff4b4b; text-decoration: line-through;'
            elif isinstance(val, (int, float)) and val < 0: return 'color: #ff4b4b'
            return ''

        formato_columnas = {'CUOTA CASA': '{:.2f}', 'PROBABILIDAD': '{:.1f}%', 'CUOTA REAL': '{:.2f}', 'EV+': '{:.2f}%'}
        
        columnas_visibles = ['FECHA', 'LIGA', 'PARTIDO', 'MERCADO', 'CUOTA CASA', 'PROBABILIDAD', 'EV+', 'Recomendación']
        st.dataframe(df_filtrado[columnas_visibles].style.map(color_tabla, subset=['Recomendación', 'EV+']).format(formato_columnas), use_container_width=True)

        # Cajas Desplegables para leer el análisis
        st.markdown("### 🧠 Justificación Matemática y Táctica")
        st.write("Haz clic en cualquier pronóstico para leer el análisis de nuestro modelo:")
        
        for index, row in df_filtrado.iterrows():
            if row['EV+'] > 0:
                with st.expander(f"{row['Recomendación']} | {row['PARTIDO']} - {row['MERCADO']} (Cuota: {row['CUOTA CASA']})"):
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        st.metric("Probabilidad", f"{row['PROBABILIDAD']}%")
                        st.metric("Ventaja Casa", f"+{row['EV+']}%")
                    with col_b:
                        st.markdown("**Contexto del Partido:**")
                        st.info(row['ANALISIS'])

        # Gráfica de Barras Horizontales
        st.divider()
        st.markdown("### 📊 Top Mejores Apuestas")
        df_plot = df_filtrado.sort_values('EV+', ascending=True)
        fig = px.bar(df_plot, x='EV+', y='MERCADO', color='Recomendación', orientation='h', text='EV+',
                     color_discrete_map={'🔥 Stake Alto': '#00ffcc', '✅ Stake Medio': '#0088ff', '⚠️ Stake Bajo (Longshot)': '#ffaa00', '❌ No Apostar': '#ff4b4b'}, template="plotly_dark")
        fig.update_traces(texttemplate='+%{text:.2f}%', textposition='outside')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Valor Esperado (EV+)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    # ---------- PESTAÑA 2: HISTORIAL ----------
    with tab2:
        st.markdown("### 📈 Auditoría de Resultados")
        st.write("La transparencia es clave. Aquí se muestran los picks finalizados.")
        if 'ESTATUS' in df_picks.columns:
            df_resueltos = df_picks[df_picks['ESTATUS'].isin(['Ganada', 'Perdida', 'GANADA', 'PERDIDA'])]
            if not df_resueltos.empty:
                st.dataframe(df_resueltos[['FECHA', 'PARTIDO', 'MERCADO', 'CUOTA CASA', 'ESTATUS']], use_container_width=True)
            else:
                st.info("Aún no tienes partidos finalizados marcados como 'Ganada' o 'Perdida' en tu base de datos.")
        else:
            st.info("Asegúrate de llenar la columna 'ESTATUS' en tu Google Sheets.")

    # ---------- PESTAÑA 3: CALCULADORA ----------
    with tab3:
        st.markdown("### 🧮 Calculadora de Beneficios")
        st.write("Simula tus ganancias antes de meter la apuesta.")
        
        if not df_filtrado.empty:
            c1, c2 = st.columns(2)
            with c1:
                pick_seleccionado = st.selectbox("1. Selecciona tu apuesta:", df_filtrado['MERCADO'].tolist())
                inversion = st.number_input("2. Ingresa el monto a apostar ($ MXN):", min_value=10, value=100, step=50)
            
            with c2:
                cuota_calc = df_filtrado[df_filtrado['MERCADO'] == pick_seleccionado]['CUOTA CASA'].values[0]
                ganancia_neta = (inversion * cuota_calc) - inversion
                retorno_total = inversion * cuota_calc
                
                st.info(f"**Cuota Oficial:** {cuota_calc}")
                st.success(f"**Tu Ganancia Limpia:** ${ganancia_neta:.2f} MXN")
                st.metric("Retorno Total a tu cuenta", f"${retorno_total:.2f} MXN")

# --- FOOTER ---
st.divider()
st.markdown("**© 2026 Desarollsdo por Torvi Analytics**")