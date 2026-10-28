#!/usr/bin/env python3
"""Auditable partial sample transcribed from the official date-indexed Plenary list.
Never label this snapshot as exhaustive. Non-official identifiers are marked 'extracto'.
"""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parent.parent
old=json.loads((root/'datos/muestra.json').read_text(encoding='utf8'))
by_old={r['id']:r for r in old['votaciones']}
rows=[]

def add(day,session,num,exp,kind,title,yes,no,abst,topic='',key=None):
    num_id=f's{session}-v{num:03d}' if session==202 or key else f'extracto-{day}-s{session}-{num:03d}'
    if key:num_id=key
    date=day[-2:]+'%2F'+day[5:7]+'%2F'+day[:4]
    url='https://www.congreso.es/es/opendata/votaciones?targetDate='+date+'&targetLegislatura=XV'
    status='Aprobada' if yes>no else 'Rechazada'
    rows.append(dict(id=num_id,legislatura='XV',fecha=day,sesion=session,numero=num if session==202 else '',expediente=exp,tipo=kind,
                     titulo=title,temas=topic,resultado=status,si=yes,no=no,abstencion=abst,no_vota=None,
                     url_votacion=url,url_expediente='',fuente='Extracto manual del listado oficial del Congreso',
                     calidad='Cobertura puntual; titulo resumido editorialmente; totales publicados por el Congreso; sin atribucion de grupos'))

