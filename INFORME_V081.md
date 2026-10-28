# Qué has hecho con mi voto · Auditoría de expedientes v0.8.1

**26/10/2026.** Análisis del archivo `expedientes_propuestos_v08.csv` recibido tras ejecutar la recuperación de sesiones.

## Resultado

- **2.127** candidatos distintos de asociación votación-expediente, procedentes de **139 fechas de sesión**; **652** números de expediente distintos.
- En las 2.127 filas se comprobó que `votacion_id`, `fecha` y la URL JSON coinciden exactamente con los archivos cargados. No hay identificadores duplicados.
- El antiguo programa ya cotejaba los totales de sí/no/abstención en cada coincidencia antes de generar el CSV; **este criterio no certifica la asociación al expediente**.
- **20** asociaciones adicionales se han cotejado directamente con dos listados oficiales de sesión: 18 de 28/11/2024 y 2 de 24/03/2026, contrastando objeto, orden y recuentos.
- Total con expediente documentado de forma individual en el proyecto: **50 votaciones** (30 anteriores + 20 nuevas; no son necesariamente 50 expedientes distintos).
- **2.127** registros conservan el candidato como **no verificado**. De ellos, tres se marcan expresamente como **posible votación conjunta de varios expedientes**.
- Ninguna propuesta preliminar se ha convertido automáticamente en una asociación definitiva.

## Riesgo detectado: votaciones conjuntas

En la sesión del **23/05/2024**, el Congreso recoge diversos acuerdos internacionales bajo un único recuento. El programa antiguo guardó el último número de expediente mencionado y puede dar la impresión de que esa votación corresponde exclusivamente a dicho expediente. Ejemplos:

- `s40-v052`: CSV original: convenio del Observatorio SKAO, que figura con expediente **110/000009** en el listado, pero el candidato recuperado es **110/000019**. En esa sección aparecen varios convenios antes del recuento.
- `s40-v055`: candidato **110/000028**, con votación presentada tras varias iniciativas.
- `s40-v056`: candidato **110/000027**, con votación presentada tras una relación de diferentes convenios.

Estos tres casos quedan **apartados de cualquier incorporación automática**, no se corrigen atribuyendo un solo expediente sin confirmar la naturaleza conjunta.

Fuente oficial: https://www.congreso.es/es/opendata/votaciones?targetDate=23%2F05%2F2024&targetLegislatura=XV

## Las dos sesiones inicialmente inaccesibles

- https://www.congreso.es/es/opendata/votaciones?targetDate=28%2F11%2F2024&targetLegislatura=XV — 18 votaciones.
- https://www.congreso.es/es/opendata/votaciones?targetDate=24%2F03%2F2026&targetLegislatura=XV — 2 votaciones.

Se cotejaron títulos, secuencia y sumas publicados con la base de referencia. Los números se incluyen en `datos/vinculos_XV.csv` con método explícito.

## Qué significa en la web

- Las **50 asociaciones cotejadas** se presentan con enlace a expediente.
- Las restantes **2.127** muestran, en su ficha, un **candidato pendiente** y un acceso a la sesión oficial (no un enlace de expediente presentado como definitivo).
- Los tres casos de posible votación conjunta muestran advertencia específica, sin asignarles en exclusiva un expediente.
- Queda pendiente volver a recuperar los HTML originales **y verificar las asociaciones con un analizador que respete el contexto de cada bloque**. Unos datos de ensayo o los recuentos coincidentes no bastan para aceptar la totalidad.

## Archivos para auditoría y continuidad

- `datos/expedientes_enlazados_XV.csv`: las 50 asociaciones cotejadas.
- `datos/expedientes_propuestos_anotados_XV.csv`: las 2.127 propuestas con estado y advertencias.
- `datos/expedientes_pendientes_XV.csv`: los 2.127 registros que siguen sin vínculo confirmado.
- `datos/auditoria_expedientes_v081.json`: resumen contable y casos particulares.
- `datos/vinculos_cotejados_2024_2026_XV.csv`: los 20 cotejos nuevos.

**El histórico de la v0.8 se conserva como informe de su fecha; la auditoría v0.8.1 sustituye sus cifras de cobertura para la versión nueva.**

## Preparación de la siguiente auditoría

La herramienta `scripts/guardar_sesiones_fuente_v081.py` permite **guardar** los HTML originales de las sesiones para validar cada contexto de votación, sin deducir el expediente a partir del último número mencionado. La ejecución se reanuda automáticamente: las sesiones ya archivadas no se vuelven a descargar. No ejecutar repetidamente contra el Congreso si éste rechaza las conexiones; usar el ZIP con lo recuperado. La descarga respeta una cadencia moderada y no intenta sortear controles del servidor.
