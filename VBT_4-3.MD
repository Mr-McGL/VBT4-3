# Guía del código de referencia `vbt_t4-3`

## Propósito de esta guía

Este documento es el índice de consulta del directorio `vbt_t4-3`. Su objetivo es permitir localizar rápidamente conceptos, responsabilidades, entradas y salidas sin tener que recorrer el código de referencia a ciegas.

> Nota sobre el nombre: la carpeta existente en el proyecto se llama `vbt_t4-3` (con `t`), aunque en algunos requisitos se la denomine `vbt_4-3`.

`vbt_t4-3` es un repositorio de referencia autocontenido. Implementa y documenta un experimento de calibración inversa de un modelo de campo medio Zerlaut-AdEx: a partir de actividad excitatoria/inhibitoria y del estímulo, un Transformer estima 11 parámetros; después se valida si esos parámetros reconstruyen la dinámica al volver a ejecutar el simulador directo.

La configuración final usa 1000 simulaciones (700 entrenamiento, 150 validación y 150 prueba), cuatro representaciones de la señal y una selección final basada en la calidad de reconstrucción directa.

## Mapa rápido del flujo

```text
ZerlautParams + protocolos de estímulo
                │
                ▼
 simulación Zerlaut-AdEx de una región
                │
                ▼
 shards HDF5 crudos (E, I, estímulo, parámetros)
                │
                ├── representación raw (3 canales)
                ├── aug9 (9 canales)
                ├── aug12 (12 canales)
                └── aug12_stable (12 canales estables)
                │
                ▼
 cuatro Transformers de regresión inversa
                │
                ▼
 predicción de parámetros + re-simulación directa
                │
                ▼
 Best-of-4 + refinado local + selección segura
```

## Dónde buscar según la necesidad

| Si se necesita entender... | Consultar primero... |
|---|---|
| Objetivo, resultado final y modo de ejecución | `README.md` |
| Ecuaciones, parámetros, unidades y simulación directa Zerlaut-AdEx | `Code/zerlaut_adex_meanfield.py` |
| Tipos de estímulo, canales derivados y resúmenes de respuesta | `Code/zerlaut_stimulus_protocols.py` |
| Generación HDF5 básica y rangos de parámetros | `Code/make_zerlaut_inverse_dataset.py` |
| Generación final con varios protocolos y objetivos auxiliares | `Code/make_zerlaut_inverse_dataset_multiprotocol.py` |
| Construcción de las cuatro variantes del dataset final | `Code/make_final_11dWi_datasets.py` |
| Dataset PyTorch, normalización, arquitectura Transformer y entrenamiento | `Code/train_transformer_raw_zerlaut_inverse.py` |
| Métricas de parámetros y reconstrucción mediante re-simulación | `Code/evaluate_raw_zerlaut_inverse.py` |
| Configuración de las cuatro candidaturas de entrenamiento | `Code/run_final_11dWi_train_eval.py` |
| Selección Best-of-4, detección de colapsos y refinado de casos difíciles | `Code/run_final_11dWi_select_refine.py` |
| Flujo completo en SLURM/JUWELS, recursos y comprobaciones finales | `Code/run_full_final_11dWi_workflow.sh` |
| Archivos generados que quedan fuera de Git | `.gitignore` |

## Contenido de cada fichero

### `README.md`

Resumen ejecutivo del experimento final. Contiene:

- el objetivo científico: comprobar si los parámetros inferidos son útiles dinámicamente;
- la configuración final de 1000 muestras y 11 parámetros;
- las métricas históricas sobre las 150 muestras de prueba;
- la orden de lanzamiento con `sbatch` y el tiempo estimado en JUWELS;
- una lista breve de los scripts principales.

Es el mejor punto de entrada para comprender qué intenta demostrar el repositorio, pero no describe los contratos HDF5 ni todos los detalles internos.

### `.gitignore`

Excluye cachés de Python y artefactos pesados o regenerables: `data/`, `results_zerlaut_inverse/`, `logs/`, ficheros HDF5, checkpoints PyTorch y salidas de SLURM. Por eso el repositorio de referencia contiene código y documentación, pero no los datasets, modelos ni resultados completos mencionados por los scripts.

### `Code/zerlaut_adex_meanfield.py`

Núcleo de simulación directa. Contiene:

- `ZerlautParams`, dataclass con parámetros biofísicos, sinápticos, de conectividad, adaptación y coeficientes de las funciones de transferencia excitatoria e inhibitoria;
- `ZerlautMeanField`, que calcula variables del régimen de fluctuaciones, umbrales efectivos, tasas de disparo y el lado derecho de las ecuaciones E/I con adaptación;
- integración temporal por Euler o Heun de `E`, `I`, `W_e` y `W_i`;
- límites defensivos para tasas, adaptación y valores no finitos;
- `simulate_zerlaut_single_region`, API cómoda que acepta parámetros como dataclass o diccionario y entradas externas escalares o temporales.