pnl='Proposici\u00f3n no de Ley'
moc='Moci\u00f3n'
conv='Acuerdo o convenio internacional'
proc='Tr\u00e1mite parlamentario'
# 30 September 2026, session 202; ordinal verified against last published S202 V20 and V21.
a=[
('162/000814',pnl,'Aplicar en Espa\u00f1a el Pacto Europeo sobre Migraci\u00f3n y Asilo (PNL del PP)',137,175,34,'migracion'),
('162/000769',pnl,'Contribuci\u00f3n europea excepcional sobre beneficios extraordinarios de empresas energ\u00e9ticas (PNL del PSOE)',166,176,5,'energia'),
('173/000194',moc,'Medidas contra el encarecimiento de los productos energ\u00e9ticos (moci\u00f3n de Belarra, punto 1)',44,181,122,'energia'),
('173/000194',moc,'Medidas contra el encarecimiento de los productos energ\u00e9ticos (moci\u00f3n de Belarra, punto 2)',166,179,0,'energia'),
('173/000194',moc,'Medidas contra el encarecimiento de los productos energ\u00e9ticos (moci\u00f3n de Belarra, punto 3)',39,181,126,'energia'),
('173/000195',moc,'Situaci\u00f3n de seguridad nacional en Ceuta (moci\u00f3n de VOX)',33,176,138,'seguridad'),
('173/000196',moc,'Gesti\u00f3n de Defensa durante la crisis en Ceuta (moci\u00f3n PP, puntos 1, 2 y 4)',172,174,0,'defensa'),
('173/000196',moc,'Gesti\u00f3n de Defensa durante la crisis en Ceuta (moci\u00f3n PP, punto 3)',171,170,6,'defensa'),
('173/000196',moc,'Gesti\u00f3n de Defensa durante la crisis en Ceuta (moci\u00f3n PP, segundo bloque)',172,170,5,'defensa'),
('121/000106','Enmienda a la totalidad','Enmienda de devoluci\u00f3n de VOX al proyecto de ley org\u00e1nica sobre violencia vicaria',34,312,0,'igualdad'),
('110/000081',conv,'Cooperaci\u00f3n t\u00e9cnica y financiera de Espa\u00f1a con Ucrania',290,4,46,'internacional'),
('110/000082',conv,'Comisi\u00f3n Internacional de Reclamaciones para Ucrania',272,4,63,'internacional'),
('110/000083',conv,'Exenci\u00f3n de visados diplom\u00e1ticos entre Espa\u00f1a y Uzbekist\u00e1n',293,0,53,'internacional'),
('110/000084',conv,'Acuerdo sobre transporte a\u00e9reo entre Espa\u00f1a y Brasil',293,32,21,'transporte'),
('110/000085',conv,'Protocolo adicional a la Convenci\u00f3n Iberoamericana de Derechos de los J\u00f3venes',301,33,12,'juventud'),
('110/000086',conv,'Exenci\u00f3n de visados diplom\u00e1ticos, especiales y de servicio entre Espa\u00f1a y Arabia Saud\u00ed',293,14,39,'internacional'),
('152/000008',proc,'Pr\u00f3rroga de la comisi\u00f3n de investigaci\u00f3n del apag\u00f3n del 28 de abril de 2025',347,0,0,'energia'),
('154/000006',proc,'Pr\u00f3rroga de la subcomisi\u00f3n sobre discursos de odio',176,33,138,'igualdad'),
('121/000092',proc,'Avocaci\u00f3n al Pleno de la reforma educativa (solicitudes de PP y VOX)',342,5,0,'educacion'),
('042/000044',proc,'Dictamen sobre declaraci\u00f3n de actividades de diputados',343,1,2,'instituciones'),
('240/000002',proc,'Dictamen sobre suplicatorio de un diputado (sin voto nominal)',340,0,0,'instituciones')]
for i,(exp,k,t,si,no,ab,topic) in enumerate(a,1):add('2026-09-30',202,i,exp,k,t,si,no,ab,topic)
# 23 September 2026, session 200; positions are extract identifiers, not original ordinal.
b=[
('162/000822',pnl,'Variante Sur Ferroviaria y medidas municipales ligadas a la Y vasca',270,70,8,'transporte'),
('162/000260',pnl,'Ley de Familias: proposici\u00f3n no de ley de Belarra y Santana',19,177,147,'familias'),
('173/000193',moc,'Pol\u00edtica educativa del Gobierno: moci\u00f3n PP, punto I',177,171,0,'educacion'),
('173/000193',moc,'Pol\u00edtica educativa del Gobierno: moci\u00f3n PP, punto II.1',177,171,0,'educacion'),
('173/000193',moc,'Pol\u00edtica educativa del Gobierno: moci\u00f3n PP, punto II.2',172,170,6,'educacion'),
('173/000193',moc,'Pol\u00edtica educativa del Gobierno: moci\u00f3n PP, punto II.3',172,176,0,'educacion'),
('173/000193',moc,'Pol\u00edtica educativa del Gobierno: moci\u00f3n PP, punto II.4',171,176,0,'educacion'),
('130/000054','Convalidaci\u00f3n de real decreto-ley','Convalidaci\u00f3n del RDL 23/2026: La Palma y excedentes de financiaci\u00f3n auton\u00f3mica',300,38,10,'fiscalidad'),
('130/000054',proc,'Tramitar como proyecto de ley urgente el RDL 23/2026',345,0,0,'instituciones')]
for i,x in enumerate(b,1):add('2026-09-23',200,i,*x)
# 10 September 2026, session 196, published vote totals (selected items).
c=[
('122/000072','Enmiendas','Nacionalidad espa\u00f1ola de saharauis: enmiendas PP n\u00ba 25, 26 y 30',139,207,1,'nacionalidad'),
('122/000072','Enmiendas','Nacionalidad espa\u00f1ola de saharauis: resto de enmiendas PP',169,177,1,'nacionalidad'),
('122/000072','Dictamen','Dictamen de la proposici\u00f3n de ley de nacionalidad espa\u00f1ola de saharauis',168,31,145,'nacionalidad'),
('162/000833',pnl,'Respuesta de Estado a la crisis en Ceuta y Melilla (PNL del PP)',170,175,1,'seguridad'),
('162/000818',pnl,'Proposici\u00f3n no de ley del PSOE sobre transparencia',163,174,8,'transparencia'),
('173/000185',moc,'Moci\u00f3n VOX sobre empobrecimiento de la poblaci\u00f3n',32,177,137,'economia'),
('173/000186',moc,'Pol\u00edtica de vivienda del Gobierno, moci\u00f3n PP, punto 1.a',170,168,8,'vivienda'),
('173/000186',moc,'Pol\u00edtica de vivienda del Gobierno, moci\u00f3n PP, punto 1.b',176,43,127,'vivienda'),
('173/000186',moc,'Pol\u00edtica de vivienda del Gobierno, moci\u00f3n PP, punto 1.c',171,44,131,'vivienda'),
('173/000186',moc,'Pol\u00edtica de vivienda del Gobierno, moci\u00f3n PP, punto 1.d',183,36,127,'vivienda'),
('173/000186',moc,'Pol\u00edtica de vivienda del Gobierno, moci\u00f3n PP, punto 1.e',183,36,126,'vivienda')]
for i,x in enumerate(c,1):add('2026-09-10',196,i,*x)
d=[
('122/000287','Toma en consideraci\u00f3n','Reforma del curso de selecci\u00f3n para ingreso en la carrera judicial (PP)',295,36,15,'justicia'),
('122/000300','Toma en consideraci\u00f3n','Rebaja de la tasa m\u00e1xima de alcohol al volante (PSOE)',173,168,5,'seguridad vial')]
for i,x in enumerate(d,1):add('2026-09-29',201,i,*x)
# Two October calls by roll call; these belong to the final sitting but not the nominal CSV.
for id in ('s203-v001','s203-v002'):
    x=by_old[id].copy();x['fuente']='Listado de llamamiento y BOE (dos derogaciones)';x['calidad']='Votacion por llamamiento; totales oficiales; no incluida en el CSV nominal ordinario';x['no_vota']=None;rows.append(x)
