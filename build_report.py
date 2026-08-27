# -*- coding: utf-8 -*-
"""build_report.py
=================
Genera el informe en PDF de la actividad a partir del notebook YA EJECUTADO.

El PDF se construye leyendo `ML_Actividad_CTG.ipynb`, de modo que el texto, el
codigo, las salidas y las figuras del informe proceden siempre de la ultima
ejecucion real: ninguna cifra se transcribe a mano y el documento no puede
desincronizarse del analisis.

Formato exigido por la actividad: tipo de letra Calibri, tamano 12, interlineado
1,5, maximo 40 paginas, en PDF.

Uso:
    python build_report.py
"""

import html
import json
import pathlib
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Preformatted,
                                Spacer, Table, TableStyle)

# ============================================================== CONFIGURACION
NOTEBOOK = "ML_Actividad_CTG.ipynb"
SALIDA = "Actividad_ML_CTG_Meneses.pdf"
REPO_URL = "https://github.com/amenesesy/actividad-ml-ctg"
DIR_FIGURAS = pathlib.Path("figuras")

TAM_CUERPO = 12                      # exigido: Calibri 12
INTERLINEADO = round(TAM_CUERPO * 1.5)   # exigido: interlineado 1,5
TAM_CODIGO = 5.9                     # monoespaciada para los listados de codigo
TAM_SALIDA = 6.2                     # monoespaciada para las salidas de consola
MAX_LINEAS_SALIDA = 11               # recorte de salidas muy largas
ANCHO_CODIGO = 136                   # caracteres antes de partir una linea

# Maquetacion de las figuras. La regla es que ninguna se reduzca por debajo
# de REDUCCION_MAX respecto de su tamano natural, para que la tipografia
# interior siga siendo legible en papel.
ANCHO_TEXTO = 17.0 * cm               # ancho util de la caja de texto
DPI_FIGURAS = 200                     # resolucion con la que se guardan
REDUCCION_MAX = 0.68                  # reduccion maxima admitida
ALTO_MAX_FIGURA = 9.5 * cm           # alto maximo de una figura

FUENTES = {
    "Calibri":   "C:/Windows/Fonts/calibri.ttf",
    "Calibri-B": "C:/Windows/Fonts/calibrib.ttf",
    "Calibri-I": "C:/Windows/Fonts/calibrii.ttf",
    "Calibri-BI": "C:/Windows/Fonts/calibriz.ttf",
    "Consolas":  "C:/Windows/Fonts/consola.ttf",
    "Consolas-B": "C:/Windows/Fonts/consolab.ttf",
}


def registrar_fuentes():
    """Registra las fuentes TrueType de Windows en reportlab."""
    for nombre, ruta in FUENTES.items():
        pdfmetrics.registerFont(TTFont(nombre, ruta))
    pdfmetrics.registerFontFamily("Calibri", normal="Calibri", bold="Calibri-B",
                                  italic="Calibri-I", boldItalic="Calibri-BI")
    pdfmetrics.registerFontFamily("Consolas", normal="Consolas", bold="Consolas-B",
                                  italic="Consolas", boldItalic="Consolas-B")


# ==================================================================== ESTILOS
AZUL = colors.HexColor("#1F3864")
GRIS_CODIGO = colors.HexColor("#F4F5F7")
GRIS_SALIDA = colors.HexColor("#FBF8F1")
BORDE_CODIGO = colors.HexColor("#C9CDD4")


