# -*- coding: utf-8 -*-
"""Celdas del notebook: portada, configuracion, carga y diccionario de datos."""

from nb_base import md, code


def construir():
    # ================================================================= PORTADA
    # La marca <!-- solo-notebook --> indica que la celda pertenece al cuaderno
    # pero no debe reproducirse en el informe en PDF, que lleva su propia
    # portada.
    md(r"""
<!-- solo-notebook -->
<a href="https://colab.research.google.com/github/amenesesy/actividad-ml-ctg/blob/main/ML_Actividad_CTG.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Abrir en Colab"/></a>

# Deteccion de anomalias y tecnicas de agrupamiento sobre el conjunto de datos CTG

**Asignatura:** Aprendizaje Automático, Maestría en Inteligencia Artificial

**Autor:** Abel Meneses Yaranga

**Repositorio del código:** https://github.com/amenesesy/actividad-ml-ctg

## Resumen

Este cuaderno desarrolla el flujo completo de trabajo de aprendizaje no
supervisado que solicita la actividad, aplicado al conjunto de datos de
cardiotocografía. Se trata de 2 126 registros de monitoreo fetal descritos por
21 variables cuantitativas que un sistema informático extrae de forma automática
de los trazados de frecuencia cardiaca fetal y de actividad uterina.

El trabajo avanza en el orden que exige el enunciado. Las secciones 1 y 2 se
ocupan de la carga de los datos, del diccionario de variables y del análisis
exploratorio, que incluye los estadísticos descriptivos de las variables
numéricas, las frecuencias de las categóricas y la matriz de correlaciones. La
sección 3 diagnostica los valores faltantes, justifica la decisión que se toma
con ellos y la respalda con un experimento controlado de imputación. La sección
4 prepara la matriz de características, es decir, selecciona las variables que
alimentarán a los modelos, depura las redundancias y estandariza las escalas. La
sección 5 aplica cinco técnicas de detección de anomalías y la sección 6, tres
algoritmos de agrupamiento. Las secciones 7 y 8 comparan las ventajas y
desventajas de cada modelo y recogen las conclusiones.

Conviene aclarar desde el principio una decisión metodológica que condiciona la
validez de todo lo que sigue. El conjunto de datos incluye dos variables de
diagnóstico, `CLASS` y `NSP`, que fueron etiquetadas por obstetras. Ninguna de
las dos se utiliza para ajustar ningún modelo, porque todo el análisis es no
supervisado. Se reservan únicamente como verdad de referencia externa, de modo
que al terminar cada etapa se pueda comprobar si las anomalías y los grupos
encontrados tienen algún sentido clínico. Esa separación estricta entre lo que
el algoritmo ve y lo que sirve para juzgarlo es la que permite afirmar que los
resultados no son un artefacto del procedimiento.

Todo el código de este cuaderno, junto con las figuras, los resultados
numéricos y el informe en PDF, está disponible en el repositorio público
https://github.com/amenesesy/actividad-ml-ctg. Pulsando el distintivo que
encabeza esta página el cuaderno se abre directamente en Google Colab y puede
ejecutarse de principio a fin sin instalar nada.
""")

    # =========================================================== 0. ENTORNO
    md(r"""
# 0. Configuración del entorno

El cuaderno está preparado para ejecutarse en dos entornos sin ningún cambio
manual. En una instalación local basta con tener el archivo `CTG.csv` junto al
cuaderno. En Google Colab, al que se accede mediante el distintivo que encabeza
el documento, la primera celda detecta el entorno, comprueba que estén las
librerías necesarias, instala las que falten y descarga el conjunto de datos
desde el repositorio público del trabajo. La ejecución completa tarda alrededor
de dos minutos.

La segunda celda reúne en un solo lugar todas las librerías del ecosistema
científico de Python que se van a utilizar y fija la semilla aleatoria. Esto
último no es un detalle menor: Isolation Forest, K-Means y el experimento de
imputación son algoritmos estocásticos, de manera que sin una semilla fija
producirían cifras distintas en cada ejecución y ninguna de las conclusiones
sería verificable.
""")

    code(r'''
# Celda 0.1. Preparacion del entorno y compatibilidad con Google Colab.
# Objetivo: que el cuaderno se ejecute igual en local que en Colab. Se detecta
#   el entorno, se instalan las librerias que falten y se descarga el conjunto
#   de datos del repositorio publico si no esta presente en el directorio.
# Salidas: la constante EN_COLAB y el archivo CTG.csv disponible en el disco.

import importlib.util
import pathlib
import subprocess
import sys
import urllib.request

# Deteccion del entorno. En Colab existe el paquete google.colab; fuera de
# Colab ni siquiera existe el paquete contenedor google, asi que la deteccion
# se hace con un import protegido y no con find_spec, que ahi fallaria.
try:
    import google.colab  # noqa: F401
    EN_COLAB = True
except ImportError:
    EN_COLAB = False

# Direccion base del repositorio publico del trabajo, desde donde se descargan
# los datos cuando el cuaderno se abre en un entorno recien creado.
REPO = "https://raw.githubusercontent.com/amenesesy/actividad-ml-ctg/main"

# Dependencias del cuaderno, como pares (modulo que se importa, paquete de pip).
DEPENDENCIAS = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("sklearn", "scikit-learn"),
    ("scipy", "scipy"),
]

faltantes = [pip for modulo, pip in DEPENDENCIAS
             if importlib.util.find_spec(modulo) is None]
if faltantes:
    print("Instalando dependencias que faltan:", ", ".join(faltantes))
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *faltantes],
                   check=True)
else:
    print("Todas las dependencias estan disponibles.")

# El conjunto de datos se descarga solo si no esta ya en el directorio actual.
if not pathlib.Path("CTG.csv").exists():
    print("Descargando CTG.csv desde el repositorio del trabajo...")
    urllib.request.urlretrieve(REPO + "/CTG.csv", "CTG.csv")

print("Entorno de ejecucion:", "Google Colab" if EN_COLAB else "instalacion local")
print("Version de Python   :", sys.version.split()[0])
print("Conjunto de datos   :", "CTG.csv disponible"
      if pathlib.Path("CTG.csv").exists() else "NO disponible")
''')

    code(r'''
# Celda 0.2. Importacion de librerias y configuracion global.
# Objetivo: cargar todas las dependencias en un unico lugar, fijar la semilla
#   aleatoria y homogeneizar el estilo de los graficos.
# Salidas: las constantes globales SEMILLA y DIR_FIGURAS, y el diccionario RES
#   en el que cada seccion va depositando sus resultados numericos.

# Utilidades del sistema
import json                      # serializacion de los resultados a disco
import pathlib                   # manejo de rutas independiente del sistema
import warnings                  # control de avisos no criticos

# Manipulacion de datos
import numpy as np               # algebra vectorial y generacion aleatoria
import pandas as pd              # estructuras tabulares (DataFrame)

# Visualizacion
import matplotlib.pyplot as plt  # motor de graficos de bajo nivel
import seaborn as sns            # graficos estadisticos de alto nivel

# Preprocesamiento
from sklearn.preprocessing import StandardScaler      # z = (x - mu) / sigma
from sklearn.impute import SimpleImputer, KNNImputer  # estrategias de imputacion

# Deteccion de anomalias
from sklearn.ensemble import IsolationForest          # aislamiento por particiones
from sklearn.neighbors import LocalOutlierFactor      # densidad local relativa
from sklearn.covariance import MinCovDet              # covarianza robusta (MCD)

# Agrupamiento
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

# Reduccion de dimensionalidad, vecindades y metricas
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import (
    silhouette_score,             # cohesion frente a separacion (validacion interna)
    silhouette_samples,           # silueta calculada por observacion
    davies_bouldin_score,         # razon dispersion/separacion (menor es mejor)
    calinski_harabasz_score,      # razon de varianzas entre/intra (mayor es mejor)
    adjusted_rand_score,          # concordancia con etiquetas (validacion externa)
    normalized_mutual_info_score, # informacion mutua normalizada
)
from scipy import stats           # pruebas estadisticas (Kolmogorov-Smirnov, chi2)

# Configuracion global del cuaderno
SEMILLA = 42                                  # unica fuente de aleatoriedad
np.random.seed(SEMILLA)
warnings.filterwarnings("ignore")             # silencia avisos de version
pd.set_option("display.width", 140)           # ancho de impresion de los DataFrame
pd.set_option("display.max_columns", 50)

# Paleta institucional, tomada de la plantilla Word de la actividad: el cian
# corporativo, los dos grises del texto y del pie, y dos tonos de apoyo para las
# escalas de gravedad clinica.
UNIR_CIAN = "#0098CD"      # color corporativo
UNIR_CIAN_OSC = "#006E96"  # variante oscura, para segundas series
UNIR_CIAN_CLA = "#7FD0EC"  # variante clara
UNIR_GRIS = "#777777"      # gris del pie de pagina
UNIR_GRIS_OSC = "#333333"  # color del texto normal
UNIR_AMBAR = "#E8A33D"     # nivel intermedio en las escalas de gravedad
UNIR_ROJO = "#C1272D"      # nivel alto en las escalas de gravedad

PALETA_UNIR = [UNIR_CIAN, UNIR_ROJO, UNIR_GRIS, UNIR_CIAN_OSC, UNIR_AMBAR,
               UNIR_GRIS_OSC, UNIR_CIAN_CLA]

# Mapas de color derivados de la misma paleta. El divergente se usa en las
# matrices de correlacion y de centroides; el secuencial, en la matriz de
# concordancia entre detectores.
from matplotlib.colors import LinearSegmentedColormap
CMAP_DIV = LinearSegmentedColormap.from_list(
    "unir_div", [UNIR_CIAN_OSC, UNIR_CIAN, "#FFFFFF", "#E38B8E", UNIR_ROJO])
CMAP_SEQ = LinearSegmentedColormap.from_list(
    "unir_seq", ["#FFFFFF", UNIR_CIAN_CLA, UNIR_CIAN, UNIR_CIAN_OSC])

sns.set_theme(style="whitegrid", palette=PALETA_UNIR)   # estilo institucional
plt.rcParams["text.color"] = UNIR_GRIS_OSC
plt.rcParams["axes.labelcolor"] = UNIR_GRIS_OSC
plt.rcParams["axes.titlecolor"] = UNIR_GRIS_OSC
plt.rcParams["xtick.color"] = UNIR_GRIS_OSC
plt.rcParams["ytick.color"] = UNIR_GRIS_OSC
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 200      # resolucion suficiente para imprimir
plt.rcParams["savefig.bbox"] = "tight"
# Tipografia holgada dentro de las figuras. Las figuras se disenan compactas y
# con letra grande para que sigan siendo legibles cuando el informe en PDF las
# reduce al ancho de la caja de texto.
plt.rcParams["font.size"] = 11
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["legend.fontsize"] = 10

DIR_FIGURAS = pathlib.Path("figuras")         # carpeta destino de las figuras
DIR_FIGURAS.mkdir(exist_ok=True)

# Diccionario acumulador. Cada seccion deposita aqui sus resultados numericos
# para que el informe en PDF se construya despues a partir de datos reales y no
# de cifras transcritas a mano.
RES = {}


def guardar(nombre):
    """Guarda la figura activa de matplotlib en figuras/<nombre>.png y la muestra.

    Parametros
    ----------
    nombre : str
        Nombre del archivo destino, sin extension ni ruta.
    """
    plt.savefig(DIR_FIGURAS / (nombre + ".png"))
    plt.show()


print("Librerias cargadas correctamente. Semilla aleatoria fijada en", SEMILLA)
''')

    # ========================================================== 1. LOS DATOS
    md(r"""
# 1. El conjunto de datos

## 1.1 Contexto del problema

La cardiotocografía es la prueba de vigilancia fetal más extendida del mundo.
Registra de manera simultánea la frecuencia cardiaca del feto y la actividad
contráctil del útero durante el embarazo tardío y el trabajo de parto. Su
interpretación visual tiene, sin embargo, una concordancia entre observadores
notoriamente baja, y por ese motivo desde los años noventa se desarrollaron
sistemas de análisis automático capaces de resumir cada trazado en un vector de
descriptores numéricos.

El archivo `CTG.csv` es precisamente el resultado de aplicar el sistema SisPorto
2.0 (Ayres-de-Campos et al., 2000) a 2 126 trazados. Cada fila corresponde a un
segmento de registro y cada columna a un descriptor calculado de forma
automática. Además, tres obstetras etiquetaron cada segmento con dos variables
de diagnóstico: `CLASS`, que recoge el patrón morfológico de la frecuencia
cardiaca fetal en diez categorías, y `NSP`, que resume el estado del feto en
tres niveles, normal, sospechoso y patológico.

## 1.2 Por qué este conjunto se ajusta a la actividad

El problema encaja de forma natural con las dos técnicas que pide el enunciado.
En cuanto a la detección de anomalías, los casos patológicos son por definición
minoritarios, apenas el 8,3 % del total, de modo que un buen detector de valores
atípicos debería enriquecerse en ellos sin haberlos visto nunca. Eso permite
medir de forma objetiva si el detector resulta útil y no solo si es
matemáticamente correcto. En cuanto al agrupamiento, si la frecuencia cardiaca
fetal presenta realmente patrones morfológicos diferenciados, un algoritmo de
clustering debería recuperarlos al menos en parte. El contraste posterior con
`NSP` cuantifica cuánta de esa estructura es real y cuánta es un artefacto del
algoritmo.
""")

    code(r'''
# Celda 1.1. Carga del conjunto de datos.
# Se usa la copia local que dejo preparada la celda 0.1 y, si por lo que fuera
# no estuviera, se recurre al archivo original publicado por el curso.
# Salidas: df_bruto, con los datos tal y como vienen del archivo.

RUTA_LOCAL = pathlib.Path("CTG.csv")
URL_CURSO = ("https://raw.githubusercontent.com/OscarJimenezFlores/ML/"
             "refs/heads/main/Data/CTG.csv")

origen = RUTA_LOCAL if RUTA_LOCAL.exists() else URL_CURSO
df_bruto = pd.read_csv(origen)

print("Origen de los datos          :", origen)
print("Dimensiones (filas, columnas):", df_bruto.shape)
print("\nPrimeras 3 filas:")
df_bruto.head(3)
''')

    md(r"""
Antes de calcular ningún estadístico conviene documentar qué significa cada
columna y, sobre todo, qué papel juega. Sin ese paso el análisis exploratorio se
convierte en estadística ciega, porque no hay forma de decidir qué variables son
informativas, cuáles son simples identificadores del registro, cuáles duplican
información que ya está en otra parte y cuáles son etiquetas que deben quedar
apartadas del modelado.
""")

    code(r'''
# Celda 1.2. Diccionario de variables.
# Documenta el significado y el rol de cada una de las 40 columnas del archivo.
# Salidas: el diccionario DICCIONARIO y la tabla legible tabla_dic.

DICCIONARIO = {
    # Identificadores del registro, sin valor descriptivo
    "FileName": ("Identificador", "Nombre del archivo del trazado original"),
    "Date":     ("Identificador", "Fecha del registro"),
    "SegFile":  ("Identificador", "Nombre del segmento analizado"),
    "b":        ("Identificador", "Indice de inicio del segmento en el trazado"),
    "e":        ("Identificador", "Indice de fin del segmento en el trazado"),
    # Descriptores de la frecuencia cardiaca fetal
    "LBE":      ("Redundante",    "Linea de base de la FCF segun el experto medico"),
    "LB":       ("Numerica",      "Linea de base de la FCF calculada por SisPorto (lpm)"),
    "AC":       ("Numerica",      "Numero de aceleraciones"),
    "FM":       ("Numerica",      "Numero de movimientos fetales"),
    "UC":       ("Numerica",      "Numero de contracciones uterinas"),
    "ASTV":     ("Numerica",      "% de tiempo con variabilidad anormal a corto plazo"),
    "MSTV":     ("Numerica",      "Valor medio de la variabilidad a corto plazo"),
    "ALTV":     ("Numerica",      "% de tiempo con variabilidad anormal a largo plazo"),
    "MLTV":     ("Numerica",      "Valor medio de la variabilidad a largo plazo"),
    "DL":       ("Numerica",      "Numero de deceleraciones ligeras"),
    "DS":       ("Numerica",      "Numero de deceleraciones severas"),
    "DP":       ("Numerica",      "Numero de deceleraciones prolongadas"),
    "DR":       ("Constante",     "Numero de deceleraciones repetitivas (siempre 0)"),
    # Descriptores del histograma de la frecuencia cardiaca fetal
    "Width":    ("Numerica",      "Amplitud del histograma de la FCF"),
    "Min":      ("Numerica",      "Valor minimo del histograma"),
    "Max":      ("Numerica",      "Valor maximo del histograma"),
    "Nmax":     ("Numerica",      "Numero de picos del histograma"),
    "Nzeros":   ("Numerica",      "Numero de ceros del histograma"),
    "Mode":     ("Numerica",      "Moda del histograma"),
    "Mean":     ("Numerica",      "Media del histograma"),
    "Median":   ("Numerica",      "Mediana del histograma"),
    "Variance": ("Numerica",      "Varianza del histograma"),
    "Tendency": ("Ordinal",       "Tendencia del histograma (-1 izq., 0 simetrica, 1 der.)"),
    # Codificacion disyuntiva (one-hot) de la etiqueta CLASS
    **{c: ("One-hot de CLASS", "Indicador binario del patron morfologico " + c)
       for c in ["A", "B", "C", "D", "E", "AD", "DE", "LD", "FS", "SUSP"]},
    # Etiquetas de diagnostico, reservadas como verdad de referencia
    "CLASS":    ("Etiqueta", "Patron morfologico de la FCF (10 categorias)"),
    "NSP":      ("Etiqueta", "Estado fetal: 1=Normal, 2=Sospechoso, 3=Patologico"),
}

tabla_dic = pd.DataFrame(
    [(v, r, d) for v, (r, d) in DICCIONARIO.items()],
    columns=["Variable", "Rol", "Descripcion"],
)

print("Columnas documentadas:", len(tabla_dic), "| reparto por rol:")
for rol, n in tabla_dic["Rol"].value_counts().items():
    ejemplos = ", ".join(tabla_dic.loc[tabla_dic["Rol"] == rol, "Variable"].head(4))
    print("  %-18s %2d   (%s%s)" % (rol, n, ejemplos, ", ..." if n > 4 else ""))

RES["n_columnas"] = int(df_bruto.shape[1])
''')

    md(r"""
El reparto por rol deja ver que el archivo contiene bastante menos información
de la que sugieren sus 40 columnas. Cinco de ellas identifican el registro, una
duplica a otra, otra es constante, diez son una recodificación de la etiqueta
`CLASS` y dos son las propias etiquetas. Solo veintiuna describen realmente el
trazado, y en la sección 4 se comprobará que incluso entre esas hay una
redundancia exacta.
""")
