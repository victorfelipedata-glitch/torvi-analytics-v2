# Importo las librerías que necesito para mi dashboard
import streamlit as st
import pandas as pd
import plotly.express as px

# Configuro mi página para que use todo el ancho de la pantalla y abro la barra lateral por defecto
st.set_page_config(page_title="GALACTIC BET ANALYTICS", layout="wide", initial_sidebar_state="expanded")

# Inyecto mi CSS personalizado para ocultar los botones por defecto y darle mi estilo futurista
st.markdown("""
    <style>
    /* 🚫 Oculto el menú de Streamlit, el enlace a GitHub y el header/footer por defecto 🚫 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    /* --------------------------------------------------------- */

    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Configuro mi fondo azul ultra oscuro */
    .main { background-color: #050814; }
    
    /* Diseño de mi título Neón Brillante */
    .titulo-futurista {
        font-family: 'Orbitron', sans-serif;
        color: #00f2ff;
        text-shadow: 0 0 5px #00f2ff, 0 0 15px #00f2ff, 0 0 30px #008cff;
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 10px;
        letter-spacing: 2px;
    }
    
    /* Diseño de mi subtítulo */
    .subtitulo {
        color: #b3cce6;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2rem;
        text-align: center;
        letter-spacing: 4px;
        margin-bottom: 40px;
    }
    
    /* Le doy un efecto de brillo y elevación a mis tarjetas de métricas cuando paso el mouse */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #0a1128, #000000);
        border: 1px solid #00f2ff;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 25px rgba(0, 242, 255, 0.6);
    }
    
    /* Diseño de mis divisores estilo láser */
    hr { 
        border: 0; 
        height: 2px; 
        background: linear-gradient(90deg, transparent, #00f2ff, #bc13fe, transparent); 
        margin: 30px 0; 
        box-shadow: 0 0 10px #00f2ff;
    }
    </style>
    """, unsafe_allow_html=True)

# Imprimo mis títulos en la pantalla principal
st.markdown('<p class="titulo-futurista">GALACTIC BET</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">SISTEMA DE ANÁLISIS EV+ AVANZADO</p>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ==========================================
# 🔐 MI SISTEMA DE SEGURIDAD (MURO DE ACCESO)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; font-family: Orbitron; color: #bc13fe;'>🔐 ACCESO VIP</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Pido la clave en mi barra lateral
mi_clave = st.sidebar.text_input("🔑 Ingresa la clave de acceso:", type="password")

# Verifico si la clave es correcta antes de mostrar mi trabajo
if mi_clave != "Galacticos2026": # <-- Aquí puedo cambiar mi contraseña cuando quiera
    st.warning("⚠️ Acceso Restringido. Ingresa la clave secreta en la consola lateral para ver mis picks.")
    st.stop() # Detengo la ejecución del código aquí si no tienen mi clave

# ==========================================
# 🚀 MI CÓDIGO PRINCIPAL (Solo visible con clave)
# ==========================================

# Conecto mi base de datos de Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/12lDBRn6nXm4yvzjHhqL6w2FbCw8FPS1dYt5BoZYuP4w/export?format=csv"

try:
    # Descargo mis datos a un DataFrame
    df = pd.read_csv(sheet_url)
    
    # Limpio el símbolo % de mi columna EV+ para que mis gráficas no fallen
    if 'EV+' in df.columns and df['EV+'].dtype == 'object':
        df['EV+'] = df['EV+'].str.replace('%', '').astype(float)

    # Agrego mi buscador a la consola lateral
    st.sidebar.markdown("<br><h2 style='text-align: center; font-family: Orbitron; color: #00f2ff;'>📟 CONSOLA</h2>", unsafe_allow_html=True)
    mi_filtro = st.sidebar.text_input("🔍 Buscar Equipo o Partido:")
    
    # Filtro mi tabla si escribo algo en el buscador
    if mi_filtro:
        df = df[df['PARTIDO'].str.contains(mi_filtro, case=False, na=False) | df['MERCADO'].str.contains(mi_filtro, case=False, na=False)]

    # Creo mis tarjetas de métricas principales (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        val_max = df['EV+'].max() if not df.empty and 'EV+' in df.columns else 0
        st.metric("🔥 MÁXIMO EV+", f"{val_max}%")
    with col2:
        st.metric("🎯 PICKS ACTIVOS", len(df))
    with col3:
        st.metric("⚡ SISTEMA", "EN LÍNEA")
    with col4:
        st.metric("🛡️ FIABILIDAD", "ALTA")

    st.markdown("<br>", unsafe_allow_html=True)

    # Construyo mi gráfica horizontal para escanear el valor de los mercados
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>📊 ESCÁNER DE VALOR (EV+)</h3>", unsafe_allow_html=True)
    if not df.empty and 'MERCADO' in df.columns and 'EV+' in df.columns:
        fig = px.bar(df, x='EV+', y='MERCADO', 
                     orientation='h',
                     color='EV+',
                     text='EV+',
                     color_continuous_scale="PuBuGn",
                     template="plotly_dark")
        
        # Saco el porcentaje afuera de la barra para que se lea mejor
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Orbitron", color="#00f2ff"),
            xaxis_title="Valor Esperado (EV+ %)",
            yaxis_title="",
            showlegend=False,
            height=400 # Limito la altura para que no se deforme
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tengo datos para graficar con ese filtro.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Creo mis tarjetas expansibles para el desglose táctico
    st.markdown("<h3 style='color: #00f2ff; font-family: Orbitron;'>🧠 DESGLOSE TÁCTICO DE MIS PICKS</h3>", unsafe_allow_html=True)
    
    if not df.empty:
        # Recorro cada fila de mis datos para armar las tarjetas
        for index, row in df.iterrows():
            partido = row.get('PARTIDO', 'Desconocido')
            mercado = row.get('MERCADO', 'N/A')
            cuota = row.get('CUOTA CASA', 'N/A')
            ev = row.get('EV+', 0)
            analisis = row.get('ANALISIS', 'Sin análisis registrado aún.')
            estatus = str(row.get('ESTATUS', ''))
            
            # Pongo un icono diferente dependiendo de si es Stal o no
            icon = "🟢" if "Stal" in estatus else "🔥"
            
            # Armo el cuadro desplegable
            with st.expander(f"{icon} {partido}  |  MERCADO: {mercado}  |  CUOTA: {cuota}  |  EV+: {ev}%"):
                st.markdown(f"""
                <div style='background-color: #0a1128; padding: 20px; border-left: 4px solid #00f2ff; border-radius: 0 10px 10px 0;'>
                    <h4 style='color: #bc13fe; margin-top: 0;'>📝 Análisis de mi Algoritmo:</h4>
                    <p style='color: #ffffff; font-size: 1.1rem; line-height: 1.6;'>{analisis}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No tengo picks en el radar en este momento.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Preparo mi botón para descargar la base de datos en CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ DESCARGAR MI BASE DE DATOS DE PICKS (CSV)",
        data=csv,
        file_name='galactic_picks.csv',
        mime='text/csv',
    )

except Exception as e:
    # Si algo falla con el Excel, muestro el error aquí
    st.error(f"Error crítico en mi sistema central: {e}")

# Pongo mi firma en el pie de página
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00f2ff; font-family: Orbitron, sans-serif; opacity: 0.8;'>© 2026 GALACTIC ANALYTICS | Desarrollado por Torvi Analytics</p>", unsafe_allow_html=True)







