# -*- coding: utf-8 -*-
"""Celdas del notebook: preparacion de la matriz (seccion 4) y deteccion de anomalias (seccion 5)."""

from nb_base import md, code


def construir():
    # ================================================== 4. PREPARACION DE DATOS
    md(r"""
# 4. Preparación de la matriz de características

Antes de aplicar los algoritmos hay que decidir con qué columnas se los
alimenta, y es probablemente la decisión de mayor impacto de todo el trabajo.
Se toma a partir de las evidencias reunidas en el análisis exploratorio.

Se descartan `FileName`, `Date`, `SegFile`, `b` y `e` porque identifican el
registro y no describen al feto, según se vio en el apartado 2.3. Se descarta
`LBE` por ser un duplicado exacto de `LB`, y `DR` por ser constante e igual a
cero, de manera que su varianza es nula y no aporta información alguna. Se
descarta `Width` porque es una combinación lineal exacta de otras dos columnas.
Se descartan las diez indicadoras que van de `A` a `SUSP` por tratarse de la
codificación disyuntiva de la etiqueta `CLASS`. Y se apartan `CLASS` y `NSP`,
que quedan reservadas como verdad de referencia externa. Las veinte columnas
restantes son descriptores cuantitativos genuinos del trazado y constituyen la
matriz de trabajo.

## 4.1 Por qué importa eliminar la variable Width

La igualdad entre `Width` y la diferencia de `Max` y `Min` se cumple en las
2 126 filas sin una sola excepción. Eso hace que la matriz de datos tenga rango
20 con 21 columnas, es decir, que su matriz de covarianzas sea singular y no
pueda invertirse. La distancia de Mahalanobis exige exactamente esa inversión,
de modo que mantener `Width` haría fracasar, o al menos volvería numéricamente
inestable, uno de los cinco detectores de la sección 5. Es un ejemplo claro de
por qué el análisis exploratorio debe preceder al modelado.

## 4.2 Por qué estandarizar

K-Means, DBSCAN, el factor local de atipicidad y la distancia de Mahalanobis se
basan todos ellos en distancias. Con las escalas originales, `Variance`, cuyo
rango va de 0 a 269, pesaría cientos de veces más que `MSTV`, que se mueve entre
0 y 7, y lo haría únicamente por su unidad de medida. La estandarización, que
transforma cada valor restándole la media de su columna y dividiéndolo entre la
desviación típica, deja todas las variables con media cero y desviación uno, de
manera que cada descriptor contribuye en igualdad de condiciones.
""")

    code(r'''
# Celda 4.1. Construccion de la matriz de caracteristicas.
# Objetivo: materializar las decisiones descritas arriba y verificar
#   numericamente que se resuelven los problemas detectados.
# Salidas: X, la matriz sin escalar; Z, la matriz estandarizada; y las etiquetas
#   y_nsp e y_class, apartadas para la validacion externa.

# Verificacion previa de las redundancias detectadas en el EDA.
print("Comprobaciones de redundancia:")
print("  LBE identica a LB          :", bool((df["LBE"] == df["LB"]).all()))
print("  DR constante               :", df["DR"].nunique() == 1,
      "(valores unicos:", df["DR"].unique().tolist(), ")")
print("  Width == Max - Min         :", bool((df["Width"] == (df["Max"] - df["Min"])).all()))

# Conjunto final de variables
VARIABLES_MODELO = ["LB", "AC", "FM", "UC", "ASTV", "MSTV", "ALTV", "MLTV",
                    "DL", "DS", "DP", "Min", "Max", "Nmax", "Nzeros",
                    "Mode", "Mean", "Median", "Variance", "Tendency"]

X = df[VARIABLES_MODELO].copy()          # matriz en unidades originales
y_nsp = df["NSP"].astype(int).values     # etiqueta apartada (3 niveles)
y_class = df["CLASS"].astype(int).values # etiqueta apartada (10 patrones)

print("\nMatriz de caracteristicas:", X.shape[0], "observaciones x",
      X.shape[1], "variables")

# Estandarizacion: StandardScaler calcula mu y sigma por columna y aplica
# z = (x - mu) / sigma.
escalador = StandardScaler()
Z = escalador.fit_transform(X)

print("\nEfecto de la estandarizacion (3 variables de control):")
print("  %-10s %12s %12s | %10s %10s" % ("Variable", "media orig.", "desv. orig.",
                                          "media z", "desv. z"))
for v in ["LB", "MSTV", "Variance"]:
    k = VARIABLES_MODELO.index(v)
    print("  %-10s %12.2f %12.2f | %10.2f %10.2f"
          % (v, X[v].mean(), X[v].std(), Z[:, k].mean(), Z[:, k].std()))

# La matriz debe tener rango completo para que su covarianza sea invertible.
rango = np.linalg.matrix_rank(Z)
print("\nRango de la matriz estandarizada:", rango, "de", Z.shape[1], "columnas")
assert rango == Z.shape[1], "La matriz sigue siendo singular: revisar redundancias"
print("Verificacion superada: la covarianza es invertible.")

RES["n_variables_modelo"] = len(VARIABLES_MODELO)
RES["variables_modelo"] = VARIABLES_MODELO
''')

    code(r'''
# Celda 4.2. Analisis de componentes principales.
# Objetivo: cuantificar la dimensionalidad efectiva del problema y obtener una
#   proyeccion en dos dimensiones que se reutilizara para visualizar tanto las
#   anomalias de la seccion 5 como los grupos de la seccion 6.
# Nota: el PCA se ajusta sobre datos ya estandarizados, lo que equivale a
#   diagonalizar la matriz de correlaciones y no la de covarianzas.
# Salidas: el objeto pca, la matriz Z_pca con todas las componentes y Z2 con las
#   dos primeras.

pca = PCA(random_state=SEMILLA)
Z_pca = pca.fit_transform(Z)

varianza = pca.explained_variance_ratio_
acumulada = np.cumsum(varianza)

print("Varianza explicada por las primeras componentes principales:")
print("  CP    individual    acumulada")
for i in range(6):
    print("  %2d    %8.1f %%   %8.1f %%" % (i + 1, 100 * varianza[i], 100 * acumulada[i]))

# Componentes necesarias para retener el 80 % y el 90 % de la varianza.
n80 = int(np.searchsorted(acumulada, 0.80) + 1)
n90 = int(np.searchsorted(acumulada, 0.90) + 1)
print("  Componentes necesarias: %d para el 80 %% de la varianza y %d para el 90 %%"
      % (n80, n90))

# Grafico de sedimentacion y varianza acumulada
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.5))

a1.bar(range(1, len(varianza) + 1), 100 * varianza, color=UNIR_CIAN)
a1.set_xlabel("Componente principal")
a1.set_ylabel("Varianza explicada (%)")
a1.set_title("Grafico de sedimentacion")

a2.plot(range(1, len(acumulada) + 1), 100 * acumulada, "o-", color=UNIR_CIAN_OSC)
a2.axhline(80, ls="--", color=UNIR_GRIS, lw=1)
a2.axhline(90, ls=":", color=UNIR_GRIS, lw=1)
a2.set_xlabel("Numero de componentes")
a2.set_ylabel("Varianza acumulada (%)")
a2.set_title("Varianza acumulada")
plt.tight_layout()
guardar("fig_pca_varianza")

# Las cargas indican con que peso entra cada variable original en cada
# componente, y son la clave para interpretarlas.
cargas = pd.DataFrame(pca.components_[:2].T, index=VARIABLES_MODELO,
                      columns=["CP1", "CP2"]).round(3)
def resumen_cargas(cp, n=4):
    """Devuelve, en una sola linea, las n cargas mas negativas y las n mas positivas."""
    orden = cargas[cp].sort_values()
    extremos = list(orden.head(n).items()) + list(orden.tail(n).items())
    return ", ".join("%s %+.2f" % (v, x) for v, x in extremos)


print("\nCargas extremas de CP1:", resumen_cargas("CP1"))
print("Cargas extremas de CP2:", resumen_cargas("CP2"))

Z2 = Z_pca[:, :2]            # proyeccion 2D reutilizada en todas las figuras
Z_pca80 = Z_pca[:, :n80]     # espacio reducido al 80 % de varianza

RES["pca_var"] = [round(float(v), 4) for v in varianza[:8]]
RES["pca_n80"] = n80
''')

    md(r"""
La primera componente explica el 27,5 % de la varianza y la segunda el 15,8 %,
de modo que entre ambas apenas superan el 43 %, y hacen falta nueve componentes
para alcanzar el 80 %. El problema no es, por tanto, de dimensionalidad trivial:
no puede resumirse en dos ejes sin perder información sustancial. Las dos
primeras componentes se emplearán únicamente para visualizar, nunca como entrada
única de un modelo.

Las cargas admiten una lectura clínica directa. La primera componente contrapone
las variables de tendencia central y anchura del histograma, `Mean`, `Mode`,
`Median` y `Max`, frente a las de variabilidad anormal, `ASTV` y `ALTV`. La
segunda separa la actividad del registro, medida por `AC`, `FM` y `UC`, de las
deceleraciones. Son, en esencia, los dos ejes con los que un obstetra describiría
un trazado.

# 5. Detección de anomalías

## 5.1 Planteamiento

Una anomalía, o valor atípico, es una observación que se aparta del
comportamiento mayoritario del conjunto. En este problema la pregunta operativa
es si resulta posible señalar automáticamente los trazados fetales inusuales sin
recurrir al diagnóstico del obstetra.

Para responderla se aplican cinco técnicas pertenecientes a tres familias
distintas. El Z-score y la regla de Tukey, también llamada criterio del rango
intercuartílico, son métodos estadísticos univariantes: el primero marca una
observación cuando alguno de sus valores tipificados supera 3 en valor absoluto
y asume por tanto la normalidad de cada variable; el segundo la marca cuando
algún valor cae fuera del intervalo delimitado por el primer cuartil menos una
vez y media el rango intercuartílico y el tercer cuartil más esa misma cantidad,
y no asume ninguna distribución, aunque sigue examinando las variables de una en
una. La distancia de Mahalanobis con estimación robusta de la covarianza es un
método estadístico multivariante que mide la separación al centro de la nube
ponderándola por la correlación entre variables, y presupone normalidad
multivariante. Isolation Forest es un ensamble de árboles que se apoya en la
idea de que los puntos raros se aíslan con muy pocos cortes aleatorios, y no
asume ninguna distribución. Por último, el factor local de atipicidad, conocido
como LOF, compara la densidad de cada punto con la de sus vecinos y tampoco
impone supuestos distribucionales.

Para que la comparación sea justa, los métodos multivariantes se calibran de
manera que señalen la misma proporción de observaciones, el 5 %. La evaluación
no se limita a contar cuántas marcan: se recurre a la etiqueta `NSP`, que ningún
modelo ha visto, para medir el enriquecimiento en casos patológicos, magnitud
que en minería de datos se conoce como lift y que se define como el cociente
entre la probabilidad de que una observación sea patológica dado que el detector
la ha marcado y la probabilidad de que lo sea sin más información. Un lift igual
a 1 significa que el detector no aporta nada frente a elegir al azar.

## 5.2 Métodos univariantes de referencia
""")

    code(r'''
# Celda 5.1. Metodos univariantes: Z-score y regla de Tukey.
# Objetivo: establecer una linea base con las dos reglas clasicas. Se aplican
#   variable a variable y se marca la fila cuando alguna de sus 20 variables
#   resulta atipica.
# Salidas: las mascaras booleanas anom_zscore y anom_iqr.

# Z-score: se marca cuando |x - mu| / sigma supera 3. Bajo normalidad, ese
# umbral deja fuera solo el 0,27 % de los casos por variable.
puntuaciones_z = np.abs((X - X.mean()) / X.std())
anom_zscore = (puntuaciones_z > 3).any(axis=1).values

# Regla de Tukey: fuera de [Q1 - 1.5*RIC, Q3 + 1.5*RIC].
Q1 = X.quantile(0.25)
Q3 = X.quantile(0.75)
RIC = Q3 - Q1
limite_inf = Q1 - 1.5 * RIC
limite_sup = Q3 + 1.5 * RIC
anom_iqr = ((X < limite_inf) | (X > limite_sup)).any(axis=1).values

print("METODOS UNIVARIANTES DE REFERENCIA\n")
print("Z-score (|z| > 3)      : %4d filas marcadas (%.1f %% del conjunto)"
      % (anom_zscore.sum(), 100 * anom_zscore.mean()))
print("Tukey (1.5 x RIC)      : %4d filas marcadas (%.1f %% del conjunto)"
      % (anom_iqr.sum(), 100 * anom_iqr.mean()))

# El problema de fondo es que la probabilidad de falso positivo se acumula con
# el numero de variables analizadas simultaneamente.
p_falso_positivo = 1 - (1 - 0.0027) ** len(VARIABLES_MODELO)
print("\nProbabilidad teorica de que una fila NORMAL sea marcada por el Z-score")
print("al examinar %d variables independientes: %.1f %%"
      % (len(VARIABLES_MODELO), 100 * p_falso_positivo))

RES["n_zscore"] = int(anom_zscore.sum())
RES["n_iqr"] = int(anom_iqr.sum())
''')

    md(r"""
Las reglas univariantes fracasan por completo en este conjunto. El Z-score marca
343 filas, el 16,1 % del total, más de tres veces la contaminación que cabría
considerar razonable. La regla de Tukey marca 1 220 filas, es decir, el 57,4 %
del conjunto; un detector de anomalías que declara anómala a más de la mitad de
la población sencillamente no detecta nada.

La causa es doble. Por un lado está el problema de las comparaciones múltiples:
aun suponiendo normalidad e independencia, examinar 20 variables con un umbral
de 3 desviaciones típicas eleva la probabilidad acumulada de falso positivo
hasta el 5,3 % por fila. Por otro, y más importante, las variables no son
normales, ya que el análisis exploratorio mostró asimetrías extremas y conteos
con exceso de ceros; en esa situación el rango intercuartílico se vuelve
minúsculo y casi cualquier valor no nulo queda fuera de los bigotes.

La lección es clara: la anormalidad de un trazado no reside en ninguna variable
aislada, sino en la combinación de sus valores, y para capturarla hacen falta
métodos multivariantes.

## 5.3 Distancia de Mahalanobis robusta
""")

    code(r'''
# Celda 5.2. Distancia de Mahalanobis con estimacion robusta de la covarianza.
# Objetivo: primer metodo multivariante. La distancia de Mahalanobis mide la
#   separacion al centro de la nube teniendo en cuenta la correlacion, mediante
#   d^2(x) = (x - mu)^T S^-1 (x - mu). Se usa el estimador MCD, que busca el
#   subconjunto mas compacto de los datos, en lugar de la media y la covarianza
#   muestrales, porque estas son ellas mismas sensibles a los atipicos y
#   producen el llamado efecto de enmascaramiento.
# Salidas: dist_mahalanobis y la mascara anom_mahalanobis.

# support_fraction = 0.85 indica que el MCD busca el subconjunto del 85 % de los
# datos cuya covarianza tiene el menor determinante, es decir, el nucleo denso.
mcd = MinCovDet(support_fraction=0.85, random_state=SEMILLA).fit(Z)
dist_mahalanobis = mcd.mahalanobis(Z)     # devuelve d^2, no d

# Criterio A: umbral teorico chi-cuadrado. Bajo normalidad multivariante, d^2
# sigue una distribucion chi2 con p grados de libertad.
umbral_chi2 = stats.chi2.ppf(0.975, df=len(VARIABLES_MODELO))
marcados_chi2 = dist_mahalanobis > umbral_chi2

# Criterio B: proporcion fija del 5 %, para poder comparar con los demas.
N_ANOMALIAS = int(round(0.05 * len(Z)))
umbral_5pct = np.sort(dist_mahalanobis)[-N_ANOMALIAS]
anom_mahalanobis = dist_mahalanobis >= umbral_5pct

print("Umbral teorico chi2(0.975, %d gl) = %.1f" % (len(VARIABLES_MODELO), umbral_chi2))
print("  marcaria %d filas (%.1f %% del conjunto)"
      % (marcados_chi2.sum(), 100 * marcados_chi2.mean()))
print("\nUmbral empirico al 5 %% (d^2 >= %.1f)" % umbral_5pct)
print("  marca %d filas (%.1f %% del conjunto)"
      % (anom_mahalanobis.sum(), 100 * anom_mahalanobis.mean()))

# Contraste del supuesto de normalidad multivariante. Si se cumpliera, los
# cuantiles empiricos de d^2 coincidirian con los de la chi2.
cuantiles_teoricos = stats.chi2.ppf(
    (np.arange(len(Z)) + 0.5) / len(Z), df=len(VARIABLES_MODELO))

plt.figure(figsize=(10, 3.8))
plt.subplot(1, 2, 1)
plt.plot(cuantiles_teoricos, np.sort(dist_mahalanobis), ".", ms=2.5, color=UNIR_CIAN)
lim = max(cuantiles_teoricos.max(), 120)
plt.plot([0, lim], [0, lim], "--", color=UNIR_ROJO, lw=1, label="Ajuste perfecto a chi2")
plt.xlim(0, lim); plt.ylim(0, np.percentile(dist_mahalanobis, 99.5))
plt.xlabel("Cuantiles teoricos chi2"); plt.ylabel("Distancia de Mahalanobis al cuadrado")
plt.title("Grafico Q-Q del supuesto de normalidad multivariante")
plt.legend(fontsize=9)

plt.subplot(1, 2, 2)
plt.hist(dist_mahalanobis, bins=80, color=UNIR_CIAN, range=(0, np.percentile(dist_mahalanobis, 99)))
plt.axvline(umbral_5pct, color=UNIR_ROJO, ls="--", label="Umbral empirico 5 %")
plt.axvline(umbral_chi2, color=UNIR_AMBAR, ls=":", label="Umbral chi2 0.975")
plt.xlabel("Distancia de Mahalanobis al cuadrado"); plt.ylabel("Frecuencia")
plt.title("Distribucion de las distancias")
plt.legend(fontsize=9)
plt.tight_layout()
guardar("fig_mahalanobis")

RES["n_mahalanobis_chi2"] = int(marcados_chi2.sum())
''')

    md(r"""
El gráfico cuantil-cuantil se separa muy pronto de la diagonal, porque las
distancias observadas crecen mucho más rápido que las que predice la
chi-cuadrado. El supuesto de normalidad multivariante no se cumple, y esa es la
razón de que el umbral teórico marque 646 observaciones, el 30,4 % del conjunto,
una cifra sin ningún sentido operativo, ya que ningún servicio de obstetricia
revisaría a mano tres de cada diez registros. Se conserva, por tanto, el umbral
empírico del 5 %, que además permite comparar este método con Isolation Forest y
con LOF en igualdad de condiciones.

## 5.4 Isolation Forest

El método fue propuesto por Liu, Ting y Zhou (2008) y parte de una observación
sencilla. Si se particiona el espacio eligiendo al azar una variable y un punto
de corte, un punto anómalo queda aislado en muy pocos cortes, mientras que uno
situado en el núcleo denso de la nube necesita muchos. El algoritmo construye un
bosque de árboles de partición aleatoria y asigna a cada observación una
puntuación basada en su profundidad media de aislamiento.

A diferencia de casi todos los demás métodos, no modela la normalidad para
buscar después desviaciones, sino que modela directamente la rareza. No asume
ninguna distribución, tolera bien la alta dimensionalidad y su coste computacional
es lineal en el número de observaciones.
""")

    code(r'''
# Celda 5.3. Isolation Forest.
# Objetivo: detectar anomalias mediante aislamiento aleatorio recursivo.
# Parametros: n_estimators = 200 fija el numero de arboles, y cuantos mas haya
#   mas estable es la puntuacion; contamination = 0.05 declara la proporcion
#   esperada de anomalias y con ello fija el umbral de decision; max_samples =
#   256 es la submuestra por arbol recomendada por los autores, ya que
#   submuestrear mejora la deteccion al reducir el enmascaramiento entre
#   anomalias proximas.
# Salidas: score_iforest, donde un valor mayor indica mas anomalo, y la mascara
#   anom_iforest.

iforest = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    max_samples=256,
    random_state=SEMILLA,
    n_jobs=-1,
)
# fit_predict devuelve -1 para las anomalias y +1 para las observaciones normales.
etiquetas_if = iforest.fit_predict(Z)
anom_iforest = etiquetas_if == -1

# score_samples devuelve valores negativos y cuanto menor es el valor, mas
# anomala es la observacion. Se invierte el signo para que "mayor" signifique
# "mas anomalo" y la lectura resulte natural.
score_iforest = -iforest.score_samples(Z)

print("Isolation Forest: %d arboles, %d observaciones marcadas (%.1f %%), "
      "umbral aprendido %.4f"
      % (iforest.n_estimators, anom_iforest.sum(),
         100 * anom_iforest.mean(), -iforest.offset_))
print("Puntuacion de anormalidad: min %.3f | mediana %.3f | max %.3f"
      % (score_iforest.min(), np.median(score_iforest), score_iforest.max()))

# Para saber QUE hace anomalas a las observaciones marcadas se compara su perfil
# medio, en unidades z, con el del resto del conjunto.
perfil = pd.DataFrame({
    "Media z (anomalias)": Z[anom_iforest].mean(axis=0),
    "Media z (resto)": Z[~anom_iforest].mean(axis=0),
}, index=VARIABLES_MODELO)
perfil["Diferencia"] = (perfil["Media z (anomalias)"] - perfil["Media z (resto)"]).round(2)
perfil = perfil.round(2).reindex(perfil["Diferencia"].abs().sort_values(ascending=False).index)

print("\nPerfil de las anomalias detectadas (en desviaciones tipicas):\n")
print(perfil.head(8).to_string())

RES["perfil_iforest"] = perfil.head(8)["Diferencia"].to_dict()
''')

    md(r"""
El perfil de las observaciones marcadas resulta clínicamente coherente y sirve
como validación cualitativa del método. La tabla anterior recoge las ocho
variables que más separan a las anomalías del resto del conjunto. Se sitúan muy
por encima de la media general en `Variance`, con 2,33 desviaciones típicas de
diferencia, en `DP`, que recoge las deceleraciones prolongadas, con 2,22, en
`MSTV`, indicador de variabilidad errática a corto plazo, con 1,68, y también en
`Max`, `Nmax` y `DL`. Al mismo tiempo se sitúan muy por debajo en `Mean`, con
1,48 desviaciones típicas menos, y en `Mode`, con 1,39 menos; el mismo
desplazamiento a la baja aparece, algo más atenuado, en `Median` y en `Min`.

Traducido al lenguaje clínico, el algoritmo ha aislado trazados con bradicardia,
puesto que toda la tendencia central del histograma aparece desplazada a la
baja, acompañada de deceleraciones prolongadas y severas y de una variabilidad
amplia y errática. Es la descripción de manual de un trazado no tranquilizador,
y lo notable es que la haya reconstruido sin haber visto un solo diagnóstico.

Merece la pena señalar un matiz. La variable `ALTV` aparece por debajo de la
media en las anomalías, con 0,54 desviaciones típicas menos. Isolation Forest no
está capturando el fenotipo del trazado plano, caracterizado por una
variabilidad reducida y monótona, sino el fenotipo errático y decelerativo. Son
dos formas distintas de compromiso fetal y el detector se especializa en la
segunda.

## 5.5 Factor local de atipicidad

El método fue propuesto por Breunig y sus colaboradores en el año 2000 y no
busca puntos lejanos del centro, sino puntos situados en zonas menos densas que
su propio vecindario. Para cada observación compara su densidad local con la
densidad local media de sus k vecinos más próximos, de modo que un cociente muy
superior a 1 indica que el punto está más solo que quienes lo rodean.

Su ventaja teórica es la capacidad de detectar anomalías locales, es decir,
puntos que resultan anómalos respecto de su grupo aunque no sean extremos en el
conjunto global. Su debilidad es que depende críticamente del valor de k y que
la noción de densidad se degrada en dimensión alta.
""")

    code(r'''
# Celda 5.4. Factor local de atipicidad (LOF).
# Objetivo: detectar anomalias por contraste de densidad local.
# Parametros: n_neighbors = 20 fija el tamano del vecindario, valor por defecto
#   recomendado, ya que un vecindario demasiado pequeno introduce ruido y uno
#   demasiado grande borra el caracter local del metodo; contamination = 0.05
#   mantiene la misma proporcion que Isolation Forest para poder comparar.
# Salidas: score_lof y la mascara anom_lof.

lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05, n_jobs=-1)
etiquetas_lof = lof.fit_predict(Z)
anom_lof = etiquetas_lof == -1

# negative_outlier_factor_ es el LOF con el signo cambiado; se reinvierte.
score_lof = -lof.negative_outlier_factor_

print("Local Outlier Factor")
print("  Tamano del vecindario  :", lof.n_neighbors)
print("  Observaciones marcadas : %d (%.1f %%)" % (anom_lof.sum(), 100 * anom_lof.mean()))
print("  Factor LOF: min = %.2f | mediana = %.2f | max = %.2f"
      % (score_lof.min(), np.median(score_lof), score_lof.max()))

# Sensibilidad al parametro k: se comprueba cuanto cambia el conjunto detectado
# al variar el tamano del vecindario.
print("\nSensibilidad al numero de vecinos (solapamiento con k = 20):")
base_lof = anom_lof
for k in [5, 10, 20, 35, 50]:
    m = LocalOutlierFactor(n_neighbors=k, contamination=0.05).fit_predict(Z) == -1
    jac = (m & base_lof).sum() / (m | base_lof).sum()
    print("  k = %2d: %3d marcadas, indice de Jaccard con k=20: %.3f" % (k, m.sum(), jac))
''')

    md(r"""
## 5.6 Comparación de los cinco detectores

Los cinco métodos ya han emitido su veredicto. La pregunta pendiente es cuál de
ellos resulta realmente útil, y para responderla se recupera la etiqueta `NSP`
que se había apartado al comienzo.
""")

    code(r'''
# Celda 5.5. Evaluacion comparativa contra la verdad de referencia externa.
# Objetivo: medir la utilidad real de cada detector usando NSP, que ningun
#   modelo ha visto. Se calcula el porcentaje de patologicos entre los marcados,
#   que actua como precision del detector; el lift, que es ese porcentaje
#   dividido por la tasa base; y el recall, que es la fraccion del total de
#   casos patologicos que el detector logra recuperar.
# Salidas: el DataFrame tabla_anomalias.

DETECTORES = {
    "Z-score (|z|>3)":      anom_zscore,
    "Tukey (1.5 RIC)":      anom_iqr,
    "Mahalanobis MCD (5 %)": anom_mahalanobis,
    "Isolation Forest (5 %)": anom_iforest,
    "LOF k=20 (5 %)":       anom_lof,
}

tasa_base = float((y_nsp == 3).mean())   # prevalencia de patologicos: 8,3 %
total_patologicos = int((y_nsp == 3).sum())

filas = []
for nombre, mascara in DETECTORES.items():
    n = int(mascara.sum())
    prec = float((y_nsp[mascara] == 3).mean())          # precision sobre NSP=3
    prec_23 = float((y_nsp[mascara] >= 2).mean())       # precision sobre no normales
    rec = float((y_nsp[mascara] == 3).sum() / total_patologicos)
    filas.append({
        "Metodo": nombre,
        "Marcadas": n,
        "% del conjunto": round(100 * n / len(Z), 1),
        "% patologicos": round(100 * prec, 1),
        "Lift": round(prec / tasa_base, 2),
        "% no normales": round(100 * prec_23, 1),
        "Recall NSP=3": round(100 * rec, 1),
    })

tabla_anomalias = pd.DataFrame(filas).set_index("Metodo")

print("EVALUACION DE LOS DETECTORES CONTRA LA ETIQUETA NSP\n")
print("Tasa base de casos patologicos: %.1f %%  (%d de %d)\n"
      % (100 * tasa_base, total_patologicos, len(y_nsp)))
print(tabla_anomalias.to_string())
print("\nUn lift de 1.00 significa que el detector no aporta nada sobre el azar.")

RES["tabla_anomalias"] = tabla_anomalias.reset_index().to_dict("records")
RES["tasa_base_nsp3"] = round(tasa_base, 4)
''')

    code(r'''
# Celda 5.6. Concordancia entre detectores y visualizacion.
# Objetivo: medir cuanto coinciden los metodos entre si mediante el indice de
#   Jaccard, definido como el tamano de la interseccion dividido por el de la
#   union; visualizar las anomalias sobre la proyeccion PCA; y comparar el lift
#   de forma grafica.
# Salidas: las figuras fig_anomalias_jaccard y fig_anomalias_pca.

nombres = list(DETECTORES.keys())
jaccard = np.ones((len(nombres), len(nombres)))
for i, ni in enumerate(nombres):
    for j, nj in enumerate(nombres):
        a, b = DETECTORES[ni], DETECTORES[nj]
        jaccard[i, j] = (a & b).sum() / max((a | b).sum(), 1)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.0))

sns.heatmap(pd.DataFrame(jaccard, index=nombres, columns=nombres), annot=True,
            fmt=".2f", cmap=CMAP_SEQ, vmin=0, vmax=1, ax=a1,
            cbar_kws={"label": "indice de Jaccard"}, annot_kws={"size": 9})
a1.set_title("Concordancia entre detectores")
a1.tick_params(axis="x", rotation=30, labelsize=8)
a1.tick_params(axis="y", labelsize=8)

orden = tabla_anomalias["Lift"].sort_values()
colores = [UNIR_ROJO if v < 2 else UNIR_AMBAR if v < 5 else UNIR_CIAN for v in orden]
a2.barh(orden.index, orden.values, color=colores)
a2.axvline(1, color=UNIR_GRIS_OSC, ls="--", lw=1, label="Sin capacidad discriminante")
a2.set_xlabel("Lift sobre la tasa base de casos patologicos")
a2.set_title("Utilidad clinica de cada detector")
a2.tick_params(labelsize=9)
a2.legend(fontsize=9)
plt.tight_layout()
guardar("fig_anomalias_jaccard")

# Proyeccion PCA de las anomalias de los tres metodos multivariantes.
fig, ejes = plt.subplots(1, 3, figsize=(12, 3.9))
for eje, nombre in zip(ejes, ["Mahalanobis MCD (5 %)", "Isolation Forest (5 %)", "LOF k=20 (5 %)"]):
    m = DETECTORES[nombre]
    eje.scatter(Z2[~m, 0], Z2[~m, 1], s=6, c="#C9CDD1", label="Normal", alpha=0.6)
    eje.scatter(Z2[m, 0], Z2[m, 1], s=16, c=UNIR_ROJO, label="Anomalia", edgecolor="k", lw=0.2)
    eje.set_title("%s\n%.0f %% de patologicos entre las marcadas"
                  % (nombre, tabla_anomalias.loc[nombre, "% patologicos"]), fontsize=10)
    eje.set_xlabel("CP1 (%.0f %% var.)" % (100 * pca.explained_variance_ratio_[0]))
    eje.set_ylabel("CP2 (%.0f %% var.)" % (100 * pca.explained_variance_ratio_[1]))
    eje.legend(fontsize=9, markerscale=1.6)
fig.suptitle("Anomalias detectadas sobre las dos primeras componentes principales", fontsize=12)
plt.tight_layout()
guardar("fig_anomalias_pca")

print("Indice de Jaccard entre los tres metodos multivariantes:")
print("  Isolation Forest y Mahalanobis: %.3f" % jaccard[nombres.index("Isolation Forest (5 %)"),
                                                         nombres.index("Mahalanobis MCD (5 %)")])
print("  Isolation Forest y LOF        : %.3f" % jaccard[nombres.index("Isolation Forest (5 %)"),
                                                         nombres.index("LOF k=20 (5 %)")])
print("  Mahalanobis y LOF             : %.3f" % jaccard[nombres.index("Mahalanobis MCD (5 %)"),
                                                         nombres.index("LOF k=20 (5 %)")])
RES["jaccard_if_lof"] = float(round(jaccard[nombres.index("Isolation Forest (5 %)"),
                                            nombres.index("LOF k=20 (5 %)")], 3))
''')

    md(r"""
La evaluación externa ordena los cinco detectores de forma inequívoca. Isolation
Forest es el mejor con diferencia: de las 107 observaciones que marca, el 54,2 %
son casos patológicos, frente a una tasa base del 8,3 %, lo que supone un lift
de 6,55. Recupera además el 33 % de todos los casos patológicos del conjunto
examinando solamente el 5 % de los registros, de modo que, en términos
operativos, una revisión manual de ese 5 % encontraría uno de cada dos casos
graves.

La distancia de Mahalanobis robusta queda en segundo lugar, con un lift de 5,01,
resultado notable si se tiene en cuenta que su supuesto de normalidad está
claramente violado; el estimador robusto compensa buena parte del problema. El
Z-score alcanza un lift alto, de 4,90, pero a un coste inaceptable, ya que marca
el 16 % del conjunto, y su recall del 79 % resulta engañoso porque se consigue
señalando una de cada seis observaciones.

El factor local de atipicidad es el peor de los métodos multivariantes, con un
lift de 2,14. El motivo es estructural: LOF busca anomalías locales y en un
espacio de veinte dimensiones la noción de densidad local se diluye. A ello se
suma que los trazados patológicos de este conjunto no forman puntos aislados
sino una región periférica relativamente poblada, que LOF interpreta como un
vecindario legítimo. La regla de Tukey, por último, no sirve en absoluto: su
lift es de 1,65 marcando el 57 % del conjunto.

Hay un hallazgo transversal que conviene subrayar. Los índices de Jaccard son
bajos en toda la matriz, y en particular Isolation Forest y LOF comparten apenas
el 20 % de sus detecciones. Dicho de otro modo, ser una anomalía no es una
propiedad absoluta del dato sino una propiedad relativa al método, y por eso la
elección del detector no puede hacerse sin un criterio externo de utilidad como
el que aquí aporta la etiqueta `NSP`.

Se adopta en consecuencia Isolation Forest al 5 % como detector de referencia.
Sus 107 anomalías no se eliminan del conjunto, porque en un problema clínico los
valores atípicos son la señal de interés y no ruido que convenga limpiar. Se
conservan marcadas, y en la sección siguiente se comprueba que el agrupamiento
las ubica efectivamente en un grupo propio.
""")
