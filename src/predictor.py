"""
Módulo predictivo
Genera probabilidades y recomendaciones tácticas basadas en patrones históricos
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
import sys

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import SESIONES, OUTPUTS_DIR


class TradingPredictor:
    """
    Motor predictivo que genera probabilidades y recomendaciones
    """
    
    def __init__(self, df, clasificaciones, stats_sesiones):
        """
        Inicializa el predictor
        
        Args:
            df: DataFrame con datos procesados
            clasificaciones: DataFrame con clasificaciones de días
            stats_sesiones: DataFrame con estadísticas de sesiones
        """
        self.df = df
        self.clasificaciones = clasificaciones
        self.stats_sesiones = stats_sesiones
        self.patrones = {}
        self.reglas_probabilisticas = {}
        
    def analizar_patrones_dia_semana(self):
        """
        Analiza probabilidades por día de semana
        
        Returns:
            dict con probabilidades por día
        """
        dias_esp = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        
        analisis = pd.crosstab(
            self.clasificaciones['dia_semana'],
            self.clasificaciones['clasificacion'],
            normalize='index'
        ) * 100
        
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        analisis = analisis.reindex(orden_dias, fill_value=0)
        
        # Convertir a dict con nombres en español
        patrones = {}
        for dia_en, dia_es in dias_esp.items():
            if dia_en in analisis.index:
                patrones[dia_es] = {
                    'prob_fuerte': round(analisis.loc[dia_en].get('FUERTE', 0), 1),
                    'prob_intermedio': round(analisis.loc[dia_en].get('INTERMEDIO', 0), 1),
                    'prob_lateral': round(analisis.loc[dia_en].get('LATERAL', 0), 1)
                }
        
        self.patrones['dia_semana'] = patrones
        return patrones
    
    def analizar_patron_sesion_previa(self):
        """
        Analiza si el comportamiento de una sesión predice la siguiente
        
        Returns:
            dict con probabilidades condicionales
        """
        # Preparar datos de sesiones por día
        pivot = self.stats_sesiones.reset_index().pivot(
            index='fecha',
            columns='sesion',
            values='rango_sesion'
        )
        
        # Merge con clasificaciones
        pivot_con_clase = pivot.merge(
            self.clasificaciones[['clasificacion']],
            left_index=True,
            right_index=True,
            how='left'
        )
        
        patrones = {}
        
        # ¿Si ASIA es fuerte, qué pasa con EUROPA?
        if 'ASIA' in pivot.columns and 'EUROPA' in pivot.columns:
            p75_asia = pivot['ASIA'].quantile(0.75)
            
            asia_fuerte = pivot_con_clase[pivot_con_clase['ASIA'] >= p75_asia]
            if len(asia_fuerte) > 3:  # Mínimo 3 casos
                europa_alta = (asia_fuerte['EUROPA'] >= asia_fuerte['EUROPA'].median()).sum()
                prob = (europa_alta / len(asia_fuerte)) * 100
                
                patrones['asia_fuerte_europa'] = {
                    'condicion': 'Si ASIA mueve >P75',
                    'probabilidad': round(prob, 1),
                    'n_casos': len(asia_fuerte),
                    'descripcion': f'Europa también sea activa ({prob:.0f}%)'
                }
        
        # ¿Si EUROPA es fuerte, qué pasa con NY?
        if 'EUROPA' in pivot.columns and 'NY' in pivot.columns:
            p75_europa = pivot['EUROPA'].quantile(0.75)
            
            europa_fuerte = pivot_con_clase[pivot_con_clase['EUROPA'] >= p75_europa]
            if len(europa_fuerte) > 3:
                ny_alta = (europa_fuerte['NY'] >= europa_fuerte['NY'].median()).sum()
                prob = (ny_alta / len(europa_fuerte)) * 100
                
                patrones['europa_fuerte_ny'] = {
                    'condicion': 'Si EUROPA mueve >P75',
                    'probabilidad': round(prob, 1),
                    'n_casos': len(europa_fuerte),
                    'descripcion': f'NY también sea activa ({prob:.0f}%)'
                }
        
        self.patrones['sesion_previa'] = patrones
        return patrones
    
    def analizar_rachas(self):
        """
        Analiza qué pasa después de rachas de días similares
        
        Returns:
            dict con probabilidades post-racha
        """
        # Ordenar por fecha
        df_sorted = self.clasificaciones.sort_index()
        
        # Detectar rachas de 2+ días consecutivos
        df_sorted['prev_clase'] = df_sorted['clasificacion'].shift(1)
        df_sorted['prev_prev_clase'] = df_sorted['clasificacion'].shift(2)
        
        patrones = {}
        
        # ¿Qué pasa después de 2 días laterales?
        dos_laterales = df_sorted[
            (df_sorted['prev_clase'] == 'LATERAL') & 
            (df_sorted['prev_prev_clase'] == 'LATERAL')
        ]
        
        if len(dos_laterales) > 3:
            prob_fuerte = (dos_laterales['clasificacion'] == 'FUERTE').sum() / len(dos_laterales) * 100
            
            patrones['post_2_laterales'] = {
                'condicion': 'Después de 2 días laterales consecutivos',
                'probabilidad_fuerte': round(prob_fuerte, 1),
                'n_casos': len(dos_laterales),
                'descripcion': f'Día fuerte ({prob_fuerte:.0f}%)'
            }
        
        # ¿Qué pasa después de 2 días fuertes?
        dos_fuertes = df_sorted[
            (df_sorted['prev_clase'] == 'FUERTE') & 
            (df_sorted['prev_prev_clase'] == 'FUERTE')
        ]
        
        if len(dos_fuertes) > 3:
            prob_lateral = (dos_fuertes['clasificacion'] == 'LATERAL').sum() / len(dos_fuertes) * 100
            
            patrones['post_2_fuertes'] = {
                'condicion': 'Después de 2 días fuertes consecutivos',
                'probabilidad_lateral': round(prob_lateral, 1),
                'n_casos': len(dos_fuertes),
                'descripcion': f'Día lateral (consolidación) ({prob_lateral:.0f}%)'
            }
        
        self.patrones['rachas'] = patrones
        return patrones
    
    def generar_reglas_probabilisticas(self):
        """
        Genera reglas probabilísticas accionables
        
        Returns:
            dict con reglas y sus probabilidades
        """
        if not self.patrones:
            self.analizar_patrones_dia_semana()
            self.analizar_patron_sesion_previa()
            self.analizar_rachas()
        
        reglas = []
        
        # Reglas por día de semana
        for dia, probs in self.patrones.get('dia_semana', {}).items():
            if probs['prob_fuerte'] >= 45:
                reglas.append({
                    'tipo': 'DIA_SEMANA',
                    'condicion': f"Es {dia}",
                    'prediccion': 'Día FUERTE probable',
                    'probabilidad': probs['prob_fuerte'],
                    'confianza': 'ALTA' if probs['prob_fuerte'] >= 50 else 'MEDIA',
                    'tactica': 'Dejar correr trades | Posiciones más grandes | Buscar breakouts'
                })
            elif probs['prob_lateral'] >= 45:
                reglas.append({
                    'tipo': 'DIA_SEMANA',
                    'condicion': f"Es {dia}",
                    'prediccion': 'Día LATERAL probable',
                    'probabilidad': probs['prob_lateral'],
                    'confianza': 'ALTA' if probs['prob_lateral'] >= 50 else 'MEDIA',
                    'tactica': 'Scalping | Range trading | Reducir exposición'
                })
        
        # Reglas por sesión previa
        for key, patron in self.patrones.get('sesion_previa', {}).items():
            if patron['probabilidad'] >= 60:
                reglas.append({
                    'tipo': 'SESION_PREVIA',
                    'condicion': patron['condicion'],
                    'prediccion': patron['descripcion'],
                    'probabilidad': patron['probabilidad'],
                    'confianza': 'ALTA' if patron['probabilidad'] >= 70 else 'MEDIA',
                    'tactica': 'Preparar estrategia para sesión activa'
                })
        
        # Reglas por rachas
        for key, patron in self.patrones.get('rachas', {}).items():
            if 'probabilidad_fuerte' in patron and patron['probabilidad_fuerte'] >= 50:
                reglas.append({
                    'tipo': 'RACHA',
                    'condicion': patron['condicion'],
                    'prediccion': patron['descripcion'],
                    'probabilidad': patron['probabilidad_fuerte'],
                    'confianza': 'ALTA' if patron['probabilidad_fuerte'] >= 65 else 'MEDIA',
                    'tactica': 'Anticipar expansión de volatilidad'
                })
            elif 'probabilidad_lateral' in patron and patron['probabilidad_lateral'] >= 50:
                reglas.append({
                    'tipo': 'RACHA',
                    'condicion': patron['condicion'],
                    'prediccion': patron['descripcion'],
                    'probabilidad': patron['probabilidad_lateral'],
                    'confianza': 'ALTA' if patron['probabilidad_lateral'] >= 65 else 'MEDIA',
                    'tactica': 'Esperar consolidación | Reducir tamaño'
                })
        
        self.reglas_probabilisticas = reglas
        return reglas
    
    def predecir_contexto_actual(self, fecha_hoy=None, hora_actual=None, rango_asia=None, rango_europa=None):
        """
        Genera predicción para el contexto actual del trading
        
        Args:
            fecha_hoy: datetime.date de hoy (default: hoy)
            hora_actual: time actual (default: ahora)
            rango_asia: rango de Asia HOY (opcional)
            rango_europa: rango de Europa HOY (opcional)
            
        Returns:
            dict con predicciones contextuales
        """
        if fecha_hoy is None:
            fecha_hoy = datetime.now().date()
        
        if hora_actual is None:
            hora_actual = datetime.now().time()
        
        dia_semana_en = pd.Timestamp(fecha_hoy).day_name()
        dias_map = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes'
        }
        dia_semana = dias_map.get(dia_semana_en, dia_semana_en)
        
        prediccion = {
            'fecha': fecha_hoy,
            'dia_semana': dia_semana,
            'hora_actual': hora_actual,
            'predicciones': [],
            'tacticas_sugeridas': []
        }
        
        # Predicción por día de semana
        if dia_semana in self.patrones.get('dia_semana', {}):
            probs = self.patrones['dia_semana'][dia_semana]
            tipo_probable = max(probs.items(), key=lambda x: x[1] if x[0].startswith('prob_') else 0)
            
            tipo_dia = tipo_probable[0].replace('prob_', '').upper()
            prob = tipo_probable[1]
            
            prediccion['predicciones'].append({
                'fuente': 'Patrón histórico día de semana',
                'prediccion': f'Día {tipo_dia}',
                'probabilidad': f'{prob:.0f}%',
                'confianza': 'ALTA' if prob >= 50 else 'MEDIA'
            })
            
            # Táctica sugerida
            if tipo_dia == 'FUERTE':
                prediccion['tacticas_sugeridas'].append('Dejar correr trades con trailing stops amplios')
            elif tipo_dia == 'LATERAL':
                prediccion['tacticas_sugeridas'].append('Scalping o range trading')
        
        # Predicción basada en sesión previa (si hay datos)
        if rango_asia:
            pivot = self.stats_sesiones.reset_index().pivot(
                index='fecha',
                columns='sesion',
                values='rango_sesion'
            )
            
            if 'ASIA' in pivot.columns:
                p75_asia = pivot['ASIA'].quantile(0.75)
                
                if rango_asia >= p75_asia:
                    # Asia fue fuerte
                    patron = self.patrones.get('sesion_previa', {}).get('asia_fuerte_europa', {})
                    if patron:
                        prediccion['predicciones'].append({
                            'fuente': 'Asia HOY fue fuerte',
                            'prediccion': f'Europa probablemente activa',
                            'probabilidad': f"{patron['probabilidad']:.0f}%",
                            'confianza': 'ALTA' if patron['probabilidad'] >= 70 else 'MEDIA'
                        })
                        prediccion['tacticas_sugeridas'].append('Preparar estrategia para Europa volátil')
        
        if rango_europa:
            pivot = self.stats_sesiones.reset_index().pivot(
                index='fecha',
                columns='sesion',
                values='rango_sesion'
            )
            
            if 'EUROPA' in pivot.columns:
                p75_europa = pivot['EUROPA'].quantile(0.75)
                
                if rango_europa >= p75_europa:
                    # Europa fue fuerte
                    patron = self.patrones.get('sesion_previa', {}).get('europa_fuerte_ny', {})
                    if patron:
                        prediccion['predicciones'].append({
                            'fuente': 'Europa HOY fue fuerte',
                            'prediccion': f'NY probablemente activa',
                            'probabilidad': f"{patron['probabilidad']:.0f}%",
                            'confianza': 'ALTA' if patron['probabilidad'] >= 70 else 'MEDIA'
                        })
                        prediccion['tacticas_sugeridas'].append('Preparar estrategia para NY volátil')
        
        # Predicción basada en rachas
        ultimos_dias = self.clasificaciones.sort_index().tail(2)
        if len(ultimos_dias) == 2:
            ultimas_clases = ultimos_dias['clasificacion'].tolist()
            
            if ultimas_clases == ['LATERAL', 'LATERAL']:
                patron = self.patrones.get('rachas', {}).get('post_2_laterales', {})
                if patron:
                    prediccion['predicciones'].append({
                        'fuente': 'Racha: 2 días laterales consecutivos',
                        'prediccion': patron['descripcion'],
                        'probabilidad': f"{patron['probabilidad_fuerte']:.0f}%",
                        'confianza': 'MEDIA'
                    })
                    prediccion['tacticas_sugeridas'].append('Anticipar posible expansión de volatilidad')
            
            elif ultimas_clases == ['FUERTE', 'FUERTE']:
                patron = self.patrones.get('rachas', {}).get('post_2_fuertes', {})
                if patron:
                    prediccion['predicciones'].append({
                        'fuente': 'Racha: 2 días fuertes consecutivos',
                        'prediccion': patron['descripcion'],
                        'probabilidad': f"{patron['probabilidad_lateral']:.0f}%",
                        'confianza': 'MEDIA'
                    })
                    prediccion['tacticas_sugeridas'].append('Esperar consolidación - reducir exposición')
        
        return prediccion
    
    def generar_reporte_predictivo(self):
        """
        Genera reporte con todas las reglas probabilísticas
        
        Returns:
            str: reporte formateado
        """
        if not self.reglas_probabilisticas:
            self.generar_reglas_probabilisticas()
        
        reporte = []
        reporte.append("=" * 80)
        reporte.append("MOTOR PREDICTIVO - REGLAS PROBABILÍSTICAS")
        reporte.append("=" * 80)
        reporte.append("")
        reporte.append("Este reporte contiene patrones históricos que puedes usar para")
        reporte.append("tomar decisiones tácticas basadas en probabilidades.")
        reporte.append("")
        
        # Agrupar reglas por tipo
        reglas_por_tipo = {}
        for regla in self.reglas_probabilisticas:
            tipo = regla['tipo']
            if tipo not in reglas_por_tipo:
                reglas_por_tipo[tipo] = []
            reglas_por_tipo[tipo].append(regla)
        
        # Reglas por día de semana
        if 'DIA_SEMANA' in reglas_por_tipo:
            reporte.append("PATRONES POR DÍA DE SEMANA")
            reporte.append("-" * 80)
            for regla in reglas_por_tipo['DIA_SEMANA']:
                reporte.append(f"\n• {regla['condicion']}")
                reporte.append(f"  Predicción: {regla['prediccion']}")
                reporte.append(f"  Probabilidad: {regla['probabilidad']:.1f}% (Confianza: {regla['confianza']})")
                reporte.append(f"  Táctica sugerida: {regla['tactica']}")
            reporte.append("")
        
        # Reglas por sesión previa
        if 'SESION_PREVIA' in reglas_por_tipo:
            reporte.append("PATRONES POR SESIÓN PREVIA")
            reporte.append("-" * 80)
            for regla in reglas_por_tipo['SESION_PREVIA']:
                reporte.append(f"\n• {regla['condicion']}")
                reporte.append(f"  Predicción: {regla['prediccion']}")
                reporte.append(f"  Probabilidad: {regla['probabilidad']:.1f}% (Confianza: {regla['confianza']})")
                reporte.append(f"  Táctica sugerida: {regla['tactica']}")
            reporte.append("")
        
        # Reglas por rachas
        if 'RACHA' in reglas_por_tipo:
            reporte.append("PATRONES POR RACHAS")
            reporte.append("-" * 80)
            for regla in reglas_por_tipo['RACHA']:
                reporte.append(f"\n• {regla['condicion']}")
                reporte.append(f"  Predicción: {regla['prediccion']}")
                reporte.append(f"  Probabilidad: {regla['probabilidad']:.1f}% (Confianza: {regla['confianza']})")
                reporte.append(f"  Táctica sugerida: {regla['tactica']}")
            reporte.append("")
        
        reporte.append("=" * 80)
        reporte.append("NOTAS IMPORTANTES")
        reporte.append("-" * 80)
        reporte.append("• Estas probabilidades se basan en datos históricos del contrato analizado")
        reporte.append("• Confianza ALTA = Probabilidad ≥ 65% con muestra significativa")
        reporte.append("• Confianza MEDIA = Probabilidad 50-65% o muestra pequeña")
        reporte.append("• Usar como GUÍA, no como verdad absoluta")
        reporte.append("• Combinar con análisis técnico y gestión de riesgo")
        reporte.append("=" * 80)
        
        return "\n".join(reporte)
    
    def exportar_predictor(self, nombre_archivo="predictor_reglas.txt"):
        """
        Exporta reglas predictivas a archivo
        
        Args:
            nombre_archivo: nombre del archivo de salida
        """
        ruta = OUTPUTS_DIR / nombre_archivo
        
        reporte = self.generar_reporte_predictivo()
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"✓ Reglas predictivas exportadas a: {ruta}")


# ==============================================
# FUNCIÓN HELPER
# ==============================================

def generar_predictor_completo(df, clasificaciones, stats_sesiones, exportar=True):
    """
    Genera análisis predictivo completo
    
    Args:
        df: DataFrame con datos procesados
        clasificaciones: DataFrame con clasificaciones
        stats_sesiones: DataFrame con stats de sesiones
        exportar: si exportar resultados
        
    Returns:
        TradingPredictor con análisis completo
    """
    predictor = TradingPredictor(df, clasificaciones, stats_sesiones)
    
    # Ejecutar análisis
    predictor.analizar_patrones_dia_semana()
    predictor.analizar_patron_sesion_previa()
    predictor.analizar_rachas()
    predictor.generar_reglas_probabilisticas()
    
    # Mostrar reporte
    print("\n" + predictor.generar_reporte_predictivo())
    
    # Exportar
    if exportar:
        predictor.exportar_predictor()
    
    return predictor


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el predictor
    """
    from src.ingestion import cargar_datos_procesados
    from src.classifier import DayClassifier
    from src.analytics import SessionAnalytics
    
    # Cargar datos
    df = cargar_datos_procesados("MNQ 03-26.Last_processed.parquet")
    
    if df is not None:
        # Clasificar días
        classifier = DayClassifier(df)
        classifier.calcular_estadisticas_diarias()
        classifier.clasificar_dias()
        
        # Analizar sesiones
        analytics = SessionAnalytics(df, classifier.clasificaciones)
        analytics.calcular_estadisticas_por_sesion()
        
        # Generar predictor
        predictor = generar_predictor_completo(
            df,
            classifier.clasificaciones,
            analytics.stats_sesiones,
            exportar=True
        )
        
        print("\n✓ Predictor generado")
        
        # Ejemplo de predicción contextual
        print("\n" + "="*80)
        print("EJEMPLO: Predicción para HOY")
        print("="*80)
        
        pred_hoy = predictor.predecir_contexto_actual()
        
        print(f"\nFecha: {pred_hoy['fecha']}")
        print(f"Día: {pred_hoy['dia_semana']}")
        print("\nPredicciones:")
        for p in pred_hoy['predicciones']:
            print(f"  • {p['prediccion']} ({p['probabilidad']}) - {p['fuente']}")
        
        if pred_hoy['tacticas_sugeridas']:
            print("\nTácticas sugeridas:")
            for t in pred_hoy['tacticas_sugeridas']:
                print(f"  ✓ {t}")