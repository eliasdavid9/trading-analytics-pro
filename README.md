# Trading Analytics

Sistema de análisis estadístico y probabilístico para futuros (MNQ, NQ, etc.).

## Objetivo

Desarrollar un conocimiento profundo del mercado mediante estadísticas y probabilidades para:
- Determinar cuándo dejar correr un trade vs hacer scalping
- Predecir qué sesión tendrá más fortaleza en determinado día
- Optimizar la estrategia de trading según contexto estadístico

## Estructura del Proyecto

```
trading_analytics/
├── data/
│   ├── raw/              # Datos originales de NinjaTrader (.txt)
│   └── processed/        # Datos procesados (.parquet)
├── src/
│   ├── ingestion.py      # Parser y validación de datos
│   ├── classifier.py     # Clasificación de días
│   ├── analytics.py      # Motor estadístico de sesiones
│   └── __init__.py
├── outputs/              # Reportes generados
├── config.py             # Configuración centralizada
├── main.py               # ⭐ SCRIPT PRINCIPAL (usar este)
└── README.md             # Este archivo
```

## Instalación

### Dependencias

```bash
pip install pandas pyarrow
```

## Uso Rápido (Recomendado)

### Método 1: Script Principal Automatizado

```bash
python main.py
```

Este script:
1. Te muestra todos los archivos .txt disponibles en `data/raw/`
2. Seleccionás el que querés analizar
3. Ejecuta TODO el pipeline automáticamente:
   - Ingestion y validación
   - Clasificación de días
   - Análisis de sesiones
   - Genera reporte consolidado
4. Guarda todos los resultados en `outputs/`

**¡Solo copiá tus archivos .txt a `data/raw/` y ejecutá `main.py`!**

### Método 2: Uso Manual (avanzado)

Si querés ejecutar pasos individuales:

#### 1. Procesar datos raw

```python
from src.ingestion import DataIngestion

parser = DataIngestion("data/raw/MNQ 03-26.Last.txt")
df = parser.procesar(guardar=True, mostrar_resumen=True)
```

#### 2. Clasificar días

```python
from src.classifier import analizar_archivo

classifier = analizar_archivo("MNQ 03-26.Last_processed.parquet")
```

#### 3. Analizar sesiones

```python
from src.analytics import analizar_sesiones_completo

analytics = analizar_sesiones_completo(df, clasificaciones)
```

## Configuración

Edita `config.py` para ajustar:
- Horarios de sesiones (ASIA, EUROPA, NY)
- Criterios de clasificación de días
- Parámetros de validación
- Formato de reportes

## Workflow Típico

1. **Exportar datos desde NinjaTrader8** al finalizar el contrato
2. **Copiar archivo .txt** a `data/raw/`
3. **Ejecutar** `python main.py`
4. **Seleccionar** el archivo a analizar
5. **Revisar reportes** en `outputs/`

## Outputs Generados

Para cada análisis se generan:
- `clasificaciones_[nombre].txt` - Clasificación de días con métricas
- `clasificaciones_[nombre].csv` - Versión CSV para Excel
- `analisis_sesiones_[nombre].txt` - Análisis profundo de sesiones
- `REPORTE_CONSOLIDADO_[nombre].txt` - Reporte ejecutivo completo

## Roadmap

- [x] Módulo de ingestion con validaciones
- [x] Clasificador inteligente de días
- [x] Análisis de sesiones y patrones
- [x] Pipeline automatizado (main.py)
- [ ] Motor probabilístico predictivo
- [ ] Dashboard operativo en tiempo real

## Notas

- El sistema detecta automáticamente todos los archivos en `data/raw/`
- Podés tener múltiples contratos y analizar el que quieras
- Los datos procesados se reutilizan (no hace falta reprocesar)
- Todos los reportes se guardan con el nombre del archivo para no sobreescribir

---
**Desarrollado con Claude** - Sistema modular y escalable