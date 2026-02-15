"""
Módulo de comparación multi-contrato
Compara estadísticas entre dos o más contratos de futuros
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

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

```python
# Configurar tema dark
if PLOTLY_AVAILABLE:
    import plotly.io as pio
    pio.templates.default = "plotly_dark"
```

class MultiContractComparison:
    """
    Comparador de múltiples contratos
    """
    
    def __init__(self, contratos_data):
        """
        Inicializa el comparador multi-contrato
        
        Args:
            contratos_data: dict con formato {
                'nombre_contrato': {
                    'df': DataFrame con datos,
                    'clasificaciones': DataFrame con clasificaciones
                }
            }
        """
        self.contratos = contratos_data
        self.comparacion = None
        self.ratios = None
        
    def calcular_metricas_comparativas(self):
        """
        Calcula métricas para cada contrato
        
        Returns:
            DataFrame con métricas comparativas
        """
        metricas = []
        
        for nombre, data in self.contratos.items():
            clasificaciones = data['clasificaciones']
            df = data['df']
            
            # Calcular métricas principales
            total_dias = len(clasificaciones)
            dias_fuertes = (clasificaciones['clasificacion'] == 'FUERTE').sum()
            dias_laterales = (clasificaciones['clasificacion'] == 'LATERAL').sum()
            
            rango_promedio = clasificaciones['rango_diario'].mean()
            rango_max = clasificaciones['rango_diario'].max()
            rango_min = clasificaciones['rango_diario'].min()
            volatilidad_promedio = clasificaciones['volatilidad'].mean()
            
            outliers = clasificaciones['es_outlier'].sum()
            
            # Volumen promedio diario
            volumen_promedio = df.groupby('fecha')['volume'].sum().mean()
            
            # Métricas de sesiones
            sesiones_stats = df.groupby('sesion')['rango'].sum().to_dict()
            
            metricas.append({
                'contrato': nombre,
                'total_dias': total_dias,
                'dias_fuertes': dias_fuertes,
                'pct_dias_fuertes': (dias_fuertes / total_dias) * 100,
                'dias_laterales': dias_laterales,
                'pct_dias_laterales': (dias_laterales / total_dias) * 100,
                'rango_promedio': rango_promedio,
                'rango_max': rango_max,
                'rango_min': rango_min,
                'volatilidad_promedio': volatilidad_promedio,
                'outliers': outliers,
                'volumen_promedio': volumen_promedio,
                'rango_asia': sesiones_stats.get('ASIA', 0) / total_dias,
                'rango_europa': sesiones_stats.get('EUROPA', 0) / total_dias,
                'rango_ny': sesiones_stats.get('NY', 0) / total_dias
            })
        
        self.comparacion = pd.DataFrame(metricas).set_index('contrato')
        
        print(f"✓ Métricas calculadas para {len(self.contratos)} contratos")
        return self.comparacion
    
    def calcular_ratios(self):
        """
        Calcula ratios entre contratos (para contratos relacionados como MNQ/NQ)
        
        Returns:
            dict con ratios calculados
        """
        if self.comparacion is None:
            self.calcular_metricas_comparativas()
        
        if len(self.contratos) != 2:
            print("⚠ Los ratios solo se calculan para 2 contratos")
            return None
        
        nombres = list(self.comparacion.index)
        contrato_1 = nombres[0]
        contrato_2 = nombres[1]
        
        ratios = {}
        
        # Ratio de volatilidad
        ratio_volatilidad = (
            self.comparacion.loc[contrato_1, 'rango_promedio'] / 
            self.comparacion.loc[contrato_2, 'rango_promedio']
        )
        
        ratios['volatilidad'] = {
            'ratio': ratio_volatilidad,
            'interpretacion': f"{contrato_1} es {ratio_volatilidad:.2f}x más volátil que {contrato_2}" 
                            if ratio_volatilidad > 1 
                            else f"{contrato_2} es {1/ratio_volatilidad:.2f}x más volátil que {contrato_1}"
        }
        
        # Ratio de días fuertes
        ratio_fuertes = (
            self.comparacion.loc[contrato_1, 'pct_dias_fuertes'] / 
            self.comparacion.loc[contrato_2, 'pct_dias_fuertes']
        )
        
        ratios['dias_fuertes'] = {
            'ratio': ratio_fuertes,
            'diferencia': abs(
                self.comparacion.loc[contrato_1, 'pct_dias_fuertes'] - 
                self.comparacion.loc[contrato_2, 'pct_dias_fuertes']
            )
        }
        
        # Ratio de volumen
        ratio_volumen = (
            self.comparacion.loc[contrato_1, 'volumen_promedio'] / 
            self.comparacion.loc[contrato_2, 'volumen_promedio']
        )
        
        ratios['volumen'] = {
            'ratio': ratio_volumen,
            'interpretacion': f"{contrato_1} tiene {ratio_volumen:.2f}x el volumen de {contrato_2}"
                            if ratio_volumen > 1
                            else f"{contrato_2} tiene {1/ratio_volumen:.2f}x el volumen de {contrato_1}"
        }
        
        self.ratios = ratios
        return ratios
    
    def calcular_correlacion_temporal(self):
        """
        Calcula correlación entre rangos diarios de dos contratos
        
        Returns:
            float: coeficiente de correlación
        """
        if len(self.contratos) != 2:
            print("⚠ La correlación solo se calcula para 2 contratos")
            return None
        
        nombres = list(self.contratos.keys())
        
        # Obtener rangos diarios de ambos contratos
        rangos_1 = self.contratos[nombres[0]]['clasificaciones']['rango_diario']
        rangos_2 = self.contratos[nombres[1]]['clasificaciones']['rango_diario']
        
        # Alinear por fechas (por si tienen días diferentes)
        df_merge = pd.DataFrame({
            nombres[0]: rangos_1,
            nombres[1]: rangos_2
        }).dropna()
        
        if len(df_merge) == 0:
            print("⚠ No hay fechas coincidentes entre contratos")
            return None
        
        correlacion = df_merge[nombres[0]].corr(df_merge[nombres[1]])
        
        print(f"\n✓ Correlación entre {nombres[0]} y {nombres[1]}: {correlacion:+.3f}")
        
        return correlacion
    
    def crear_grafico_comparativo(self):
        """
        Crea gráficos comparativos entre contratos
        
        Returns:
            plotly.graph_objects.Figure
        """
        if not PLOTLY_AVAILABLE:
            print("⚠ Plotly no disponible")
            return None
        
        if self.comparacion is None:
            self.calcular_metricas_comparativas()
        
        # Crear subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Rango Promedio Diario',
                'Volatilidad Promedio',
                'Distribución de Días (Fuerte/Lateral)',
                'Volumen Promedio Diario'
            ),
            specs=[
                [{'type': 'bar'}, {'type': 'bar'}],
                [{'type': 'bar'}, {'type': 'bar'}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )
        
        contratos = self.comparacion.index.tolist()
        colores = ['#667eea', '#764ba2', '#f59e0b', '#10b981']
        
        # 1. Rango promedio
        fig.add_trace(
            go.Bar(
                x=contratos,
                y=self.comparacion['rango_promedio'],
                marker_color=colores[0],
                name='Rango Promedio',
                hovertemplate='%{x}<br>Rango: %{y:.1f} pts<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. Volatilidad
        fig.add_trace(
            go.Bar(
                x=contratos,
                y=self.comparacion['volatilidad_promedio'],
                marker_color=colores[1],
                name='Volatilidad',
                hovertemplate='%{x}<br>Volatilidad: %{y:.2f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. Distribución fuertes/laterales
        fig.add_trace(
            go.Bar(
                x=contratos,
                y=self.comparacion['pct_dias_fuertes'],
                marker_color='#10b981',
                name='% Días Fuertes',
                hovertemplate='%{x}<br>Fuertes: %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=contratos,
                y=self.comparacion['pct_dias_laterales'],
                marker_color='#ef4444',
                name='% Días Laterales',
                hovertemplate='%{x}<br>Laterales: %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 4. Volumen
        fig.add_trace(
            go.Bar(
                x=contratos,
                y=self.comparacion['volumen_promedio'],
                marker_color=colores[2],
                name='Volumen',
                hovertemplate='%{x}<br>Volumen: %{y:,.0f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Layout
        fig.update_yaxes(title_text="Puntos", row=1, col=1)
        fig.update_yaxes(title_text="Volatilidad", row=1, col=2)
        fig.update_yaxes(title_text="Porcentaje", row=2, col=1)
        fig.update_yaxes(title_text="Contratos", row=2, col=2)
        
        fig.update_layout(
            title_text="Comparación Multi-Contrato",
            showlegend=False,
            height=700,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        ```python
        fig.update_layout(
            # ... todo lo existente ...
            plot_bgcolor='rgba(30, 30, 30, 0.5)',
            paper_bgcolor='rgba(20, 20, 20, 0.85)',
            font={'color': '#ffffff'},
            margin={'l': 60, 'r': 40, 't': 100, 'b': 60}
        )
        ```
        
        return fig
    
    def crear_grafico_overlay(self):
        """
        Crea gráfico overlay de evolución temporal (para 2 contratos)
        
        Returns:
            plotly.graph_objects.Figure
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        if len(self.contratos) != 2:
            print("⚠ El overlay solo funciona con 2 contratos")
            return None
        
        nombres = list(self.contratos.keys())
        
        # Obtener datos de ambos contratos
        datos_1 = self.contratos[nombres[0]]['clasificaciones'].sort_index()
        datos_2 = self.contratos[nombres[1]]['clasificaciones'].sort_index()
        
        # Crear figura
        fig = go.Figure()
        
        # Contrato 1
        fig.add_trace(go.Scatter(
            x=datos_1.index,
            y=datos_1['rango_diario'],
            mode='lines+markers',
            name=nombres[0],
            line=dict(color='#667eea', width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Rango: %{y:.1f} pts<extra></extra>'
        ))
        
        # Contrato 2
        fig.add_trace(go.Scatter(
            x=datos_2.index,
            y=datos_2['rango_diario'],
            mode='lines+markers',
            name=nombres[1],
            line=dict(color='#f59e0b', width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Rango: %{y:.1f} pts<extra></extra>'
        ))
        
        # Layout
        fig.update_layout(
            title='Evolución Temporal Comparada',
            xaxis_title='Fecha',
            yaxis_title='Rango Diario (puntos)',
            hovermode='x unified',
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        ```python
        fig.update_layout(
            # ... todo lo existente ...
            plot_bgcolor='rgba(30, 30, 30, 0.5)',
            paper_bgcolor='rgba(20, 20, 20, 0.85)',
            font={'color': '#ffffff'},
            xaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
            yaxis={'gridcolor': 'rgba(255,255,255,0.1)'},
            margin={'l': 60, 'r': 40, 't': 80, 'b': 60}
        )
        ```
        
        return fig
    
    def generar_reporte_comparativo(self):
        """
        Genera reporte completo de comparación
        
        Returns:
            str: reporte formateado
        """
        if self.comparacion is None:
            self.calcular_metricas_comparativas()
        
        reporte = []
        reporte.append("=" * 70)
        reporte.append("COMPARACIÓN MULTI-CONTRATO")
        reporte.append("=" * 70)
        reporte.append("")
        
        # 1. Tabla comparativa
        reporte.append("MÉTRICAS COMPARATIVAS")
        reporte.append("-" * 70)
        reporte.append("")
        
        for contrato in self.comparacion.index:
            row = self.comparacion.loc[contrato]
            
            reporte.append(f"📊 {contrato}")
            reporte.append(f"  Total días: {row['total_dias']}")
            reporte.append(f"  Rango promedio: {row['rango_promedio']:.1f} pts")
            reporte.append(f"  Rango máximo: {row['rango_max']:.1f} pts")
            reporte.append(f"  Días fuertes: {row['dias_fuertes']} ({row['pct_dias_fuertes']:.1f}%)")
            reporte.append(f"  Días laterales: {row['dias_laterales']} ({row['pct_dias_laterales']:.1f}%)")
            reporte.append(f"  Volatilidad: {row['volatilidad_promedio']:.2f}")
            reporte.append(f"  Volumen promedio: {row['volumen_promedio']:,.0f}")
            reporte.append(f"  Outliers: {row['outliers']}")
            reporte.append("")
        
        # 2. Ratios (si hay 2 contratos)
        if len(self.contratos) == 2:
            if self.ratios is None:
                self.calcular_ratios()
            
            reporte.append("RATIOS Y COMPARACIONES")
            reporte.append("-" * 70)
            
            nombres = list(self.comparacion.index)
            
            reporte.append(f"• Volatilidad: {self.ratios['volatilidad']['interpretacion']}")
            reporte.append(f"• Diferencia en días fuertes: {self.ratios['dias_fuertes']['diferencia']:.1f} puntos porcentuales")
            reporte.append(f"• Volumen: {self.ratios['volumen']['interpretacion']}")
            
            # Correlación
            correlacion = self.calcular_correlacion_temporal()
            if correlacion:
                reporte.append(f"• Correlación temporal: {correlacion:+.3f}")
                
                if abs(correlacion) > 0.7:
                    reporte.append("  → Los contratos se mueven de forma muy similar")
                elif abs(correlacion) > 0.4:
                    reporte.append("  → Los contratos tienen correlación moderada")
                else:
                    reporte.append("  → Los contratos se mueven de forma independiente")
            
            reporte.append("")
        
        # 3. Recomendación
        reporte.append("RECOMENDACIÓN")
        reporte.append("-" * 70)
        
        # Contrato más volátil
        mas_volatil = self.comparacion['rango_promedio'].idxmax()
        reporte.append(f"• Para mayor movimiento: Tradear {mas_volatil}")
        
        # Contrato más consistente (menos outliers)
        mas_consistente = self.comparacion['outliers'].idxmin()
        reporte.append(f"• Para menor sorpresas: Tradear {mas_consistente}")
        
        # Mayor volumen (liquidez)
        mayor_volumen = self.comparacion['volumen_promedio'].idxmax()
        reporte.append(f"• Para mejor liquidez: Tradear {mayor_volumen}")
        
        reporte.append("")
        reporte.append("=" * 70)
        
        return "\n".join(reporte)
    
    def exportar_comparacion(self, nombre_archivo="comparacion_contratos.txt"):
        """
        Exporta comparación a archivo
        
        Args:
            nombre_archivo: nombre del archivo de salida
        """
        ruta = OUTPUTS_DIR / nombre_archivo
        
        reporte = self.generar_reporte_comparativo()
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"✓ Comparación exportada a: {ruta}")
        
        # CSV
        ruta_csv = OUTPUTS_DIR / nombre_archivo.replace('.txt', '.csv')
        self.comparacion.to_csv(ruta_csv)
        print(f"✓ Versión CSV guardada en: {ruta_csv}")


# ==============================================
# FUNCIÓN HELPER
# ==============================================

def comparar_contratos(contratos_data, exportar=True, generar_graficos=True):
    """
    Ejecuta comparación completa entre contratos
    
    Args:
        contratos_data: dict con datos de contratos
        exportar: si exportar resultados
        generar_graficos: si generar gráficos
        
    Returns:
        MultiContractComparison con análisis completo
    """
    comparador = MultiContractComparison(contratos_data)
    
    # Ejecutar análisis
    comparador.calcular_metricas_comparativas()
    
    if len(contratos_data) == 2:
        comparador.calcular_ratios()
    
    # Mostrar reporte
    print("\n" + comparador.generar_reporte_comparativo())
    
    # Exportar
    if exportar:
        comparador.exportar_comparacion()
    
    # Generar gráficos
    if generar_graficos and PLOTLY_AVAILABLE:
        # Gráfico comparativo
        fig1 = comparador.crear_grafico_comparativo()
        if fig1:
            ruta_html = OUTPUTS_DIR / "comparacion_contratos.html"
            fig1.write_html(str(ruta_html))
            print(f"✓ Gráfico comparativo guardado en: {ruta_html}")
        
        # Overlay (solo para 2 contratos)
        if len(contratos_data) == 2:
            fig2 = comparador.crear_grafico_overlay()
            if fig2:
                ruta_html = OUTPUTS_DIR / "overlay_contratos.html"
                fig2.write_html(str(ruta_html))
                print(f"✓ Overlay temporal guardado en: {ruta_html}")
    
    return comparador


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para comparar dos contratos
    """
    from src.ingestion import cargar_datos_procesados
    from src.classifier import DayClassifier
    
    # Cargar primer contrato (ejemplo: MNQ 03-26)
    df1 = cargar_datos_procesados("MNQ 03-26.Last_processed.parquet")
    
    if df1 is not None:
        classifier1 = DayClassifier(df1)
        classifier1.calcular_estadisticas_diarias()
        classifier1.clasificar_dias()
        
        # Simular segundo contrato (en uso real, cargarías otro archivo)
        # df2 = cargar_datos_procesados("NQ 03-26.Last_processed.parquet")
        # Para este ejemplo, usaremos el mismo
        
        contratos = {
            'MNQ 03-26': {
                'df': df1,
                'clasificaciones': classifier1.clasificaciones
            },
            # 'NQ 03-26': {
            #     'df': df2,
            #     'clasificaciones': classifier2.clasificaciones
            # }
        }
        
        # Comparar
        comparador = comparar_contratos(
            contratos,
            exportar=True,
            generar_graficos=True
        )
        
        print("\n✓ Comparación completada")
