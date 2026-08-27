# -*- coding: utf-8 -*-
"""Ensambla el notebook de la actividad a partir de los modulos nb_parteN.py.

Uso:
    python build_notebook.py
"""

import nb_base
import nb_parte1
import nb_parte2
import nb_parte3
import nb_parte4

SALIDA = "ML_Actividad_CTG.ipynb"

if __name__ == "__main__":
    nb_parte1.construir()
    nb_parte2.construir()
    nb_parte3.construir()
    nb_parte4.construir()

    n = nb_base.escribir(SALIDA)
    n_codigo = sum(1 for c in nb_base.CELDAS if c["cell_type"] == "code")
    print("Notebook generado: %s" % SALIDA)
    print("  Celdas totales   : %d" % n)
    print("  Celdas de codigo : %d" % n_codigo)
    print("  Celdas Markdown  : %d" % (n - n_codigo))
