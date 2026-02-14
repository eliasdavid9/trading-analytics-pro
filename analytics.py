"""
Módulo de análisis avanzado de sesiones y patrones
Identifica correlaciones y comportamientos predictivos
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import SESIONES, DECIMALES_PORCENTAJE, OUTPUTS_DIR


class SessionAnalytics:
    """
    Analizador de sesiones y patrones de trading
    """
    
    def __init__(self, df, clasificaciones=None):
        """
        Inicializa el analizador
        
        Args:
            df: DataFrame con datos procesados (de ingestion.py)
            clasificaciones: DataFrame con clasificaciones de días (opcional)
        """
        self.df = df.copy()
        self.clasificaciones = clasificaciones
        self.stats_sesiones = None
        self.correlaciones = None
        
    def calcular_estadisticas_por_sesion(self):
        """
        Calcula estadísticas agregadas por sesión y día
        
        Returns:
            DataFrame con stats por sesión
        """
        # Agrupar por fecha y sesión
        stats = self.df.groupby(['fecha', 'sesion']).agg({
            'high': 'max',
            'low': 'min',
            'open': 'first',
            'close': 'last',
            'volume': 'sum',
            'rango': 'sum',
            'datetime': 'count'
        }).rename(columns={'datetime': 'num_velas', 'rango': 'rango_total'})
        
        # Calcular rango de la sesión
        stats['rango_sesion'] = stats['high'] - stats['low']
        
        # Calcular cambio dentro de la sesión
        stats['cambio_sesion'] = stats['close'] - stats['open']
        stats['cambio_pct'] = (stats['cambio_sesion'] / stats['open']) * 100
        
        # Dirección de la sesión
        stats['direccion'] = stats['cambio_sesion'].apply(
            lambda x: 'ALCISTA' if x > 0 else ('BAJISTA' if x < 0 else 'NEUTRO')
        )
        
        self.stats_sesiones = stats
        
        print(f"✓ Calculadas estadísticas para {len(stats)} sesiones")
        return stats
    
    def analizar_distribucion_sesiones(self):
        """
        Analiza cómo se distribuye el movimiento entre sesiones
        
        Returns:
            DataFrame con distribución promedio por sesión
        """
        if self.stats_sesiones is None:
            self.calcular_estadisticas_por_sesion()
        
        # Calcular rango total del día
        rango_diario = self.df.groupby('fecha').agg({
            'high': 'max',
            'low': 'min'
        })
        rango_diario['rango_dia'] = rango_diario['high'] - rango_diario['low']
        
        # Merge con stats de sesiones
        stats_con_dia = self.stats_sesiones.reset_index().merge(
            rango_diario[['rango_dia']],
            left_on='fecha',
            right_index=True
        )
        
        # Calcular % del rango diario que corresponde a cada sesión
        stats_con_dia['pct_rango_dia'] = (
            stats_con_dia['rango_sesion'] / stats_con_dia['rango_dia'] * 100
        )
        
        # Promedios por sesión
        resumen = stats_con_dia.groupby('sesion').agg({
            'rango_sesion': ['mean', 'std', 'min', 'max'],
            'pct_rango_dia': ['mean', 'std'],
            'volume': 'mean',
            'num_velas': 'mean'
        }).round(2)
        
        return resumen
    
    def identificar_sesion_dominante(self):
        """
        Identifica qué sesión suele ser la dominante (mayor movimiento)
        
        Returns:
            DataFrame con análisis de dominancia por día
        """
        if self.stats_sesiones is None:
            self.calcular_estadisticas_por_sesion()
        
        # Encontrar sesión con mayor rango por día
        idx_max = self.stats_sesiones.groupby(level='fecha')['rango_sesion'].idxmax()
        
        sesiones_dominantes = []
        for fecha, idx in idx_max.items():
            if pd.notna(idx):  # Verificar que el índice sea válido
                sesion = idx[1] if isinstance(idx, tuple) else self.stats_sesiones.loc[idx].name[1]
                rango = self.stats_sesiones.loc[idx, 'rango_sesion']
                sesiones_dominantes.append({
                    'fecha': fecha,
                    'sesion_dominante': sesion,
                    'rango': rango
                })
        
        df_dominantes = pd.DataFrame(sesiones_dominantes)
        
        # Contar frecuencia
        conteo = df_dominantes['sesion_dominante'].value_counts()
        porcentajes = (conteo / len(df_dominantes) * 100).round(1)
        
        print("\nSESIONES DOMINANTES (mayor rango del día):")
        print("-" * 50)
        for sesion in ['ASIA', 'EUROPA', 'NY']:
            if sesion in conteo:
                print(f"  {sesion:8} : {conteo[sesion]:2} días ({porcentajes[sesion]:5.1f}%)")
        
        return df_dominantes
    
    def analizar_sesiones_por_tipo_dia(self):
        """
        Analiza comportamiento de sesiones según tipo de día
        Requiere que se hayan cargado clasificaciones
        
        Returns:
            DataFrame con análisis por tipo de día y sesión
        """
        if self.clasificaciones is None:
            print("⚠ No hay clasificaciones cargadas. Ejecutá primero el classifier.")
            return None
        
        if self.stats_sesiones is None:
            self.calcular_estadisticas_por_sesion()
        
        # Merge sesiones con clasificaciones
        stats_merge = self.stats_sesiones.reset_index().merge(
            self.clasificaciones[['clasificacion']],
            left_on='fecha',
            right_index=True,
            how='left'
        )
        
        # Análisis por clasificación y sesión
        analisis = stats_merge.groupby(['clasificacion', 'sesion']).agg({
            'rango_sesion': ['mean', 'std', 'count'],
            'volume': 'mean'
        }).round(2)
        
        analisis.columns = ['rango_promedio', 'rango_std', 'num_ocurrencias', 'volumen_promedio']
        
        return analisis
    
    def detectar_correlacion_sesiones(self):
        """
        Detecta si el comportamiento de una sesión predice la siguiente
        
        Returns:
            dict con correlaciones entre sesiones
        """
        if self.stats_sesiones is None:
            self.calcular_estadisticas_por_sesion()
        
        # Pivot para tener sesiones como columnas
        pivot = self.stats_sesiones.reset_index().pivot(
            index='fecha',
            columns='sesion',
            values='rango_sesion'
        )
        
        # Calcular correlaciones
        correlaciones = {}
        
        # ¿Asia predice Europa?
        if 'ASIA' in pivot.columns and 'EUROPA' in pivot.columns:
            corr_asia_europa = pivot['ASIA'].corr(pivot['EUROPA'])
            correlaciones['ASIA→EUROPA'] = round(corr_asia_europa, 3)
        
        # ¿Europa predice NY?
        if 'EUROPA' in pivot.columns and 'NY' in pivot.columns:
            corr_europa_ny = pivot['EUROPA'].corr(pivot['NY'])
            correlaciones['EUROPA→NY'] = round(corr_europa_ny, 3)
        
        # ¿Asia predice NY?
        if 'ASIA' in pivot.columns and 'NY' in pivot.columns:
            corr_asia_ny = pivot['ASIA'].corr(pivot['NY'])
            correlaciones['ASIA→NY'] = round(corr_asia_ny, 3)
        
        # Correlación con rango total del día
        rango_diario = self.df.groupby('fecha').agg({
            'high': 'max',
            'low': 'min'
        })
        rango_diario['rango_dia'] = rango_diario['high'] - rango_diario['low']
        
        for sesion in pivot.columns:
            merged = pivot.merge(rango_diario[['rango_dia']], left_index=True, right_index=True)
            corr = merged[sesion].corr(merged['rango_dia'])
            correlaciones[f'{sesion}→RANGO_DIA'] = round(corr, 3)
        
        self.correlaciones = correlaciones
        return correlaciones
    
    def detectar_patron_apertura(self):
        """
        Analiza el patrón de la primera hora vs el resto del día
        
        Returns:
            DataFrame con estadísticas de apertura
        """
        # Identificar primera hora de cada sesión
        df_sorted = self.df.sort_values(['fecha', 'datetime'])
        
        # Primera vela de cada sesión
        primera_vela = df_sorted.groupby(['fecha', 'sesion']).first()
        
        # Analizar gaps de apertura entre sesiones
        pivot_open = primera_vela.reset_index().pivot(
            index='fecha',
            columns='sesion',
            values='open'
        )
        
        # Calcular gaps
        gaps = {}
        if 'ASIA' in pivot_open.columns and 'EUROPA' in pivot_open.columns:
            gaps['gap_asia_europa'] = (pivot_open['EUROPA'] - pivot_open['ASIA']).describe()
        
        if 'EUROPA' in pivot_open.columns and 'NY' in pivot_open.columns:
            gaps['gap_europa_ny'] = (pivot_open['NY'] - pivot_open['EUROPA']).describe()
        
        return gaps
    
    def generar_reporte_sesiones(self):
        """
        Genera reporte completo de análisis de sesiones
        
        Returns:
            str: reporte formateado
        """
        if self.stats_sesiones is None:
            self.calcular_estadisticas_por_sesion()
        
        reporte = []
        reporte.append("=" * 70)
        reporte.append("ANÁLISIS PROFUNDO DE SESIONES")
        reporte.append("=" * 70)
        reporte.append("")
        
        # 1. Distribución de movimiento por sesión
        reporte.append("1. DISTRIBUCIÓN DE RANGOS POR SESIÓN")
        reporte.append("-" * 70)
        dist = self.analizar_distribucion_sesiones()
        reporte.append(str(dist))
        reporte.append("")
        
        # 2. Sesiones dominantes
        reporte.append("2. FRECUENCIA DE SESIÓN DOMINANTE")
        reporte.append("-" * 70)
        dominantes = self.identificar_sesion_dominante()
        reporte.append("")
        
        # 3. Correlaciones
        reporte.append("3. CORRELACIONES ENTRE SESIONES")
        reporte.append("-" * 70)
        if self.correlaciones is None:
            self.detectar_correlacion_sesiones()
        
        for clave, valor in self.correlaciones.items():
            interpretacion = self._interpretar_correlacion(valor)
            reporte.append(f"  {clave:20} : {valor:+.3f}  ({interpretacion})")
        reporte.append("")
        
        # 4. Análisis por tipo de día (si hay clasificaciones)
        if self.clasificaciones is not None:
            reporte.append("4. SESIONES POR TIPO DE DÍA")
            reporte.append("-" * 70)
            por_tipo = self.analizar_sesiones_por_tipo_dia()
            if por_tipo is not None:
                reporte.append(str(por_tipo))
            reporte.append("")
        
        reporte.append("=" * 70)
        
        return "\n".join(reporte)
    
    def _interpretar_correlacion(self, valor):
        """
        Interpreta el valor de correlación
        
        Args:
            valor: coeficiente de correlación (-1 a 1)
            
        Returns:
            str: interpretación
        """
        abs_val = abs(valor)
        
        if abs_val > 0.7:
            fuerza = "Correlación FUERTE"
        elif abs_val > 0.4:
            fuerza = "Correlación MODERADA"
        elif abs_val > 0.2:
            fuerza = "Correlación DÉBIL"
        else:
            fuerza = "Sin correlación"
        
        direccion = "positiva" if valor > 0 else "negativa"
        
        return f"{fuerza} {direccion}"
    
    def exportar_analisis(self, nombre_archivo="analisis_sesiones.txt"):
        """
        Exporta análisis completo a archivo
        
        Args:
            nombre_archivo: nombre del archivo de salida
        """
        ruta = OUTPUTS_DIR / nombre_archivo
        
        reporte = self.generar_reporte_sesiones()
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"✓ Análisis de sesiones exportado a: {ruta}")


# ==============================================
# FUNCIÓN HELPER
# ==============================================

def analizar_sesiones_completo(df, clasificaciones=None, exportar=True):
    """
    Ejecuta análisis completo de sesiones
    
    Args:
        df: DataFrame con datos procesados
        clasificaciones: DataFrame con clasificaciones (opcional)
        exportar: si exportar resultados
        
    Returns:
        SessionAnalytics con análisis completo
    """
    analytics = SessionAnalytics(df, clasificaciones)
    
    # Ejecutar todos los análisis
    analytics.calcular_estadisticas_por_sesion()
    analytics.analizar_distribucion_sesiones()
    analytics.identificar_sesion_dominante()
    analytics.detectar_correlacion_sesiones()
    
    if clasificaciones is not None:
        analytics.analizar_sesiones_por_tipo_dia()
    
    # Mostrar reporte
    print("\n" + analytics.generar_reporte_sesiones())
    
    # Exportar
    if exportar:
        analytics.exportar_analisis()
    
    return analytics


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el analizador de sesiones
    """
    from src.ingestion import cargar_datos_procesados
    from src.classifier import DayClassifier
    
    # Cargar datos
    df = cargar_datos_procesados("MNQ 03-26.Last_processed.parquet")
    
    if df is not None:
        # Cargar clasificaciones
        classifier = DayClassifier(df)
        classifier.calcular_estadisticas_diarias()
        classifier.clasificar_dias()
        clasificaciones = classifier.clasificaciones
        
        # Análisis de sesiones
        analytics = analizar_sesiones_completo(
            df, 
            clasificaciones=clasificaciones,
            exportar=True
        )
        
        print("\n✓ Análisis de sesiones completado")