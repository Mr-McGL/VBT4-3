# Instrucciones para agentes

Estas reglas son obligatorias para cualquier agente que trabaje en este repositorio.

## Orden de lectura antes de actuar

1. Leer `STRUCTURE.MD` antes de crear, modificar, mover o eliminar cualquier fichero o carpeta.
2. Si la tarea guarda relación con el código de referencia, leer `VBT_4-3.MD` antes de consultar `0.sample_code/sinovia`.
3. Usar `VBT_4-3.MD` para localizar el fichero concreto que contiene la información buscada. No recorrer ni buscar directamente por toda la carpeta `0.sample_code/sinovia` como primer método de investigación.
4. Una vez localizado el fichero mediante la guía, puede leerse el fragmento necesario como fuente de inspiración o para confirmar un detalle.

## Language and TODO comments

- Write new or edited project content in English, including code comments, docstrings, identifiers, messages, and documentation, unless the user explicitly requests another language.
- Keep existing development notes in their original language unless the user explicitly asks to translate them.
- Treat TODO comments in source code as pending notes. Do not implement, remove, or rewrite a TODO until the user explicitly asks to address it.

## Scope of code changes and authorial intent

- Change code only when the change is necessary to implement the functionality the user requested. Make the smallest change that achieves that functionality; do not perform unrelated cleanup, refactoring, renaming, reformatting, or speculative improvements.
- A question, a request for an explanation, or a request for a code snippet does not authorize editing project files. Provide the answer or snippet without changing the repository.
- Treat this as teaching code with a past and a future. Preserve the user's existing structure, progression, examples, and notes about previous or possible future approaches.
- Do not edit, delete, move, translate, or reformat comments written by the user or code the user has commented out. Keep them exactly as they are, even when they are outside the currently executed path.
- Preserve the user's coding style, including naming, formatting, organization, and presentation. Follow that style when adding necessary code.
- Code or comments introduced by other AI agents may be changed when necessary for the requested functionality; this does not authorize changes to surrounding user-authored material.
- If authorship is unclear, or it is unclear whether a change is necessary or would affect protected user material, ask the user before making that change.

## Código de referencia: `0.sample_code/sinovia`

- `0.sample_code/sinovia` contiene código de referencia, no la implementación editable de este proyecto.
- Puede leerse para comprender decisiones o tomar inspiración.
- Nunca debe modificarse ningún fichero, directorio ni metadato dentro de `0.sample_code/sinovia`, incluido cualquier `.git` interno.
- No deben generarse datasets, resultados, logs, cachés ni entornos virtuales dentro de `0.sample_code/sinovia`.
- Todo código nuevo debe crearse fuera de esa carpeta.
- Si la guía `VBT_4-3.MD` resulta incompleta o desactualizada, actualizar la guía fuera del directorio de referencia; no alterar el código de referencia.

## Mantenimiento de `STRUCTURE.MD`

- `STRUCTURE.MD` es la fuente de verdad sobre la organización del proyecto.
- Debe consultarse antes de modificar cualquier fichero o carpeta.
- Si una modificación hace que su árbol, descripciones o relaciones dejen de ser correctos, actualizar `STRUCTURE.MD` como parte del mismo trabajo.
- No dar por terminada una tarea estructural mientras `STRUCTURE.MD` esté desactualizado.

## Environment configuration and teaching notebooks

- Keep only execution-environment settings, such as working and results directories, in the tracked root `.env_default` file. Do not put simulation, model, stimulus, or output filename values in dotenv files.
- Put local overrides in the root `.env` file. Keep `.env` ignored by Git and never commit its contents.
- Load `.env_default` first, then let `.env` override it. Document any new environment variable in `.env_default` when adding it. Resolve a relative working directory from the dotenv files' directory, and a relative results directory from the working directory; accept absolute paths for both.
- The original teaching notebook `notebooks/zerlaut/simulation_step_by_step.ipynb` keeps its simulation logic in the notebook. Its modular copy, `simulation_step_by_step_modular.ipynb`, imports auxiliary functions and classes from `src/` while retaining the simulation steps and values in the notebook.
- Define simulation and model values explicitly in teaching notebooks so readers can see and edit them alongside the steps they control.

## Repository code layout

- Put executable Python scripts under `scripts/<topic>/<script_name>.py`.
- Put reusable helper functions and classes under `src/`; group TVB-specific helpers under `src/tvb/`.
- This repository does not define an installable Python distribution. Use the root dotenv files to locate `TVB_IMPORT_DIR`, then add that directory to `sys.path` before importing `src` modules from a notebook or script. If unset, use the dotenv files' directory.

## Directorio protegido `.prompts`

- Está terminantemente prohibido leer, listar, buscar, indexar, copiar, mover, renombrar o modificar `.prompts` y todo su contenido.
- Las búsquedas e inventarios del repositorio deben excluir explícitamente `.prompts`.
- No se debe intentar inferir ni documentar su contenido.
- Si una tarea parece requerir acceso a `.prompts`, detener esa parte del trabajo y solicitar al usuario la información necesaria sin abrir la carpeta.

## Comprobación antes de finalizar

Antes de cerrar una tarea, verificar que:

- `0.sample_code/sinovia` no ha sufrido cambios;
- `.prompts` no ha sido accedida ni modificada;
- los cambios nuevos están fuera de `0.sample_code/sinovia`;
- `STRUCTURE.MD` sigue describiendo fielmente el proyecto;
- `VBT_4-3.MD` sigue siendo un índice válido si cambió documentación relacionada con el código de referencia.