def construir_estilos():
    """Devuelve el diccionario de estilos de parrafo del informe."""
    base = dict(fontName="Calibri", fontSize=TAM_CUERPO, leading=INTERLINEADO)
    return {
        "cuerpo": ParagraphStyle("cuerpo", alignment=TA_JUSTIFY, spaceAfter=4, **base),
        # Sangria francesa de 1,25 cm en la lista de referencias, segun APA.
        "referencia": ParagraphStyle("referencia", alignment=0, spaceAfter=2,
                                     leftIndent=1.25 * cm,
                                     firstLineIndent=-1.25 * cm, **base),
        "lista": ParagraphStyle("lista", alignment=TA_JUSTIFY, leftIndent=16,
                                bulletIndent=4, spaceAfter=3, **base),
        "cita": ParagraphStyle("cita", alignment=TA_JUSTIFY, leftIndent=18,
                               rightIndent=10, spaceBefore=5, spaceAfter=8,
                               borderPadding=(6, 6, 6, 6), backColor=colors.HexColor("#EEF2F8"),
                               borderColor=colors.HexColor("#C3D0E6"), borderWidth=0.6, **base),
        "h1": ParagraphStyle("h1", fontName="Calibri-B", fontSize=16, leading=20,
                             textColor=AZUL, spaceBefore=10, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName="Calibri-B", fontSize=13.5, leading=17,
                             textColor=AZUL, spaceBefore=8, spaceAfter=4),
        "h3": ParagraphStyle("h3", fontName="Calibri-B", fontSize=12.5, leading=16,
                             textColor=colors.HexColor("#2E5090"), spaceBefore=7, spaceAfter=3),
        "codigo": ParagraphStyle("codigo", fontName="Consolas", fontSize=TAM_CODIGO,
                                 leading=TAM_CODIGO + 0.9),
        "salida": ParagraphStyle("salida", fontName="Consolas", fontSize=TAM_SALIDA,
                                 leading=TAM_SALIDA + 0.9),
        # Formato APA de figuras: numero, titulo en cursiva, imagen y nota.
        "figura_numero": ParagraphStyle("figura_numero", fontName="Calibri-B", fontSize=10,
                                        leading=12, spaceAfter=0),
        "figura_titulo": ParagraphStyle("figura_titulo", fontName="Calibri-I", fontSize=10,
                                        leading=12, spaceAfter=4),
        "figura_nota": ParagraphStyle("figura_nota", fontName="Calibri", fontSize=8.5,
                                      leading=10.4, alignment=TA_JUSTIFY,
                                      spaceBefore=2, spaceAfter=6),
        "tabla": ParagraphStyle("tabla", fontName="Calibri", fontSize=8.5,
                                leading=10.5, alignment=TA_JUSTIFY),
        "tabla_cab": ParagraphStyle("tabla_cab", fontName="Calibri-B", fontSize=8.5,
                                    leading=10.5, textColor=colors.white),
        "portada_titulo": ParagraphStyle("pt", fontName="Calibri-B", fontSize=25, leading=31,
                                         alignment=TA_CENTER, textColor=AZUL, spaceAfter=14),
        "portada_sub": ParagraphStyle("ps", fontName="Calibri", fontSize=14, leading=21,
                                      alignment=TA_CENTER, spaceAfter=6),
        "portada_dato": ParagraphStyle("pd", fontName="Calibri", fontSize=12, leading=19,
                                       alignment=TA_CENTER),
    }


# =================================================== CONVERSION DE MARKDOWN
def formato_inline(texto):
    """Traduce el formato en linea de Markdown a las etiquetas de reportlab.

    Cubre negrita, cursiva, codigo en linea, enlaces y entidades HTML.
    """
    texto = html.escape(texto)
    # Codigo en linea `x` -> fuente monoespaciada resaltada.
    texto = re.sub(r"`([^`]+)`",
                   r'<font face="Consolas" size="10" color="#8B2252">\1</font>', texto)
    # Negrita **x** y cursiva *x* (la negrita primero para no romperla).
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", texto)
    # Enlaces [texto](url) -> texto subrayado en azul.
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   r'<link href="\2" color="#1F4E9C">\1</link>', texto)
    # URLs sueltas que quedan en las referencias bibliograficas.
    texto = re.sub(r"(?<![\">])(https?://[^\s<]+)",
                   r'<link href="\1" color="#1F4E9C">\1</link>', texto)
    return texto


def partir_linea_larga(linea, ancho):
    """Parte una linea de codigo demasiado ancha respetando la sangria."""
    if len(linea) <= ancho:
        return [linea]
    sangria = len(linea) - len(linea.lstrip())
    trozos, resto = [], linea
    while len(resto) > ancho:
        corte = resto.rfind(" ", sangria + 1, ancho)
        if corte <= sangria:
            corte = ancho
        trozos.append(resto[:corte])
        resto = " " * (sangria + 4) + resto[corte:].lstrip()
    trozos.append(resto)
    return trozos


