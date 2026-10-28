# Plantillas CSV para el observatorio

Los ficheros de esta carpeta están **vacíos salvo por el encabezado**; no contienen datos reales ni ejemplos inventados. Cada archivo de votaciones tiene una fila por resultado nominal o punto votado (no una fila por ley), y cada archivo de posiciones tiene una fila por grupo o candidatura y votación.

- Para importaciones del navegador, selecciona la legislatura adecuada.
- Para archivos que mezclen legislaturas, incluye la columna `legislatura` en cada fila.
- Usa fechas `AAAA-MM-DD`.
- Identifica la votación con `id` y las posiciones con `votacion_id` coincidente.
- Cuando el voto mayoritario sea diverso, indícalo como `Dividido / empate` o conserva los conteos.
- Para partidos, aporta el dato explícitamente o reconstruye la candidatura de cada diputado aplicable **a la fecha del voto**; no confundas grupo y partido.
- Conserva enlaces fuente originales en la columna `url_votacion` y un informe de calidad del conjunto.
