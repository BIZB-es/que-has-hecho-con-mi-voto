# Que has hecho con mi voto - cotejo de expedientes 0.8.2

Fecha de revision: 28/10/2026.

## Entrada y metodologia

La fuente principal de esta iteracion es `fuentes_sesiones_XV.zip`, facilitado por el usuario, que contiene 139 paginas HTML de sesiones del Congreso de los Diputados y un `manifest.csv`. Se ha comprobado **el tamano y SHA-256 de cada HTML** contra el manifiesto aportado (139 de 139). Esa operacion verifica la integridad interna del ZIP, pero no certifica por si sola que el HTML sea una copia incorrupta del servidor en el instante actual.

El analizador `scripts/cotejar_html_sesiones_v082.py` vincula un voto con sus expedientes solamente si se cumplen simultaneamente:

1. La URL del JSON del voto coincide exactamente con la de la tabla de referencia de la XV Legislatura.
2. Los tres totales de SI, NO y ABSTENCIONES del bloque del HTML coinciden con los del CSV de referencia.
3. Uno o varios enlaces a expedientes (`n_exp`) aparecen **en el acordeon de ese voto, o en el primer acordeon antecesor con enlace**, nunca por el ultimo expediente citado en el resto de la pagina.
4. El codigo del expediente se extrae del enlace explicito del mismo bloque. Si hay varios codigos, todos se conservan como relaciones independientes con la misma votacion.

Los HTML del ZIP se pueden consultar en `datos/fuentes_sesiones_XV.zip` (adjunto en la distribucion). La referencia publica de la sesion se conserva para cada votacion.

## Resultados (respecto de la base 0.8.1)

| Categoria | Votaciones |
|---|---:|
| Total en la web | 2.177 |
| Cotejadas con los 139 HTML del ZIP | 2.134 |
| Con un unico expediente en estos HTML | 2.119 |
| Con varios expedientes en estos HTML | 15 |
| Con cotejo documental previo y HTML no presente en ZIP | 43 |
| Sin ningun expediente asociado en el inventario actual | 0 |

El total es **2.206 relaciones votacion-expediente**, correspondientes a **707 codigos de expediente diferentes**. No debe confundirse el numero de relaciones con el numero de votos ni con el de leyes.

**Los 43 cotejos previos** pertenecen a las sesiones del 28/11/2024 (18), 24/03/2026 (2), 30/09/2026 (21) y los dos llamamientos del 02/10/2026 (2). Se mantienen sus metodologias de verificacion previas, identificadas como `COTEJO_ANTERIOR`: no se afirma haber comprobado sus HTML en este ZIP. Los dos llamamientos no estan en los CSV nominales originales.

## Correcciones a las propuestas de la version 0.8.1

Ocho propuestas habian asociado el expediente equivocado, porque el antiguo recuperador propagaba el ultimo numero mencionado sin delimitar el bloque de cada voto. Estas **propuestas** no habian sido publicadas como definitivas en la version 0.8.1. El ZIP permite corregirlas con una fuente trazable.

| Votacion | Propuesta anterior | Expediente del bloque oficial |
|---|---|---|
| s19-v001 | 125/000017 | 125/000002 |
| s27-v001 | 125/000021 | 125/000003 |
| s34-v001 | 120/000026 | 120/000004 |
| s64-v001 | 120/000031 | 120/000001 |
| s83-v001 | 120/000018 | 120/000003 |
| s110-v001 | 125/000022 | 125/000004 |
| s157-v001 | 101/000004 | 101/000002 |
| s166-v010 | 101/000004 | 101/000002 |

En otras 15 votaciones la propuesta anterior era **incompleta**, pues la pagina oficial incluye mas de un expediente para la misma votacion. Por ejemplo, `s40-v056` enlaza a doce expedientes `110/...` de acuerdos internacionales. La web 0.8.2 ofrece los doce, no solo uno.

## Archivos generados

- `datos/vinculos_XV.csv`: una fila por votacion (2.177), con estado de verificacion y fuente.
- `datos/relaciones_votacion_expediente_XV.csv`: una fila por relacion (2.206), con URL del expediente y evidencias.
- `datos/auditoria_expedientes_v082.json`: totales, casos multiples y ocho correcciones.
- `datos/historico/expedientes_propuestos_v081.csv`: anterior lista de propuestas con estado actualizado.
- `datos/historico/expedientes_propuestos_v08.csv`: CSV original de propuestas, preservado como fuente de revision.
- `assets/precarga_XV.js` y los cuatro `datos/historico/XV-AAAA.json`: actualizados para servir los expedientes tambien en el modo sin conexion.
- `datos/paquetes.json`: nueva huella SHA-256 de cada paquete anual.

Para reproducir la extraccion (Python con `beautifulsoup4` y `lxml`):

```
py scripts\cotejar_html_sesiones_v082.py --fuentes datos\fuentes_sesiones_XV.zip --propuestas datos\historico\expedientes_propuestos_v08.csv
```

## Limitaciones pendientes hacia 1.00

- **La cobertura no equivale al universo de todas las votaciones del Congreso**: se limita a las 2.177 del catalogo de trabajo de la XV Legislatura, incluyendo los dos llamamientos incorporados de otra fuente.
- Los **votos individuales de diputados** siguen sin cuadrar con los agregados en muchas votaciones; no se imputan votos ausentes.
- Falta reconstruir completamente partidos, coaliciones, candidaturas y afiliacion historica por fecha.
- Las fichas de argumentos sometidos a contraste y las series de resultados de leyes requieren ampliacion y revision editorial.
- La web todavia no se ha publicado en un dominio publico ni se ha sometido a una auditoria formal de accesibilidad.

No se debe presentar esta version 0.8.2 como la version 1.00 publicada.
