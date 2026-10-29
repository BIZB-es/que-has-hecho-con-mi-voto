# Qué has hecho con mi voto · Versión pública 1.00

**Estado: PUBLICADO en GitHub Pages.** Fecha de lanzamiento: 29 de octubre de 2026. Sitio público: https://bizb-es.github.io/que-has-hecho-con-mi-voto/. El proyecto continúa en desarrollo y conserva limitaciones de cobertura documentadas.

## Qué incluye

El portal tiene tres entradas principales:

1. **`index.html` · España en datos.** Diez bloques de indicadores para economía, ingresos, desempleo, pobreza, desigualdad de renta (índice de Gini), vivienda, empresas, poder adquisitivo y ayudas públicas. Nueve contienen series históricas; el bloque de subvenciones y beneficios fiscales enlaza las fuentes oficiales pero no inventa una agregación. La pobreza monetaria extrema está señalada como pendiente de definición y serie validada. Los gráficos muestran período, unidad, metodología, fuente y posibilidad de ver tablas/descargar CSV en modo avanzado.
2. **`congreso.html` · Qué han votado.** Conserva el observatorio de la XV Legislatura: 2.177 votaciones, 2.206 relaciones votación-expediente, censo de 412 personas, argumentos piloto, calidad nominal y seguimiento piloto de la Ley de Vivienda. **Los resultados y votos nominales tienen las limitaciones explicadas en `calidad.html`.** La pertenencia temporal completa a partidos aún no está resuelta.
3. **`proyecto.html` · Conoce el proyecto.** Guía de uso para personas no expertas, cómo se obtienen y revisan los datos, estado de cada área, limitaciones, fuentes, actualizaciones y correcciones.

No se han precargado todas las legislaturas. Los conjuntos históricos pueden incorporarse en el futuro. **No se ofrecen resultados políticos ni índices globales de veracidad de partidos.**

## Cómo abrirlo

Descomprime el ZIP manteniendo toda su estructura y abre `index.html` con Chrome, Firefox o Edge. La portada carga solo sus datos estadísticos. El archivo parlamentario (de mayor tamaño) se carga al abrir `congreso.html`, no antes. El proyecto es estático, no exige base de datos ni API de pago para las consultas normales.

Si el navegador restringe la descarga de archivos CSV por `file://`, la web seguirá siendo navegable. Para las pruebas de publicación completa puede servirse con `py -m http.server 8000` desde la raíz y abrir `http://localhost:8000`.

## Verificación técnica

```shell
python scripts/verificar_publicacion_v100.py
python scripts/verificar_importacion_v06.py
node --check assets/portal.js
node --check assets/indicadores_espana_v1.js
```

La validación inicial en navegador aislado cubrió los nueve bloques y ocho gráficos originales, los filtros por temas, la búsqueda, el modo avanzado, las tablas y el diseño móvil/escritorio. El panel actual incluye diez bloques y nueve gráficos; el nuevo indicador de Gini incorpora la serie anual INE 2008–2025 (años de encuesta, renta del año anterior), sin alquiler imputado. **Esto no acredita aún accesibilidad WCAG completa ni una prueba de producción del portal parlamentario.**

## Metodología y trazabilidad

- `datos/indicadores_espana_v1.json`: series y metadatos de la portada.
- `datos/indicadores_espana_fuentes.csv`: relación reproducible de fuentes públicas.
- `datos/relaciones_votacion_expediente_XV.csv`: vínculos del catálogo parlamentario.
- `datos/auditoria_expedientes_v082.json`, `datos/auditoria_XV.json`, `calidad.html`: limitaciones y auditorías.
- `datos/fuentes_sesiones_XV.zip`: archivo documental de las sesiones recuperadas, **para auditoría, no necesario para la navegación normal**.

Los datos de empleo y pobreza provienen de operaciones diferentes, y las fechas de referencia no son intercambiables. La renta ECV corresponde al año anterior a la encuesta. El alquiler fiscal declarado no es el alquiler anunciado ni cubre exactamente todo el territorio. El valor tasado de vivienda no equivale al precio medio escriturado. La renta salarial real es una razón **calculada por el portal** entre salario bruto medio e IPC, no el poder adquisitivo de cada hogar. Los resultados empresariales no incluyen necesariamente toda empresa y pérdida. Las estimaciones de personas en pobreza calculadas multiplicando tasas por población están identificadas como **aproximaciones**.

## Publicación y responsabilidades

La carpeta `.github/workflows/publicar.yml` contiene el flujo de despliegue manual de GitHub Pages. La publicación inicial de la versión 1.00 se completó correctamente el 29 de octubre de 2026. El flujo ejecuta controles de integridad antes de desplegar. El sitio puede utilizarse sin dominio propio. El paquete desplegado excluye los archivos de desarrollo y el material documental pesado.

**Titular:** Trust Society BISB, S.L. (BIZB) · **Contacto público:** qhhcmv@bizb.es. Las páginas `aviso-legal.html`, `privacidad.html` y `rectificaciones.html` explican la titularidad, el tratamiento de datos y el canal de correcciones.

**Tareas abiertas tras la primera publicación:** auditoría completa de accesibilidad, navegación con teclado y rendimiento; revisión editorial continua de fuentes y rótulos; ampliación y cotejo de partidos históricos y registros nominales. Se mantiene visible la cobertura parcial de indicadores y análisis.
