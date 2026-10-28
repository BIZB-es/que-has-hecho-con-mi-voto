import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sections=[
('Democracia e instituciones',[
('Administración pública y función pública','funcion publica|administraciones publicas|empleados publicos|funcionarios|interinos|oposiciones|administracion general'),
('Constitución, instituciones y monarquía','constitucion|constitucional|casa real|monarquia|jefatura del estado|reforma del reglamento|reglamento del congreso'),
('Democracia, elecciones y participación','electoral|elecciones|referendum|consulta popular|participacion ciudadana|partidos politicos|circunscripcion|democracia'),
('Transparencia, integridad y corrupción','transparencia|corrupcion|conflictos de intereses|puertas giratorias|buen gobierno|etica publica|lobbies'),
('Organización territorial y autonomías','comunidades autonomas|estatuto de autonomia|transferencia de competencias|municipios|diputaciones|financiacion autonomica|ayuntamientos|provincias|entidades locales'),
('Justicia y derechos fundamentales','poder judicial|justicia|tribunales|jueces|fiscalia|derecho de defensa|codigo penal|indulto|amnistia|derechos fundamentales|derechos civiles'),
('Interior y seguridad ciudadana','seguridad ciudadana|fuerzas y cuerpos de seguridad|policia|guardia civil|delincuencia|prisiones|instituciones penitenciarias|terrorismo'),
('Protección de datos y privacidad','proteccion de datos|datos personales|privacidad|derecho al olvido|rgpd|loml?|vigilancia digital'),
]),
('Economía y empleo',[
('Trabajo, empleo y relaciones laborales','empleo|jornada laboral|trabajo|salario minimo|despido|negociacion colectiva|relaciones laborales|desempleo|paro|convenio colectivo|huelga|contratacion laboral'),
('Pensiones y Seguridad Social','pensiones|jubilacion|seguridad social|cotizaciones|viudedad|pension|subsidio mayores|prestaciones contributivas'),
('Hacienda e impuestos','fiscal|impuesto|tribut|irpf|iva|hacienda|recaudacion|incentivos fiscales|fraude fiscal|tasas'),
('Presupuestos y deuda pública','presupuestos generales|estabilidad presupuestaria|deficit publico|deuda publica|gasto publico|reglas fiscales|techo de gasto'),
('Economía, empresas y competencia','economia|empresa|pymes|autonomos|competencia|mercados|consumo|comercio|precios|inflacion|banca|mercado financiero'),
('Industria, minería y producción','industria|industrial|mineria|minero|fabricacion|produccion industrial|cadena de valor|sector manufacturero'),
('Turismo y hostelería','turismo|hotel|turistico|hosteleria|alojamientos turisticos'),
]),
('Personas y servicios públicos',[
('Vivienda y urbanismo','vivienda|alquiler|arrendamiento|hipoteca|urbanismo|suelo residencial|desahucios|inquilinos|precio de la vivienda'),
('Sanidad y salud pública','sanidad|salud|hospital|medicamentos|atencion primaria|enfermedad|vacunacion|farmacia|sistema nacional de salud'),
('Educación no universitaria','educacion|escuelas|colegios|institutos|docentes|profesores|formacion profesional|fp dual|ensenanza'),
('Universidades e investigación','universidad|universidades|investigacion|ciencia|cientific|transferencia tecnologica|becas universitarias'),
('Cultura, artes y patrimonio','cultura|cultural|cine|museo|patrimonio historico|bibliotecas|artes escenicas|libros|propiedad intelectual'),
('Igualdad, feminismo y violencia de género','igualdad|violencia de genero|violencia vicaria|feminismo|violencia machista|brecha salarial|discriminacion por sexo'),
('Infancia, juventud y familias','infancia|menores|ninos|juventud|familias|natalidad|proteccion del menor|crianza|conciliacion familiar'),
('Servicios sociales, pobreza y dependencia','pobreza|exclusion social|renta minima|ingreso minimo vital|servicios sociales|dependencia|cuidados|sin hogar|vulnerabilidad'),
('Discapacidad y accesibilidad','discapacidad|accesibilidad|barreras arquitectonicas|personas con discapacidad|diversidad funcional'),
('Derechos LGTBI y diversidad','lgtbi|lgbti|transexualidad|transgenero|identidad de genero|orientacion sexual'),
('Deporte y actividad física','deporte|deportiva|federaciones deportivas|olimpiadas|actividad fisica'),
]),
('Territorio, recursos y movilidad',[
('Transporte, tráfico y movilidad','transporte|ferrocarril|tren|aeropuerto|aviacion|movilidad|carretera|trafico|autobus|autopista|puertos|taxi|vehiculos'),
('Infraestructuras y obra pública','infraestructuras|obra publica|obras publicas|red vial|carreteras|infraestructura hidraulica|tunel|puente|red ferroviaria'),
('Energía y transición energética','energia|energetico|electricidad|renovables|hidrogeno|nuclear|gas natural|petroleo|precio de la luz|mercado electrico'),
('Medio ambiente y cambio climático','medio ambiente|biodiversidad|cambio climatico|emisiones|contaminacion|espacios protegidos|conservacion ambiental|residuos|reciclaje'),
('Agricultura, ganadería y pesca','agricultura|ganaderia|pesca|agricola|agrario|campesino|sector primario|pac|regadios|forestal'),
('Agua y gestión hídrica','sequia|agua potable|trasvase|recursos hidricos|acuiferos|embalses|politica hidrologica'),
('Medio rural y reto demográfico','despoblacion|medio rural|rural|reto demografico|cohesion territorial|pueblos'),
('Protección de animales','bienestar animal|proteccion animal|maltrato animal|especies de compania'),
]),
('Tecnología, comunicación y mundo',[
('Digitalización, inteligencia artificial y tecnologías','inteligencia artificial|digitalizacion|algoritmos|ciberseguridad|nuevas tecnologias|automatizacion|tecnologia'),
('Telecomunicaciones y medios de comunicación','telecomunicacion|internet|telefonia|medios de comunicacion|television|radio|plataformas digitales|publicidad'),
('Migración, extranjería y asilo','inmigracion|migracion|extranjeria|asilo|refugiados|fronteras|nacionalidad|regularizacion de extranjeros'),
('Relaciones internacionales y cooperación','politica exterior|relaciones internacionales|onu|union europea|ue|cooperacion internacional|tratado internacional|convenio internacional|acuerdo internacional|embajadas|diplomacia'),
('Defensa y Fuerzas Armadas','defensa|ejercito|fuerzas armadas|militar|otan|seguridad nacional|armamento|operaciones militares'),
]),
('Procedimiento parlamentario',[
('Tramitación y organización parlamentaria','declaracion de actividades|estatuto del diputado|comision parlamentaria|prorroga del plazo|tramitacion parlamentaria|avocacion|reglamento de la camara|mesa del congreso'),
])
]
areas=[]
for section, values in sections:
 for title,keys in values:
  ident=''.join(c if c.isalnum() else '-' for c in title.lower()).strip('-')
  areas.append({'id':ident,'nombre':title,'familia':section,'palabras':keys.split('|')})
