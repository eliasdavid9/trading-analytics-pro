"""
Aplicación Streamlit - Sistema de Análisis de Trading
Interfaz gráfica profesional para análisis de contratos de futuros
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Importar módulos propios
from src.ingestion import DataIngestion
from src.classifier import DayClassifier
from src.analytics import SessionAnalytics
from src.predictor import TradingPredictor
from src.visualizer import TradingVisualizer

# Configuración de la página
st.set_page_config(
    page_title="Trading Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
def load_css():
    """Carga estilos CSS personalizados - Dark Premium Theme"""
    st.markdown("""
    <style>
    /* ============================================
       VARIABLES DE COLOR - DARK PREMIUM THEME
       ============================================ */
    :root {
        --bg-dark: #0a0a0a;
        --bg-secondary: #141414;
        --bg-card: rgba(30, 30, 30, 0.6);
        --accent-purple: #8b5cf6;
        --accent-blue: #3b82f6;
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
        --border-color: rgba(255, 255, 255, 0.1);
    }
    
    /* ============================================
       FONDO PRINCIPAL CON DEGRADADO
       ============================================ */
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        background-attachment: fixed;
        padding: 2rem;
    }
    
    /* Efecto de grano sutil */
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E");
        opacity: 0.3;
        pointer-events: none;
        z-index: 0;
    }
    
    /* ============================================
       TIPOGRAFÍA MODERNA
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 3rem !important;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        font-size: 2rem !important;
        margin-top: 3rem !important;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border-color);
    }
    
    p, label, span {
        color: var(--text-secondary) !important;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* ============================================
       CARDS CON GLASSMORPHISM
       ============================================ */
    div[data-testid="stMetricValue"], 
    div[data-testid="metric-container"] {
        background: var(--bg-card) !important;
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(139, 92, 246, 0.3);
        border-color: var(--accent-purple);
    }
    
    div[data-testid="metric-container"] label {
        color: var(--text-secondary) !important;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 2.5rem !important;
        font-weight: 700;
    }
    
    /* ============================================
       BOTONES PREMIUM
       ============================================ */
    .stButton button {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.02em;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.6);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* ============================================
       SIDEBAR DARK
       ============================================ */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent;
    }
    
    /* ============================================
       FILE UPLOADER
       ============================================ */
    div[data-testid="stFileUploader"] {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 2px dashed var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--accent-purple);
        background: rgba(139, 92, 246, 0.05);
    }
    
    /* ============================================
       TABS MODERNOS
       ============================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        color: var(--text-secondary);
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(139, 92, 246, 0.1);
        border-color: var(--accent-purple);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%);
        border-color: transparent;
        color: white !important;
    }
    
    /* ============================================
       DATAFRAMES Y TABLAS
       ============================================ */
    .dataframe {
        background: var(--bg-card) !important;
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    .dataframe thead tr {
        background: rgba(139, 92, 246, 0.2) !important;
    }
    
    .dataframe thead th {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 1rem !important;
        border-bottom: 2px solid var(--accent-purple) !important;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid var(--border-color) !important;
        transition: all 0.2s ease;
    }
    
    .dataframe tbody tr:hover {
        background: rgba(139, 92, 246, 0.05) !important;
    }
    
    .dataframe td {
        color: var(--text-secondary) !important;
        padding: 0.875rem 1rem !important;
    }
    
    /* ============================================
       ALERTS Y NOTIFICACIONES
       ============================================ */
    .stSuccess, .stWarning, .stError, .stInfo {
        background: var(--bg-card) !important;
        backdrop-filter: blur(20px);
        border-radius: 12px !important;
        border-left: 4px solid;
        padding: 1rem 1.5rem !important;
    }
    
    .stSuccess {
        border-left-color: #10b981;
    }
    
    .stWarning {
        border-left-color: #f59e0b;
    }
    
    .stError {
        border-left-color: #ef4444;
    }
    
    .stInfo {
        border-left-color: var(--accent-blue);
    }
    
    /* ============================================
       INPUTS Y SELECTORES
       ============================================ */
    input, textarea, select {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease;
    }
    
    input:focus, textarea:focus, select:focus {
        border-color: var(--accent-purple) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* ============================================
       EXPANDERS
       ============================================ */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(139, 92, 246, 0.1) !important;
        border-color: var(--accent-purple) !important;
    }
    
    /* ============================================
       SCROLLBAR DARK
       ============================================ */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-purple);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-blue);
    }
    
    /* ============================================
       ANIMACIONES SUAVES
       ============================================ */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .main > div {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* ============================================
       PLOTLY CHARTS DARK
       ============================================ */
    .js-plotly-plot {
        background: var(--bg-card) !important;
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1rem;
    }
    
    </style>
    """, unsafe_allow_html=True)

# Inicializar session state
def init_session_state():
    """Inicializa variables de sesión"""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'classifier' not in st.session_state:
        st.session_state.classifier = None
    if 'analytics' not in st.session_state:
        st.session_state.analytics = None
    if 'predictor' not in st.session_state:
        st.session_state.predictor = None
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = None
    if 'archivo_nombre' not in st.session_state:
        st.session_state.archivo_nombre = None
    if 'procesado' not in st.session_state:
        st.session_state.procesado = False
    if 'tema' not in st.session_state:
        st.session_state.tema = 'claro'
    if 'comparador' not in st.session_state:
        st.session_state.comparador = None
    if 'comparacion_lista' not in st.session_state:
        st.session_state.comparacion_lista = False

def sidebar():
    """Renderiza el sidebar con controles"""
    with st.sidebar:
        st.markdown("# 📊 Trading Analytics")
        st.markdown("---")
        
        # Upload de archivo
        st.markdown("### 📁 Cargar Datos")
        uploaded_file = st.file_uploader(
            "Sube tu archivo .txt de NinjaTrader",
            type=['txt'],
            help="Archivo con datos OHLCV de 1 minuto"
        )
        
        if uploaded_file is not None:
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            st.session_state.archivo_nombre = uploaded_file.name
            
            # Botón para procesar
            if st.button("🚀 Analizar", type="primary", use_container_width=True):
                procesar_archivo(tmp_path)
        
        st.markdown("---")
        
        # Glosario
        with st.expander("📖 Glosario"):
            st.markdown("""
            **Rango Diario:** Diferencia entre High y Low del día
            
            **Clasificación:**
            - 🟢 **FUERTE:** Top 33% de movimiento
            - 🟡 **INTERMEDIO:** Medio 33%
            - 🔴 **LATERAL:** Bottom 33%
            
            **Volatilidad:** Desviación estándar de precios intradiarios
            
            **Outlier:** Día con volatilidad extrema (>2σ)
            
            **Correlación:** Medida de relación entre sesiones (-1 a +1)
            
            **Sesiones (Hora de Nueva York - ET):**
            - 🌏 **ASIA:** 7:00 PM - 4:00 AM ET
            - 🇪🇺 **EUROPA:** 3:00 AM - 12:00 PM ET
            - 🇺🇸 **NY:** 9:30 AM - 5:00 PM ET
            
            *Los horarios se ajustan automáticamente según DST*
            """)
        
        # Info
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #6b7280; font-size: 0.85em;'>
            <p><b>Trading Analytics Pro</b></p>
            <p>v1.0 - Sistema de análisis estadístico</p>
        </div>
        """, unsafe_allow_html=True)