Convenciones importantes: las entradas externas y las tasas E/I están en Hz; el tiempo está en ms; la función pública devuelve `t_grid`, `E`, `I` y `W_e`. Aunque internamente también se integra `W_i`, la API pública no lo devuelve.

### `Code/zerlaut_stimulus_protocols.py`

Biblioteca de estímulos y extracción de características. Contiene:

- protocolos `constant`, `step`, `pulse`, `slow_ramp`, `double_pulse`, `recovery`, `sine` y `ou_like`;
- la selección aleatoria de protocolos y generación de ruido suavizado;
- la lista de protocolos centrados en adaptación;
- construcción de canales directos y derivados: E, I, estímulo, entradas Fe/Fi, adaptación W, derivadas, diferencias y cocientes E/I, medias móviles y transformaciones logarítmicas;
- estadísticas globales y temporales de respuesta: medias, desviaciones, máximos, respuesta temprana/tardía, índice de adaptación, recuperación y pendiente de decaimiento;
- conversión de esos resúmenes a un vector de objetivos auxiliares.

Es el lugar apropiado para localizar la semántica exacta de un protocolo o de un canal derivado.

### `Code/make_zerlaut_inverse_dataset.py`

Generador base de shards HDF5 para calibración inversa. Contiene:

- conjuntos de parámetros `six`, `eleven_inhibitory` y `extended`;
- cotas predeterminadas, parámetros muestreados en escala logarítmica y parámetros enteros;
- validación de la cuadrícula temporal y promediado por bins;
- estímulos sintéticos (`constant`, `step`, `multi_step`, `pulse`, `ramp`, `sine`, `ou_like`) o carga de plantillas desde CSV/HDF5;
- muestreo de parámetros, ejecución del simulador y filtros de aceptación;
- escritura atómica de `signals`, `params` y `sample_stats`, atributos descriptivos y, opcionalmente, un manifiesto JSON.

Contrato HDF5 básico:

- `signals`: `(muestras, bins temporales, canales)`;
- `params`: `(muestras, parámetros)`;
- `sample_stats`: media, desviación y máximo de E e I;
- atributos como `param_names`, `channels`, `dt_ms`, `bin_ms`, `method`, convención de estímulo y manifiesto.

La convención de entrada es `Fe_ext(t) = scale * stim(t)` y `Fi_ext(t) = Fi_ratio * Fe_ext(t)`.

### `Code/make_zerlaut_inverse_dataset_multiprotocol.py`

Especialización del generador para el dataset final multiprotocolo. Reutiliza el simulador, las cotas y utilidades del generador base, y añade:

- conjuntos `four`, `eleven_inhibitory` y `twelve_synaptic`;
- elección explícita entre varios protocolos de estímulo;
- filtros adicionales sobre variabilidad y media inhibitoria;
- todos los canales derivados definidos en `zerlaut_stimulus_protocols.py`;
- datasets HDF5 adicionales `aux_targets` y `protocol_idx`;
- metadatos con nombres de protocolos y objetivos auxiliares.

Es el generador que usa el flujo final de 11 parámetros (`scale`, `Fi_ratio`, `g`, `b_e`, `tau_w_e`, `T`, `a_i`, `b_i`, `tau_w_i`, `Q_i`, `tau_i`).

### `Code/make_final_11dWi_datasets.py`

Prepara las cuatro vistas finales del mismo conjunto de simulaciones:

- `raw`: E, I y estímulo;
- `aug9`: añade derivadas, diferencia E-I, cociente I/E y medias móviles;
- `aug12`: añade además log(E), log(I) y log(estímulo);
- `aug12_stable`: sustituye el potencialmente inestable `I_over_E` por `logI_minus_logE`.

Si no existe el dataset crudo, lanza el generador multiprotocolo en varios shards. Después copia parámetros, datasets auxiliares y atributos a las variantes aumentadas. Sus opciones permiten forzar la regeneración del crudo o de los aumentados. Las rutas de `data/` están fijadas como constantes al principio del fichero.

### `Code/train_transformer_raw_zerlaut_inverse.py`

Implementación completa del entrenamiento inverso con PyTorch. Contiene:

- `H5SignalDataset`, que reúne varios shards, valida que canales/parámetros/longitud temporal sean compatibles y abre los HDF5 de forma diferida;
- expansión de rutas, directorios y patrones glob;
- partición reproducible en entrenamiento, validación y prueba;
- `Standardizer` y cálculo de estadísticas sólo con el conjunto de entrenamiento;
- `RawSignalTransformerRegressor`: proyección lineal, codificación posicional sinusoidal, encoder Transformer, pooling mediante token CLS o media y cabeza de regresión;
- entrenamiento con AdamW, MSE sobre variables normalizadas, recorte de gradiente, AMP opcional y parada temprana;
- métricas RMSE, MAE y R² por parámetro.

