"""Documenta y revisa la diferencia entre la muestra y paquetes precargados."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent.parent
m=json.loads((root/'datos/paquetes.json').read_text())
packs=[x for x in m.get('paquetes',[]) if x['legislatura']=='XV']
count=sum(x['registros'] for x in packs)
print('Paquetes XV:',len(packs),'| Registros:',count)
print('Aplicación: cuando hay >= 2.000 registros en los paquetes, los carga automáticamente al abrirla por HTTP(S).')