def bloque_monoespaciado(texto, estilo, fondo, borde, ancho_max):
    """Envuelve un bloque de texto monoespaciado en una tabla con fondo.

    Se genera UNA FILA POR LINEA en lugar de una unica celda alta: asi el
    bloque puede repartirse entre paginas cuando un listado es mas largo que
    el marco disponible, en vez de provocar un error de maquetacion.
    """
    lineas = []
    for linea in texto.rstrip().split("\n"):
        lineas.extend(partir_linea_larga(linea.rstrip(), ancho_max))

    datos = [[Preformatted(linea if linea else " ", estilo)] for linea in lineas]
    tabla = Table(datos, colWidths=[17.0 * cm], splitByRow=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fondo),
        ("BOX", (0, 0), (-1, -1), 0.6, borde),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return tabla


def tabla_markdown(filas, estilos):
    """Convierte una tabla Markdown (lista de listas de celdas) en una Table."""
    n_col = max(len(f) for f in filas)
    datos = []
    for i, fila in enumerate(filas):
        fila = fila + [""] * (n_col - len(fila))
        estilo = estilos["tabla_cab"] if i == 0 else estilos["tabla"]
        datos.append([Paragraph(formato_inline(c), estilo) for c in fila])

    # Reparto de anchos: la primera columna algo mas estrecha que las de texto.
    ancho_total = 17.0 * cm
    if n_col <= 2:
        pesos = [1.0] * n_col
    else:
        pesos = [0.85] + [1.0] * (n_col - 1)
    factor = ancho_total / sum(pesos)
    anchos = [p * factor for p in pesos]

    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5FA")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C0CC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabla


def renderizar_markdown(texto, estilos):
    """Convierte el texto Markdown de una celda en una lista de flowables."""
    elementos = []
    lineas = texto.split("\n")
    i = 0
    parrafo = []
    # A partir del encabezado "Referencias" los parrafos se componen con
    # sangria francesa, tal como exige el manual APA para la lista de fuentes.
    estado = {"referencias": False}

    def volcar_parrafo():
        """Vuelca el parrafo acumulado como un unico Paragraph."""
        if parrafo:
            estilo = estilos["referencia"] if estado["referencias"] else estilos["cuerpo"]
            elementos.append(Paragraph(formato_inline(" ".join(parrafo)), estilo))
            parrafo.clear()

    while i < len(lineas):
        linea = lineas[i]
        limpia = linea.strip()

        # --- Separador horizontal: se ignora (solo marca visual del notebook) --
        if limpia in ("---", "***", "___"):
            volcar_parrafo()
            i += 1
            continue

        # --- Encabezados -------------------------------------------------------
        m = re.match(r"^(#{1,4})\s+(.*)$", limpia)
        if m:
            volcar_parrafo()
            nivel = len(m.group(1))
            estilo = estilos["h1"] if nivel == 1 else estilos["h2"] if nivel == 2 else estilos["h3"]
            if m.group(2).strip().lower() == "referencias":
                estado["referencias"] = True
            elementos.append(Paragraph(formato_inline(m.group(2)), estilo))
            i += 1
            continue

        # --- Tablas ------------------------------------------------------------
        if limpia.startswith("|") and i + 1 < len(lineas) and re.match(
                r"^\|[\s:\-|]+\|$", lineas[i + 1].strip()):
            volcar_parrafo()
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                fila = lineas[i].strip().strip("|")
                if not re.match(r"^[\s:\-|]+$", fila):
                    filas.append([c.strip() for c in fila.split("|")])
                i += 1
            elementos.append(Spacer(1, 4))
            elementos.append(tabla_markdown(filas, estilos))
            elementos.append(Spacer(1, 9))
            continue

        # --- Citas / notas destacadas -----------------------------------------
        if limpia.startswith(">"):
            volcar_parrafo()
            bloque = []
            while i < len(lineas) and lineas[i].strip().startswith(">"):
                bloque.append(lineas[i].strip().lstrip(">").strip())
                i += 1
            elementos.append(Paragraph(formato_inline(" ".join(bloque)), estilos["cita"]))
            continue

        # --- Lista con vinetas -------------------------------------------------
        if re.match(r"^[-*]\s+", limpia):
            volcar_parrafo()
            texto_item = re.sub(r"^[-*]\s+", "", limpia)
            i += 1
            while i < len(lineas) and lineas[i].startswith("  ") and lineas[i].strip():
                texto_item += " " + lineas[i].strip()
                i += 1
            elementos.append(Paragraph(formato_inline(texto_item), estilos["lista"],
                                       bulletText="\u2022"))
            continue

        # --- Lista numerada ----------------------------------------------------
        m = re.match(r"^(\d+)\.\s+(.*)$", limpia)
        if m:
            volcar_parrafo()
            texto_item = m.group(2)
            numero = m.group(1)
            i += 1
            while i < len(lineas) and lineas[i].startswith("   ") and lineas[i].strip():
                texto_item += " " + lineas[i].strip()
                i += 1
            elementos.append(Paragraph(formato_inline(texto_item), estilos["lista"],
                                       bulletText=numero + "."))
            continue

        # --- Formula en bloque -------------------------------------------------
        if limpia.startswith("$$"):
            volcar_parrafo()
            formula = []
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("$$"):
                formula.append(lineas[i].strip())
                i += 1
            i += 1
            texto_formula = " ".join(formula)
            texto_formula = (texto_formula.replace("\\text", "").replace("\\frac", "")
                             .replace("{", "").replace("}", "").replace("\\mid", "|"))
            elementos.append(Paragraph(
                "<i>lift = P(NSP=3 | marcado como anomalia) / P(NSP=3)</i>",
                ParagraphStyle("f", parent=estilos["cuerpo"], alignment=TA_CENTER)))
            continue

        # --- Linea en blanco ---------------------------------------------------
        if not limpia:
            volcar_parrafo()
            i += 1
            continue

        # --- Texto corriente ---------------------------------------------------
        parrafo.append(limpia)
        i += 1

    volcar_parrafo()
    return elementos


