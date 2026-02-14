"""
Módulo de comparación mensual
Analiza evolución temporal y detecta patrones estacionales
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Importar Plotly para visualizaciones
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import OUTPUTS_DIR


class MonthlyComparison:
    """
    Comparador mensual de estadísticas de trading
    """
    
    def __init__(self, df, clasificaciones):
        """
        Inicializa el comparador mensual
        
        Args:
            df: DataFrame con datos procesados
            clasificaciones: DataFrame con clasificaciones de días
        """
        self.df = df
        self.clasificaciones = clasificaciones
        self.stats_mensuales = None
        self.comparacion = None
        
    def calcular_estadisticas_mensuales(self):
        """
        Calcula estadísticas agregadas por mes
        
        Returns:
            DataFrame con stats mensuales
        """
        # Agregar año-mes para agrupar
        self.clasificaciones['año_mes'] = pd.to_datetime(
            self.clasificaciones.index
        ).to_period('M')
        
        # Agrupar por mes
        stats = self.clasificaciones.groupby('año_mes').agg({
            'rango_diario': ['mean', 'std', 'min', 'max', 'count'],
            'volatilidad': 'mean',
            'clasificacion': lambda x: (x == 'FUERTE').sum(),
            'es_outlier': 'sum'
        })
        
        # Renombrar columnas
        stats.columns = [
            'rango_promedio', 'rango_std', 'rango_min', 'rango_max', 'num_dias',
            'volatilidad_promedio', 'dias_fuertes', 'outliers'
        ]
        
        # Calcular porcentajes
        stats['pct_dias_fuertes'] = (stats['dias_fuertes'] / stats['num_dias']) * 100
        stats['pct_outliers'] = (stats['outliers'] / stats['num_dias']) * 100
        
        # Agregar nombre del mes en español
        meses_es = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        stats['mes_nombre'] = stats.index.map(lambda x: meses_es[x.month])
        stats['año'] = stats.index.map(lambda x: x.year)
        
        self.stats_mensuales = stats
        
        print(f"✓ Calculadas estadísticas para {len(stats)} meses")
        return stats
    
    def generar_comparacion(self):
        """
        Genera comparación detallada entre meses
        
        Returns:
            DataFrame con comparación
        """
        if self.stats_mensuales is None:
            self.calcular_estadisticas_mensuales()
        
        # Crear tabla comparativa
        comparacion = self.stats_mensuales[[
            'año', 'mes_nombre', 'num_dias', 'rango_promedio', 
            'dias_fuertes', 'pct_dias_fuertes', 'volatilidad_promedio', 'outliers'
        ]].copy()
        
        # Calcular ranking
        comparacion['ranking_volatilidad'] = comparacion['rango_promedio'].rank(ascending=False).astype(int)
        
        # Ordenar por fecha
        comparacion = comparacion.sort_index()
        
        self.comparacion = comparacion
        return comparacion
    
    def detectar_tendencias(self):
        """
        Detecta tendencias en la evolución temporal
        
        Returns:
            dict con análisis de tendencias
        """
        if self.stats_mensuales is None:
            self.calcular_estadisticas_mensuales()
        
        tendencias = {}
        
        # Tendencia de volatilidad
        meses_ordenados = self.stats_mensuales.sort_index()
        rangos = meses_ordenados['rango_promedio'].values
        
        if len(rangos) >= 2:
            # Calcular pendiente (regresión lineal simple)
            x = np.arange(len(rangos))
            slope = np.polyfit(x, rangos, 1)[0]
            
            if slope > 10:
                tendencias['volatilidad'] = {
                    'direccion': 'CRECIENTE',
                    'magnitud': slope,
                    'descripcion': f'La volatilidad aumenta ~{slope:.1f} puntos por mes'
                }
            elif slope < -10:
                tendencias['volatilidad'] = {
                    'direccion': 'DECRECIENTE',
                    'magnitud': abs(slope),
                    'descripcion': f'La volatilidad disminuye ~{abs(slope):.1f} puntos por mes'
                }
            else:
                tendencias['volatilidad'] = {
                    'direccion': 'ESTABLE',
                    'magnitud': abs(slope),
                    'descripcion': 'La volatilidad se mantiene relativamente estable'
                }
        
        # Detectar mes más volátil
        mes_max = meses_ordenados['rango_promedio'].idxmax()
        mes_max_valor = meses_ordenados.loc[mes_max, 'rango_promedio']
        mes_max_nombre = meses_ordenados.loc[mes_max, 'mes_nombre']
        
        tendencias['mes_mas_volatil'] = {
            'periodo': str(mes_max),
            'nombre': mes_max_nombre,
            'rango_promedio': mes_max_valor
        }
        
        # Detectar mes más lateral
        mes_min = meses_ordenados['rango_promedio'].idxmin()
        mes_min_valor = meses_ordenados.loc[mes_min, 'rango_promedio']
        mes_min_nombre = meses_ordenados.loc[mes_min, 'mes_nombre']
        
        tendencias['mes_mas_lateral'] = {
            'periodo': str(mes_min),
            'nombre': mes_min_nombre,
            'rango_promedio': mes_min_valor
        }
        
        # Variabilidad entre meses
        cv = (meses_ordenados['rango_promedio'].std() / meses_ordenados['rango_promedio'].mean()) * 100
        
        tendencias['variabilidad'] = {
            'coeficiente_variacion': cv,
            'interpretacion': 'ALTA' if cv > 30 else ('MODERADA' if cv > 15 else 'BAJA'),
            'descripcion': f'Los meses varían {cv:.1f}% en promedio'
        }
        
        return tendencias
    
    def crear_grafico_evolucion(self):
        """
        Crea gráfico de evolución mensual
        
        Returns:
            plotly.graph_objects.Figure
        """
        if not PLOTLY_AVAILABLE:
            print("⚠ Plotly no disponible para crear gráficos")
            return None
        
        if self.stats_mensuales is None:
            self.calcular_estadisticas_mensuales()
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Evolución del Rango Promedio Mensual', 
                          'Porcentaje de Días Fuertes por Mes'),
            vertical_spacing=0.12,
            row_heights=[0.6, 0.4]
        )
        
        # Preparar datos
        stats_sorted = self.stats_mensuales.sort_index()
        x_labels = [f"{row['mes_nombre']}\n{row['año']}" 
                   for idx, row in stats_sorted.iterrows()]
        
        # Gráfico 1: Rango promedio con barras de error
        fig.add_trace(
            go.Scatter(
                x=x_labels,
                y=stats_sorted['rango_promedio'],
                mode='lines+markers',
                name='Rango Promedio',
                line=dict(color='#667eea', width=3),
                marker=dict(size=10, color='#667eea'),
                error_y=dict(
                    type='data',
                    array=stats_sorted['rango_std'],
                    visible=True,
                    color='rgba(102, 126, 234, 0.3)'
                ),
                hovertemplate='<b>%{x}</b><br>Rango: %{y:.1f} ± %{error_y.array:.1f} pts<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Agregar línea de tendencia
        x_numeric = np.arange(len(stats_sorted))
        z = np.polyfit(x_numeric, stats_sorted['rango_promedio'], 1)
        p = np.poly1d(z)
        
        fig.add_trace(
            go.Scatter(
                x=x_labels,
                y=p(x_numeric),
                mode='lines',
                name='Tendencia',
                line=dict(dash='dash', color='red', width=2),
                hoverinfo='skip'
            ),
            row=1, col=1
        )
        
        # Gráfico 2: Porcentaje días fuertes
        colors = ['#10b981' if pct >= 40 else ('#f59e0b' if pct >= 25 else '#ef4444') 
                 for pct in stats_sorted['pct_dias_fuertes']]
        
        fig.add_trace(
            go.Bar(
                x=x_labels,
                y=stats_sorted['pct_dias_fuertes'],
                name='% Días Fuertes',
                marker_color=colors,
                hovertemplate='<b>%{x}</b><br>Días fuertes: %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Línea de referencia (33% - equilibrio)
        fig.add_hline(
            y=33.33,
            line_dash="dot",
            line_color="gray",
            annotation_text="Equilibrio (33%)",
            annotation_position="right",
            row=2, col=1
        )
        
        # Layout
        fig.update_xaxes(title_text="Mes", row=2, col=1)
        fig.update_yaxes(title_text="Rango Promedio (puntos)", row=1, col=1)
        fig.update_yaxes(title_text="% Días Fuertes", row=2, col=1)
        
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12)
        )
        
        return fig
    
    def generar_reporte_mensual(self):
        """
        Genera reporte completo de comparación mensual
        
        Returns:
            str: reporte formateado
        """
        if self.comparacion is None:
            self.generar_comparacion()
        
        tendencias = self.detectar_tendencias()
        
        reporte = []
        reporte.append("=" * 70)
        reporte.append("ANÁLISIS DE COMPARACIÓN MENSUAL")
        reporte.append("=" * 70)
        reporte.append("")
        
        # 1. Tabla comparativa
        reporte.append("COMPARACIÓN POR MES")
        reporte.append("-" * 70)
        reporte.append("")
        
        for idx, row in self.comparacion.iterrows():
            reporte.append(f"{row['mes_nombre']} {row['año']}")
            reporte.append(f"  Días analizados: {row['num_dias']}")
            reporte.append(f"  Rango promedio: {row['rango_promedio']:.1f} puntos")
            reporte.append(f"  Días fuertes: {row['dias_fuertes']} ({row['pct_dias_fuertes']:.1f}%)")
            reporte.append(f"  Volatilidad: {row['volatilidad_promedio']:.2f}")
            reporte.append(f"  Ranking: #{row['ranking_volatilidad']} en volatilidad")
            if row['outliers'] > 0:
                reporte.append(f"  ⚠ Outliers: {row['outliers']}")
            reporte.append("")
        
        # 2. Tendencias detectadas
        reporte.append("TENDENCIAS DETECTADAS")
        reporte.append("-" * 70)
        
        # Volatilidad
        vol_trend = tendencias['volatilidad']
        reporte.append(f"• Tendencia de volatilidad: {vol_trend['direccion']}")
        reporte.append(f"  {vol_trend['descripcion']}")
        reporte.append("")
        
        # Mes más volátil
        mes_max = tendencias['mes_mas_volatil']
        reporte.append(f"• Mes más volátil: {mes_max['nombre']} ({mes_max['rango_promedio']:.1f} pts promedio)")
        
        # Mes más lateral
        mes_min = tendencias['mes_mas_lateral']
        reporte.append(f"• Mes más lateral: {mes_min['nombre']} ({mes_min['rango_promedio']:.1f} pts promedio)")
        reporte.append("")
        
        # Variabilidad
        variab = tendencias['variabilidad']
        reporte.append(f"• Variabilidad entre meses: {variab['interpretacion']}")
        reporte.append(f"  {variab['descripcion']}")
        
        reporte.append("")
        reporte.append("=" * 70)
        
        return "\n".join(reporte)
    
    def exportar_comparacion(self, nombre_archivo="comparacion_mensual.txt"):
        """
        Exporta comparación a archivo
        
        Args:
            nombre_archivo: nombre del archivo de salida
        """
        if self.comparacion is None:
            self.generar_comparacion()
        
        ruta = OUTPUTS_DIR / nombre_archivo
        
        # Generar reporte
        reporte = self.generar_reporte_mensual()
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"✓ Comparación mensual exportada a: {ruta}")
        
        # También exportar CSV
        ruta_csv = OUTPUTS_DIR / nombre_archivo.replace('.txt', '.csv')
        self.comparacion.to_csv(ruta_csv)
        print(f"✓ Versión CSV guardada en: {ruta_csv}")


# ==============================================
# FUNCIÓN HELPER
# ==============================================

def analizar_evolucion_mensual(df, clasificaciones, exportar=True, mostrar_grafico=True):
    """
    Ejecuta análisis completo de evolución mensual
    
    Args:
        df: DataFrame con datos procesados
        clasificaciones: DataFrame con clasificaciones
        exportar: si exportar resultados
        mostrar_grafico: si generar gráfico interactivo
        
    Returns:
        MonthlyComparison con análisis completo
    """
    comparador = MonthlyComparison(df, clasificaciones)
    
    # Ejecutar análisis
    comparador.calcular_estadisticas_mensuales()
    comparador.generar_comparacion()
    
    # Mostrar reporte
    print("\n" + comparador.generar_reporte_mensual())
    
    # Exportar
    if exportar:
        comparador.exportar_comparacion()
    
    # Generar gráfico
    if mostrar_grafico and PLOTLY_AVAILABLE:
        fig = comparador.crear_grafico_evolucion()
        if fig:
            # Guardar gráfico
            ruta_html = OUTPUTS_DIR / "evolucion_mensual.html"
            fig.write_html(str(ruta_html))
            print(f"✓ Gráfico de evolución guardado en: {ruta_html}")
    
    return comparador


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el comparador mensual
    """
    from src.ingestion import cargar_datos_procesados
    from src.classifier import DayClassifier
    
    # Cargar datos
    df = cargar_datos_procesados("MNQ 03-26.Last_processed.parquet")
    
    if df is not None:
        # Clasificar días
        classifier = DayClassifier(df)
        classifier.calcular_estadisticas_diarias()
        classifier.clasificar_dias()
        
        # Análisis mensual
        comparador = analizar_evolucion_mensual(
            df,
            classifier.clasificaciones,
            exportar=True,
            mostrar_grafico=True
        )
        
        print("\n✓ Análisis mensual completado")
