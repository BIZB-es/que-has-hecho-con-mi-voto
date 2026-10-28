#!/usr/bin/env python3
"""Produce static annual JSON packages from CSV exports. No data is fabricated.

Supported source: Congreso Abierto XV (votaciones.csv, votos-grupo.csv,
votos-diputado.csv, diputados.csv); or normalized historic CSV with same columns and
legislatura column (or a separate --legislatura for each import).

Party attribution is explicitly electoral candidacy at the record date, when the
metadata permits that inference. Not an assumption about parliamentary group.
"""
from __future__ import annotations
import argparse, collections, csv, datetime as dt, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DATES=json.loads((ROOT/'datos/legislaturas.json').read_text(encoding='utf8'))['legislaturas']
LEGS={x['id']:x for x in DATES}

def readrows(path):
    if not path:return
    path=Path(path)
    if path.suffix.lower()=='.json':
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(obj,dict):obj=obj.get('votaciones',obj.get('grupos',obj.get('partidos',[])))
        if not isinstance(obj,list):raise ValueError(f'{path}: JSON must contain an array')
        for r in obj:yield r
        return
    with path.open(encoding='utf-8-sig',newline='') as f:
        first=f.readline();f.seek(0)
        delim=';' if first.count(';')>first.count(',') else ','
        rd=csv.DictReader(f,delimiter=delim)
        if not rd.fieldnames:raise ValueError(f'{path}: CSV empty')
        for r in rd:yield r

def is_in(r,leg,date_from,date_to):
    l=str(r.get('legislatura') or leg).upper().strip()
    return (l==leg and (not date_from or r.get('fecha','')>=date_from)
            and (not date_to or r.get('fecha','')<=date_to))

def stance(x):
    z=[(int(x.get('si') or 0),'Sí'),(int(x.get('no') or 0),'No'),(int(x.get('abstencion') or 0),'Abstención')]
    top=max(i for i,_ in z)
    if top==0:return 'Sin votos emitidos'
    if sum(1 for i,_ in z if i==top)>1:return 'Dividido / empate'
    return next(t for i,t in z if i==top)

def load_roster(leg, path):
    out={};ambiguity=0
    for row in readrows(path):
        if row.get('legislatura',leg)!=leg:continue
        key=str(row.get('id') or row.get('diputado_id') or '').strip()
        candidature=str(row.get('partido') or row.get('candidatura') or '').strip()
        if not key or not candidature:continue
        start=row.get('fecha_alta','')[:10]; end=row.get('fecha_baja','')[:10]
        if key in out and out[key]['candidatura']!=candidature:ambiguity+=1
        out[key]={'candidatura':candidature,'start':start,'end':end}
    return out, ambiguity