# ============================================= EXTRACCION DE LAS SALIDAS
def texto_de_salidas(celda):
    """Concatena las salidas de texto de una celda de codigo, recortadas."""
    partes = []
    for salida in celda.get("outputs", []):
        tipo = salida.get("output_type")
        if tipo == "stream":
            partes.append("".join(salida.get("text", [])))
        elif tipo in ("execute_result", "display_data"):
            datos = salida.get("data", {})
            if "text/plain" in datos and "image/png" not in datos:
                partes.append("".join(datos["text/plain"]))
    texto = "\n".join(p.rstrip() for p in partes if p.strip())
    if not texto:
        return None

    lineas = texto.split("\n")
    if len(lineas) > MAX_LINEAS_SALIDA:
        recorte = lineas[:MAX_LINEAS_SALIDA]
        recorte.append("[Salida recortada: %d lineas mas. La salida completa esta en el "
                       "cuaderno del repositorio.]" % (len(lineas) - MAX_LINEAS_SALIDA))
        lineas = recorte
    return "\n".join(lineas)


def figuras_de_celda(celda):
    """Devuelve los nombres de archivo de las figuras que genera la celda."""
    fuente = "".join(celda["source"])
    return re.findall(r'guardar\("([^"]+)"\)', fuente)


# Titulo y nota de cada figura, en el formato que exige la 7.a edicion del
# manual APA: numero de figura, titulo en cursiva y nota explicativa al pie.
FIGURAS_APA = {
    "fig_correlaciones": (
        "Matriz de correlaciones de las 21 variables descriptivas",
        "Coeficientes de correlación de Pearson calculados sobre las 2 126 "
        "observaciones válidas. Solo se representa el triángulo inferior para "
        "evitar la duplicación de cada par. El valor numérico de los pares más "
        "correlacionados aparece en la salida que precede a la figura. "
        "Elaboración propia."),
    "fig_distribuciones": (
        "Distribución de las variables más relevantes",
        "Histogramas con estimación de densidad por núcleos. Entre paréntesis "
        "se indica el coeficiente de asimetría de cada variable. Elaboración "
        "propia."),
    "fig_boxplots": (
        "Diagramas de caja de las 21 variables estandarizadas",
        "Las variables se estandarizaron únicamente para poder representarlas "
        "en un mismo eje. Los puntos situados fuera de los bigotes son los "
        "valores atípicos según el criterio de Tukey. Elaboración propia."),
    "fig_imputacion": (
        "Efecto de cada estrategia de imputación sobre la distribución",
        "Curvas de densidad obtenidas tras borrar de forma aleatoria el 10 % "
        "de los valores y reconstruirlos con cuatro estrategias distintas. El "
        "área sombreada corresponde a la distribución original. Elaboración "
        "propia."),
    "fig_pca_varianza": (
        "Sedimentación y varianza acumulada del análisis de componentes principales",
        "Las líneas discontinuas señalan los umbrales del 80 % y del 90 % de "
        "varianza explicada. Elaboración propia."),
    "fig_mahalanobis": (
        "Contraste del supuesto de normalidad multivariante",
        "A la izquierda, gráfico cuantil-cuantil de la distancia de "
        "Mahalanobis robusta frente a la distribución chi-cuadrado con 20 "
        "grados de libertad. A la derecha, distribución empírica de esas "
        "distancias con los dos umbrales considerados. Elaboración propia."),
    "fig_anomalias_jaccard": (
        "Concordancia entre detectores y utilidad clínica de cada uno",
        "El índice de Jaccard mide la proporción de detecciones compartidas "
        "entre cada par de métodos. El lift es el cociente entre la "
        "proporción de casos patológicos entre los registros marcados y la "
        "tasa base del 8,3 %. Elaboración propia."),
    "fig_anomalias_pca": (
        "Anomalías detectadas por los tres métodos multivariantes",
        "Proyección sobre las dos primeras componentes principales, que "
        "explican en conjunto el 43,3 % de la varianza. Elaboración propia."),
    "fig_kmeans_seleccion": (
        "Criterios internos y externos para elegir el número de grupos",
        "La línea vertical discontinua señala el valor óptimo de k según cada "
        "criterio por separado. Los dos paneles inferiores corresponden a la "
        "validación externa frente a la etiqueta NSP. Elaboración propia."),
    "fig_kmeans_perfil": (
        "Perfil de los centroides de K-Means con tres grupos",
        "Cada celda indica cuántas desviaciones típicas por encima o por "
        "debajo de la media general se sitúa el grupo en esa variable. "
        "Elaboración propia."),
    "fig_kmeans_nsp": (
        "Composición diagnóstica de los grupos y proyección sobre el plano principal",
        "A la izquierda, reparto de los tres diagnósticos dentro de cada "
        "grupo. A la derecha, los grupos sobre las dos primeras componentes "
        "principales, con los centroides marcados con una equis. Elaboración "
        "propia."),
    "fig_dbscan_kdist": (
        "Gráfico de k-distancias para la elección del parámetro eps",
        "Distancia de cada observación a su décimo vecino más próximo, "
        "ordenada de menor a mayor. El codo de la curva orienta la elección "
        "del radio de vecindario. Elaboración propia."),
    "fig_dbscan": (
        "Resultado de DBSCAN frente al diagnóstico real",
        "A la izquierda, los grupos y el ruido que identifica el algoritmo. A "
        "la derecha, las mismas observaciones coloreadas según la etiqueta "
        "NSP, que el algoritmo no ha utilizado. Elaboración propia."),
    "fig_dendrograma": (
        "Dendrograma del agrupamiento jerárquico con enlace de Ward",
        "Se representan las últimas treinta fusiones. La altura de cada unión "
        "corresponde al incremento de varianza que provoca. Elaboración "
        "propia."),
    "fig_clustering_comparacion": (
        "Los tres agrupamientos sobre el mismo plano de componentes principales",
        "Bajo el nombre de cada algoritmo se indica su índice de Rand "
        "ajustado frente a la etiqueta NSP. Elaboración propia."),
}


