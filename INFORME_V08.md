# Qué has hecho con mi voto — Informe de la versión 0.8

**Fecha de revisión: 26/10/2026.** La versión 0.8 mejora la transparencia y el control de integridad; **no constituye todavía la versión 1.00** ni certifica cobertura de toda la actividad parlamentaria.

## Resultado ya disponible

| Capa | Registros | Alcance |
|---|---:|---|
| Votaciones del CSV de Congreso Abierto | 2.175 | 19/09/2023–30/09/2026, legislatura XV |
| Votaciones por llamamiento añadidas | 2 | Sesión 203, 02/10/2026, expedientes 130/000055 y 130/000056 |
| Votaciones que muestra la web | **2.177** | 2.175 del CSV + 2 documentales, **no todo el universo parlamentario** |
| Registros agregados por grupo del CSV | 19.561 | Sus sumas coinciden con el total de las 2.173 votaciones que cuentan con desglose |
| Filas nominales de diputados | 726.564 | Procedentes del CSV entregado, conservadas sin modificaciones |
| Votaciones que cuadran nominal con total | 95 | Igualdad de recuentos no garantiza verificación independiente de identidad histórica |
| Votaciones con nominales incompletos | **2.078** | En todas hay menos filas nominales que el total publicado |
| Votaciones del CSV sin desglose nominal | 2 | Identificadores s89-v005 y s202-v021 |
| Personas censo oficial XV | 412 | Se cruzaron 350 identidades con código; no se deduce que los otros 62 nunca votaran |
| Expedientes con relación documental | 30 | 28 anteriores + 2 por llamamiento de octubre |
| Expedientes del CSV pendientes | 2.147 | Su enlace a votación no está todavía verificado |

### Qué significan las discrepancias

Para cada votación se han sumado las cuatro categorías de voto individual. Se han comparado con los totales generales y también los agregados por grupo. Los resultados detallados se publican en `datos/calidad_XV.json` y `datos/incidencias_nominales_XV.csv`.

En las 2.078 discrepancias el número individual es menor que el general. La suma de las diferencias por categorías a lo largo de las votaciones es **15.264 sí, 15.491 no, 2.841 abstenciones y 1.058 no vota**. Son *diferencias de registros por votación*, **no** personas distintas ni prueba de ausencias reales.

**No se ha confrontado aún cada JSON/XML del Congreso con cada fila nominal**: el entorno utilizado no permite descargar en bloque los ficheros primarios. El cotejo de identidad histórica, partido y grupo a cada fecha sigue siendo parcial.

### Dos votaciones finales incorporadas

La sesión plenaria 203 del 02/10/2026 debatió los RDL 26/2026 y 27/2026 (expedientes 130/000055 y 130/000056). El BOE registra la derogación de ambos. La fuente que detalla los recuentos es la crónica de El Debate del 02/10/2026: **172 sí y 178 no**, y **166 sí y 184 no**. No se han reconstruido nominales ni grupos a partir de esa información.

- Vídeo oficial de la sesión: https://app.congreso.es/AudiovisualCongreso/audiovisualdetalledisponible?codOrgano=400&codSesion=203&fechaSesion=02%2F10%2F2026&i=779883&idLegislaturaElegida=15&mp4=mp4
- Derogación RDL 26/2026: https://www.boe.es/buscar/doc.php?id=BOE-A-2026-20526
- Derogación RDL 27/2026: https://www.boe.es/buscar/doc.php?id=BOE-A-2026-20527
- Recuentos: https://www.eldebate.com/espana/20261002/asi-han-votado-partidos-decretos-vivienda-quien-apoyado-quien-tumbado-cada-texto-cns_465496_amp.html

La web expone el estado y fuentes en cada ficha; para los dos nuevos registros no muestra un desglose nominal inexistente.

## Cambios de producto

- Enlace a **Calidad de datos** desde todas las páginas principales; filtros de cobertura por año, estado y texto.
- Aviso específico en cada ficha: coincidente, incompleto o sin desglose, con diferencia numérica por sentido de voto.
- Enlace a la página de votaciones de la sesión oficial cuando falta el número de expediente; ese enlace **no equivale a haber vinculado un expediente**.
- Proceso reproducible `scripts/auditar_calidad_v08.py` para auditar los tres archivos de origen.
- Proceso reproducible `scripts/incorporar_llamamientos_v08.py` que agrega dos actos documentales sin inventar votos.
- Preparador **no destructivo** `scripts/proponer_expedientes_v08.py` para extraer propuestas de asociación a expediente de la página del Congreso. Solo acepta candidatos que coinciden en URL JSON y totales sí/no/abstención; se revisan antes de publicarse. No se pudo ejecutar contra todos los HTML oficiales desde este entorno por falta de acceso de red.
- Se ha retirado de `.github/workflows/` el proceso de reimportación automática legado porque **no preservaba** los datos y controles de calidad de la v0.8. No se ejecuta una actualización que pudiera sobrescribir silenciosamente los llamamientos y datos auditados.

## Qué sigue sin resolverse

1. **Recuperar y verificar 2.147 expedientes:** el número no está en los CSV aportados. El importador no hace asociaciones por similitud de títulos. Se preparó el parser para ejecutar en un entorno con acceso a los listados oficiales; las propuestas deben ser cotejadas.
2. **Cotejar nominal con JSON primarios:** diferencias detectadas no equivalen a errores del Congreso; las causas deben identificarse con evidencia primaria antes de corregir cualquier registro.
3. **Identificar partido y grupo por fechas:** las 412 personas del censo no traen filiación política histórica sistemática. Continúa prohibido atribuir todos los votos del Grupo Mixto o de SUMAR a un partido sin prueba.
4. **Revisar clasificación temática** automática, incluida la materia de asuntos aún genéricos o ambiguos.
5. **Abarcar otras legislaturas** con carga realmente auditada. Las opciones en el selector no equivalen a datos disponibles.
6. **Contraste de argumentos y evaluación de leyes:** fichas existentes siguen siendo muestras, no un estudio exhaustivo.

## Reproducibilidad

```bash
python scripts/auditar_calidad_v08.py \
  --votaciones 'congreso-abierto-votaciones(1).csv' \
  --grupos congreso-abierto-votos-grupo.csv \
  --nominales congreso-abierto-votos.csv
python scripts/verificar_importacion_v06.py
python scripts/verificar_v08.py
python tests/test_v08.py
```

Los CSV originales no están duplicados dentro del ZIP, pero se incluyen las huellas SHA-256 y un archivo con las cifras originales de voto por votación en `datos/votaciones_referencia_XV.csv`. La auditoría se recalcula con los CSV originales.

## Estado de publicación

V0.8 es una **versión de trabajo reproducible**, no desplegada en un dominio público. La web se abre desde su carpeta local; GitHub Pages se puede usar más adelante tras validar la integridad del sitio y el contenido editorial. No se ha conectado un repositorio ni publicado automáticamente.
