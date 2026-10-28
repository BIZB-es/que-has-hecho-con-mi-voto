"""Verifica asociación determinista, no aproximada, sin navegar la red."""
import csv, tempfile, subprocess, sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
SOURCE=(R/'datos/votaciones_referencia_XV.csv')
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
 ref={r['id']:r for r in csv.DictReader(f,delimiter=';')}
r=ref['s2-v001']
assert (r['si'],r['no'],r['abstencion'])==('176','169','2')
template='''<html><body><h2>Proposición de reforma</h2>
<p>(Núm. expte. <a href="#">410/000001</a>)</p>
<h6>Si: {si}</h6><h6>No: {no}</h6><h6>Abstenciones: {abst}</h6>
<a href="{url}">JSON</a>
</body></html>'''
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);file=t/'2023-09-19.html';out=t/'result.csv'
 file.write_text(template.format(si=r['si'],no=r['no'],abst=r['abstencion'],url=r['url_votacion']),encoding='utf8')
 cmd=[sys.executable,str(R/'scripts/proponer_expedientes_v08.py'),'--html-dir',str(t),'--desde','2023-09-19','--hasta','2023-09-19','--out',str(out)]
 subprocess.run(cmd,check=True)
 with out.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter=';'))
 assert len(rows)==1 and rows[0]['votacion_id']=='s2-v001' and rows[0]['expediente_candidato']=='410/000001'
 out.unlink()
 # Las sumas incorrectas no autorizan asociación
 file.write_text(template.format(si=175,no=169,abst=2,url=r['url_votacion']),encoding='utf8')
 subprocess.run(cmd,check=True)
 assert not out.exists()
 print('OK parser: enlace oficial + recuentos verificados; rechazo con recuentos distintos.')