x=by_old['demo-jornada'].copy();x['fuente']='Congreso y noticia de RTVE sobre la votacion';x['calidad']='Registro puntual documentado; no es una ley aprobada';rows.append(x)
# Only observed, verified group rows; never infer a vote from a public speech.
groups=[]
for group,si,no,ab,nv in [('SUMAR',24,0,0,2),('ERC',7,0,0,0),('EH Bildu',6,0,0,0),('PSOE',118,1,1,1),('PNV',5,0,0,0),('Mixto',8,0,1,0),('Junts',6,0,0,1),('PP',137,0,0,0)]:
    groups.append(dict(votacion_id='s202-v020',grupo=group,si=si,no=no,abstencion=ab,no_vota=nv,
                       voto_mayoritario='S\u00ed' if si>max(no,ab) else 'No',
                       fuente='Congreso Abierto: desglose sobre registro oficial'))
args=old.get('argumentos',[])
seed={'votaciones':rows,'grupos':groups,'argumentos':args,'metadata':{'cobertura':'extracto_no_exhaustivo','n_votaciones':len(rows),'fecha_revision':'2026-10-26',
       'fuente_primaria':'https://www.congreso.es/es/opendata/votaciones','advertencia':'Extractos comprobados puntuales, no inventario XV; los titulos estan resumidos.'}}
(root/'datos/muestra.json').write_text(json.dumps(seed,ensure_ascii=True,indent=2),encoding='utf8')
# Build every global from the authoritative JSON files: do not let a broad
# regular expression swallow QHV_TAX between SEED and LEGIS.
boot=root/'assets/bootstrap.js'
content=['/* Extracto documental sin cobertura completa. */']
for key,filename in [('SEED','muestra.json'),('TAX','taxonomia.json'),('LEGIS','legislaturas.json')]:
    payload=json.loads((root/'datos'/filename).read_text(encoding='utf8'))
    content.append('window.QHV_'+key+'='+json.dumps(payload,ensure_ascii=True,separators=(',',':'))+';')
boot.write_text('\n'.join(content)+'\n',encoding='utf8')
print('Registros del extracto:',len(rows),'posiciones de grupo verificadas:',len(groups))
