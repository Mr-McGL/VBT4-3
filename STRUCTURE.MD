# Estructura del proyecto

## Finalidad

Este fichero describe la estructura vigente del proyecto. Debe leerse antes de crear, mover, modificar o eliminar cualquier fichero o carpeta. Si un cambio altera la estructura, las responsabilidades o los puntos de entrada descritos aquí, este documento debe actualizarse en el mismo cambio.

## Árbol actual

```text
tvb_test/
├── AGENTS.MD
├── STRUCTURE.MD
├── VBT_4-3.MD
├── .gitignore
├── .prompts/                 # Área reservada; prohibido leerla o modificarla
├── .vscode/                  # Configuración local del editor; actualmente sin ficheros
└── vbt_t4-3/                 # Repositorio de referencia de solo lectura
    ├── README.md
    └── Code/
        ├── evaluate_raw_zerlaut_inverse.py
        ├── make_final_11dWi_datasets.py
        ├── make_zerlaut_inverse_dataset.py
        ├── make_zerlaut_inverse_dataset_multiprotocol.py
        ├── run_final_11dWi_select_refine.py
        ├── run_final_11dWi_train_eval.py
        ├── run_full_final_11dWi_workflow.sh
        ├── train_transformer_raw_zerlaut_inverse.py
        ├── zerlaut_adex_meanfield.py
        └── zerlaut_stimulus_protocols.py
```

## Responsabilidad de cada elemento raíz

- `AGENTS.MD`: instrucciones obligatorias para los agentes que trabajen en este repositorio.
- `STRUCTURE.MD`: mapa de la estructura actual y contrato para mantenerla documentada.
- `VBT_4-3.MD`: índice funcional detallado del código de referencia `vbt_t4-3`.
- `.gitignore`: excluye del repositorio principal la carpeta de referencia y el área reservada `.prompts`.
- `.prompts/`: contenido reservado al usuario. Los agentes no deben leer, listar, buscar ni modificar esta carpeta.
- `.vscode/`: espacio para configuración local del editor. Actualmente está vacío y no forma parte de la lógica del proyecto.
- `vbt_t4-3/`: snapshot/repo de referencia. Puede consultarse, siguiendo primero `VBT_4-3.MD`, pero nunca modificarse.

## Estado funcional del proyecto

En este momento no hay una implementación propia fuera de `vbt_t4-3`; la raíz contiene únicamente reglas y documentación. El código ejecutable disponible es material de referencia y no debe convertirse implícitamente en el código activo del proyecto.

Cuando se añada una implementación propia, deberá situarse fuera de `vbt_t4-3` y quedar descrita aquí, indicando como mínimo:

- finalidad de cada directorio de primer nivel;
- puntos de entrada y módulos principales;
- ubicación de pruebas, configuración, datos y resultados;
- relaciones importantes entre componentes;
- elementos generados que no deban editarse manualmente.

## Reglas para mantener este mapa

1. Leer `STRUCTURE.MD` antes de modificar la estructura o los ficheros del proyecto.
2. No usar `vbt_t4-3` como destino de código nuevo ni modificar nada en su interior.
3. No acceder a `.prompts` bajo ninguna circunstancia.
4. Actualizar este fichero en el mismo cambio que añada, elimine, mueva o cambie sustancialmente la función de un elemento documentado.
5. Mantener el árbol conciso: deben figurar los ficheros mantenidos por el proyecto, no cachés ni artefactos temporales.