def procesar_archivo(ruta_archivo):
    """Procesa el archivo cargado y ejecuta todo el pipeline"""
    
    with st.spinner("⏳ Procesando datos..."):
        # Paso 1: Ingestion
        try:
            parser = DataIngestion(ruta_archivo)
            df = parser.procesar(guardar=False, mostrar_resumen=False)
            
            if df is None:
                st.error("❌ Error al procesar el archivo")
                return
            
            st.session_state.df = df
            
        except Exception as e:
            st.error(f"❌ Error en ingestion: {str(e)}")
            return
    
    with st.spinner("📊 Clasificando días..."):
        # Paso 2: Clasificación
        try:
            classifier = DayClassifier(df)
            classifier.calcular_estadisticas_diarias()
            classifier.calcular_percentiles()
            classifier.clasificar_dias()
            
            st.session_state.classifier = classifier
            
        except Exception as e:
            st.error(f"❌ Error en clasificación: {str(e)}")
            return
    
    with st.spinner("🌏 Analizando sesiones..."):
        # Paso 3: Analytics
        try:
            analytics = SessionAnalytics(df, classifier.clasificaciones)
            analytics.calcular_estadisticas_por_sesion()
            analytics.analizar_distribucion_sesiones()
            analytics.identificar_sesion_dominante()
            analytics.detectar_correlacion_sesiones()
            analytics.analizar_sesiones_por_tipo_dia()
            
            st.session_state.analytics = analytics
            
        except Exception as e:
            st.error(f"❌ Error en analytics: {str(e)}")
            return
    
    with st.spinner("🎯 Generando predicciones..."):
        # Paso 4: Predictor
        try:
            predictor = TradingPredictor(df, classifier.clasificaciones, analytics.stats_sesiones)
            predictor.analizar_patrones_dia_semana()
            predictor.analizar_patron_sesion_previa()
            predictor.analizar_rachas()
            predictor.generar_reglas_probabilisticas()
            
            st.session_state.predictor = predictor
            
        except Exception as e:
            st.error(f"❌ Error en predictor: {str(e)}")
            return
    
    with st.spinner("📈 Creando visualizaciones..."):
        # Paso 5: Visualizaciones
        try:
            visualizer = TradingVisualizer(
                df,
                classifier.clasificaciones,
                analytics.stats_sesiones,
                st.session_state.archivo_nombre.replace('.txt', '')
            )
            
            st.session_state.visualizer = visualizer
            
        except Exception as e:
            st.warning(f"⚠️ No se pudieron crear visualizaciones: {str(e)}")
    
    st.session_state.procesado = True
    st.success("✅ Análisis completado exitosamente!")

