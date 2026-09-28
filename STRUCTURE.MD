# Estructura del proyecto

## Finalidad

Este fichero describe la estructura vigente del proyecto. Debe leerse antes de crear, mover, modificar o eliminar cualquier fichero o carpeta. Si un cambio altera la estructura, las responsabilidades o los puntos de entrada descritos aquí, este documento debe actualizarse en el mismo cambio.

## Árbol actual

```text
tvb_test/
├── AGENTS.MD
├── README.md
├── STRUCTURE.MD
├── VBT_4-3.MD
├── .gitignore
├── .prompts/                 # Área reservada; prohibido leerla o modificarla
├── .vscode/
│   └── settings.json         # Configuración local del editor y de micromamba
├── 0.sample_code/            # Código externo de referencia; solo lectura
│   └── sinovia/
│       ├── README.md
│       └── Code/
│           ├── evaluate_raw_zerlaut_inverse.py
│           ├── make_final_11dWi_datasets.py
│           ├── make_zerlaut_inverse_dataset.py
│           ├── make_zerlaut_inverse_dataset_multiprotocol.py
│           ├── run_final_11dWi_select_refine.py
│           ├── run_final_11dWi_train_eval.py
│           ├── run_full_final_11dWi_workflow.sh
│           ├── train_transformer_raw_zerlaut_inverse.py
│           ├── zerlaut_adex_meanfield.py
│           └── zerlaut_stimulus_protocols.py
├── conda/
│   └── environment.yml       # Definición reproducible del entorno micromamba
├── config/
│   ├── simulation.json          # Valores usados por el ejemplo
│   └── parameter_ranges.json    # Rangos orientativos, no consumidos por el ejecutable
├── notebooks/
│   └── zerlaut/
│       ├── simulation_step_by_step.ipynb
│       └── visualize_simulation.ipynb
├── src/
│   └── zerlaut/
│       ├── run_simulation.py        # Ejemplo configurable mediante JSON
│       └── run_simulation_simple.py # Ejemplo didáctico con entradas hardcodeadas
└── results/                   # Salidas NPZ generadas; ignoradas por Git
```

## Responsabilidad de cada elemento raíz

- `AGENTS.MD`: instrucciones obligatorias para los agentes que trabajen en este repositorio.
- `README.md`: instrucciones para crear el entorno, ejecutar la simulación y abrir el cuaderno.
- `STRUCTURE.MD`: mapa de la estructura actual y contrato para mantenerla documentada.
- `VBT_4-3.MD`: índice funcional detallado del código de referencia `0.sample_code/sinovia`.
- `.gitignore`: excluye del repositorio principal la carpeta de referencia y el área reservada `.prompts`.
- `.prompts/`: contenido reservado al usuario. Los agentes no deben leer, listar, buscar ni modificar esta carpeta.
- `.vscode/`: configuración local del editor, incluido el uso de micromamba como gestor de entornos.
- `0.sample_code/`: código externo de referencia ignorado por Git y de solo lectura; el proyecto consultado está en `sinovia/`.
- `conda/`: definición del entorno micromamba; `tvb-library` se instala después mediante `pip`.
- `config/`: configuración JSON activa y catálogo independiente de rangos admisibles/orientativos.
- `notebooks/zerlaut/`: cuadernos Jupyter para visualizar la salida configurable y recorrer paso a paso la versión didáctica.
- `src/zerlaut/`: implementación propia; `run_simulation.py` acepta configuración JSON y `run_simulation_simple.py` agrupa entradas hardcodeadas para explicar el flujo mínimo.
- `results/`: directorio generado durante la ejecución. Sus NPZ no se versionan y no deben editarse manualmente.

## Estado funcional del proyecto

La implementación propia contiene dos ejemplos ejecutables de TVB para una única región con el modelo `ZerlautAdaptationFirstOrder`: uno configurable mediante `config/simulation.json` y otro autocontenido con entradas hardcodeadas. Cada run genera un experimento completo en su propio NPZ, con nombres como `results/simulation_run_0.npz` y `results/simple_simulation_run_0.npz`. El cuaderno de visualización puede superponer una o varias runs.

Cuando se añada una implementación propia, deberá situarse fuera de `0.sample_code` y quedar descrita aquí, indicando como mínimo:

- finalidad de cada directorio de primer nivel;
- puntos de entrada y módulos principales;
- ubicación de pruebas, configuración, datos y resultados;
- relaciones importantes entre componentes;
- elementos generados que no deban editarse manualmente.

## Reglas para mantener este mapa

1. Leer `STRUCTURE.MD` antes de modificar la estructura o los ficheros del proyecto.
2. No usar `0.sample_code` como destino de código nuevo ni modificar nada en su interior.
3. No acceder a `.prompts` bajo ninguna circunstancia.
4. Actualizar este fichero en el mismo cambio que añada, elimine, mueva o cambie sustancialmente la función de un elemento documentado.
5. Mantener el árbol conciso: deben figurar los ficheros mantenidos por el proyecto, no cachés ni artefactos temporales.
