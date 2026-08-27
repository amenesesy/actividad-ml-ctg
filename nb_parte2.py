# -*- coding: utf-8 -*-
"""Celdas del notebook: analisis exploratorio (seccion 2) y valores faltantes (seccion 3)."""

from nb_base import md, code


def construir():
    # ================================================================ 2. EDA
    md(r"""
# 2. Análisis descriptivo de los datos

El análisis exploratorio persigue tres objetivos concretos antes de aplicar
ningún algoritmo. El primero es conocer la escala y la forma de cada variable,
porque tanto la detección de anomalías como el agrupamiento se basan en
distancias y son, por tanto, muy sensibles a las unidades de medida y a la
asimetría. El segundo es detectar los problemas de calidad, es decir, filas
espurias, columnas constantes, duplicados y redundancias que contaminarían los
modelos si pasaran inadvertidos. El tercero es cuantificar la redundancia entre
variables mediante la matriz de correlaciones, dato que resultará decisivo para
saber si conviene reducir la dimensionalidad.

## 2.1 Estructura del conjunto
""")

    code(r'''
# Celda 2.1. Estructura general del conjunto de datos.
# Objetivo: inspeccionar dimensiones, tipos de dato, memoria y duplicados. Es el
#   primer control de calidad, y cualquier anomalia estructural debe detectarse
#   aqui y no cuando ya estan fallando los modelos.

print("=" * 78)
print("ESTRUCTURA DEL CONJUNTO DE DATOS")
print("=" * 78)
print("Numero de filas    :", df_bruto.shape[0])
print("Numero de columnas :", df_bruto.shape[1])
print("Memoria ocupada    : %.1f KB" % (df_bruto.memory_usage(deep=True).sum() / 1024))

# Reparto de tipos de dato: distingue las columnas de texto de las numericas.
print("\nTipos de dato presentes:")
print(df_bruto.dtypes.value_counts().to_string())

# Filas completamente duplicadas: en un conjunto de senales clinicas serian
# sospechosas de un error de exportacion.
print("\nFilas exactamente duplicadas:", int(df_bruto.duplicated().sum()))

# Ultimas filas del archivo: es donde suelen aparecer los artefactos de las
# hojas de calculo originales, como filas de totales o separadores en blanco.
print("\nUltimas 4 filas del archivo (primeras 12 columnas):")
print(df_bruto.iloc[-4:, :12].to_string())
''')

    md(r"""
La inspección de las últimas filas revela el primer hallazgo importante del
trabajo, y es que el archivo no termina en un registro clínico. Las tres últimas
líneas son residuos de la hoja de cálculo original `CTG.xls`: una fila
completamente vacía, una fila con ceros de relleno y una fila de totales que
agrega columnas como `FM`, `UC` o `ASTV`. No son pacientes, sino artefactos de
exportación. El detalle condiciona por completo la sección 3, porque son
exactamente esas tres filas las que generan todos los valores faltantes del
conjunto.

## 2.2 Estadísticos descriptivos de las variables numéricas
""")

    code(r'''
# Celda 2.2. Estadisticos descriptivos de las variables numericas.
# Objetivo: obtener tendencia central, dispersion y forma de cada variable. A
#   los descriptivos clasicos se anaden la asimetria y la curtosis, que son las
#   medidas que anticipan como se comportaran los detectores de anomalias
#   basados en la hipotesis de normalidad.
# Salidas: el DataFrame desc, con una fila por variable.

# Se excluyen las columnas de texto; el resto son numericas.
num_bruto = df_bruto.select_dtypes(include=[np.number])

# describe() entrega conteo, media, desviacion, minimo, cuartiles y maximo.
desc = num_bruto.describe().T

# Asimetria: 0 indica simetria; un valor absoluto mayor que 1 indica cola marcada.
desc["asimetria"] = num_bruto.skew()
# Curtosis de Fisher: 0 es la normal; por encima de 3 hay colas muy pesadas.
desc["curtosis"] = num_bruto.kurtosis()
# Coeficiente de variacion: dispersion relativa, comparable entre variables.
desc["cv"] = desc["std"] / desc["mean"].replace(0, np.nan)

desc = desc.round(2)

print("Estadisticos descriptivos de las", desc.shape[0], "variables numericas:\n")
print(desc[["count", "mean", "std", "min", "50%", "max", "asimetria", "curtosis"]].to_string())

# Se guardan las variables mas asimetricas, que son las que mas condicionan la
# eleccion del metodo de deteccion de anomalias.
RES["top_asimetria"] = desc["asimetria"].abs().sort_values(ascending=False).head(6).round(2).to_dict()
desc
''')

    md(r"""
La tabla admite tres lecturas relevantes. La primera es que la columna `count`
no es constante: la mayoría de variables tiene 2 126 observaciones válidas, pero
unas pocas tienen 2 127 o 2 128, y esa irregularidad es la huella de las filas
de artefacto detectadas en el apartado anterior.

La segunda es que las escalas son radicalmente distintas. La línea de base `LB`
se mueve en torno a 133 latidos por minuto, `MSTV` en torno a 1,3 y `Variance`
alcanza valores de 269. Cualquier algoritmo basado en la distancia euclídea
quedaría dominado por las variables de rango grande, de modo que la
estandarización no es opcional sino imprescindible, cuestión que se retoma en la
sección 4.

La tercera lectura tiene que ver con la forma de las distribuciones. Variables
como `DS`, `DP`, `Variance` o `Nzeros` presentan asimetrías muy superiores a 1 y
curtosis elevadas, porque son conteos de eventos raros con una enorme
acumulación de ceros. Esto anticipa que los métodos de detección de anomalías
que asumen normalidad, como el Z-score o la distancia de Mahalanobis, marcarán
muchos falsos positivos, y favorece de entrada a los métodos no paramétricos.

## 2.3 Variables categóricas y frecuencias
""")

    code(r'''
# Celda 2.3. Variables categoricas: categorias y frecuencias.
# Objetivo: listar las categorias de cada variable cualitativa y su frecuencia.
#   Se distinguen dos grupos, porque pandas solo reconoce el primero: las
#   categoricas almacenadas como texto (FileName, Date, SegFile) y las
#   codificadas como numeros (CLASS, NSP, Tendency y las diez indicadoras).
#   Tratar estas ultimas como continuas seria un error conceptual, porque la
#   media de NSP no significa nada.

# Categoricas almacenadas como texto
cat_texto = df_bruto.select_dtypes(include=["object"]).columns.tolist()
print("Variables categoricas de tipo texto:", cat_texto, "\n")

for col in cat_texto:
    n_cat = df_bruto[col].nunique()
    print("  " + col + ": " + str(n_cat) + " categorias distintas "
          + "(cardinalidad " + str(round(100 * n_cat / len(df_bruto), 1)) + "% de las filas)")
    print("    5 mas frecuentes: " + str(df_bruto[col].value_counts().head(5).to_dict()))

print("\n" + "-" * 78)
print("La cardinalidad casi maxima confirma que las tres son IDENTIFICADORES")
print("del registro y no variables analizables.")
print("-" * 78 + "\n")

# Categoricas codificadas como numeros
cat_numericas = ["Tendency", "CLASS", "NSP"]
ETIQUETAS_NSP = {1: "Normal", 2: "Sospechoso", 3: "Patologico"}
ETIQUETAS_TEND = {-1: "Desplazado a la izquierda", 0: "Simetrico", 1: "Desplazado a la derecha"}

for col in cat_numericas:
    frec = df_bruto[col].value_counts(dropna=False).sort_index()
    prop = (100 * frec / frec.sum()).round(2)
    tabla = pd.DataFrame({"frecuencia": frec, "porcentaje": prop})
    if col == "NSP":
        tabla.insert(0, "significado", [ETIQUETAS_NSP.get(i, "artefacto") for i in tabla.index])
    if col == "Tendency":
        tabla.insert(0, "significado", [ETIQUETAS_TEND.get(i, "artefacto") for i in tabla.index])
    print("Frecuencias de '" + col + "':")
    print(tabla.to_string(), "\n")

# Coherencia de la codificacion one-hot de CLASS
COLS_ONEHOT = ["A", "B", "C", "D", "E", "AD", "DE", "LD", "FS", "SUSP"]
suma_onehot = df_bruto[COLS_ONEHOT].sum(axis=1)
print("Suma por fila de las 10 indicadoras one-hot:",
      suma_onehot.value_counts(dropna=False).to_dict())
print("Al ser constante e igual a 1, se trata de una recodificacion EXACTA de")
print("CLASS: no aportan informacion nueva e introducen una dependencia lineal")
print("perfecta que rompe los metodos basados en la matriz de covarianzas.")

RES["frec_nsp"] = df_bruto["NSP"].value_counts(dropna=False).sort_index().to_dict()
''')

    md(r"""
El análisis de las categóricas produce cuatro decisiones de modelado. Las
variables `FileName`, `Date` y `SegFile` tienen una cardinalidad casi igual al
número de filas, lo que las identifica como identificadores del registro; no
describen al feto y por tanto se descartan. La variable `NSP` está muy
desbalanceada, con un 77,8 % de casos normales, un 13,9 % de sospechosos y un
8,3 % de patológicos, y ese desbalance es justamente lo que convierte al
conjunto en un buen banco de pruebas para la detección de anomalías. La variable
`CLASS` reparte los datos en diez categorías con frecuencias muy dispares, entre
53 y 579 casos. Por último, las diez indicadoras que van de `A` a `SUSP` suman
exactamente 1 en todas las filas, lo que demuestra que son una codificación
disyuntiva de `CLASS`. Mantenerlas junto a `CLASS` supondría duplicar
información y, lo que es peor, haría singular la matriz de covarianzas e
impediría calcular la distancia de Mahalanobis, así que también se eliminan.

## 2.4 Matriz de correlaciones
""")

    code(r'''
# Celda 2.4. Matriz de correlaciones entre las variables numericas.
# Objetivo: cuantificar la redundancia lineal entre descriptores. La matriz se
#   calcula solo sobre las 21 variables descriptivas reales, porque incluir los
#   identificadores, las one-hot o las etiquetas produciria correlaciones
#   espurias y una figura ilegible.
# Salidas: la figura fig_correlaciones y la lista de pares muy correlacionados.

# Variables descriptivas: se excluyen identificadores (FileName, Date, SegFile,
# b, e), la redundante LBE, la constante DR, las one-hot y las etiquetas.
VARIABLES = ["LB", "AC", "FM", "UC", "ASTV", "MSTV", "ALTV", "MLTV",
             "DL", "DS", "DP", "Width", "Min", "Max", "Nmax", "Nzeros",
             "Mode", "Mean", "Median", "Variance", "Tendency"]

# Se usan solo las filas validas; las 3 de artefacto se depuran en la seccion 3.
corr = df_bruto[VARIABLES].dropna().corr(method="pearson")

plt.figure(figsize=(9.5, 7.6))
mascara = np.triu(np.ones_like(corr, dtype=bool))   # oculta el triangulo superior
# Se representa el color sin anotar cada coeficiente: con 21 variables son
# 210 numeros que resultarian ilegibles al reducir la figura al ancho de la
# pagina. Los pares fuertes se listan a continuacion en forma de tabla.
sns.heatmap(corr, mask=mascara, annot=False, cmap=CMAP_DIV,
            center=0, vmin=-1, vmax=1, linewidths=0.3,
            cbar_kws={"shrink": 0.8, "label": "r de Pearson"})
plt.title("Matriz de correlaciones de las 21 variables descriptivas")
plt.tight_layout()
guardar("fig_correlaciones")

# Extraccion de los pares fuertemente correlacionados. Se recorre solo el
# triangulo inferior para no repetir cada par dos veces.
pares = []
for i in range(len(VARIABLES)):
    for j in range(i + 1, len(VARIABLES)):
        r = corr.iloc[i, j]
        if abs(r) >= 0.70:
            pares.append((VARIABLES[i], VARIABLES[j], round(float(r), 3)))
pares = sorted(pares, key=lambda t: -abs(t[2]))

print("Pares de variables con |r| >= 0.70:\n")
for a, b, r in pares:
    print("  %-9s y %-9s  r = %+.3f" % (a, b, r))

RES["pares_correlacionados"] = pares
RES["corr_media_abs"] = float(np.abs(corr.values[np.triu_indices_from(corr, k=1)]).mean().round(3))
print("\nCorrelacion absoluta media entre pares: %.3f" % RES["corr_media_abs"])
''')

    md(r"""
La matriz revela una estructura de redundancia muy clara y, además,
clínicamente interpretable. Existe un primer bloque formado por `Mean`,
`Median`, `Mode` y `LB`, con correlaciones que van de 0,71 a 0,95, siendo el par
`Mean` y `Median` el más redundante de todo el conjunto. Las cuatro variables
miden lo mismo, esto es, dónde se sitúa la frecuencia cardiaca fetal, y solo se
diferencian en el estimador que emplean.

Un segundo bloque agrupa a los descriptores de dispersión del histograma. La
amplitud `Width` correlaciona a −0,90 con `Min`, a 0,75 con `Nmax` y a 0,69 con
`Max`. La relación resulta ser, de hecho, exacta, puesto que `Width` es igual a
`Max` menos `Min`, como se comprobará en la sección 4; la correlación lineal por
pares no llega a revelarla porque la dependencia involucra a tres variables a la
vez.

También aparecen correlaciones negativas informativas. La variable `ASTV`
correlaciona a −0,43 con `MSTV`, y `Variance` a −0,55 con `Min`, lo que expresa
que cuanto mayor es el porcentaje de tiempo con variabilidad anormal, menor es
la variabilidad media efectiva del trazado. En conjunto, la redundancia es
moderada, con una correlación absoluta media de 0,234, y está concentrada en
esos dos bloques. La consecuencia práctica es que una parte apreciable de la
varianza total se concentra en pocas direcciones, lo que justifica recurrir al
análisis de componentes principales tanto para visualizar como para mitigar la
maldición de la dimensionalidad que sufre DBSCAN.

## 2.5 Distribuciones de las variables clave
""")

    code(r'''
# Celda 2.5. Distribucion de las variables mas relevantes.
# Objetivo: visualizar la forma de la distribucion de un subconjunto
#   representativo de variables, para confirmar graficamente la asimetria que
#   ya se detecto numericamente en la celda 2.2.
# Salidas: las figuras fig_distribuciones y fig_boxplots.

VARS_CLAVE = ["LB", "ASTV", "MSTV", "ALTV", "MLTV", "AC",
              "UC", "DL", "Width", "Variance", "Mean", "Nmax"]

datos_validos = df_bruto[VARIABLES].dropna()

# Histogramas con estimacion de densidad
fig, ejes = plt.subplots(3, 4, figsize=(11, 6.6))
for eje, col in zip(ejes.flatten(), VARS_CLAVE):
    sns.histplot(datos_validos[col], bins=30, kde=True, ax=eje, color=UNIR_CIAN)
    eje.set_title(col + "  (asimetria = %.2f)" % datos_validos[col].skew(), fontsize=10)
    eje.set_xlabel("")
    eje.set_ylabel("")
fig.suptitle("Distribucion de las variables mas relevantes", fontsize=13)
plt.tight_layout()
guardar("fig_distribuciones")

# Diagramas de caja sobre datos estandarizados. Se estandariza solo para poder
# dibujar todas las variables en un mismo eje; el objetivo es comparar la
# CANTIDAD de puntos que quedan fuera de los bigotes.
datos_z = (datos_validos - datos_validos.mean()) / datos_validos.std()

plt.figure(figsize=(10.5, 4.2))
sns.boxplot(data=datos_z, orient="v", fliersize=1.5, color=UNIR_CIAN_CLA)
plt.xticks(rotation=90)
plt.axhline(0, color=UNIR_GRIS, lw=0.8)
plt.ylabel("Valor estandarizado (z)")
plt.title("Diagramas de caja de las 21 variables estandarizadas")
plt.tight_layout()
guardar("fig_boxplots")

# Cuantificacion del numero de atipicos univariantes por variable segun la
# regla clasica de Tukey: fuera de [Q1 - 1.5*RIC, Q3 + 1.5*RIC].
q1 = datos_validos.quantile(0.25)
q3 = datos_validos.quantile(0.75)
ric = q3 - q1
atipicos_por_var = ((datos_validos < (q1 - 1.5 * ric)) | (datos_validos > (q3 + 1.5 * ric))).sum()
atipicos_por_var = atipicos_por_var.sort_values(ascending=False)

print("Numero de valores atipicos univariantes (criterio de Tukey) por variable:\n")
print(atipicos_por_var.to_string())
RES["atipicos_univariantes"] = atipicos_por_var.head(8).to_dict()
''')

    md(r"""
Los histogramas confirman lo que ya anticipaban la asimetría y la curtosis. Solo
`LB`, `Mean`, `Mode` y `Median` son aproximadamente simétricas; el resto son
distribuciones fuertemente sesgadas a la derecha, con una masa enorme de ceros
en los conteos de eventos como `DS`, `DP` o `Nzeros`.

Los diagramas de caja muestran que prácticamente todas las variables tienen
puntos fuera de los bigotes, lo que constituye una advertencia metodológica de
primer orden. Si se aplicara una regla univariante y se eliminara toda fila con
algún valor atípico, se perdería una fracción enorme del conjunto y, además,
serían precisamente los casos clínicamente más interesantes los que
desaparecerían. La detección de anomalías tiene que ser multivariante.

# 3. Tratamiento de los valores faltantes

## 3.1 Diagnóstico
""")

    code(r'''
# Celda 3.1. Diagnostico de los valores faltantes.
# Objetivo: cuantificar los faltantes y, sobre todo, describir su PATRON. La
#   decision de imputar o eliminar depende del patron y no del recuento:
#   faltantes dispersos y faltantes concentrados en filas completas son
#   problemas distintos que admiten soluciones opuestas.
# Salidas: la serie faltantes y los indices filas_con_na.

faltantes = df_bruto.isnull().sum()
faltantes_pos = faltantes[faltantes > 0].sort_values(ascending=False)

print("=" * 78)
print("DIAGNOSTICO DE VALORES FALTANTES")
print("=" * 78)
print("Celdas faltantes en total :", int(faltantes.sum()))
print("Columnas afectadas        :", int((faltantes > 0).sum()), "de", df_bruto.shape[1])
print("Porcentaje sobre el total : %.3f %%"
      % (100 * faltantes.sum() / (df_bruto.shape[0] * df_bruto.shape[1])))

print("\nFaltantes por columna (solo las afectadas):")
print(faltantes_pos.to_string())

# Analisis del patron: se cuenta cuantos faltantes tiene CADA FILA.
na_por_fila = df_bruto.isnull().sum(axis=1)
filas_con_na = df_bruto.index[na_por_fila > 0]

print("\nFilas con al menos un valor faltante:", len(filas_con_na))
print("Indices de esas filas:", list(filas_con_na))
print("\nNumero de valores faltantes en cada una de ellas (sobre 40 columnas):")
print(na_por_fila[filas_con_na].to_string())

print("\nContenido de las filas sospechosas (columnas 8 a 20):")
print(df_bruto.loc[filas_con_na].iloc[:, 8:20].to_string())

RES["faltantes_total"] = int(faltantes.sum())
RES["filas_con_na"] = [int(i) for i in filas_con_na]
''')

    md(r"""
El diagnóstico es concluyente y desmonta la lectura ingenua del problema. Hay
106 celdas faltantes repartidas en 39 columnas, pero todas ellas se concentran
en solo 3 filas, las de índice 2126, 2127 y 2128, que son las tres últimas del
archivo. Esas tres filas no son pacientes con datos incompletos: son artefactos
de exportación de la hoja de cálculo original. La primera está completamente
vacía, la segunda contiene ceros de relleno en `DL`, `DS`, `DP` y `DR`, y la
tercera es una fila de totales con valores como `FM` igual a 564 o `MLTV` igual
a 50,7, que están varios órdenes de magnitud fuera del rango clínico de
cualquiera de esas variables. Ninguna de las tres tiene valor en `NSP` ni en
`CLASS`, es decir, ningún obstetra las diagnosticó, sencillamente porque no
existen como observaciones.

## 3.2 Decisión: eliminar frente a imputar

En términos de la tipología de Rubin (1976), este no es un caso de datos
faltantes completamente al azar, ni al azar, ni no al azar. No hay ningún dato
que falte; lo que hay son filas que no son observaciones. La discusión sobre si
conviene la media, la mediana o la moda solo es pertinente cuando la fila
representa a un individuo real del que se desconoce alguna medida, y no es este
el caso.

La decisión adoptada es, por tanto, eliminar las tres filas. La justifican
varios argumentos convergentes. El primero atañe a la naturaleza del dato:
eliminar es correcto porque no se está descartando información clínica, mientras
que imputar fabricaría tres pacientes ficticios. El segundo es el coste, que
resulta despreciable, ya que se pierden 3 filas de 2 129, apenas el 0,14 % del
conjunto. El tercero, y el más importante para este trabajo, es el efecto sobre
los modelos: la fila de totales, de conservarse imputada, se convertiría en el
valor atípico más extremo de todo el conjunto y capturaría buena parte de la
capacidad de detección, además de desplazar los centroides de K-Means, que no
son robustos frente a valores extremos. A ello se añade un argumento de
trazabilidad, porque la imputación enmascararía un error de origen que conviene
dejar documentado.

Imputar con la media sería, por añadidura, internamente incoherente, ya que se
estaría usando la media de una columna que la propia fila de totales ha
contaminado para completar esa misma fila.

De todo ello se deriva una regla general que vale la pena retener: antes de
elegir una estrategia de imputación hay que preguntarse si la fila representa a
una entidad real, y solo cuando la respuesta es afirmativa tiene sentido
comparar la media, la mediana, la moda o el vecino más cercano.
""")

    code(r'''
# Celda 3.2. Aplicacion de la decision: depuracion del conjunto.
# Objetivo: eliminar las filas de artefacto y verificar que el conjunto
#   resultante queda completo y es coherente.
# Salidas: df, el DataFrame depurado que se usa en el resto del trabajo.

n_antes = len(df_bruto)

# Criterio de eliminacion: una fila sin diagnostico NSP no es una observacion
# clinica. Es un criterio semantico, basado en el significado de la variable, y
# resulta mas seguro que un dropna() global, que dependeria del azar de cada
# columna.
df = df_bruto.dropna(subset=["NSP"]).reset_index(drop=True)

print("Filas antes de la depuracion  :", n_antes)
print("Filas despues de la depuracion:", len(df))
print("Filas eliminadas              :", n_antes - len(df),
      "(%.2f %% del conjunto)" % (100 * (n_antes - len(df)) / n_antes))

# El conjunto debe quedar sin ningun faltante.
faltantes_despues = df.isnull().sum().sum()
print("\nValores faltantes tras la depuracion:", int(faltantes_despues))
assert faltantes_despues == 0, "Quedan faltantes: revisar el criterio de depuracion"
print("Verificacion superada: el conjunto esta completo.")

# Verificacion de coherencia de los rangos clinicos.
print("\nRangos de tres variables de control tras la depuracion:")
for col in ["LB", "FM", "MLTV"]:
    print("  %-6s min = %7.1f   max = %7.1f" % (col, df[col].min(), df[col].max()))
print("\nLos maximos vuelven a rangos fisiologicos, lo que confirma que la fila")
print("de totales, que aportaba FM = 564 y MLTV = 50.7, ha desaparecido.")

RES["n_filas_final"] = int(len(df))
RES["n_filas_eliminadas"] = int(n_antes - len(df))
''')

    md(r"""
## 3.3 Experimento de validación

La decisión anterior se apoya en el significado de los datos. Para respaldarla
también de forma cuantitativa, y para responder de manera completa a la pregunta
que plantea el enunciado sobre la media, la mediana y la moda, se diseña un
experimento controlado en cuatro pasos. Se parte del conjunto ya depurado, que
está completo; se borra artificialmente el 10 % de los valores numéricos de
forma completamente aleatoria, lo que reproduce un mecanismo de pérdida
completamente al azar; se reconstruye la matriz con cuatro estrategias distintas,
media, mediana, moda y vecinos más cercanos con k igual a 5; y por último se
mide el error frente al valor verdadero, que en este montaje sí se conoce. Este
diseño permite comparar estrategias contra una verdad de referencia, algo
imposible cuando los faltantes son reales.
""")

    code(r'''
# Celda 3.3. Experimento controlado de imputacion.
# Objetivo: comparar media, mediana, moda y KNN sobre faltantes SIMULADOS, donde
#   el valor verdadero se conoce y el error puede medirse.
# Metricas: RMSE normalizado, que mide el error de reconstruccion y conviene que
#   sea bajo, y el ratio de desviaciones tipicas, que mide la conservacion de la
#   dispersion y cuyo valor ideal es 1.
# Salidas: el DataFrame comparacion_imp y la figura fig_imputacion.

# Paso 1: matriz completa de referencia
X_completa = df[VARIABLES].copy()

# Paso 2: borrado aleatorio del 10 % de las celdas
generador = np.random.default_rng(SEMILLA)
mascara_na = generador.random(X_completa.shape) < 0.10
X_perforada = X_completa.mask(mascara_na)

print("Celdas borradas artificialmente:", int(mascara_na.sum()),
      "(%.1f %% de la matriz)" % (100 * mascara_na.mean()))

# Paso 3: reconstruccion con cuatro estrategias
ESTRATEGIAS = {
    "Media":    SimpleImputer(strategy="mean"),
    "Mediana":  SimpleImputer(strategy="median"),
    "Moda":     SimpleImputer(strategy="most_frequent"),
    "KNN (k=5)": KNNImputer(n_neighbors=5),
}

# Escala de referencia para normalizar el error: la desviacion tipica real de
# cada variable. Sin ella el RMSE quedaria dominado por Variance y Width.
sigma = X_completa.std().replace(0, np.nan)

filas_resultado = []
imputaciones = {}

for nombre, imputador in ESTRATEGIAS.items():
    # fit_transform aprende el estadistico de cada columna y rellena los huecos.
    X_rec = pd.DataFrame(imputador.fit_transform(X_perforada),
                         columns=VARIABLES, index=X_completa.index)
    imputaciones[nombre] = X_rec

    # El error se mide solo en las celdas borradas; las demas son exactas.
    error = (X_rec - X_completa)[mascara_na]
    rmse_norm = float(np.sqrt(((error / sigma) ** 2).stack().mean()))

    # Conservacion de la dispersion: toda imputacion por una constante central
    # reduce artificialmente la varianza de la variable.
    ratio_sd = float((X_rec.std() / X_completa.std()).mean())

    # Conservacion de la estructura de correlaciones, importante para el PCA.
    corr_real = X_completa.corr().values[np.triu_indices(len(VARIABLES), k=1)]
    corr_rec = X_rec.corr().values[np.triu_indices(len(VARIABLES), k=1)]
    error_corr = float(np.abs(corr_real - corr_rec).mean())

    filas_resultado.append({
        "Estrategia": nombre,
        "RMSE normalizado": round(rmse_norm, 4),
        "Ratio desv. tipica": round(ratio_sd, 4),
        "Error medio de correlacion": round(error_corr, 4),
    })

comparacion_imp = pd.DataFrame(filas_resultado).set_index("Estrategia")
print("\nComparacion de estrategias de imputacion (faltantes simulados al 10 %):\n")
print(comparacion_imp.to_string())

RES["comparacion_imputacion"] = comparacion_imp.reset_index().to_dict("records")
''')

    code(r'''
# Celda 3.4. Efecto visual de la imputacion sobre las distribuciones.
# Objetivo: mostrar graficamente la distorsion que introduce cada estrategia. La
#   comparacion se hace sobre cuatro variables de forma distinta: una simetrica,
#   una sesgada, una porcentual y una de conteo.
# Salidas: la figura fig_imputacion.

def comparar_distribuciones(df_real, dict_imputados, columnas, ncols=4):
    """Superpone la distribucion real y la imputada para cada variable.

    Parametros
    ----------
    df_real : DataFrame
        Datos completos originales, que hacen de verdad de referencia.
    dict_imputados : dict
        Diccionario {nombre_estrategia: DataFrame imputado}.
    columnas : list
        Variables a representar.
    ncols : int
        Numero de columnas de la rejilla de subgraficos.
    """
    nrows = int(np.ceil(len(columnas) / ncols))
    fig, ejes = plt.subplots(nrows, ncols, figsize=(ncols * 2.9, nrows * 2.7))
    ejes = np.atleast_1d(ejes).flatten()

    for eje, col in zip(ejes, columnas):
        # Distribucion verdadera como referencia, con area rellena.
        sns.kdeplot(df_real[col], ax=eje, color=UNIR_GRIS_OSC, lw=2,
                    label="Original", fill=True, alpha=0.12)
        # Una curva por estrategia de imputacion.
        for nombre, X_rec in dict_imputados.items():
            sns.kdeplot(X_rec[col], ax=eje, lw=1.3, label=nombre)
        eje.set_title(col, fontsize=10)
        eje.set_xlabel("")
        eje.set_ylabel("")
        eje.legend(fontsize=8)

    # Se eliminan los ejes sobrantes de la rejilla.
    for eje in ejes[len(columnas):]:
        fig.delaxes(eje)

    fig.suptitle("Efecto de cada estrategia de imputacion sobre la distribucion",
                 fontsize=12)
    plt.tight_layout()


comparar_distribuciones(X_completa, imputaciones,
                        ["LB", "ASTV", "MSTV", "Variance"])
guardar("fig_imputacion")
''')

    md(r"""
El experimento cuantifica lo que la teoría anticipaba. La imputación por vecinos
más cercanos gana en las tres métricas a la vez: su RMSE normalizado es de
0,224, frente a 0,382 de la media, 0,399 de la mediana y 0,481 de la moda, de
modo que reduce el error de reconstrucción casi a la mitad. La razón es que
estima cada hueco a partir de las cinco observaciones más parecidas y aprovecha
así la correlación entre variables documentada en el apartado 2.4, estructura
que los tres imputadores por constante ignoran por completo.

Todas las estrategias comprimen la dispersión, puesto que el ratio de
desviaciones típicas cae por debajo de 1 en los cuatro casos. Sustituir el 10 %
de los valores por un único número central reduce de forma mecánica la varianza.
La media es la que más la degrada, con un ratio de 0,949, y el método de vecinos
la que menos, con 0,983. Este último es además el único que preserva la
estructura de correlaciones, algo decisivo para el análisis de componentes
principales posterior: su error medio en la matriz de correlaciones es de 0,006,
cuatro veces menor que el de la media, que llega a 0,027, y seis veces menor que
el de la moda, que alcanza 0,038.

La figura muestra un aspecto que el RMSE no llega a capturar. La media, dibujada
en azul, crea un pico artificial justo en el valor medio de `ASTV` y de `MSTV`,
una moda que no existe en la distribución real. La moda, en verde, resulta aún
peor, porque concentra masa en el valor más frecuente y deforma por completo la
distribución de `LB` y de `ASTV`. La curva del método de vecinos, en rojo, se
superpone casi exactamente a la distribución original.

En conclusión, si en este conjunto hubiera habido faltantes reales y dispersos,
la elección correcta habría sido la imputación por vecinos más cercanos, y por
un margen amplio. Entre las estrategias simples, la media y la mediana quedan
muy igualadas, ya que la primera reconstruye algo mejor y la segunda conserva
algo mejor la dispersión, mientras que la moda debe descartarse para variables
continuas. Pero como los faltantes de este conjunto proceden de tres filas que
no son observaciones, la decisión que finalmente se aplica es eliminarlas, y el
conjunto de trabajo queda con 2 126 registros completos.
""")
