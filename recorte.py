# -*- coding: utf-8 -*-
"""Suprime de las capturas de Colab la franja que ocupa el grafico, porque el
informe lo reproduce a continuacion como figura en formato APA y de otro modo
apareceria dos veces.

Las franjas se dan en pixeles de la captura original y se comprobaron una a una
sobre la imagen; no se deducen de la imagen porque ninguna regla automatica
separa con fiabilidad el borde inferior de un grafico de la primera linea de la
salida de texto que viene despues.
"""

import pathlib

from PIL import Image

FRANJA_GRAFICO = {
    "2.4": (884, 1699),
    "2.5": (998, 2155),
    "3.4": (941, 99999),
    "4.2": (1366, 1737),
    "5.2": (1202, 99999),
    "5.6": (1131, 1975),
    "6.2": (675, 99999),
    "6.3": (915, 1242),
    "6.4": (1325, 99999),
    "6.6": (733, 1093),
    "6.8": (1227, 99999),
    "6.9": (1074, 1494),
    "6.10": (1275, 99999),
}


def sin_grafico(clave, origen, destino):
    """Devuelve la ruta de la captura sin el grafico; la genera si hace falta."""
    origen = pathlib.Path(origen)
    if clave not in FRANJA_GRAFICO:
        return origen
    destino = pathlib.Path(destino)
    if destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime:
        return destino
    imagen = Image.open(str(origen))
    arriba, abajo = FRANJA_GRAFICO[clave]
    abajo = min(abajo, imagen.height)
    trozos = []
    if arriba > 0:
        trozos.append(imagen.crop((0, 0, imagen.width, arriba)))
    if abajo < imagen.height:
        trozos.append(imagen.crop((0, abajo, imagen.width, imagen.height)))
    alto = sum(t.height for t in trozos)
    recortada = Image.new("RGB", (imagen.width, alto), "white")
    y = 0
    for trozo in trozos:
        recortada.paste(trozo, (0, y))
        y += trozo.height
    destino.parent.mkdir(parents=True, exist_ok=True)
    recortada.save(str(destino))
    return destino