Salidas principales: `raw_zerlaut_inverse_transformer.pt` (pesos, hiperparámetros, escaladores y splits), `raw_zerlaut_inverse_metrics.json`, `training_history.json` y, opcionalmente, `test_predictions_original_units.csv`.

### `Code/evaluate_raw_zerlaut_inverse.py`

Evalúa un checkpoint tanto en el espacio de parámetros como en el espacio dinámico. Contiene:

- carga y reconstrucción del modelo guardado;
- selección de split y predicción en unidades originales;
- exportación de valores reales, predichos y errores por parámetro;
- RMSE, MAE y R² por objetivo;
- conversión de parámetros predichos a `ZerlautParams` y re-simulación del modelo directo;
- métricas de reconstrucción E/I: correlación, NMSE y medias;
- generación opcional de gráficos superpuestos.

Salidas principales: `parameter_predictions.csv`, `parameter_metrics.json`, `reconstruction_metrics.csv` y el directorio opcional `overlays/`.

### `Code/run_final_11dWi_train_eval.py`

Orquestador de las cuatro candidaturas finales: `Wi_raw`, `Wi_aug9`, `Wi_aug12` y `Wi_aug12_stable`. Para cada una:

- elige el patrón HDF5 y la lista exacta de canales;
- lanza el script de entrenamiento con un split 70/15/15 y una arquitectura fijada;
- lanza la evaluación sobre las 150 muestras de prueba y solicita su reconstrucción directa;
- evita repetir trabajos terminados, salvo que se indiquen `--force_train` o `--force_eval`;
- permite ejecutar sólo un subconjunto o imprimir las órdenes con `--dry_run`.

Este fichero es donde buscar la configuración comparable de los cuatro Transformers.

### `Code/run_final_11dWi_select_refine.py`

Realiza la selección y el refinado final. Contiene:

- lectura y unión de las predicciones y métricas de reconstrucción de las cuatro candidaturas;
- cálculo de `mean_nmse` y penalización fuerte de reconstrucciones colapsadas;
- selección por muestra del mejor candidato (Best-of-4);
- obtención de cotas de búsqueda a partir de los parámetros presentes en los HDF5;
- búsqueda local aleatoria multietapa, paralelizada, para casos cuyo NMSE supera el umbral;
- una segunda búsqueda sensible a correlación para los peores casos restantes;
- regla segura que sólo acepta esa segunda propuesta si mejora NMSE y no colapsa la actividad;
- resúmenes antes/después y listados detallados en CSV.

La salida final de referencia es `selected_11dWi_bestof4_safe_refined_candidates.csv`; el resumen agregado es `safe_final_summary.csv`.

### `Code/run_full_final_11dWi_workflow.sh`

Punto de entrada de extremo a extremo para SLURM en JUWELS. Contiene:

- directivas de recursos (8 CPU, 32 GB, partición `batch`, límite de 5 h 20 min);
- ruta absoluta de despliegue y módulos del entorno HPC;
- comprobación de que todos los scripts requeridos existen;
- creación/verificación de datasets y sus dimensiones;
- limpieza acotada de resultados de este flujo final;
- entrenamiento y evaluación de las cuatro candidaturas;
- selección/refinado final;
- comprobaciones reproducibles y tolerantes sobre número de casos y calidad NMSE.

Este script contiene órdenes destructivas `rm -rf` dirigidas a directorios de resultados concretos. Es código de referencia y no debe ejecutarse fuera del entorno previsto ni copiarse sin revisar sus rutas, módulos y efectos.

## Dependencias y artefactos externos

El código usa Python 3 y, según la etapa, NumPy, SciPy, pandas, h5py, PyTorch y Matplotlib. El lanzador completo presupone SLURM, módulos de JUWELS y una ruta absoluta propia de ese sistema.

Los directorios `data/`, `results_zerlaut_inverse/` y `logs/` no están incluidos. Se crean durante la ejecución y se ignoran en Git. Por tanto, cualquier referencia a shards, checkpoints, CSV de evaluación, imágenes o logs describe artefactos esperados, no ficheros actualmente presentes en esta copia.

## Relación entre módulos

- `make_zerlaut_inverse_dataset_multiprotocol.py` importa utilidades del generador base y de los protocolos.
- Ambos generadores dependen de `zerlaut_adex_meanfield.py` para producir E/I.
- `make_final_11dWi_datasets.py` llama al generador multiprotocolo y produce las variantes de canales.
- `train_transformer_raw_zerlaut_inverse.py` consume los HDF5.
- `evaluate_raw_zerlaut_inverse.py` reutiliza el dataset y el modelo del entrenador, y el simulador directo.
- `run_final_11dWi_train_eval.py` llama al entrenador y al evaluador cuatro veces.
- `run_final_11dWi_select_refine.py` consume sus CSV y reutiliza la re-simulación del evaluador.
- `run_full_final_11dWi_workflow.sh` coordina todas las etapas y verifica el resultado.

