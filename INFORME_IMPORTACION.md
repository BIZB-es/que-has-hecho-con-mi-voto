# Informe de importación — 26 de octubre de 2026

**Recibidos:** los tres CSV de Congreso Abierto sobre votaciones XV, desgloses de grupo y votos individuales.

**Importados y conciliados:** 2.175 votaciones, 19.561 posiciones de grupo y 726.564 registros nominales. Fechas 19/09/2023–30/09/2026. Reparto por año: 2023: 32; 2024: 862; 2025: 741; 2026: 540.

**Comprobado:** IDs de voto únicos, no hay filas duplicadas de grupo ni de nombre/votación, fechas coherentes, totales por grupo iguales a los totales publicados de cada votación con desglose. Dos votaciones carecen de grupos y de individuales (s89-v005 y s202-v021); siete identificadores son descripciones de proveedor, no códigos estándar de sesión.

**Diferencias de origen:** 2.078 votaciones cuyo conteo individual no coincide con el total general; 12.750 parejas votación/grupo cuyo conteo individual no coincide con el total del grupo. No se infieren datos ausentes. Los agregados y el detalle nominal permanecen separados.

**Producto:** `index.html` abre el catálogo real sin CSV manuales, se puede filtrar por legislatura y fechas, tiene desgloses de todos los grupos y consulta nominal por sesión. Las otras legislaturas siguen pendientes.

**Pruebas:** `tests/test_importacion_real.py` verifica 2.175 registros en interfaz, 19.561 grupos, filtros por año, detalle nominal de una votación con 350 filas, los dos suplicatorios sin desglose, los IDs especiales y versión móvil. `scripts/verificar_importacion_v06.py` comprueba las huellas SHA-256 de cuatro paquetes y de cada uno de los ficheros nominales.

**Alcance de completitud:** completo exclusivamente respecto de las tablas CSV aportadas. No auditado contra la totalidad de registros oficiales del Congreso. La atribuición a partidos sigue pendiente por falta de censo de candidaturas fechado.

**Fuentes y hashes detallados:** `datos/auditoria_XV.json`.
