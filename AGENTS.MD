# Instrucciones para agentes

Estas reglas son obligatorias para cualquier agente que trabaje en este repositorio.

## Orden de lectura antes de actuar

1. Leer `STRUCTURE.MD` antes de crear, modificar, mover o eliminar cualquier fichero o carpeta.
2. Si la tarea guarda relación con el código de referencia, leer `VBT_4-3.MD` antes de consultar `vbt_t4-3`.
3. Usar `VBT_4-3.MD` para localizar el fichero concreto que contiene la información buscada. No recorrer ni buscar directamente por toda la carpeta `vbt_t4-3` como primer método de investigación.
4. Una vez localizado el fichero mediante la guía, puede leerse el fragmento necesario como fuente de inspiración o para confirmar un detalle.

## Código de referencia: `vbt_t4-3`

- `vbt_t4-3` contiene código de referencia, no la implementación editable de este proyecto.
- Puede leerse para comprender decisiones o tomar inspiración.
- Nunca debe modificarse ningún fichero, directorio ni metadato dentro de `vbt_t4-3`, incluido su `.git` interno.
- No deben generarse datasets, resultados, logs, cachés ni entornos virtuales dentro de `vbt_t4-3`.
- Todo código nuevo debe crearse fuera de esa carpeta.
- Si la guía `VBT_4-3.MD` resulta incompleta o desactualizada, actualizar la guía fuera del directorio de referencia; no alterar el código de referencia.

## Mantenimiento de `STRUCTURE.MD`

- `STRUCTURE.MD` es la fuente de verdad sobre la organización del proyecto.
- Debe consultarse antes de modificar cualquier fichero o carpeta.
- Si una modificación hace que su árbol, descripciones o relaciones dejen de ser correctos, actualizar `STRUCTURE.MD` como parte del mismo trabajo.
- No dar por terminada una tarea estructural mientras `STRUCTURE.MD` esté desactualizado.

## Directorio protegido `.prompts`

- Está terminantemente prohibido leer, listar, buscar, indexar, copiar, mover, renombrar o modificar `.prompts` y todo su contenido.
- Las búsquedas e inventarios del repositorio deben excluir explícitamente `.prompts`.
- No se debe intentar inferir ni documentar su contenido.
- Si una tarea parece requerir acceso a `.prompts`, detener esa parte del trabajo y solicitar al usuario la información necesaria sin abrir la carpeta.

## Comprobación antes de finalizar

Antes de cerrar una tarea, verificar que:

- `vbt_t4-3` no ha sufrido cambios;
- `.prompts` no ha sido accedida ni modificada;
- los cambios nuevos están fuera de `vbt_t4-3`;
- `STRUCTURE.MD` sigue describiendo fielmente el proyecto;
- `VBT_4-3.MD` sigue siendo un índice válido si cambió documentación relacionada con el código de referencia.