areas.append({'id':'sin-clasificar','nombre':'Sin clasificar / pendiente de revisión','familia':'Control de calidad','palabras':[]})
(ROOT/'datos'/'taxonomia.json').write_text(json.dumps({'version':'0.3','nota':'Categorías temáticas transversales, no denominaciones de ministerios. Etiquetado automático orientativo, no exhaustivo; permite varias categorías y revisión humana.','areas':areas},indent=2,ensure_ascii=False))
leg=[('X','2011-12-13','2015-10-27'),('XI','2016-01-13','2016-05-03'),('XII','2016-07-19','2019-03-05'),('XIII','2019-05-21','2019-09-24'),('XIV','2019-12-03','2023-05-30'),('XV','2023-08-17','2026-10-06')]
(ROOT/'datos'/'legislaturas.json').write_text(json.dumps({'version':'0.3','fuente':'https://www.congreso.es/es/cem/historical','legislaturas':[{'id':n,'inicio':st,'fin':end,'detalle':('Hay registros de votaciones nominales; documentación y clasificación histórica dependen de las fuentes disponibles.' if n!='XV' else 'El catálogo del Pleno disponible abarca desde 19/09/2023 hasta 30/09/2026, más casos por llamamiento del 02/10/2026.') } for n,st,end in leg]},ensure_ascii=False,indent=2))
print('Areas',len(areas),'legislatures',len(leg))
