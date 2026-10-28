# Qué has hecho con mi voto · Candidata de lanzamiento 1.00

**Estado: NO PUBLICADO.** Fecha de revisión: 29 de octubre de 2026. Esta versión es candidata, no una web 1.00 puesta a disposición del público.

## Qué incluye

El portal tiene tres entradas principales:

1. **`index.html` · España en datos.** Nueve bloques de indicadores para economía, ingresos, desempleo, pobreza, vivienda, empresas, poder adquisitivo y ayudas públicas. Ocho contienen series históricas; el bloque de subvenciones y beneficios fiscales enlaza las fuentes oficiales pero no inventa una agregación. La pobreza monetaria extrema está señalada como pendiente de definición y serie validada. Los gráficos muestran período, unidad, metodología, fuente y posibilidad de ver tablas/descargar CSV en modo avanzado.
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

Se han probado en navegador aislado la portada, los 9 bloques y 8 gráficos, los filtros por temas, la búsqueda, el modo avanzado, las tablas y el diseño móvil/escritorio. **Esto no acredita aún accesibilidad WCAG completa ni una prueba de producción del portal parlamentario.**

## Metodología y trazabilidad

- `datos/indicadores_espana_v1.json`: series y metadatos de la portada.
- `datos/indicadores_espana_fuentes.csv`: relación reproducible de fuentes públicas.
- `datos/relaciones_votacion_expediente_XV.csv`: vínculos del catálogo parlamentario.
- `datos/auditoria_expedientes_v082.json`, `datos/auditoria_XV.json`, `calidad.html`: limitaciones y auditorías.
- `datos/fuentes_sesiones_XV.zip`: archivo documental de las sesiones recuperadas, **para auditoría, no necesario para la navegación normal**.

Los datos de empleo y pobreza provienen de operaciones diferentes, y las fechas de referencia no son intercambiables. La renta ECV corresponde al año anterior a la encuesta. El alquiler fiscal declarado no es el alquiler anunciado ni cubre exactamente todo el territorio. El valor tasado de vivienda no equivale al precio medio escriturado. La renta salarial real es una razón **calculada por el portal** entre salario bruto medio e IPC, no el poder adquisitivo de cada hogar. Los resultados empresariales no incluyen necesariamente toda empresa y pérdida. Las estimaciones de personas en pobreza calculadas multiplicando tasas por población están identificadas como **aproximaciones**.

## Publicación y responsabilidades

La carpeta `.github/workflows/publicar.yml` contiene una configuración para GitHub Pages. **No se ha publicado en Internet.** Antes de autorizar el despliegue 1.00 deben realizarse:

1. Designación de titular del sitio y correo público de consultas/rectificaciones.
2. Página legal y tratamiento de datos adecuados al titular y al uso real de cookies, analítica o formularios.
3. Revisión editorial final de fuentes y rótulos (en especial categorías pendientes).
4. Pruebas reales de accesibilidad, teclado, rendimiento, enlaces externos y dispositivos.
5. Autorización expresa de publicar y configuración del repositorio/dominio.

Para publicar en GitHub Pages: crear repositorio, subir los archivos de esta carpeta conservando directorios, revisar la pestaña Actions, activar Settings → Pages → GitHub Actions, y ejecutar el flujo con autorización. El flujo está configurado para verificar primero la integridad. Puede usarse sin dominio propio. No es necesario publicar los archivos de sesiones originales en el sitio público; la configuración de despliegue excluye archivos de desarrollo y material documental pesado.