def tab_overview():
    """Tab de resumen ejecutivo"""
    st.markdown("## 📊 Resumen Ejecutivo")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    classifier = st.session_state.classifier
    analytics = st.session_state.analytics
    df = st.session_state.df
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Días",
            f"{len(classifier.clasificaciones)}"
        )
    
    with col2:
        dias_fuertes = (classifier.clasificaciones['clasificacion'] == 'FUERTE').sum()
        pct_fuertes = (dias_fuertes / len(classifier.clasificaciones)) * 100
        st.metric(
            "Días Fuertes",
            f"{dias_fuertes}",
            f"{pct_fuertes:.1f}%"
        )
    
    with col3:
        rango_promedio = classifier.clasificaciones['rango_diario'].mean()
        st.metric(
            "Rango Promedio",
            f"{rango_promedio:.1f} pts"
        )
    
    with col4:
        outliers = classifier.clasificaciones['es_outlier'].sum()
        st.metric(
            "Días Outliers",
            f"{outliers}"
        )
    
    st.markdown("---")
    
    # Insights clave
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔑 Insights Clave")
        
        # Mejor día de semana
        analisis_semana = classifier.analizar_por_dia_semana()
        mejor_dia = analisis_semana['%_FUERTE'].idxmax()
        mejor_pct = analisis_semana.loc[mejor_dia, '%_FUERTE']
        
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        mejor_dia_esp = dias_esp.get(mejor_dia, mejor_dia)
        
        st.success(f"**Mejor día para trading:** {mejor_dia_esp} ({mejor_pct:.1f}% días fuertes)")
        
        # Sesión dominante
        dominantes = analytics.identificar_sesion_dominante()
        sesion_top = dominantes['sesion_dominante'].value_counts().idxmax()
        sesion_pct = (dominantes['sesion_dominante'].value_counts()[sesion_top] / len(dominantes) * 100)
        
        st.info(f"**Sesión dominante:** {sesion_top} ({sesion_pct:.1f}% de los días)")
        
        # Correlación más fuerte
        if analytics.correlaciones:
            max_corr = max(analytics.correlaciones.items(), key=lambda x: abs(x[1]))
            st.warning(f"**Correlación más fuerte:** {max_corr[0]} = {max_corr[1]:+.3f}")
    
    with col2:
        st.markdown("### 📈 Distribución de Días")
        
        # Gráfico de pie
        conteo = classifier.clasificaciones['clasificacion'].value_counts()
        
        fig_data = {
            'Clasificación': conteo.index.tolist(),
            'Cantidad': conteo.values.tolist()
        }
        
        st.bar_chart(conteo)
    
    st.markdown("---")
    
    # Top 5 días más fuertes
    st.markdown("### 🏆 Top 5 Días Más Fuertes")
    
    top5 = classifier.clasificaciones.nlargest(5, 'rango_diario')[
        ['rango_diario', 'cambio_pct', 'direccion', 'volatilidad']
    ]
    
    st.dataframe(
        top5.style.format({
            'rango_diario': '{:.2f}',
            'cambio_pct': '{:+.2f}%',
            'volatilidad': '{:.2f}'
        }),
        use_container_width=True
    )

