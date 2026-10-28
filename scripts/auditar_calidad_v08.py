#!/usr/bin/env python3
"""Audita CSV reales de XV sin inferir votos ni afiliaciones. Solo stdlib.

Uso:
 python scripts/auditar_calidad_v08.py --votaciones CSV --grupos CSV --nominales CSV
Reproduce datos/calidad_XV.json, assets/calidad_XV.js y el CSV de incidencias.
"""
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parent.parent
FIELDS=('si','no','abstencion','no_vota')
LABELS=('Sí','No','Abstención','No vota')

def read_csv(path,sep=None):
    with open(path,encoding='utf-8-sig',newline='') as f:
        rows=csv.DictReader(f,delimiter=sep or ',')
        yield from rows

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def num(x):return int(x or 0)
def sesion_url(fecha):
    dd,mm,yyyy=fecha[8:10],fecha[5:7],fecha[:4]
    return 'https://www.congreso.es/es/opendata/votaciones?'+urlencode({'targetDate':f'{dd}/{mm}/{yyyy}','targetLegislatura':'XV'})

def write_json(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--votaciones',type=Path,required=True)
    ap.add_argument('--grupos',type=Path,required=True)
    ap.add_argument('--nominales',type=Path,required=True)
    args=ap.parse_args()
    V={};census=defaultdict(lambda:Counter());gr=defaultdict(lambda:Counter());sessions=defaultdict(list)
    for v in read_csv(args.votaciones):
        assert v['id'] not in V, ('ID duplicado',v['id'])
        V[v['id']]=v;sessions[(v['sesion'],v['fecha'])].append(v['id'])
    group_rows=0;group_seen=set()
    for g in read_csv(args.grupos,';'):
        uid=g['Votación'];key=(uid,g['Grupo']);assert key not in group_seen,('Grupo duplicado',key)
        assert uid in V,('ID de grupo inexistente',uid)
        group_seen.add(key)
        group_rows+=1
        for field,col in zip(FIELDS,LABELS):gr[uid][field]+=num(g[col])
    seen_nominal=set();people=set();nominal_rows=0;group_labels_per_deputy=defaultdict(set)
    for row in read_csv(args.nominales):
        uid=row['votacion_id'];pid=row['diputado_id'];vote=row['voto']
        assert uid in V, ('ID nominal inexistente',uid)
        assert vote in LABELS,(uid,vote)
        key=(uid,pid);assert key not in seen_nominal,('Voto nominal duplicado',key)
        seen_nominal.add(key);people.add(pid)
        group_labels_per_deputy[pid].add(row['grupo'])
        field=FIELDS[LABELS.index(vote)]
        census[uid][field]+=1;nominal_rows+=1
    report={'version':'0.8','fecha_revision':str(date.today()),'legislatura':'XV',
        'fuentes':{
            'votaciones':{'nombre':args.votaciones.name,'sha256':digest(args.votaciones)},
            'grupos':{'nombre':args.grupos.name,'sha256':digest(args.grupos)},
            'nominales':{'nombre':args.nominales.name,'sha256':digest(args.nominales)}},
        'recuentos_csv':{'votaciones':len(V),'filas_grupo':group_rows,'filas_nominales':nominal_rows,'identificadores_individuales_distintos':len(people),'sesiones_con_voto':len(sessions)},
        'calidad':{},'anomalias':{},'notas':[
            'Los recuentos nominales proceden exclusivamente de las filas de los CSV; no se reconstruye ningun voto.',
            'La discrepancia entre nominal y agregado no significa que un diputado cambiase el sentido del voto.',
            'El grupo de la tabla nominal puede ser retrospectivo y no se usa para calcular los totales por grupo.',
            'Las dos votaciones por llamamiento de 02/10/2026 se incorporan como registros documentales separados; no figuran en estos CSV.',
            'Los totales de la votacion y los agregados por grupo son internamente coherentes; no sustituyen cotejo de cada JSON oficial.'
        ]}
    tally=Counter();tally_by_year=defaultdict(Counter);bad_group=[];incid=[];compact={};total_missing=Counter();nonstandard=[]
    for vid,v in V.items():
        official={key:num(v[key]) for key in FIELDS}
        nom={key:census[vid][key] for key in FIELDS}
        d={key:official[key]-nom[key] for key in FIELDS}
        total=sum(official.values());available=sum(nom.values());missing=sum(d.values())
        if any(x<0 for x in d.values()):status='contradictorio'
        elif not available:status='sin_nominal'
        elif not any(d.values()):status='coincide'
        else:status='incompleto'
        if not gr[vid]:gstatus='sin_grupos'
        elif any(gr[vid][k]!=official[k] for k in FIELDS):gstatus='diferencia_grupos'
        else:gstatus='cuadra'
        tally[status]+=1;tally_by_year[v['fecha'][:4]][status]+=1;tally['filas_que_cuadran_grupos']+=(gstatus=='cuadra')
        if gstatus=='diferencia_grupos':bad_group.append(vid)
        if not re.fullmatch(r's\d+-v\d+',vid):nonstandard.append(vid)
        for k in FIELDS:total_missing[k]+=d[k]
        compact[vid]=[status,missing,*[d[k] for k in FIELDS],available,gstatus]
        if status!='coincide':incid.append({
            'votacion_id':vid,'fecha':v['fecha'],'sesion':v['sesion'],'numero':v['numero'],
            'estado':status,'nominales_disponibles':available,'total_publicado':total,
            **{f'diferencia_{k}':d[k] for k in FIELDS},
            'faltan_en_nominal':missing,'estado_grupos':gstatus,
            'url_votacion':v['url_votacion'],'url_sesion':sesion_url(v['fecha'])})
    report['calidad']={
        'filas_que_cuadran_grupos':tally['filas_que_cuadran_grupos'],
        'votaciones_con_nominal_exacto':tally['coincide'],
        'votaciones_con_nominal_incompleto':tally['incompleto'],
        'votaciones_sin_nominal':tally['sin_nominal'],
        'votaciones_con_recuento_contradictorio':tally['contradictorio'],
        'votaciones_sin_grupos':sum(not gr[vid] for vid in V),
        'discrepancias_por_sentido':dict(total_missing),
        'por_anio':{k:dict(s) for k,s in sorted(tally_by_year.items())}}
    report['anomalias']={'identificadores_descriptivos_proveedor':nonstandard,'diferencias_totales_grupo':bad_group}
    assert report['recuentos_csv']=={'votaciones':2175,'filas_grupo':19561,'filas_nominales':726564,'identificadores_individuales_distintos':350,'sesiones_con_voto':len(sessions)}
    assert tally['coincide']==95 and tally['incompleto']==2078 and tally['sin_nominal']==2 and not tally['contradictorio']
    assert tally['filas_que_cuadran_grupos']==2173 and not bad_group
    write_json(ROOT/'datos/calidad_XV.json',report)
    with open(ROOT/'datos/incidencias_nominales_XV.csv','w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(incid[0]),delimiter=';');writer.writeheader();writer.writerows(sorted(incid,key=lambda x:(x['fecha'],x['votacion_id'])))
    # tabla compacta para consultar desde las fichas sin peticiones al servidor
    (ROOT/'assets/calidad_XV.js').write_text('window.QHV_CALIDAD_XV='+json.dumps({'campos':['estado','diferencia_total','diferencia_si','diferencia_no','diferencia_abstencion','diferencia_no_vota','nominales','grupo_estado'],'por_voto':compact},ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    with open(ROOT/'datos/sesiones_XV.csv','w',encoding='utf-8-sig',newline='') as f:
        wr=csv.writer(f,delimiter=';');wr.writerow(['legislatura','sesion','fecha','votaciones_csv','url_sesion_congreso','con_expediente_v07','pendientes_expediente'])
        for (s,fecha),ids in sorted(sessions.items(),key=lambda x:x[0][1]):wr.writerow(['XV',s,fecha,len(ids),sesion_url(fecha),'',''])
    print(json.dumps(report['calidad'],ensure_ascii=False,indent=2))
    return report

if __name__=='__main__':main()
