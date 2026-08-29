# -*- coding: utf-8 -*-
"""Compara las salidas del cuaderno antes y despues de reejecutarlo."""
import io, json, re

previo = json.load(io.open(
    'C:/Users/ABELME~1/AppData/Local/Temp/claude/D--Abel-TrabajosConClaude/'
    '05200e69-9fa4-413c-a72b-c074ca9030e1/scratchpad/ipynb_previo.json',
    encoding='utf-8'))
nuevo = json.load(io.open('ML_Actividad_CTG.ipynb', encoding='utf-8'))

def por_celda(nb):
    d = {}
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        fuente = ''.join(c['source'])
        m = re.search(r'# Celda ([\d.]+)\.', fuente)
        if not m:
            continue
        partes = []
        for o in c.get('outputs', []):
            if o.get('output_type') == 'stream':
                partes.append(''.join(o['text']))
            elif 'data' in o:
                if 'text/plain' in o['data'] and 'image/png' not in o['data']:
                    partes.append(''.join(o['data']['text/plain']))
                if 'image/png' in o['data']:
                    partes.append('<imagen %d bytes>' % len(o['data']['image/png']))
        d[m.group(1)] = ''.join(partes)
    return d

a, b = por_celda(previo), por_celda(nuevo)
cambiadas = [k for k in b if a.get(k) != b[k]]
print('celdas de codigo:', len(b), '| ejecutadas:',
      sum(1 for c in nuevo['cells'] if c['cell_type'] == 'code' and c.get('execution_count')))
print('celdas con salida distinta:', cambiadas)
for k in cambiadas:
    if k not in ('1.1', '2.3'):
        print('  --- INESPERADO en', k)
        print('  antes:', repr(a.get(k, ''))[:300])
        print('  ahora:', repr(b[k])[:300])
