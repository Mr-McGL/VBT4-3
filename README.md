# Ejemplo TVB de una sola región

Este proyecto ejecuta una simulación de una única región con el modelo de campo
medio `ZerlautAdaptationFirstOrder` de TVB. La configuración completa se lee de
JSON y el resultado se guarda como un fichero binario NumPy `.npz`, que puede
abrirse sin una base de datos ni el framework web de TVB.

El ejemplo sigue las convenciones del código de referencia:

- las tasas y entradas externas del JSON están expresadas en Hz;
- `Fe_ext(t) = scale * stimulus(t)`;
- `Fi_ext(t) = Fi_ratio * Fe_ext(t)`;
- el tiempo está expresado en ms;
- las tasas internas de TVB, expresadas en kHz, se convierten a Hz al guardar.

## Preparación del entorno

```bash
micromamba create -f conda/environment.yml
micromamba activate tvb
python -m pip install tvb-library==2.10.0
```

## Ejecución

```bash
python src/zerlaut/run_simulation.py --config config/simulation.json
```

El resultado se guarda en `results/simulation.npz`. Puede cambiarse la ruta
sin editar el JSON:

```bash
python src/zerlaut/run_simulation.py \
  --config config/simulation.json \
  --output results/otra_simulacion.npz
```

El `.npz` contiene `time_ms`, `E_hz`, `I_hz`, `W_e_pA`, `W_i_pA`,
`stimulus_hz`, `Fe_ext_hz`, `Fi_ext_hz` y `metadata_json`. Se carga con
`numpy.load`; no necesita `pickle`.

Las unidades de las series son:

- `time_ms`: milisegundos (ms).
- `E_hz`, `I_hz`, `stimulus_hz`, `Fe_ext_hz` y `Fi_ext_hz`: hercios (Hz).
- `W_e_pA` y `W_i_pA`: picoamperios (pA).

### Versión didáctica sin JSON

`src/zerlaut/run_simulation_simple.py` contiene las entradas como constantes al
principio del fichero y sólo implementa un pulso, una región y el integrador de
Heun. No lee configuración ni datos externos:

```bash
python src/zerlaut/run_simulation_simple.py
```

El resultado es `results/simple_simulation.npz`. El cuaderno
`notebooks/zerlaut/simulation_step_by_step.ipynb` reconstruye el mismo proceso en
etapas comentadas.

## Configuración

- `config/simulation.json`: valores utilizados por el ejemplo, incluido el
  tipo de estímulo.
- `config/parameter_ranges.json`: rangos orientativos inspirados en el proyecto
  de referencia. Es documentación legible por máquinas y el ejecutable no lo
  consume.

Los tipos de estímulo admitidos son `constant`, `step`, `pulse`, `slow_ramp`,
`double_pulse`, `recovery`, `sine` y `ou_like`. Los campos que no necesita un
tipo concreto pueden permanecer en el JSON y se ignoran.

## Visualización

Después de ejecutar la simulación:

```bash
jupyter lab notebooks/zerlaut/visualize_simulation.ipynb
```

Ejecute este comando desde la raíz del repositorio para que el cuaderno localice
los resultados. La lista `RESULT_FILES` permite mostrar uno o varios ficheros
en las mismas gráficas.

## Conectividad y ficheros externos

Ninguno de los dos scripts carga un fichero de conectividad. Al haber una sola
región, se pasa al modelo un tensor de acoplamiento lleno de ceros con forma
`(1, 1, 1)`.

El ejemplo configurable sólo lee `config/simulation.json`. El fichero
`config/parameter_ranges.json` sirve como documentación y no se abre durante
la simulación. La versión didáctica no lee ningún fichero del proyecto; su única
dependencia externa es el módulo Python de TVB, que se instala por separado
después de crear el entorno definido en `conda/environment.yml`.