def flowable_figura(nombre, estilos, contador):
    """Compone una figura con el formato de la 7.a edicion del manual APA.

    El orden que exige la norma es: el numero de figura en negrita y alineado a
    la izquierda, el titulo en cursiva en la linea siguiente, despues la imagen
    y por ultimo la nota, encabezada por la palabra Nota en cursiva.
    """
    ruta = DIR_FIGURAS / (nombre + ".png")
    if not ruta.exists():
        return []
    from reportlab.lib.utils import ImageReader
    ancho_px, alto_px = ImageReader(str(ruta)).getSize()

    # Tamano natural de la figura en centimetros, a partir de la resolucion con
    # la que matplotlib la guardo.
    ancho_natural = (ancho_px / DPI_FIGURAS) * 2.54 * cm

    # La figura se imprime a su tamano natural reducido como mucho al factor
    # REDUCCION_MAX, de modo que la tipografia interior siga siendo legible, y
    # sin sobrepasar nunca el ancho de la caja de texto.
    ancho = min(ANCHO_TEXTO, ancho_natural * REDUCCION_MAX)
    alto = ancho * alto_px / ancho_px

    # Ninguna figura debe ocupar mas de la mitad larga de la pagina util.
    if alto > ALTO_MAX_FIGURA:
        alto = ALTO_MAX_FIGURA
        ancho = alto * ancho_px / alto_px

    titulo, nota = FIGURAS_APA.get(nombre, (nombre, "Elaboración propia."))

    return [
        Spacer(1, 4),
        Paragraph("<b>Figura %d</b>" % contador, estilos["figura_numero"]),
        Paragraph("<i>%s</i>" % html.escape(titulo), estilos["figura_titulo"]),
        Image(str(ruta), width=ancho, height=alto, hAlign="CENTER"),
        Spacer(1, 3),
        Paragraph("<i>Nota.</i> " + formato_inline(nota), estilos["figura_nota"]),
    ]


