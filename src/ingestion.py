"""
Módulo de ingestion de datos
Parsea archivos raw de NinjaTrader y valida integridad
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import pytz

# Importar configuración
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    FORMATO_ENTRADA, 
    VALIDACIONES, 
    SESIONES,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    ZONA_HORARIA_DATOS,
    ZONA_HORARIA_REFERENCIA,
    obtener_horarios_sesion_et
)


class DataIngestion:
    """
    Clase para parsear y validar datos de trading
    """
    
    def __init__(self, archivo_path):
        """
        Inicializa el parser
        
        Args:
            archivo_path: Path al archivo .txt con datos raw
        """
        self.archivo_path = Path(archivo_path)
        self.df = None
        self.errores = []
        self.warnings = []
        
    def cargar_datos(self):
        """
        Carga datos desde archivo raw
        
        Returns:
            DataFrame con datos cargados o None si falla
        """
        try:
            # Leer archivo
            self.df = pd.read_csv(
                self.archivo_path,
                sep=FORMATO_ENTRADA["separador"],
                names=FORMATO_ENTRADA["columnas"],
                parse_dates=["datetime"],
                date_format=FORMATO_ENTRADA["formato_fecha"]
            )
            
            print(f"✓ Archivo cargado: {len(self.df)} registros")
            return True
            
        except FileNotFoundError:
            self.errores.append(f"Archivo no encontrado: {self.archivo_path}")
            return False
        except Exception as e:
            self.errores.append(f"Error al cargar datos: {str(e)}")
            return False
    
    def validar_datos(self):
        """
        Ejecuta validaciones de integridad sobre los datos
        
        Returns:
            bool: True si pasa validaciones, False si hay errores críticos
        """
        if self.df is None:
            self.errores.append("No hay datos cargados para validar")
            return False
        
        validacion_ok = True
        
        # 1. Verificar valores nulos
        nulos = self.df.isnull().sum()
        if nulos.any():
            self.warnings.append(f"Valores nulos encontrados:\n{nulos[nulos > 0]}")
        
        # 2. Verificar rangos de precios
        for col in ['open', 'high', 'low', 'close']:
            min_val = self.df[col].min()
            max_val = self.df[col].max()
            
            if min_val < VALIDACIONES["precio_min"]:
                self.errores.append(f"{col}: precio mínimo ({min_val}) fuera de rango")
                validacion_ok = False
                
            if max_val > VALIDACIONES["precio_max"]:
                self.errores.append(f"{col}: precio máximo ({max_val}) fuera de rango")
                validacion_ok = False
        
        # 3. Verificar volumen
        vol_negativo = (self.df['volume'] < VALIDACIONES["volumen_min"]).sum()
        if vol_negativo > 0:
            self.errores.append(f"{vol_negativo} registros con volumen negativo")
            validacion_ok = False
        
        # 4. Verificar High >= Low
        if VALIDACIONES["check_high_low"]:
            invalidos = self.df[self.df['high'] < self.df['low']]
            if len(invalidos) > 0:
                self.errores.append(f"{len(invalidos)} velas con High < Low")
                validacion_ok = False
        
        # 5. Verificar OHLC consistencia
        if VALIDACIONES["check_ohlc"]:
            # Open y Close deben estar entre High y Low
            invalidos_open = self.df[
                (self.df['open'] > self.df['high']) | 
                (self.df['open'] < self.df['low'])
            ]
            invalidos_close = self.df[
                (self.df['close'] > self.df['high']) | 
                (self.df['close'] < self.df['low'])
            ]
            
            if len(invalidos_open) > 0:
                self.errores.append(f"{len(invalidos_open)} velas con Open fuera de rango H/L")
                validacion_ok = False
                
            if len(invalidos_close) > 0:
                self.errores.append(f"{len(invalidos_close)} velas con Close fuera de rango H/L")
                validacion_ok = False
        
        # 6. Verificar duplicados de timestamp
        duplicados = self.df[self.df.duplicated(subset=['datetime'], keep=False)]
        if len(duplicados) > 0:
            self.warnings.append(f"{len(duplicados)} timestamps duplicados encontrados")
        
        # 7. Verificar gaps temporales (velas faltantes)
        self.df = self.df.sort_values('datetime').reset_index(drop=True)
        diferencias = self.df['datetime'].diff()
        # Asumimos velas de 1 minuto
        gaps = diferencias[diferencias > pd.Timedelta(minutes=5)]
        if len(gaps) > 0:
            self.warnings.append(f"{len(gaps)} gaps temporales detectados (>5 min)")
        
        return validacion_ok
    
    def enriquecer_datos(self):
        """
        Agrega columnas calculadas útiles para análisis
        INCLUYE CONVERSIÓN DE ZONA HORARIA A ET (hora NY)
        """
        if self.df is None:
            return
        
        # PASO 1: Convertir timestamps a hora de Nueva York (ET)
        try:
            # Localizar timestamps en la zona horaria de los datos
            tz_datos = pytz.timezone(ZONA_HORARIA_DATOS)
            tz_ny = pytz.timezone(ZONA_HORARIA_REFERENCIA)
            
            # Si los datos no tienen timezone, asignarla
            if self.df['datetime'].dt.tz is None:
                self.df['datetime'] = self.df['datetime'].dt.tz_localize(tz_datos)
            
            # Convertir a hora de Nueva York
            self.df['datetime'] = self.df['datetime'].dt.tz_convert(tz_ny)
            
            # Quitar timezone info para facilitar operaciones posteriores
            self.df['datetime'] = self.df['datetime'].dt.tz_localize(None)
            
            print(f"✓ Timestamps convertidos de {ZONA_HORARIA_DATOS} a {ZONA_HORARIA_REFERENCIA}")
            
        except Exception as e:
            print(f"⚠ Advertencia al convertir zona horaria: {str(e)}")
            print("  Continuando con timestamps originales...")
        
        # PASO 2: Extraer componentes de fecha (ahora en hora NY)
        self.df['fecha'] = self.df['datetime'].dt.date
        self.df['hora'] = self.df['datetime'].dt.time
        self.df['dia_semana'] = self.df['datetime'].dt.day_name()
        self.df['dia_mes'] = self.df['datetime'].dt.day
        self.df['mes'] = self.df['datetime'].dt.month
        self.df['año'] = self.df['datetime'].dt.year
        
        # Calcular rango de cada vela
        self.df['rango'] = self.df['high'] - self.df['low']
        
        # Identificar sesión (ahora basado en hora NY)
        self.df['sesion'] = self.df['datetime'].apply(self._identificar_sesion)
        
        print("✓ Datos enriquecidos con columnas adicionales")
    
    def _identificar_sesion(self, timestamp):
        """
        Identifica a qué sesión pertenece un timestamp
        USA HORARIOS DE NUEVA YORK (ET) - ya convertidos
        
        Args:
            timestamp: datetime (ya en hora NY)
            
        Returns:
            str: nombre de la sesión (ASIA, EUROPA, NY)
        """
        # Obtener horarios de sesión en ET
        sesiones = obtener_horarios_sesion_et(timestamp)
        
        hora_str = timestamp.strftime("%H:%M")
        
        # Caso especial: sesión ASIA cruza medianoche (19:00 → 04:00)
        # Si hora >= 19:00, es ASIA del día actual
        # Si hora < 04:00, es ASIA del día anterior (continuación)
        
        if sesiones["ASIA"]["inicio"] <= hora_str or hora_str < sesiones["ASIA"]["fin"]:
            return "ASIA"
        elif sesiones["EUROPA"]["inicio"] <= hora_str < sesiones["EUROPA"]["fin"]:
            return "EUROPA"
        elif sesiones["NY"]["inicio"] <= hora_str < sesiones["NY"]["fin"]:
            return "NY"
        else:
            # Horario entre cierre NY (17:00) y apertura ASIA (19:00)
            return "NY"  # Post-market, considerado NY
    
    def guardar_procesado(self, nombre_salida=None):
        """
        Guarda datos procesados en formato parquet (más eficiente que CSV)
        
        Args:
            nombre_salida: nombre del archivo de salida (sin extensión)
        """
        if self.df is None:
            print("⚠ No hay datos para guardar")
            return
        
        if nombre_salida is None:
            nombre_salida = self.archivo_path.stem + "_processed"
        
        ruta_salida = PROCESSED_DATA_DIR / f"{nombre_salida}.parquet"
        
        try:
            self.df.to_parquet(ruta_salida, index=False)
            print(f"✓ Datos guardados en: {ruta_salida}")
        except Exception as e:
            self.errores.append(f"Error al guardar: {str(e)}")
    
    def mostrar_resumen(self):
        """
        Muestra resumen de los datos cargados
        """
        if self.df is None:
            print("⚠ No hay datos cargados")
            return
        
        print("\n" + "="*60)
        print("RESUMEN DE DATOS CARGADOS")
        print("="*60)
        print(f"Archivo: {self.archivo_path.name}")
        print(f"Total registros: {len(self.df):,}")
        print(f"Rango fechas: {self.df['datetime'].min()} → {self.df['datetime'].max()}")
        print(f"Días únicos: {self.df['fecha'].nunique()}")
        print(f"\nPrecio - Min: {self.df['low'].min():.2f} | Max: {self.df['high'].max():.2f}")
        print(f"Volumen total: {self.df['volume'].sum():,}")
        
        print(f"\n{'Distribución por sesión:'}")
        print(self.df['sesion'].value_counts().sort_index())
        
        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")
        
        if self.errores:
            print(f"\n✗ ERRORES ({len(self.errores)}):")
            for e in self.errores:
                print(f"  - {e}")
        else:
            print("\n✓ Todas las validaciones pasaron correctamente")
        
        print("="*60 + "\n")
    
    def procesar(self, guardar=True, mostrar_resumen=True):
        """
        Pipeline completo de procesamiento
        
        Args:
            guardar: si guardar datos procesados
            mostrar_resumen: si mostrar resumen en consola
            
        Returns:
            DataFrame procesado o None si falla
        """
        # 1. Cargar
        if not self.cargar_datos():
            print("✗ Fallo al cargar datos")
            return None
        
        # 2. Validar
        if not self.validar_datos():
            print("✗ Validación falló - revisa errores")
            return None
        
        # 3. Enriquecer
        self.enriquecer_datos()
        
        # 4. Guardar (opcional)
        if guardar:
            self.guardar_procesado()
        
        # 5. Mostrar resumen (opcional)
        if mostrar_resumen:
            self.mostrar_resumen()
        
        return self.df


def cargar_datos_procesados(nombre_archivo):
    """
    Función helper para cargar datos ya procesados
    
    Args:
        nombre_archivo: nombre del archivo parquet (con o sin extensión)
        
    Returns:
        DataFrame o None si no existe
    """
    if not nombre_archivo.endswith('.parquet'):
        nombre_archivo += '.parquet'
    
    ruta = PROCESSED_DATA_DIR / nombre_archivo
    
    if not ruta.exists():
        print(f"✗ Archivo no encontrado: {ruta}")
        return None
    
    try:
        df = pd.read_parquet(ruta)
        print(f"✓ Cargados {len(df):,} registros desde {ruta.name}")
        return df
    except Exception as e:
        print(f"✗ Error al cargar: {str(e)}")
        return None


# ==============================================
# EJEMPLO DE USO
# ==============================================
if __name__ == "__main__":
    """
    Script de ejemplo para probar el módulo
    """
    # Ejemplo: procesar un archivo
    archivo = RAW_DATA_DIR / "MNQ 03-26.Last.txt"
    
    parser = DataIngestion(archivo)
    df = parser.procesar(guardar=True, mostrar_resumen=True)
    
    if df is not None:
        print("\n✓ Pipeline de ingestion completado exitosamente")
        print(f"DataFrame resultante: {df.shape}")