def tab_clasificacion():
    """Tab de clasificación de días"""
    st.markdown("## 📅 Clasificación de Días")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    classifier = st.session_state.classifier
    
    # Mostrar tabla completa
    st.markdown("### 📋 Tabla Completa de Clasificaciones")
    
    df_display = classifier.clasificaciones[[
        'dia_semana', 'clasificacion', 'rango_diario', 
        'cambio_pct', 'direccion', 'volatilidad', 'es_outlier'
    ]].copy()
    
    # Aplicar formato
    st.dataframe(
        df_display.style.format({
            'rango_diario': '{:.2f}',
            'cambio_pct': '{:+.2f}%',
            'volatilidad': '{:.2f}'
        }).background_gradient(subset=['rango_diario'], cmap='RdYlGn'),
        use_container_width=True,
        height=400
    )
    
    # Análisis por día de semana
    st.markdown("### 📊 Análisis por Día de Semana")
    
    analisis_semana = classifier.analizar_por_dia_semana()
    st.dataframe(analisis_semana, use_container_width=True)
    
    # Rachas detectadas
    st.markdown("### 🔁 Rachas Detectadas (3+ días consecutivos)")
    
    rachas = classifier.detectar_rachas()
    
    if len(rachas) > 0:
        st.dataframe(rachas, use_container_width=True)
    else:
        st.info("No se detectaron rachas significativas")

def tab_sesiones():
    """Tab de análisis de sesiones"""
    st.markdown("## 🌏 Análisis de Sesiones")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    analytics = st.session_state.analytics
    
    # Distribución de sesiones
    st.markdown("### 📊 Distribución de Rangos por Sesión")
    
    dist = analytics.analizar_distribucion_sesiones()
    st.dataframe(dist, use_container_width=True)
    
    # Sesiones por tipo de día
    st.markdown("### 🎯 Sesiones por Tipo de Día")
    
    por_tipo = analytics.analizar_sesiones_por_tipo_dia()
    if por_tipo is not None:
        st.dataframe(por_tipo, use_container_width=True)
    
    # Correlaciones
    st.markdown("### 🔗 Correlaciones entre Sesiones")
    
    col1, col2, col3 = st.columns(3)
    
    if analytics.correlaciones:
        for i, (clave, valor) in enumerate(analytics.correlaciones.items()):
            col = [col1, col2, col3][i % 3]
            with col:
                delta_color = "normal" if abs(valor) < 0.5 else "inverse"
                st.metric(
                    clave,
                    f"{valor:+.3f}",
                    delta_color=delta_color
                )