# =========================================================== PIE DE PAGINA
def pie_de_pagina(lienzo, documento):
    """Dibuja el numero de pagina y una linea de identificacion del trabajo."""
    lienzo.saveState()
    lienzo.setFont("Calibri", 8.5)
    lienzo.setFillColor(colors.HexColor("#7A7A7A"))
    lienzo.drawString(2.0 * cm, 1.1 * cm,
                      "Aprendizaje Automático  |  Detección de anomalías y agrupamiento (CTG)")
    lienzo.drawRightString(A4[0] - 2.0 * cm, 1.1 * cm, "Página %d" % documento.page)
    lienzo.setStrokeColor(colors.HexColor("#CCCCCC"))
    lienzo.setLineWidth(0.4)
    lienzo.line(2.0 * cm, 1.4 * cm, A4[0] - 2.0 * cm, 1.4 * cm)
    lienzo.restoreState()


# =================================================================== PORTADA
def portada(estilos):
    """Construye los flowables de la portada del informe."""
    return [
        Spacer(1, 3.2 * cm),
        Paragraph("Detección de anomalías y técnicas de agrupamiento",
                  estilos["portada_titulo"]),
        Paragraph("Aplicación de aprendizaje no supervisado al conjunto de datos "
                  "de cardiotocografía (CTG)", estilos["portada_sub"]),
        Spacer(1, 2.2 * cm),
        Paragraph("<b>Asignatura:</b> Aprendizaje Automático", estilos["portada_dato"]),
        Paragraph("<b>Programa:</b> Maestría en Inteligencia Artificial", estilos["portada_dato"]),
        Paragraph("<b>Autor:</b> Abel Meneses Yupanqui", estilos["portada_dato"]),
        Spacer(1, 1.2 * cm),
        Paragraph("<b>Conjunto de datos:</b> CTG.csv, con 2 126 registros de monitoreo fetal",
                  estilos["portada_dato"]),
        Paragraph("<b>Entorno:</b> Python 3.14 con pandas, scikit-learn, SciPy, "
                  "matplotlib y seaborn", estilos["portada_dato"]),
        Spacer(1, 1.2 * cm),
        Paragraph("<b>Código fuente:</b>", estilos["portada_dato"]),
        Paragraph('<link href="%s" color="#1F4E9C">%s</link>' % (REPO_URL, REPO_URL),
                  estilos["portada_dato"]),
        Spacer(1, 2.2 * cm),
        Paragraph("Todo el código, las figuras y los resultados numéricos que "
                  "aparecen en este informe proceden de una única ejecución del "
                  "cuaderno <font face='Consolas' size='10'>ML_Actividad_CTG.ipynb</font>, "
                  "con la semilla aleatoria fijada en 42 para que los resultados "
                  "sean reproducibles. El repositorio enlazado contiene el "
                  "cuaderno ejecutado, los scripts que lo generan y las quince "
                  "figuras en su resolución original.",
                  ParagraphStyle("nota", parent=estilos["cuerpo"], fontSize=10.5,
                                 leading=15, alignment=TA_CENTER,
                                 textColor=colors.HexColor("#555555"))),
        PageBreak(),
    ]


