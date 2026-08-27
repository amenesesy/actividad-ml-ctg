# -*- coding: utf-8 -*-
"""Celdas del notebook: agrupamiento (seccion 6), comparativa (7) y conclusiones (8)."""

from nb_base import md, code


def construir():
    # ================================================================ 6. CLUSTER
    md(r"""
# 6. Técnicas de agrupamiento

## 6.1 Planteamiento

El agrupamiento busca particionar las observaciones en grupos internamente
homogéneos y mutuamente diferenciados, sin recurrir a ninguna etiqueta. Se
aplican tres algoritmos de familias distintas.

K-Means es un método particional que minimiza la inercia dentro de cada grupo,
tiende a producir grupos de forma esférica y tamaño parecido y exige fijar de
antemano el número de grupos. DBSCAN pertenece a la familia de los métodos
basados en densidad: busca regiones densas separadas por regiones vacías, admite
grupos de forma arbitraria, no obliga a fijar su número y etiqueta como ruido
aquello que no encaja en ninguno. El agrupamiento jerárquico aglomerativo con
criterio de Ward construye una jerarquía de fusiones sucesivas que minimizan el
incremento de varianza, produce grupos compactos y anidados y permite decidir el
número de grupos a posteriori, al cortar el árbol a la altura deseada.

Para valorar los resultados se emplean dos tipos de métricas. Las de validación
interna se calculan solo con los datos, y son el coeficiente de silueta, que se
mueve entre menos uno y uno y mide la cohesión frente a la separación; el índice
de Davies-Bouldin, que compara dispersión y separación y conviene que sea bajo;
y el índice de Calinski-Harabasz, que relaciona la varianza entre grupos con la
varianza interna y conviene que sea alto. Las de validación externa contrastan
la partición con la etiqueta `NSP`, que no interviene en el ajuste, y son el
índice de Rand ajustado y la información mutua normalizada; un índice de Rand
ajustado igual a cero equivale a una partición completamente aleatoria.

## 6.2 K-Means: elección del número de grupos
""")

    code(r'''
# Celda 6.1. Barrido del numero de grupos k para K-Means.
# Objetivo: evaluar k entre 2 y 10 con cuatro criterios de validacion interna y
#   dos de validacion externa, para decidir el numero de grupos con evidencia y
#   no por intuicion.
# Nota: n_init = 20 relanza el algoritmo veinte veces con inicializaciones
#   distintas y conserva la mejor, lo que mitiga su dependencia del arranque
#   aleatorio, ya que K-Means solo garantiza alcanzar un optimo local.
# Salidas: el DataFrame barrido_k.

RANGO_K = range(2, 11)
registros = []

for k in RANGO_K:
    modelo = KMeans(n_clusters=k, n_init=20, random_state=SEMILLA).fit(Z)
    etiquetas = modelo.labels_
    registros.append({
        "k": k,
        "Inercia": round(modelo.inertia_, 1),
        "Silueta": round(silhouette_score(Z, etiquetas), 4),
        "Davies-Bouldin": round(davies_bouldin_score(Z, etiquetas), 4),
        "Calinski-Harabasz": round(calinski_harabasz_score(Z, etiquetas), 1),
        "ARI vs NSP": round(adjusted_rand_score(y_nsp, etiquetas), 4),
        "NMI vs NSP": round(normalized_mutual_info_score(y_nsp, etiquetas), 4),
    })

barrido_k = pd.DataFrame(registros).set_index("k")
print("Barrido del numero de grupos (validacion interna y externa):")
print(barrido_k.to_string())

# Deteccion analitica del codo de la curva de inercia. Se define como el punto
# de maxima distancia perpendicular a la recta que une el primer y el ultimo
# valor de la curva, lo que evita la lectura subjetiva del grafico.
ks = np.array(list(RANGO_K), dtype=float)
inercias = barrido_k["Inercia"].values.astype(float)
p1 = np.array([ks[0], inercias[0]])
p2 = np.array([ks[-1], inercias[-1]])
direccion = (p2 - p1) / np.linalg.norm(p2 - p1)
distancias = []
for x, yv in zip(ks, inercias):
    v = np.array([x, yv]) - p1
    distancias.append(np.linalg.norm(v - np.dot(v, direccion) * direccion))
k_codo = int(ks[int(np.argmax(distancias))])
print("\nCodo detectado analiticamente en k =", k_codo)

RES["barrido_k"] = barrido_k.reset_index().to_dict("records")
RES["k_codo"] = k_codo
''')

    code(r'''
# Celda 6.2. Representacion grafica de los criterios de seleccion de k.
# Objetivo: mostrar en un solo panel los cuatro criterios internos y los dos
#   externos, para que el conflicto entre ellos resulte visible de un vistazo.
# Salidas: la figura fig_kmeans_seleccion.

fig, ejes = plt.subplots(2, 3, figsize=(11.5, 6.0))

paneles = [
    ("Inercia", "Metodo del codo", UNIR_CIAN, None),
    ("Silueta", "Coeficiente de silueta (mayor = mejor)", UNIR_CIAN_OSC, "max"),
    ("Davies-Bouldin", "Indice Davies-Bouldin (menor = mejor)", UNIR_ROJO, "min"),
    ("Calinski-Harabasz", "Indice Calinski-Harabasz (mayor = mejor)", UNIR_GRIS, "max"),
    ("ARI vs NSP", "Rand ajustado frente a NSP (validacion externa)", UNIR_AMBAR, "max"),
    ("NMI vs NSP", "Informacion mutua normalizada frente a NSP", UNIR_CIAN_CLA, "max"),
]

for eje, (columna, titulo, color, optimo) in zip(ejes.flatten(), paneles):
    serie = barrido_k[columna]
    eje.plot(serie.index, serie.values, "o-", color=color, lw=1.8)
    # Se marca el k optimo segun ese criterio concreto.
    if optimo == "max":
        k_opt = serie.idxmax()
    elif optimo == "min":
        k_opt = serie.idxmin()
    else:
        k_opt = k_codo
    eje.axvline(k_opt, ls="--", color=UNIR_GRIS, lw=1)
    eje.set_title(titulo + "  (k = %d)" % k_opt, fontsize=10)
    eje.set_xlabel("Numero de grupos k")
    eje.set_xticks(list(RANGO_K))

fig.suptitle("Criterios para elegir el numero de grupos en K-Means", fontsize=13)
plt.tight_layout()
guardar("fig_kmeans_seleccion")
''')

    md(r"""
Los criterios no coinciden entre sí, y esa discrepancia constituye en sí misma
el hallazgo más instructivo del apartado. La curva de inercia decrece de forma
suave, sin codo pronunciado; el criterio analítico lo sitúa en k igual a 5, pero
la curvatura es débil, lo que indica que no existe una estructura de grupos
fuertemente separados. El coeficiente de silueta alcanza su máximo en k igual a
2, con un valor de 0,183, y todos los valores del barrido quedan por debajo de
0,19, cuando en un conjunto con grupos nítidos se esperarían valores superiores
a 0,5. El índice de Davies-Bouldin alcanza su mínimo en k igual a 7, con 1,47, y
el de Calinski-Harabasz decrece de forma monótona, favoreciendo por tanto el
menor k posible. Los tres criterios internos apuntan, en definitiva, a tres
valores distintos: 5, 2 y 2.

La validación externa, en cambio, sí resulta concluyente. El índice de Rand
ajustado alcanza su máximo inequívoco en k igual a 3, con 0,214, y cae a menos
de la mitad en k igual a 4, donde vale 0,091. La información mutua normalizada
es prácticamente máxima también ahí, con 0,222 frente a los 0,226 de k igual a
6, un valor que requiere el doble de grupos para no ganar nada.

Se adopta en consecuencia k igual a 3, por dos razones independientes que
apuntan al mismo valor. La razón primaria es de dominio: el problema clínico
está definido sobre tres estados fetales, normal, sospechoso y patológico, de
manera que elegir tres grupos responde a la estructura conocida del fenómeno y
no a los datos, lo que evita cualquier circularidad. La razón secundaria es la
confirmación externa: que el índice de Rand ajustado alcance su máximo
precisamente en tres grupos indica que esa estructura de tres niveles existe
realmente en los descriptores numéricos y no es solo una convención médica.

Conviene señalar de forma explícita que el coeficiente de silueta habría llevado
a elegir dos grupos, una partición cuyo índice de Rand ajustado resulta ser
prácticamente nulo, de 0,016. Es un aviso importante: los índices internos miden
geometría, no significado.

## 6.3 Perfilado e interpretación de los grupos
""")

    code(r'''
# Celda 6.3. Ajuste final de K-Means y perfilado de los grupos.
# Objetivo: ajustar el modelo definitivo y caracterizar cada grupo. Un
#   agrupamiento sin interpretacion no pasa de ser un vector de numeros: el
#   valor del analisis esta en explicar que distingue a cada grupo.
# Salidas: las etiquetas etq_kmeans, el DataFrame centroides y la figura
#   fig_kmeans_perfil.

K_ELEGIDO = 3
kmeans = KMeans(n_clusters=K_ELEGIDO, n_init=50, random_state=SEMILLA).fit(Z)
etq_kmeans = kmeans.labels_

# Los centroides estan en unidades estandarizadas, de modo que cada valor indica
# cuantas desviaciones tipicas por encima o por debajo de la media general se
# situa el grupo en esa variable.
centroides = pd.DataFrame(kmeans.cluster_centers_, columns=VARIABLES_MODELO)
centroides.index = ["Grupo %d" % i for i in range(K_ELEGIDO)]

tamanos = pd.Series(etq_kmeans).value_counts().sort_index()
print("Tamano de los grupos:")
for i, n in tamanos.items():
    print("  Grupo %d: %4d observaciones (%.1f %%)" % (i, n, 100 * n / len(Z)))
print("\nSilueta global: %.4f" % silhouette_score(Z, etq_kmeans))

plt.figure(figsize=(11, 3.1))
sns.heatmap(centroides, annot=True, fmt=".2f", cmap=CMAP_DIV, center=0,
            vmin=-2.2, vmax=2.2, linewidths=0.4, annot_kws={"size": 8},
            cbar_kws={"label": "desviaciones tipicas"})
plt.title("Perfil de los centroides de K-Means (k = 3)")
plt.tight_layout()
guardar("fig_kmeans_perfil")

print("\nVariables mas caracteristicas de cada grupo:\n")
for g in range(K_ELEGIDO):
    fila = centroides.loc["Grupo %d" % g]
    destacadas = fila.reindex(fila.abs().sort_values(ascending=False).index).head(6)
    texto = ", ".join(["%s %+.2f" % (v, x) for v, x in destacadas.items()])
    print("  Grupo %d (n = %d): %s" % (g, tamanos[g], texto))

RES["tamanos_kmeans"] = {int(i): int(n) for i, n in tamanos.items()}
RES["silueta_kmeans"] = round(float(silhouette_score(Z, etq_kmeans)), 4)
RES["centroides_kmeans"] = centroides.round(2).to_dict("index")
''')

    code(r'''
# Celda 6.4. Validacion externa: contraste de los grupos con el diagnostico NSP.
# Objetivo: comprobar si los grupos hallados sin supervision se corresponden con
#   los estados fetales que diagnosticaron los obstetras.
# Salidas: la tabla de contingencia y la figura fig_kmeans_nsp.

NOMBRES_NSP = {1: "Normal", 2: "Sospechoso", 3: "Patologico"}

contingencia = pd.crosstab(
    pd.Series(etq_kmeans, name="Grupo K-Means"),
    pd.Series([NOMBRES_NSP[v] for v in y_nsp], name="Diagnostico NSP"),
)
contingencia = contingencia[["Normal", "Sospechoso", "Patologico"]]
porcentajes = (100 * contingencia.div(contingencia.sum(axis=1), axis=0)).round(1)

print("Contingencia (conteos y, entre parentesis, porcentaje por fila):\n")
print((contingencia.astype(str) + " (" + porcentajes.astype(str) + " %)").to_string())

ari = adjusted_rand_score(y_nsp, etq_kmeans)
nmi = normalized_mutual_info_score(y_nsp, etq_kmeans)
# Pureza: proporcion de aciertos si a cada grupo se le asignara su clase mayoritaria.
pureza = contingencia.max(axis=1).sum() / contingencia.values.sum()
# Prueba chi-cuadrado de independencia entre grupo y diagnostico.
chi2, p_valor, gl, _ = stats.chi2_contingency(contingencia.values)

print("\nValidacion externa: ARI %.4f | NMI %.4f | pureza %.4f" % (ari, nmi, pureza))
print("Chi-cuadrado de independencia: %.1f (gl = %d), p = %.3e" % (chi2, gl, p_valor))
print("Con p < 0.001, la asociacion con el diagnostico no es atribuible al azar.")

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.9))

porcentajes.plot(kind="bar", stacked=True, ax=a1,
                 color=[UNIR_CIAN, UNIR_AMBAR, UNIR_ROJO], width=0.7)
a1.axhline(100 * (y_nsp == 1).mean(), ls="--", color=UNIR_GRIS_OSC, lw=1,
           label="Tasa base de normales (%.0f %%)" % (100 * (y_nsp == 1).mean()))
a1.set_ylabel("Composicion del grupo (%)")
a1.set_xlabel("")
a1.set_title("Composicion diagnostica de cada grupo")
a1.tick_params(axis="x", rotation=0)
a1.legend(fontsize=9, loc="lower right")

for g in range(K_ELEGIDO):
    m = etq_kmeans == g
    a2.scatter(Z2[m, 0], Z2[m, 1], s=7, alpha=0.6, label="Grupo %d (n=%d)" % (g, m.sum()))
centros_2d = pca.transform(kmeans.cluster_centers_)[:, :2]
a2.scatter(centros_2d[:, 0], centros_2d[:, 1], s=130, marker="X",
           c=UNIR_GRIS_OSC, edgecolor="white", lw=1.5, label="Centroides", zorder=5)
a2.set_xlabel("CP1 (%.0f %% var.)" % (100 * pca.explained_variance_ratio_[0]))
a2.set_ylabel("CP2 (%.0f %% var.)" % (100 * pca.explained_variance_ratio_[1]))
a2.set_title("Grupos sobre las componentes principales")
a2.legend(fontsize=9, markerscale=1.8)
plt.tight_layout()
guardar("fig_kmeans_nsp")

RES["ari_kmeans"] = round(float(ari), 4)
RES["nmi_kmeans"] = round(float(nmi), 4)
RES["pureza_kmeans"] = round(float(pureza), 4)
RES["contingencia_kmeans"] = contingencia.to_dict("index")
RES["porcentajes_kmeans"] = porcentajes.to_dict("index")
''')

    code(r'''
# Celda 6.5. Relacion entre los grupos y las anomalias de la seccion 5.
# Objetivo: comprobar si las dos tecnicas, aplicadas de forma independiente,
#   convergen. Si el agrupamiento aisla un grupo minoritario y ese mismo grupo
#   concentra las anomalias de Isolation Forest, ambas estan describiendo la
#   misma estructura subyacente.

cruce = pd.crosstab(
    pd.Series(etq_kmeans, name="Grupo K-Means"),
    pd.Series(np.where(anom_iforest, "Anomalia IF", "Normal IF"), name="Isolation Forest"),
)
cruce_pct = (100 * cruce.div(cruce.sum(axis=1), axis=0)).round(1)

print("Anomalias de Isolation Forest por grupo de K-Means "
      "(tasa global: 5.0 %):\n")
print(pd.DataFrame({"Anomalias": cruce["Anomalia IF"],
                    "Normales": cruce["Normal IF"],
                    "% anomalias": cruce_pct["Anomalia IF"]}).to_string())

RES["anomalias_por_grupo"] = cruce_pct["Anomalia IF"].round(1).to_dict()
''')

    md(r"""
El perfilado convierte tres etiquetas numéricas en tres fenotipos clínicos
reconocibles.

El grupo 0 reúne 204 observaciones, el 9,6 % del conjunto, y corresponde al
trazado comprometido. Es el grupo pequeño y extremo. Presenta `DP` en 2,21 y
`DL` en 1,66 desviaciones típicas por encima de la media, lo que se traduce en
abundantes deceleraciones prolongadas y ligeras; `Variance` en 1,73 y `MSTV` en
1,28, indicativos de una variabilidad errática; y valores muy bajos de tendencia
central, con `Mean` en menos 1,86, `Median` en menos 1,56, `Mode` en menos 1,55
y `Min` en menos 1,10, es decir, bradicardia. Su composición diagnóstica es la
más severa, con un 51,5 % de casos patológicos frente a la tasa base del 8,3 %.
Este único grupo, que representa menos de una décima parte del conjunto,
contiene el 60 % de todos los casos patológicos. Además, el 38 % de sus miembros
fueron marcados como anomalía por Isolation Forest, cuando en los otros dos
grupos esa proporción no llega al 2 %.

El grupo 1 reúne 835 observaciones, el 39,3 %, y corresponde a un patrón de
variabilidad reducida con taquicardia relativa. Muestra `LB` en 0,72 y `Min` en
0,88, lo que indica una línea de base elevada; `ASTV` en 0,58 y `ALTV` en 0,67,
que reflejan mucho tiempo con variabilidad anormal; y `MSTV` en menos 0,75, es
decir, una variabilidad efectiva baja. Su composición es del 61,3 % de casos
normales pero también de un 31,0 % de sospechosos, casi el triple de la tasa
base. Es, en definitiva, el grupo intermedio o de vigilancia.

El grupo 2 reúne 1 087 observaciones, el 51,1 %, y corresponde al trazado
tranquilizador. Presenta `AC` en 0,27 y `MLTV` en 0,29, con aceleraciones
presentes y buena variabilidad a largo plazo, junto a `ASTV` en menos 0,49 y
`ALTV` en menos 0,42, esto es, poco tiempo anormal. Su composición es de un
97,1 % de casos normales, con apenas 7 patológicos.

El índice de Rand ajustado de 0,214 puede parecer modesto en abstracto, pero la
prueba chi-cuadrado descarta el azar de forma contundente y la tabla de
contingencia muestra un gradiente monótono de gravedad entre los grupos. El
valor moderado tiene además una explicación clara: el agrupamiento separa muy
bien los extremos, es decir, los grupos 0 y 2, pero no logra aislar la categoría
de los sospechosos, que es intrínsecamente una zona de transición y no un
fenotipo con frontera propia. Por otra parte, la convergencia entre las dos
técnicas, dado que el grupo más anómalo según K-Means es también donde se
concentran las anomalías de Isolation Forest, refuerza la conclusión de que la
estructura hallada es real.

## 6.4 DBSCAN
""")

    code(r'''
# Celda 6.6. DBSCAN: eleccion de eps mediante el grafico de k-distancias.
# Objetivo: DBSCAN agrupa regiones densas y etiqueta como ruido, con el valor
#   -1, lo que queda fuera. Necesita dos parametros: min_samples, que es el
#   numero minimo de puntos para considerar densa una zona, y eps, que es el
#   radio del vecindario. El valor de eps se elige con la heuristica de Ester y
#   colaboradores (1996): se ordena la distancia de cada punto a su k-esimo
#   vecino y se busca el codo de la curva resultante.
# Nota: DBSCAN se aplica sobre el espacio reducido por PCA y no sobre las veinte
#   variables originales, porque en dimension alta las distancias se concentran
#   y la nocion de densidad pierde contraste.
# Salidas: la figura fig_dbscan_kdist y el valor EPS_ELEGIDO.

Z_dbscan = Z_pca80
MIN_SAMPLES = 10
print("Espacio de trabajo de DBSCAN:", Z_dbscan.shape[1], "componentes principales",
      "(%.0f %% de la varianza)" % (100 * np.cumsum(pca.explained_variance_ratio_)[Z_dbscan.shape[1] - 1]))

vecinos = NearestNeighbors(n_neighbors=MIN_SAMPLES).fit(Z_dbscan)
distancias, _ = vecinos.kneighbors(Z_dbscan)
k_dist = np.sort(distancias[:, -1])

plt.figure(figsize=(6.5, 3.4))
plt.plot(k_dist, lw=1.6, color=UNIR_CIAN)
plt.axhline(2.0, color=UNIR_ROJO, ls="--", lw=1, label="eps = 2.0 (valor elegido)")
plt.xlabel("Observaciones ordenadas por distancia")
plt.ylabel("Distancia al vecino n. %d" % MIN_SAMPLES)
plt.title("Grafico de k-distancias para la eleccion de eps")
plt.legend(fontsize=9)
plt.tight_layout()
guardar("fig_dbscan_kdist")

print("\nPercentiles de la distancia al vecino n. %d:" % MIN_SAMPLES)
for p in [50, 75, 90, 95, 99]:
    print("  P%2d = %.2f" % (p, np.percentile(k_dist, p)))

EPS_ELEGIDO = 2.0
''')

    code(r'''
# Celda 6.7. Barrido de parametros y ajuste final de DBSCAN.
# Objetivo: explorar la sensibilidad de DBSCAN al par (eps, min_samples) y
#   ajustar el modelo definitivo. La silueta se calcula excluyendo el ruido,
#   porque los puntos etiquetados con -1 no constituyen un grupo.
# Salidas: las etiquetas etq_dbscan y el DataFrame barrido_dbscan.

registros = []
for eps in [1.6, 1.8, 2.0, 2.2, 2.5, 3.0]:
    for ms in [10, 16, 20]:
        etiquetas = DBSCAN(eps=eps, min_samples=ms).fit_predict(Z_dbscan)
        n_grupos = len(set(etiquetas)) - (1 if -1 in etiquetas else 0)
        n_ruido = int((etiquetas == -1).sum())
        # La silueta requiere al menos dos grupos entre los puntos no ruidosos.
        if n_grupos > 1:
            sil = silhouette_score(Z_dbscan[etiquetas != -1], etiquetas[etiquetas != -1])
        else:
            sil = np.nan
        registros.append({
            "eps": eps, "min_samples": ms, "Grupos": n_grupos,
            "Ruido": n_ruido, "% ruido": round(100 * n_ruido / len(Z), 1),
            "Silueta (sin ruido)": round(sil, 4) if not np.isnan(sil) else None,
            "ARI vs NSP": round(adjusted_rand_score(y_nsp, etiquetas), 4),
        })

barrido_dbscan = pd.DataFrame(registros)

# De las 18 combinaciones se imprimen solo las que llegan a formar mas de un
# grupo, porque son las unicas comparables; de las demas basta con saber cuantas
# son, ya que todas devuelven un unico grupo mas ruido.
un_solo_grupo = int((barrido_dbscan["Grupos"] <= 1).sum())
print("Sensibilidad de DBSCAN: de las %d combinaciones probadas, %d devuelven un"
      % (len(barrido_dbscan), un_solo_grupo))
print("unico grupo mas ruido. Las %d restantes son:\n"
      % (len(barrido_dbscan) - un_solo_grupo))
print(barrido_dbscan[barrido_dbscan["Grupos"] > 1].to_string(index=False))

dbscan = DBSCAN(eps=EPS_ELEGIDO, min_samples=MIN_SAMPLES)
etq_dbscan = dbscan.fit_predict(Z_dbscan)

n_grupos_db = len(set(etq_dbscan)) - (1 if -1 in etq_dbscan else 0)
ruido_db = etq_dbscan == -1

tamanos_db = ", ".join(
    "%s: %d" % ("ruido" if g == -1 else "grupo %d" % g, (etq_dbscan == g).sum())
    for g in sorted(set(etq_dbscan)))
print("\nDBSCAN definitivo (eps = %.1f, min_samples = %d): %d grupos y %d puntos "
      "de ruido (%.1f %%)"
      % (EPS_ELEGIDO, MIN_SAMPLES, n_grupos_db, ruido_db.sum(), 100 * ruido_db.mean()))
print("  Tamanos -> %s" % tamanos_db)

RES["dbscan_n_grupos"] = int(n_grupos_db)
RES["dbscan_ruido"] = int(ruido_db.sum())
RES["barrido_dbscan"] = barrido_dbscan.to_dict("records")
''')

    code(r'''
# Celda 6.8. Interpretacion de la salida de DBSCAN.
# Objetivo: contrastar los grupos y el ruido de DBSCAN con el diagnostico NSP y
#   con las anomalias de Isolation Forest.
# Salidas: las tablas impresas y la figura fig_dbscan.

etiquetas_legibles = ["Ruido" if g == -1 else "Grupo %d" % g for g in etq_dbscan]
cont_db = pd.crosstab(
    pd.Series(etiquetas_legibles, name="DBSCAN"),
    pd.Series([NOMBRES_NSP[v] for v in y_nsp], name="Diagnostico NSP"),
)[["Normal", "Sospechoso", "Patologico"]]

pct_db = (100 * cont_db.div(cont_db.sum(axis=1), axis=0)).round(1)
print("Contingencia DBSCAN frente a NSP "
      "(conteos y, entre parentesis, porcentaje por fila):\n")
print((cont_db.astype(str) + " (" + pct_db.astype(str) + " %)").to_string())

print("\nValidacion externa: ARI = %.4f | NMI = %.4f"
      % (adjusted_rand_score(y_nsp, etq_dbscan),
         normalized_mutual_info_score(y_nsp, etq_dbscan)))

jaccard_ruido = (ruido_db & anom_iforest).sum() / (ruido_db | anom_iforest).sum()
print("\nCoincidencia entre el ruido de DBSCAN y las anomalias de Isolation Forest:")
print("  Indice de Jaccard: %.3f" % jaccard_ruido)
print("  Puntos marcados por ambos metodos: %d" % (ruido_db & anom_iforest).sum())

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.0))

for g in sorted(set(etq_dbscan)):
    m = etq_dbscan == g
    if g == -1:
        a1.scatter(Z2[m, 0], Z2[m, 1], s=14, c=UNIR_ROJO, marker="x",
                   label="Ruido (n=%d)" % m.sum())
    else:
        a1.scatter(Z2[m, 0], Z2[m, 1], s=7, alpha=0.6, label="Grupo %d (n=%d)" % (g, m.sum()))
a1.set_xlabel("CP1"); a1.set_ylabel("CP2")
a1.set_title("Resultado de DBSCAN (eps = %.1f, min_samples = %d)" % (EPS_ELEGIDO, MIN_SAMPLES))
a1.legend(fontsize=9, markerscale=1.6)

colores_nsp = {1: UNIR_CIAN, 2: UNIR_AMBAR, 3: UNIR_ROJO}
for v in [1, 2, 3]:
    m = y_nsp == v
    a2.scatter(Z2[m, 0], Z2[m, 1], s=7, alpha=0.65, c=colores_nsp[v],
               label="%s (n=%d)" % (NOMBRES_NSP[v], m.sum()))
a2.set_xlabel("CP1"); a2.set_ylabel("CP2")
a2.set_title("Referencia: diagnostico real NSP")
a2.legend(fontsize=9, markerscale=1.8)
plt.tight_layout()
guardar("fig_dbscan")

RES["dbscan_ari"] = round(float(adjusted_rand_score(y_nsp, etq_dbscan)), 4)
RES["jaccard_ruido_if"] = round(float(jaccard_ruido), 3)
''')

    md(r"""
DBSCAN no produce una partición útil del conjunto, y el motivo resulta
informativo. Con los parámetros elegidos encuentra dos grupos y 213 puntos de
ruido, pero el reparto es radicalmente asimétrico: un grupo absorbe 1 885
observaciones, el 88,7 % del conjunto, y el otro apenas 28.

El barrido de parámetros demuestra que este comportamiento es estructural y no
consecuencia de una mala elección de eps. En once de las dieciocho combinaciones
probadas DBSCAN devuelve un único grupo más ruido, y en las siete restantes el
segundo grupo nunca supera unas pocas decenas de puntos. La razón es que los
datos no tienen zonas de baja densidad que separen regiones densas, sino que
forman una nube única cuya densidad decae de manera continua hacia la periferia.
DBSCAN necesita valles y aquí no los hay.

Ahora bien, el grupo 1, formado por 28 observaciones, está compuesto
íntegramente por casos patológicos. El algoritmo ha aislado un fenotipo extremo
con una precisión perfecta, si bien cubre solo el 16 % de los patológicos del
conjunto. El ruido también resulta informativo: de los 213 puntos etiquetados
con menos uno, el 33,8 % son patológicos, cuatro veces la tasa base, y su índice
de Jaccard con las anomalías de Isolation Forest es de 0,455, ya que comparten
100 puntos; se trata de la concordancia más alta observada entre dos métodos en
todo el trabajo.

La conclusión es que en este conjunto DBSCAN rinde mejor como detector de
anomalías que como algoritmo de agrupamiento. Su índice de Rand ajustado global,
de 0,197, es comparable al de K-Means, pero se consigue por una vía distinta: no
por particionar bien, sino por apartar correctamente los casos extremos. Resulta
coherente, en ese sentido, que su información mutua normalizada, de 0,134, sea
muy inferior a la de K-Means, que llega a 0,222, porque reparte mucha menos
información sobre el diagnóstico al dejar el 88,7 % de los registros en un único
grupo indiferenciado.

## 6.5 Agrupamiento jerárquico aglomerativo
""")

    code(r'''
# Celda 6.9. Agrupamiento jerarquico: dendrograma y criterios de enlace.
# Objetivo: construir la jerarquia completa de fusiones y comparar tres
#   criterios de enlace. El dendrograma permite decidir el numero de grupos a
#   posteriori, observando a que altura se producen las fusiones mas costosas.
# Salidas: la figura fig_dendrograma, las etiquetas etq_jerarquico y el
#   DataFrame comparacion_enlaces.

# linkage() de SciPy calcula la jerarquia completa. El metodo de Ward minimiza
# el incremento de varianza intragrupo en cada fusion, que es el criterio mas
# proximo al que emplea K-Means.
matriz_enlace = linkage(Z, method="ward")

plt.figure(figsize=(11, 4.0))
dendrogram(matriz_enlace, truncate_mode="lastp", p=30, leaf_rotation=90,
           leaf_font_size=9, show_contracted=True, color_threshold=70)
plt.title("Dendrograma del agrupamiento jerarquico (enlace de Ward)")
plt.xlabel("Grupos; el numero entre parentesis indica cuantas observaciones agrupa")
plt.ylabel("Distancia de fusion (incremento de varianza)")
plt.tight_layout()
guardar("fig_dendrograma")

# Comparacion de criterios de enlace. Se comprueba una advertencia clasica: los
# enlaces average y complete pueden producir particiones degeneradas con
# siluetas enganosamente altas.
filas = []
for enlace in ["ward", "average", "complete"]:
    etiquetas = AgglomerativeClustering(n_clusters=3, linkage=enlace).fit_predict(Z)
    tam = np.bincount(etiquetas)
    filas.append({
        "Enlace": enlace,
        "Tamanos": " / ".join(str(t) for t in sorted(tam, reverse=True)),
        "Grupo mayor (%)": round(100 * tam.max() / len(Z), 1),
        "Silueta": round(silhouette_score(Z, etiquetas), 4),
        "ARI vs NSP": round(adjusted_rand_score(y_nsp, etiquetas), 4),
    })

comparacion_enlaces = pd.DataFrame(filas).set_index("Enlace")
print("Comparacion de criterios de enlace con k = 3:\n")
print(comparacion_enlaces.to_string())
print("\nLos enlaces average y complete logran siluetas muy superiores a ward,")
print("pero dejando mas del 99 % de las observaciones en un unico grupo. Una")
print("silueta alta con una particion degenerada NO indica un buen agrupamiento.")

jerarquico = AgglomerativeClustering(n_clusters=3, linkage="ward")
etq_jerarquico = jerarquico.fit_predict(Z)

print("\nWard definitivo (k = 3): tamanos %s, silueta %.4f"
      % (np.bincount(etq_jerarquico).tolist(), silhouette_score(Z, etq_jerarquico)))
print("  ARI frente a NSP %.4f | ARI frente a K-Means %.4f (concordancia)"
      % (adjusted_rand_score(y_nsp, etq_jerarquico),
         adjusted_rand_score(etq_kmeans, etq_jerarquico)))

RES["comparacion_enlaces"] = comparacion_enlaces.reset_index().to_dict("records")
RES["ari_jerarquico"] = round(float(adjusted_rand_score(y_nsp, etq_jerarquico)), 4)
RES["ari_kmeans_vs_jerarquico"] = round(float(adjusted_rand_score(etq_kmeans, etq_jerarquico)), 4)
''')

    md(r"""
El dendrograma muestra un salto de altura claro en las últimas fusiones,
compatible con dos o tres grupos, lo que respalda la elección de k igual a 3.

La comparación de criterios de enlace produce el aviso metodológico más
importante de la sección. Los enlaces `average` y `complete` obtienen siluetas de
0,52 y 0,57 respectivamente, es decir, hasta cuatro veces mejores que las de
Ward, que se queda en 0,13, pero lo consiguen dejando más del 99 % de las
observaciones en un único grupo y aislando dos grupitos de entre 3 y 7 puntos.
Sus índices de Rand ajustado son prácticamente nulos, de 0,02. Es la ilustración
perfecta de que una métrica interna alta puede corresponder a un modelo
inservible, porque la silueta premia particiones en las que casi todo está junto
y unos pocos puntos muy alejados forman grupos triviales.

Con el enlace de Ward la partición es equilibrada, con 1 097, 942 y 87
observaciones, y su índice de Rand ajustado frente a `NSP` es de 0,179, algo
inferior al de K-Means, que llega a 0,214. Curiosamente su información mutua
normalizada es ligeramente superior, de 0,230 frente a 0,222, lo que indica que
Ward capta algo más de información sobre el diagnóstico pero la reparte peor
entre los grupos, que es justo lo que penaliza el índice de Rand. La concordancia
entre ambas particiones es de 0,371, de modo que coinciden en lo esencial pero
no son intercambiables, sobre todo en el trazado de la frontera entre los dos
grupos grandes.

## 6.6 Comparación global de los tres algoritmos
""")

    code(r'''
# Celda 6.10. Comparacion final de los tres algoritmos de agrupamiento.
# Objetivo: reunir en una sola tabla y en una sola figura los resultados de
#   K-Means, DBSCAN y jerarquico, con metricas internas y externas.
# Salidas: el DataFrame tabla_clustering y la figura fig_clustering_comparacion.

def evaluar_agrupamiento(nombre, etiquetas, espacio, requiere_k, maneja_ruido):
    """Calcula el bloque de metricas de un agrupamiento.

    El ruido, con etiqueta -1, se excluye de las metricas internas, ya que por
    definicion no constituye un grupo; si se incluyera penalizaria de forma
    artificial a DBSCAN frente a los algoritmos que particionan todo.
    """
    validos = etiquetas != -1
    n_grupos = len(set(etiquetas[validos]))
    sil = silhouette_score(espacio[validos], etiquetas[validos]) if n_grupos > 1 else np.nan
    db = davies_bouldin_score(espacio[validos], etiquetas[validos]) if n_grupos > 1 else np.nan
    return {
        "Algoritmo": nombre,
        "Grupos": n_grupos,
        "Sin asignar": int((~validos).sum()),
        "Silueta": round(sil, 4) if not np.isnan(sil) else None,
        "Davies-Bouldin": round(db, 4) if not np.isnan(db) else None,
        "ARI vs NSP": round(adjusted_rand_score(y_nsp, etiquetas), 4),
        "NMI vs NSP": round(normalized_mutual_info_score(y_nsp, etiquetas), 4),
        "Requiere k": "Si" if requiere_k else "No",
        "Detecta ruido": "Si" if maneja_ruido else "No",
    }


tabla_clustering = pd.DataFrame([
    evaluar_agrupamiento("K-Means (k=3)", etq_kmeans, Z, True, False),
    evaluar_agrupamiento("DBSCAN (eps=2.0)", etq_dbscan, Z_dbscan, False, True),
    evaluar_agrupamiento("Jerarquico Ward (k=3)", etq_jerarquico, Z, True, False),
]).set_index("Algoritmo")

print("COMPARACION FINAL DE LOS ALGORITMOS DE AGRUPAMIENTO\n")
print(tabla_clustering.to_string())

fig, ejes = plt.subplots(1, 3, figsize=(12, 3.9))
particiones = [
    ("K-Means (k=3)", etq_kmeans),
    ("DBSCAN (eps=2.0)", etq_dbscan),
    ("Jerarquico Ward (k=3)", etq_jerarquico),
]
for eje, (nombre, etiquetas) in zip(ejes, particiones):
    for g in sorted(set(etiquetas)):
        m = etiquetas == g
        if g == -1:
            eje.scatter(Z2[m, 0], Z2[m, 1], s=12, c=UNIR_GRIS, marker="x", label="Ruido")
        else:
            eje.scatter(Z2[m, 0], Z2[m, 1], s=6, alpha=0.6, label="G%d" % g)
    eje.set_title("%s\nARI = %.3f" % (nombre, tabla_clustering.loc[nombre, "ARI vs NSP"]), fontsize=10)
    eje.set_xlabel("CP1"); eje.set_ylabel("CP2")
    eje.legend(fontsize=9, markerscale=1.8)
fig.suptitle("Los tres agrupamientos sobre el mismo plano de componentes principales", fontsize=12)
plt.tight_layout()
guardar("fig_clustering_comparacion")

RES["tabla_clustering"] = tabla_clustering.reset_index().to_dict("records")
''')

    # =========================================== 7. VENTAJAS Y DESVENTAJAS
    md(r"""
# 7. Ventajas y desventajas de cada modelo

## 7.1 Modelos de detección de anomalías

El Z-score tiene a su favor que es trivial de calcular e interpretar y que su
umbral posee un significado probabilístico directo. En su contra pesan tres
limitaciones: asume normalidad, es univariante y por tanto ignora por completo
las correlaciones entre variables, y su error acumulado crece con el número de
columnas examinadas. En este conjunto marcó el 16,1 % de las observaciones y,
aunque alcanzó un lift de 4,90, lo hizo a costa de demasiados falsos positivos.

La regla de Tukey no asume ninguna distribución, es robusta frente a valores
extremos y constituye la base del diagrama de caja, que es una herramienta
exploratoria muy valiosa. Sin embargo, también es univariante y resulta
inservible cuando las variables presentan fuerte asimetría o exceso de ceros,
que es exactamente lo que ocurre aquí. Marcó el 57,4 % del conjunto con un lift
de 1,65, de manera que no discrimina.

La distancia de Mahalanobis con estimación robusta es multivariante y tiene en
cuenta la covarianza, y el estimador de determinante mínimo evita el efecto de
enmascaramiento que padecen la media y la covarianza muestrales. Como
contrapartida exige que la matriz de covarianzas sea invertible, requisito que
obligó a eliminar la variable `Width`, asume normalidad multivariante y su coste
computacional crece de forma cúbica con el número de variables. Obtuvo un lift
de 5,01 marcando el 5 % del conjunto, si bien el gráfico cuantil-cuantil dejó
claro que su supuesto no se cumple.

Isolation Forest no asume ninguna distribución, su coste es lineal en el número
de observaciones, escala bien en dimensión alta y tiene pocos hiperparámetros
que ajustar. Sus inconvenientes son que la proporción de contaminación debe
fijarse a priori, que el resultado varía con la semilla aleatoria y que sus
cortes son siempre paralelos a los ejes, lo que puede dificultar la detección de
estructuras oblicuas. Fue el mejor método, con un lift de 6,55, un 54,2 % de
casos patológicos entre los marcados y un recall del 33 %.

El factor local de atipicidad es el único capaz de detectar anomalías locales y
no impone ninguna forma global a los datos. En contra tiene una sensibilidad muy
alta al número de vecinos, la degradación de la noción de densidad en dimensión
alta y la imposibilidad de generalizar a datos nuevos salvo que se active
explícitamente el modo de novedad. Resultó el peor de los métodos
multivariantes, con un lift de 2,14.

## 7.2 Modelos de agrupamiento

K-Means es rápido y escalable, produce grupos fácilmente interpretables a través
de sus centroides y converge siempre. A cambio exige fijar el número de grupos,
supone que estos son esféricos y de tamaño similar, sus centroides no son
robustos frente a valores atípicos y solo garantiza alcanzar óptimos locales.
Fue el mejor de los tres, con un índice de Rand ajustado de 0,214 y tres
fenotipos clínicamente coherentes.

DBSCAN no exige fijar el número de grupos, admite grupos de forma arbitraria e
identifica el ruido de manera explícita. Sus desventajas son la enorme
sensibilidad al par de parámetros eps y min_samples, el fracaso cuando la
densidad varía de forma continua y la degradación en dimensión alta. Aquí
produjo dos grupos muy desiguales, de 1 885 y 28 observaciones, más 213 puntos
de ruido, y un índice de Rand ajustado de 0,197; resultó útil como detector pero
no como partición.

El agrupamiento jerárquico produce la jerarquía completa, de modo que el número
de grupos puede decidirse después, su dendrograma es muy interpretable y el
resultado es determinista. En su contra están el coste cuadrático en memoria y
tiempo, la imposibilidad de deshacer una fusión ya realizada y una fuerte
dependencia del criterio de enlace. Con Ward obtuvo un índice de Rand ajustado
de 0,179, mientras que los enlaces `average` y `complete` degeneraron pese a
exhibir siluetas mucho más altas.

## 7.3 Síntesis metodológica

De la comparación se desprenden tres lecciones transversales. La primera es que
las métricas internas no bastan por sí solas. El coeficiente de silueta escogía
dos grupos en K-Means, partición con un índice de Rand ajustado de 0,016, y
premiaba los enlaces degenerados del jerárquico con valores de 0,52 y 0,57 pese
a que dejaban el 99 % de los datos en un solo grupo. Sin una referencia externa
o sin conocimiento del dominio, esos criterios habrían llevado a conclusiones
erróneas.

La segunda es que los supuestos distribucionales importan más que la
sofisticación del método. Los dos algoritmos que no asumen ninguna distribución,
Isolation Forest y K-Means, fueron los mejores de su categoría, y lo fueron
precisamente en un conjunto de datos fuertemente asimétrico.

La tercera es que la convergencia entre técnicas independientes constituye la
mejor evidencia disponible. El grupo 0 de K-Means, el grupo 1 y el ruido de
DBSCAN, y las anomalías de Isolation Forest apuntan al mismo subconjunto de
trazados. Tres algoritmos con criterios matemáticos distintos coinciden porque
existe una estructura real que describir.

# 8. Conclusiones
""")

    code(r'''
# Celda 8.1. Resumen ejecutivo de resultados y volcado a disco.
# Objetivo: recapitular las cifras clave y guardar todos los resultados en
#   resultados.json, que es la fuente unica desde la que se genera el informe en
#   PDF. De este modo ninguna cifra del informe se transcribe a mano y no puede
#   desincronizarse del codigo.
# Salidas: el archivo resultados.json.

print("RESUMEN EJECUTIVO\n")
mejor = max(RES["tabla_anomalias"], key=lambda r: r["Lift"])
print("Datos      : %d registros analizados (de %d en el archivo), %d variables"
      % (RES["n_filas_final"],
         RES["n_filas_final"] + RES["n_filas_eliminadas"],
         RES["n_variables_modelo"]))
print("             %d filas eliminadas por ser filas de resumen de la hoja"
      % RES["n_filas_eliminadas"])
print("\nAnomalias  : Isolation Forest al 5 %%, %d observaciones marcadas"
      % mejor["Marcadas"])
print("             %.1f %% patologicos (tasa base %.1f %%), lift %.2f, recall %.1f %%"
      % (mejor["% patologicos"], 100 * RES["tasa_base_nsp3"],
         mejor["Lift"], mejor["Recall NSP=3"]))
print("\nAgrupamiento: K-Means con k = 3, grupos de %s observaciones"
      % " / ".join(str(v) for v in RES["tamanos_kmeans"].values()))
print("             silueta %.4f | ARI %.4f | NMI %.4f | pureza %.4f"
      % (RES["silueta_kmeans"], RES["ari_kmeans"],
         RES["nmi_kmeans"], RES["pureza_kmeans"]))


def convertir(objeto):
    """Convierte tipos de NumPy a tipos nativos serializables por json."""
    if isinstance(objeto, (np.integer,)):
        return int(objeto)
    if isinstance(objeto, (np.floating,)):
        return float(objeto)
    if isinstance(objeto, np.ndarray):
        return objeto.tolist()
    return str(objeto)


with open("resultados.json", "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=2, default=convertir)

print("\nResultados guardados en 'resultados.json' (%d claves)." % len(RES))
print("Figuras guardadas en '%s/' (%d archivos)."
      % (DIR_FIGURAS, len(list(DIR_FIGURAS.glob("*.png")))))
''')

    md(r"""
## 8.1 Sobre el análisis exploratorio

El análisis exploratorio no fue un trámite previo, sino que determinó todas las
decisiones posteriores. Permitió descubrir que las tres últimas filas del
archivo eran artefactos de exportación y no pacientes; que `LBE` duplica a `LB`,
que `DR` es constante y que `Width` equivale exactamente a la diferencia entre
`Max` y `Min`, redundancia esta última que hacía singular la matriz de
covarianzas e impedía calcular la distancia de Mahalanobis; y que las diez
variables comprendidas entre `A` y `SUSP` son una recodificación de la etiqueta
`CLASS`. De las 40 columnas iniciales solo 20 son descriptores genuinos.

El estudio de las distribuciones reveló asimetrías extremas y colas pesadas, lo
que permitió anticipar, y después confirmar, que los métodos basados en la
hipótesis de normalidad rendirían peor que los no paramétricos.

## 8.2 Sobre el tratamiento de los valores faltantes

La respuesta correcta no consistía en elegir entre la media, la mediana o la
moda, sino en reconocer que las filas afectadas no eran observaciones. Las 106
celdas faltantes se concentraban en 3 filas sin diagnóstico que resultaron ser
las filas de resumen de la hoja de cálculo original: una de mínimos y otra que
reproduce el máximo de cada columna, coincidencia comprobada variable a
variable. Imputarlas con la media habría fabricado tres pacientes ficticios, uno
de los cuales alcanzaría a la vez el valor extremo de diez variables distintas,
combinación que no se da en ningún trazado real, y habría contaminado tanto la
detección de anomalías como los centroides de K-Means.

El experimento controlado del apartado 3.3 aporta la respuesta a la pregunta
general. Cuando los faltantes son reales y dispersos, la mejor estrategia es la
imputación por vecinos más cercanos, porque aprovecha la correlación entre
variables, y la mediana es la mejor alternativa simple para las variables
sesgadas. La media, que suele aplicarse por costumbre, distorsiona la forma de
las distribuciones asimétricas, y la moda resulta la peor opción para variables
continuas.

## 8.3 Sobre la detección de anomalías

Isolation Forest es el método elegido. Marcando solo el 5 % de los registros, el
54,2 % de los señalados resultaron ser casos patológicos frente a una tasa base
del 8,3 %, lo que supone un enriquecimiento de 6,6 veces y la recuperación de un
tercio de todos los casos graves. Su perfil medio, caracterizado por
deceleraciones prolongadas y severas, variabilidad errática y bradicardia,
reproduce la descripción clínica de un trazado no tranquilizador sin haber visto
ni un solo diagnóstico.

Los métodos univariantes quedaron descartados por marcar el 16 % y el 57 % del
conjunto respectivamente. El factor local de atipicidad, pese a su sofisticación
teórica, fue el peor de los multivariantes, porque en veinte dimensiones la
densidad local pierde contraste y porque los casos patológicos de este conjunto
no son puntos aislados sino una región periférica poblada que el método
interpreta como un vecindario legítimo.

El bajo solapamiento entre métodos, con índices de Jaccard que van de 0,07 a
0,37, demuestra que ser una anomalía es una noción relativa al método empleado.
Elegir un detector exige, por tanto, un criterio externo de utilidad; sin él, la
elección sería arbitraria.

## 8.4 Sobre el agrupamiento

K-Means con tres grupos es el modelo elegido, con un índice de Rand ajustado de
0,214 frente a `NSP` y una prueba chi-cuadrado que descarta el azar. Los tres
grupos admiten lectura clínica directa: un grupo tranquilizador de 1 087
registros con un 97,1 % de casos normales, un grupo de vigilancia de 835
registros con un 31 % de sospechosos y un grupo comprometido de 204 registros
con un 51,5 % de patológicos, que concentra el 60 % de todos los casos graves
del conjunto.

DBSCAN no logró una partición útil porque los datos forman una nube única de
densidad decreciente, sin los valles que el algoritmo necesita; sin embargo
aisló un grupo de 28 casos íntegramente patológicos y su ruido coincide en un
46 %, medido por el índice de Jaccard, con las anomalías de Isolation Forest. El
jerárquico con enlace de Ward produjo una partición equilibrada y coherente, con
un índice de 0,179, mientras que los enlaces `average` y `complete` degeneraron
pese a exhibir siluetas mucho más altas.

El valor moderado de todos los índices de Rand ajustado tiene una explicación
sustantiva y no metodológica: los algoritmos separan bien los extremos, pero la
categoría de los sospechosos es por naturaleza una zona de transición y no un
fenotipo con frontera propia. Ningún método no supervisado puede recuperar una
categoría que no forma un grupo en el espacio de características.

## 8.5 Conclusión general

El trabajo muestra que el aprendizaje no supervisado recupera estructura
clínicamente válida en los datos de cardiotocografía. Sin acceder a ningún
diagnóstico, los algoritmos identificaron el subconjunto de trazados
comprometidos y un gradiente de gravedad coherente con la clasificación
obstétrica.

La conclusión práctica es que ambas técnicas resultan complementarias y no
alternativas. Isolation Forest responde a la pregunta de qué registros concretos
hay que revisar con prioridad, mientras que K-Means responde a la de qué tipos
de trazado existen en la población. Un sistema de apoyo a la decisión clínica se
beneficiaría de las dos: el agrupamiento para estratificar a la población y la
detección de anomalías para priorizar la revisión individual.

La lección metodológica de mayor alcance es que la calidad de un modelo no
supervisado no puede juzgarse solo con métricas internas. En dos ocasiones a lo
largo de este trabajo el coeficiente de silueta habría conducido a la peor
decisión posible, al elegir dos grupos en K-Means y al preferir los enlaces
degenerados del agrupamiento jerárquico. El conocimiento del dominio y una
referencia externa, cuando existe, resultan insustituibles.

# Referencias

Ayres-de-Campos, D., Bernardes, J., Garrido, A., Marques-de-Sá, J., &
Pereira-Leite, L. (2000). SisPorto 2.0: A program for automated analysis of
cardiotocograms. *Journal of Maternal-Fetal Medicine, 9*(5), 311-318.
https://doi.org/10.1002/1520-6661(200009/10)9:5<311::AID-MFM12>3.0.CO;2-9

Breunig, M. M., Kriegel, H.-P., Ng, R. T., & Sander, J. (2000). LOF:
Identifying density-based local outliers. *Proceedings of the 2000 ACM SIGMOD
International Conference on Management of Data*, 93-104.
https://doi.org/10.1145/342009.335388

Calinski, T., & Harabasz, J. (1974). A dendrite method for cluster analysis.
*Communications in Statistics, 3*(1), 1-27.
https://doi.org/10.1080/03610927408827101

Davies, D. L., & Bouldin, D. W. (1979). A cluster separation measure. *IEEE
Transactions on Pattern Analysis and Machine Intelligence, PAMI-1*(2), 224-227.
https://doi.org/10.1109/TPAMI.1979.4766909

Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based
algorithm for discovering clusters in large spatial databases with noise.
*Proceedings of the Second International Conference on Knowledge Discovery and
Data Mining (KDD-96)*, 226-231.

Hubert, L., & Arabie, P. (1985). Comparing partitions. *Journal of
Classification, 2*(1), 193-218. https://doi.org/10.1007/BF01908075

Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. *2008 Eighth
IEEE International Conference on Data Mining*, 413-422.
https://doi.org/10.1109/ICDM.2008.17

Meneses Yaranga, A. (2026). *Actividad de Aprendizaje Automático: detección de
anomalías y técnicas de agrupamiento sobre el conjunto de datos CTG* [Código
fuente]. GitHub. https://github.com/amenesesy/actividad-ml-ctg

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O.,
Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos,
A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011).
Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research,
12*, 2825-2830.

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and
validation of cluster analysis. *Journal of Computational and Applied
Mathematics, 20*, 53-65. https://doi.org/10.1016/0377-0427(87)90125-7

Rousseeuw, P. J., & Van Driessen, K. (1999). A fast algorithm for the minimum
covariance determinant estimator. *Technometrics, 41*(3), 212-223.
https://doi.org/10.1080/00401706.1999.10485670

Rubin, D. B. (1976). Inference and missing data. *Biometrika, 63*(3), 581-592.
https://doi.org/10.1093/biomet/63.3.581

Tukey, J. W. (1977). *Exploratory data analysis*. Addison-Wesley.

Ward, J. H. (1963). Hierarchical grouping to optimize an objective function.
*Journal of the American Statistical Association, 58*(301), 236-244.
https://doi.org/10.1080/01621459.1963.10500845
""")