def party_aggregate(nominal,roster,leg,ids, date_of):
    tally=collections.defaultdict(lambda:{'si':0,'no':0,'abstencion':0,'no_vota':0})
    without=0;unknown=0
    for row in readrows(nominal):
        if row.get('legislatura',leg)!=leg:continue
        vid=str(row.get('votacion_id') or '').strip()
        if vid not in ids:continue
        pid=str(row.get('diputado_id') or '').strip()
        meta=roster.get(pid)
        if not meta:without+=1;continue
        date=date_of.get(vid,'')
        if (meta['start'] and meta['start']>date) or (meta['end'] and meta['end']<date):without+=1;continue
        candidature=meta['candidatura'];
        # Party means electoral candidature; no retroactive membership claims.
        s=str(row.get('voto','')).lower().strip()
        if s in ('sí','si','a favor','favor'):category='si'
        elif s in ('no','en contra'):category='no'
        elif s.startswith('abst'):category='abstencion'
        elif s in ('no vota','ausente','ausentes','no ha votado'):category='no_vota'
        else:unknown+=1;continue
        tally[(vid,candidature)][category]+=1
    out=[]
    for (vid,candidature),v in tally.items():
        out.append({'votacion_id':vid,'partido':candidature,**v,'voto_mayoritario':stance(v)})
    return out,without,unknown

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--legislatura',required=True,choices=list(LEGS))
    p.add_argument('--votaciones',required=True,type=Path)
    p.add_argument('--grupos',type=Path)
    p.add_argument('--partidos',type=Path,help='Precomputed party/candidature vote counts')
    p.add_argument('--votos-diputado',type=Path,help='Official individual vote CSV')
    p.add_argument('--candidaturas',type=Path,help='Deputy ID and electoral candidature from Congress; needs --votos-diputado')
    p.add_argument('--desde',type=str,default='')
    p.add_argument('--hasta',type=str,default='')
    p.add_argument('--fuente',default='Congreso de los Diputados: datos abiertos')
    p.add_argument('--cobertura',choices=['parcial','completa'],default='parcial')
    p.add_argument('--ref-verificacion',default='',help='Required to claim full official coverage')
    opt=p.parse_args(argv)
    if opt.cobertura=='completa' and not opt.ref_verificacion: p.error('--cobertura completa requires --ref-verificacion with a public reconciliation report')
    if opt.votos_diputado and not opt.candidaturas or opt.candidaturas and not opt.votos_diputado:p.error('Provide --votos-diputado and --candidaturas together')
    if opt.desde and opt.hasta and opt.desde>opt.hasta:p.error('desde must be <= hasta')
    leg=opt.legislatura
    votes=[x for x in readrows(opt.votaciones) if is_in(x,leg,opt.desde,opt.hasta)]
    if not votes:raise SystemExit('No votes in requested range; no files changed')
    for r in votes:
        if not r.get('id') or not r.get('fecha') or not r.get('titulo'):raise ValueError(f'Incomplete record: {r}')
        if not LEGS[leg]['inicio']<=r['fecha']<=LEGS[leg]['fin']:raise ValueError(f'{leg}: date out of legislature: {r["fecha"]}')
    id_set={r['id'] for r in votes}
    if len(id_set)!=len(votes):raise ValueError('Duplicate vote IDs in same legislature')
    groupRows=[x for x in readrows(opt.grupos) if x.get('votacion_id') in id_set] if opt.grupos else []
    partyRows=[x for x in readrows(opt.partidos) if x.get('votacion_id') in id_set] if opt.partidos else []
    missing=0;unread=0;ambig=0
    if opt.votos_diputado:
        roster,ambig=load_roster(leg,opt.candidaturas)
        extra,missing,unread=party_aggregate(opt.votos_diputado,roster,leg,id_set,{v['id']:v['fecha'] for v in votes})
        partyRows.extend(extra)
    errors=[]
    by_year=collections.defaultdict(lambda:{'votaciones':[],'grupos':[],'partidos':[]})
    year_id={}
    for v in votes:
        y=v['fecha'][:4];year_id[v['id']]=y;by_year[y]['votaciones'].append(v)
    for g in groupRows:
        by_year[year_id[g['votacion_id']]]['grupos'].append(g)
    for x in partyRows:
        by_year[year_id[x['votacion_id']]]['partidos'].append(x)
    target=ROOT/'datos/historico';target.mkdir(parents=True,exist_ok=True)
    manifest_path=ROOT/'datos/paquetes.json';manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    existing={(x['legislatura'],x.get('anio')):x for x in manifest.get('paquetes',[])}
    for y,pack in sorted(by_year.items()):
        pack['votaciones'].sort(key=lambda r:(r['fecha'],str(r['id'])))
        data={'legislatura':leg,'anio':y,'votaciones':pack['votaciones'],'grupos':pack['grupos'],'partidos':pack['partidos'],'procedencia':opt.fuente,
              'nota':'Votaciones registradas y posiciones de grupos o candidaturas; candidatura NO significa afiliación política en esa fecha.'}
        dest=target/f'{leg}-{y}.json'
        raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf8')
        sha=hashlib.sha256(raw).hexdigest();dest.write_bytes(raw)
        entry={'legislatura':leg,'anio':y,'ruta':'datos/historico/'+dest.name,'desde':min(v['fecha'] for v in pack['votaciones']),
               'hasta':max(v['fecha'] for v in pack['votaciones']),'registros':len(pack['votaciones']),
               'cobertura':opt.cobertura,'fuente':opt.fuente,'sha256':sha,'ref_verificacion':opt.ref_verificacion or ''}
        existing[(leg,y)]=entry
        print(f'{dest}: {len(pack["votaciones"])} votos, {len(pack["grupos"])} grupos, {len(pack["partidos"])} partidos/candidaturas')
    manifest['paquetes']=sorted(existing.values(),key=lambda x:(x['legislatura'],x['anio']))
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print('Sin atribución de candidatura:',missing,' | Voto nominal no reconocido:',unread,' | Fichas electorales conflictivas:',ambig)
    print('Total paquetes registrados:',len(manifest['paquetes']))
    if missing or unread or ambig:print('ADVERTENCIA: revisar los casos no atribuibles antes de publicar una estadística de partidos.',file=sys.stderr)
if __name__=='__main__':main()
