# Auditoría de identidad y expedientes — Versión 0.7

Fecha de corte: 26/10/2026.

## Entregables contrastados

- 2.175/2.175 votaciones de la exportación incluyen URL del JSON de votación publicado por el Congreso. Todos los identificadores de la nueva exportación coinciden con la versión 0.6. No se han modificado votos sí/no/abstención/resultado. Se recuperan también los valores originales `no_vota` de dos suplicatorios sin desglose nominal.
- 350 códigos parlamentarios distintos con 350 nombres nominales distintos. **350/350 nombres se relacionan sin ambigüedad con 350 filas** del CSV de diputados oficiales de la XV Legislatura. Cada persona tiene un enlace de ficha construido con el código, conforme al patrón del Congreso; no se han comprobado individualmente 350 enlaces por HTTP.
- El CSV general de diputados incluye **412 personas para la XV**, 62 de ellas ausentes del archivo de votos descargado. El campo `FECHAINICIOLEGISLATURA` es comienzo de legislatura, **no** fecha individual de incorporación al escaño.
- 28 expedientes enlazados: **7 ya venían en el CSV** y **21** se asociaron contrastando los números de votación, títulos y resultados con el listado oficial de la sesión plenaria n.º 202 del 30/09/2026. Los **2.147 restantes** carecen de expediente identificado; se muestra un aviso y acceso al buscador oficial, nunca una asociación deducida de palabras clave.

## Advertencias imprescindibles

**El ID de la persona no identifica su partido.** La exportación oficial del censo suministrada solo tiene nombre, apellido, legislatura y fechas globales de esa legislatura. El CSV de votos incluye un campo `grupo` que, para los 350 nombres, se mantiene constante en todo el intervalo: no constituye un historial fiable del grupo. Las cifras generales de los grupos siguen tomándose de la tabla agregada de origen, y no de ese campo individual.

Se han cotejado cuatro fichas individuales de muestra: Ione Belarra (262), Àgueda Micó (164), Cristina Valido (38) y Néstor Rego (238). Estas últimas fichas muestran una *formación electoral*, no garantizan la afiliación política en todas las fechas. Para Ione y Àgueda existe una transición de grupo documentada en su ficha; los votos que coinciden exactamente con la fecha de cambio se dejan sin rectificación automática por la ambigüedad temporal de la anotación oficial. No se infiere partido de grupo para ninguno de los 350 diputados.

Las URL de los expedientes siguen el formato del buscador de iniciativas del Congreso y su vinculación está respaldada por el listado de sesión para 21 casos o el CSV para 7 casos. **No se ha podido abrir por HTTP cada enlace desde este entorno**. El registro oficial de cada votación sí tiene la URL original del CSV.

## Archivos añadidos

- `datos/auditoria_v07.json`: huellas SHA-256 de los tres CSV nuevos y recuentos.
- `datos/vinculos_XV.csv`: una fila por votación, URL oficial y expediente identificado si existe.
- `datos/censo_XV.csv` y `datos/identidades_XV.json`: cruce de los 412 nombres, con código solo para 350.
- `assets/identidades_XV.js`: diccionario nominal embebido para lectura sin servidor y fichas con enlace al Congreso.
- `diputados.html`: buscador sencillo del censo completo de XV.
- `scripts/enriquecer_v07.py`: proceso reproducible con los tres CSV y la precarga v0.6.

## Próximo paso real para los 2.147 expedientes restantes

La página oficial de **datos abiertos de votaciones del Congreso** muestra, dentro de cada sesión, los números de expediente junto a las votaciones. Necesitamos recuperar y parsear el listado de las otras sesiones, unirlo a cada URL de voto y contrastar los títulos/resultado para no asignar un expediente incorrecto a una enmienda o a un punto separado.

Para el desglose riguroso por **partido**, hay que recuperar la *formación de cada diputado en fecha*, no extrapolar la etiqueta de la coalición o del grupo. La ficha del Congreso ofrece información de formación y algunos intervalos de grupo; deberá verificarse la pertenencia real a cada partido mediante documentación de candidaturas y cambios. Estos dos enriquecimientos quedan expresamente **pendientes**, no se presentan como completos.

Fuentes de referencia: https://www.congreso.es/es/opendata/votaciones , https://www.congreso.es/es/opendata/diputados , https://congresoabierto.org/datos/ .
