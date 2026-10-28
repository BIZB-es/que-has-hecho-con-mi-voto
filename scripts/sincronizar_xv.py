#!/usr/bin/env python3
"""Download or ingest the XV plenary vote CSVs, audit them, and build yearly bundles.

No data is fabricated, coverage is ALWAYS reported as partial until an independent
official inventory (including non-nominal cases) has been reconciled. This workflow
uses Congreso Abierto's CC BY 4.0 CSV tables, derived from official Congress files.

Usage on a machine with internet:
  python scripts/sincronizar_xv.py --descargar --url-votaciones URL_CSV_VOTOS --url-grupos URL_CSV_GRUPOS
Or with user-downloaded CSVs (no network):
  python scripts/sincronizar_xv.py --votaciones /tmp/votaciones.csv --grupos /tmp/votos-grupo.csv
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
LIMIT=350

def readrows(path):
    text=Path(path).read_text(encoding='utf-8-sig')
    delimiter=';' if text.splitlines()[0].count(';')>text.splitlines()[0].count(',') else ','
    data=list(csv.DictReader(io.StringIO(text),delimiter=delimiter))
    if not data:raise ValueError(f'{path}: CSV sin filas')
    return data

def load_url(url,target):
    req=urllib.request.Request(url,headers={'User-Agent':'QHV-investigacion-0.4 (+https://www.congreso.es/es/opendata/votaciones)','Accept':'text/csv,text/plain,application/octet-stream'})
    err=None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req,timeout=40) as r:
                raw=r.read(90*1024*1024+1)
                if len(raw)>90*1024*1024:raise ValueError('Archivo supera 90 MB')
                if b'<html' in raw[:1000].lower():raise ValueError('La URL devuelve una pagina, no CSV')
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(raw)
                return
        except Exception as e:err=e;time.sleep(1)
    raise RuntimeError(f'Fallo de descarga {url}: {err}')

def number(v):
    try:return int(str(v or '0').strip())
    except ValueError:return None

def audit(votes, groups, min_expected, min_groups):
    problems=[];warnings=[];ids=set();dates=[];cross={};missing_source=0;nonvote=0
    for r in votes:
        k=str(r.get('id','')).strip()
        if not k:problems.append('Fila sin identificador');continue
        if k in ids:problems.append('ID de votacion duplicado: '+k)
        ids.add(k)
        d=str(r.get('fecha',''));dates.append(d)
        if not re.fullmatch(r'20\d{2}-\d\d-\d\d',d):problems.append('Fecha invalida: '+k+':'+d)
        vals=[number(r.get(x)) for x in ('si','no','abstencion','no_vota')]
        if any(v is None or v<0 for v in vals):problems.append('Total invalido: '+k)
        elif sum(vals)>LIMIT:problems.append('La suma de votos excede 350: '+k)
        if not r.get('titulo'):problems.append('Titulo vacio: '+k)
        if not str(r.get('url_votacion','')).startswith('https://www.congreso.es/'):missing_source+=1
        cross[k]=r
    if len(votes)<min_expected:problems.append(f'Hay solo {len(votes)} registros; umbral de seguridad {min_expected}. No se publica como base XV.')
    s202=next((x for x in votes if x.get('id')=='s202-v020'),None)
    if s202 and tuple(number(s202.get(k)) for k in ('si','no','abstencion'))!=(343,1,2):
        warnings.append('S202 V20 no coincide con el listado oficial de 30/09/2026: 343-1-2')
    elif not s202:warnings.append('No consta S202 V20, el listado puede usar un ID alternativo o estar incompleto.')
    if len(groups)<min_groups:problems.append(f'Solo {len(groups)} filas de grupos; umbral minimo {min_groups}; no se publica.')
    group_ids=set();agg={};bad_group=0
    for r in groups:
        vid=str(r.get('votacion_id','')).strip();group=str(r.get('grupo','')).strip();key=(vid,group)
        if key in group_ids:problems.append('Fila de grupo duplicada '+str(key))
        group_ids.add(key)
        if vid not in ids:bad_group+=1;continue
        n=[number(r.get(k)) for k in ('si','no','abstencion','no_vota')]
        if any(v is None or v<0 for v in n):problems.append('Cifras de grupo invalidas: '+str(key));continue
        t=agg.setdefault(vid,[0,0,0,0]);t[:]=[a+b for a,b in zip(t,n)]
    if bad_group:warnings.append(f'{bad_group} filas de grupo sin identificador entre las votaciones descargadas')
    mismatches=[]
    for vid,total in agg.items():
        row=cross[vid];original=[number(row.get(k)) for k in ('si','no','abstencion')]
        if any(v is None for v in original):continue
        if total[:3]!=original:mismatches.append({'votacion_id':vid,'por_grupo':total[:3],'totales':original})
    if mismatches:warnings.append(f'{len(mismatches)} votaciones con discrepancias entre sumas de grupos y totales (pueden existir grupos sin atribucion).')
    if missing_source:warnings.append(f'{missing_source} votaciones sin URL oficial directa normalizada')
    return {'version':'0.4','fecha_revision':'2026-10-26','legislatura':'XV','ambito':'Votaciones nominales de Pleno incorporadas desde un tercero; sin llamamientos ni resoluciones no nominales',
            'fuente':'Congreso Abierto, datos derivados de fuentes oficiales del Congreso de los Diputados (CC BY 4.0)',
            'num_votaciones':len(votes),'num_filas_grupo':len(groups),'fechas':[min(dates) if dates else '',max(dates) if dates else ''],
            'distintos_grupos':sorted({str(x.get('grupo','')).strip() for x in groups if x.get('grupo')}),'total_votaciones_con_grupos':len(agg),
            'discordancias_grupos':mismatches[:25],'errores':problems[:70],'advertencias':warnings,
            'cobertura':'PARCIAL: no reconciliada con el listado oficial completo del Pleno',
            'referencia_cuantitativa_externa':'2175 registros publicados por Congreso Abierto, consulta 26/10/2026; referencia no equivale a completitud oficial',
            'siguiente_revision':'Inventario de fechas y ZIP oficiales; llamadas nominales ausentes; sesiones sin desglose; identidad historica de diputados y candidaturas'}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--descargar',action='store_true',help='Descargar los CSV desde las URLs publicas')
    p.add_argument('--url-votaciones',default='',help='URL real del CSV completo de votaciones de la fuente')
    p.add_argument('--url-grupos',default='',help='URL real del CSV completo de votos por grupo de la fuente')
    p.add_argument('--url-nominales',default='',help='Opcional: URL del CSV con los votos de cada diputado')
    p.add_argument('--url-candidaturas',default='',help='Opcional: URL del CSV de candidaturas con fecha')
    p.add_argument('--votaciones',type=Path)
    p.add_argument('--grupos',type=Path)
    p.add_argument('--nominales',type=Path)
    p.add_argument('--candidaturas',type=Path)
    p.add_argument('--min-votos',type=int,default=2000,help='Umbral preventivo contra descargas incompletas')
    p.add_argument('--min-grupos',type=int,default=15000,help='Umbral preventivo contra descargas incompletas de grupos')
    o=p.parse_args(argv)
    if o.descargar and (not o.url_votaciones or not o.url_grupos):p.error('Debe indicar las URLs reales de ambos CSV; no se han validado endpoints de descarga automáticos')
    if o.descargar and (o.votaciones or o.grupos):p.error('No mezclar --descargar con --votaciones/--grupos')
    if not o.descargar and (not o.votaciones or not o.grupos):p.error('Especificar --descargar o ambos CSV locales')
    if bool(o.nominales)!=bool(o.candidaturas) or bool(o.url_nominales)!=bool(o.url_candidaturas):p.error('Los votos nominales requieren tabla de candidaturas, y viceversa')
    files={}
    if o.descargar:
        for k,url in [('votaciones',o.url_votaciones),('grupos',o.url_grupos)]:
            dest=ROOT/'importaciones'/(k+'.csv');load_url(url,dest);files[k]=dest
        if o.url_nominales:
            for k,url in [('nominales',o.url_nominales),('candidaturas',o.url_candidaturas)]:
                dest=ROOT/'importaciones'/(k+'.csv');load_url(url,dest);files[k]=dest
    else:files={'votaciones':o.votaciones,'grupos':o.grupos}
    if o.nominales:files['nominales']=o.nominales;files['candidaturas']=o.candidaturas
    v=readrows(files['votaciones']);g=readrows(files['grupos'])
    report=audit(v,g,o.min_votos,o.min_grupos)
    report['archivos']={k:{'nombre':str(p.name),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for k,p in files.items()}
    path=ROOT/'datos/auditoria_XV.json';path.write_text(json.dumps(report,indent=2,ensure_ascii=True),encoding='utf8')
    print(f'Auditoria: {path}\nVotaciones: {len(v)}; grupos: {len(g)}; errores: {len(report["errores"])}; advertencias: {len(report["advertencias"])}')
    for line in report['errores']:print('ERROR:',line,file=sys.stderr)
    for line in report['advertencias']:print('AVISO:',line,file=sys.stderr)
    if report['errores']:raise SystemExit('NO PUBLICADO: errores de integridad o registros insuficientes')
    cmd=[sys.executable,str(ROOT/'scripts/construir_paquetes.py'),'--legislatura','XV','--votaciones',str(files['votaciones']),
         '--grupos',str(files['grupos']),'--fuente','Congreso Abierto / Congreso (CC BY 4.0) - corte nominal de XV', '--cobertura','parcial']
    if 'nominales' in files:cmd+=['--votos-diputado',str(files['nominales']),'--candidaturas',str(files['candidaturas'])]
    subprocess.run(cmd,check=True)
    print('Paquetes anuales creados, etiqueta de cobertura: parcial. Faltan reconciliaciones oficiales.')

if __name__=='__main__':main()