def tab_predictor():
    """Tab de predicciones"""
    st.markdown("## 🎯 Motor Predictivo")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    predictor = st.session_state.predictor
    
    # Mostrar reglas
    st.markdown("### 📋 Reglas Probabilísticas")
    
    if predictor.reglas_probabilisticas:
        for regla in predictor.reglas_probabilisticas:
            with st.expander(f"**{regla['tipo']}** | {regla['condicion']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Predicción:** {regla['prediccion']}")
                    st.markdown(f"**Táctica:** {regla['tactica']}")
                
                with col2:
                    st.metric("Probabilidad", f"{regla['probabilidad']:.1f}%")
                    st.metric("Confianza", regla['confianza'])
    else:
        st.warning("No se generaron reglas probabilísticas")

def tab_visualizaciones():
    """Tab de visualizaciones interactivas"""
    st.markdown("## 📈 Visualizaciones Interactivas")
    
    if not st.session_state.procesado:
        st.info("👈 Sube un archivo en el sidebar para comenzar")
        return
    
    visualizer = st.session_state.visualizer
    
    # Crear todas las figuras
    st.markdown("### 🔥 Heatmap Día-Sesión")
    fig1 = visualizer.crear_heatmap_semana_sesion()
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 Distribución de Rangos")
    fig2 = visualizer.crear_distribucion_rangos()
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📉 Timeline de Clasificaciones")
    fig3 = visualizer.crear_timeline_clasificaciones()
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Correlación entre Sesiones")
    fig4 = visualizer.crear_correlacion_sesiones()
    st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 Clasificaciones por Día")
    fig5 = visualizer.crear_barras_clasificacion_dia()
    st.plotly_chart(fig5, use_container_width=True)

