# -*- coding: utf-8 -*-
"""Infraestructura minima para construir el notebook celda a celda.

El cuaderno de la actividad se genera por codigo (y no editando el .ipynb a
mano) para que sea reproducible y facil de versionar: cada celda se declara
como una cadena de texto en los modulos `nb_parteN.py` y este modulo las
ensambla en el formato JSON de nbformat v4.
"""

import json

CELDAS = []


def md(texto):
    """Anade una celda Markdown al cuaderno.

    Parametros
    ----------
    texto : str
        Contenido Markdown de la celda.
    """
    CELDAS.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": texto.strip("\n").splitlines(keepends=True),
    })


def code(texto):
    """Anade una celda de codigo Python al cuaderno.

    Parametros
    ----------
    texto : str
        Codigo fuente de la celda.
    """
    CELDAS.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": texto.strip("\n").splitlines(keepends=True),
    })


def escribir(ruta):
    """Serializa las celdas acumuladas como un notebook nbformat v4.

    Parametros
    ----------
    ruta : str
        Ruta del archivo .ipynb de salida.
    """
    cuaderno = {
        "cells": CELDAS,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.14.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(cuaderno, fh, ensure_ascii=False, indent=1)
    return len(CELDAS)
