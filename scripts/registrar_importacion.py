"""Actualiza el estado editorial al concluir la importación de dos CSV íntegros."""
import json, argparse
from pathlib import Path
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--votaciones',required=True);p.add_argument('--grupos',required=True);args=p.parse_args()
report_path=root/'datos/auditoria_XV.json'
if not report_path.exists():raise SystemExit('No se publica sin un informe de auditoría')
r=json.loads(report_path.read_text())
if r.get('errores') or r.get('num_votaciones',0)<2175 or r.get('num_filas_grupo',0)<19561:raise SystemExit('No se alcanzó la referencia mínima documentada: 2175 / 19561')
s=root/'datos/estado_publicacion.json';state=json.loads(s.read_text())
state.update({'version':'0.5','estado':'Catálogo nominal XV incorporado de archivos fuente; solo el ámbito nominal, pendientes las votaciones no nominales',
              'registros_XV_precargados':r['num_votaciones'],'desgloses_de_grupo_precargados':r['num_filas_grupo'],
              'auditoria_nominal_completa':'datos/auditoria_XV.json',
              'modo_de_ingesta':'CSV auditados + paquetes históricos anuales'})
s.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
print('Estado de publicación actualizado: votos',r['num_votaciones'],'grupos',r['num_filas_grupo'])