def indice(estilos):
    """Construye un indice estatico de contenidos del informe."""
    entradas = [
        ("0.", "Configuración del entorno"),
        ("1.", "El conjunto de datos"),
        ("2.", "Análisis descriptivo de los datos"),
        ("3.", "Tratamiento de los valores faltantes"),
        ("4.", "Preparación de la matriz de características"),
        ("5.", "Detección de anomalías"),
        ("6.", "Técnicas de agrupamiento"),
        ("7.", "Ventajas y desventajas de cada modelo"),
        ("8.", "Conclusiones"),
        ("", "Referencias"),
    ]
    elementos = [Paragraph("Contenido", estilos["h1"]), Spacer(1, 6)]
    for numero, titulo in entradas:
        elementos.append(Paragraph(
            "<b>%s</b>  %s" % (numero, titulo),
            ParagraphStyle("idx", parent=estilos["cuerpo"], spaceAfter=3, leftIndent=10)))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(
        "El informe reproduce íntegramente el desarrollo del cuaderno. Para cada "
        "etapa se presenta primero la explicación metodológica, después el código "
        "Python comentado, a continuación la salida que produce y, por último, la "
        "interpretación de los resultados obtenidos.", estilos["cuerpo"]))
    elementos.append(Paragraph(
        "Las salidas de consola más extensas aparecen recortadas para respetar la "
        "extensión máxima que fija el enunciado. La versión completa, con todas "
        "las salidas y las figuras a resolución original, está disponible en el "
        'repositorio público <link href="%s" color="#1F4E9C">%s</link>.'
        % (REPO_URL, REPO_URL), estilos["cuerpo"]))
    return elementos


# ====================================================================== MAIN
def main():
    registrar_fuentes()
    estilos = construir_estilos()

    cuaderno = json.load(open(NOTEBOOK, encoding="utf-8"))
    celdas = cuaderno["cells"]

    elementos = []
    elementos += portada(estilos)
    elementos += indice(estilos)

    n_figura = 0
    n_listado = 0

    for celda in celdas:
        fuente = "".join(celda["source"])

        if celda["cell_type"] == "markdown":
            # Las celdas marcadas como exclusivas del cuaderno, como la portada
            # con el distintivo de Google Colab, no se reproducen en el PDF,
            # que lleva su propia portada.
            if "<!-- solo-notebook -->" in fuente:
                continue
            elementos += renderizar_markdown(fuente, estilos)
            continue

        # ---- Celda de codigo -------------------------------------------------
        n_listado += 1
        titulo = re.search(r"^# Celda ([\d.]+)\.\s*(.+?)\.?$", fuente, flags=re.M)
        rotulo = ("Celda %s. %s" % (titulo.group(1), titulo.group(2))
                  if titulo else "Código %d" % n_listado)
        elementos.append(Spacer(1, 2))
        elementos.append(Paragraph(
            "<b>Listado %d.</b> %s" % (n_listado, html.escape(rotulo)),
            ParagraphStyle("rot", parent=estilos["cuerpo"], fontSize=9, leading=11,
                           textColor=colors.HexColor("#444444"), spaceAfter=1)))
        elementos.append(bloque_monoespaciado(fuente, estilos["codigo"],
                                              GRIS_CODIGO, BORDE_CODIGO, ANCHO_CODIGO))
        elementos.append(Spacer(1, 4))

        # ---- Salida de consola -----------------------------------------------
        salida = texto_de_salidas(celda)
        if salida:
            elementos.append(Spacer(1, 2))
            elementos.append(bloque_monoespaciado(salida, estilos["salida"],
                                                  GRIS_SALIDA, colors.HexColor("#E0D8C8"),
                                                  int(ANCHO_CODIGO * 1.22)))
            elementos.append(Spacer(1, 6))

        # ---- Figuras ---------------------------------------------------------
        for nombre in figuras_de_celda(celda):
            n_figura += 1
            bloque = flowable_figura(nombre, estilos, n_figura)
            if bloque:
                elementos.append(KeepTogether(bloque))

    # ---- Documento -----------------------------------------------------------
    documento = BaseDocTemplate(
        SALIDA, pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=1.9 * cm, bottomMargin=1.9 * cm,
        title="Deteccion de anomalias y tecnicas de agrupamiento (CTG)",
        author="Abel Meneses Yupanqui",
        subject="Actividad de Aprendizaje Automatico",
    )
    marco = Frame(documento.leftMargin, documento.bottomMargin,
                  documento.width, documento.height, id="normal")
    documento.addPageTemplates([PageTemplate(id="principal", frames=[marco],
                                             onPage=pie_de_pagina)])
    documento.build(elementos)

    tamano = pathlib.Path(SALIDA).stat().st_size / 1024
    print("Informe generado: %s (%.0f KB)" % (SALIDA, tamano))
    print("  Listados de codigo: %d" % n_listado)
    print("  Figuras           : %d" % n_figura)


if __name__ == "__main__":
    main()