def tab_comparacion():
    """Tab de comparación multi-contrato"""
    st.markdown("## 🔀 Comparación de Contratos")
    
    st.info("👈 Sube dos archivos .txt en el sidebar para comparar contratos")
    
    # Upload de segundo archivo
    st.markdown("### 📁 Cargar Segundo Contrato")
    
    uploaded_file_2 = st.file_uploader(
        "Sube el segundo archivo .txt para comparar",
        type=['txt'],
        key='file_2',
        help="Archivo con datos OHLCV de 1 minuto del segundo contrato"
    )
    
    if uploaded_file_2 is not None and st.session_state.procesado:
        if st.button("🔀 Comparar Contratos", type="primary", use_container_width=True):
            
            # Guardar archivo temporalmente
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                tmp_file.write(uploaded_file_2.getvalue())
                tmp_path_2 = tmp_file.name
            
            with st.spinner("⏳ Procesando segundo contrato..."):
                # Procesar segundo archivo
                try:
                    from src.ingestion import DataIngestion
                    from src.classifier import DayClassifier
                    
                    parser_2 = DataIngestion(tmp_path_2)
                    df_2 = parser_2.procesar(guardar=False, mostrar_resumen=False)
                    
                    if df_2 is None:
                        st.error("❌ Error al procesar segundo archivo")
                        return
                    
                    # Clasificar segundo contrato
                    classifier_2 = DayClassifier(df_2)
                    classifier_2.calcular_estadisticas_diarias()
                    classifier_2.calcular_percentiles()
                    classifier_2.clasificar_dias()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
            
            with st.spinner("📊 Generando comparación..."):
                try:
                    from src.multi_contract import MultiContractComparison
                    
                    # Preparar datos
                    contratos_data = {
                        st.session_state.archivo_nombre.replace('.txt', ''): {
                            'df': st.session_state.df,
                            'clasificaciones': st.session_state.classifier.clasificaciones
                        },
                        uploaded_file_2.name.replace('.txt', ''): {
                            'df': df_2,
                            'clasificaciones': classifier_2.clasificaciones
                        }
                    }
                    
                    # Crear comparador
                    comparador = MultiContractComparison(contratos_data)
                    comparador.calcular_metricas_comparativas()
                    comparador.calcular_ratios()
                    
                    # Guardar en session state
                    st.session_state.comparador = comparador
                    st.session_state.comparacion_lista = True
                    
                    st.success("✅ Comparación completada!")
                    
                except Exception as e:
                    st.error(f"❌ Error en comparación: {str(e)}")
                    return
    
    # Mostrar resultados si hay comparación
    if hasattr(st.session_state, 'comparacion_lista') and st.session_state.comparacion_lista:
        comparador = st.session_state.comparador
        
        st.markdown("---")
        
        # Métricas comparativas
        st.markdown("### 📊 Métricas Comparativas")
        
        comparacion_df = comparador.comparacion
        
        # Formatear para display
        display_df = comparacion_df[[
            'total_dias', 'rango_promedio', 'pct_dias_fuertes', 
            'volatilidad_promedio', 'volumen_promedio', 'outliers'
        ]].copy()
        
        display_df.columns = [
            'Días', 'Rango Prom.', '% Fuertes', 
            'Volatilidad', 'Volumen Prom.', 'Outliers'
        ]
        
        st.dataframe(
            display_df.style.format({
                'Rango Prom.': '{:.1f}',
                '% Fuertes': '{:.1f}%',
                'Volatilidad': '{:.2f}',
                'Volumen Prom.': '{:,.0f}'
            }).background_gradient(subset=['Rango Prom.'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Ratios y recomendaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Ratios")
            
            if comparador.ratios:
                st.info(f"**Volatilidad:** {comparador.ratios['volatilidad']['interpretacion']}")
                st.info(f"**Volumen:** {comparador.ratios['volumen']['interpretacion']}")
                
                dif_fuertes = comparador.ratios['dias_fuertes']['diferencia']
                st.info(f"**Diferencia días fuertes:** {dif_fuertes:.1f} puntos porcentuales")
        
        with col2:
            st.markdown("### 🎯 Recomendaciones")
            
            mas_volatil = comparacion_df['rango_promedio'].idxmax()
            mas_consistente = comparacion_df['outliers'].idxmin()
            mayor_volumen = comparacion_df['volumen_promedio'].idxmax()
            
            st.success(f"**Mayor movimiento:** {mas_volatil}")
            st.warning(f"**Más consistente:** {mas_consistente}")
            st.info(f"**Mejor liquidez:** {mayor_volumen}")
        
        st.markdown("---")
        
        # Gráficos
        st.markdown("### 📊 Gráficos Comparativos")
        
        # Gráfico comparativo
        fig1 = comparador.crear_grafico_comparativo()
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("---")
        
        # Overlay temporal
        st.markdown("### 📉 Evolución Temporal")
        
        fig2 = comparador.crear_grafico_overlay()
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        
        # Correlación
        correlacion = comparador.calcular_correlacion_temporal()
        if correlacion:
            st.metric(
                "Correlación Temporal",
                f"{correlacion:+.3f}",
                help="Mide qué tan similares se mueven los contratos (-1 a +1)"
            )
            
            if abs(correlacion) > 0.7:
                st.success("✓ Los contratos se mueven de forma muy similar")
            elif abs(correlacion) > 0.4:
                st.warning("~ Los contratos tienen correlación moderada")
            else:
                st.info("○ Los contratos se mueven de forma independiente")


def main():
    """Función principal"""
    
    # Cargar CSS
    load_css()
    
    # Inicializar estado
    init_session_state()
    
    # Sidebar
    sidebar()
    
    # Header principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3em; margin: 0;'>📊 Trading Analytics Pro</h1>
        <p style='font-size: 1.2em; color: #6b7280;'>Sistema profesional de análisis estadístico para futuros</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "📅 Clasificación",
        "🌏 Sesiones",
        "🎯 Predictor",
        "📈 Visualizaciones",
        "🔀 Comparar"
    ])
    
    with tab1:
        tab_overview()
    
    with tab2:
        tab_clasificacion()
    
    with tab3:
        tab_sesiones()
    
    with tab4:
        tab_predictor()
    
    with tab5:
        tab_visualizaciones()
    
    with tab6:
        tab_comparacion()

if __name__ == "__main__":
    main()
